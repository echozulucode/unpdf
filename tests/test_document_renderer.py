"""Tests for document_renderer module."""

import pytest

from unpdf.models.layout import Block, BlockType, BoundingBox, Style
from unpdf.processors.block_classifier import FontStatistics
from unpdf.processors.document_processor import (
    ProcessedDocument,
    ProcessedPage,
)
from unpdf.renderers.document_renderer import MarkdownRenderer


@pytest.fixture
def basic_renderer():
    """Create a basic renderer."""
    return MarkdownRenderer()


@pytest.fixture
def renderer_no_metadata():
    """Create renderer without metadata."""
    return MarkdownRenderer(include_metadata=False)


@pytest.fixture
def sample_style_bold():
    """Create a bold style."""
    return Style(weight="bold", style="normal", size=12.0)


@pytest.fixture
def sample_style_italic():
    """Create an italic style."""
    return Style(weight="normal", style="italic", size=12.0)


@pytest.fixture
def sample_style_plain():
    """Create a plain style."""
    return Style(weight="normal", style="normal", size=12.0)


def test_render_empty_document(basic_renderer):
    """Test rendering empty document."""
    doc = ProcessedDocument(
        pages=[],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)
    assert result == ""


def test_render_frontmatter(basic_renderer):
    """Test rendering document metadata as frontmatter."""
    metadata = {
        "title": "Test Document",
        "author": "John Doe",
        "date": "2025-11-04",
    }

    doc = ProcessedDocument(
        pages=[],
        metadata=metadata,
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "---" in result
    assert "title: Test Document" in result
    assert "author: John Doe" in result
    assert "date: 2025-11-04" in result


def test_render_frontmatter_with_special_chars(basic_renderer):
    """Test rendering frontmatter with special characters."""
    metadata = {
        "title": "Test: Document #1",
        "keywords": "test, [draft], {work}",
    }

    doc = ProcessedDocument(
        pages=[],
        metadata=metadata,
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    # Special chars should be quoted
    assert 'title: "Test: Document #1"' in result
    assert 'keywords: "test, [draft], {work}"' in result


def test_render_no_frontmatter(renderer_no_metadata):
    """Test rendering without frontmatter."""
    metadata = {"title": "Test Document"}

    doc = ProcessedDocument(
        pages=[],
        metadata=metadata,
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = renderer_no_metadata.render(doc)

    assert "---" not in result
    assert "title:" not in result


def test_render_heading_h1(basic_renderer, sample_style_bold):
    """Test rendering H1 heading."""
    block = Block(
        block_type=BlockType.HEADING,
        content="Main Title",
        bbox=BoundingBox(x=0, y=0, width=100, height=20),
        style=sample_style_bold,
        metadata={"level": 1},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "# **Main Title**" in result


def test_render_heading_h2(basic_renderer, sample_style_bold):
    """Test rendering H2 heading."""
    block = Block(
        block_type=BlockType.HEADING,
        content="Section Title",
        bbox=BoundingBox(x=0, y=0, width=100, height=20),
        style=sample_style_bold,
        metadata={"level": 2},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "## **Section Title**" in result


def test_render_paragraph(basic_renderer, sample_style_plain):
    """Test rendering plain paragraph."""
    block = Block(
        block_type=BlockType.TEXT,
        content="This is a plain paragraph.",
        bbox=BoundingBox(x=0, y=0, width=200, height=20),
        style=sample_style_plain,
        metadata={},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "This is a plain paragraph." in result


def test_render_paragraph_with_bold(basic_renderer, sample_style_bold):
    """Test rendering paragraph with bold text."""
    block = Block(
        block_type=BlockType.TEXT,
        content="Important text",
        bbox=BoundingBox(x=0, y=0, width=200, height=20),
        style=sample_style_bold,
        metadata={},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "**Important text**" in result


def test_render_paragraph_with_italic(basic_renderer, sample_style_italic):
    """Test rendering paragraph with italic text."""
    block = Block(
        block_type=BlockType.TEXT,
        content="Emphasized text",
        bbox=BoundingBox(x=0, y=0, width=200, height=20),
        style=sample_style_italic,
        metadata={},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "*Emphasized text*" in result


def test_render_bullet_list(basic_renderer, sample_style_plain):
    """Test rendering bullet list."""
    blocks = [
        Block(
            block_type=BlockType.LIST,
            content="First item",
            bbox=BoundingBox(x=0, y=0, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "bullet", "indent_level": 0},
        ),
        Block(
            block_type=BlockType.LIST,
            content="Second item",
            bbox=BoundingBox(x=0, y=20, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "bullet", "indent_level": 0},
        ),
    ]

    page = ProcessedPage(
        page_number=1, blocks=blocks, tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "- First item" in result
    assert "- Second item" in result


def test_render_ordered_list(basic_renderer, sample_style_plain):
    """Test rendering ordered list."""
    blocks = [
        Block(
            block_type=BlockType.LIST,
            content="First step",
            bbox=BoundingBox(x=0, y=0, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "ordered", "indent_level": 0, "number": 1},
        ),
        Block(
            block_type=BlockType.LIST,
            content="Second step",
            bbox=BoundingBox(x=0, y=20, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "ordered", "indent_level": 0, "number": 2},
        ),
    ]

    page = ProcessedPage(
        page_number=1, blocks=blocks, tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "1. First step" in result
    assert "2. Second step" in result


def test_render_nested_list(basic_renderer, sample_style_plain):
    """Test rendering nested list."""
    blocks = [
        Block(
            block_type=BlockType.LIST,
            content="Top level",
            bbox=BoundingBox(x=0, y=0, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "bullet", "indent_level": 0},
        ),
        Block(
            block_type=BlockType.LIST,
            content="Nested item",
            bbox=BoundingBox(x=20, y=20, width=180, height=20),
            style=sample_style_plain,
            metadata={"list_type": "bullet", "indent_level": 1},
        ),
    ]

    page = ProcessedPage(
        page_number=1, blocks=blocks, tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "- Top level" in result
    assert "  - Nested item" in result


def test_render_checkbox_list(basic_renderer, sample_style_plain):
    """Test rendering checkbox list."""
    blocks = [
        Block(
            block_type=BlockType.LIST,
            content="Completed task",
            bbox=BoundingBox(x=0, y=0, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "checkbox", "indent_level": 0, "checked": True},
        ),
        Block(
            block_type=BlockType.LIST,
            content="Incomplete task",
            bbox=BoundingBox(x=0, y=20, width=200, height=20),
            style=sample_style_plain,
            metadata={"list_type": "checkbox", "indent_level": 0, "checked": False},
        ),
    ]

    page = ProcessedPage(
        page_number=1, blocks=blocks, tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "- [x] Completed task" in result
    assert "- [ ] Incomplete task" in result


def test_render_code_block(basic_renderer):
    """Test rendering code block."""
    block = Block(
        block_type=BlockType.CODE,
        content='def hello():\n    print("Hello, World!")',
        bbox=BoundingBox(x=0, y=0, width=200, height=40),
        style=Style(weight="normal", style="normal", monospace=True, size=10.0),
        metadata={"language": "python"},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "```python" in result
    assert "def hello():" in result
    assert '    print("Hello, World!")' in result
    assert "```" in result


def test_render_blockquote(basic_renderer, sample_style_plain):
    """Test rendering blockquote."""
    block = Block(
        block_type=BlockType.BLOCKQUOTE,
        content="This is a quoted text.",
        bbox=BoundingBox(x=20, y=0, width=180, height=20),
        style=sample_style_plain,
        metadata={},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "> This is a quoted text." in result


def test_render_horizontal_rule(basic_renderer, sample_style_plain):
    """Test rendering horizontal rule."""
    block = Block(
        block_type=BlockType.HORIZONTAL_RULE,
        content="",
        bbox=BoundingBox(x=0, y=100, width=500, height=1),
        style=sample_style_plain,
        metadata={},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "---" in result


def test_render_link(basic_renderer, sample_style_plain):
    """Test rendering link."""
    block = Block(
        block_type=BlockType.TEXT,
        content="Click here",
        bbox=BoundingBox(x=0, y=0, width=100, height=20),
        style=sample_style_plain,
        metadata={"url": "https://example.com"},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "[Click here](https://example.com)" in result


def test_render_complex_document(basic_renderer):
    """Test rendering a document with multiple block types."""
    blocks = [
        Block(
            block_type=BlockType.HEADING,
            content="Document Title",
            bbox=BoundingBox(x=0, y=0, width=200, height=30),
            style=Style(weight="bold", style="normal", monospace=False, size=18.0),
            metadata={"level": 1},
        ),
        Block(
            block_type=BlockType.TEXT,
            content="Introduction paragraph.",
            bbox=BoundingBox(x=0, y=50, width=200, height=20),
            style=Style(weight="normal", style="normal", monospace=False, size=12.0),
            metadata={},
        ),
        Block(
            block_type=BlockType.HEADING,
            content="Features",
            bbox=BoundingBox(x=0, y=100, width=200, height=20),
            style=Style(weight="bold", style="normal", monospace=False, size=14.0),
            metadata={"level": 2},
        ),
        Block(
            block_type=BlockType.LIST,
            content="Feature one",
            bbox=BoundingBox(x=0, y=140, width=200, height=20),
            style=Style(weight="normal", style="normal", monospace=False, size=12.0),
            metadata={"list_type": "bullet", "indent_level": 0},
        ),
        Block(
            block_type=BlockType.LIST,
            content="Feature two",
            bbox=BoundingBox(x=0, y=170, width=200, height=20),
            style=Style(weight="normal", style="normal", monospace=False, size=12.0),
            metadata={"list_type": "bullet", "indent_level": 0},
        ),
    ]

    page = ProcessedPage(
        page_number=1, blocks=blocks, tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={"title": "Test Doc"},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    assert "title: Test Doc" in result
    assert "# **Document Title**" in result
    assert "Introduction paragraph." in result
    assert "## **Features**" in result
    assert "- Feature one" in result
    assert "- Feature two" in result


def test_heading_level_clamping(basic_renderer):
    """Test that heading levels are clamped to 1-6."""
    # Test level 0 (should become 1)
    block_0 = Block(
        block_type=BlockType.HEADING,
        content="Level 0",
        bbox=BoundingBox(x=0, y=0, width=100, height=20),
        style=Style(weight="bold", style="normal", monospace=False, size=18.0),
        metadata={"level": 0},
    )

    # Test level 10 (should become 6)
    block_10 = Block(
        block_type=BlockType.HEADING,
        content="Level 10",
        bbox=BoundingBox(x=0, y=30, width=100, height=20),
        style=Style(weight="bold", style="normal", monospace=False, size=18.0),
        metadata={"level": 10},
    )

    page = ProcessedPage(
        page_number=1, blocks=[block_0, block_10], tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    # Level 0 becomes level 1 (single #)
    assert result.count("# **Level 0**") == 1
    # Level 10 becomes level 6 (six #s)
    assert result.count("###### **Level 10**") == 1


def test_no_excessive_blank_lines(basic_renderer, sample_style_plain):
    """Test that excessive blank lines are removed."""
    blocks = [
        Block(
            block_type=BlockType.TEXT,
            content="Paragraph 1",
            bbox=BoundingBox(x=0, y=0, width=200, height=20),
            style=sample_style_plain,
            metadata={},
        ),
        Block(
            block_type=BlockType.TEXT,
            content="Paragraph 2",
            bbox=BoundingBox(x=0, y=50, width=200, height=20),
            style=sample_style_plain,
            metadata={},
        ),
    ]

    page = ProcessedPage(
        page_number=1, blocks=blocks, tables=[], images=[], layout_info={}
    )

    doc = ProcessedDocument(
        pages=[page],
        metadata={},
        font_stats=FontStatistics(
            body_size=12.0, size_counts={12.0: 100}, monospace_ratio=0.0
        ),
    )

    result = basic_renderer.render(doc)

    # Should not have triple newlines
    assert "\n\n\n" not in result
