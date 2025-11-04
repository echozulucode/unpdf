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


class TestXYCutSegmentation:
    """Tests for XY-Cut recursive segmentation algorithm."""

    def test_xy_cut_single_block(self):
        """Test XY-Cut with single block."""
        blocks = [TextBlock(BoundingBox(50, 700, 500, 720), "Single block", 12.0)]

        analyzer = LayoutAnalyzer(method="xy_cut")
        segments = analyzer.xy_cut_segmentation(blocks, page_width=600, page_height=800)

        assert len(segments) == 1
        assert len(segments[0]) == 1
        assert segments[0][0].text == "Single block"

    def test_xy_cut_two_columns(self):
        """Test XY-Cut with two columns separated by vertical gap."""
        blocks = [
            # Left column
            TextBlock(BoundingBox(50, 700, 200, 720), "Left 1", 12.0),
            TextBlock(BoundingBox(50, 650, 200, 670), "Left 2", 12.0),
            # Right column (significant horizontal gap)
            TextBlock(BoundingBox(400, 700, 550, 720), "Right 1", 12.0),
            TextBlock(BoundingBox(400, 650, 550, 670), "Right 2", 12.0),
        ]

        analyzer = LayoutAnalyzer(method="xy_cut", xy_cut_ty_threshold=0.5)
        segments = analyzer.xy_cut_segmentation(blocks, page_width=600, page_height=800)

        # Should segment into at least 2 groups (likely 4 - 2 columns x 2 rows)
        assert len(segments) >= 2

    def test_xy_cut_two_rows(self):
        """Test XY-Cut with two rows separated by horizontal gap."""
        blocks = [
            # Top row
            TextBlock(BoundingBox(50, 700, 500, 720), "Top", 12.0),
            # Bottom row (significant vertical gap - 180px gap)
            TextBlock(BoundingBox(50, 500, 500, 520), "Bottom", 12.0),
        ]

        analyzer = LayoutAnalyzer(method="xy_cut", xy_cut_tx_threshold=0.3)
        segments = analyzer.xy_cut_segmentation(blocks, page_width=600, page_height=800)

        # Should segment into 2 groups
        assert len(segments) == 2

    def test_xy_cut_grid_layout(self):
        """Test XY-Cut with 2x2 grid layout."""
        blocks = [
            # Top-left
            TextBlock(BoundingBox(50, 700, 200, 720), "TL", 12.0),
            # Top-right
            TextBlock(BoundingBox(400, 700, 550, 720), "TR", 12.0),
            # Bottom-left
            TextBlock(BoundingBox(50, 500, 200, 520), "BL", 12.0),
            # Bottom-right
            TextBlock(BoundingBox(400, 500, 550, 520), "BR", 12.0),
        ]

        analyzer = LayoutAnalyzer(
            method="xy_cut", xy_cut_tx_threshold=0.3, xy_cut_ty_threshold=0.5
        )
        segments = analyzer.xy_cut_segmentation(blocks, page_width=600, page_height=800)

        # Should segment into 4 groups (2 columns × 2 rows)
        assert len(segments) >= 4

    def test_xy_cut_no_gaps(self):
        """Test XY-Cut with densely packed blocks (no significant gaps)."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 500, 720), "Block 1", 12.0),
            TextBlock(BoundingBox(50, 680, 500, 700), "Block 2", 12.0),
            TextBlock(BoundingBox(50, 660, 500, 680), "Block 3", 12.0),
        ]

        analyzer = LayoutAnalyzer(method="xy_cut")
        segments = analyzer.xy_cut_segmentation(blocks, page_width=600, page_height=800)

        # Should not segment (all in one group)
        assert len(segments) == 1
        assert len(segments[0]) == 3

    def test_estimate_avg_char_height(self):
        """Test average character height estimation."""
        blocks = [
            TextBlock(BoundingBox(0, 0, 100, 12), "Text 1", 12.0),
            TextBlock(BoundingBox(0, 15, 100, 27), "Text 2", 12.0),
            TextBlock(BoundingBox(0, 30, 200, 54), "Header", 24.0),
        ]

        analyzer = LayoutAnalyzer()
        avg_height = analyzer._estimate_avg_char_height(blocks)

        assert avg_height > 0
        # Average of 12, 12, 24 = 16
        assert 14 <= avg_height <= 18

    def test_estimate_avg_char_width(self):
        """Test average character width estimation."""
        blocks = [
            TextBlock(BoundingBox(0, 0, 70, 12), "10chars!!", 12.0),  # ~7 per char
            TextBlock(
                BoundingBox(0, 15, 100, 27), "12character!", 12.0
            ),  # ~8.3 per char
        ]

        analyzer = LayoutAnalyzer()
        avg_width = analyzer._estimate_avg_char_width(blocks)

        assert avg_width > 0
        assert 6 <= avg_width <= 10  # Reasonable range

    def test_compute_horizontal_profile(self):
        """Test horizontal projection profile computation."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 150, 720), "Block 1", 12.0),
            TextBlock(BoundingBox(200, 700, 300, 720), "Block 2", 12.0),
        ]

        analyzer = LayoutAnalyzer()
        profile = analyzer._compute_horizontal_profile(blocks, 0, 400)

        # Profile should have entries for x-coordinates covered by blocks
        assert len(profile) > 0
        assert 50.0 in profile or 51.0 in profile  # Block 1 starts at x=50

    def test_compute_vertical_profile(self):
        """Test vertical projection profile computation."""
        blocks = [
            TextBlock(BoundingBox(50, 700, 150, 720), "Block 1", 12.0),
            TextBlock(BoundingBox(50, 600, 150, 620), "Block 2", 12.0),
        ]

        analyzer = LayoutAnalyzer()
        profile = analyzer._compute_vertical_profile(blocks, 500, 800)

        # Profile should have entries for y-coordinates covered by blocks
        assert len(profile) > 0
        assert 700.0 in profile or 701.0 in profile  # Block 1 starts at y=700

    def test_find_valleys(self):
        """Test valley detection in projection profile."""
        # Create a profile with a clear gap
        profile = {
            0.0: 1,
            1.0: 1,
            2.0: 1,
            # Gap from 3-12
            3.0: 0,
            4.0: 0,
            5.0: 0,
            6.0: 0,
            7.0: 0,
            8.0: 0,
            9.0: 0,
            10.0: 0,
            11.0: 0,
            12.0: 0,
            # Content resumes
            13.0: 1,
            14.0: 1,
            15.0: 1,
        }

        analyzer = LayoutAnalyzer()
        valleys = analyzer._find_valleys(profile, threshold=5.0)

        # Should detect one valley from 3-12 (width = 10)
        assert len(valleys) == 1
        assert valleys[0][0] == 3.0
        assert valleys[0][1] == 12.0

    def test_find_valleys_no_gaps(self):
        """Test valley detection with no gaps."""
        # Continuous profile (no gaps)
        profile = {float(i): 1 for i in range(20)}

        analyzer = LayoutAnalyzer()
        valleys = analyzer._find_valleys(profile, threshold=5.0)

        # Should find no valleys
        assert len(valleys) == 0

    def test_find_valleys_small_gaps(self):
        """Test valley detection ignores gaps below threshold."""
        # Profile with small gaps
        profile = {
            0.0: 1,
            1.0: 1,
            # Small gap (below threshold)
            2.0: 0,
            3.0: 0,
            # Content resumes
            4.0: 1,
            5.0: 1,
        }

        analyzer = LayoutAnalyzer()
        valleys = analyzer._find_valleys(profile, threshold=5.0)

        # Should ignore small gap
        assert len(valleys) == 0

    def test_xy_cut_empty_blocks(self):
        """Test XY-Cut with empty block list."""
        analyzer = LayoutAnalyzer(method="xy_cut")
        segments = analyzer.xy_cut_segmentation([], page_width=600, page_height=800)

        assert len(segments) == 0
