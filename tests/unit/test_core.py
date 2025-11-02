"""Unit tests for unpdf.core module."""

from pathlib import Path

import pytest

from unpdf import convert_pdf


def test_convert_pdf_file_not_found():
    """Test that FileNotFoundError is raised for non-existent files."""
    with pytest.raises(FileNotFoundError, match="PDF file not found"):
        convert_pdf("nonexistent.pdf")


def test_convert_pdf_invalid_extension():
    """Test that ValueError is raised for non-PDF files."""
    with pytest.raises(ValueError, match="File must be a PDF"):
        convert_pdf("document.txt")


def test_convert_pdf_returns_string(tmp_path: Path):
    """Test that convert_pdf returns a string (placeholder for now).

    Args:
        tmp_path: Pytest fixture providing temporary directory.

    Note:
        This test uses a placeholder PDF. Once we implement extraction,
        we'll use real PDF fixtures.
    """
    # Create a fake PDF file for testing
    fake_pdf = tmp_path / "test.pdf"
    fake_pdf.write_text("%PDF-1.4\n%placeholder", encoding="latin-1")

    result = convert_pdf(fake_pdf)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "test.pdf" in result  # Should mention the filename


def test_convert_pdf_with_output_path(tmp_path: Path):
    """Test that convert_pdf writes to file when output_path provided.

    Args:
        tmp_path: Pytest fixture providing temporary directory.
    """
    # Create a fake PDF
    fake_pdf = tmp_path / "input.pdf"
    fake_pdf.write_text("%PDF-1.4\n%placeholder", encoding="latin-1")

    output_path = tmp_path / "output.md"
    result = convert_pdf(fake_pdf, output_path=output_path)

    # Should return the markdown
    assert isinstance(result, str)
    assert len(result) > 0

    # Should write to file
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert content == result
