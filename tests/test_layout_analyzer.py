"""Tests for layout analyzer."""

from unpdf.processors.layout_analyzer import (
    BoundingBox,
    LayoutAnalyzer,
    TextBlock,
    analyze_page_layout,
)


class TestBoundingBox:
    """Tests for BoundingBox class."""

    def test_width_height(self):
        """Test width and height properties."""
        bbox = BoundingBox(10, 20, 50, 80)
        assert bbox.width == 40
        assert bbox.height == 60

    def test_center(self):
        """Test center calculation."""
        bbox = BoundingBox(0, 0, 100, 50)
        assert bbox.center_x == 50
        assert bbox.center_y == 25

    def test_overlaps_horizontally(self):
        """Test horizontal overlap detection."""
        bbox1 = BoundingBox(0, 0, 50, 10)
        bbox2 = BoundingBox(40, 0, 100, 10)
        bbox3 = BoundingBox(60, 0, 100, 10)

        assert bbox1.overlaps_horizontally(bbox2)
        assert not bbox1.overlaps_horizontally(bbox3)

    def test_overlaps_vertically(self):
        """Test vertical overlap detection."""
        bbox1 = BoundingBox(0, 0, 10, 50)
        bbox2 = BoundingBox(0, 40, 10, 100)
        bbox3 = BoundingBox(0, 60, 10, 100)

        assert bbox1.overlaps_vertically(bbox2)
        assert not bbox1.overlaps_vertically(bbox3)

    def test_contains(self):
        """Test containment detection."""
        outer = BoundingBox(0, 0, 100, 100)
        inner = BoundingBox(10, 10, 50, 50)
        separate = BoundingBox(200, 200, 300, 300)

        assert outer.contains(inner)
        assert not inner.contains(outer)
        assert not outer.contains(separate)


