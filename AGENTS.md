# AI Agent Instructions for unpdf Development

**Last Updated:** 2025-11-02  
**Project:** unpdf - Simple, MIT-licensed PDF-to-Markdown converter

---

## Project Mission

Build a **simple, transparent, MIT-licensed** PDF-to-Markdown converter that excels at common use cases (documentation, technical content, business reports) through rule-based, predictable conversion without ML dependencies.

### Core Principles

1. **Simplicity over completeness** - Better quality on 80% of use cases than mediocre on 100%
2. **Transparency over magic** - Developers should understand why conversions happen
3. **Speed over accuracy edge cases** - Sub-second conversion on typical documents
4. **MIT licensing** - No AGPL contamination, no commercial restrictions
5. **Developer-first** - Easy to use, extend, and contribute to

---

## Differentiation Strategy

### We Are NOT Competing With
- **PyMuPDF** - Complex, AGPL-licensed, feature-rich, handles everything
- **Marker** - ML-based, GPU-powered, commercial licensing, complex pipelines

### We ARE Targeting
- Developers who need **fast, predictable, explainable** PDF conversion
- Projects requiring **true MIT licensing** (no AGPL viral effects)
- Use cases: documentation, technical content, business reports
- Environments: serverless, edge computing, CI/CD pipelines
- Teams: wanting **lightweight dependencies** and **simple codebase**

### Positioning Statement
> "unpdf is the simple, MIT-licensed PDF-to-Markdown converter for developers who value transparency, predictability, and ease of use over handling every edge case."

---

## Architecture Vision

### Package Structure
```
unpdf/
├── __init__.py           # Main API: convert_pdf()
├── core.py               # Conversion pipeline orchestration
├── cli.py                # Command-line interface
├── extractors/           # PDF content extraction
│   ├── text.py           # Text extraction with metadata
│   ├── tables.py         # Table detection & extraction
│   └── images.py         # Image extraction & saving
├── processors/           # Content processing & classification
│   ├── headings.py       # Heading detection (font-size based)
│   ├── lists.py          # List detection (bullets, numbers)
│   ├── code.py           # Code block detection (monospace fonts)
│   ├── blockquotes.py    # Quote detection
│   └── links.py          # Hyperlink processing
└── renderers/            # Output generation
    ├── markdown.py       # Markdown rendering
    └── html.py           # (Future) HTML output
```

### Design Pattern: Pipeline Architecture
1. **Extractors** - Pull raw content from PDF (text, tables, images)
2. **Processors** - Classify and transform content (identify headings, lists, code)
3. **Renderers** - Output in target format (Markdown, HTML)

Each stage is **independent**, **testable**, and **replaceable** (plugin system).

---

## Development Guidelines

### Code Style

**Formatting:** Use **Black** (line length: 88 characters)  
**Docstrings:** Use **Google-style** docstrings  
**Type Hints:** Required on all public functions (Python 3.10+)

#### Simplicity First
```python
# GOOD - Clear, explicit, readable
def is_heading(text_span: TextSpan, avg_font_size: float) -> bool:
    """Detect if text is a heading based on font size.

    Args:
        text_span: Text element with font metadata.
        avg_font_size: Average font size in the document.

    Returns:
        True if text should be treated as a heading.

    Example:
        >>> span = TextSpan("Title", font_size=24)
        >>> is_heading(span, avg_font_size=12)
        True
    """
    return text_span.font_size > avg_font_size * 1.3


# BAD - Over-engineered, no clarity
def classify_text_element(span, context, model, threshold=0.85):
    features = extract_features(span, context)
    prediction = model.predict(features)
    return prediction[0] if prediction[1] > threshold else None
```

#### No Hidden Magic
```python
# GOOD - Explicit behavior with clear documentation
def convert_pdf(
    pdf_path: Path,
    output_path: Path | None = None,
    force_ocr: bool = False,
) -> str:
    """Convert PDF to Markdown.

    Args:
        pdf_path: Path to PDF file to convert.
        output_path: Output path (default: same name with .md extension).
        force_ocr: Force OCR even if text is embedded in PDF.

    Returns:
        Converted Markdown content as string.

    Raises:
        FileNotFoundError: If pdf_path does not exist.
        ValueError: If PDF is corrupted or unreadable.

    Example:
        >>> markdown = convert_pdf("document.pdf")
        >>> print(markdown[:50])
        # Document Title

        First paragraph...
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    # ... implementation


# BAD - Hidden complexity, unclear behavior
def convert(input, **kwargs):
    """Convert something."""
    # Autodetects everything, unpredictable behavior
    pass
```

