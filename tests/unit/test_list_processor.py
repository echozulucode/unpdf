"""Unit tests for unpdf.processors.lists module."""

from unpdf.processors.headings import ParagraphElement
from unpdf.processors.lists import ListItemElement, ListProcessor


def test_list_item_element_to_markdown_bullet():
    """Test ListItemElement markdown for bullet lists."""
    item = ListItemElement("First item", is_ordered=False, indent_level=0)
    assert item.to_markdown() == "- First item"


def test_list_item_element_to_markdown_numbered():
    """Test ListItemElement markdown for numbered lists."""
    item = ListItemElement("First item", is_ordered=True, indent_level=0)
    assert item.to_markdown() == "1. First item"


def test_list_item_element_to_markdown_nested():
    """Test ListItemElement markdown with indentation."""
    item = ListItemElement("Nested item", is_ordered=False, indent_level=1)
    assert item.to_markdown() == "    - Nested item"

    item2 = ListItemElement("Double nested", is_ordered=True, indent_level=2)
    assert item2.to_markdown() == "        1. Double nested"


def test_list_processor_initialization():
    """Test ListProcessor initialization."""
    processor = ListProcessor(base_indent=100.0, indent_threshold=25.0)
    assert processor.base_indent == 100.0
    assert processor.indent_threshold == 25.0


def test_list_processor_detects_bullet():
    """Test bullet list detection."""
    processor = ListProcessor()

    span = {"text": "• First item", "x0": 72.0}
    result = processor.process(span)

    assert isinstance(result, ListItemElement)
    assert result.text == "First item"
    assert result.is_ordered is False
    assert result.indent_level == 0


def test_list_processor_detects_various_bullets():
    """Test detection of various bullet characters."""
    processor = ListProcessor()

    bullets = ["•", "●", "○", "▪", "-", "–", "·"]

    for bullet in bullets:
        span = {"text": f"{bullet} Item", "x0": 72.0}
        result = processor.process(span)

        assert isinstance(result, ListItemElement), f"Failed for bullet: {bullet}"
        assert result.text == "Item"
        assert result.is_ordered is False


def test_list_processor_detects_numbered():
    """Test numbered list detection."""
    processor = ListProcessor()

    # Numeric
    span1 = {"text": "1. First item", "x0": 72.0}
    result1 = processor.process(span1)
    assert isinstance(result1, ListItemElement)
    assert result1.text == "First item"
    assert result1.is_ordered is True

    # Letter
    span2 = {"text": "a) Second item", "x0": 72.0}
    result2 = processor.process(span2)
    assert isinstance(result2, ListItemElement)
    assert result2.text == "Second item"
    assert result2.is_ordered is True

    # Roman numerals
    span3 = {"text": "i. Third item", "x0": 72.0}
    result3 = processor.process(span3)
    assert isinstance(result3, ListItemElement)
    assert result3.text == "Third item"
    assert result3.is_ordered is True


def test_list_processor_detects_paragraph():
    """Test that non-list text becomes paragraph."""
    processor = ListProcessor()

    span = {"text": "Just a regular paragraph", "x0": 72.0}
    result = processor.process(span)

    assert isinstance(result, ParagraphElement)
    assert result.text == "Just a regular paragraph"


def test_list_processor_calculates_indent_level():
    """Test indent level calculation from x-coordinate."""
    processor = ListProcessor(base_indent=72.0, indent_threshold=20.0)

    # Base level
    assert processor._calculate_indent_level(72.0) == 0
    assert processor._calculate_indent_level(70.0) == 0

    # First indent
    assert processor._calculate_indent_level(92.0) == 1  # 72 + 20

    # Second indent
    assert processor._calculate_indent_level(112.0) == 2  # 72 + 40


def test_list_processor_nested_bullet():
    """Test nested bullet list detection."""
    processor = ListProcessor(base_indent=72.0, indent_threshold=20.0)

    # Top level
    span1 = {"text": "• Top item", "x0": 72.0}
    result1 = processor.process(span1)
    assert isinstance(result1, ListItemElement)
    assert result1.indent_level == 0

    # Nested level
    span2 = {"text": "• Nested item", "x0": 100.0}
    result2 = processor.process(span2)
    assert isinstance(result2, ListItemElement)
    assert result2.indent_level == 1


def test_list_processor_remove_bullet():
    """Test bullet character removal."""
    processor = ListProcessor()

    assert processor._remove_bullet("• Text") == "Text"
    assert processor._remove_bullet("•  Text with spaces") == "Text with spaces"
    assert processor._remove_bullet("- Item") == "Item"


def test_list_processor_is_bullet_list():
    """Test bullet detection method."""
    processor = ListProcessor()

    assert processor._is_bullet_list("• Item") is True
    assert processor._is_bullet_list("- Item") is True
    assert processor._is_bullet_list("Plain text") is False
    assert processor._is_bullet_list("") is False
