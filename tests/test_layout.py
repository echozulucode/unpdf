"""Tests for intermediate layout representation."""

from unpdf.models import Block, BlockType, BoundingBox, Document, Page, Style


def test_bounding_box_properties():
    """Test bounding box coordinate properties."""
    bbox = BoundingBox(x=10, y=20, width=100, height=50)
    assert bbox.x0 == 10
    assert bbox.y0 == 20
    assert bbox.x1 == 110
    assert bbox.y1 == 70
    assert bbox.center_x == 60
    assert bbox.center_y == 45


def test_bounding_box_overlaps():
    """Test bounding box overlap detection."""
    bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
    bbox2 = BoundingBox(x=50, y=50, width=100, height=100)
    bbox3 = BoundingBox(x=200, y=200, width=100, height=100)

    assert bbox1.overlaps(bbox2)
    assert bbox2.overlaps(bbox1)
    assert not bbox1.overlaps(bbox3)


def test_bounding_box_contains():
    """Test bounding box containment."""
    outer = BoundingBox(x=0, y=0, width=100, height=100)
    inner = BoundingBox(x=10, y=10, width=50, height=50)
    separate = BoundingBox(x=200, y=200, width=50, height=50)

    assert outer.contains(inner)
    assert not inner.contains(outer)
    assert not outer.contains(separate)


def test_document_to_dict():
    """Test document serialization to dictionary."""
    doc = Document()
    page = Page(number=1, width=612, height=792)

    bbox = BoundingBox(x=50, y=100, width=500, height=30)
    style = Style(font="Arial", size=24, weight="bold")
    block = Block(
        block_type=BlockType.HEADING,
        bbox=bbox,
        content="Test Heading",
        style=style,
        confidence=0.95,
    )

    page.blocks.append(block)
    doc.pages.append(page)

    data = doc.to_dict()
    assert len(data["pages"]) == 1
    assert data["pages"][0]["number"] == 1
    assert len(data["pages"][0]["blocks"]) == 1
    assert data["pages"][0]["blocks"][0]["type"] == "heading"
    assert data["pages"][0]["blocks"][0]["content"] == "Test Heading"


def test_document_json_roundtrip(tmp_path):
    """Test JSON serialization and deserialization."""
    doc = Document(metadata={"title": "Test Doc"})
    page = Page(number=1, width=612, height=792)

    bbox = BoundingBox(x=50, y=100, width=500, height=30)
    block = Block(block_type=BlockType.TEXT, bbox=bbox, content="Test content")

    page.blocks.append(block)
    doc.pages.append(page)

    # Serialize to JSON file
    json_path = tmp_path / "test.json"
    doc.to_json(path=json_path)

    assert json_path.exists()

    # Deserialize from JSON file
    loaded_doc = Document.from_json(path=json_path)

    assert loaded_doc.metadata["title"] == "Test Doc"
    assert len(loaded_doc.pages) == 1
    assert loaded_doc.pages[0].number == 1
    assert len(loaded_doc.pages[0].blocks) == 1
    assert loaded_doc.pages[0].blocks[0].content == "Test content"


def test_block_type_enum():
    """Test BlockType enum values."""
    assert BlockType.TEXT.value == "text"
    assert BlockType.HEADING.value == "heading"
    assert BlockType.TABLE.value == "table"
    assert BlockType.CODE.value == "code"
