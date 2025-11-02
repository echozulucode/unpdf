"""Tests for hyperlink extraction."""

from unittest.mock import Mock, patch

import pytest

from unpdf.processors.links import (
    LinkInfo,
    _extract_plain_urls,
    _extract_text_at_position,
    convert_link_to_markdown,
    extract_links,
)


@pytest.fixture
def mock_page_with_links():
    """Mock pdfplumber page with annotations."""
    page = Mock()
    page.annots = [
        {
            "uri": "https://example.com",
            "rect": [100, 200, 300, 220],
        },
        {
            "uri": "https://github.com/test",
            "rect": [100, 250, 300, 270],
        },
    ]
    page.extract_text = Mock(return_value="Visit https://python.org for more info")

    # Mock crop for text extraction
    crop = Mock()
    crop.extract_text = Mock(return_value="Example Link")
    page.crop = Mock(return_value=crop)

    return page


@pytest.fixture
def mock_pdf_with_links(mock_page_with_links):
    """Mock pdfplumber PDF object with links."""
    pdf = Mock()
    pdf.pages = [mock_page_with_links]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)
    return pdf


def test_extract_links_from_annotations(mock_pdf_with_links):
    """Test extracting links from PDF annotations."""
    with patch("pdfplumber.open", return_value=mock_pdf_with_links):
        links = extract_links("test.pdf")

        # Should have 2 annotation links + 1 plain URL
        assert len(links) >= 2
        annotation_links = [
            link
            for link in links
            if "example.com" in link.url or "github.com" in link.url
        ]
        assert len(annotation_links) == 2


def test_extract_plain_urls():
    """Test extraction of plain URLs from text."""
    text = "Visit https://example.com and http://github.com/test"
    urls = _extract_plain_urls(text)

    assert len(urls) == 2
    assert "https://example.com" in urls
    assert "http://github.com/test" in urls


def test_extract_plain_urls_no_urls():
    """Test extraction when no URLs are present."""
    text = "This is just plain text without any links"
    urls = _extract_plain_urls(text)

    assert len(urls) == 0


def test_extract_plain_urls_removes_duplicates():
    """Test that duplicate URLs are removed."""
    text = "Visit https://example.com and https://example.com again"
    urls = _extract_plain_urls(text)

    assert len(urls) == 1
    assert "https://example.com" in urls


def test_extract_plain_urls_complex():
    """Test extraction of URLs with query parameters and fragments."""
    text = "See https://example.com/path?param=value&other=123#section"
    urls = _extract_plain_urls(text)

    assert len(urls) >= 1
    assert any("example.com" in url for url in urls)


def test_convert_link_to_markdown_basic():
    """Test basic link to Markdown conversion."""
    link = LinkInfo(
        text="Example",
        url="https://example.com",
        page_num=1,
        x0=100,
        y0=200,
    )

    markdown = convert_link_to_markdown(link)
    assert markdown == "[Example](https://example.com)"


def test_convert_link_to_markdown_url_as_text():
    """Test link where text is the same as URL."""
    link = LinkInfo(
        text="https://example.com",
        url="https://example.com",
        page_num=1,
        x0=100,
        y0=200,
    )

    markdown = convert_link_to_markdown(link)
    assert markdown == "<https://example.com>"


def test_convert_link_to_markdown_escapes_brackets():
    """Test that brackets in link text are escaped."""
    link = LinkInfo(
        text="Example [with brackets]",
        url="https://example.com",
        page_num=1,
        x0=100,
        y0=200,
    )

    markdown = convert_link_to_markdown(link)
    assert markdown == "[Example \\[with brackets\\]](https://example.com)"


def test_extract_links_no_annotations():
    """Test link extraction when page has no annotations."""
    page = Mock()
    page.annots = None
    page.extract_text = Mock(return_value="Plain text with https://example.com")

    pdf = Mock()
    pdf.pages = [page]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)

    with patch("pdfplumber.open", return_value=pdf):
        links = extract_links("test.pdf")

        # Should still find the plain URL
        assert len(links) >= 1
        assert any("example.com" in link.url for link in links)


def test_extract_links_empty_annotations():
    """Test link extraction with empty annotations list."""
    page = Mock()
    page.annots = []
    page.extract_text = Mock(return_value="No links here")

    pdf = Mock()
    pdf.pages = [page]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)

    with patch("pdfplumber.open", return_value=pdf):
        links = extract_links("test.pdf")

        assert len(links) == 0


def test_extract_text_at_position():
    """Test text extraction at a specific position."""
    page = Mock()
    crop = Mock()
    crop.extract_text = Mock(return_value="Link Text")
    page.crop = Mock(return_value=crop)

    text = _extract_text_at_position(page, [100, 200, 300, 220])
    assert text == "Link Text"


def test_extract_text_at_position_handles_exception():
    """Test that text extraction handles exceptions gracefully."""
    page = Mock()
    page.crop = Mock(side_effect=Exception("Crop failed"))

    text = _extract_text_at_position(page, [100, 200, 300, 220])
    assert text is None


def test_extract_text_at_position_no_text():
    """Test text extraction when no text is at position."""
    page = Mock()
    crop = Mock()
    crop.extract_text = Mock(return_value=None)
    page.crop = Mock(return_value=crop)

    text = _extract_text_at_position(page, [100, 200, 300, 220])
    assert text is None


def test_link_info_creation():
    """Test LinkInfo object creation."""
    link = LinkInfo(
        text="Test Link",
        url="https://test.com",
        page_num=3,
        x0=150.0,
        y0=250.0,
    )

    assert link.text == "Test Link"
    assert link.url == "https://test.com"
    assert link.page_num == 3
    assert link.x0 == 150.0
    assert link.y0 == 250.0


def test_extract_links_annotation_without_uri():
    """Test that annotations without URI are skipped."""
    page = Mock()
    page.annots = [
        {"rect": [100, 200, 300, 220]},  # No URI
        {"uri": "https://example.com", "rect": [100, 250, 300, 270]},
    ]
    page.extract_text = Mock(return_value="")

    pdf = Mock()
    pdf.pages = [page]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)

    with patch("pdfplumber.open", return_value=pdf):
        links = extract_links("test.pdf")

        # Should only have 1 link (the one with URI)
        annotation_links = [link for link in links if "example.com" in link.url]
        assert len(annotation_links) == 1


def test_extract_links_uses_url_as_fallback_text():
    """Test that URL is used as text when text extraction fails."""
    page = Mock()
    page.annots = [
        {
            "uri": "https://example.com",
            "rect": [100, 200, 300, 220],
        },
    ]
    page.extract_text = Mock(return_value="")

    # Mock crop to return no text
    crop = Mock()
    crop.extract_text = Mock(return_value=None)
    page.crop = Mock(return_value=crop)

    pdf = Mock()
    pdf.pages = [page]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)

    with patch("pdfplumber.open", return_value=pdf):
        links = extract_links("test.pdf")

        assert len(links) >= 1
        # The link text should be the URL itself
        link = links[0]
        assert link.text == link.url