#### Transparent Decisions
```python
# GOOD - Log reasoning for debugging
def process_text_span(
    text_span: TextSpan, avg_size: float
) -> HeadingElement | ParagraphElement:
    """Process text span and classify as heading or paragraph.

    Args:
        text_span: Text element to process.
        avg_size: Average font size for comparison.

    Returns:
        Either a HeadingElement or ParagraphElement.
    """
    threshold = avg_size * 1.3
    if text_span.font_size > threshold:
        logger.debug(
            f"Detected heading: font_size={text_span.font_size:.1f} "
            f"> threshold={threshold:.1f}"
        )
        return HeadingElement(text_span.text, level=1)
    return ParagraphElement(text_span.text)


# BAD - Black box, no explanation
def process_span(span):
    if _is_heading_ml(span):
        return HeadingElement(span.text, level=1)
    return ParagraphElement(span.text)
```

### Google-Style Docstring Format

**Use this format for all public functions, classes, and methods:**

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """One-line summary (imperative mood, ends with period).

    Optional longer description that provides more details about what
    the function does. Can span multiple lines.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter. Can span
            multiple lines if needed.

    Returns:
        Description of return value.

    Raises:
        ErrorType: Description of when this error is raised.
        AnotherError: Description of another error condition.

    Example:
        >>> result = function_name("value1", 42)
        >>> print(result)
        expected output

    Note:
        Additional notes or warnings if needed.
    """
    pass
```

**Real Example:**

```python
from pathlib import Path
from typing import Any


def extract_text_with_metadata(
    pdf_path: Path, pages: list[int] | None = None
) -> list[dict[str, Any]]:
    """Extract text and metadata from PDF pages.

    Reads the PDF file and extracts text content along with font
    information (size, family, weight) for each text span. This metadata
    is used later to classify text as headings, paragraphs, or code.

    Args:
        pdf_path: Path to the PDF file to process.
        pages: Optional list of specific page numbers to process
            (1-indexed). If None, processes all pages.

    Returns:
        List of dictionaries, one per text span, containing:
            - text (str): The actual text content.
            - font_size (float): Font size in points.
            - font_family (str): Font family name.
            - is_bold (bool): Whether text is bold.
            - is_italic (bool): Whether text is italic.
            - bbox (tuple): Bounding box (x0, y0, x1, y1).

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If PDF is corrupted or password-protected.

    Example:
        >>> spans = extract_text_with_metadata(Path("doc.pdf"))
        >>> print(spans[0])
        {
            'text': 'Document Title',
            'font_size': 24.0,
            'font_family': 'Helvetica-Bold',
            'is_bold': True,
            'is_italic': False,
            'bbox': (72, 720, 540, 750)
        }

    Note:
        Font detection relies on PDF metadata. Some PDFs may not have
        accurate font information, especially if generated incorrectly.
    """
    pass
