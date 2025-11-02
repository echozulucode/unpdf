# unpdf Python Style Guide

**Last Updated:** 2025-11-02

---

## Overview

This project uses **Black** for code formatting and **Google-style docstrings** for documentation. These choices prioritize simplicity, consistency, and readability.

---

## Code Formatting

### Black Formatter

We use [Black](https://black.readthedocs.io/) for automatic code formatting.

**Configuration:**
- Line length: **88 characters** (Black's default)
- Target: Python 3.10+
- String normalization: Enabled (prefer double quotes)
- Magic trailing comma: Enabled

**Why Black?**
- Zero configuration decisions
- Deterministic formatting (same code always formats the same way)
- Fast
- Widely adopted in Python community

**Auto-format command:**
```bash
black .
```

**Check without modifying:**
```bash
black --check .
```

### Import Sorting

We use **Ruff** for import organization (compatible with Black).

**Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example:**
```python
# Standard library
from pathlib import Path
from typing import Any

# Third-party
import pdfplumber

# Local
from unpdf.core import Pipeline
from unpdf.extractors import TextExtractor
```

---

## Docstring Style: Google Format

### Why Google Style?

- **Readable in code** - Clear section headers (Args, Returns, Raises)
- **Readable in docs** - Renders well in Sphinx/MkDocs
- **Concise** - Less verbose than NumPy style
- **Standard** - Widely used in Python community (TensorFlow, Django)

### Basic Template

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """One-line summary ending with period.

    Optional multi-line description providing more context.
    Can span multiple paragraphs if needed.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.
            Can continue on next line with indent.

    Returns:
        Description of return value.

    Raises:
        ErrorType: When this error occurs.
        AnotherError: When this error occurs.

    Example:
        >>> result = function_name("value", 42)
        >>> print(result)
        expected output

    Note:
        Additional information if needed.
    """
    pass
```

### Section Breakdown

#### 1. Summary Line
- **One line**, imperative mood, ending with period
- Should complete: "This function will..."
- Max 88 characters (fits in one line with Black)

```python
def extract_text(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""  # Good
    
def extract_text(pdf_path: Path) -> str:
    """This function extracts text from PDF."""  # Bad (not imperative)
```

#### 2. Description (Optional)
- Blank line after summary
- Provides context, caveats, algorithm details
- Multiple paragraphs OK

```python
def complex_function(data: dict) -> Result:
    """Process complex data structure.

    This function handles nested dictionaries with special attention
    to circular references. It uses a depth-first traversal with
    memoization to avoid infinite loops.

    The algorithm runs in O(n) time where n is the number of nodes.
    """
    pass
```

#### 3. Args Section
- List each parameter with colon separator
- Start with lowercase, no period at end (unless multiple sentences)
- Indent continuation lines

```python
def convert_pdf(
    pdf_path: Path,
    output_path: Path | None = None,
    force_ocr: bool = False,
) -> str:
    """Convert PDF to Markdown.

    Args:
        pdf_path: Path to the PDF file to convert.
        output_path: Optional output path. If None, uses same name
            as input with .md extension.
        force_ocr: Whether to force OCR even if text is embedded.
            Set to True for scanned documents.
    """
    pass
```

#### 4. Returns Section
- Describe what is returned
- Include type information if not obvious from signature

```python
def get_metadata(pdf_path: Path) -> dict[str, Any]:
    """Extract metadata from PDF.

    Returns:
        Dictionary containing:
            - title (str): Document title
            - author (str): Document author
            - pages (int): Number of pages
            - created (datetime): Creation date
    """
    pass
```

#### 5. Raises Section
- List exceptions that can be raised
- Explain when each occurs

```python
def open_pdf(pdf_path: Path) -> PDF:
    """Open a PDF file for processing.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        Opened PDF object ready for processing.

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If file exists but is not a valid PDF.
        PermissionError: If file is password-protected.
    """
    pass
```

#### 6. Example Section (Recommended)
- Show typical usage with doctest format
- Use `>>>` for interactive examples
- Include expected output

```python
def is_heading(text_span: TextSpan, avg_size: float) -> bool:
    """Check if text span is a heading.

    Args:
        text_span: Text element to check.
        avg_size: Average font size in document.

    Returns:
        True if text is a heading.

    Example:
        >>> span = TextSpan("Title", font_size=24)
        >>> is_heading(span, avg_size=12)
        True
        >>> span2 = TextSpan("Body", font_size=12)
        >>> is_heading(span2, avg_size=12)
        False
    """
    return text_span.font_size > avg_size * 1.3
```

#### 7. Note Section (Optional)
- Additional warnings or information
- Implementation details
- Performance considerations

```python
def batch_process(files: list[Path]) -> list[str]:
    """Process multiple PDF files in parallel.

    Args:
        files: List of PDF paths to process.

    Returns:
        List of Markdown strings, one per file.

    Note:
        This function uses multiprocessing. Each PDF should be
        at least 100KB to justify parallelization overhead.
        For smaller files, use serial processing instead.
    """
    pass
```

---

## Complete Examples

### Function with All Sections

```python
from pathlib import Path


def extract_text_with_metadata(
    pdf_path: Path,
    pages: list[int] | None = None,
    include_images: bool = False,
) -> list[dict[str, Any]]:
    """Extract text and metadata from PDF pages.

    Reads the specified PDF file and extracts text content along with
    font information for each text span. Optionally includes image data.

    Args:
        pdf_path: Path to the PDF file to process.
        pages: Optional list of page numbers (1-indexed). If None,
            processes all pages.
        include_images: Whether to extract and include image data
            in the output.

    Returns:
        List of dictionaries, one per text span, containing:
            - text (str): The actual text content
            - font_size (float): Font size in points
            - font_family (str): Font family name
            - is_bold (bool): Whether text is bold
            - is_italic (bool): Whether text is italic
            - bbox (tuple): Bounding box (x0, y0, x1, y1)
            - image (bytes | None): Image data if include_images=True

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If PDF is corrupted or unreadable.
        PermissionError: If PDF is password-protected.

    Example:
        >>> spans = extract_text_with_metadata(Path("doc.pdf"))
        >>> print(spans[0]['text'])
        'Document Title'
        >>> print(spans[0]['font_size'])
        24.0

        Process specific pages:
        >>> spans = extract_text_with_metadata(
        ...     Path("doc.pdf"),
        ...     pages=[1, 2, 3]
        ... )
        >>> len(spans)
        45

    Note:
        Font detection relies on PDF metadata. Some PDFs generated
        by certain tools may not have accurate font information.
    """
    pass
```

### Class Documentation

```python
class HeadingProcessor:
    """Process and classify text spans as headings.

    The HeadingProcessor analyzes text spans and determines if they
    should be treated as headings based on their font size relative
    to the document average. Heading levels (H1-H6) are assigned
    based on relative size differences.

    Attributes:
        avg_font_size: Average font size in the document.
        heading_ratio: Multiplier to determine heading threshold.
        max_level: Maximum heading level to generate (default: 6).

    Example:
        >>> processor = HeadingProcessor(avg_font_size=12.0)
        >>> element = processor.process(TextSpan("Title", font_size=24))
        >>> isinstance(element, HeadingElement)
        True
        >>> element.level
        1
        >>> element.markdown
        '# Title'
    """

    def __init__(
        self,
        avg_font_size: float,
        heading_ratio: float = 1.3,
        max_level: int = 6,
    ):
        """Initialize HeadingProcessor.

        Args:
            avg_font_size: Average font size in the document.
            heading_ratio: Multiplier for heading threshold.
            max_level: Maximum heading level (1-6).

        Raises:
            ValueError: If max_level is not between 1 and 6.
        """
        if not 1 <= max_level <= 6:
            raise ValueError(f"max_level must be 1-6, got {max_level}")
        self.avg_font_size = avg_font_size
        self.heading_ratio = heading_ratio
        self.max_level = max_level

    def process(self, text_span: TextSpan) -> HeadingElement | ParagraphElement:
        """Process text span and classify as heading or paragraph.

        Args:
            text_span: Text element to process.

        Returns:
            HeadingElement if detected as heading, ParagraphElement otherwise.

        Example:
            >>> span = TextSpan("Section", font_size=18)
            >>> result = processor.process(span)
            >>> result.level
            2
        """
        threshold = self.avg_font_size * self.heading_ratio
        if text_span.font_size > threshold:
            level = self._calculate_level(text_span.font_size)
            return HeadingElement(text_span.text, level=level)
        return ParagraphElement(text_span.text)

    def _calculate_level(self, font_size: float) -> int:
        """Calculate heading level based on font size.

        Private method. Not documented in detail since it's internal.

        Args:
            font_size: Font size to analyze.

        Returns:
            Heading level from 1 (largest) to max_level.
        """
        # Implementation details...
        pass
```

### Module-Level Docstring

```python
"""Text extraction and processing for PDF files.

This module provides core functionality for extracting text from PDFs
with metadata like font information, positioning, and styling. It serves
as the foundation for the unpdf conversion pipeline.

Typical usage:
    from unpdf.extractors.text import extract_text_with_metadata

    spans = extract_text_with_metadata(Path("document.pdf"))
    for span in spans:
        print(f"{span['text']}: {span['font_size']}pt")

Classes:
    TextExtractor: Main class for text extraction.
    TextSpan: Data class representing a text element.

Functions:
    extract_text_with_metadata: Extract text with font info.
    merge_adjacent_spans: Combine consecutive text spans.
"""

from pathlib import Path
from typing import Any

# ... rest of module
```

---

## Type Hints

### Required for Public Functions

```python
# Good - Full type hints
def convert_text(text: str, encoding: str = "utf-8") -> bytes:
    pass

# Bad - Missing types
def convert_text(text, encoding="utf-8"):
    pass
```

### Use Modern Python 3.10+ Syntax

```python
# Good - Python 3.10+ union syntax
def get_value(key: str) -> str | None:
    pass

# Good - Modern generic syntax
def process_items(items: list[str]) -> dict[str, int]:
    pass

# Bad - Old-style typing
from typing import Optional, Dict, List

def get_value(key: str) -> Optional[str]:
    pass

def process_items(items: List[str]) -> Dict[str, int]:
    pass
```

### Complex Types

```python
from pathlib import Path
from typing import Any, Callable, TypeAlias

# Type aliases for clarity
PDFMetadata: TypeAlias = dict[str, Any]
ProcessorFunc: TypeAlias = Callable[[str], str]

def extract_metadata(pdf_path: Path) -> PDFMetadata:
    """Extract metadata from PDF."""
    pass

def apply_processor(text: str, func: ProcessorFunc) -> str:
    """Apply processing function to text."""
    pass
```

---

## Tools Setup

### Install Formatters

```bash
pip install black ruff
```

### Format Code

```bash
# Format with Black
black .

# Check only (don't modify)
black --check .

# Format and organize imports with Ruff
ruff check --fix .
```

### Pre-commit Hook (Recommended)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
black --check . || exit 1
ruff check . || exit 1
mypy unpdf/ || exit 1
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## VS Code Integration

Install extensions:
- `ms-python.black-formatter` - Black formatting
- `charliermarsh.ruff` - Ruff linting

Settings are already configured in `.vscode/settings.json`:
- Format on save: **Enabled**
- Formatter: **Black** (line length: 88)
- Linter: **Ruff** (with Google docstring checks)

---

## Quick Reference

| Aspect | Standard | Example |
|--------|----------|---------|
| Formatter | Black | `black .` |
| Line length | 88 characters | Black default |
| Quotes | Double quotes | `"text"` not `'text'` |
| Docstring style | Google | See examples above |
| Type hints | Required (public) | `def func(x: int) -> str:` |
| Import order | stdlib, 3rd-party, local | See examples above |

---

## Questions?

- See [AGENTS.md](../AGENTS.md) for more code examples
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for workflow
- Check Black docs: https://black.readthedocs.io/
- Check Google style guide: https://google.github.io/styleguide/pyguide.html

---

**Remember:** Consistency matters more than personal preference. Let Black handle formatting so you can focus on logic.