class TestLayoutAnalyzer:
    """Tests for LayoutAnalyzer class."""

    def test_single_column_detection(self):
        """Test detection of single column layout."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 500, 720), "Header", 16.0),
            TextBlock(BoundingBox(50, 650, 500, 670), "Paragraph 1", 12.0),
            TextBlock(BoundingBox(50, 600, 500, 620), "Paragraph 2", 12.0),
        ]

        analyzer = LayoutAnalyzer()
        columns = analyzer.detect_columns(blocks, page_width=600)

        assert len(columns) == 1
        assert len(columns[0].blocks) == 3
        assert columns[0].index == 0

    def test_two_column_detection(self):
        """Test detection of two column layout."""
        blocks = [
            # Left column
            TextBlock(BoundingBox(50, 700, 250, 720), "Left col 1", 12.0),
            TextBlock(BoundingBox(50, 650, 250, 670), "Left col 2", 12.0),
            # Right column
            TextBlock(BoundingBox(350, 700, 550, 720), "Right col 1", 12.0),
            TextBlock(BoundingBox(350, 650, 550, 670), "Right col 2", 12.0),
        ]

        analyzer = LayoutAnalyzer(column_gap_threshold=0.1)
        columns = analyzer.detect_columns(blocks, page_width=600)

        assert len(columns) == 2
        assert all(b.column_index == 0 for b in columns[0].blocks)
        assert all(b.column_index == 1 for b in columns[1].blocks)

    def test_three_column_detection(self):
        """Test detection of three column layout."""
        blocks = [
            # Left column
            TextBlock(BoundingBox(50, 700, 200, 720), "Left", 12.0),
            # Middle column
            TextBlock(BoundingBox(250, 700, 400, 720), "Middle", 12.0),
            # Right column
            TextBlock(BoundingBox(450, 700, 600, 720), "Right", 12.0),
        ]

        analyzer = LayoutAnalyzer(column_gap_threshold=0.05, min_column_width_ratio=0.2)
        columns = analyzer.detect_columns(blocks, page_width=650)

        assert len(columns) == 3

    def test_find_vertical_gaps(self):
        """Test vertical gap detection."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 250, 720), "Left", 12.0),
            TextBlock(BoundingBox(350, 700, 550, 720), "Right", 12.0),
        ]

        analyzer = LayoutAnalyzer(column_gap_threshold=0.1)
        sorted_blocks = sorted(blocks, key=lambda b: b.bbox.x0)
        gaps = analyzer._find_vertical_gaps(sorted_blocks, page_width=600)

        assert len(gaps) == 1
        assert gaps[0][0] == 250  # gap starts after left block
        assert gaps[0][1] == 350  # gap ends before right block

    def test_reading_order_single_column(self):
        """Test reading order for single column."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 500, 720), "First", 12.0),
            TextBlock(BoundingBox(50, 650, 500, 670), "Second", 12.0),
            TextBlock(BoundingBox(50, 600, 500, 620), "Third", 12.0),
        ]

        analyzer = LayoutAnalyzer()
        columns = analyzer.detect_columns(blocks, page_width=600)
        ordered = analyzer.determine_reading_order(columns)

        assert len(ordered) == 3
        assert ordered[0].text == "First"
        assert ordered[1].text == "Second"
        assert ordered[2].text == "Third"
        assert ordered[0].reading_order == 0
        assert ordered[1].reading_order == 1
        assert ordered[2].reading_order == 2

    def test_reading_order_two_columns(self):
        """Test reading order for two column layout."""
        blocks = [
            # Left column
            TextBlock(BoundingBox(50, 700, 250, 720), "Top left", 12.0),
            TextBlock(BoundingBox(50, 650, 250, 670), "Bottom left", 12.0),
            # Right column
            TextBlock(BoundingBox(350, 700, 550, 720), "Top right", 12.0),
            TextBlock(BoundingBox(350, 650, 550, 670), "Bottom right", 12.0),
        ]

        analyzer = LayoutAnalyzer(column_gap_threshold=0.1)
        columns = analyzer.detect_columns(blocks, page_width=600)
        ordered = analyzer.determine_reading_order(columns)

        # Should read top-to-bottom
        assert ordered[0].text == "Top left"
        assert ordered[1].text == "Top right"

    def test_empty_blocks(self):
        """Test handling of empty block list."""
        analyzer = LayoutAnalyzer()
        columns = analyzer.detect_columns([], page_width=600)

        assert len(columns) == 0

    def test_column_width_threshold(self):
        """Test minimum column width threshold."""
        # Create a very narrow "column" that should be filtered out
        blocks = [
            TextBlock(BoundingBox(50, 700, 500, 720), "Main content", 12.0),
            TextBlock(BoundingBox(550, 700, 560, 710), "Tiny", 8.0),
        ]

        analyzer = LayoutAnalyzer(min_column_width_ratio=0.3)
        columns = analyzer.detect_columns(blocks, page_width=600)

        # Tiny column should be filtered out
        assert len(columns) <= 2


class TestAnalyzePageLayout:
    """Tests for analyze_page_layout function."""

    def test_analyze_single_column(self):
        """Test full page layout analysis for single column."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 500, 720), "Header", 16.0),
            TextBlock(BoundingBox(50, 650, 500, 670), "Content", 12.0),
        ]

        columns, ordered = analyze_page_layout(blocks, page_width=600, page_height=800)

        assert len(columns) == 1
        assert len(ordered) == 2
        assert ordered[0].reading_order is not None

    def test_analyze_multi_column(self):
        """Test full page layout analysis for multi-column."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 250, 720), "Left", 12.0),
            TextBlock(BoundingBox(350, 700, 550, 720), "Right", 12.0),
        ]

        columns, ordered = analyze_page_layout(blocks, page_width=600, page_height=800)

        assert len(columns) >= 1
        assert len(ordered) == 2
        assert all(b.reading_order is not None for b in ordered)

    def test_analyze_empty_page(self):
        """Test analysis of empty page."""
        columns, ordered = analyze_page_layout([], page_width=600, page_height=800)

        assert len(columns) == 0
        assert len(ordered) == 0
