# LFL Ingestion Error Code Reference

Every error or warning the ingestion pipeline can produce is assigned a **unique, structured code** of the form `LFL-XNNN`.

## Quick Commands

```bash
# List all codes
lfl error-codes

# Explain a specific code
lfl explain-error LFL-E101
```

## Code Categories

| Prefix | Category | Description |
|--------|----------|-------------|
| `LFL-D1xx` | **Detection** | File discovery, type detection, input directory |
| `LFL-C2xx` | **Conversion** | LibreOffice / Pandoc document conversion |
| `LFL-E1xx` | **Extraction** | PDF, DOCX, XLSX, HTML, TXT, OCR content extraction |
| `LFL-K3xx` | **Chunking** | YAML frontmatter, chunk structure, metadata |
| `LFL-V4xx` | **Validation** | Corpus validation, sources.json integrity |
| `LFL-M5xx` | **Embedding** | Model loading, encoding, dimension checks |
| `LFL-P6xx` | **Pipeline** | Orchestration, dedup, manifest writing |

---

## Detection Errors (LFL-D1xx)

### LFL-D100 — Input directory not found
- **Severity:** Error
- **Cause:** The specified ingestion input directory does not exist.
- **Fix:** Create the directory and place source files inside:
  ```bash
  mkdir -p ingestion/<domain>
  cp *.pdf ingestion/<domain>/
  ```

### LFL-D101 — Unrecognised file type
- **Severity:** Warning
- **Cause:** File extension is not in the supported type map.
- **Fix:** Rename with a supported extension or convert to PDF/DOCX/XLSX/HTML/TXT/MD.

### LFL-D102 — No ingestible files found
- **Severity:** Error
- **Cause:** Input directory exists but contains no supported file types.
- **Fix:** Add files with supported extensions (`.pdf`, `.docx`, `.xlsx`, `.html`, `.txt`, `.md`).

### LFL-D103 — Hidden file skipped
- **Severity:** Warning
- **Cause:** Filename starts with `.` (e.g., `.DS_Store`).
- **Fix:** Rename to remove the leading dot if the file should be ingested.

---

## Conversion Errors (LFL-C2xx)

### LFL-C200 — LibreOffice not installed
- **Severity:** Error
- **Cause:** `.doc`, `.xls`, `.ppt`, `.pages`, `.numbers`, `.key` files require LibreOffice.
- **Fix:**
  ```bash
  # Ubuntu/Debian
  sudo apt install libreoffice
  # macOS
  brew install libreoffice
  ```

### LFL-C201 — Conversion timed out
- **Severity:** Error
- **Cause:** LibreOffice headless conversion exceeded the timeout (default 300s).
- **Fix:** Convert the file manually in LibreOffice GUI and ingest the result.

### LFL-C202 — Conversion failed
- **Severity:** Error
- **Cause:** LibreOffice returned a non-zero exit code.
- **Fix:** Open the file manually in LibreOffice. If it opens, export to the target format by hand.

### LFL-C203 — Conversion output missing
- **Severity:** Error
- **Cause:** LibreOffice reported success but the expected output file wasn't created.
- **Fix:** Convert the file manually. This is typically a path-mapping or permissions issue.

---

## Extraction Errors (LFL-E1xx)

### LFL-E100 — No content extracted
- **Severity:** Error
- **Cause:** All extraction methods (native + OCR) returned empty content.
- **Fix:**
  1. Open the file in its native application — if unreadable, the source is corrupt.
  2. For scanned PDFs, try re-exporting with "Print to PDF."
  3. Compare the SHA256 hash with the original source.

### LFL-E101 — Corrupt PDF streams (zlib error)
- **Severity:** Error
- **Cause:** The PDF contains image/content streams with damaged zlib compression. Every page's internal data fails decompression (`incorrect header check`). This is **irrecoverable** — no PDF library or OCR can extract content.
- **Common Causes:**
  - Download was interrupted or corrupted during transfer
  - Binary PDF data was transcoded through a UTF-8 text pipeline
  - Storage medium corruption (disk/cloud sync errors)
- **Fix:**
  1. **Re-download** from the original publisher.
  2. If you have the physical book, re-scan it.
  3. Compare SHA256 hashes with a known-good copy.
  4. Verify the download process preserves binary data (no text encoding).

### LFL-E102 — OCR fallback unavailable
- **Severity:** Warning
- **Cause:** Image-based PDF detected but OCR dependencies are missing.
- **Fix:**
  ```bash
  pip install 'lfl[ocr]'           # pytesseract + Pillow
  sudo apt install tesseract-ocr    # system binary
  ```

### LFL-E103 — Partial extraction
- **Severity:** Warning
- **Cause:** Some pages produced text but others were blank (may be image-only).
- **Fix:** Review generated chunks. For missing pages, consider OCR or re-export.

### LFL-E104 — PyMuPDF not installed
- **Severity:** Warning
- **Cause:** Primary PDF extractor unavailable; falling back to pdfplumber.
- **Fix:** `pip install pymupdf`

### LFL-E105 — pdfplumber not installed
- **Severity:** Warning
- **Cause:** Table extraction unavailable for PDFs.
- **Fix:** `pip install pdfplumber`

### LFL-E106 — Extractor exception
- **Severity:** Error
- **Cause:** An unexpected error occurred during extraction.
- **Fix:** Try opening the file in its native application. If valid, file a bug report.

### LFL-E110 — python-docx not installed
- **Severity:** Error
- **Fix:** `pip install python-docx`

