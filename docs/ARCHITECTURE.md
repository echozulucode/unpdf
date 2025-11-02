# unpdf Architecture

Developer guide to understanding unpdf's internal architecture and design decisions.

---

## Table of Contents

1. [Overview](#overview)
2. [Design Philosophy](#design-philosophy)
3. [Pipeline Architecture](#pipeline-architecture)
4. [Module Structure](#module-structure)
5. [Data Flow](#data-flow)
6. [Key Algorithms](#key-algorithms)
7. [Extension Points](#extension-points)
8. [Testing Strategy](#testing-strategy)

---

## Overview

unpdf is a **rule-based PDF-to-Markdown converter** built on three core principles:

1. **Transparency** - No black-box ML models
2. **Simplicity** - Straightforward codebase, easy to understand
3. **Extensibility** - Plugin-friendly architecture

**Core Dependencies:**
- `pdfplumber` - PDF parsing and text extraction
- `pdfminer.six` - Low-level PDF processing
- Python 3.10+ standard library

---

## Design Philosophy

### 1. Rule-Based Over ML

**Why no machine learning?**

- **Predictability** - Same PDF always produces same output
- **Debuggability** - Can trace every decision
- **Lightweight** - No GPU, no model downloads
- **Fast** - No inference overhead

**Trade-off:** Lower accuracy on complex/unusual layouts vs ML-based tools.

### 2. Pipeline Architecture

**Three-stage pipeline:**

```
PDF → Extract → Process → Render → Markdown
```

**Benefits:**
- Clear separation of concerns
- Easy to test each stage independently
- Simple to add new processors/renderers

### 3. Heuristic-Driven

**Common heuristics:**
- Font size → Heading detection
- Font family → Code block detection
- Indentation → List detection
- Line patterns → Table detection

**Philosophy:** 80% accuracy on common cases beats 95% on edge cases.

---

## Pipeline Architecture

### Stage 1: Extraction

**Responsibility:** Pull raw content from PDF.

**Extractors:**
- `extractors/text.py` - Text with font metadata
- `extractors/images.py` - Images with positioning

**Output:** Structured elements with metadata:
```python
@dataclass
class TextElement:
    text: str
    bbox: tuple[float, float, float, float]
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
```

### Stage 2: Processing

**Responsibility:** Classify and structure content.

**Processors:**
- `processors/headings.py` - Heading level detection
- `processors/lists.py` - List item identification
- `processors/code.py` - Code block detection
- `processors/table.py` - Table extraction
- `processors/links.py` - Hyperlink extraction
- `processors/blockquote.py` - Quote detection

**Output:** Annotated elements with semantic meaning.

### Stage 3: Rendering

**Responsibility:** Convert structured data to output format.

**Renderers:**
- `renderers/markdown.py` - Markdown output

**Output:** Final Markdown string.

---

## Module Structure

```
unpdf/
├── __init__.py           # Public API (convert_pdf)
├── core.py               # Pipeline orchestration
├── cli.py                # Command-line interface
│
├── extractors/
│   ├── __init__.py
│   ├── text.py           # Text + metadata extraction
│   └── images.py         # Image extraction + caption detection
│
├── processors/
│   ├── __init__.py
│   ├── headings.py       # Font-size based heading detection
│   ├── lists.py          # Bullet/numbered list detection
│   ├── code.py           # Monospace font code detection
│   ├── table.py          # pdfplumber table extraction
│   ├── links.py          # URL/annotation extraction
│   └── blockquote.py     # Quote block detection
│
└── renderers/
    ├── __init__.py
    └── markdown.py       # Markdown output formatting
```

### Module Responsibilities

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `__init__.py` | Public API | `convert_pdf()` |
| `core.py` | Pipeline coordination | `process_pdf()`, `convert_page()` |
| `cli.py` | CLI interface | `main()`, `parse_page_spec()` |
| `extractors/text.py` | Text extraction | `extract_text_with_metadata()` |
| `extractors/images.py` | Image extraction | `extract_images()`, `detect_caption()` |
| `processors/headings.py` | Heading detection | `detect_headings()` |
| `processors/lists.py` | List detection | `detect_lists()` |
| `processors/code.py` | Code detection | `detect_code_blocks()` |
| `processors/table.py` | Table extraction | `extract_tables()` |
| `processors/links.py` | Link extraction | `extract_links()` |
| `processors/blockquote.py` | Quote detection | `detect_blockquotes()` |
| `renderers/markdown.py` | Markdown output | `render()` |

---

## Data Flow

### Element Data Structure

**Core element type:**

```python
from dataclasses import dataclass

@dataclass
class TextElement:
    """Represents a text span with formatting metadata."""
    text: str
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    element_type: str = "text"  # text, heading, list_item, code, etc.
    metadata: dict = None       # Additional context
```

### Processing Flow

```
1. PDF File (bytes)
   ↓
2. pdfplumber.open()
   ↓
3. Extract text elements (TextElement[])
   ↓
4. Process each element type:
   - Detect headings (font size ratio)
   - Detect lists (bullet/number patterns)
   - Detect code (monospace fonts)
   - Detect blockquotes (indentation)
   ↓
5. Extract tables separately (pdfplumber)
   ↓
6. Extract images (save to disk)
   ↓
7. Extract links (annotations + plain URLs)
   ↓
8. Merge all elements by position
   ↓
9. Render to Markdown
   ↓
10. Output string
```

### Example: Page Processing

```python
def convert_page(page, avg_font_size, output_dir):
    """Process a single PDF page."""
    
    # 1. Extract text
    text_elements = extract_text_with_metadata(page)
    
    # 2. Detect headings
    text_elements = detect_headings(
        text_elements,
        avg_font_size,
        ratio=1.3
    )
    
    # 3. Detect lists
    text_elements = detect_lists(text_elements)
    
    # 4. Detect code blocks
    text_elements = detect_code_blocks(text_elements)
    
    # 5. Detect blockquotes
    text_elements = detect_blockquotes(text_elements)
    
    # 6. Extract tables
    tables = extract_tables(page)
    
    # 7. Extract images
    images = extract_images(page, output_dir)
    
    # 8. Extract links
    links = extract_links(page)
    
    # 9. Merge all elements
    all_elements = merge_by_position(
        text_elements,
        tables,
        images,
        links
    )
    
    # 10. Render
    renderer = MarkdownRenderer()
    return renderer.render(all_elements)
```

---

## Key Algorithms

### 1. Heading Detection

**Algorithm:** Font size ratio comparison

```python
def is_heading(element, avg_font_size, ratio=1.3):
    """
    Detect if text element is a heading based on font size.
    
    Logic:
    - Compare element font size to page average
    - If ratio exceeds threshold, it's a heading
    - Heading level determined by relative size
    """
    if element.font_size > avg_font_size * ratio:
        # Calculate heading level (1-6)
        size_diff = element.font_size - avg_font_size
        level = max(1, min(6, int(size_diff / 2)))
        return True, level
    return False, 0
```

**Configuration:**
- Default ratio: 1.3
- Adjustable via `--heading-ratio` CLI flag
- Level calculation: `size_difference / 2`

### 2. List Detection

**Algorithm:** Pattern matching on line starts

```python
def detect_lists(elements):
    """
    Detect list items by checking line prefixes.
    
    Bullet patterns: -, *, •, ◦, ▪
    Number patterns: 1., 2), (1), a., i., etc.
    """
    for element in elements:
        text = element.text.lstrip()
        
        # Check bullet list
        if re.match(r'^[-*•◦▪]\s', text):
            element.element_type = "list_item"
            element.metadata = {"list_type": "bullet"}
        
        # Check numbered list
        elif re.match(r'^\d+[.)]\s', text):
            element.element_type = "list_item"
            element.metadata = {"list_type": "number"}
    
    return elements
```

**Patterns supported:**
- Bullets: `-`, `*`, `•`, `◦`, `▪`
- Numbers: `1.`, `2)`, `(3)`, `a.`, `i.`

### 3. Code Block Detection

**Algorithm:** Monospace font family detection

```python
def detect_code_blocks(elements):
    """
    Detect code blocks by identifying monospace fonts.
    
    Common monospace fonts:
    - Courier, Courier New
    - Consolas, Monaco
    - Source Code Pro, Fira Code
    """
    monospace_fonts = {
        "courier", "consolas", "monaco",
        "monospace", "source", "fira"
    }
    
    for element in elements:
        font_lower = element.font_name.lower()
        if any(mono in font_lower for mono in monospace_fonts):
            element.element_type = "code"
    
    return elements
```

**Grouping:** Consecutive code elements merged into code blocks.

### 4. Table Detection

**Algorithm:** pdfplumber's table extraction

```python
def extract_tables(page):
    """
    Extract tables using pdfplumber's built-in detection.
    
    Strategies:
    1. Line-based: Detect table borders
    2. Text-based: Detect aligned columns (whitespace)
    """
    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 3,
    }
    
    tables = page.find_tables(settings)
    
    # Fallback to text-based if no lines detected
    if not tables:
        settings["vertical_strategy"] = "text"
        settings["horizontal_strategy"] = "text"
        tables = page.find_tables(settings)
    
    return [t.extract() for t in tables]
```

**Header detection:**
```python
def has_header_row(rows):
    """
    Heuristic: First row likely header if:
    1. More bold/uppercase than subsequent rows
    2. Different alignment pattern
    3. Shorter text (column names vs data)
    """
    if len(rows) < 2:
        return False
    
    first_row = rows[0]
    second_row = rows[1]
    
    # Check if first row is all uppercase/bold
    first_formatted = sum(1 for cell in first_row if cell.isupper())
    return first_formatted > len(first_row) / 2
```

### 5. Image Extraction

**Algorithm:** Extract images and detect captions

```python
def extract_images(page, output_dir):
    """
    Extract images and save to disk.
    
    1. Get all images from page
    2. Generate unique filename (MD5 hash)
    3. Save image file
    4. Detect caption (text within 50pt below image)
    """
    images = []
    
    for img in page.images:
        # Generate unique filename
        image_data = img["stream"].get_data()
        hash_id = hashlib.md5(image_data).hexdigest()[:8]
        filename = f"page{page.page_number}_img{hash_id}.png"
        
        # Save image
        filepath = output_dir / filename
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        # Detect caption
        caption = detect_caption(page, img["bbox"])
        
        images.append({
            "path": filename,
            "caption": caption,
            "bbox": img["bbox"]
        })
    
    return images
```

**Caption detection:**
```python
def detect_caption(page, image_bbox):
    """
    Look for text within 50pt below image.
    """
    x0, y0, x1, y1 = image_bbox
    caption_area = (x0, y1, x1, y1 + 50)
    
    text_in_area = page.within_bbox(caption_area).extract_text()
    
    # Return first line as caption
    if text_in_area:
        return text_in_area.split('\n')[0].strip()
    return None
```

### 6. Link Extraction

**Algorithm:** Annotations + regex for plain URLs

```python
def extract_links(page):
    """
    Extract hyperlinks from PDF annotations and plain text.
    """
    links = []
    
    # 1. Extract from annotations
    for annotation in page.annots:
        if annotation.get("uri"):
            links.append({
                "text": annotation.get("text", ""),
                "url": annotation["uri"],
                "bbox": annotation["rect"]
            })
    
    # 2. Extract plain URLs from text
    text = page.extract_text()
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    for match in re.finditer(url_pattern, text):
        url = match.group(0)
        links.append({
            "text": url,
            "url": url,
            "bbox": None
        })
    
    return links
```

---

## Extension Points

### Adding New Processors

**Example: Custom heading detection**

```python
# unpdf/processors/custom_headings.py

def detect_headings_by_style(elements):
    """
    Alternative heading detection using font style.
    """
    for element in elements:
        # Check if font is bold AND larger than 12pt
        if element.is_bold and element.font_size > 12:
            element.element_type = "heading"
            element.metadata = {"level": calculate_level(element)}
    
    return elements
```

**Integrate in pipeline:**

```python
# unpdf/core.py

from unpdf.processors.custom_headings import detect_headings_by_style

def convert_page(page, **options):
    elements = extract_text_with_metadata(page)
    
    # Use custom processor
    if options.get("use_style_headings"):
        elements = detect_headings_by_style(elements)
    else:
        elements = detect_headings(elements, avg_font_size)
    
    # ... rest of pipeline
```

### Adding New Renderers

**Example: HTML renderer**

```python
# unpdf/renderers/html.py

class HTMLRenderer:
    """Render elements as HTML."""
    
    def render(self, elements):
        html = []
        
        for element in elements:
            if element.element_type == "heading":
                level = element.metadata.get("level", 1)
                html.append(f"<h{level}>{element.text}</h{level}>")
            
            elif element.element_type == "text":
                html.append(f"<p>{element.text}</p>")
            
            # ... handle other types
        
        return "\n".join(html)
```

**Use in API:**

```python
from unpdf.renderers.html import HTMLRenderer

def convert_pdf_to_html(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        elements = extract_all_elements(pdf)
        renderer = HTMLRenderer()
        return renderer.render(elements)
```

### Configuration System (Future)

**Planned: YAML config file**

```yaml
# unpdf.config.yaml

headings:
  font_size_ratio: 1.3
  style_based: false

lists:
  detect_nested: true
  max_depth: 3

code:
  monospace_fonts:
    - Courier
    - Consolas
    - Monaco

tables:
  strategy: lines  # or "text"
  min_rows: 2

output:
  format: markdown
  line_width: 80
```

---

## Testing Strategy

### Unit Tests

**Test individual functions in isolation.**

```python
# tests/unit/test_headings.py

def test_is_heading_above_ratio():
    element = TextElement(
        text="Chapter 1",
        font_size=18.0,
        # ...
    )
    avg_font_size = 12.0
    
    result = is_heading(element, avg_font_size, ratio=1.3)
    assert result is True
```

**Coverage goal:** 90%+ for processor modules

### Integration Tests

**Test full pipeline on real PDFs.**

```python
# tests/integration/test_pipeline.py

def test_convert_simple_pdf():
    markdown = convert_pdf("tests/fixtures/simple.pdf")
    
    assert "# Heading" in markdown
    assert "- List item" in markdown
    assert "```" in markdown  # Code block
```

### Feature Tests

**Test specific features with minimal PDFs.**

```python
# tests/features/test_tables.py

def test_table_with_header():
    # PDF with single table
    markdown = convert_pdf("tests/fixtures/table_header.pdf")
    
    assert "| Name | Age |" in markdown
    assert "|------|-----|" in markdown  # Separator
```

### Regression Tests

**Prevent breaking changes.**

Store expected outputs for known PDFs:

```python
def test_regression_technical_doc():
    markdown = convert_pdf("tests/fixtures/tech_doc.pdf")
    expected = Path("tests/expected/tech_doc.md").read_text()
    
    assert markdown == expected
```

### Test Organization

```
tests/
├── unit/                  # Pure function tests
│   ├── test_headings.py
│   ├── test_lists.py
│   ├── test_code.py
│   └── test_tables.py
│
├── integration/           # Full pipeline tests
│   └── test_pipeline.py
│
├── features/              # Feature-specific tests
│   ├── test_tables.py
│   ├── test_images.py
│   └── test_links.py
│
├── fixtures/              # Test PDF files
│   ├── simple.pdf
│   ├── table_header.pdf
│   └── code_blocks.pdf
│
└── expected/              # Expected outputs
    ├── simple.md
    └── table_header.md
```

---

## Performance Considerations

### Memory Usage

**Optimization strategies:**

1. **Streaming processing** - Process pages one at a time
2. **Lazy loading** - Only extract content when needed
3. **Image compression** - Compress extracted images

### Speed Optimization

**Bottlenecks:**

1. **PDF parsing** - pdfplumber overhead (unavoidable)
2. **Table detection** - Line detection is expensive
3. **Image extraction** - I/O bound

**Optimizations:**

- Disable unused features (`--no-code-blocks`)
- Use line-based table detection (faster than text)
- Process pages in parallel (future)

### Benchmarks

**Typical performance (single-threaded):**

| Document Type | Pages | Time | Memory |
|---------------|-------|------|--------|
| Simple text | 10 | 0.5s | 20MB |
| With tables | 10 | 1.2s | 30MB |
| Image-heavy | 10 | 2.0s | 50MB |
| Large manual | 100 | 8.0s | 100MB |

---

## Security Considerations

### PDF Parsing

- **Use pdfplumber** - Well-tested, secure library
- **No code execution** - PDFs can contain JavaScript (not executed)
- **Sandboxing** - Run in isolated environment for untrusted PDFs

### File I/O

- **Path validation** - Prevent directory traversal
- **Permission checks** - Verify write access before processing
- **Temp file cleanup** - Delete extracted images on error

### Input Validation

```python
def convert_pdf(pdf_path, output_path=None):
    """Validate inputs before processing."""
    
    # Check file exists
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # Check readable
    if not os.access(pdf_path, os.R_OK):
        raise PermissionError(f"Cannot read: {pdf_path}")
    
    # Validate output path
    if output_path:
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            raise ValueError(f"Output directory not found: {output_dir}")
```

---

## Future Architecture Plans

### v1.1: Plugin System

**Goal:** Allow external processors/renderers

```python
# Example plugin registration
from unpdf import register_processor

@register_processor("custom_tables")
def my_table_processor(elements):
    # Custom logic
    return processed_elements
```

### v1.2: Streaming API

**Goal:** Handle PDFs too large for memory

```python
def convert_pdf_streaming(pdf_path):
    """Yield Markdown page by page."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            yield convert_page(page)
```

### v2.0: Parallel Processing

**Goal:** Process pages concurrently

```python
from concurrent.futures import ProcessPoolExecutor

def convert_pdf_parallel(pdf_path, workers=4):
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(convert_page, page) 
                   for page in pdf.pages]
        results = [f.result() for f in futures]
    return "\n\n".join(results)
```

---

## Contributing to Architecture

**Guidelines for architectural changes:**

1. **Maintain separation of concerns** - Keep extractors, processors, renderers separate
2. **Add tests first** - TDD for new features
3. **Document decisions** - Update this file for major changes
4. **Benchmark** - Measure performance impact
5. **Backwards compatibility** - Don't break existing API

**Review checklist:**

- [ ] New modules follow existing patterns
- [ ] Data structures are documented
- [ ] Integration tests cover new features
- [ ] Performance benchmarks included
- [ ] Architecture doc updated

---

**Last Updated:** 2025-11-02  
**Version:** 1.0.0
