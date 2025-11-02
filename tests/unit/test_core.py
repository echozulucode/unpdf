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


@pytest.mark.skip(reason="Requires real PDF fixture")
def test_convert_pdf_returns_string(tmp_path: Path):
    """Test that convert_pdf returns a string.

    Args:
        tmp_path: Pytest fixture providing temporary directory.

    Note:
        This test is skipped until we create sample PDF fixtures.
        Fake PDFs don't work with pdfplumber.
    """
    # Will be implemented when we have real PDF fixtures
    pass


@pytest.mark.skip(reason="Requires real PDF fixture")
def test_convert_pdf_with_output_path(tmp_path: Path):
    """Test that convert_pdf writes to file when output_path provided.

    Args:
        tmp_path: Pytest fixture providing temporary directory.

    Note:
        This test is skipped until we create sample PDF fixtures.
        Fake PDFs don't work with pdfplumber.
    """
    # Will be implemented when we have real PDF fixtures
    pass
