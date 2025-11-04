"""Tests for whitespace analysis module."""


from unpdf.processors.layout_analyzer import BoundingBox, TextBlock
from unpdf.processors.whitespace import (
    WhitespaceAnalyzer,
    calculate_avg_line_height,
)


class TestWhitespaceAnalyzer:
    """Test suite for WhitespaceAnalyzer."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        analyzer = WhitespaceAnalyzer()
        assert analyzer.column_gap_threshold == 0.15
        assert analyzer.paragraph_gap_multiplier == 1.5
        assert analyzer.alignment_tolerance == 10.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        analyzer = WhitespaceAnalyzer(
            column_gap_threshold=0.2,
            paragraph_gap_multiplier=2.0,
            alignment_tolerance=5.0,
        )
        assert analyzer.column_gap_threshold == 0.2
        assert analyzer.paragraph_gap_multiplier == 2.0
        assert analyzer.alignment_tolerance == 5.0

    def test_detect_column_boundaries_empty(self):
        """Test column detection with no blocks."""
        analyzer = WhitespaceAnalyzer()
        boundaries = analyzer.detect_column_boundaries([], 600.0)
        assert boundaries == []

    def test_detect_column_boundaries_single_column(self):
        """Test column detection with single column layout."""
        analyzer = WhitespaceAnalyzer(column_gap_threshold=0.15)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=100), text="Block 1"),
            TextBlock(bbox=BoundingBox(x0=50, y0=120, x1=500, y1=170), text="Block 2"),
        ]
        boundaries = analyzer.detect_column_boundaries(blocks, 600.0)
        # No column boundaries in single column
        assert len(boundaries) == 0

    def test_detect_column_boundaries_two_columns(self):
        """Test column detection with two-column layout."""
        analyzer = WhitespaceAnalyzer(column_gap_threshold=0.15)
        blocks = [
            # Left column
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=250, y1=100), text="Left 1"),
            TextBlock(bbox=BoundingBox(x0=50, y0=120, x1=250, y1=170), text="Left 2"),
            # Right column (gap of 100px, page width 600 -> 100/600 = 0.167 > 0.15)
            TextBlock(bbox=BoundingBox(x0=350, y0=50, x1=550, y1=100), text="Right 1"),
            TextBlock(bbox=BoundingBox(x0=350, y0=120, x1=550, y1=170), text="Right 2"),
        ]
        boundaries = analyzer.detect_column_boundaries(blocks, 600.0)
        assert len(boundaries) == 1
        # Boundary should be in the middle of the gap (250-350 = 100, midpoint = 300)
        assert abs(boundaries[0] - 300.0) < 1.0

    def test_detect_paragraph_boundaries_empty(self):
        """Test paragraph detection with no blocks."""
        analyzer = WhitespaceAnalyzer()
        boundaries = analyzer.detect_paragraph_boundaries([], 20.0)
        assert boundaries == []

    def test_detect_paragraph_boundaries_no_gaps(self):
        """Test paragraph detection with no significant gaps."""
        analyzer = WhitespaceAnalyzer(paragraph_gap_multiplier=1.5)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=70), text="Line 1"),
            TextBlock(
                bbox=BoundingBox(x0=50, y0=75, x1=500, y1=95), text="Line 2"
            ),  # Gap: 5px
            TextBlock(
                bbox=BoundingBox(x0=50, y0=100, x1=500, y1=120), text="Line 3"
            ),  # Gap: 5px
        ]
        boundaries = analyzer.detect_paragraph_boundaries(blocks, 20.0)
        # No gaps >= 1.5 * 20 = 30px
        assert boundaries == []

    def test_detect_paragraph_boundaries_with_gaps(self):
        """Test paragraph detection with paragraph gaps."""
        analyzer = WhitespaceAnalyzer(paragraph_gap_multiplier=1.5)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=70), text="Para 1"),
            TextBlock(
                bbox=BoundingBox(x0=50, y0=105, x1=500, y1=125), text="Para 2"
            ),  # Gap: 35px
            TextBlock(
                bbox=BoundingBox(x0=50, y0=160, x1=500, y1=180), text="Para 3"
            ),  # Gap: 35px
        ]
        boundaries = analyzer.detect_paragraph_boundaries(blocks, 20.0)
        # Two paragraph boundaries (1.5 * 20 = 30px threshold)
        assert boundaries == [(0, 1), (1, 2)]

    def test_detect_section_boundaries_empty(self):
        """Test section detection with no blocks."""
        analyzer = WhitespaceAnalyzer()
        sections = analyzer.detect_section_boundaries([], 20.0)
        assert sections == []

    def test_detect_section_boundaries_no_large_gaps(self):
        """Test section detection with only paragraph-sized gaps."""
        analyzer = WhitespaceAnalyzer(paragraph_gap_multiplier=1.5)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=70), text="Para 1"),
            TextBlock(
                bbox=BoundingBox(x0=50, y0=105, x1=500, y1=125), text="Para 2"
            ),  # Gap: 35px
        ]
        sections = analyzer.detect_section_boundaries(blocks, 20.0)
        # Gap is 35px, threshold is 1.5 * 2 * 20 = 60px
        assert sections == []

    def test_detect_section_boundaries_with_large_gaps(self):
        """Test section detection with section-sized gaps."""
        analyzer = WhitespaceAnalyzer(paragraph_gap_multiplier=1.5)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=70), text="Section 1"),
            TextBlock(
                bbox=BoundingBox(x0=50, y0=135, x1=500, y1=155), text="Section 2"
            ),  # Gap: 65px
            TextBlock(
                bbox=BoundingBox(x0=50, y0=220, x1=500, y1=240), text="Section 3"
            ),  # Gap: 65px
        ]
        sections = analyzer.detect_section_boundaries(blocks, 20.0)
        # Two section boundaries (1.5 * 2 * 20 = 60px threshold)
        assert sections == [1, 2]

    def test_build_spatial_graph_empty(self):
        """Test spatial graph with no blocks."""
        analyzer = WhitespaceAnalyzer()
        graph = analyzer.build_spatial_graph([])
        assert graph == {}

    def test_build_spatial_graph_single_block(self):
        """Test spatial graph with single block."""
        analyzer = WhitespaceAnalyzer()
        blocks = [TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=100), text="A")]
        graph = analyzer.build_spatial_graph(blocks)
        assert graph == {0: {"up": None, "down": None, "left": None, "right": None}}

    def test_build_spatial_graph_vertical_alignment(self):
        """Test spatial graph with vertically aligned blocks."""
        analyzer = WhitespaceAnalyzer(alignment_tolerance=10.0)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=100), text="Top"),
            TextBlock(bbox=BoundingBox(x0=50, y0=120, x1=500, y1=170), text="Middle"),
            TextBlock(bbox=BoundingBox(x0=50, y0=190, x1=500, y1=240), text="Bottom"),
        ]
        graph = analyzer.build_spatial_graph(blocks)

        # Top block: down -> Middle
        assert graph[0]["up"] is None
        assert graph[0]["down"] == 1
        # Middle block: up -> Top, down -> Bottom
        assert graph[1]["up"] == 0
        assert graph[1]["down"] == 2
        # Bottom block: up -> Middle
        assert graph[2]["up"] == 1
        assert graph[2]["down"] is None

    def test_build_spatial_graph_horizontal_alignment(self):
        """Test spatial graph with horizontally aligned blocks."""
        analyzer = WhitespaceAnalyzer(alignment_tolerance=10.0)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=150, y1=100), text="Left"),
            TextBlock(bbox=BoundingBox(x0=200, y0=50, x1=300, y1=100), text="Middle"),
            TextBlock(bbox=BoundingBox(x0=350, y0=50, x1=450, y1=100), text="Right"),
        ]
        graph = analyzer.build_spatial_graph(blocks)

        # Left block: right -> Middle
        assert graph[0]["left"] is None
        assert graph[0]["right"] == 1
        # Middle block: left -> Left, right -> Right
        assert graph[1]["left"] == 0
        assert graph[1]["right"] == 2
        # Right block: left -> Middle
        assert graph[2]["left"] == 1
        assert graph[2]["right"] is None

    def test_build_spatial_graph_two_column_layout(self):
        """Test spatial graph with two-column layout."""
        analyzer = WhitespaceAnalyzer(alignment_tolerance=10.0)
        blocks = [
            # Left column
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=250, y1=100), text="L1"),
            TextBlock(bbox=BoundingBox(x0=50, y0=120, x1=250, y1=170), text="L2"),
            # Right column
            TextBlock(bbox=BoundingBox(x0=300, y0=50, x1=500, y1=100), text="R1"),
            TextBlock(bbox=BoundingBox(x0=300, y0=120, x1=500, y1=170), text="R2"),
        ]
        graph = analyzer.build_spatial_graph(blocks)

        # L1: down -> L2, right -> R1
        assert graph[0]["down"] == 1
        assert graph[0]["right"] == 2
        # L2: up -> L1, right -> R2
        assert graph[1]["up"] == 0
        assert graph[1]["right"] == 3
        # R1: down -> R2, left -> L1
        assert graph[2]["down"] == 3
        assert graph[2]["left"] == 0
        # R2: up -> R1, left -> L2
        assert graph[3]["up"] == 2
        assert graph[3]["left"] == 1

    def test_get_spatial_relationships_empty(self):
        """Test spatial relationships with no blocks."""
        analyzer = WhitespaceAnalyzer()
        relationships = analyzer.get_spatial_relationships([])
        assert relationships == []

    def test_get_spatial_relationships_vertical(self):
        """Test spatial relationships with vertical alignment."""
        analyzer = WhitespaceAnalyzer()
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=100), text="Top"),
            TextBlock(bbox=BoundingBox(x0=50, y0=120, x1=500, y1=170), text="Bottom"),
        ]
        relationships = analyzer.get_spatial_relationships(blocks)

        # Two relationships: Top->Bottom (down), Bottom->Top (up)
        assert len(relationships) == 2

        # Find down relationship
        down_rel = next(r for r in relationships if r.direction == "down")
        assert down_rel.source_id == 0
        assert down_rel.target_id == 1
        assert down_rel.distance == 20.0  # 120 - 100
        assert down_rel.confidence > 0.9  # Perfect alignment

        # Find up relationship
        up_rel = next(r for r in relationships if r.direction == "up")
        assert up_rel.source_id == 1
        assert up_rel.target_id == 0
        assert up_rel.distance == 20.0  # 120 - 100

    def test_get_spatial_relationships_horizontal(self):
        """Test spatial relationships with horizontal alignment."""
        analyzer = WhitespaceAnalyzer()
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=200, y1=100), text="Left"),
            TextBlock(bbox=BoundingBox(x0=250, y0=50, x1=400, y1=100), text="Right"),
        ]
        relationships = analyzer.get_spatial_relationships(blocks)

        # Two relationships: Left->Right (right), Right->Left (left)
        assert len(relationships) == 2

        # Find right relationship
        right_rel = next(r for r in relationships if r.direction == "right")
        assert right_rel.source_id == 0
        assert right_rel.target_id == 1
        assert right_rel.distance == 50.0  # 250 - 200
        assert right_rel.confidence > 0.9  # Perfect alignment

        # Find left relationship
        left_rel = next(r for r in relationships if r.direction == "left")
        assert left_rel.source_id == 1
        assert left_rel.target_id == 0
        assert left_rel.distance == 50.0  # 250 - 200

    def test_alignment_tolerance(self):
        """Test alignment tolerance in spatial graph."""
        analyzer = WhitespaceAnalyzer(alignment_tolerance=10.0)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=500, y1=100), text="Top"),
            TextBlock(
                bbox=BoundingBox(x0=55, y0=120, x1=505, y1=170), text="Bottom"
            ),  # Offset by 5px
        ]
        graph = analyzer.build_spatial_graph(blocks)

        # Should still be connected (5px < 10px tolerance)
        assert graph[0]["down"] == 1
        assert graph[1]["up"] == 0

    def test_alignment_strict_tolerance(self):
        """Test strict alignment with small tolerance and no overlap."""
        analyzer = WhitespaceAnalyzer(alignment_tolerance=2.0)
        blocks = [
            TextBlock(bbox=BoundingBox(x0=50, y0=50, x1=100, y1=100), text="Top"),
            TextBlock(
                bbox=BoundingBox(x0=110, y0=120, x1=160, y1=170), text="Side"
            ),  # Offset by 10px, no overlap
        ]
        graph = analyzer.build_spatial_graph(blocks)

        # Should NOT be connected (10px > 2px tolerance, no horizontal overlap)
        assert graph[0].get("down") is None
        assert graph[1].get("up") is None


class TestCalculateAvgLineHeight:
    """Test suite for calculate_avg_line_height function."""

    def test_empty_blocks(self):
        """Test with empty list of blocks."""
        assert calculate_avg_line_height([]) == 0.0

    def test_single_block(self):
        """Test with single block."""
        blocks = [TextBlock(bbox=BoundingBox(x0=0, y0=0, x1=100, y1=20), text="Test")]
        assert calculate_avg_line_height(blocks) == 20.0

    def test_multiple_blocks(self):
        """Test with multiple blocks."""
        blocks = [
            TextBlock(bbox=BoundingBox(x0=0, y0=0, x1=100, y1=20), text="Line 1"),
            TextBlock(bbox=BoundingBox(x0=0, y0=25, x1=100, y1=45), text="Line 2"),
            TextBlock(bbox=BoundingBox(x0=0, y0=50, x1=100, y1=80), text="Line 3"),
        ]
        # Heights: 20, 20, 30 -> avg = 23.33
        avg = calculate_avg_line_height(blocks)
        assert abs(avg - 23.33) < 0.01

    def test_ignores_zero_height_blocks(self):
        """Test that zero-height blocks are ignored."""
        blocks = [
            TextBlock(bbox=BoundingBox(x0=0, y0=0, x1=100, y1=20), text="Line 1"),
            TextBlock(bbox=BoundingBox(x0=0, y0=20, x1=100, y1=20), text="Zero"),
            TextBlock(bbox=BoundingBox(x0=0, y0=25, x1=100, y1=45), text="Line 2"),
        ]
        # Only 20 and 20 should be counted -> avg = 20.0
        assert calculate_avg_line_height(blocks) == 20.0

    def test_all_zero_height_blocks(self):
        """Test with all zero-height blocks."""
        blocks = [
            TextBlock(bbox=BoundingBox(x0=0, y0=0, x1=100, y1=0), text="A"),
            TextBlock(bbox=BoundingBox(x0=0, y0=0, x1=100, y1=0), text="B"),
        ]
        assert calculate_avg_line_height(blocks) == 0.0
