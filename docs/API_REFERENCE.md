# unpdf API Reference

Complete API documentation for using unpdf as a Python library.

---

## Table of Contents

1. [Public API](#public-api)
2. [Core Functions](#core-functions)
3. [Extractors](#extractors)
4. [Processors](#processors)
5. [Renderers](#renderers)
6. [Data Structures](#data-structures)
7. [Exceptions](#exceptions)
8. [Configuration](#configuration)

---

## Public API

### `unpdf.convert_pdf()`

Main entry point for PDF conversion.

```python
def convert_pdf(
    pdf_path: str,
    output_path: str | None = None,
    detect_code_blocks: bool = True,
    heading_font_ratio: float = 1.3,
    pages: list[int] | None = None,
) -> str:
    """
    Convert a PDF file to Markdown format.
    
    Args:
        pdf_path: Path to input PDF file
        output_path: Optional path for output Markdown file
        detect_code_blocks: Whether to detect code blocks (default: True)
        heading_font_ratio: Font size ratio for heading detection (default: 1.3)
        pages: List of page numbers to convert (1-indexed), None for all
    
    Returns:
        Markdown string
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PermissionError: If file cannot be read
        ValueError: If PDF is corrupted or invalid
    
    Examples:
        >>> from unpdf import convert_pdf
        >>> markdown = convert_pdf("document.pdf")
        >>> print(markdown)
        
        >>> # Convert specific pages
        >>> markdown = convert_pdf("doc.pdf", pages=[1, 3, 5])
        
        >>> # Custom heading detection
        >>> markdown = convert_pdf("doc.pdf", heading_font_ratio=1.5)
        
        >>> # Save to file
        >>> markdown = convert_pdf("input.pdf", output_path="output.md")
    """
```

**Usage patterns:**

```python
from unpdf import convert_pdf

# Basic conversion
markdown = convert_pdf("document.pdf")

# With all options
markdown = convert_pdf(
    pdf_path="document.pdf",
    output_path="output.md",
    detect_code_blocks=True,
    heading_font_ratio=1.3,
    pages=[1, 2, 3, 10, 15]
)

# Error handling
try:
    markdown = convert_pdf("document.pdf")
except FileNotFoundError:
    print("PDF file not found")
except PermissionError:
    print("Cannot read PDF file")
except ValueError as e:
    print(f"Invalid PDF: {e}")
```

---

## Core Functions

### `unpdf.core.process_pdf()`

Low-level PDF processing function.

```python
def process_pdf(
    pdf_path: str,
    detect_code_blocks: bool = True,
    heading_font_ratio: float = 1.3,
    pages: list[int] | None = None,
) -> list[dict]:
    """
    Process PDF and return structured elements.
    
    Args:
        pdf_path: Path to PDF file
        detect_code_blocks: Enable code block detection
        heading_font_ratio: Heading detection threshold
        pages: Page numbers to process
    
    Returns:
        List of element dictionaries with keys:
        - type: Element type (text, heading, list, table, etc.)
        - content: Element content
        - metadata: Additional information
    
    Example:
        >>> from unpdf.core import process_pdf
        >>> elements = process_pdf("document.pdf")
        >>> for elem in elements:
        ...     print(f"{elem['type']}: {elem['content'][:50]}")
    """
```

### `unpdf.core.convert_page()`

Convert a single PDF page.

```python
def convert_page(
    page: pdfplumber.Page,
    avg_font_size: float,
    output_dir: Path | None = None,
    detect_code_blocks: bool = True,
    heading_font_ratio: float = 1.3,
) -> str:
    """
    Convert a single PDF page to Markdown.
    
    Args:
        page: pdfplumber Page object
        avg_font_size: Average font size for the document
        output_dir: Directory to save extracted images
        detect_code_blocks: Enable code detection
        heading_font_ratio: Heading threshold
    
    Returns:
        Markdown string for the page
    
    Example:
        >>> import pdfplumber
        >>> from unpdf.core import convert_page
        >>> 
        >>> with pdfplumber.open("doc.pdf") as pdf:
        ...     markdown = convert_page(pdf.pages[0], avg_font_size=12.0)
    """
```

---

## Extractors

### Text Extractor

**Module:** `unpdf.extractors.text`

#### `extract_text_with_metadata()`

```python
def extract_text_with_metadata(
    page: pdfplumber.Page
) -> list[TextElement]:
    """
    Extract text with font and formatting metadata.
    
    Args:
        page: pdfplumber Page object
    
    Returns:
        List of TextElement objects with:
        - text: Text content
        - bbox: Bounding box (x0, y0, x1, y1)
        - font_name: Font family name
        - font_size: Font size in points
        - is_bold: Whether text is bold
        - is_italic: Whether text is italic
    
    Example:
        >>> from unpdf.extractors.text import extract_text_with_metadata
        >>> import pdfplumber
        >>> 
        >>> with pdfplumber.open("doc.pdf") as pdf:
        ...     elements = extract_text_with_metadata(pdf.pages[0])
        ...     for elem in elements:
        ...         if elem.is_bold:
        ...             print(f"Bold text: {elem.text}")
    """
```

#### `calculate_average_font_size()`

```python
def calculate_average_font_size(
    elements: list[TextElement]
) -> float:
    """
    Calculate weighted average font size.
    
    Args:
        elements: List of TextElement objects
    
    Returns:
        Average font size weighted by text length
    
    Example:
        >>> elements = extract_text_with_metadata(page)
        >>> avg_size = calculate_average_font_size(elements)
        >>> print(f"Average font size: {avg_size:.1f}pt")
    """
```

### Image Extractor

**Module:** `unpdf.extractors.images`

#### `extract_images()`

```python
def extract_images(
    page: pdfplumber.Page,
    output_dir: Path | None = None,
    page_number: int = 1,
) -> list[ImageInfo]:
    """
    Extract images from PDF page and save to disk.
    
    Args:
        page: pdfplumber Page object
        output_dir: Directory to save images (default: same as PDF)
        page_number: Page number for filename generation
    
    Returns:
        List of ImageInfo objects with:
        - path: Saved image filename
        - caption: Detected caption text (if any)
        - bbox: Image bounding box
        - alt_text: Alternative text for accessibility
    
    Example:
        >>> from unpdf.extractors.images import extract_images
        >>> from pathlib import Path
        >>> 
        >>> output_dir = Path("output/images")
        >>> output_dir.mkdir(parents=True, exist_ok=True)
        >>> 
        >>> with pdfplumber.open("doc.pdf") as pdf:
        ...     images = extract_images(pdf.pages[0], output_dir, page_number=1)
        ...     for img in images:
        ...         print(f"Saved: {img.path}")
        ...         if img.caption:
        ...             print(f"Caption: {img.caption}")
    """
```

#### `detect_caption()`

```python
def detect_caption(
    page: pdfplumber.Page,
    image_bbox: tuple[float, float, float, float],
    search_distance: float = 50.0,
) -> str | None:
    """
    Detect caption text near an image.
    
    Searches for text within specified distance below the image.
    
    Args:
        page: pdfplumber Page object
        image_bbox: Image bounding box (x0, y0, x1, y1)
        search_distance: Maximum distance to search (points)
    
    Returns:
        Caption text if found, None otherwise
    
    Example:
        >>> bbox = (100, 200, 300, 400)  # Image position
        >>> caption = detect_caption(page, bbox)
        >>> if caption:
        ...     print(f"Figure caption: {caption}")
    """
```

---

## Processors

### Heading Processor

**Module:** `unpdf.processors.headings`

#### `detect_headings()`

```python
def detect_headings(
    elements: list[TextElement],
    avg_font_size: float,
    ratio: float = 1.3,
) -> list[TextElement]:
    """
    Detect and mark heading elements based on font size.
    
    Args:
        elements: List of text elements
        avg_font_size: Average font size for the document
        ratio: Font size ratio threshold (default: 1.3)
    
    Returns:
        Elements with heading types assigned
    
    Heading levels are determined by relative font size:
    - Level 1: Largest headings
    - Level 6: Smallest headings (but still > ratio)
    
    Example:
        >>> from unpdf.processors.headings import detect_headings
        >>> 
        >>> elements = extract_text_with_metadata(page)
        >>> avg_size = calculate_average_font_size(elements)
        >>> 
        >>> # Default threshold
        >>> elements = detect_headings(elements, avg_size)
        >>> 
        >>> # More aggressive detection
        >>> elements = detect_headings(elements, avg_size, ratio=1.2)
        >>> 
        >>> # Print detected headings
        >>> for elem in elements:
        ...     if elem.element_type.startswith("heading"):
        ...         level = elem.metadata.get("level", 1)
        ...         print(f"H{level}: {elem.text}")
    """
```

### List Processor

**Module:** `unpdf.processors.lists`

#### `detect_lists()`

```python
def detect_lists(
    elements: list[TextElement]
) -> list[TextElement]:
    """
    Detect and mark list items.
    
    Recognizes:
    - Bullet lists: -, *, •, ◦, ▪
    - Numbered lists: 1., 2), (3), a., i., etc.
    
    Args:
        elements: List of text elements
    
    Returns:
        Elements with list item types assigned
    
    Example:
        >>> from unpdf.processors.lists import detect_lists
        >>> 
        >>> elements = extract_text_with_metadata(page)
        >>> elements = detect_lists(elements)
        >>> 
        >>> for elem in elements:
        ...     if elem.element_type == "list_item":
        ...         list_type = elem.metadata.get("list_type")
        ...         print(f"{list_type} list: {elem.text}")
    """
```

### Code Processor

**Module:** `unpdf.processors.code`

#### `detect_code_blocks()`

```python
def detect_code_blocks(
    elements: list[TextElement],
    enabled: bool = True,
) -> list[TextElement]:
    """
    Detect code blocks based on monospace font families.
    
    Recognized monospace fonts:
    - Courier, Courier New
    - Consolas, Monaco
    - Source Code Pro, Fira Code, JetBrains Mono
    - Liberation Mono, DejaVu Sans Mono
    
    Args:
        elements: List of text elements
        enabled: Whether to perform detection (default: True)
    
    Returns:
        Elements with code types assigned
    
    Example:
        >>> from unpdf.processors.code import detect_code_blocks
        >>> 
        >>> elements = extract_text_with_metadata(page)
        >>> elements = detect_code_blocks(elements)
        >>> 
        >>> # Collect code blocks
        >>> code_blocks = [elem for elem in elements 
        ...                if elem.element_type == "code"]
        >>> for block in code_blocks:
        ...     print(f"Code: {block.text}")
    """
```

### Table Processor

**Module:** `unpdf.processors.table`

#### `extract_tables()`

```python
def extract_tables(
    page: pdfplumber.Page,
    strategy: str = "lines",
) -> list[TableElement]:
    """
    Extract tables from PDF page.
    
    Args:
        page: pdfplumber Page object
        strategy: Detection strategy ("lines" or "text")
            - "lines": Use table borders (more accurate)
            - "text": Use whitespace alignment (fallback)
    
    Returns:
        List of TableElement objects
    
    Example:
        >>> from unpdf.processors.table import extract_tables
        >>> 
        >>> with pdfplumber.open("doc.pdf") as pdf:
        ...     tables = extract_tables(pdf.pages[0])
        ...     for i, table in enumerate(tables):
        ...         print(f"Table {i+1}: {len(table.rows)} rows")
        ...         print(f"Columns: {table.columns}")
    """
```

#### `table_to_markdown()`

```python
def table_to_markdown(
    table: TableElement,
    has_header: bool = True,
) -> str:
    """
    Convert table to Markdown pipe-table format.
    
    Args:
        table: TableElement object
        has_header: Whether first row is a header
    
    Returns:
        Markdown table string
    
    Example:
        >>> from unpdf.processors.table import extract_tables, table_to_markdown
        >>> 
        >>> tables = extract_tables(page)
        >>> for table in tables:
        ...     markdown = table_to_markdown(table)
        ...     print(markdown)
    """
```

### Link Processor

**Module:** `unpdf.processors.links`

#### `extract_links()`

```python
def extract_links(
    page: pdfplumber.Page
) -> list[LinkInfo]:
    """
    Extract hyperlinks from PDF page.
    
    Extracts from:
    1. PDF URI annotations (proper links)
    2. Plain URLs in text (regex detection)
    
    Args:
        page: pdfplumber Page object
    
    Returns:
        List of LinkInfo objects with:
        - text: Link text
        - url: Target URL
        - bbox: Link position (if available)
    
    Example:
        >>> from unpdf.processors.links import extract_links
        >>> 
        >>> with pdfplumber.open("doc.pdf") as pdf:
        ...     links = extract_links(pdf.pages[0])
        ...     for link in links:
        ...         print(f"[{link.text}]({link.url})")
    """
```

### Blockquote Processor

**Module:** `unpdf.processors.blockquote`

#### `detect_blockquotes()`

```python
def detect_blockquotes(
    elements: list[TextElement],
    indent_threshold: float = 36.0,
) -> list[TextElement]:
    """
    Detect blockquote elements based on indentation.
    
    Args:
        elements: List of text elements
        indent_threshold: Minimum left margin for quotes (points)
    
    Returns:
        Elements with blockquote types assigned
    
    Example:
        >>> from unpdf.processors.blockquote import detect_blockquotes
        >>> 
        >>> elements = extract_text_with_metadata(page)
        >>> elements = detect_blockquotes(elements)
        >>> 
        >>> quotes = [elem for elem in elements 
        ...           if elem.element_type == "blockquote"]
        >>> for quote in quotes:
        ...     print(f"> {quote.text}")
    """
```

---

## Renderers

### Markdown Renderer

**Module:** `unpdf.renderers.markdown`

#### `MarkdownRenderer`

```python
class MarkdownRenderer:
    """
    Render structured elements as Markdown.
    
    Attributes:
        line_width: Maximum line width (default: no limit)
        preserve_whitespace: Keep original whitespace (default: False)
    
    Example:
        >>> from unpdf.renderers.markdown import MarkdownRenderer
        >>> 
        >>> renderer = MarkdownRenderer()
        >>> markdown = renderer.render(elements)
        >>> print(markdown)
    """
    
    def render(self, elements: list[TextElement]) -> str:
        """
        Render elements to Markdown.
        
        Args:
            elements: List of text/table/image elements
        
        Returns:
            Markdown formatted string
        """
    
    def render_text(self, element: TextElement) -> str:
        """Render plain text element."""
    
    def render_heading(self, element: TextElement) -> str:
        """Render heading element."""
    
    def render_list_item(self, element: TextElement) -> str:
        """Render list item element."""
    
    def render_code(self, element: TextElement) -> str:
        """Render code element."""
    
    def render_table(self, table: TableElement) -> str:
        """Render table element."""
    
    def render_image(self, image: ImageInfo) -> str:
        """Render image reference."""
    
    def render_link(self, link: LinkInfo) -> str:
        """Render hyperlink."""
    
    def render_blockquote(self, element: TextElement) -> str:
        """Render blockquote element."""
```

---

## Data Structures

### `TextElement`

```python
@dataclass
class TextElement:
    """Represents a text span with formatting."""
    
    text: str
    bbox: tuple[float, float, float, float]
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    element_type: str = "text"
    metadata: dict | None = None
```

### `ImageInfo`

```python
@dataclass
class ImageInfo:
    """Represents an extracted image."""
    
    path: str
    caption: str | None
    bbox: tuple[float, float, float, float]
    alt_text: str = ""
```

### `LinkInfo`

```python
@dataclass
class LinkInfo:
    """Represents a hyperlink."""
    
    text: str
    url: str
    bbox: tuple[float, float, float, float] | None
```

### `TableElement`

```python
@dataclass
class TableElement:
    """Represents a table."""
    
    rows: list[list[str]]
    bbox: tuple[float, float, float, float]
    columns: int
    has_header: bool = True
```

---

## Exceptions

### `PDFConversionError`

```python
class PDFConversionError(Exception):
    """Base exception for PDF conversion errors."""
    pass
```

### `PDFParseError`

```python
class PDFParseError(PDFConversionError):
    """Raised when PDF cannot be parsed."""
    pass
```

### `UnsupportedFeatureError`

```python
class UnsupportedFeatureError(PDFConversionError):
    """Raised when PDF contains unsupported features."""
    pass
```

**Example usage:**

```python
from unpdf import convert_pdf
from unpdf.exceptions import PDFConversionError

try:
    markdown = convert_pdf("document.pdf")
except PDFConversionError as e:
    print(f"Conversion failed: {e}")
```

---

## Configuration

### Environment Variables

```bash
# Set default heading ratio
export UNPDF_HEADING_RATIO=1.5

# Disable code detection by default
export UNPDF_CODE_DETECTION=false

# Set default output directory
export UNPDF_OUTPUT_DIR=./output
```

### Programmatic Configuration

```python
from unpdf import convert_pdf

# Global settings (future feature)
import unpdf
unpdf.set_default_heading_ratio(1.5)
unpdf.set_code_detection(False)

# Per-conversion settings
markdown = convert_pdf(
    "document.pdf",
    detect_code_blocks=False,
    heading_font_ratio=1.5
)
```

---

## Advanced Usage Examples

### Custom Pipeline

```python
import pdfplumber
from unpdf.extractors.text import extract_text_with_metadata, calculate_average_font_size
from unpdf.processors.headings import detect_headings
from unpdf.processors.lists import detect_lists
from unpdf.processors.code import detect_code_blocks
from unpdf.renderers.markdown import MarkdownRenderer

def custom_convert(pdf_path, custom_processor=None):
    """Custom conversion pipeline with additional processing."""
    
    with pdfplumber.open(pdf_path) as pdf:
        all_elements = []
        
        for page in pdf.pages:
            # Extract
            elements = extract_text_with_metadata(page)
            avg_size = calculate_average_font_size(elements)
            
            # Process
            elements = detect_headings(elements, avg_size)
            elements = detect_lists(elements)
            elements = detect_code_blocks(elements)
            
            # Custom processing
            if custom_processor:
                elements = custom_processor(elements)
            
            all_elements.extend(elements)
        
        # Render
        renderer = MarkdownRenderer()
        return renderer.render(all_elements)

# Usage
def my_processor(elements):
    """Custom processor to uppercase headings."""
    for elem in elements:
        if elem.element_type.startswith("heading"):
            elem.text = elem.text.upper()
    return elements

markdown = custom_convert("doc.pdf", custom_processor=my_processor)
```

### Batch Processing with Progress

```python
from pathlib import Path
from unpdf import convert_pdf
from tqdm import tqdm  # pip install tqdm

def batch_convert_with_progress(input_dir, output_dir):
    """Convert all PDFs with progress bar."""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    pdf_files = list(input_path.glob("*.pdf"))
    
    for pdf_file in tqdm(pdf_files, desc="Converting PDFs"):
        try:
            output_file = output_path / f"{pdf_file.stem}.md"
            markdown = convert_pdf(str(pdf_file))
            output_file.write_text(markdown, encoding="utf-8")
        except Exception as e:
            print(f"\nError converting {pdf_file.name}: {e}")

# Usage
batch_convert_with_progress("pdfs/", "markdown/")
```

### Selective Processing

```python
from unpdf import convert_pdf

def convert_only_text_pages(pdf_path, text_pages):
    """Convert only pages that are text-heavy."""
    
    markdown_parts = []
    
    for page_num in text_pages:
        markdown = convert_pdf(pdf_path, pages=[page_num])
        markdown_parts.append(f"## Page {page_num}\n\n{markdown}")
    
    return "\n\n---\n\n".join(markdown_parts)

# Convert only pages 1, 5, 10
result = convert_only_text_pages("doc.pdf", [1, 5, 10])
```

---

## Type Hints

Full type annotations are provided for all public APIs:

```python
from typing import List, Optional, Tuple
from pathlib import Path

def convert_pdf(
    pdf_path: str,
    output_path: Optional[str] = None,
    detect_code_blocks: bool = True,
    heading_font_ratio: float = 1.3,
    pages: Optional[List[int]] = None,
) -> str:
    ...
```

Use with mypy for static type checking:

```bash
mypy your_script.py
```

---

## Deprecation Warnings

Future API changes will include deprecation warnings:

```python
import warnings

# Deprecated function
def old_convert(pdf_path):
    warnings.warn(
        "old_convert() is deprecated, use convert_pdf() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return convert_pdf(pdf_path)
```

---

**Last Updated:** 2025-11-02  
**Version:** 1.0.0
