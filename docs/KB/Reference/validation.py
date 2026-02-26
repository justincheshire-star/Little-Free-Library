"""
lfl.validation
==============
Core retrieval validation and scoring engine.

Scores a corpus against synthetic queries using recall@k and
efficiency-adjusted scoring. The primary optimization target is:

    higher recall + lower tokens = best score

Tunable ingestion parameters (chunk_size, overlap, strategy, profile)
are recorded in every report so results are reproducible and comparable.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Literal

import numpy as np
import yaml


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    chunk_id: str
    title: str
    domain: str
    source: str
    source_license: str
    version: str
    content_hash: str
    body: str
    token_count: int
    embedding: np.ndarray | None = None

    @classmethod
    def from_md(cls, path: Path, tokenizer_fn: Callable[[str], int]) -> "Chunk":
        text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        fm, body = _parse_frontmatter(text)
        token_count = tokenizer_fn(body)
        return cls(
            chunk_id=path.stem,
            title=fm.get("title", path.stem),
            domain=fm.get("domain", "unknown"),
            source=fm.get("source", ""),
            source_license=fm.get("source_license", ""),
            version=fm.get("version", "0.0.0"),
            content_hash=fm.get("content_hash", _sha256(body)),
            body=body,
            token_count=token_count,
        )


@dataclass
class QuerySet:
    """Ground-truth query → chunk_id mappings."""
    queries: list[tuple[str, str]]  # (query_text, chunk_id)
    generated_at: str = ""
    strategy: str = "heuristic"


@dataclass
class RetrievalResult:
    query: str
    expected_chunk_id: str
    retrieved_chunk_ids: list[str]
    hit_at_1: bool = False
    hit_at_3: bool = False
    hit_at_5: bool = False
    bm25_score: float = 0.0
    rank: int | None = None  # rank of expected chunk (None = not found in top-k)


@dataclass
class TuningParams:
    """
    Ingestion parameters that affect retrieval quality.
    These are the levers — change them, re-ingest, re-benchmark.
    """
    chunk_size: int = 512           # target tokens per chunk
    chunk_overlap: int = 64         # token overlap between consecutive chunks
    chunking_strategy: Literal[
        "naive_paragraph",
        "sliding_window",
        "heading_aware",
        "semantic",
    ] = "naive_paragraph"
    embedding_profile: str = "baseline_cpu_onnx_small"
    text_normalization: bool = True  # strip excess whitespace, normalize unicode
    min_chunk_tokens: int = 32       # discard chunks shorter than this
    max_chunk_tokens: int = 1024     # hard cap (safety valve)


@dataclass
class BenchmarkReport:
    corpus_path: str
    profile: str
    params: TuningParams
    chunk_count: int
    query_count: int
    avg_chunk_tokens: float
    target_chunk_tokens: int

    # Recall metrics
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mrr: float = 0.0               # Mean Reciprocal Rank

    # Efficiency metrics
    normalized_token_cost: float = 0.0
    efficiency_score: float = 0.0   # recall@3 / normalized_token_cost
    coverage_penalty: float = 1.0   # drops if chunks exceed context window budget

    # Final composite score (higher = better)
    final_score: float = 0.0

    # Human-readable recommendation
    recommendations: list[str] = field(default_factory=list)

    elapsed_seconds: float = 0.0
    generated_at: str = ""

    def as_dict(self) -> dict:
        d = asdict(self)
        d["params"] = asdict(self.params)
        return d

    def summary(self) -> str:
        lines = [
            "",
            "=" * 60,
            "  LFL Retrieval Benchmark Report",
            "=" * 60,
            f"  Corpus       : {self.corpus_path}",
            f"  Profile      : {self.profile}",
            f"  Strategy     : {self.params.chunking_strategy}",
            f"  Chunk size   : {self.params.chunk_size} tokens  "
            f"(overlap: {self.params.chunk_overlap})",
            f"  Chunks       : {self.chunk_count}  "
            f"(avg {self.avg_chunk_tokens:.0f} tokens)",
            f"  Queries      : {self.query_count}",
            "-" * 60,
            f"  Recall@1     : {self.recall_at_1:.3f}",
            f"  Recall@3     : {self.recall_at_3:.3f}",
            f"  Recall@5     : {self.recall_at_5:.3f}",
            f"  MRR          : {self.mrr:.3f}",
            "-" * 60,
            f"  Token cost   : {self.normalized_token_cost:.3f}",
            f"  Coverage pen : {self.coverage_penalty:.3f}",
            f"  Efficiency   : {self.efficiency_score:.3f}",
            f"  FINAL SCORE  : {self.final_score:.3f}  ★",
            "-" * 60,
        ]
        if self.recommendations:
            lines.append("  Recommendations:")
            for r in self.recommendations:
                lines.append(f"    → {r}")
        lines += [
            "-" * 60,
            f"  Elapsed      : {self.elapsed_seconds:.1f}s",
            "=" * 60,
            "",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown chunk."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()
    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        fm = {}
    return fm, body


def _naive_tokenize(text: str) -> int:
    """
    Approximate token count without loading a tokenizer.
    ~4 chars per token is a reasonable heuristic for English text.
    Replace with a real tokenizer for production accuracy.
    """
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# BM25 scorer (pure Python, no deps)
# ---------------------------------------------------------------------------

class BM25:
    """
    Lightweight BM25 implementation for scoring retrieved vs expected chunks.
    Used as a fast quality proxy without requiring a cross-encoder.
    """

    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = [self._tokenize(doc) for doc in corpus]
        self.n = len(self.corpus)
        self.avgdl = sum(len(d) for d in self.corpus) / max(self.n, 1)
        self._build_index()

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()

    def _build_index(self) -> None:
        from collections import Counter
        self.df: dict[str, int] = {}
        self.tf: list[dict[str, float]] = []
        for doc in self.corpus:
            counts = Counter(doc)
            self.tf.append(counts)
            for term in counts:
                self.df[term] = self.df.get(term, 0) + 1

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log((self.n - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        tokens = self._tokenize(query)
        doc = self.corpus[doc_idx]
        dl = len(doc)
        score = 0.0
        tf_map = self.tf[doc_idx]
        for term in tokens:
            if term not in tf_map:
                continue
            tf = tf_map[term]
            idf = self.idf(term)
            score += idf * (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            )
        return score

    def get_scores(self, query: str) -> list[float]:
        return [self.score(query, i) for i in range(self.n)]

    def top_k(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        scores = self.get_scores(query)
        ranked = sorted(enumerate(scores), key=lambda x: -x[1])
        return ranked[:k]


# ---------------------------------------------------------------------------
# Corpus loader
# ---------------------------------------------------------------------------

def load_corpus(corpus_dir: Path, tokenizer_fn: Callable[[str], int] | None = None) -> list[Chunk]:
    tf = tokenizer_fn or _naive_tokenize
    chunks_dir = corpus_dir / "chunks"
    if not chunks_dir.exists():
        raise FileNotFoundError(f"No chunks/ directory found in {corpus_dir}")
    chunks = []
    for md in sorted(chunks_dir.glob("*.md")):
        try:
            chunks.append(Chunk.from_md(md, tf))
        except Exception as e:
            print(f"  [WARN] Skipping {md.name}: {e}")
    return chunks


# ---------------------------------------------------------------------------
# Retrieval engine (BM25 baseline)
# ---------------------------------------------------------------------------

def run_retrieval(
    queries: QuerySet,
    chunks: list[Chunk],
    k: int = 5,
) -> list[RetrievalResult]:
    """
    Run BM25 retrieval for each query against the chunk corpus.
    Returns one RetrievalResult per query.

    For vector retrieval, replace or augment this with embedding similarity.
    """
    bodies = [c.body for c in chunks]
    ids = [c.chunk_id for c in chunks]
    bm25 = BM25(bodies)

    results = []
    for query_text, expected_id in queries.queries:
        top = bm25.top_k(query_text, k=k)
        retrieved_ids = [ids[i] for i, _ in top]
        top_score = top[0][1] if top else 0.0

        # Find rank of expected chunk
        rank = None
        for r, (idx, _) in enumerate(top, start=1):
            if ids[idx] == expected_id:
                rank = r
                break

        results.append(RetrievalResult(
            query=query_text,
            expected_chunk_id=expected_id,
            retrieved_chunk_ids=retrieved_ids,
            hit_at_1=rank == 1,
            hit_at_3=rank is not None and rank <= 3,
            hit_at_5=rank is not None and rank <= 5,
            bm25_score=top_score,
            rank=rank,
        ))
    return results


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _coverage_penalty(avg_tokens: float, context_window: int = 4096, budget_fraction: float = 0.25) -> float:
    """
    Penalize if average chunk size exceeds a fraction of the context window.
    Ensures chunks fit comfortably in a retrieval context budget.
    """
    budget = context_window * budget_fraction
    if avg_tokens <= budget:
        return 1.0
    # Linear decay above budget
    return max(0.1, budget / avg_tokens)


def score_results(
    results: list[RetrievalResult],
    chunks: list[Chunk],
    params: TuningParams,
    context_window: int = 4096,
) -> dict:
    n = len(results)
    if n == 0:
        return {}

    recall_1 = sum(r.hit_at_1 for r in results) / n
    recall_3 = sum(r.hit_at_3 for r in results) / n
    recall_5 = sum(r.hit_at_5 for r in results) / n

    # Mean Reciprocal Rank
    mrr = sum(1.0 / r.rank for r in results if r.rank is not None) / n

    avg_tokens = sum(c.token_count for c in chunks) / max(len(chunks), 1)
    normalized_token_cost = avg_tokens / max(params.chunk_size, 1)

    coverage_pen = _coverage_penalty(avg_tokens, context_window)

    # Primary efficiency score: recall@3 balanced against token cost
    efficiency_score = recall_3 / max(normalized_token_cost, 0.01)

    # Final composite: efficiency × coverage penalty
    final_score = efficiency_score * coverage_pen

    return {
        "recall_at_1": round(recall_1, 4),
        "recall_at_3": round(recall_3, 4),
        "recall_at_5": round(recall_5, 4),
        "mrr": round(mrr, 4),
        "avg_chunk_tokens": round(avg_tokens, 1),
        "normalized_token_cost": round(normalized_token_cost, 4),
        "coverage_penalty": round(coverage_pen, 4),
        "efficiency_score": round(efficiency_score, 4),
        "final_score": round(final_score, 4),
    }


# ---------------------------------------------------------------------------
# Recommendations engine
# ---------------------------------------------------------------------------

def generate_recommendations(report: BenchmarkReport) -> list[str]:
    recs = []
    p = report.params

    if report.recall_at_1 < 0.5:
        recs.append(
            "Recall@1 is low (<0.50). Try reducing chunk_size to improve "
            "chunk specificity, or switch to heading_aware chunking strategy."
        )
    if report.recall_at_3 < 0.75:
        recs.append(
            "Recall@3 is below target (<0.75). Consider increasing chunk_overlap "
            f"(current: {p.chunk_overlap}) to reduce context boundary losses."
        )
    if report.avg_chunk_tokens > p.chunk_size * 0.9:
        recs.append(
            f"Average chunk tokens ({report.avg_chunk_tokens:.0f}) is close to "
            f"chunk_size ({p.chunk_size}). Many chunks may be hitting the hard cap — "
            "try increasing chunk_size or reducing max_chunk_tokens."
        )
    if report.avg_chunk_tokens < p.min_chunk_tokens * 2:
        recs.append(
            f"Average chunk tokens ({report.avg_chunk_tokens:.0f}) is very low. "
            "Chunks may be too granular. Try increasing chunk_size or min_chunk_tokens."
        )
    if report.coverage_penalty < 0.9:
        recs.append(
            f"Coverage penalty is {report.coverage_penalty:.2f} — chunks are large "
            "relative to context window budget. Reduce chunk_size to improve fit."
        )
    if report.normalized_token_cost > 1.2:
        recs.append(
            "Token cost is high. Chunks are larger than the target chunk_size on average. "
            "Check for documents that are bypassing the chunk splitter."
        )
    if report.efficiency_score > 0.9 and report.recall_at_5 > 0.95:
        recs.append(
            "Excellent score. Consider publishing this profile + params as the "
            "recommended ingestion config for this corpus."
        )
    if not recs:
        recs.append("No critical issues detected. Consider running with a different chunking strategy to compare.")

    return recs


# ---------------------------------------------------------------------------
# Report persistence
# ---------------------------------------------------------------------------

def save_report(report: BenchmarkReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = report.generated_at.replace(":", "-").replace(" ", "_")
    filename = f"benchmark_{report.params.chunking_strategy}_{report.params.chunk_size}_{ts}.json"
    path = output_dir / filename
    path.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")
    return path


def load_reports(report_dir: Path) -> list[BenchmarkReport]:
    """Load all benchmark reports for comparison."""
    reports = []
    for p in sorted(report_dir.glob("benchmark_*.json")):
        try:
            d = json.loads(p.read_text())
            params = TuningParams(**d.pop("params"))
            reports.append(BenchmarkReport(params=params, **d))
        except Exception as e:
            print(f"[WARN] Could not load report {p.name}: {e}")
    return reports


def compare_reports(reports: list[BenchmarkReport]) -> str:
    """Render a comparison table of all reports sorted by final_score."""
    if not reports:
        return "No reports to compare."

    reports = sorted(reports, key=lambda r: -r.final_score)
    header = f"{'Strategy':<20} {'Size':>6} {'Ovlp':>5} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'MRR':>6} {'Score':>8}"
    sep = "-" * len(header)
    lines = ["", "LFL Benchmark Comparison", sep, header, sep]

    for r in reports:
        lines.append(
            f"{r.params.chunking_strategy:<20} "
            f"{r.params.chunk_size:>6} "
            f"{r.params.chunk_overlap:>5} "
            f"{r.recall_at_1:>6.3f} "
            f"{r.recall_at_3:>6.3f} "
            f"{r.recall_at_5:>6.3f} "
            f"{r.mrr:>6.3f} "
            f"{r.final_score:>8.3f}"
            + (" ★ BEST" if r == reports[0] else "")
        )
    lines.append(sep)
    return "\n".join(lines)
