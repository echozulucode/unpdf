"""Unit tests for unpdf.renderers.markdown module."""

from unpdf.renderers.markdown import _apply_inline_formatting, render_spans_to_markdown


def test_apply_inline_formatting_plain():
    """Test that plain text is unchanged."""
    assert _apply_inline_formatting("Hello", False, False) == "Hello"


def test_apply_inline_formatting_bold():
    """Test bold formatting."""
    assert _apply_inline_formatting("Hello", True, False) == "**Hello**"


def test_apply_inline_formatting_italic():
    """Test italic formatting."""
    assert _apply_inline_formatting("Hello", False, True) == "*Hello*"


def test_apply_inline_formatting_bold_italic():
    """Test combined bold and italic formatting."""
    assert _apply_inline_formatting("Hello", True, True) == "***Hello***"


def test_apply_inline_formatting_whitespace():
    """Test that whitespace-only text is preserved."""
    assert _apply_inline_formatting("   ", False, False) == "   "
    assert _apply_inline_formatting(" ", True, False) == " "


def test_render_spans_to_markdown_empty():
    """Test rendering empty span list."""
    assert render_spans_to_markdown([]) == ""


def test_render_spans_to_markdown_single_span():
    """Test rendering single text span."""
    spans = [
        {
            "text": "Hello world",
            "is_bold": False,
            "is_italic": False,
            "y0": 100,
        }
    ]
    assert render_spans_to_markdown(spans) == "Hello world"


def test_render_spans_to_markdown_bold_text():
    """Test rendering bold text."""
    spans = [
        {
            "text": "Bold text",
            "is_bold": True,
            "is_italic": False,
            "y0": 100,
        }
    ]
    assert render_spans_to_markdown(spans) == "**Bold text**"


def test_render_spans_to_markdown_mixed_formatting():
    """Test rendering mixed bold and italic."""
    spans = [
        {"text": "Normal ", "is_bold": False, "is_italic": False, "y0": 100},
        {"text": "bold", "is_bold": True, "is_italic": False, "y0": 100},
        {"text": " and ", "is_bold": False, "is_italic": False, "y0": 100},
        {"text": "italic", "is_bold": False, "is_italic": True, "y0": 100},
        {"text": " text", "is_bold": False, "is_italic": False, "y0": 100},
    ]

    result = render_spans_to_markdown(spans)
    assert result == "Normal **bold** and *italic* text"


def test_render_spans_to_markdown_paragraph_break():
    """Test that vertical gaps create paragraph breaks."""
    spans = [
        {"text": "First paragraph", "is_bold": False, "is_italic": False, "y0": 100},
        {
            "text": "Second paragraph",
            "is_bold": False,
            "is_italic": False,
            "y0": 80,  # 20pt gap = new paragraph
        },
    ]

    result = render_spans_to_markdown(spans)
    assert result == "First paragraph\n\nSecond paragraph"


def test_render_spans_to_markdown_no_paragraph_break():
    """Test that small gaps don't create paragraph breaks."""
    spans = [
        {"text": "First line", "is_bold": False, "is_italic": False, "y0": 100},
        {
            "text": "Same paragraph",
            "is_bold": False,
            "is_italic": False,
            "y0": 95,  # 5pt gap = same paragraph
        },
    ]

    result = render_spans_to_markdown(spans)
    assert result == "First lineSame paragraph"


def test_render_spans_to_markdown_combined_bold_italic():
    """Test rendering combined bold and italic formatting."""
    spans = [
        {
            "text": "Bold and italic",
            "is_bold": True,
            "is_italic": True,
            "y0": 100,
        }
    ]

    result = render_spans_to_markdown(spans)
    assert result == "***Bold and italic***"
