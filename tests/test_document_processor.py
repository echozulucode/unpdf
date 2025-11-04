"""Tests for the integrated document processor."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from unpdf.models.layout import Block, BlockType, BoundingBox, Style
from unpdf.processors.block_classifier import FontStatistics
from unpdf.processors.document_processor import (
    DocumentProcessor,
    ProcessedDocument,
    ProcessedPage,
)
from unpdf.processors.layout_analyzer import TextBlock


class TestDocumentProcessor:
    """Tests for DocumentProcessor."""

    def test_initialization_all_features(self):
        """Test processor initialization with all features enabled."""
        processor = DocumentProcessor(
            detect_columns=True,
            detect_tables=True,
            detect_lists=True,
            detect_code=True,
            detect_checkboxes=True,
        )

        assert processor.detect_columns
        assert processor.detect_tables
        assert processor.detect_lists
        assert processor.detect_code
        assert processor.detect_checkboxes
        assert processor.layout_analyzer is not None
        assert processor.block_classifier is not None
        assert processor.table_detector is not None

    def test_initialization_minimal_features(self):
        """Test processor initialization with minimal features."""
        processor = DocumentProcessor(
            detect_columns=False,
            detect_tables=False,
            detect_lists=False,
            detect_code=False,
            detect_checkboxes=False,
        )

        assert not processor.detect_columns
        assert not processor.detect_tables
        assert not processor.detect_lists

    def test_blocks_to_text_blocks(self):
        """Test conversion of raw blocks to TextBlock objects."""
        processor = DocumentProcessor()

        raw_blocks = [
            {
                "text": "Hello World",
                "bbox": (10, 20, 100, 30),
                "font": "Arial",
                "size": 12.0,
                "flags": 0,
                "color": 0,
            },
            {
                "text": "Second line",
                "bbox": (10, 35, 100, 45),
                "font": "Arial",
                "size": 12.0,
                "flags": 0,
                "color": 0,
            },
        ]

        text_blocks = processor._blocks_to_text_blocks(raw_blocks)

        assert len(text_blocks) == 2
        assert text_blocks[0].text == "Hello World"
        assert text_blocks[0].bbox.x0 == 10
        assert text_blocks[0].bbox.y0 == 20
        assert text_blocks[1].text == "Second line"

    def test_compute_font_statistics_single_size(self):
        """Test font statistics computation with single font size."""
        processor = DocumentProcessor()

        blocks = [
            {"text": "Text 1", "size": 12.0, "font": "Arial"},
            {"text": "Text 2", "size": 12.0, "font": "Arial"},
            {"text": "Text 3", "size": 12.0, "font": "Arial"},
        ]

        stats = processor._compute_font_statistics(blocks)

        assert stats.body_size == 12.0
        assert stats.size_counts[12.0] == 3
        assert stats.monospace_ratio == 0.0

    def test_compute_font_statistics_mixed_sizes(self):
        """Test font statistics with mixed font sizes."""
        processor = DocumentProcessor()

        blocks = [
            {"text": "Header", "size": 18.0, "font": "Arial-Bold"},
            {"text": "Body 1", "size": 12.0, "font": "Arial"},
            {"text": "Body 2", "size": 12.0, "font": "Arial"},
            {"text": "Body 3", "size": 12.0, "font": "Arial"},
            {"text": "Small", "size": 10.0, "font": "Arial"},
        ]

        stats = processor._compute_font_statistics(blocks)

        # Body size should be 12.0 (most common)
        assert stats.body_size == 12.0
        assert stats.size_counts[12.0] == 3
        assert stats.size_counts[18.0] == 1
        assert stats.size_counts[10.0] == 1

    def test_compute_font_statistics_monospace(self):
        """Test monospace detection in font statistics."""
        processor = DocumentProcessor()

        blocks = [
            {"text": "Normal", "size": 12.0, "font": "Arial"},
            {"text": "Code", "size": 10.0, "font": "Courier"},
            {"text": "Code", "size": 10.0, "font": "Consolas"},
        ]

        stats = processor._compute_font_statistics(blocks)

        # 2 out of 3 blocks are monospace
        assert abs(stats.monospace_ratio - 2 / 3) < 0.01

    def test_compute_font_statistics_empty(self):
        """Test font statistics with no blocks."""
        processor = DocumentProcessor()

        stats = processor._compute_font_statistics([])

        assert stats.body_size == 12.0  # Default
        assert stats.size_counts == {}
        assert stats.monospace_ratio == 0.0

    @patch("unpdf.processors.document_processor.pymupdf")
    def test_extract_metadata(self, mock_pymupdf):
        """Test metadata extraction."""
        mock_doc = Mock()
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
        }
        mock_doc.__len__ = Mock(return_value=5)
        mock_pymupdf.open.return_value = mock_doc

        processor = DocumentProcessor()
        metadata = processor._extract_metadata("test.pdf")

        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "Test Author"
        assert metadata["page_count"] == 5
        mock_doc.close.assert_called_once()

    def test_extract_images_from_page(self):
        """Test image extraction from a page."""
        processor = DocumentProcessor()

        mock_page = Mock()
        mock_page.get_images.return_value = [(100, 0, 0, 0), (101, 0, 0, 0)]
        mock_page.get_image_bbox.side_effect = [
            (10, 20, 100, 150),
            (120, 20, 200, 150),
        ]

        images = processor._extract_images(mock_page)

        assert len(images) == 2
        assert images[0]["xref"] == 100
        assert images[0]["bbox"] == (10, 20, 100, 150)
        assert images[1]["xref"] == 101

    def test_classify_blocks_basic(self):
        """Test basic block classification."""
        from unpdf.processors.layout_analyzer import (
            BoundingBox as LayoutBoundingBox,
        )

        processor = DocumentProcessor()

        text_blocks = [
            TextBlock(
                bbox=LayoutBoundingBox(x0=10, y0=20, x1=100, y1=30),
                text="Paragraph 1",
            ),
            TextBlock(
                bbox=LayoutBoundingBox(x0=10, y0=35, x1=100, y1=45),
                text="Paragraph 2",
            ),
        ]

        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 2}, monospace_ratio=0.0
        )

        classified = processor._classify_blocks(text_blocks, font_stats)

        assert len(classified) == 2
        assert all(isinstance(b, Block) for b in classified)
        assert classified[0].content == "Paragraph 1"
        assert classified[1].content == "Paragraph 2"

    def test_apply_content_processors_with_lists(self):
        """Test content processor application."""
        processor = DocumentProcessor(
            detect_lists=True,
            detect_code=True,
            detect_checkboxes=True,
        )

        blocks = [
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=10, y=20, width=90, height=10),
                content="Normal text",
                style=Style(),
            )
        ]

        mock_page = Mock()
        processed = processor._apply_content_processors(blocks, mock_page)

        # Should return processed blocks (even if unchanged)
        assert len(processed) >= 1

    @patch("unpdf.processors.document_processor.pymupdf")
    def test_process_document_basic(self, mock_pymupdf):
        """Test basic document processing."""
        # Setup mock document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.metadata = {"title": "Test"}

        mock_page = Mock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Hello",
                                    "bbox": (10, 20, 50, 30),
                                    "font": "Arial",
                                    "size": 12.0,
                                    "flags": 0,
                                    "color": 0,
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        mock_page.get_images.return_value = []

        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_pymupdf.open.return_value = mock_doc

        processor = DocumentProcessor(
            detect_columns=False, detect_tables=False
        )
        result = processor.process_document("test.pdf")

        assert isinstance(result, ProcessedDocument)
        assert len(result.pages) == 1
        assert result.metadata["title"] == "Test"
        assert result.metadata["page_count"] == 1
        mock_doc.close.assert_called()

    def test_processed_document_structure(self):
        """Test ProcessedDocument data structure."""
        font_stats = FontStatistics(
            body_size=12.0, size_counts={12.0: 10}, monospace_ratio=0.1
        )

        page = ProcessedPage(
            page_number=1,
            blocks=[],
            tables=[],
            images=[],
            layout_info={},
        )

        doc = ProcessedDocument(
            pages=[page], metadata={"title": "Test"}, font_stats=font_stats
        )

        assert len(doc.pages) == 1
        assert doc.pages[0].page_number == 1
        assert doc.metadata["title"] == "Test"
        assert doc.font_stats.body_size == 12.0

    def test_processed_page_structure(self):
        """Test ProcessedPage data structure."""
        block = Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=0, y=0, width=100, height=20),
            content="Test content",
            style=Style(),
        )

        page = ProcessedPage(
            page_number=1,
            blocks=[block],
            tables=[],
            images=[],
            layout_info={"columns": []},
        )

        assert page.page_number == 1
        assert len(page.blocks) == 1
        assert page.blocks[0].content == "Test content"
        assert len(page.tables) == 0
        assert "columns" in page.layout_info

    @patch("unpdf.processors.document_processor.pymupdf")
    def test_extract_blocks_from_page_empty(self, mock_pymupdf):
        """Test block extraction from empty page."""
        processor = DocumentProcessor()

        mock_page = Mock()
        mock_page.get_text.return_value = {"blocks": []}

        blocks = processor._extract_blocks_from_page(mock_page)

        assert blocks == []

    @patch("unpdf.processors.document_processor.pymupdf")
    def test_extract_blocks_from_page_multiple_spans(self, mock_pymupdf):
        """Test block extraction with multiple spans."""
        processor = DocumentProcessor()

        mock_page = Mock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "First",
                                    "bbox": (10, 20, 50, 30),
                                    "font": "Arial",
                                    "size": 12.0,
                                    "flags": 0,
                                    "color": 0,
                                },
                                {
                                    "text": "Second",
                                    "bbox": (55, 20, 100, 30),
                                    "font": "Arial-Bold",
                                    "size": 12.0,
                                    "flags": 16,
                                    "color": 0,
                                },
                            ]
                        }
                    ],
                }
            ]
        }

        blocks = processor._extract_blocks_from_page(mock_page)

        assert len(blocks) == 2
        assert blocks[0]["text"] == "First"
        assert blocks[1]["text"] == "Second"
        assert blocks[1]["font"] == "Arial-Bold"

    def test_font_statistics_attributes(self):
        """Test FontStatistics dataclass."""
        stats = FontStatistics(
            body_size=12.0,
            size_counts={12.0: 10, 14.0: 2},
            monospace_ratio=0.15,
        )

        assert stats.body_size == 12.0
        assert stats.size_counts[12.0] == 10
        assert stats.size_counts[14.0] == 2
        assert abs(stats.monospace_ratio - 0.15) < 0.01
