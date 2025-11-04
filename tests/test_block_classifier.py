"""Tests for block classification."""

import pytest

from unpdf.models.layout import Block, BlockType, BoundingBox, Style
from unpdf.processors.block_classifier import BlockClassifier, FontStatistics


@pytest.fixture
def classifier() -> BlockClassifier:
    """Create a BlockClassifier instance."""
    return BlockClassifier()


@pytest.fixture
def sample_blocks() -> list[Block]:
    """Create sample blocks with various font sizes."""
    bbox = BoundingBox(x=0, y=0, width=100, height=20)

    return [
        # Body text (12pt, most common)
        Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Normal paragraph text.",
            style=Style(font="Arial", size=12.0),
        ),
        Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Another paragraph.",
            style=Style(font="Arial", size=12.0),
        ),
        Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Yet another paragraph.",
            style=Style(font="Arial", size=12.0),
        ),
        # Large text (24pt - likely H1)
        Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Large Heading",
            style=Style(font="Arial", size=24.0, weight="bold"),
        ),
        # Medium text (18pt - likely H2)
        Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Medium Heading",
            style=Style(font="Arial", size=18.0, weight="bold"),
        ),
        # Code block (monospace)
        Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="def hello():\n    print('world')",
            style=Style(font="Courier", size=10.0, monospace=True),
        ),
    ]


class TestFontStatistics:
    """Tests for font statistics computation."""

    def test_compute_font_statistics_basic(
        self, classifier: BlockClassifier, sample_blocks: list[Block]
    ) -> None:
        """Test basic font statistics computation."""
        stats = classifier.compute_font_statistics(sample_blocks)

        assert stats.body_size == 12.0  # Most common size
        assert 12.0 in stats.size_counts
        assert stats.size_counts[12.0] == 3  # Three 12pt blocks
        assert stats.monospace_ratio == pytest.approx(1 / 6)  # One monospace block

    def test_compute_font_statistics_empty(self, classifier: BlockClassifier) -> None:
        """Test font statistics with no blocks."""
        stats = classifier.compute_font_statistics([])

        assert stats.body_size == 12.0  # Default
        assert stats.size_counts == {}
        assert stats.monospace_ratio == 0.0

    def test_compute_font_statistics_no_style(
        self, classifier: BlockClassifier
    ) -> None:
        """Test font statistics when blocks have no style."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        blocks = [
            Block(block_type=BlockType.TEXT, bbox=bbox, content="No style"),
        ]

        stats = classifier.compute_font_statistics(blocks)

        assert stats.body_size == 12.0  # Default
        assert stats.size_counts == {}


class TestHeadingDetection:
    """Tests for heading classification."""

    def test_classify_h1(self, classifier: BlockClassifier) -> None:
        """Test H1 detection (2.0-2.5× body)."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Main Heading",
            style=Style(font="Arial", size=24.0, weight="bold"),
        )
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block_type = classifier.classify_block(block, font_stats)

        assert block_type == BlockType.HEADING
        assert block.metadata is not None
        assert block.metadata["heading_level"] == 1

    def test_classify_h2(self, classifier: BlockClassifier) -> None:
        """Test H2 detection (1.5-1.8× body)."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Section Heading",
            style=Style(font="Arial", size=18.0),
        )
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block_type = classifier.classify_block(block, font_stats)

        assert block_type == BlockType.HEADING
        assert block.metadata is not None
        assert block.metadata["heading_level"] == 2

    def test_classify_h3(self, classifier: BlockClassifier) -> None:
        """Test H3 detection (1.2-1.4× body)."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Subsection",
            style=Style(font="Arial", size=15.0),
        )
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block_type = classifier.classify_block(block, font_stats)

        assert block_type == BlockType.HEADING
        assert block.metadata is not None
        assert block.metadata["heading_level"] == 3

    def test_classify_h5_requires_bold(self, classifier: BlockClassifier) -> None:
        """Test H5 requires bold weight."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)

        # Without bold - should be TEXT
        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Small heading",
            style=Style(font="Arial", size=13.0, weight="normal"),
        )
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.TEXT

        # With bold - should be HEADING
        block.style = Style(font="Arial", size=13.0, weight="bold")
        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.HEADING
        assert block.metadata is not None
        assert block.metadata["heading_level"] == 5


class TestListDetection:
    """Tests for list item classification."""

    def test_classify_bullet_list(self, classifier: BlockClassifier) -> None:
        """Test bullet list detection."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        # Test various bullet characters
        bullets = ["•", "◦", "▪", "‣", "⁃"]
        for bullet in bullets:
            block = Block(
                block_type=BlockType.TEXT,
                bbox=bbox,
                content=f"{bullet} List item",
                style=Style(font="Arial", size=12.0),
            )

            block_type = classifier.classify_block(block, font_stats)
            assert block_type == BlockType.LIST, f"Failed for bullet: {bullet}"

    def test_classify_numbered_list(self, classifier: BlockClassifier) -> None:
        """Test numbered list detection."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="1. First item",
            style=Style(font="Arial", size=12.0),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.LIST

    def test_classify_lettered_list(self, classifier: BlockClassifier) -> None:
        """Test lettered list detection."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="a. First item",
            style=Style(font="Arial", size=12.0),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.LIST

    def test_classify_markdown_bullet(self, classifier: BlockClassifier) -> None:
        """Test markdown-style bullet detection."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        for marker in ["-", "*", "+"]:
            block = Block(
                block_type=BlockType.TEXT,
                bbox=bbox,
                content=f"{marker} List item",
                style=Style(font="Arial", size=12.0),
            )

            block_type = classifier.classify_block(block, font_stats)
            assert block_type == BlockType.LIST, f"Failed for marker: {marker}"

    def test_classify_checkbox_list(self, classifier: BlockClassifier) -> None:
        """Test checkbox list detection."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        for marker in ["☐", "☑", "✓", "✗"]:
            block = Block(
                block_type=BlockType.TEXT,
                bbox=bbox,
                content=f"{marker} Task item",
                style=Style(font="Arial", size=12.0),
            )

            block_type = classifier.classify_block(block, font_stats)
            assert block_type == BlockType.LIST, f"Failed for checkbox: {marker}"


