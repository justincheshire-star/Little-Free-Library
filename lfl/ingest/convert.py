"""
Document conversion utilities (LibreOffice, Pandoc wrappers).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Literal


def has_libreoffice() -> bool:
    """Check if LibreOffice (soffice) is available in PATH."""
    return shutil.which('soffice') is not None


def has_pandoc() -> bool:
    """Check if Pandoc is available in PATH."""
    return shutil.which('pandoc') is not None


def convert_with_libreoffice(
    input_path: Path,
    output_dir: Path,
    target_format: Literal['pdf', 'docx', 'xlsx'] = 'pdf',
    timeout: int = 300,
) -> Path:
    """
    Convert document using LibreOffice headless mode.
    
    Args:
        input_path: Source file (Pages, Numbers, Keynote, legacy Office)
        output_dir: Directory for converted file
        target_format: Output format (pdf, docx, xlsx)
        timeout: Conversion timeout in seconds
        
    Returns:
        Path to converted file
        
    Raises:
        FileNotFoundError: LibreOffice not installed
        subprocess.TimeoutExpired: Conversion timed out
        RuntimeError: Conversion failed
    """
    if not has_libreoffice():
        raise FileNotFoundError(
            "LibreOffice not found. Install with:\n"
            "  macOS: brew install libreoffice\n"
            "  Ubuntu: sudo apt install libreoffice\n"
            "  Windows: Download from https://www.libreoffice.org/"
        )
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'soffice',
        '--headless',
        '--convert-to', target_format,
        '--outdir', str(output_dir),
        str(input_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
    except subprocess.TimeoutExpired:
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=timeout,
            output=f"LibreOffice conversion timed out after {timeout}s",
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"LibreOffic conversion failed:\n{e.stderr}"
        )
    
    # Find converted file
    expected_name = input_path.stem + f'.{target_format}'
    converted_path = output_dir / expected_name
    
    if not converted_path.exists():
        raise RuntimeError(
            f"Conversion succeeded but output file not found: {converted_path}"
        )
    
    return converted_path


def needs_conversion(file_type: str) -> bool:
    """Check if file type needs conversion before extraction."""
    conversion_types = {
        'pages', 'numbers', 'keynote',
        'doc_legacy', 'xls_legacy', 'ppt_legacy',
    }
    return file_type in conversion_types


def get_conversion_target(file_type: str) -> Literal['pdf', 'docx', 'xlsx']:
    """Determine optimal conversion target format."""
    target_map = {
        'pages': 'pdf',
        'numbers': 'xlsx',
        'keynote': 'pdf',
        'doc_legacy': 'docx',
        'xls_legacy': 'xlsx',
        'ppt_legacy': 'pdf',
    }
    return target_map.get(file_type, 'pdf')
