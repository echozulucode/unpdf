"""Tests for image extraction."""

from unittest.mock import Mock, patch

import pytest

from unpdf.extractors.images import (
    ImageInfo,
    detect_image_caption,
    extract_images,
)


@pytest.fixture
def mock_image_data():
    """Mock image data for testing."""
    return {
        "x0": 100.0,
        "y0": 200.0,
        "x1": 300.0,
        "y1": 400.0,
        "width": 200,
        "height": 200,
    }


@pytest.fixture
def mock_page(mock_image_data):
    """Mock pdfplumber page with images."""
    page = Mock()
    page.images = [mock_image_data]
    page.crop = Mock(return_value=page)
    page.to_image = Mock()

    # Mock the image object
    img_obj = Mock()
    img_obj.original = Mock()
    img_obj.original.tobytes = Mock(return_value=b"fake_image_data")
    page.to_image.return_value = img_obj

    return page


@pytest.fixture
def mock_pdf(mock_page):
    """Mock pdfplumber PDF object."""
    pdf = Mock()
    pdf.pages = [mock_page]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)
    return pdf


def test_extract_images_basic(mock_pdf):
    """Test basic image extraction."""
    with patch("pdfplumber.open", return_value=mock_pdf):
        images = extract_images("test.pdf")

        assert len(images) == 1
        img = images[0]
        assert img.page_num == 1
        assert img.x0 == 100.0
        assert img.y0 == 200.0
        assert img.x1 == 300.0
        assert img.y1 == 400.0
        assert img.width == 200
        assert img.height == 200
        assert img.ext == "png"


def test_extract_images_generates_unique_ids(mock_pdf):
    """Test that image IDs are unique and consistent."""
    with patch("pdfplumber.open", return_value=mock_pdf):
        images = extract_images("test.pdf")

        assert len(images) == 1
        img = images[0]
        assert img.image_id.startswith("image_p1_")
        assert len(img.image_id) > 8  # Has hash component


def test_extract_images_filename_generation(mock_pdf):
    """Test that filenames are generated correctly."""
    with patch("pdfplumber.open", return_value=mock_pdf):
        images = extract_images("test.pdf")

        assert len(images) == 1
        img = images[0]
        assert img.filename.endswith(".png")
        assert img.filename.startswith("image_p1_")


def test_extract_images_no_output_dir(mock_pdf, tmp_path):
    """Test image extraction without saving to disk."""
    with patch("pdfplumber.open", return_value=mock_pdf):
        images = extract_images("test.pdf", output_dir=None)

        assert len(images) == 1
        # No files should be created
        assert len(list(tmp_path.iterdir())) == 0


def test_extract_images_with_output_dir(mock_pdf, tmp_path):
    """Test image extraction with saving to disk."""
    output_dir = str(tmp_path / "images")

    with patch("pdfplumber.open", return_value=mock_pdf):
        images = extract_images("test.pdf", output_dir=output_dir)

        assert len(images) == 1
        # Check that the image file was created
        img = images[0]
        image_file = tmp_path / "images" / img.filename
        assert image_file.exists()


def test_extract_images_multiple_pages():
    """Test image extraction from multiple pages."""
    page1 = Mock()
    page1.images = [
        {"x0": 100, "y0": 200, "x1": 300, "y1": 400, "width": 200, "height": 200}
    ]
    page1.crop = Mock(return_value=page1)
    img_obj1 = Mock()
    img_obj1.original.tobytes = Mock(return_value=b"fake_data_1")
    page1.to_image = Mock(return_value=img_obj1)

    page2 = Mock()
    page2.images = [
        {"x0": 50, "y0": 100, "x1": 150, "y1": 200, "width": 100, "height": 100}
    ]
    page2.crop = Mock(return_value=page2)
    img_obj2 = Mock()
    img_obj2.original.tobytes = Mock(return_value=b"fake_data_2")
    page2.to_image = Mock(return_value=img_obj2)

    pdf = Mock()
    pdf.pages = [page1, page2]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)

    with patch("pdfplumber.open", return_value=pdf):
        images = extract_images("test.pdf")

        assert len(images) == 2
        assert images[0].page_num == 1
        assert images[1].page_num == 2


def test_extract_images_handles_extraction_failure():
    """Test that image extraction handles failures gracefully."""
    page = Mock()
    page.images = [
        {"x0": 100, "y0": 200, "x1": 300, "y1": 400, "width": 200, "height": 200}
    ]
    page.crop = Mock(side_effect=Exception("Extraction failed"))

    pdf = Mock()
    pdf.pages = [page]
    pdf.__enter__ = Mock(return_value=pdf)
    pdf.__exit__ = Mock(return_value=False)

    with patch("pdfplumber.open", return_value=pdf):
        images = extract_images("test.pdf")

        # Should still create ImageInfo but with empty data
        assert len(images) == 1
        assert images[0].image_data == b""


def test_detect_image_caption():
    """Test caption detection for an image."""
    page = Mock()
    crop = Mock()
    crop.extract_text = Mock(return_value="Figure 1: A sample image")
    page.crop = Mock(return_value=crop)

    image_info = ImageInfo(
        image_id="test",
        page_num=1,
        x0=100,
        y0=200,
        x1=300,
        y1=400,
        width=200,
        height=200,
        image_data=b"",
    )

    caption = detect_image_caption(page, image_info)
    assert caption == "Figure 1: A sample image"


def test_detect_image_caption_no_text():
    """Test caption detection when no text is found."""
    page = Mock()
    crop = Mock()
    crop.extract_text = Mock(return_value=None)
    page.crop = Mock(return_value=crop)

    image_info = ImageInfo(
        image_id="test",
        page_num=1,
        x0=100,
        y0=200,
        x1=300,
        y1=400,
        width=200,
        height=200,
        image_data=b"",
    )

    caption = detect_image_caption(page, image_info)
    assert caption is None


def test_detect_image_caption_too_long():
    """Test that very long captions are rejected."""
    page = Mock()
    crop = Mock()
    crop.extract_text = Mock(return_value="A" * 300)  # Too long
    page.crop = Mock(return_value=crop)

    image_info = ImageInfo(
        image_id="test",
        page_num=1,
        x0=100,
        y0=200,
        x1=300,
        y1=400,
        width=200,
        height=200,
        image_data=b"",
    )

    caption = detect_image_caption(page, image_info)
    assert caption is None


def test_detect_image_caption_handles_exception():
    """Test that caption detection handles exceptions gracefully."""
    page = Mock()
    page.crop = Mock(side_effect=Exception("Crop failed"))

    image_info = ImageInfo(
        image_id="test",
        page_num=1,
        x0=100,
        y0=200,
        x1=300,
        y1=400,
        width=200,
        height=200,
        image_data=b"",
    )

    caption = detect_image_caption(page, image_info)
    assert caption is None


def test_image_info_creation():
    """Test ImageInfo object creation."""
    img = ImageInfo(
        image_id="test_123",
        page_num=2,
        x0=50.0,
        y0=100.0,
        x1=250.0,
        y1=300.0,
        width=200,
        height=200,
        image_data=b"test_data",
        ext="jpg",
    )

    assert img.image_id == "test_123"
    assert img.page_num == 2
    assert img.x0 == 50.0
    assert img.filename == "test_123.jpg"
    assert img.image_data == b"test_data"
