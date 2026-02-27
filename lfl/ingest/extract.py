"""
Format-specific content extractors.

Each extractor returns an ExtractedDoc with text, tables, and metadata.
"""

from __future__ import annotations

from pathlib import Path

from .types import ExtractedDoc, ExtractedTable


def extract_text(path: Path, file_type: str) -> ExtractedDoc:
    """
    Extract content from any supported file type.
    
    Dispatches to format-specific extractor.
    """
    extractors = {
        'pdf': extract_pdf,
        'docx': extract_docx,
        'xlsx': extract_xlsx,
        'html': extract_html,
        'text': extract_plain_text,
        'markdown': extract_plain_text,
    }
    
    extractor = extractors.get(file_type, extract_plain_text)
    return extractor(path)


def extract_pdf(path: Path) -> ExtractedDoc:
    """
    Extract text from PDF with fallback chain.
    
    1. Try PyMuPDF (fast)
    2. Fallback to pdfplumber (better tables)
    3. Fallback to OCR (if available and text empty)
    """
    text = ""
    tables = []
    method = "native"
    warnings = []
    
    # Try PyMuPDF first
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        text = "\n\n".join(pages)
        doc.close()
        
    except ImportError:
        warnings.append("PyMuPDF not installed (pip install pymupdf)")
    except Exception as e:
        warnings.append(f"PyMuPDF extraction failed: {e}")
    
    # Fallback to pdfplumber if no text extracted
    if not text.strip():
        try:
            import pdfplumber
            
            with pdfplumber.open(path) as pdf:
                pages = []
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")
                    
                    # Extract tables
                    for table in page.extract_tables():
                        if table:
                            # Convert to markdown-ish
                            md_table = _table_to_markdown(table)
                            tables.append(ExtractedTable(
                                sheet_name=None,
                                data=[],  # TODO: convert to dict format
                                markdown=md_table,
                            ))
                
                text = "\n\n".join(pages)
        
        except ImportError:
            warnings.append("pdfplumber not installed (pip install pdfplumber)")
        except Exception as e:
            warnings.append(f"pdfplumber extraction failed: {e}")
    
    # OCR fallback if still empty
    if not text.strip():
        try:
            text = extract_pdf_ocr(path)
            method = "ocr"
        except Exception as e:
            warnings.append(f"OCR fallback unavailable: {e}")
    
    return ExtractedDoc(
        text=text,
        title=path.stem,
        source_path=path,
        detected_type='pdf',
        extraction_method=method,
        tables=tables,
        warnings=warnings,
    )


def extract_pdf_ocr(path: Path) -> str:
    """Extract text from PDF using OCR (Tesseract)."""
    try:
        import pytesseract
        from PIL import Image
        import fitz  # PyMuPDF for page -> image
        
        doc = fitz.open(path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
            pages.append(text)
        
        doc.close()
        return "\n\n".join(pages)
    
    except ImportError:
        raise ImportError(
            "OCR dependencies not installed. "
            "Install with: pip install 'lfl[ocr]'"
        )


def extract_docx(path: Path) -> ExtractedDoc:
    """Extract text and tables from DOCX."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx not installed (pip install python-docx)")
    
    doc = Document(path)
    
    # Extract paragraphs
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    
    # Extract tables
    tables = []
    for table in doc.tables:
        rows = []
        for row in table.rows:
            rows.append([cell.text for cell in row.cells])
        
        if rows:
            md_table = _table_to_markdown(rows)
            tables.append(ExtractedTable(
                sheet_name=None,
                data=[],  # TODO: convert to dict format
                markdown=md_table,
            ))
    
    return ExtractedDoc(
        text=text,
        title=path.stem,
        source_path=path,
        detected_type='docx',
        extraction_method='native',
        tables=tables,
    )


def extract_xlsx(path: Path) -> ExtractedDoc:
    """Extract tables from Excel."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas not installed (pip install pandas openpyxl)")
    
    sheets = pd.read_excel(path, sheet_name=None, engine='openpyxl')
    
    tables = []
    for sheet_name, df in sheets.items():
        if not df.empty:
            tables.append(ExtractedTable(
                sheet_name=sheet_name,
                data=df.to_dict('records'),
                markdown=df.to_markdown(index=False),
            ))
    
    # Generate text summary
    text_parts = []
    for table in tables:
        text_parts.append(f"# Sheet: {table.sheet_name}\n\n{table.markdown}")
    
    text = "\n\n".join(text_parts)
    
    return ExtractedDoc(
        text=text,
        title=path.stem,
        source_path=path,
        detected_type='xlsx',
        extraction_method='native',
        tables=tables,
    )


def extract_html(path: Path) -> ExtractedDoc:
    """Extract text from HTML."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("beautifulsoup4 not installed (pip install beautifulsoup4 lxml)")
    
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove scripts and styles
    for tag in soup(['script', 'style', 'nav', 'footer']):
        tag.decompose()
    
    # Get title
    title = None
    if soup.title:
        title = soup.title.string
    
    # Extract text
    text = soup.get_text(separator='\n\n')
    
    # Clean up whitespace
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return ExtractedDoc(
        text=text,
        title=title or path.stem,
        source_path=path,
        detected_type='html',
        extraction_method='native',
    )


def extract_plain_text(path: Path) -> ExtractedDoc:
    """Extract from plain text files."""
    # Try different encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(path, 'r', encoding=encoding) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        # Last resort: binary read with replace
        with open(path, 'rb') as f:
            text = f.read().decode('utf-8', errors='replace')
    
    return ExtractedDoc(
        text=text,
        title=path.stem,
        source_path=path,
        detected_type='text',
        extraction_method='native',
    )


def _table_to_markdown(rows: list[list[str]]) -> str:
    """Convert table rows to Markdown format."""
    if not rows:
        return ""
    
    # Header
    header = "| " + " | ".join(str(cell) for cell in rows[0]) + " |"
    separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
    
    # Body
    body = []
    for row in rows[1:]:
        body.append("| " + " | ".join(str(cell) for cell in row) + " |")
    
    return "\n".join([header, separator] + body)
