"""
lfl.ingest.errors — Structured error codes for the ingestion pipeline.

Every failure that the pipeline can produce is mapped to a unique,
human-readable error code of the form ``LFL-XNNN`` where:

- ``X`` is a category letter:
    - **D** – Detection / file-discovery
    - **C** – Conversion (LibreOffice, Pandoc)
    - **E** – Extraction (PDF / DOCX / XLSX / HTML / TXT / OCR)
    - **K** – Chunking / frontmatter
    - **V** – Validation
    - **M** – Embedding / model
    - **P** – Pipeline orchestration
- ``NNN`` is a three-digit number, unique within category.

Each code carries:

- ``code``        – e.g. ``"LFL-E101"``
- ``severity``    – ``"error"`` or ``"warning"``
- ``summary``     – one-line description shown in console output
- ``detail``      – multi-line explanation aimed at the end-user
- ``resolution``  – actionable fix steps
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


# ── Severity ─────────────────────────────────────────────────────
class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


# ── Structured Error ─────────────────────────────────────────────
@dataclass(frozen=True)
class IngestionError:
    """One structured error emitted by the pipeline."""

    code: str
    severity: Severity
    summary: str
    detail: str = ""
    resolution: str = ""
    file_path: str | None = None
    context: dict = field(default_factory=dict)

    # Convenience helpers ------------------------------------------------
    def cli_message(self) -> str:
        """Compact single-line message for terminal output."""
        prefix = "⚠️ " if self.severity == Severity.WARNING else "✗ "
        file_hint = f" [{self.file_path}]" if self.file_path else ""
        return f"{prefix}{self.code}: {self.summary}{file_hint}"

    def verbose_message(self) -> str:
        """Multi-line message with resolution steps."""
        lines = [self.cli_message()]
        if self.detail:
            lines.append(f"  Detail: {self.detail}")
        if self.resolution:
            lines.append(f"  Fix:    {self.resolution}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """JSON-serializable representation (for manifest)."""
        d: dict = {
            "code": self.code,
            "severity": self.severity.value,
            "summary": self.summary,
        }
        if self.detail:
            d["detail"] = self.detail
        if self.resolution:
            d["resolution"] = self.resolution
        if self.file_path:
            d["file_path"] = self.file_path
        if self.context:
            d["context"] = self.context
        return d


# ──────────────────────────────────────────────────────────────────
# Error-code catalogue — factory helpers
# ──────────────────────────────────────────────────────────────────

# ── D: Detection / Discovery ─────────────────────────────────────

def D100_input_dir_not_found(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-D100",
        severity=Severity.ERROR,
        summary="Input directory not found",
        detail=f"The directory '{path}' does not exist or is not readable.",
        resolution=(
            "Create the directory and place source files inside, e.g.:\n"
            "  mkdir -p ingestion/<domain>\n"
            "  cp *.pdf ingestion/<domain>/"
        ),
        file_path=path,
    )

def D101_unknown_file_type(path: str, ext: str) -> IngestionError:
    return IngestionError(
        code="LFL-D101",
        severity=Severity.WARNING,
        summary=f"Unrecognised file type '{ext}' — skipped",
        detail=(
            f"'{path}' has extension '{ext}' which is not in the supported "
            "type map. The file will be ignored during ingestion."
        ),
        resolution=(
            "Rename the file with a supported extension, or convert it to a "
            "supported format (pdf, docx, xlsx, html, txt, md)."
        ),
        file_path=path,
    )

def D102_empty_input_dir(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-D102",
        severity=Severity.ERROR,
        summary="No ingestible files found in input directory",
        detail=f"'{path}' exists but contains no files with supported extensions.",
        resolution=(
            "Place PDF, DOCX, XLSX, HTML, TXT, or MD files into the directory."
        ),
        file_path=path,
    )

def D103_hidden_file_skipped(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-D103",
        severity=Severity.WARNING,
        summary="Hidden file skipped",
        detail=f"'{path}' starts with '.' and was ignored.",
        resolution="Rename the file to remove the leading dot if you want it ingested.",
        file_path=path,
    )


# ── C: Conversion ────────────────────────────────────────────────

def C200_libreoffice_not_found() -> IngestionError:
    return IngestionError(
        code="LFL-C200",
        severity=Severity.ERROR,
        summary="LibreOffice not installed — cannot convert legacy/Apple formats",
        detail=(
            "Files of type .doc, .xls, .ppt, .pages, .numbers, .key require "
            "LibreOffice for headless conversion."
        ),
        resolution=(
            "Install LibreOffice:\n"
            "  macOS:   brew install libreoffice\n"
            "  Ubuntu:  sudo apt install libreoffice\n"
            "  Windows: https://www.libreoffice.org/download/"
        ),
    )

def C201_conversion_timeout(path: str, timeout_s: int) -> IngestionError:
    return IngestionError(
        code="LFL-C201",
        severity=Severity.ERROR,
        summary=f"LibreOffice conversion timed out after {timeout_s}s",
        detail=f"'{path}' could not be converted within the timeout window.",
        resolution=(
            "The file may be very large or complex. Try:\n"
            "  1. Convert it manually in LibreOffice GUI and ingest the result.\n"
            "  2. Increase --conversion-timeout (if available)."
        ),
        file_path=path,
    )

def C202_conversion_failed(path: str, stderr: str) -> IngestionError:
    return IngestionError(
        code="LFL-C202",
        severity=Severity.ERROR,
        summary="LibreOffice conversion failed",
        detail=f"'{path}' conversion produced an error:\n  {stderr[:300]}",
        resolution=(
            "Try opening the file in LibreOffice manually. If it opens, "
            "export it to the target format by hand and re-ingest."
        ),
        file_path=path,
        context={"stderr": stderr[:500]},
    )

def C203_conversion_output_missing(path: str, expected: str) -> IngestionError:
    return IngestionError(
        code="LFL-C203",
        severity=Severity.ERROR,
        summary="Conversion succeeded but output file not found",
        detail=(
            f"LibreOffice reported success for '{path}' but the expected "
            f"output '{expected}' does not exist."
        ),
        resolution="This is usually a LibreOffice path-mapping issue. Try converting manually.",
        file_path=path,
        context={"expected_output": expected},
    )


# ── E: Extraction ────────────────────────────────────────────────

def E100_no_content_extracted(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-E100",
        severity=Severity.ERROR,
        summary="No text or tables could be extracted",
        detail=(
            f"All extraction attempts (native + OCR) returned empty content "
            f"for '{path}'. This usually means the file is corrupted or "
            f"image-only with damaged image streams."
        ),
        resolution=(
            "1. Open the file in its native application — if it is unreadable "
            "   there too, the source is corrupt and must be re-obtained.\n"
            "2. If the file is a scanned PDF that opens fine visually, the "
            "   internal image streams may use unsupported compression. Try "
            "   re-exporting with 'Print to PDF' from any viewer.\n"
            "3. Check `lfl ingest <domain> --inventory` for the file's "
            "   SHA256 hash and compare with your original source."
        ),
        file_path=path,
    )

def E101_pdf_stream_corruption(path: str, page_count: int) -> IngestionError:
    return IngestionError(
        code="LFL-E101",
        severity=Severity.ERROR,
        summary="PDF contains corrupted image/content streams (zlib error)",
        detail=(
            f"'{path}' has {page_count} page(s) but every content stream "
            f"fails zlib decompression ('incorrect header check'). The file's "
            f"internal compression is irreparably damaged — no PDF library or "
            f"OCR engine can recover the content."
        ),
        resolution=(
            "The source file must be re-obtained or re-created:\n"
            "  1. Re-download from the original publisher.\n"
            "  2. If you have the physical book, re-scan it.\n"
            "  3. If another copy exists, compare SHA256 hashes.\n"
            "  4. Verify the download was not interrupted or "
            "     transcoded (e.g. UTF-8 re-encoding of binary data)."
        ),
        file_path=path,
        context={"page_count": page_count},
    )

def E102_ocr_unavailable(path: str, reason: str) -> IngestionError:
    return IngestionError(
        code="LFL-E102",
        severity=Severity.WARNING,
        summary="OCR fallback unavailable",
        detail=f"Could not OCR '{path}': {reason}",
        resolution=(
            "Install OCR dependencies:\n"
            "  pip install 'lfl[ocr]'          # pytesseract + Pillow\n"
            "  sudo apt install tesseract-ocr   # system binary"
        ),
        file_path=path,
    )

def E103_partial_extraction(path: str, pages_ok: int, pages_total: int) -> IngestionError:
    return IngestionError(
        code="LFL-E103",
        severity=Severity.WARNING,
        summary=f"Partial extraction — {pages_ok}/{pages_total} pages produced text",
        detail=(
            f"'{path}' has {pages_total} pages but only {pages_ok} yielded "
            f"text. Some pages may be images, blank, or have corrupt streams."
        ),
        resolution=(
            "Review the generated chunks to assess content coverage. "
            "If critical content is missing, try re-exporting the PDF with "
            "'Print to PDF' or supply a different copy."
        ),
        file_path=path,
        context={"pages_ok": pages_ok, "pages_total": pages_total},
    )

def E104_pymupdf_not_installed(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-E104",
        severity=Severity.WARNING,
        summary="PyMuPDF not installed — falling back to pdfplumber",
        detail=f"Primary PDF extractor unavailable for '{path}'.",
        resolution="pip install pymupdf",
        file_path=path,
    )

def E105_pdfplumber_not_installed(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-E105",
        severity=Severity.WARNING,
        summary="pdfplumber not installed — table extraction unavailable",
        detail=f"Table detection unavailable for '{path}'.",
        resolution="pip install pdfplumber",
        file_path=path,
    )

def E106_extractor_exception(path: str, extractor: str, exc: str) -> IngestionError:
    return IngestionError(
        code="LFL-E106",
        severity=Severity.ERROR,
        summary=f"{extractor} extraction failed with unexpected error",
        detail=f"'{path}': {exc[:300]}",
        resolution=(
            "This may be a malformed file. Try opening it in its native "
            "application. If the file is valid, please file a bug report."
        ),
        file_path=path,
        context={"extractor": extractor, "exception": exc[:500]},
    )

def E110_docx_not_installed() -> IngestionError:
    return IngestionError(
        code="LFL-E110",
        severity=Severity.ERROR,
        summary="python-docx not installed — cannot extract DOCX",
        resolution="pip install python-docx",
    )

def E111_pandas_not_installed() -> IngestionError:
    return IngestionError(
        code="LFL-E111",
        severity=Severity.ERROR,
        summary="pandas/openpyxl not installed — cannot extract XLSX",
        resolution="pip install pandas openpyxl",
    )

def E112_bs4_not_installed() -> IngestionError:
    return IngestionError(
        code="LFL-E112",
        severity=Severity.ERROR,
        summary="beautifulsoup4 not installed — cannot extract HTML",
        resolution="pip install beautifulsoup4 lxml",
    )

def E113_encoding_fallback(path: str, final_encoding: str) -> IngestionError:
    return IngestionError(
        code="LFL-E113",
        severity=Severity.WARNING,
        summary=f"UTF-8 decode failed — fell back to {final_encoding}",
        detail=f"'{path}' is not valid UTF-8. Content was decoded with replacement characters.",
        resolution=(
            "Convert the file to UTF-8 before ingesting:\n"
            "  iconv -f <encoding> -t utf-8 input.txt > output.txt"
        ),
        file_path=path,
    )


# ── K: Chunking / Frontmatter ────────────────────────────────────

def K300_no_frontmatter(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-K300",
        severity=Severity.ERROR,
        summary="Chunk file does not begin with YAML frontmatter ('---')",
        detail=f"'{path}' is missing the required opening '---' delimiter.",
        resolution="Ensure the file starts with '---\\n' followed by YAML.",
        file_path=path,
    )

def K301_frontmatter_parse_error(path: str, yaml_error: str) -> IngestionError:
    return IngestionError(
        code="LFL-K301",
        severity=Severity.ERROR,
        summary="Invalid YAML frontmatter",
        detail=(
            f"'{path}' — parser error:\n  {yaml_error[:300]}\n\n"
            "Common causes: unescaped double-quotes in title or source fields, "
            "tabs instead of spaces, or missing closing '---'."
        ),
        resolution=(
            "Edit the chunk and fix the YAML. Typical fix: replace inner "
            '\" with \\\\" inside double-quoted values, e.g.:\n'
            '  title: "The \\"lowest\\" part of the stack"'
        ),
        file_path=path,
    )

def K302_missing_required_field(path: str, field: str) -> IngestionError:
    return IngestionError(
        code="LFL-K302",
        severity=Severity.ERROR,
        summary=f"Missing or empty required field: '{field}'",
        detail=f"'{path}' frontmatter is missing '{field}'.",
        resolution=f"Add '{field}' to the YAML frontmatter.",
        file_path=path,
    )

def K303_wrong_field_type(
    path: str, field: str, expected: str, got: str,
) -> IngestionError:
    return IngestionError(
        code="LFL-K303",
        severity=Severity.ERROR,
        summary=f"Field '{field}' has wrong type (expected {expected}, got {got})",
        detail=f"'{path}': field '{field}' parsed as {got}.",
        resolution=f"Change '{field}' to the correct type ({expected}).",
        file_path=path,
    )

def K304_importance_out_of_range(path: str, value: float) -> IngestionError:
    return IngestionError(
        code="LFL-K304",
        severity=Severity.ERROR,
        summary=f"'importance' must be 0.0–1.0, got {value}",
        file_path=path,
        resolution="Set 'importance' to a float between 0.0 and 1.0.",
    )

def K305_empty_body(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-K305",
        severity=Severity.WARNING,
        summary="Chunk has empty body content (only frontmatter)",
        file_path=path,
        resolution="Check if the source document produced empty text for this section.",
    )


# ── V: Validation ────────────────────────────────────────────────

def V400_sources_json_missing(corpus_dir: str) -> IngestionError:
    return IngestionError(
        code="LFL-V400",
        severity=Severity.WARNING,
        summary="sources.json not found in corpus directory",
        detail=f"'{corpus_dir}' has no sources.json.",
        resolution="Run `lfl ingest <domain>` to generate sources.json.",
        file_path=corpus_dir,
    )

def V401_sources_json_invalid(corpus_dir: str, reason: str) -> IngestionError:
    return IngestionError(
        code="LFL-V401",
        severity=Severity.ERROR,
        summary="sources.json is malformed",
        detail=f"'{corpus_dir}/sources.json': {reason}",
        resolution="Fix or regenerate sources.json by re-running ingestion.",
        file_path=corpus_dir,
    )

def V402_orphaned_source(source_id: str) -> IngestionError:
    return IngestionError(
        code="LFL-V402",
        severity=Severity.WARNING,
        summary=f"Source '{source_id}' defined but never referenced by any chunk",
        resolution="Remove the stale entry from sources.json or re-ingest.",
        context={"source_id": source_id},
    )

def V403_unknown_source_ref(path: str, source_id: str) -> IngestionError:
    return IngestionError(
        code="LFL-V403",
        severity=Severity.ERROR,
        summary=f"Chunk references unknown source_id '{source_id}'",
        detail=f"'{path}' says source_id='{source_id}' but no matching entry in sources.json.",
        resolution="Add the source to sources.json or re-run ingestion.",
        file_path=path,
    )

def V404_duplicate_source_id(source_id: str) -> IngestionError:
    return IngestionError(
        code="LFL-V404",
        severity=Severity.ERROR,
        summary=f"Duplicate source ID '{source_id}' in sources.json",
        resolution="Remove or rename the duplicate entry.",
        context={"source_id": source_id},
    )


# ── M: Embedding / Model ─────────────────────────────────────────

def M500_profile_not_found(profile_id: str) -> IngestionError:
    return IngestionError(
        code="LFL-M500",
        severity=Severity.ERROR,
        summary=f"Embedding profile '{profile_id}' not found",
        resolution=(
            "List available profiles:\n"
            "  ls lfl/profiles/\n"
            "Or use: --profile baseline_cpu_onnx_small"
        ),
        context={"profile_id": profile_id},
    )

def M501_model_load_failed(profile_id: str, exc: str) -> IngestionError:
    return IngestionError(
        code="LFL-M501",
        severity=Severity.ERROR,
        summary="Embedding model failed to load",
        detail=f"Profile '{profile_id}': {exc[:300]}",
        resolution=(
            "Ensure model files exist under models/. Run:\n"
            "  python scripts/download_fastembed_models.py"
        ),
        context={"profile_id": profile_id, "exception": exc[:500]},
    )

def M502_embedding_dimension_mismatch(
    expected: int, got: int, profile_id: str,
) -> IngestionError:
    return IngestionError(
        code="LFL-M502",
        severity=Severity.ERROR,
        summary=f"Vector dimension mismatch: expected {expected}, got {got}",
        detail=f"Profile '{profile_id}' should produce {expected}-dim vectors.",
        resolution="Check that the correct model is loaded for this profile.",
        context={"expected": expected, "got": got, "profile_id": profile_id},
    )

def M503_encoding_failed(path: str, exc: str) -> IngestionError:
    return IngestionError(
        code="LFL-M503",
        severity=Severity.ERROR,
        summary="Embedding encoding failed",
        detail=f"Error while encoding chunks from '{path}': {exc[:300]}",
        resolution="Check available memory and model integrity.",
        file_path=path,
    )


# ── P: Pipeline / Orchestration ──────────────────────────────────

def P600_duplicate_skipped(path: str, sha256: str) -> IngestionError:
    return IngestionError(
        code="LFL-P600",
        severity=Severity.WARNING,
        summary="File skipped — duplicate content hash already in corpus",
        detail=f"'{path}' (sha256:{sha256[:16]}…) matches existing chunks.",
        resolution="Use --on-duplicate overwrite to replace, or skip (default).",
        file_path=path,
        context={"sha256": sha256},
    )

def P601_zero_chunks_from_file(path: str) -> IngestionError:
    return IngestionError(
        code="LFL-P601",
        severity=Severity.WARNING,
        summary="File produced zero chunks after extraction + splitting",
        detail=(
            f"'{path}' was extracted successfully but the chunker produced "
            f"no output. The text may be too short or entirely whitespace."
        ),
        resolution="Check the extracted text length; very short documents may be below the chunk threshold.",
        file_path=path,
    )

def P602_manifest_write_failed(path: str, exc: str) -> IngestionError:
    return IngestionError(
        code="LFL-P602",
        severity=Severity.ERROR,
        summary="Could not write ingestion manifest",
        detail=f"Failed to write '{path}': {exc}",
        resolution="Check disk space and directory permissions.",
        file_path=path,
    )

def P603_unexpected_pipeline_error(path: str, stage: str, exc: str) -> IngestionError:
    return IngestionError(
        code="LFL-P603",
        severity=Severity.ERROR,
        summary=f"Unexpected error in stage '{stage}'",
        detail=f"'{path}': {exc[:300]}",
        resolution="This is likely a bug. Please file an issue with the full traceback.",
        file_path=path,
        context={"stage": stage, "exception": exc[:500]},
    )


# ──────────────────────────────────────────────────────────────────
# Registry — look up any code by string
# ──────────────────────────────────────────────────────────────────

# Quick lookup for user-facing docs / CLI help.
# Maps code → (summary, resolution) for static reference.
ERROR_CATALOGUE: dict[str, tuple[str, str]] = {
    "LFL-D100": ("Input directory not found", "Create the directory with source files"),
    "LFL-D101": ("Unrecognised file type — skipped", "Rename or convert to supported format"),
    "LFL-D102": ("No ingestible files in directory", "Add PDF/DOCX/XLSX/HTML/TXT/MD files"),
    "LFL-D103": ("Hidden file skipped", "Remove leading dot from filename"),
    "LFL-C200": ("LibreOffice not installed", "Install LibreOffice (apt/brew)"),
    "LFL-C201": ("Conversion timed out", "Convert manually or increase timeout"),
    "LFL-C202": ("Conversion failed", "Open file manually in LibreOffice"),
    "LFL-C203": ("Conversion output missing", "Convert file manually"),
    "LFL-E100": ("No content extracted", "File may be corrupt — re-obtain source"),
    "LFL-E101": ("Corrupt PDF streams (zlib)", "Source has damaged compression — re-download"),
    "LFL-E102": ("OCR unavailable", "pip install 'lfl[ocr]' + apt install tesseract-ocr"),
    "LFL-E103": ("Partial extraction", "Some pages are image-only — review chunks"),
    "LFL-E104": ("PyMuPDF not installed", "pip install pymupdf"),
    "LFL-E105": ("pdfplumber not installed", "pip install pdfplumber"),
    "LFL-E106": ("Extractor exception", "File may be malformed — try opening manually"),
    "LFL-E110": ("python-docx not installed", "pip install python-docx"),
    "LFL-E111": ("pandas/openpyxl not installed", "pip install pandas openpyxl"),
    "LFL-E112": ("beautifulsoup4 not installed", "pip install beautifulsoup4 lxml"),
    "LFL-E113": ("Encoding fallback", "Convert file to UTF-8"),
    "LFL-K300": ("Missing YAML frontmatter", "Add opening '---' delimiter"),
    "LFL-K301": ("YAML parse error", "Fix unescaped quotes or syntax in frontmatter"),
    "LFL-K302": ("Missing required field", "Add the field to frontmatter"),
    "LFL-K303": ("Wrong field type", "Correct the field type in frontmatter"),
    "LFL-K304": ("importance out of range", "Set importance between 0.0 and 1.0"),
    "LFL-K305": ("Empty body content", "Source may have produced blank text"),
    "LFL-V400": ("sources.json missing", "Run `lfl ingest <domain>` to generate"),
    "LFL-V401": ("sources.json malformed", "Fix or regenerate via re-ingestion"),
    "LFL-V402": ("Orphaned source entry", "Remove stale source from sources.json"),
    "LFL-V403": ("Unknown source_id ref", "Add source to sources.json"),
    "LFL-V404": ("Duplicate source ID", "Remove duplicate in sources.json"),
    "LFL-M500": ("Profile not found", "Check lfl/profiles/ for available profiles"),
    "LFL-M501": ("Model load failed", "Download model files (see setup docs)"),
    "LFL-M502": ("Dimension mismatch", "Verify correct model for profile"),
    "LFL-M503": ("Encoding failed", "Check memory and model integrity"),
    "LFL-P600": ("Duplicate skipped", "Use --on-duplicate overwrite to replace"),
    "LFL-P601": ("Zero chunks produced", "Text may be too short to chunk"),
    "LFL-P602": ("Manifest write failed", "Check disk space and permissions"),
    "LFL-P603": ("Unexpected pipeline error", "File a bug report with traceback"),
}


def lookup_error_code(code: str) -> tuple[str, str] | None:
    """Look up (summary, resolution) for an error code. Returns None if unknown."""
    return ERROR_CATALOGUE.get(code.upper())


def format_error_reference() -> str:
    """Format the full error catalogue as a Markdown table for docs/CLI help."""
    lines = [
        "| Code | Summary | Resolution |",
        "|------|---------|------------|",
    ]
    for code, (summary, resolution) in sorted(ERROR_CATALOGUE.items()):
        lines.append(f"| `{code}` | {summary} | {resolution} |")
    return "\n".join(lines)
