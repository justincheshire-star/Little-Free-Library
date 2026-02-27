"""
Document conversion utilities (LibreOffice, Pandoc wrappers).

Raises structured IngestionError codes (LFL-C2xx) on failure.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Literal

from .errors import (
    C200_libreoffice_not_found,
    C201_conversion_timeout,
    C202_conversion_failed,
    C203_conversion_output_missing,
    IngestionError,
)


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
        FileNotFoundError: LibreOffice not installed (LFL-C200)
        subprocess.TimeoutExpired: Conversion timed out (LFL-C201)
        RuntimeError: Conversion failed (LFL-C202, LFL-C203)
    """
    if not has_libreoffice():
        err = C200_libreoffice_not_found()
        raise FileNotFoundError(err.verbose_message())
    
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
        err = C201_conversion_timeout(str(input_path), timeout)
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=timeout,
            output=err.verbose_message(),
        )
    except subprocess.CalledProcessError as e:
        err = C202_conversion_failed(str(input_path), e.stderr or "")
        raise RuntimeError(err.verbose_message()) from e
    
    # Find converted file
    expected_name = input_path.stem + f'.{target_format}'
    converted_path = output_dir / expected_name
    
    if not converted_path.exists():
        err = C203_conversion_output_missing(str(input_path), str(converted_path))
        raise RuntimeError(err.verbose_message())
    
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
