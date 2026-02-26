"""
lfl.cli  (benchmark commands)
=============================
Adds benchmark, sweep, and compare commands to the lfl CLI.

Add these to your existing cli.py app:

    from lfl.cli_benchmark import benchmark_app
    app.add_typer(benchmark_app, name="benchmark")

Or merge the commands directly into your existing app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .benchmark import SWEEP_GRID, run_benchmark, run_sweep
from .validation import TuningParams, compare_reports, load_reports

benchmark_app = typer.Typer(
    name="benchmark",
    help="Retrieval validation and parameter tuning.",
    no_args_is_help=True,
)


@benchmark_app.command("run")
def cmd_run(
    corpus_dir: Path = typer.Argument(..., help="Path to a corpus directory, e.g. corpora/programming"),
    profile: str = typer.Option("baseline_cpu_onnx_small", "--profile", "-p", help="Embedding profile ID"),
    chunk_size: int = typer.Option(512, "--chunk-size", help="Target tokens per chunk"),
    overlap: int = typer.Option(64, "--overlap", help="Token overlap between chunks"),
    strategy: str = typer.Option("naive_paragraph", "--strategy", "-s",
                                  help="Chunking strategy: naive_paragraph | heading_aware | sliding_window | semantic"),
    queries_per_chunk: int = typer.Option(2, "--qpc", help="Synthetic queries generated per chunk"),
    query_strategy: str = typer.Option("heuristic", "--query-strategy",
                                        help="Query generation strategy: heuristic | extractive | llm"),
    llm_endpoint: str = typer.Option("", "--llm-endpoint", help="Local LLM endpoint URL (for llm query strategy)"),
    k: int = typer.Option(5, "--top-k", help="Top-k for retrieval evaluation"),
    context_window: int = typer.Option(4096, "--context-window", help="Target LLM context window size"),
    no_reuse: bool = typer.Option(False, "--no-reuse", help="Regenerate queries even if cached"),
    verbose: bool = typer.Option(True, "--verbose/--quiet"),
) -> None:
    """
    Run a retrieval benchmark on a corpus.

    Generates synthetic queries, runs BM25 retrieval, scores recall and
    token efficiency, and saves a report to corpus_dir/benchmarks/.

    Adjust --chunk-size, --overlap, and --strategy to tune ingestion params,
    then re-run to compare scores.

    Example:
        lfl benchmark run corpora/programming --chunk-size 256 --overlap 32
    """
    if not corpus_dir.exists():
        typer.echo(f"[ERROR] Corpus directory not found: {corpus_dir}", err=True)
        raise typer.Exit(1)

    params = TuningParams(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        chunking_strategy=strategy,  # type: ignore[arg-type]
        embedding_profile=profile,
    )

    report = run_benchmark(
        corpus_dir=corpus_dir,
        params=params,
        queries_per_chunk=queries_per_chunk,
        query_strategy=query_strategy,  # type: ignore[arg-type]
        llm_endpoint=llm_endpoint,
        k=k,
        context_window=context_window,
        reuse_queries=not no_reuse,
        verbose=verbose,
    )

    typer.echo(report.summary())


@benchmark_app.command("sweep")
def cmd_sweep(
    corpus_dir: Path = typer.Argument(..., help="Path to a corpus directory"),
    profile: str = typer.Option("baseline_cpu_onnx_small", "--profile", "-p"),
    queries_per_chunk: int = typer.Option(2, "--qpc"),
    query_strategy: str = typer.Option("heuristic", "--query-strategy"),
) -> None:
    """
    Sweep a grid of chunk_size / overlap / strategy combinations and
    rank them by final score.

    The best configuration is printed with recommendations.
    All reports are saved to corpus_dir/benchmarks/.

    Example:
        lfl benchmark sweep corpora/programming
    """
    if not corpus_dir.exists():
        typer.echo(f"[ERROR] Corpus directory not found: {corpus_dir}", err=True)
        raise typer.Exit(1)

    base_params = TuningParams(embedding_profile=profile)
    run_sweep(
        corpus_dir=corpus_dir,
        base_params=base_params,
        queries_per_chunk=queries_per_chunk,
        query_strategy=query_strategy,  # type: ignore[arg-type]
    )


@benchmark_app.command("compare")
def cmd_compare(
    corpus_dir: Path = typer.Argument(..., help="Path to a corpus directory"),
) -> None:
    """
    Compare all saved benchmark reports for a corpus.

    Renders a table sorted by final_score with the best config marked.

    Example:
        lfl benchmark compare corpora/programming
    """
    report_dir = corpus_dir / "benchmarks"
    if not report_dir.exists():
        typer.echo(f"[ERROR] No benchmarks directory found at {report_dir}", err=True)
        raise typer.Exit(1)

    reports = load_reports(report_dir)
    if not reports:
        typer.echo("No benchmark reports found. Run `lfl benchmark run` first.")
        raise typer.Exit(0)

    typer.echo(compare_reports(reports))
    best = sorted(reports, key=lambda r: -r.final_score)[0]
    typer.echo(f"\nBest config: chunk_size={best.params.chunk_size} "
               f"overlap={best.params.chunk_overlap} "
               f"strategy={best.params.chunking_strategy} "
               f"score={best.final_score:.3f}")
    if best.recommendations:
        typer.echo("\nRecommendations:")
        for r in best.recommendations:
            typer.echo(f"  → {r}")