```

**Class Example:**

```python
class HeadingProcessor:
    """Process and classify text as headings based on font size.

    The HeadingProcessor analyzes text spans and determines if they should
    be treated as headings based on their font size relative to the
    document average. Heading levels (H1-H6) are assigned based on
    relative size differences.

    Attributes:
        avg_font_size: Average font size in the document.
        heading_ratio: Multiplier to determine heading threshold.
            Default is 1.3 (30% larger than average).

    Example:
        >>> processor = HeadingProcessor(avg_font_size=12.0)
        >>> element = processor.process(TextSpan("Title", font_size=24))
        >>> isinstance(element, HeadingElement)
        True
        >>> element.level
        1
    """

    def __init__(self, avg_font_size: float, heading_ratio: float = 1.3):
        """Initialize HeadingProcessor.

        Args:
            avg_font_size: Average font size in the document.
            heading_ratio: Multiplier for heading detection threshold.
        """
        self.avg_font_size = avg_font_size
        self.heading_ratio = heading_ratio

    def process(self, text_span: TextSpan) -> HeadingElement | ParagraphElement:
        """Process text span and classify as heading or paragraph.

        Args:
            text_span: Text element to process.

        Returns:
            HeadingElement if detected as heading, otherwise ParagraphElement.
        """
        threshold = self.avg_font_size * self.heading_ratio
        if text_span.font_size > threshold:
            level = self._calculate_level(text_span.font_size)
            return HeadingElement(text_span.text, level=level)
        return ParagraphElement(text_span.text)

    def _calculate_level(self, font_size: float) -> int:
        """Calculate heading level based on font size.

        Args:
            font_size: Font size to analyze.

        Returns:
            Heading level from 1 (largest) to 6 (smallest).
        """
        # Implementation...
        pass
```

### Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Installation time | < 10 seconds | No large model downloads |
| Dependencies | < 10 packages | Minimize surface area |
| Memory per page | < 50 MB | Enable serverless deployment |
| Processing speed | < 0.5s/page | Typical documents (text-heavy) |
| Cold start | < 1 second | No model loading |

### Testing Philosophy

#### Test Pyramid
1. **Unit tests (70%)** - Test individual extractors/processors
2. **Integration tests (20%)** - Test full pipeline on sample PDFs
3. **Round-trip tests (10%)** - Markdown → PDF → Markdown comparison

#### Example Test Structure
```python
def test_heading_detection():
    """Test font-size based heading detection."""
    # Given: Text with varying font sizes
    text_spans = [
        TextSpan("Title", font_size=24),
        TextSpan("Body", font_size=12),
        TextSpan("Heading", font_size=18),
    ]
    avg_size = 12
    
    # When: Processing text
    processor = HeadingProcessor(avg_font_size=avg_size)
    elements = [processor.process(span) for span in text_spans]
    
    # Then: Correct classification
    assert isinstance(elements[0], HeadingElement)
    assert elements[0].level == 1  # Largest
    assert isinstance(elements[1], ParagraphElement)
    assert isinstance(elements[2], HeadingElement)
    assert elements[2].level == 2  # Medium
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Working skeleton with simple text extraction

**AI Agent Tasks:**
1. Create package structure (unpdf/, extractors/, processors/, renderers/)
2. Setup pyproject.toml with MIT license and minimal dependencies
3. Implement basic text extraction using pdfplumber
4. Create CLI entry point: `unpdf input.pdf`
5. Add unit tests for text extraction

**Success Criteria:**
- `unpdf sample.pdf` creates `sample.md` with plain text
- Tests pass, type hints present
- < 5 dependencies in pyproject.toml

### Phase 2: Text Formatting (Week 2)
**Goal:** Bold, italic, font style detection

**AI Agent Tasks:**
1. Implement font metadata extraction
2. Detect bold text (font name contains "Bold" or weight > 600)
3. Detect italic text (font name contains "Italic" or angle != 0)
4. Wrap in Markdown formatting (`**bold**`, `*italic*`)
5. Test on PDFs with varied formatting

**Success Criteria:**
- Bold/italic text correctly wrapped in Markdown
- Handles combined formatting (bold + italic)
- Clear logging of detection decisions

### Phase 3: Structure (Week 3)
**Goal:** Headings, lists, blockquotes

