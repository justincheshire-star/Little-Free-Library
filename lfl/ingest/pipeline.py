"""
Main ingestion pipeline orchestration.

Converts arbitrary documents → validated LFL corpus format:
    ingestion/<domain>/ → corpora/<domain>/chunks/*.md + sources.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .types import IngestionManifest, IngestionResult
from .detect import discover_files, compute_file_hash
from .convert import needs_conversion, get_conversion_target, convert_with_libreoffice, has_libreoffice
from .extract import extract_text


def _build_sources_json(
    corpus_dir: Path,
    manifest: IngestionManifest,
) -> dict:
    """
    Build or update sources.json with ingested file provenance.
    
    Merges with existing sources.json if present.
    """
    sources_path = corpus_dir / "sources.json"
    
    # Load existing sources if present
    existing: dict = {"sources": []}
    if sources_path.exists():
        try:
            existing = json.loads(sources_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    
    existing_ids = {s["id"] for s in existing.get("sources", []) if isinstance(s, dict)}
    
    for result in manifest.results:
        if result.status != "success":
            continue
        
        source_id = f"local_{result.sha256[:8]}"
        
        if source_id in existing_ids:
            continue
        
        existing["sources"].append({
            "id": source_id,
            "name": result.file_path.stem,
            "url": f"file://{result.file_path}",
            "license": "unknown",
            "retrieval_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": (
                f"Ingested via lfl ingest. "
                f"Type: {result.detected_type}. "
                f"Method: {result.extraction_method}. "
                f"SHA256: {result.sha256}. "
                f"Review and update license before publishing."
            ),
        })
        existing_ids.add(source_id)
    
    return existing


def _write_corpus_manifest(corpus_dir: Path, domain: str) -> None:
    """Create or preserve CORPUS.md in the corpus directory."""
    corpus_md = corpus_dir / "CORPUS.md"
    if corpus_md.exists():
        return
    
    corpus_md.write_text(f"""# Corpus Manifest — {domain.title()}

## Metadata

| Field | Value |
|---|---|
| **Domain** | `{domain}` |
| **Version** | `1.0.0` |
| **Status** | `ingested` |
| **License (corpus data)** | CC-BY-SA 4.0 |
| **Maintainer** | Little Free Library Contributors |
| **Last Updated** | {datetime.now().strftime("%Y-%m-%d")} |

---

## Description

Auto-generated corpus via `lfl ingest`. Review and update metadata before publishing.

---

## Sources

See [`sources.json`](sources.json) for full provenance details.

---

## Notes