class TestCodeDetection:
    """Tests for code block classification."""

    def test_classify_monospace_code(self, classifier: BlockClassifier) -> None:
        """Test code detection with monospace font."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="def hello():\n    return 'world'",
            style=Style(font="Courier", size=10.0, monospace=True),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.CODE

    def test_classify_indented_code(self, classifier: BlockClassifier) -> None:
        """Test code detection with indentation."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="    def hello():\n        return 'world'",
            style=Style(font="Courier", size=10.0, monospace=True),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.CODE

    def test_classify_not_code_without_indicators(
        self, classifier: BlockClassifier
    ) -> None:
        """Test that monospace without code indicators is not classified as code."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Just some regular text in monospace",
            style=Style(font="Courier", size=10.0, monospace=True),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.TEXT


class TestHorizontalRule:
    """Tests for horizontal rule classification."""

    def test_classify_dash_hr(self, classifier: BlockClassifier) -> None:
        """Test dash horizontal rule."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        for hr in ["---", "----", "-----"]:
            block = Block(
                block_type=BlockType.TEXT,
                bbox=bbox,
                content=hr,
                style=Style(font="Arial", size=12.0),
            )

            block_type = classifier.classify_block(block, font_stats)
            assert block_type == BlockType.HORIZONTAL_RULE, f"Failed for: {hr}"

    def test_classify_other_hr_chars(self, classifier: BlockClassifier) -> None:
        """Test other horizontal rule characters."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        for hr in ["___", "***", "===", "~~~"]:
            block = Block(
                block_type=BlockType.TEXT,
                bbox=bbox,
                content=hr,
                style=Style(font="Arial", size=12.0),
            )

            block_type = classifier.classify_block(block, font_stats)
            assert block_type == BlockType.HORIZONTAL_RULE, f"Failed for: {hr}"


class TestBlockquote:
    """Tests for blockquote classification."""

    def test_classify_blockquote(self, classifier: BlockClassifier) -> None:
        """Test blockquote detection."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="> This is a quote\n> With multiple lines",
            style=Style(font="Arial", size=12.0),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.BLOCKQUOTE

    def test_classify_not_blockquote_minority(
        self, classifier: BlockClassifier
    ) -> None:
        """Test that minority of quote lines doesn't classify as blockquote."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="> One quote line\nBut mostly regular\ntext lines",
            style=Style(font="Arial", size=12.0),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.TEXT


class TestClassifyBlocks:
    """Tests for batch block classification."""

    def test_classify_blocks_all(
        self, classifier: BlockClassifier, sample_blocks: list[Block]
    ) -> None:
        """Test classifying multiple blocks."""
        classifier.classify_blocks(sample_blocks)

        # Check that blocks were classified
        assert sample_blocks[0].block_type == BlockType.TEXT  # Normal text
        assert sample_blocks[1].block_type == BlockType.TEXT
        assert sample_blocks[2].block_type == BlockType.TEXT
        assert sample_blocks[3].block_type == BlockType.HEADING  # Large (H1)
        assert sample_blocks[4].block_type == BlockType.HEADING  # Medium (H2)
        assert sample_blocks[5].block_type == BlockType.CODE  # Monospace with code

    def test_classify_blocks_empty(self, classifier: BlockClassifier) -> None:
        """Test classifying empty list."""
        blocks: list[Block] = []
        classifier.classify_blocks(blocks)
        assert len(blocks) == 0

    def test_classify_blocks_preserves_order(
        self, classifier: BlockClassifier, sample_blocks: list[Block]
    ) -> None:
        """Test that classification preserves block order."""
        original_order = [id(b) for b in sample_blocks]
        classifier.classify_blocks(sample_blocks)
        new_order = [id(b) for b in sample_blocks]

        assert original_order == new_order


class TestEdgeCases:
    """Tests for edge cases."""

    def test_classify_empty_content(self, classifier: BlockClassifier) -> None:
        """Test classification with empty content."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="",
            style=Style(font="Arial", size=12.0),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.TEXT

    def test_classify_none_content(self, classifier: BlockClassifier) -> None:
        """Test classification with None content."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content=None,
            style=Style(font="Arial", size=12.0),
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.TEXT

    def test_classify_no_style(self, classifier: BlockClassifier) -> None:
        """Test classification with no style info."""
        bbox = BoundingBox(x=0, y=0, width=100, height=20)
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.0
        )

        block = Block(
            block_type=BlockType.TEXT,
            bbox=bbox,
            content="Regular text",
            style=None,
        )

        block_type = classifier.classify_block(block, font_stats)
        assert block_type == BlockType.TEXT
