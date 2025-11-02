"""Unit tests for unpdf.processors.blockquote module."""

from unpdf.processors.blockquote import BlockquoteElement, BlockquoteProcessor
from unpdf.processors.headings import ParagraphElement


def test_blockquote_element_to_markdown():
    """Test BlockquoteElement markdown generation."""
    quote = BlockquoteElement("Quote text", level=0)
    assert quote.to_markdown() == "> Quote text"


def test_blockquote_element_nested():
    """Test nested BlockquoteElement."""
    quote = BlockquoteElement("Nested quote", level=1)
    assert quote.to_markdown() == "> > Nested quote"

    double_nested = BlockquoteElement("Double nested", level=2)
    assert double_nested.to_markdown() == "> > > Double nested"


def test_blockquote_processor_initialization():
    """Test BlockquoteProcessor initialization."""
    processor = BlockquoteProcessor(base_indent=100.0, quote_threshold=50.0)
    assert processor.base_indent == 100.0
    assert processor.quote_threshold == 50.0


def test_blockquote_processor_detects_indented():
    """Test detection of indented text as blockquote."""
    processor = BlockquoteProcessor(base_indent=72.0, quote_threshold=40.0)

    # Indented enough to be quote (72 + 40 = 112)
    span = {"text": "This is a quote", "x0": 120.0}
    result = processor.process(span)

    assert isinstance(result, BlockquoteElement)
    assert result.text == "This is a quote"
    assert result.level == 0


def test_blockquote_processor_rejects_normal_indent():
    """Test that normal indent is not detected as quote."""
    processor = BlockquoteProcessor(base_indent=72.0, quote_threshold=40.0)

    # Not indented enough (below threshold)
    span = {"text": "Normal paragraph", "x0": 80.0}
    result = processor.process(span)

    assert isinstance(result, ParagraphElement)
    assert result.text == "Normal paragraph"


def test_blockquote_processor_calculates_nesting():
    """Test nesting level calculation."""
    processor = BlockquoteProcessor(
        base_indent=72.0, quote_threshold=40.0, nested_threshold=30.0
    )

    # Level 0: just over threshold
    span0 = {"text": "Level 0", "x0": 115.0}  # 72 + 40 + 3
    result0 = processor.process(span0)
    assert isinstance(result0, BlockquoteElement)
    assert result0.level == 0

    # Level 1: one nesting deeper
    span1 = {"text": "Level 1", "x0": 145.0}  # 72 + 40 + 30 + 3
    result1 = processor.process(span1)
    assert isinstance(result1, BlockquoteElement)
    assert result1.level == 1


def test_blockquote_processor_removes_quote_marks():
    """Test removal of quote marks from text."""
    processor = BlockquoteProcessor()

    # Double quotes
    span1 = {"text": '"This is quoted"', "x0": 120.0}
    result1 = processor.process(span1)
    assert isinstance(result1, BlockquoteElement)
    assert result1.text == "This is quoted"

    # Smart quotes
    span2 = {"text": '"Smart quotes"', "x0": 120.0}
    result2 = processor.process(span2)
    assert isinstance(result2, BlockquoteElement)
    assert result2.text == "Smart quotes"

    # Single leading quote
    span3 = {"text": '"Only leading', "x0": 120.0}
    result3 = processor.process(span3)
    assert isinstance(result3, BlockquoteElement)
    assert result3.text == "Only leading"


def test_blockquote_processor_remove_quote_marks_method():
    """Test quote mark removal method."""
    processor = BlockquoteProcessor()

    assert processor._remove_quote_marks('"Quote"') == "Quote"
    assert processor._remove_quote_marks('"Quote') == "Quote"
    assert processor._remove_quote_marks('Quote"') == "Quote"
    assert processor._remove_quote_marks("'Quote'") == "Quote"
    assert processor._remove_quote_marks("No quotes") == "No quotes"
    assert processor._remove_quote_marks("") == ""


def test_blockquote_processor_max_nesting():
    """Test that nesting is capped at 5 levels."""
    processor = BlockquoteProcessor(
        base_indent=72.0, quote_threshold=40.0, nested_threshold=20.0
    )

    # Very deep indent (should cap at level 5)
    span = {"text": "Deep", "x0": 300.0}
    result = processor.process(span)

    assert isinstance(result, BlockquoteElement)
    assert result.level <= 5
