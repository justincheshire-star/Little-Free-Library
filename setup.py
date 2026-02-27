"""Setup script for Little Free Library."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

# Optional dependency groups for document ingestion
extras_require = {
    # Common document formats (no ML dependencies)
    'ingest': [
        'python-magic>=0.4.27; platform_system!="Windows"',
        'puremagic>=1.15; platform_system=="Windows"',
        'charset-normalizer>=3.2',
        'beautifulsoup4>=4.12',
        'lxml>=4.9',
        'python-docx>=1.1.0',
        'openpyxl>=3.1.0',
        'pandas>=2.0.0',
    ],
    
    # PDF text extraction
    'pdf': [
        'pymupdf>=1.23.0',
        'pdfplumber>=0.11.0',
    ],
    
    # OCR support for scanned documents
    'ocr': [
        'pytesseract>=0.3.10',
        'Pillow>=10.0.0',
    ],
    
    # Universal document conversion utilities
    'convert': [
        'pypandoc>=1.12',
    ],
    
    # Encrypted Office file support
    'office_crypto': [
        'msoffcrypto-tool>=5.0.0',
    ],
    
    # Development dependencies
    'dev': [
        'pytest>=7.0',
        'pytest-cov>=4.0',
        'black>=23.0',
        'isort>=5.12',
        'flake8>=6.0',
        'mypy>=1.0',
    ],
    
    # Documentation build
    'docs': [
        'sphinx>=7.0.0',
        'sphinx-rtd-theme>=2.0.0',
        'myst-parser>=2.0.0',
    ],
}

# Convenience bundle for complete ingestion support
extras_require['all_ingest'] = [
    dep
    for group in ['ingest', 'pdf', 'ocr', 'convert', 'office_crypto']
    for dep in extras_require[group]
]

# Full development environment
extras_require['all'] = [
    dep
    for group in extras_require.values()
    if isinstance(group, list)
    for dep in group
]

setup(
    name="little-free-library",
    version="1.0.0",
    description="Corpus curation and RAG validation toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Little Free Library Contributors",
    url="https://github.com/justincheshire-star/Little-Free-Library",
    license="Apache 2.0 with Commons Clause",
    packages=find_packages(include=["lfl", "lfl.*"]),
    package_data={
        "lfl": ["profiles/*.json"],
    },
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "lfl=lfl.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="corpus rag retrieval benchmark validation nlp document-ingestion",
)
