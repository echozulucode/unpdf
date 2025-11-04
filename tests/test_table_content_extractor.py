"""Tests for table content extraction."""

import pytest

from unpdf.models.layout import BoundingBox
from unpdf.processors.table_content_extractor import (
    TableContentExtractor,
    TextBlock,
)
from unpdf.processors.table_detector import Table, TableCell, TableDetectionMethod


class TestTextBlock:
    """Test TextBlock data structure."""

    def test_create_text_block(self):
        """Test creating a text block."""
        bbox = BoundingBox(10, 20, 30, 10)
        block = TextBlock(bbox=bbox, content="Hello", font_size=12.0, is_bold=True)

        assert block.bbox == bbox
        assert block.content == "Hello"
        assert block.font_size == 12.0
        assert block.is_bold is True

    def test_text_block_defaults(self):
        """Test text block default values."""
        bbox = BoundingBox(0, 0, 10, 10)
        block = TextBlock(bbox=bbox, content="Test")

        assert block.font_size == 12.0
        assert block.is_bold is False


class TestFindCellText:
    """Test finding text blocks within cells."""

    def test_single_block_fully_contained(self):
        """Test single text block fully contained in cell."""
        extractor = TableContentExtractor()

        cell = TableCell(bbox=BoundingBox(0, 0, 100, 50), row=0, col=0)
        text_blocks = [
            TextBlock(bbox=BoundingBox(10, 10, 80, 30), content="Cell content")
        ]

        result = extractor._find_cell_text(cell, text_blocks)

        assert len(result) == 1
        assert result[0].content == "Cell content"

    def test_multiple_blocks_in_cell(self):
        """Test multiple text blocks in single cell."""
        extractor = TableContentExtractor()

        cell = TableCell(bbox=BoundingBox(0, 0, 100, 50), row=0, col=0)
        text_blocks = [
            TextBlock(bbox=BoundingBox(10, 10, 40, 15), content="Line 1"),
            TextBlock(bbox=BoundingBox(10, 25, 40, 15), content="Line 2"),
        ]

        result = extractor._find_cell_text(cell, text_blocks)

        assert len(result) == 2
        assert result[0].content == "Line 1"
        assert result[1].content == "Line 2"

    def test_partial_overlap_above_threshold(self):
        """Test text block with partial overlap above threshold."""
        extractor = TableContentExtractor(cell_overlap_threshold=0.5)

        cell = TableCell(bbox=BoundingBox(0, 0, 100, 50), row=0, col=0)
        # Block is 75% inside cell (60 out of 80 pixels)
        text_blocks = [TextBlock(bbox=BoundingBox(50, 10, 80, 30), content="Partial")]

        result = extractor._find_cell_text(cell, text_blocks)

        assert len(result) == 1

    def test_partial_overlap_below_threshold(self):
        """Test text block with overlap below threshold."""
        extractor = TableContentExtractor(cell_overlap_threshold=0.8)

        cell = TableCell(bbox=BoundingBox(0, 0, 100, 50), row=0, col=0)
        # Block is only 25% inside cell
        text_blocks = [
            TextBlock(bbox=BoundingBox(80, 10, 80, 30), content="Mostly outside")
        ]

        result = extractor._find_cell_text(cell, text_blocks)

        assert len(result) == 0

    def test_blocks_sorted_by_position(self):
        """Test blocks are sorted top-to-bottom, left-to-right."""
        extractor = TableContentExtractor()

        cell = TableCell(bbox=BoundingBox(0, 0, 100, 100), row=0, col=0)
        text_blocks = [
            TextBlock(bbox=BoundingBox(50, 50, 20, 10), content="Bottom Right"),
            TextBlock(bbox=BoundingBox(10, 10, 20, 10), content="Top Left"),
            TextBlock(bbox=BoundingBox(50, 10, 20, 10), content="Top Right"),
            TextBlock(bbox=BoundingBox(10, 50, 20, 10), content="Bottom Left"),
        ]

        result = extractor._find_cell_text(cell, text_blocks)

        assert len(result) == 4
        assert result[0].content == "Top Left"
        assert result[1].content == "Top Right"
        assert result[2].content == "Bottom Left"
        assert result[3].content == "Bottom Right"


