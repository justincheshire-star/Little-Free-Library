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
    keywords="corpus rag retrieval benchmark validation nlp",
)
