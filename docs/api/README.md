# API Documentation

Sphinx-based API reference documentation for the Little Free Library Toolkit.

## Building the Documentation

### Prerequisites

Install documentation dependencies:

```bash
pip install -r requirements.txt
```

Or install with the package:

```bash
pip install -e ".[docs]"
```

### Build HTML Documentation

```bash
cd docs/api
make html
```

The generated documentation will be in `_build/html/`.

### View Documentation Locally

```bash
make html && make serve
```

Then open http://localhost:8000 in your browser.

### Clean Build Artifacts

```bash
make clean
```

## Documentation Structure

```
docs/api/
├── conf.py                 # Sphinx configuration
├── index.rst              # Main documentation index
├── overview.rst           # Overview and architecture
├── quickstart.rst         # Quick start guide
├── cli.rst                # CLI reference
├── examples.rst           # Usage examples
├── modules/               # Module documentation
│   ├── index.rst
│   ├── chunking.rst
│   ├── retrieval.rst
│   └── ...
├── Makefile               # Build commands
└── requirements.txt       # Documentation dependencies
```

## Contributing

When adding new modules or features:

1. Update module `.rst` files in `modules/`
2. Add examples to `examples.rst`
3. Update CLI documentation in `cli.rst` if needed
4. Rebuild docs: `make clean && make html`
5. Verify all autodoc references resolve

## Autodoc Configuration

The documentation uses Sphinx autodoc to generate API reference from docstrings:

- **Style**: NumPy/Google docstring format
- **Type hints**: Extracted from function signatures
- **Examples**: Include in docstrings with code blocks
- **Cross-references**: Use `:func:`, `:class:`, `:mod:` directives

## Sphinx Extensions

- `sphinx.ext.autodoc` — Automatic API documentation from docstrings
- `sphinx.ext.napoleon` — NumPy/Google docstring support
- `sphinx.ext.viewcode` — Link to source code
- `sphinx.ext.intersphinx` — Cross-reference external docs (Python, NumPy)
- `sphinx.ext.autosummary` — Generate summary tables
- `myst_parser` — Markdown support in .rst files

## Theme

Uses Read the Docs theme (`sphinx_rtd_theme`) for clean, modern appearance.

## Deployment

Documentation can be deployed to:

- **Read the Docs** — Automatic builds from GitHub
- **GitHub Pages** — Static HTML hosting
- **Self-hosted** — Deploy `_build/html/` to any web server

## Troubleshooting

### Import Errors

If autodoc fails to import modules:

```bash
# Ensure package is installed
pip install -e ../../

# Check Python path
python -c "import lfl; print(lfl.__file__)"
```

### Missing Dependencies

If build fails on missing packages:

```bash
pip install sphinx sphinx-rtd-theme myst-parser
```

### Build Warnings

Fix all Sphinx warnings before committing:

```bash
make html 2>&1 | grep -i warning
```

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
- [MyST Parser](https://myst-parser.readthedocs.io/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/)