class TestMergeTextBlocks:
    """Test merging text blocks into cell content."""

    def test_empty_blocks(self):
        """Test merging empty list."""
        extractor = TableContentExtractor()
        result = extractor._merge_text_blocks([])
        assert result == ""

    def test_single_block(self):
        """Test single text block."""
        extractor = TableContentExtractor()
        blocks = [TextBlock(bbox=BoundingBox(0, 0, 50, 10), content="  Hello  ")]

        result = extractor._merge_text_blocks(blocks)

        assert result == "Hello"

    def test_multiple_lines(self):
        """Test multiple text blocks on different lines."""
        extractor = TableContentExtractor()
        blocks = [
            TextBlock(bbox=BoundingBox(0, 0, 50, 10), content="Line 1"),
            TextBlock(
                bbox=BoundingBox(0, 15, 50, 10), content="Line 2"
            ),  # Y diff = 15
        ]

        result = extractor._merge_text_blocks(blocks)

        assert result == "Line 1\nLine 2"

    def test_same_line_merge(self):
        """Test blocks on same line are space-separated."""
        extractor = TableContentExtractor()
        blocks = [
            TextBlock(bbox=BoundingBox(0, 10, 30, 10), content="Hello"),
            TextBlock(
                bbox=BoundingBox(35, 10, 30, 10), content="World"
            ),  # Small Y diff
        ]

        result = extractor._merge_text_blocks(blocks)

        assert result == "Hello World"

    def test_merge_with_whitespace(self):
        """Test merging strips and normalizes whitespace."""
        extractor = TableContentExtractor()
        blocks = [
            TextBlock(bbox=BoundingBox(0, 0, 50, 10), content="  First  "),
            TextBlock(bbox=BoundingBox(0, 15, 50, 10), content="  Second  "),
        ]

        result = extractor._merge_text_blocks(blocks)

        assert result == "First\nSecond"


class TestMergeLine:
    """Test merging text blocks on same line."""

    def test_single_block(self):
        """Test single block on line."""
        extractor = TableContentExtractor()
        blocks = [TextBlock(bbox=BoundingBox(0, 0, 50, 10), content="  Test  ")]

        result = extractor._merge_line(blocks)

        assert result == "Test"

    def test_two_blocks_close_together(self):
        """Test blocks close together get single space."""
        extractor = TableContentExtractor(merge_spacing_threshold=2.0)
        blocks = [
            TextBlock(bbox=BoundingBox(0, 0, 30, 10), content="Hello"),
            TextBlock(bbox=BoundingBox(35, 0, 30, 10), content="World"),  # Gap = 5
        ]

        result = extractor._merge_line(blocks)

        assert result == "Hello World"

    def test_blocks_far_apart(self):
        """Test blocks far apart get more space."""
        extractor = TableContentExtractor(merge_spacing_threshold=2.0)
        blocks = [
            TextBlock(bbox=BoundingBox(0, 0, 30, 10), content="Left"),
            TextBlock(bbox=BoundingBox(100, 0, 30, 10), content="Right"),  # Gap = 70
        ]

        result = extractor._merge_line(blocks)

        # Should have space due to large gap
        assert "Left" in result
        assert "Right" in result
        assert " " in result


