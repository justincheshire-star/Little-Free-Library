# Ingestion Drop Folder

This directory is where you place documents for ingestion into LFL corpora.

## ⚠️ Important

**This directory is gitignored and never committed.**  
Place your source documents here temporarily during ingestion only.

## Structure

```
ingestion/
└── <domain>/
    └── (your documents here)
```

## Usage

```bash
# 1. Create a domain folder
mkdir -p ingestion/programming

# 2. Copy your documents
cp ~/Downloads/*.pdf ingestion/programming/

# 3. Run ingestion
lfl ingest programming

# 4. Check output
ls corpora/programming/chunks/
cat ingestion_out/programming/manifest.json
```

## Supported Formats

- **PDFs** (with text or OCR)
- **Microsoft Office:** DOCX, XLSX, PPTX
- **Apple iWork:** Pages, Numbers, Keynote (requires LibreOffice)
- **Web:** HTML
- **Plain text:** TXT, MD
- **Legacy Office:** DOC, XLS, PPT (requires LibreOffice)

## System Prerequisites

For full format support:

```bash
# macOS
brew install libreoffice tesseract

# Ubuntu/Debian
sudo apt install libreoffice tesseract-ocr

# Windows
# Download LibreOffice from https://www.libreoffice.org/
# Download Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
```

## What Happens During Ingestion

1. **Discovery** — Scans this folder recursively
2. **Type Detection** — MIME detection + extension fallback
3. **Conversion** — Pages/Numbers → PDF/XLSX (if LibreOffice available)
4. **Extraction** — Text and tables extracted
5. **Chunking** — Documents split into semantic chunks
6. **Validation** — Metadata and structure validated
7. **Output** — Final corpus written to `corpora/<domain>/`

## Cleanup

After ingestion, you can safely delete files from this directory:

```bash
# Remove input files after successful ingestion
rm -rf ingestion/programming/*

# Or keep them as backup (they won't be committed)
```

## Notes

- **License Responsibility:** You must verify that source documents are licensed for use in your corpus. Ingestion defaults `source_license: unknown` — update metadata before publishing.
- **Privacy:** Never commit documents with PII, credentials, or sensitive data.
- **Size Limits:** Very large files (>100MB) may timeout during conversion. Split them manually if needed.
