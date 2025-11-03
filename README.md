# unpdf

**Simple, MIT-licensed PDF-to-Markdown converter for developers who value transparency and predictability.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Why unpdf?

While tools like PyMuPDF and Marker are powerful, they come with trade-offs:

- **PyMuPDF**: AGPL-licensed (viral) or expensive commercial license
- **Marker**: Complex ML pipeline, requires GPU, custom licensing with revenue limits

**unpdf is different:**

✅ **MIT Licensed** - Use freely in any commercial project  
✅ **Simple & Fast** - Rule-based, no ML, sub-second conversion  
✅ **Transparent** - Understand *why* conversions happen  
✅ **Lightweight** - No torch/transformers, <10 dependencies  
✅ **Developer-First** - Easy to use, extend, and contribute to  

---

## Perfect For

- 📄 **Documentation** - Technical docs, user guides, manuals
- 📊 **Business Reports** - Proposals, presentations, contracts
- 📝 **Technical Content** - Whitepapers, specifications, RFCs
- ⚙️ **CI/CD Pipelines** - Automated document processing
- ☁️ **Serverless/Edge** - Low memory, fast cold starts

**Not targeting:** Forms, equations, scanned PDFs (use Marker for those)

---

## Quick Start

### Installation

```bash
# Basic installation
pip install unpdf

# With table support
pip install unpdf[tables]

# Development installation
pip install unpdf[dev]
```

### Usage

```bash
# Convert a PDF
unpdf document.pdf

# Specify output path
unpdf input.pdf -o output.md

# Process directory
unpdf docs/ --recursive

# Verbose output
unpdf file.pdf --verbose
```

### Python API

```python
from unpdf import convert_pdf

# Simple conversion
markdown = convert_pdf("document.pdf")

# With options
markdown = convert_pdf(
    "document.pdf",
    detect_code_blocks=True,
    heading_font_ratio=1.3
)

# Save to file
with open("output.md", "w") as f:
    f.write(markdown)
```

---

## Features

| Feature | Status | Notes |
|---------|--------|-------|
| Text extraction | ✅ | Preserves paragraphs, spacing |
| **Bold/Italic** | ✅ | Font metadata detection |
| Headings | ✅ | Font-size based (configurable) |
| Lists | ✅ | Bullets, numbered, nested (up to 5 levels) |
| Code blocks | ✅ | Monospace font detection + language inference |
| Tables | ✅ | Pipe-table format with header detection |
| Images | ✅ | Extracted with caption detection |
| Hyperlinks | ✅ | Preserved as `[text](url)` |
| Blockquotes | ✅ | Indentation-based detection |
| Footnotes | ⚠️ | Detected as regular text |
| Equations | ❌ | Use Marker instead |
| Forms | ❌ | Use Marker instead |
| Multi-column | ⚠️ | Limited support (reading order may vary) |

---

## How It Works

**unpdf uses a simple, transparent pipeline:**

1. **Extract** - Pull text, images, tables from PDF using pdfplumber
2. **Process** - Classify content (headings, lists, code) via heuristics
3. **Render** - Output as clean Markdown

**No black-box ML models.** Every decision is rule-based and configurable.

### Example: Heading Detection

```python
def is_heading(text_span, avg_font_size):
    """Simple, predictable logic."""
    return text_span.font_size > avg_font_size * 1.3
```

---

## Philosophy

**Simplicity over Completeness**  
Better quality on 80% of use cases than mediocre on 100%.

**Transparency over Magic**  
Understand why conversions happen. No hidden ML models.

**Speed over Edge Cases**  
Sub-second conversion for typical documents.

**MIT Licensing**  
No AGPL contamination, no commercial restrictions.

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/unpdf.git
cd unpdf

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
ruff check .
ruff format .
mypy unpdf/
```

### Project Structure

```
unpdf/
├── unpdf/
│   ├── __init__.py       # Main API
│   ├── core.py           # Pipeline orchestration
│   ├── cli.py            # Command-line interface
│   ├── extractors/       # PDF content extraction
│   ├── processors/       # Content classification
│   └── renderers/        # Markdown output
├── tests/
├── docs/
└── pyproject.toml
```

---

## Comparison

| Feature | unpdf | PyMuPDF | Marker |
|---------|-------|---------|--------|
| License | MIT ✅ | AGPL ⚠️ | Custom ⚠️ |
| Dependencies | <10 | Moderate | Many (ML) |
| GPU Required | No ✅ | No | Optional |
| Speed (typical) | <0.5s/page | ~0.2s/page | ~2.8s/page |
| Memory | <50MB/page | Moderate | High (GPU) |
| Edge Cases | Fair | Excellent | Excellent |
| Explainability | High ✅ | Low | Low |
| Customization | Easy | Moderate | Complex |

---

## Contributing

Contributions welcome! See [AGENTS.md](AGENTS.md) for development guidelines.

**Areas we'd love help with:**
- Better list detection (nested structures)
- Column layout handling (newspapers)
- More robust table extraction
- Additional output formats (HTML, reStructuredText)

---

## Roadmap

See [docs/ai/plan-001-implementation.md](docs/ai/plan-001-implementation.md) for detailed implementation plan.

### v1.0 (Current - Phases 1-8 Complete)
- ✅ Basic text extraction with metadata
- ✅ Font style detection (bold, italic)
- ✅ Heading detection (font-size based)
- ✅ List detection (bullets, numbered, nested)
- ✅ Code blocks (monospace detection)
- ✅ Tables (pdfplumber integration)
- ✅ Images & links extraction
- ✅ CLI with advanced features
- ✅ Comprehensive test suite (172 tests, 96% coverage)

**Status**: Documentation & polish phase (Phase 9)

### v1.1 (Future)
- Plugin system for custom processors
- Configuration file support (YAML)
- Streaming API for large PDFs
- Performance optimizations
- Better column layout handling

### v2.0 (Future)
- Optional OCR plugin (keep base lightweight)
- Watch mode (auto-convert on changes)
- VS Code extension
- GitHub Action for CI/CD
- HTML and reStructuredText output formats

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

**Use freely in commercial projects without restrictions.**

---

## Acknowledgments

Built with:
- [pdfplumber](https://github.com/jsvine/pdfplumber) - MIT license
- [pdfminer.six](https://github.com/pdfminer/pdfminer.six) - MIT license
- [camelot-py](https://github.com/camelot-dev/camelot) - MIT license (optional)

Inspired by the need for a truly open-source PDF converter.

---

## Troubleshooting

### Common Issues

**Headings not detected?**
```bash
# Lower the threshold (more aggressive)
unpdf document.pdf --heading-ratio 1.1
```

**Too many headings?**
```bash
# Raise the threshold (more conservative)
unpdf document.pdf --heading-ratio 1.5
```

**Code blocks incorrectly detected?**
```bash
# Disable code block detection
unpdf document.pdf --no-code-blocks
```

**Tables not appearing?**
```bash
# Ensure table support is installed
pip install unpdf[tables]
```

**Memory issues with large PDFs?**
```bash
# Process in batches
unpdf large.pdf --pages 1-50 -o part1.md
unpdf large.pdf --pages 51-100 -o part2.md
```

For detailed troubleshooting, see [docs/USER_GUIDE.md](docs/USER_GUIDE.md#troubleshooting).

---

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/unpdf/issues)
- 💬 [Discussions](https://github.com/yourusername/unpdf/discussions)

---

**Made with ❤️ for developers who value simplicity and transparency.**
