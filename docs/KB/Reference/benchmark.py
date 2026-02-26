"""
lfl.benchmark
=============
CLI-facing benchmark runner.
Ties together: corpus loading → query generation → retrieval → scoring → report.

Usage (via lfl CLI):
    lfl benchmark corpora/programming --profile baseline_cpu_onnx_small
    lfl benchmark corpora/programming --chunk-size 256 --overlap 32 --strategy heading_aware
    lfl benchmark corpora/programming --compare          # compare all saved reports
    lfl benchmark corpora/programming --sweep            # auto-sweep parameter grid
"""

from __future__ import annotations

import datetime
import time
from pathlib import Path
from typing import Literal

from .query_gen import QueryStrategy, generate_query_set, load_query_set, save_query_set
from .validation import (
    BenchmarkReport,
    TuningParams,
    compare_reports,
    generate_recommendations,
    load_corpus,
    load_reports,
    run_retrieval,
    save_report,
    score_results,
)


# ---------------------------------------------------------------------------
# Parameter sweep grid
# ---------------------------------------------------------------------------

SWEEP_GRID = [
    # (chunk_size, overlap, strategy)
    (256,  32,  "naive_paragraph"),
    (512,  64,  "naive_paragraph"),
    (512,  128, "naive_paragraph"),
    (768,  64,  "naive_paragraph"),
    (256,  32,  "heading_aware"),
    (512,  64,  "heading_aware"),
    (512,  128, "sliding_window"),
    (768,  128, "sliding_window"),
]


# ---------------------------------------------------------------------------
# Core benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark(
    corpus_dir: Path,
    params: TuningParams,
    queries_per_chunk: int = 2,
    query_strategy: QueryStrategy = "heuristic",
    llm_endpoint: str = "",
    k: int = 5,
    context_window: int = 4096,
    reuse_queries: bool = True,
    report_dir: Path | None = None,
    verbose: bool = False,
) -> BenchmarkReport:
    """
    Run a full benchmark cycle on a corpus directory.

    Parameters
    ----------
    corpus_dir       : path to corpora/<domain>/
    params           : TuningParams (the levers)
    queries_per_chunk: synthetic queries generated per chunk
    query_strategy   : heuristic | extractive | llm
    llm_endpoint     : local LLM URL (for llm strategy)
    k                : top-k for retrieval evaluation
    context_window   : target LLM context window (for coverage penalty)
    reuse_queries    : if True, reuse saved query set if present
    report_dir       : where to save the report JSON (default: corpus_dir/benchmarks/)
    verbose          : print progress

    Returns
    -------
    BenchmarkReport
    """
    t0 = time.perf_counter()
    report_dir = report_dir or (corpus_dir / "benchmarks")

    # 1. Load corpus
    if verbose:
        print(f"[1/4] Loading corpus from {corpus_dir} ...")
    chunks = load_corpus(corpus_dir)
    if not chunks:
        raise ValueError(f"No chunks found in {corpus_dir}/chunks/")
    if verbose:
        print(f"      Loaded {len(chunks)} chunks.")

    # 2. Generate or reuse queries
    query_cache = report_dir / f"queries_{query_strategy}.json"
    if reuse_queries and query_cache.exists():
        if verbose:
            print(f"[2/4] Reusing saved query set ({query_cache.name}) ...")
        qs = load_query_set(query_cache)
        # Filter to chunks that still exist
        valid_ids = {c.chunk_id for c in chunks}
        qs.queries = [(q, cid) for q, cid in qs.queries if cid in valid_ids]
    else:
        if verbose:
            print(f"[2/4] Generating synthetic queries (strategy={query_strategy}) ...")
        qs = generate_query_set(
            chunks,
            queries_per_chunk=queries_per_chunk,
            strategy=query_strategy,
            llm_endpoint=llm_endpoint,
        )
        save_query_set(qs, query_cache)
        if verbose:
            print(f"      Generated {len(qs.queries)} queries. Saved to {query_cache.name}")

    # 3. Run retrieval
    if verbose:
        print(f"[3/4] Running BM25 retrieval (k={k}) ...")
    results = run_retrieval(qs, chunks, k=k)

    # 4. Score
    if verbose:
        print("[4/4] Scoring results ...")
    scores = score_results(results, chunks, params, context_window)

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    elapsed = time.perf_counter() - t0

    report = BenchmarkReport(
        corpus_path=str(corpus_dir),
        profile=params.embedding_profile,
        params=params,
        chunk_count=len(chunks),
        query_count=len(qs.queries),
        avg_chunk_tokens=scores["avg_chunk_tokens"],
        target_chunk_tokens=params.chunk_size,
        recall_at_1=scores["recall_at_1"],
        recall_at_3=scores["recall_at_3"],
        recall_at_5=scores["recall_at_5"],
        mrr=scores["mrr"],
        normalized_token_cost=scores["normalized_token_cost"],
        efficiency_score=scores["efficiency_score"],
        coverage_penalty=scores["coverage_penalty"],
        final_score=scores["final_score"],
        elapsed_seconds=round(elapsed, 2),
        generated_at=now,
    )
    report.recommendations = generate_recommendations(report)

    # Save report
    saved_path = save_report(report, report_dir)
    if verbose:
        print(f"      Report saved → {saved_path.name}")

    return report


# ---------------------------------------------------------------------------
# Parameter sweep
# ---------------------------------------------------------------------------

def run_sweep(
    corpus_dir: Path,
    base_params: TuningParams,
    grid: list[tuple[int, int, str]] | None = None,
    queries_per_chunk: int = 2,
    query_strategy: QueryStrategy = "heuristic",
    verbose: bool = True,
) -> list[BenchmarkReport]:
    """
    Run a full parameter sweep across chunk_size / overlap / strategy combinations.
    Returns all reports sorted by final_score descending.
    """
    grid = grid or SWEEP_GRID
    reports = []

    print(f"\nStarting sweep: {len(grid)} configurations on {corpus_dir.name}\n")

    for i, (chunk_size, overlap, strategy) in enumerate(grid, 1):
        print(f"[{i}/{len(grid)}] chunk_size={chunk_size} overlap={overlap} strategy={strategy}")
        p = TuningParams(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            chunking_strategy=strategy,
            embedding_profile=base_params.embedding_profile,
            text_normalization=base_params.text_normalization,
            min_chunk_tokens=base_params.min_chunk_tokens,
            max_chunk_tokens=base_params.max_chunk_tokens,
        )
        try:
            r = run_benchmark(
                corpus_dir=corpus_dir,
                params=p,
                queries_per_chunk=queries_per_chunk,
                query_strategy=query_strategy,
                reuse_queries=True,
                verbose=False,
            )
            reports.append(r)
            print(f"        → score={r.final_score:.3f}  recall@3={r.recall_at_3:.3f}  "
                  f"avg_tokens={r.avg_chunk_tokens:.0f}")
        except Exception as e:
            print(f"        [FAIL] {e}")

    reports.sort(key=lambda r: -r.final_score)

    print("\n" + compare_reports(reports))

    if reports:
        best = reports[0]
        print(f"\nBest configuration:")
        print(f"  chunk_size={best.params.chunk_size}  "
              f"overlap={best.params.chunk_overlap}  "
              f"strategy={best.params.chunking_strategy}")
        print(f"  final_score={best.final_score:.3f}  "
              f"recall@3={best.recall_at_3:.3f}")
        if best.recommendations:
            print("\nRecommendations for best config:")
            for rec in best.recommendations:
                print(f"  → {rec}")

    return reports
