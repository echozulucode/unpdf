"""Unit tests for unpdf.extractors.text module."""

from pathlib import Path

import pytest

from unpdf.extractors.text import (
    _is_bold_font,
    _is_italic_font,
    _should_continue_span,
    calculate_average_font_size,
    extract_text_with_metadata,
)


def test_is_bold_font():
    """Test bold font detection from font names."""
    assert _is_bold_font("Helvetica-Bold")
    assert _is_bold_font("Arial-BoldMT")
    assert _is_bold_font("TimesNewRoman-Heavy")
    assert _is_bold_font("Calibri-Semibold")
    assert not _is_bold_font("Helvetica")
    assert not _is_bold_font("Arial-Italic")


def test_is_italic_font():
    """Test italic font detection from font names."""
    assert _is_italic_font("Helvetica-Oblique")
    assert _is_italic_font("Arial-ItalicMT")
    assert _is_italic_font("TimesNewRoman-Italic")
    assert not _is_italic_font("Helvetica-Bold")
    assert not _is_italic_font("Arial")


def test_should_continue_span_same_format():
    """Test span continuation when formatting matches."""
    current_span = {
        "font_family": "Helvetica",
        "font_size": 12.0,
        "is_bold": False,
        "is_italic": False,
    }

    assert _should_continue_span(current_span, "Helvetica", 12.0, False, False)
    assert _should_continue_span(
        current_span, "Helvetica", 12.05, False, False
    )  # Small diff OK


def test_should_continue_span_different_format():
    """Test span breaks when formatting changes."""
    current_span = {
        "font_family": "Helvetica",
        "font_size": 12.0,
        "is_bold": False,
        "is_italic": False,
    }

    # Different font
    assert not _should_continue_span(current_span, "Arial", 12.0, False, False)

    # Different size
    assert not _should_continue_span(current_span, "Helvetica", 14.0, False, False)

    # Different bold
    assert not _should_continue_span(current_span, "Helvetica", 12.0, True, False)

    # Different italic
    assert not _should_continue_span(current_span, "Helvetica", 12.0, False, True)


def test_calculate_average_font_size_empty():
    """Test average calculation with empty list."""
    assert calculate_average_font_size([]) == 12.0  # Default


def test_calculate_average_font_size_single():
    """Test average calculation with single span."""
    spans = [{"text": "Hello", "font_size": 14.0}]
    assert calculate_average_font_size(spans) == 14.0


def test_calculate_average_font_size_weighted():
    """Test that average is weighted by text length."""
    spans = [
        {"text": "Short", "font_size": 24.0},  # 5 chars at 24pt
        {"text": "This is a much longer text", "font_size": 12.0},  # 26 chars at 12pt
    ]

    avg = calculate_average_font_size(spans)
    # Weighted average: (5*24 + 26*12) / (5+26) = (120 + 312) / 31 = 13.9
    assert 13.8 < avg < 14.0


def test_extract_text_with_metadata_file_not_found():
    """Test that FileNotFoundError is raised for non-existent files."""
    with pytest.raises(FileNotFoundError, match="PDF not found"):
        extract_text_with_metadata(Path("nonexistent.pdf"))


@pytest.mark.skip(reason="Requires real PDF file")
def test_extract_text_with_metadata_real_pdf(sample_pdf):
    """Test extraction with real PDF file.

    Args:
        sample_pdf: Pytest fixture providing sample PDF path.

    Note:
        This test is skipped until we create sample PDF fixtures.
    """
    spans = extract_text_with_metadata(sample_pdf)

    assert len(spans) > 0
    assert all("text" in span for span in spans)
    assert all("font_size" in span for span in spans)
    assert all("is_bold" in span for span in spans)
    assert all("is_italic" in span for span in spans)