- Source licenses default to `unknown` — verify before publishing.
- Chunks default to `verified: unverified` — review before publishing.
- Run `lfl validate {domain}` to check corpus quality.
""", encoding="utf-8")


def ingest_directory(
    domain: str,
    input_dir: Path | str,
    corpus_dir: Path | str,
    recursive: bool = True,
    on_duplicate: str = "update",
    strategy: str = "heading_aware",
    chunk_size: int = 512,
    overlap: int = 64,
    embed: bool = False,
    profile: str = "baseline_cpu_onnx_small",
    strict: bool = False,
    inventory: bool = False,
) -> IngestionManifest:
    """
    Ingest directory of arbitrary documents into LFL corpus format.
    
    Pipeline:
        1. Discover files (type detection + hashing)
        2. Convert if needed (Pages → PDF, legacy Office → modern)
        3. Extract text and tables
        4. Chunk documents (calls lfl.chunking)
        5. Write chunks with YAML frontmatter
        6. Generate / update sources.json
        7. (Optional) Validate corpus
        8. (Optional) Generate embeddings
        9. Write ingestion manifest
    
    Args:
        domain: Corpus domain name
        input_dir: Directory containing documents to ingest
        corpus_dir: Output corpus directory
        recursive: Scan subdirectories
        on_duplicate: How to handle existing chunks ("skip" or "update")
        strategy: Chunking strategy (heading_aware, naive_paragraph, sliding_window)
        chunk_size: Target tokens per chunk
        overlap: Token overlap between chunks
        embed: Generate embeddings after chunking
        profile: Embedding profile name
        strict: Enable strict validation mode
        inventory: Dry-run mode — show plan without writing
        
    Returns:
        IngestionManifest with run statistics and per-file results
    """
    input_dir = Path(input_dir)
    corpus_dir = Path(corpus_dir)
    
    # Generate run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize manifest
    manifest = IngestionManifest(
        run_id=run_id,
        domain=domain,
        input_dir=str(input_dir),
        output_dir=str(corpus_dir),
        timestamp=datetime.now(),
        files_discovered=0,
        files_converted=0,
        files_extracted=0,
        chunks_created=0,
        chunks_updated=0,
        failures=0,
        system_info={
            "libreoffice_available": has_libreoffice(),
            "strategy": strategy,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "on_duplicate": on_duplicate,
        },
    )
    
    # ── Stage 1: Discover files ──────────────────────────────────
    print(f"📂 Scanning {input_dir} ...")
    discovered = discover_files(input_dir, recursive=recursive)
    manifest.files_discovered = len(discovered)
    print(f"   Found {len(discovered)} ingestible file(s)")
    
    if not discovered:
        print("⚠️  No ingestible files found. Check the input directory.")
        return manifest
    
    # ── Inventory mode (dry-run) ─────────────────────────────────
    if inventory:
        print("\n📋 Inventory (dry-run) — no files will be written:\n")
        for f in discovered:
            conv = " → convert" if needs_conversion(f.detected_type) else ""
            print(f"   {f.path.name}  [{f.detected_type}]  "
                  f"{f.size_bytes:,} bytes  sha256:{f.sha256[:12]}…{conv}")
        print(f"\n   Total: {len(discovered)} files")
        manifest.system_info["mode"] = "inventory"
        return manifest
    
    # ── Create output directories ────────────────────────────────
    chunks_dir = corpus_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine ingestion_out path
    # Support both repo-relative (ingestion_out/<domain>) and absolute paths
    if str(corpus_dir).startswith("corpora"):
        out_base = Path("ingestion_out") / domain
    else:
        out_base = corpus_dir.parent / "ingestion_out" / domain
    converted_dir = out_base / "converted"
    converted_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect existing chunk hashes for dedup
    existing_hashes: set[str] = set()
    if on_duplicate == "skip":
        for md_file in chunks_dir.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                for line in text.split("\n"):
                    if line.startswith("content_hash:"):
                        existing_hashes.add(line.split(":", 1)[-1].strip().strip('"'))
                        break
            except OSError:
                pass
    
    # ── Stage 2-5: Process each file ─────────────────────────────
    # Lazy import chunking to avoid circular deps
    from ..chunking import chunk_document, save_chunk_to_markdown
    
    global_chunk_index = len(list(chunks_dir.glob("*.md")))
    
    for file_info in discovered:
        print(f"\n📄 {file_info.path.name}")
        
        try:
            # Stage 2: Convert if necessary
            extraction_path = file_info.path
            effective_type = file_info.detected_type
            
            if needs_conversion(file_info.detected_type):
                target_fmt = get_conversion_target(file_info.detected_type)
                print(f"   ↳ Converting {file_info.detected_type} → {target_fmt} …")
                extraction_path = convert_with_libreoffice(
                    file_info.path, converted_dir, target_format=target_fmt,
                )
                manifest.files_converted += 1
                effective_type = target_fmt
                print(f"   ✓ Converted")
            
            # Stage 3: Extract text / tables
            extracted = extract_text(extraction_path, effective_type)
            manifest.files_extracted += 1
            
            if not extracted.text.strip() and not extracted.tables:
                # Use the most specific structured error from the extractor
                se = extracted.structured_errors
                primary = se[-1] if se else None
                code = primary.code if primary else "LFL-E100"
                msg = primary.cli_message() if primary else "No text or tables extracted"
                print(f"   {msg}")
                manifest.results.append(IngestionResult(
                    file_path=file_info.path,
                    sha256=file_info.sha256,
                    detected_type=effective_type,
                    extraction_method=extracted.extraction_method,
                    chunks_produced=0, status="failed",
                    error=msg,
                    error_code=code,
                    warnings=extracted.warnings,
                    structured_errors=[e.to_dict() for e in se],
                ))
                manifest.failures += 1
                continue
            
            # Combine text + table markdown into a single document
            full_text = extracted.text
            if extracted.tables:
                table_md = "\n\n".join(
                    f"## Table: {t.sheet_name or 'Untitled'}\n\n{t.markdown}"
                    for t in extracted.tables
                )
                if full_text.strip():
                    full_text = full_text + "\n\n" + table_md
                else:
                    full_text = table_md
            
            print(f"   ✓ Extracted {len(full_text):,} chars")
            
            # Stage 4: Chunk using existing lfl.chunking module
            source_id = f"local_{file_info.sha256[:8]}"
            base_metadata = {
                "domain": domain,
                "subdomain": "",
                "source": f"file://{file_info.path}",
                "source_license": "unknown",
                "source_id": source_id,
                "source_path": str(file_info.path.name),
                "retrieved_at": datetime.now().strftime("%Y-%m-%d"),
                "verified": "unverified",
                "importance": 0.5,
                "tags": [domain, effective_type],
                "version": "1.0.0",
            }
            
            chunks = chunk_document(
                text=full_text,
                base_metadata=base_metadata,
                strategy=strategy,  # type: ignore[arg-type]
                chunk_size=chunk_size,
                overlap=overlap,
            )
            
            if not chunks:
                from .errors import P601_zero_chunks_from_file
                err = P601_zero_chunks_from_file(str(file_info.path))
                print(f"   {err.cli_message()}")
                manifest.results.append(IngestionResult(
                    file_path=file_info.path,
                    sha256=file_info.sha256,
                    detected_type=effective_type,
                    extraction_method=extracted.extraction_method,
                    chunks_produced=0, status="failed",
                    error=err.summary,
                    error_code=err.code,
                    warnings=extracted.warnings,
                    structured_errors=[err.to_dict()],
                ))
                manifest.failures += 1
                continue
            
            # Stage 5: Write chunks
            written = 0
            skipped = 0
            for chunk in chunks:
                # Duplicate check
                if on_duplicate == "skip" and chunk.metadata.content_hash in existing_hashes:
                    skipped += 1
                    continue
                
                output_path = chunks_dir / f"{chunk.metadata.chunk_id}.md"
                save_chunk_to_markdown(chunk, output_path)
                existing_hashes.add(chunk.metadata.content_hash)
                written += 1
                global_chunk_index += 1
            
            manifest.chunks_created += written
            manifest.chunks_updated += skipped
            
            # Propagate any non-fatal structured warnings from extractor
            se_dicts = [e.to_dict() for e in extracted.structured_errors] if extracted.structured_errors else []
            manifest.results.append(IngestionResult(
                file_path=file_info.path,
                sha256=file_info.sha256,
                detected_type=effective_type,
                extraction_method=extracted.extraction_method,
                chunks_produced=written,
                status="success",
                warnings=extracted.warnings,
                structured_errors=se_dicts,
            ))
            
            skip_note = f" ({skipped} skipped as duplicates)" if skipped else ""
            print(f"   ✓ {written} chunk(s) written{skip_note}")
        
        except Exception as exc:
            from .errors import P603_unexpected_pipeline_error
            err = P603_unexpected_pipeline_error(
                str(file_info.path), "processing", str(exc),
            )
            print(f"   {err.cli_message()}")
            manifest.results.append(IngestionResult(
                file_path=file_info.path,
                sha256=file_info.sha256,
                detected_type=file_info.detected_type,
                extraction_method="failed",
                chunks_produced=0, status="failed",
                error=str(exc),
                error_code=err.code,
                structured_errors=[err.to_dict()],
            ))
            manifest.failures += 1
    
    # ── Stage 6: Update sources.json ─────────────────────────────
    print("\n📝 Updating sources.json …")
    sources_data = _build_sources_json(corpus_dir, manifest)
    sources_path = corpus_dir / "sources.json"
    sources_path.write_text(
        json.dumps(sources_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    source_count = len(sources_data.get("sources", []))
    print(f"   ✓ {source_count} source(s) in sources.json")
    
    # ── Stage 6b: Create CORPUS.md if missing ────────────────────
    _write_corpus_manifest(corpus_dir, domain)
    
    # ── Stage 7: Validate (optional) ─────────────────────────────
    try:
        from ..corpus_validation import validate_corpus, format_validation_report
        
        print("\n🔍 Validating corpus …")
        valid, invalid, errors_by_file, src_errors, orphaned = validate_corpus(
            corpus_dir, strict=strict, check_sources=True,
        )
        print(f"   ✓ {valid} valid, {invalid} invalid chunk(s)")
        if invalid > 0:
            for fp, errs in errors_by_file[:5]:
                print(f"     {fp.name}: {'; '.join(errs[:2])}")
        if src_errors:
            for e in src_errors[:3]:
                print(f"     ⚠️  {e}")
    except Exception as exc:
        print(f"   ⚠️  Validation skipped: {exc}")
    
    # ── Stage 8: Embeddings (optional) ───────────────────────────
    if embed:
        try:
            from ..embeddings import EmbeddingModel, save_embeddings
            from ..validation import load_corpus
            
            print(f"\n🧠 Generating embeddings (profile={profile}) …")
            model = EmbeddingModel(profile_id=profile)
            
            corpus_chunks = load_corpus(corpus_dir)
            texts = [c.body for c in corpus_chunks]
            vectors = model.encode(texts)
            
            emb_dir = corpus_dir / "embeddings"
            emb_dir.mkdir(parents=True, exist_ok=True)
            
            import numpy as np
            np.save(emb_dir / "vectors.npy", vectors)
            print(f"   ✓ {len(vectors)} vectors saved to embeddings/vectors.npy")
            manifest.system_info["embeddings"] = {
                "profile": profile,
                "vectors": len(vectors),
            }
        except Exception as exc:
            print(f"   ⚠️  Embedding generation failed: {exc}")
            manifest.warnings.append(f"Embedding failed: {exc}")
    
    # ── Stage 9: Write manifest ──────────────────────────────────
    manifest_path = out_base / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    
    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  ✅ Ingestion complete — {domain}")
    print(f"{'=' * 60}")
    print(f"  Files discovered : {manifest.files_discovered}")
    print(f"  Files converted  : {manifest.files_converted}")
    print(f"  Chunks created   : {manifest.chunks_created}")
    if manifest.chunks_updated:
        print(f"  Chunks skipped   : {manifest.chunks_updated} (duplicates)")
    print(f"  Failures         : {manifest.failures}")
    print(f"  Corpus dir       : {corpus_dir}")
    print(f"  Manifest         : {manifest_path}")
    print(f"{'=' * 60}")
    
    return manifest
