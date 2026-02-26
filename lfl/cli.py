"""
lfl.cli — Main CLI entry point for Little Free Library.

Usage:
    lfl --help
    lfl benchmark --help
    lfl validate --help
    lfl chunk --help
"""

from pathlib import Path
from typing import Optional
import sys
from datetime import datetime

import typer

from .cli_benchmark import benchmark_app


app = typer.Typer(
    name="lfl",
    help="Little Free Library — Corpus curation and RAG validation toolkit",
    no_args_is_help=True,
)

# Register the benchmark subcommand
app.add_typer(benchmark_app, name="benchmark")


@app.command("validate")
def cmd_validate(
    corpus_dir: Path = typer.Argument(..., help="Path to a corpus directory"),
    strict: bool = typer.Option(False, "--strict", help="Fail on warnings"),
    skip_sources: bool = typer.Option(False, "--skip-sources", help="Skip sources.json validation"),
) -> None:
    """
    Validate a corpus directory for required metadata and structure.

    Checks:
    - YAML frontmatter completeness
    - Required fields present
    - sources.json exists and is valid
    - Chunk files are well-formed
    - Source ID references are valid
    """
    from .corpus_validation import validate_corpus, format_validation_report
    
    try:
        valid_count, invalid_count, errors_by_file, source_errors, orphaned = validate_corpus(
            corpus_dir, strict=strict, check_sources=not skip_sources
        )
        
        report = format_validation_report(
            corpus_dir, valid_count, invalid_count, errors_by_file, source_errors, orphaned, strict
        )
        typer.echo(report)
        
        # Calculate exit code
        total_errors = invalid_count + len([e for e in source_errors if not e.startswith("sources.json not found")])
        total_warnings = len([e for e in source_errors if e.startswith("sources.json not found")]) + len(orphaned)
        
        if total_errors > 0:
            raise typer.Exit(1)
        elif strict and total_warnings > 0:
            raise typer.Exit(1)
        
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


@app.command("chunk")
def cmd_chunk(
    input_file: Path = typer.Argument(..., help="Input text or markdown file to chunk"),
    output_dir: Path = typer.Argument(..., help="Output directory for chunks"),
    domain: str = typer.Option(..., "--domain", "-d", help="Domain (e.g., 'programming')"),
    subdomain: str = typer.Option("", "--subdomain", help="Subdomain (optional)"),
    source: str = typer.Option(..., "--source", help="Source name/description"),
    source_license: str = typer.Option(..., "--license", "-l", help="Source license"),
    source_id: str = typer.Option(..., "--source-id", help="Source ID (from sources.json)"),
    source_path: str = typer.Option("", "--source-path", help="Path within source"),
    strategy: str = typer.Option("naive_paragraph", "--strategy", "-s",
                                   help="Chunking strategy: naive_paragraph | heading_aware | sliding_window"),
    chunk_size: int = typer.Option(512, "--chunk-size", help="Target tokens per chunk"),
    overlap: int = typer.Option(64, "--overlap", help="Token overlap between chunks"),
    min_tokens: int = typer.Option(32, "--min-tokens", help="Minimum tokens per chunk"),
    max_tokens: int = typer.Option(1024, "--max-tokens", help="Maximum tokens per chunk"),
    importance: float = typer.Option(0.5, "--importance", help="Importance score (0.0-1.0)"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    verified: str = typer.Option("", "--verified", help="Verification date (YYYY-MM-DD)"),
) -> None:
    """
    Chunk a document into corpus-ready markdown files.
    
    Reads a text or markdown file, chunks it using the specified strategy,
    and outputs individual chunk files with complete YAML frontmatter.
    
    Example:
        lfl chunk document.md corpora/programming/chunks \\
          --domain programming \\
          --subdomain python \\
          --source "Python Docs" \\
          --license PSF-2.0 \\
          --source-id python-docs-3.12
    """
    from .chunking import chunk_document, save_chunk_to_markdown
    
    try:
        if not input_file.exists():
            typer.echo(f"[ERROR] Input file not found: {input_file}", err=True)
            raise typer.Exit(1)
        
        # Read input
        text = input_file.read_text(encoding="utf-8")
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Set defaults
        if not verified:
            verified = datetime.now().strftime("%Y-%m-%d")
        
        if not source_path:
            source_path = str(input_file.name)
        
        # Prepare metadata
        base_metadata = {
            "domain": domain,
            "subdomain": subdomain,
            "source": source,
            "source_license": source_license,
            "source_id": source_id,
            "source_path": source_path,
            "retrieved_at": datetime.now().strftime("%Y-%m-%d"),
            "verified": verified,
            "importance": importance,
            "tags": tag_list,
            "version": "1.0.0",
        }
        
        typer.echo(f"Chunking {input_file.name} with strategy '{strategy}'...")
        
        # Chunk the document
        chunks = chunk_document(
            text,
            base_metadata,
            strategy=strategy,  # type: ignore
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_tokens=min_tokens,
            max_chunk_tokens=max_tokens,
        )
        
        if not chunks:
            typer.echo("[WARNING] No chunks generated. Check input file and parameters.", err=True)
            raise typer.Exit(1)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save chunks
        typer.echo(f"Generated {len(chunks)} chunks. Saving to {output_dir}/...")
        
        for i, chunk in enumerate(chunks, 1):
            output_path = output_dir / f"{chunk.metadata.chunk_id}.md"
            save_chunk_to_markdown(chunk, output_path)
            typer.echo(f"  [{i}/{len(chunks)}] {output_path.name} ({chunk.token_count} tokens)")
        
        typer.echo(f"\n✅ Successfully chunked document into {len(chunks)} files")
        typer.echo(f"   Output directory: {output_dir}")
        
    except Exception as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


@app.command("version")
def cmd_version() -> None:
    """Show lfl version."""
    from . import __version__
    typer.echo(f"lfl version {__version__}")


def main():
    """Entry point for the lfl CLI."""
    app()


if __name__ == "__main__":
    main()
