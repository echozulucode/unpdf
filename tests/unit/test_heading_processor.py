"""Unit tests for unpdf.processors.headings module."""

import pytest

from unpdf.processors.headings import (
    HeadingElement,
    HeadingProcessor,
    ParagraphElement,
)


def test_heading_element_to_markdown():
    """Test HeadingElement markdown generation."""
    h1 = HeadingElement("Title", level=1)
    assert h1.to_markdown() == "# Title"

    h2 = HeadingElement("Section", level=2)
    assert h2.to_markdown() == "## Section"

    h6 = HeadingElement("Subsection", level=6)
    assert h6.to_markdown() == "###### Subsection"


def test_paragraph_element_to_markdown():
    """Test ParagraphElement markdown generation."""
    para = ParagraphElement("Plain text")
    assert para.to_markdown() == "Plain text"


def test_heading_processor_initialization():
    """Test HeadingProcessor initialization."""
    processor = HeadingProcessor(avg_font_size=12.0)
    assert processor.avg_font_size == 12.0
    assert processor.heading_ratio == 1.3  # Default
    assert abs(processor.threshold - 15.6) < 0.01  # 12 * 1.3 (with float tolerance)


def test_heading_processor_invalid_params():
    """Test HeadingProcessor with invalid parameters."""
    with pytest.raises(ValueError, match="max_level must be 1-6"):
        HeadingProcessor(12.0, max_level=0)

    with pytest.raises(ValueError, match="max_level must be 1-6"):
        HeadingProcessor(12.0, max_level=7)

    with pytest.raises(ValueError, match="avg_font_size must be positive"):
        HeadingProcessor(0)

    with pytest.raises(ValueError, match="heading_ratio must be > 1.0"):
        HeadingProcessor(12.0, heading_ratio=1.0)


def test_heading_processor_detects_large_text():
    """Test that large text is detected as heading."""
    processor = HeadingProcessor(avg_font_size=12.0, heading_ratio=1.5)
    # Threshold = 12 * 1.5 = 18pt

    span = {"text": "Big Title", "font_size": 24.0, "is_bold": True}
    result = processor.process(span)

    assert isinstance(result, HeadingElement)
    assert result.text == "Big Title"
    assert 1 <= result.level <= 6


def test_heading_processor_detects_paragraph():
    """Test that normal-sized text is paragraph."""
    processor = HeadingProcessor(avg_font_size=12.0, heading_ratio=1.5)
    # Threshold = 18pt

    span = {"text": "Normal text", "font_size": 12.0, "is_bold": False}
    result = processor.process(span)

    assert isinstance(result, ParagraphElement)
    assert result.text == "Normal text"


def test_heading_processor_level_calculation():
    """Test heading level is calculated based on size."""
    processor = HeadingProcessor(avg_font_size=12.0, heading_ratio=1.3)
    # Threshold = 15.6pt

    # Very large = H1
    span_h1 = {"text": "Huge", "font_size": 36.0, "is_bold": False}
    result_h1 = processor.process(span_h1)
    assert isinstance(result_h1, HeadingElement)
    assert result_h1.level == 1

    # Large = H2-H4 (size ratio 20/15.6 = 1.28, maps to H4 or better with bold)
    span_h2 = {"text": "Large", "font_size": 20.0, "is_bold": False}
    result_h2 = processor.process(span_h2)
    assert isinstance(result_h2, HeadingElement)
    assert 2 <= result_h2.level <= 4

    # Just above threshold = higher level number (but still relatively large at 1.33x body)
    span_h3 = {"text": "Small heading", "font_size": 16.0, "is_bold": False}
    result_h3 = processor.process(span_h3)
    assert isinstance(result_h3, HeadingElement)
    assert result_h3.level == 3  # 1.33x ratio maps to H3


def test_heading_processor_bold_affects_level():
    """Test that bold text gets priority in level."""
    processor = HeadingProcessor(avg_font_size=12.0)

    # Same font size, different bold
    span_bold = {"text": "Bold", "font_size": 18.0, "is_bold": True}
    span_normal = {"text": "Normal", "font_size": 18.0, "is_bold": False}

    result_bold = processor.process(span_bold)
    result_normal = processor.process(span_normal)

    # Bold should have lower level number (higher priority)
    if isinstance(result_bold, HeadingElement) and isinstance(
        result_normal, HeadingElement
    ):
        assert result_bold.level <= result_normal.level


def test_heading_processor_respects_max_level():
    """Test that max_level is respected."""
    processor = HeadingProcessor(avg_font_size=12.0, max_level=3)

    # Even very small headings shouldn't exceed max_level
    span = {"text": "Small", "font_size": 16.0, "is_bold": False}
    result = processor.process(span)

    if isinstance(result, HeadingElement):
        assert result.level <= 3
