# Ingestion Output Artifacts

This directory contains generated artifacts from ingestion runs.

## ⚠️ Important

**This directory is gitignored and never committed.**  
Artifacts here are ephemeral and regenerable.

## Structure

```
ingestion_out/
└── <domain>/
    ├── converted/        # LibreOffice/Pandoc conversion outputs
    ├── extracted/        # Pre-chunking normalized text (future)
    └── manifest.json    # Run report
```

## Manifest Schema

Each ingestion run produces a manifest:

```json
{
  "run_id": "20260227_143022",
  "domain": "programming",
  "timestamp": "2026-02-27T14:30:22Z",
  "stats": {
    "files_discovered": 45,
    "files_converted": 3,
    "files_extracted": 45,
    "chunks_created": 287,
    "failures": 0
  },
  "files": [
    {
      "path": "ingestion/programming/python_guide.pdf",
      "sha256": "4b3a2f...",
      "detected_type": "pdf",
      "extraction_method": "native",
      "chunks_produced": 12,
      "status": "success"
    }
  ],
  "warnings": []
}
```

## Cleanup

These artifacts can be deleted anytime:

```bash
# Clean specific domain
rm -rf ingestion_out/programming/

# Clean everything
rm -rf ingestion_out/
```

The manifest is useful for troubleshooting failed ingestions.

## Troubleshooting

If ingestion fails, check the manifest for:

- **status: "failed"** — Files that couldn't be processed
- **error** — Specific error message
- **warnings** — Non-fatal issues (missing dependencies, etc.)

Common issues:

```json
{
  "status": "failed",
  "error": "LibreOffice not found. Install with: brew install libreoffice"
}
```

```json
{
  "status": "success",
  "warnings": ["OCR fallback unavailable: pytesseract not installed"]
}
```