**AI Agent Tasks:**
1. Implement heading detection (font-size threshold heuristic)
2. Map heading levels (#, ##, ###) based on relative size
3. Detect bullet lists (•, –, -, etc.) and numbered lists
4. Preserve list nesting via indentation
5. Detect blockquotes (indent > threshold or quote prefix)

**Success Criteria:**
- Document structure preserved (heading hierarchy)
- Lists properly nested and formatted
- Clear about detection thresholds in docs

### Phase 4: Code Detection (Week 4)
**Goal:** Code blocks and inline code

**AI Agent Tasks:**
1. Detect monospaced fonts (Courier, Consolas, etc.)
2. Distinguish inline code (`code`) vs blocks (```)
3. Preserve code indentation and whitespace
4. Optional: infer language from context

**Success Criteria:**
- Code blocks properly fenced with backticks
- Inline code identified correctly
- No false positives on regular text

### Phase 5: Tables (Week 5-6)
**Goal:** Table extraction and pipe-table rendering

**AI Agent Tasks:**
1. Integrate pdfplumber or Camelot table detection
2. Detect tables via grid lines or column alignment
3. Convert to Markdown pipe tables
4. Handle merged cells (best effort)
5. Fallback to plain text for complex tables

**Success Criteria:**
- Simple tables render as pipe tables
- Complex tables degrade gracefully
- Clear warnings when fallback used

### Phase 6: Images & Links (Week 7)
**Goal:** Extract images, preserve hyperlinks

**AI Agent Tasks:**
1. Extract embedded images (JPEG, PNG)
2. Save to separate files with unique names
3. Insert `![alt](image.png)` references
4. Detect PDF hyperlink annotations
5. Convert to `[text](url)` format

**Success Criteria:**
- Images extracted and referenced
- Links preserved with proper formatting
- Alt text generated from captions if available

### Phase 7: Polish & CLI (Week 8)
**Goal:** Production-ready CLI and error handling

**AI Agent Tasks:**
1. Implement full CLI with argparse
2. Add flags: `-o/--output`, `--pages`, `--verbose`
3. Default output: same name with .md extension
4. Batch processing for directories
5. Graceful error handling with helpful messages

**Success Criteria:**
- `unpdf --help` shows clear usage
- Errors provide actionable guidance
- Works on single files and directories

### Phase 8: Testing & Validation (Week 9)
**Goal:** Comprehensive test coverage

**AI Agent Tasks:**
1. Round-trip tests (Markdown → PDF → Markdown)
2. Feature-specific tests (one per feature)
3. Edge case tests (empty pages, weird fonts)
4. Integration tests on real-world PDFs
5. Aim for >80% test coverage

**Success Criteria:**
- All tests pass in CI
- Coverage report shows >80%
- Edge cases documented and tested

### Phase 9: Documentation (Week 10)
**Goal:** Clear, comprehensive docs

**AI Agent Tasks:**
1. README with quick start and examples
2. API documentation (docstrings)
3. Architecture guide for contributors
4. Feature support matrix
5. Limitations clearly documented

**Success Criteria:**
- New user can get started in < 5 minutes
- Contributors understand architecture
- Limitations clearly stated

### Phase 10: Release (Week 11)
**Goal:** Published on PyPI

**AI Agent Tasks:**
1. Finalize version 1.0.0
2. Test installation from TestPyPI
3. Publish to PyPI as `unpdf`
4. Create GitHub release with examples
5. Announce in relevant communities

**Success Criteria:**
- `pip install unpdf` works
- GitHub stars > 0
- At least one external contribution/issue

---

## AI Agent Decision Framework

### When to Add Complexity
✅ **Add if:**
- Required for core use cases (documentation, technical content)
- Improves common-case quality significantly
- Keeps dependencies minimal (<10 total)
- Doesn't require ML/GPU

❌ **Skip if:**
- Only helps edge cases (<5% of documents)
- Requires large dependencies (torch, transformers)
- Makes code harder to understand
- Requires GPU/specialized hardware

### Example Decisions

| Feature | Decision | Rationale |
|---------|----------|-----------|
| Basic heading detection | ✅ Add | Core feature, font-size heuristic simple |
| ML-based layout analysis | ❌ Skip | Complexity, requires GPU, against principles |
| Table detection | ✅ Add | Important for business docs, pdfplumber handles it |
| Equation support | ❌ Skip | Edge case, requires complex parsing or ML |
| Hyperlink extraction | ✅ Add | Common feature, straightforward implementation |
| OCR for scanned PDFs | ❌ Core, ✅ Plugin | Optional feature, keep base lightweight |

### When to Fail Gracefully
```python
# GOOD - Clear failure message
if has_complex_layout(page):
    logger.warning(
        "Complex multi-column layout detected. "
        "Output may not preserve reading order. "
        "Consider using --force-ocr or PyMuPDF for this document."
    )
    # Continue with best effort
```

---

## Prompt Templates for AI Agents

### For Code Generation
```
Task: Implement [feature] for unpdf

Context:
- unpdf is a simple, rule-based PDF-to-Markdown converter
- No ML dependencies allowed
- Must be explainable and predictable
- Target: documentation and technical content

Requirements:
1. Use pdfplumber for PDF access
2. Add type hints (Python 3.10+)
3. Log detection decisions at DEBUG level
4. Include docstrings with examples
5. Write unit tests

Keep it simple: prefer explicit heuristics over complex algorithms.
```

### For Code Review
```
Review this code for unpdf against these principles:
1. Simplicity - Is this the simplest solution?
2. Transparency - Can developers understand the logic?
3. Performance - Will this run fast (<0.5s/page)?
4. Dependencies - Does this add new dependencies?
5. Testing - Is this easily testable?

Suggest simplifications if code is over-engineered.
```

### For Documentation
```
Document [feature] for unpdf users:
1. What it does (plain language)
2. When it works well (use cases)
3. When it doesn't (limitations)
4. How to configure (if applicable)
5. Example usage

Tone: Honest, direct, helpful. Don't oversell capabilities.
```

---

## Quality Gates

### Before Committing Code
- [ ] Type hints on all functions
- [ ] Docstrings with examples
- [ ] Unit tests written and passing
- [ ] No new dependencies without approval
- [ ] Runs in < 0.5s/page on sample PDFs
- [ ] Logging explains decisions

### Before Merging PR
- [ ] All tests pass in CI
- [ ] Code review by human (if available)
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added
- [ ] No performance regressions

### Before Release
- [ ] All quality gates passed
- [ ] Round-trip tests passing
- [ ] Documentation complete
- [ ] Examples included
- [ ] License compliance verified (MIT only)

---

## Common Pitfalls to Avoid

### ❌ Don't: Over-engineer
```python
# BAD
class AbstractProcessorFactory:
    def create_processor(self, processor_type: ProcessorType) -> BaseProcessor:
        return self.registry[processor_type]()
```

### ✅ Do: Keep it simple
```python
# GOOD
def process_text(text_span, avg_font_size):
    if text_span.font_size > avg_font_size * 1.3:
        return heading_markdown(text_span)
    return paragraph_markdown(text_span)
```

### ❌ Don't: Add ML without justification
```python
# BAD - Requires torch, tensorflow
model = load_layout_detection_model()
layout = model.predict(page_image)
```

### ✅ Do: Use rule-based approaches
```python
# GOOD - Simple, fast, predictable
def detect_columns(text_spans):
    x_coords = [span.x0 for span in text_spans]
    gaps = find_large_gaps(x_coords, min_gap=50)
    return split_by_gaps(text_spans, gaps)
```

### ❌ Don't: Hide complexity
```python
# BAD
convert_pdf(input, smart_mode=True)  # What does smart_mode do?
```

### ✅ Do: Be explicit
```python
# GOOD
convert_pdf(
    input,
    detect_headings=True,
    heading_font_size_ratio=1.3,
    detect_code_blocks=True,
    code_fonts=['Courier', 'Consolas']
)
```

---

## Success Metrics (v1.0)

### Technical
- [ ] Installation < 10 seconds
- [ ] Processing < 0.5s/page (typical docs)
- [ ] Memory < 50MB per page
- [ ] Dependencies < 10 packages
- [ ] Test coverage > 80%

### Quality
- [ ] Round-trip tests pass (>95% content match)
- [ ] Handles 80% of target documents well
- [ ] Clear error messages for remaining 20%

### Community
- [ ] Published on PyPI
- [ ] >50 GitHub stars in first month
- [ ] >5 external issues/PRs
- [ ] Clear documentation
- [ ] MIT license verified

---

## Contact & Resources

- **Repository:** [To be created]
- **Documentation:** [To be created]
- **Issues:** [GitHub Issues]
- **Discussions:** [GitHub Discussions]
- **License:** MIT (strict requirement)

---

## Version History

- **2025-11-02:** Initial agent instructions created
- **Future:** Will be updated as project evolves

---

**Remember:** When in doubt, choose simplicity. Our users value predictability and ease of use over handling every possible edge case.