class TestDetectHeaderRows:
    """Test header row detection."""

    def test_first_row_bold(self):
        """Test first row with bold text is detected as header."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0, content="Header1"),
            TableCell(
                bbox=BoundingBox(50, 0, 50, 20), row=0, col=1, content="Header2"
            ),
            TableCell(bbox=BoundingBox(0, 20, 50, 20), row=1, col=0, content="Data1"),
            TableCell(bbox=BoundingBox(50, 20, 50, 20), row=1, col=1, content="Data2"),
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 40),
            cells=cells,
            num_rows=2,
            num_cols=2,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        text_blocks = [
            TextBlock(
                bbox=BoundingBox(5, 5, 40, 10), content="Header1", is_bold=True
            ),
            TextBlock(
                bbox=BoundingBox(55, 5, 40, 10), content="Header2", is_bold=True
            ),
            TextBlock(bbox=BoundingBox(5, 25, 40, 10), content="Data1", is_bold=False),
            TextBlock(
                bbox=BoundingBox(55, 25, 40, 10), content="Data2", is_bold=False
            ),
        ]

        result = extractor._detect_header_rows(table, text_blocks)

        assert 0 in result

    def test_first_row_large_font(self):
        """Test first row with large font is detected as header."""
        extractor = TableContentExtractor(header_font_size_ratio=1.1)

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0),
            TableCell(bbox=BoundingBox(50, 0, 50, 20), row=0, col=1),
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 20),
            cells=cells,
            num_rows=1,
            num_cols=2,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        text_blocks = [
            TextBlock(
                bbox=BoundingBox(5, 5, 40, 10), content="Header", font_size=16.0
            ),
            TextBlock(
                bbox=BoundingBox(55, 5, 40, 10), content="Header2", font_size=14.0
            ),
        ]

        result = extractor._detect_header_rows(table, text_blocks)

        assert 0 in result

    def test_no_formatting_defaults_first_row(self):
        """Test table with no special formatting defaults to first row."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0),
            TableCell(bbox=BoundingBox(0, 20, 50, 20), row=1, col=0),
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 50, 40),
            cells=cells,
            num_rows=2,
            num_cols=1,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        text_blocks = [
            TextBlock(
                bbox=BoundingBox(5, 5, 40, 10), content="Row1", font_size=12.0
            ),
            TextBlock(
                bbox=BoundingBox(5, 25, 40, 10), content="Row2", font_size=12.0
            ),
        ]

        result = extractor._detect_header_rows(table, text_blocks)

        assert result == [0]

    def test_empty_table(self):
        """Test empty table returns empty list."""
        extractor = TableContentExtractor()

        table = Table(
            bbox=BoundingBox(0, 0, 100, 100),
            cells=[],
            num_rows=0,
            num_cols=0,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        result = extractor._detect_header_rows(table, [])

        assert result == []


class TestExtractContent:
    """Test full content extraction pipeline."""

    def test_simple_table(self):
        """Test extracting content from simple 2x2 table."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0),
            TableCell(bbox=BoundingBox(50, 0, 50, 20), row=0, col=1),
            TableCell(bbox=BoundingBox(0, 20, 50, 20), row=1, col=0),
            TableCell(bbox=BoundingBox(50, 20, 50, 20), row=1, col=1),
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 40),
            cells=cells,
            num_rows=2,
            num_cols=2,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        text_blocks = [
            TextBlock(bbox=BoundingBox(5, 5, 40, 10), content="A", is_bold=True),
            TextBlock(bbox=BoundingBox(55, 5, 40, 10), content="B", is_bold=True),
            TextBlock(bbox=BoundingBox(5, 25, 40, 10), content="1"),
            TextBlock(bbox=BoundingBox(55, 25, 40, 10), content="2"),
        ]

        result = extractor.extract_content(table, text_blocks)

        assert result.cells[0].content == "A"
        assert result.cells[1].content == "B"
        assert result.cells[2].content == "1"
        assert result.cells[3].content == "2"
        assert result.header_rows == [0]

    def test_multi_line_cell(self):
        """Test cell with multiple lines of text."""
        extractor = TableContentExtractor()

        cells = [TableCell(bbox=BoundingBox(0, 0, 100, 50), row=0, col=0)]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 50),
            cells=cells,
            num_rows=1,
            num_cols=1,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        text_blocks = [
            TextBlock(bbox=BoundingBox(10, 10, 80, 10), content="First line"),
            TextBlock(bbox=BoundingBox(10, 25, 80, 10), content="Second line"),
        ]

        result = extractor.extract_content(table, text_blocks)

        assert result.cells[0].content == "First line\nSecond line"

    def test_empty_cells(self):
        """Test table with some empty cells that don't merge."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0),
            TableCell(bbox=BoundingBox(50, 0, 50, 20), row=0, col=1),
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 20),
            cells=cells,
            num_rows=1,
            num_cols=2,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        # Two text blocks, one in each cell to prevent merging
        text_blocks = [
            TextBlock(bbox=BoundingBox(5, 5, 40, 10), content="Data"),
            TextBlock(bbox=BoundingBox(55, 5, 40, 10), content="More"),
        ]

        result = extractor.extract_content(table, text_blocks)

        assert len(result.cells) == 2
        assert result.cells[0].content == "Data"
        assert result.cells[1].content == "More"


class TestSpanningCells:
    """Test detection of cells that span multiple rows/columns."""

    def test_no_spanning(self):
        """Test table with no spanning cells."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0, content="A"),
            TableCell(bbox=BoundingBox(50, 0, 50, 20), row=0, col=1, content="B"),
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 20),
            cells=cells,
            num_rows=1,
            num_cols=2,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        extractor._detect_spanning_cells(table)

        assert table.cells[0].col_span == 1
        assert table.cells[1].col_span == 1

    def test_horizontal_span(self):
        """Test cell spanning multiple columns."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0, content="Header"),
            TableCell(
                bbox=BoundingBox(50, 0, 50, 20), row=0, col=1, content=""
            ),  # Empty
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 100, 20),
            cells=cells.copy(),
            num_rows=1,
            num_cols=2,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        extractor._detect_spanning_cells(table)

        # First cell should span 2 columns, second should be removed
        assert any(c.col_span == 2 for c in table.cells)

    def test_vertical_span(self):
        """Test cell spanning multiple rows."""
        extractor = TableContentExtractor()

        cells = [
            TableCell(bbox=BoundingBox(0, 0, 50, 20), row=0, col=0, content="Data"),
            TableCell(
                bbox=BoundingBox(0, 20, 50, 20), row=1, col=0, content=""
            ),  # Empty
        ]

        table = Table(
            bbox=BoundingBox(0, 0, 50, 40),
            cells=cells.copy(),
            num_rows=2,
            num_cols=1,
            header_rows=[],
            method=TableDetectionMethod.STREAM,
        )

        extractor._detect_spanning_cells(table)

        # First cell should span 2 rows
        assert any(c.row_span == 2 for c in table.cells)
