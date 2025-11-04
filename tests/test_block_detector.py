"""Tests for unified block detection and classification."""

import pytest
from dataclasses import dataclass
from unpdf.processors.block_detector import (
    BlockDetector,
    BlockCategory,
    DetectedBlock,
)
from unpdf.processors.block_classifier import BlockType
from unpdf.processors.header_classifier import HeaderLevel


@dataclass
class MockBBox:
    """Mock bounding box for testing."""

    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class MockTextBlock:
    """Mock text block for testing."""

    text: str
    bbox: MockBBox
    font_size: float = 12.0
    is_bold: bool = False
    is_italic: bool = False


class TestBlockDetector:
    """Test suite for BlockDetector."""

    def test_initialization(self):
        """Test detector initialization with default settings."""
        detector = BlockDetector()
        assert detector.base_classifier is not None
        assert detector.list_detector is not None
        assert detector.code_detector is not None
        assert detector.header_classifier is not None
        assert detector.caption_detector is not None
        assert detector.footnote_detector is not None

    def test_initialization_disabled_features(self):
        """Test detector initialization with features disabled."""
        detector = BlockDetector(
            use_lists=False,
            use_code=False,
            use_headers=False,
            use_captions=False,
            use_footnotes=False,
        )
        assert detector.base_classifier is not None
        assert detector.list_detector is None
        assert detector.code_detector is None
        assert detector.header_classifier is None
        assert detector.caption_detector is None
        assert detector.footnote_detector is None

    def test_detect_blocks_empty(self):
        """Test detection with no text blocks."""
        detector = BlockDetector()
        blocks = detector.detect_blocks([], body_font_size=12.0, page_num=0)
        assert blocks == []

    def test_detect_blocks_single_paragraph(self):
        """Test detection of a single paragraph."""
        detector = BlockDetector()
        text_blocks = [
            MockTextBlock(
                text="This is a regular paragraph.",
                bbox=MockBBox(100, 100, 500, 120),
                font_size=12.0,
            )
        ]

        blocks = detector.detect_blocks(text_blocks, body_font_size=12.0, page_num=0)
        assert len(blocks) == 1
        assert blocks[0].category in (BlockCategory.PARAGRAPH, BlockCategory.UNKNOWN)
        assert blocks[0].text == "This is a regular paragraph."
        assert blocks[0].page_num == 0

    def test_detect_blocks_header(self):
        """Test detection of a header."""
        detector = BlockDetector()
        text_blocks = [
            MockTextBlock(
                text="Chapter 1: Introduction",
                bbox=MockBBox(100, 50, 500, 80),
                font_size=24.0,
                is_bold=True,
            )
        ]

        blocks = detector.detect_blocks(text_blocks, body_font_size=12.0, page_num=0)
        assert len(blocks) == 1
        # Should be classified as header due to large font size
        assert blocks[0].category == BlockCategory.HEADER

    def test_detect_blocks_multiple_types(self):
        """Test detection of multiple block types."""
        detector = BlockDetector()
        text_blocks = [
            MockTextBlock(
                text="Main Title",
                bbox=MockBBox(100, 50, 500, 80),
                font_size=24.0,
            ),
            MockTextBlock(
                text="This is a paragraph.",
                bbox=MockBBox(100, 100, 500, 120),
                font_size=12.0,
            ),
            MockTextBlock(
                text="• First item",
                bbox=MockBBox(100, 140, 500, 160),
                font_size=12.0,
            ),
        ]

        blocks = detector.detect_blocks(text_blocks, body_font_size=12.0, page_num=0)
        assert len(blocks) == 3

    def test_map_block_type_to_category(self):
        """Test mapping from BlockType to BlockCategory."""
        detector = BlockDetector()

        mapping = {
            BlockType.HEADER: BlockCategory.HEADER,
            BlockType.BODY_TEXT: BlockCategory.PARAGRAPH,
            BlockType.LIST_ITEM: BlockCategory.LIST,
            BlockType.CODE: BlockCategory.CODE,
            BlockType.TABLE: BlockCategory.TABLE,
            BlockType.CAPTION: BlockCategory.CAPTION,
            BlockType.FOOTNOTE: BlockCategory.FOOTNOTE,
            BlockType.HORIZONTAL_RULE: BlockCategory.HORIZONTAL_RULE,
            BlockType.BLOCKQUOTE: BlockCategory.BLOCKQUOTE,
        }

        for block_type, expected_category in mapping.items():
            category = detector._map_block_type_to_category(block_type)
            assert category == expected_category

    def test_classify_headers(self):
        """Test header classification refinement."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.HEADER,
                bbox=MockBBox(100, 50, 500, 80),
                text="Main Title",
                confidence=0.5,
                page_num=0,
                metadata={"font_size": 24.0, "is_bold": True},
            )
        ]

        refined_blocks = detector._classify_headers(blocks, body_font_size=12.0)
        assert len(refined_blocks) == 1
        assert refined_blocks[0].header_level is not None
        assert refined_blocks[0].confidence > 0.5

    def test_detect_lists_bullet(self):
        """Test bullet list detection."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 100, 500, 120),
                text="• First item",
                confidence=0.5,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 130, 500, 150),
                text="• Second item",
                confidence=0.5,
                page_num=0,
            ),
        ]

        refined_blocks = detector._detect_lists(blocks)
        # Note: List detection depends on the list_detector implementation
        # This test verifies the method runs without errors
        assert len(refined_blocks) == 2

    def test_detect_code_blocks(self):
        """Test code block detection."""
        detector = BlockDetector()
        code_text = "def hello():\n    print('world')"
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 100, 500, 140),
                text=code_text,
                confidence=0.5,
                page_num=0,
            )
        ]

        refined_blocks = detector._detect_code_blocks(blocks)
        assert len(refined_blocks) == 1
        # Code detection depends on code_detector heuristics
        # This test verifies the method runs without errors

    def test_detect_captions_with_images(self):
        """Test caption detection with images."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 400, 500, 420),
                text="Figure 1: A diagram",
                confidence=0.5,
                page_num=0,
            )
        ]

        # Mock image
        @dataclass
        class MockImage:
            bbox: MockBBox

        images = [MockImage(bbox=MockBBox(100, 200, 500, 380))]

        refined_blocks = detector._detect_captions(blocks, images, [])
        assert len(refined_blocks) == 1
        # Caption detection depends on proximity and keywords
        # This test verifies the method runs without errors

    def test_detect_footnotes(self):
        """Test footnote detection."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 700, 500, 720),
                text="1. This is a footnote.",
                confidence=0.5,
                page_num=0,
                metadata={"font_size": 9.0},
            )
        ]

        refined_blocks = detector._detect_footnotes(blocks)
        assert len(refined_blocks) == 1
        # Footnote detection depends on position and markers
        # This test verifies the method runs without errors

    def test_get_reading_order(self):
        """Test reading order sorting."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 200, 500, 220),
                text="Second",
                confidence=0.8,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 100, 500, 120),
                text="First",
                confidence=0.8,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 300, 500, 320),
                text="Third",
                confidence=0.8,
                page_num=0,
            ),
        ]

        ordered = detector.get_reading_order(blocks)
        assert len(ordered) == 3
        assert ordered[0].text == "First"
        assert ordered[1].text == "Second"
        assert ordered[2].text == "Third"

    def test_get_reading_order_left_to_right(self):
        """Test reading order with horizontal layout."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(300, 100, 500, 120),
                text="Right",
                confidence=0.8,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 100, 250, 120),
                text="Left",
                confidence=0.8,
                page_num=0,
            ),
        ]

        ordered = detector.get_reading_order(blocks)
        assert len(ordered) == 2
        assert ordered[0].text == "Left"
        assert ordered[1].text == "Right"

    def test_filter_by_confidence(self):
        """Test confidence filtering."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 100, 500, 120),
                text="High confidence",
                confidence=0.9,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 130, 500, 150),
                text="Medium confidence",
                confidence=0.65,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 160, 500, 180),
                text="Low confidence",
                confidence=0.3,
                page_num=0,
            ),
        ]

        # Filter with default threshold (0.6)
        filtered = detector.filter_by_confidence(blocks)
        assert len(filtered) == 2
        assert filtered[0].text == "High confidence"
        assert filtered[1].text == "Medium confidence"

        # Filter with higher threshold
        filtered_high = detector.filter_by_confidence(blocks, min_confidence=0.8)
        assert len(filtered_high) == 1
        assert filtered_high[0].text == "High confidence"

    def test_group_blocks_by_category(self):
        """Test grouping blocks by category."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.HEADER,
                bbox=MockBBox(100, 50, 500, 80),
                text="Title",
                confidence=0.9,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 100, 500, 120),
                text="Paragraph 1",
                confidence=0.8,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.PARAGRAPH,
                bbox=MockBBox(100, 130, 500, 150),
                text="Paragraph 2",
                confidence=0.8,
                page_num=0,
            ),
            DetectedBlock(
                category=BlockCategory.LIST,
                bbox=MockBBox(100, 160, 500, 180),
                text="• List item",
                confidence=0.85,
                page_num=0,
            ),
        ]

        groups = detector.group_blocks_by_category(blocks)
        assert len(groups) == 3
        assert BlockCategory.HEADER in groups
        assert BlockCategory.PARAGRAPH in groups
        assert BlockCategory.LIST in groups
        assert len(groups[BlockCategory.HEADER]) == 1
        assert len(groups[BlockCategory.PARAGRAPH]) == 2
        assert len(groups[BlockCategory.LIST]) == 1

    def test_detect_blocks_with_metadata(self):
        """Test that metadata is preserved during detection."""
        detector = BlockDetector()

        @dataclass
        class TextBlockWithMetadata:
            text: str
            bbox: MockBBox
            font_size: float
            is_bold: bool

        text_blocks = [
            TextBlockWithMetadata(
                text="Bold text",
                bbox=MockBBox(100, 100, 500, 120),
                font_size=12.0,
                is_bold=True,
            )
        ]

        blocks = detector.detect_blocks(text_blocks, body_font_size=12.0, page_num=0)
        assert len(blocks) == 1
        # Metadata handling depends on implementation
        # This test verifies the method handles objects with metadata

    def test_detect_blocks_with_tables(self):
        """Test detection with tables present."""
        detector = BlockDetector()

        @dataclass
        class MockTable:
            bbox: MockBBox

        text_blocks = [
            MockTextBlock(
                text="Table 1: Results",
                bbox=MockBBox(100, 100, 500, 120),
                font_size=12.0,
            )
        ]
        tables = [MockTable(bbox=MockBBox(100, 140, 500, 300))]

        blocks = detector.detect_blocks(
            text_blocks, body_font_size=12.0, page_num=0, tables=tables
        )
        assert len(blocks) == 1
        # Caption detection should attempt to link with table
        # This test verifies the method handles tables parameter

    def test_confidence_increases_with_classification(self):
        """Test that confidence scores increase with successful classification."""
        detector = BlockDetector()
        blocks = [
            DetectedBlock(
                category=BlockCategory.HEADER,
                bbox=MockBBox(100, 50, 500, 80),
                text="Main Title",
                confidence=0.5,
                page_num=0,
                metadata={"font_size": 24.0, "is_bold": True},
            )
        ]

        initial_confidence = blocks[0].confidence
        refined_blocks = detector._classify_headers(blocks, body_font_size=12.0)
        assert refined_blocks[0].confidence >= initial_confidence

    def test_block_detector_full_pipeline(self):
        """Test complete detection pipeline."""
        detector = BlockDetector()
        text_blocks = [
            MockTextBlock(
                text="Document Title",
                bbox=MockBBox(100, 50, 500, 80),
                font_size=24.0,
                is_bold=True,
            ),
            MockTextBlock(
                text="This is the introduction paragraph.",
                bbox=MockBBox(100, 100, 500, 120),
                font_size=12.0,
            ),
            MockTextBlock(
                text="• First bullet point",
                bbox=MockBBox(100, 140, 500, 160),
                font_size=12.0,
            ),
            MockTextBlock(
                text="• Second bullet point",
                bbox=MockBBox(100, 170, 500, 190),
                font_size=12.0,
            ),
        ]

        blocks = detector.detect_blocks(text_blocks, body_font_size=12.0, page_num=0)
        assert len(blocks) == 4

        # Get reading order
        ordered = detector.get_reading_order(blocks)
        assert len(ordered) == 4

        # Group by category
        groups = detector.group_blocks_by_category(ordered)
        assert len(groups) >= 1

        # Filter by confidence
        filtered = detector.filter_by_confidence(ordered, min_confidence=0.4)
        assert len(filtered) <= 4
