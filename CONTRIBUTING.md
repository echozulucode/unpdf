# Contributing to unpdf

Thank you for your interest in contributing to unpdf! This guide will help you get started.

---

## Code of Conduct

Be respectful, constructive, and welcoming to all contributors.

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/your-username/unpdf.git
cd unpdf
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_extractors.py

# Run with coverage
pytest --cov=unpdf --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

### Code Quality

```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Type checking
mypy unpdf/

# All quality checks
ruff check . && ruff format --check . && mypy unpdf/
```

### Manual Testing

```bash
# Test CLI
unpdf tests/fixtures/sample.pdf

# Test with verbose output
unpdf tests/fixtures/sample.pdf --verbose

# Test library API
python -c "from unpdf import convert_pdf; print(convert_pdf('sample.pdf'))"
```

---

## Contribution Guidelines

### Code Style

**Formatting:** Use **Black** (line length: 88 characters)  
**Docstrings:** Use **Google-style** docstrings  
**Type Hints:** Required on all public functions (Python 3.10+)

- **Simplicity first** - Prefer clear, explicit code over clever solutions
- **Type hints** - All functions must have type hints (Python 3.10+)
- **Docstrings** - All public functions need Google-style docstrings with examples
- **No hidden magic** - Avoid implicit behavior, be explicit

#### Good Example (Google-style docstring)
```python
def detect_heading(text_span: TextSpan, avg_font_size: float) -> bool:
    """Detect if text is a heading based on font size.

    Args:
        text_span: Text element with font metadata.
        avg_font_size: Average font size in the document.

    Returns:
        True if text should be treated as a heading.

    Example:
        >>> span = TextSpan("Title", font_size=24)
        >>> detect_heading(span, avg_font_size=12)
        True
    """
    threshold = avg_font_size * 1.3
    return text_span.font_size > threshold
```

#### Bad Example
```python
def process(span, context):
    # No type hints, unclear logic, no docstring
    return _classify(span, context, mode="auto")
```

See [AGENTS.md](AGENTS.md) for complete docstring examples including classes and methods.

### Testing

- **All new features need tests** - Aim for >80% coverage
- **Test edge cases** - Empty inputs, weird fonts, malformed PDFs
- **Use descriptive test names** - `test_heading_detection_with_large_font`
- **Follow Given-When-Then** - Structure tests clearly

```python
def test_heading_detection_with_large_font():
    """Test that large font size is detected as heading."""
    # Given: Text with font size 2x average
    text_span = TextSpan("Title", font_size=24)
    avg_size = 12
    
    # When: Processing text
    processor = HeadingProcessor(avg_font_size=avg_size)
    result = processor.process(text_span)
    
    # Then: Should be classified as heading
    assert isinstance(result, HeadingElement)
    assert result.level == 1
```

### Documentation

- Update README.md if adding user-facing features
- Update AGENTS.md if changing architecture
- Add docstrings with examples
- Include type hints in function signatures

---

## What to Contribute

### 🟢 Good First Issues

- Improve test coverage
- Add more file format examples
- Enhance error messages
- Update documentation
- Fix typos or clarify docs

### 🟡 Intermediate

- Better list detection (nested structures)
- Improve table extraction accuracy
- Add new CLI options
- Performance optimizations
- Better column detection

### 🔴 Advanced

- Plugin system architecture
- Streaming API for large PDFs
- Alternative output formats (HTML, reStructuredText)
- VS Code extension
- GitHub Action

---

## Pull Request Process

### 1. Before Submitting

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`ruff format .`)
- [ ] No linting issues (`ruff check .`)
- [ ] Type checks pass (`mypy unpdf/`)
- [ ] Documentation updated if needed
- [ ] Commit messages are clear

### 2. Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add blockquote detection
fix: handle empty PDF pages
docs: update installation instructions
test: add table extraction tests
refactor: simplify heading detection logic
```

### 3. Submit PR

- Provide clear description of changes
- Reference related issues (`Fixes #123`)
- Include screenshots/examples if applicable
- Request review from maintainers

### 4. Review Process

- Maintainers will review within 2-3 days
- Address feedback constructively
- Keep PR focused (one feature/fix per PR)
- Rebase if needed to keep history clean

---

## Architecture Principles

See [AGENTS.md](AGENTS.md) for detailed guidelines. Key points:

1. **Simplicity over completeness** - Solve 80% well
2. **Transparency over magic** - Rule-based, not ML
3. **Speed over edge cases** - Fast for common cases
4. **MIT licensing** - No AGPL contamination

### Design Patterns

**Pipeline Architecture:**
```
Extractors → Processors → Renderers
```

Each stage is independent and testable.

---

## Questions?

- 💬 Ask in [Discussions](https://github.com/yourusername/unpdf/discussions)
- 🐛 Report bugs in [Issues](https://github.com/yourusername/unpdf/issues)
- 📧 Email maintainers (for security issues only)

---

## Recognition

All contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for helping make unpdf better! 🎉