### LFL-E111 — pandas/openpyxl not installed
- **Severity:** Error
- **Fix:** `pip install pandas openpyxl`

### LFL-E112 — beautifulsoup4 not installed
- **Severity:** Error
- **Fix:** `pip install beautifulsoup4 lxml`

### LFL-E113 — Encoding fallback
- **Severity:** Warning
- **Cause:** UTF-8 decode failed; content decoded with a fallback encoding.
- **Fix:** Convert the file to UTF-8:
  ```bash
  iconv -f <encoding> -t utf-8 input.txt > output.txt
  ```

---

## Chunking / Frontmatter Errors (LFL-K3xx)

### LFL-K300 — Missing YAML frontmatter
- **Severity:** Error
- **Cause:** Chunk file doesn't start with `---`.
- **Fix:** Ensure the file begins with `---\n` followed by valid YAML.

### LFL-K301 — YAML parse error
- **Severity:** Error
- **Cause:** Frontmatter contains invalid YAML, typically unescaped double-quotes.
- **Fix:** Escape inner quotes:
  ```yaml
  title: "The \"lowest\" part of the stack"
  ```

### LFL-K302 — Missing required field
- **Severity:** Error
- **Cause:** A required frontmatter field is missing (title, domain, source, source_license, verified, importance, tags, version).
- **Fix:** Add the missing field to the YAML frontmatter.

### LFL-K303 — Wrong field type
- **Severity:** Error
- **Cause:** A frontmatter field has an incorrect type (e.g., `importance` is a string instead of float).
- **Fix:** Correct the field to the expected type.

### LFL-K304 — importance out of range
- **Severity:** Error
- **Cause:** `importance` is not between 0.0 and 1.0.
- **Fix:** Set to a float in the valid range.

### LFL-K305 — Empty body content
- **Severity:** Warning
- **Cause:** Chunk has frontmatter but no body text after the closing `---`.
- **Fix:** Check if the source document produced empty text for this section.

---

## Validation Errors (LFL-V4xx)

### LFL-V400 — sources.json missing
- **Severity:** Warning
- **Fix:** Run `lfl ingest <domain>` to generate sources.json.

### LFL-V401 — sources.json malformed
- **Severity:** Error
- **Fix:** Fix the JSON syntax or re-run ingestion to regenerate.

### LFL-V402 — Orphaned source entry
- **Severity:** Warning
- **Cause:** A source is defined in sources.json but no chunk references it.
- **Fix:** Remove the stale entry or re-ingest its documents.

### LFL-V403 — Unknown source_id reference
- **Severity:** Error
- **Cause:** A chunk's `source_id` doesn't match any entry in sources.json.
- **Fix:** Add the source to sources.json or re-run ingestion.

### LFL-V404 — Duplicate source ID
- **Severity:** Error
- **Fix:** Remove or rename duplicate entries in sources.json.

---

## Embedding Errors (LFL-M5xx)

### LFL-M500 — Profile not found
- **Severity:** Error
- **Fix:** List available profiles: `ls lfl/profiles/`

### LFL-M501 — Model load failed
- **Severity:** Error
- **Fix:** Download model files:
  ```bash
  python scripts/download_fastembed_models.py
  ```

### LFL-M502 — Dimension mismatch
- **Severity:** Error
- **Cause:** Model produced vectors with a different dimension than expected.
- **Fix:** Verify the correct model is loaded for the selected profile.

### LFL-M503 — Encoding failed
- **Severity:** Error
- **Fix:** Check available memory and model integrity.

---

## Pipeline Errors (LFL-P6xx)

### LFL-P600 — Duplicate skipped
- **Severity:** Warning
- **Cause:** File's content hash already exists in the corpus.
- **Fix:** Use `--on-duplicate overwrite` to replace existing chunks.

### LFL-P601 — Zero chunks produced
- **Severity:** Warning
- **Cause:** Extraction succeeded but the chunker produced no output (text may be below the minimum size threshold).
- **Fix:** Check extracted text length.

### LFL-P602 — Manifest write failed
- **Severity:** Error
- **Fix:** Check disk space and directory permissions.

### LFL-P603 — Unexpected pipeline error
- **Severity:** Error
- **Cause:** An unhandled exception occurred during processing.
- **Fix:** This is likely a bug — file an issue with the full traceback.

---

## Reading Error Codes in Output

### CLI Output
Error codes appear in console messages:
```
✗ LFL-E101: PDF contains corrupted image/content streams (zlib error) [ingestion/programming/file.pdf]
```

### Manifest JSON
Error codes are included in `ingestion_out/<domain>/manifest.json`:
```json
{
  "files": [
    {
      "path": "ingestion/programming/file.pdf",
      "status": "failed",
      "error": "...",
      "error_code": "LFL-E101",
      "structured_errors": [
        {
          "code": "LFL-E101",
          "severity": "error",
          "summary": "PDF contains corrupted image/content streams (zlib error)",
          "detail": "...",
          "resolution": "..."
        }
      ]
    }
  ]
}
```

### Validation Output
Error codes appear in validation results:
```
[LFL-K301] Invalid YAML frontmatter: ...
```

---

## Searching for Errors

```bash
# Find all errors in a manifest
jq '.files[] | select(.error_code != null) | {path, error_code, error}' ingestion_out/programming/manifest.json

# Count errors by code
jq '[.files[] | .error_code // empty] | group_by(.) | map({code: .[0], count: length})' ingestion_out/programming/manifest.json
```
