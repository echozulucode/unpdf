"""Pytest configuration and shared fixtures.

This module provides fixtures and configuration for all tests.
"""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory.

    Returns:
        Path to tests/fixtures/ directory.
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf(fixtures_dir: Path) -> Path:
    """Return path to a sample PDF file (to be created).

    Args:
        fixtures_dir: Path to fixtures directory.

    Returns:
        Path to sample.pdf file.

    Note:
        This fixture will fail until we create a sample PDF.
        For Phase 1, we'll skip tests that require actual PDFs.
    """
    pdf_path = fixtures_dir / "sample.pdf"
    if not pdf_path.exists():
        pytest.skip("Sample PDF not available yet")
    return pdf_path
