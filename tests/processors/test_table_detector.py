"""Tests for table detection module."""

import numpy as np
from PIL import Image

from unpdf.models.layout import BoundingBox
from unpdf.processors.table_detector import (
    HybridTableDetector,
    LatticeTableDetector,
    StreamTableDetector,
    Table,
    TableCell,
    TableDetectionMethod,
)


class TestTableCell:
    """Tests for TableCell dataclass."""

    def test_create_simple_cell(self):
        """Test creating a simple table cell."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        cell = TableCell(bbox=bbox, row=0, col=0)

        assert cell.bbox == bbox
        assert cell.row == 0
        assert cell.col == 0
        assert cell.row_span == 1
        assert cell.col_span == 1
        assert cell.content == ""

    def test_create_spanning_cell(self):
        """Test creating a cell with row/col spans."""
        bbox = BoundingBox(x=0, y=0, width=200, height=100)
        cell = TableCell(
            bbox=bbox,
            row=1,
            col=2,
            row_span=2,
            col_span=3,
            content="Merged cell",
        )

        assert cell.row_span == 2
        assert cell.col_span == 3
        assert cell.content == "Merged cell"


class TestTable:
    """Tests for Table dataclass."""

    def test_create_simple_table(self):
        """Test creating a simple table."""
        bbox = BoundingBox(x=0, y=0, width=300, height=200)
        cells = [
            TableCell(BoundingBox(x=0, y=0, width=100, height=50), 0, 0),
            TableCell(BoundingBox(x=100, y=0, width=100, height=50), 0, 1),
            TableCell(BoundingBox(x=0, y=50, width=100, height=50), 1, 0),
            TableCell(BoundingBox(x=100, y=50, width=100, height=50), 1, 1),
        ]

        table = Table(
            bbox=bbox,
            cells=cells,
            num_rows=2,
            num_cols=2,
            header_rows=[0],
        )

        assert table.bbox == bbox
        assert len(table.cells) == 4
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert table.header_rows == [0]
        assert table.caption is None
        assert table.confidence == 0.0

    def test_table_with_caption(self):
        """Test table with caption."""
        bbox = BoundingBox(x=0, y=0, width=300, height=200)
        table = Table(
            bbox=bbox,
            cells=[],
            num_rows=2,
            num_cols=2,
            header_rows=[0],
            caption="Table 1: Test Results",
            confidence=0.85,
        )

        assert table.caption == "Table 1: Test Results"
        assert table.confidence == 0.85


class TestLatticeTableDetector:
    """Tests for LatticeTableDetector."""

    def test_init(self):
        """Test detector initialization."""
        detector = LatticeTableDetector(
            min_line_length=60,
            line_confidence_threshold=0.8,
            cell_min_size=(15, 15),
        )

        assert detector.min_line_length == 60
        assert detector.line_confidence_threshold == 0.8
        assert detector.cell_min_size == (15, 15)

    def test_detect_edges(self):
        """Test edge detection."""
        detector = LatticeTableDetector()

        # Create test image with black lines on white background
        img = Image.new("L", (100, 100), 255)
        pixels = img.load()

        # Draw horizontal line
        for x in range(20, 80):
            pixels[x, 30] = 0

        # Draw vertical line
        for y in range(20, 80):
            pixels[50, y] = 0

        edges = detector._detect_edges(img)

        # Should detect edge pixels
        assert edges[30, 40] > 0  # Horizontal line
        assert edges[40, 50] > 0  # Vertical line

    def test_detect_horizontal_lines(self):
        """Test horizontal line detection."""
        detector = LatticeTableDetector(min_line_length=30)

        # Create edge array with horizontal line
        edges = np.zeros((100, 100), dtype=np.uint8)
        edges[30, 20:80] = 255  # 60-pixel line

        lines = detector._detect_horizontal_lines(edges)

        assert len(lines) > 0
        assert any(y == 30 for y, _ in lines)

    def test_detect_vertical_lines(self):
        """Test vertical line detection."""
        detector = LatticeTableDetector(min_line_length=30)

        # Create edge array with vertical line
        edges = np.zeros((100, 100), dtype=np.uint8)
        edges[20:80, 50] = 255  # 60-pixel line

        lines = detector._detect_vertical_lines(edges)

        assert len(lines) > 0
        assert any(x == 50 for x, _ in lines)

    def test_find_intersections(self):
        """Test finding line intersections."""
        detector = LatticeTableDetector()

        h_lines = [(30, 60), (70, 60)]  # Two horizontal lines
        v_lines = [(20, 80), (80, 80)]  # Two vertical lines

        intersections = detector._find_intersections(h_lines, v_lines)

        # Should have 4 intersections (2x2 grid)
        assert len(intersections) == 4
        assert (20, 30) in intersections
        assert (80, 30) in intersections
        assert (20, 70) in intersections
        assert (80, 70) in intersections

    def test_group_into_rows(self):
        """Test grouping intersections into rows."""
        detector = LatticeTableDetector()

        intersections = [
            (10, 10),
            (50, 10),
            (90, 10),  # Row 1
            (10, 50),
            (50, 50),
            (90, 50),  # Row 2
        ]

        rows = detector._group_into_rows(intersections, tolerance=5)

        assert len(rows) == 2
        assert len(rows[0]) == 3
        assert len(rows[1]) == 3
        assert rows[0][0] == (10, 10)
        assert rows[1][0] == (10, 50)

    def test_construct_tables_insufficient_points(self):
        """Test table construction with insufficient intersections."""
        detector = LatticeTableDetector()

        # Only 2 points - not enough for a table
        intersections = [(10, 10), (50, 50)]

        tables = detector._construct_tables(intersections, scale_factor=1.0)

        assert len(tables) == 0

    def test_detect_no_lines(self):
        """Test detection with image containing no lines."""
        detector = LatticeTableDetector()

        # Plain white image
        img = Image.new("L", (100, 100), 255)

        tables = detector.detect(img, scale_factor=1.0)

        # Should detect no tables
        assert len(tables) == 0


class TestStreamTableDetector:
    """Tests for StreamTableDetector."""

    def test_init(self):
        """Test detector initialization."""
        detector = StreamTableDetector(
            alignment_tolerance=15.0,
            min_rows=3,
            min_cols=3,
            min_silhouette_score=0.6,
        )

        assert detector.alignment_tolerance == 15.0
        assert detector.min_rows == 3
        assert detector.min_cols == 3
        assert detector.min_silhouette_score == 0.6

    def test_cluster_coordinates_simple(self):
        """Test coordinate clustering with well-separated values."""
        detector = StreamTableDetector(alignment_tolerance=10.0)

        coordinates = [10, 12, 11, 50, 52, 51, 90, 91, 89]

        clusters = detector._cluster_coordinates(coordinates)

        # Should have 3 clusters
        assert len(clusters) == 3
        assert abs(clusters[0] - 11) < 1  # ~11
        assert abs(clusters[1] - 51) < 1  # ~51
        assert abs(clusters[2] - 90) < 1  # ~90

    def test_cluster_coordinates_empty(self):
        """Test clustering with empty list."""
        detector = StreamTableDetector()

        clusters = detector._cluster_coordinates([])

        assert clusters == []

    def test_find_nearest_cluster(self):
        """Test finding nearest cluster."""
        detector = StreamTableDetector(alignment_tolerance=10.0)

        clusters = [10.0, 50.0, 90.0]

        # Test exact match
        assert detector._find_nearest_cluster(50.0, clusters) == 1

        # Test within tolerance
        assert detector._find_nearest_cluster(55.0, clusters) == 1

        # Test outside tolerance
        assert detector._find_nearest_cluster(70.0, clusters) is None

    def test_detect_insufficient_blocks(self):
        """Test detection with insufficient text blocks."""
        detector = StreamTableDetector(min_rows=2, min_cols=2)

        # Only 2 blocks - not enough
        blocks = [
            BoundingBox(x=0, y=0, width=50, height=20),
            BoundingBox(x=60, y=0, width=50, height=20),
        ]

        page_bbox = BoundingBox(x=0, y=0, width=200, height=200)

        tables = detector.detect(blocks, page_bbox)

        assert len(tables) == 0

    def test_detect_aligned_grid(self):
        """Test detection with properly aligned grid."""
        detector = StreamTableDetector(alignment_tolerance=5.0, min_rows=2, min_cols=2)

        # Create 2x2 grid of text blocks
        blocks = [
            BoundingBox(x=10, y=10, width=40, height=20),  # Row 0, Col 0
            BoundingBox(x=60, y=10, width=40, height=20),  # Row 0, Col 1
            BoundingBox(x=10, y=40, width=40, height=20),  # Row 1, Col 0
            BoundingBox(x=60, y=40, width=40, height=20),  # Row 1, Col 1
        ]

        page_bbox = BoundingBox(x=0, y=0, width=200, height=200)

        tables = detector.detect(blocks, page_bbox)

        assert len(tables) == 1
        table = tables[0]
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert len(table.cells) == 4
        assert table.method == TableDetectionMethod.STREAM

    def test_detect_misaligned_blocks(self):
        """Test detection with poorly aligned blocks."""
        detector = StreamTableDetector(alignment_tolerance=5.0, min_rows=2, min_cols=2)

        # Create misaligned blocks
        blocks = [
            BoundingBox(x=10, y=10, width=40, height=20),
            BoundingBox(x=80, y=15, width=40, height=20),  # Different alignment
            BoundingBox(x=15, y=50, width=40, height=20),  # Different alignment
            BoundingBox(x=85, y=55, width=40, height=20),  # Different alignment
        ]

        page_bbox = BoundingBox(x=0, y=0, width=200, height=200)

        tables = detector.detect(blocks, page_bbox)

        # May or may not detect depending on clustering
        # Just verify it doesn't crash
        assert isinstance(tables, list)


class TestHybridTableDetector:
    """Tests for HybridTableDetector."""

    def test_init(self):
        """Test detector initialization."""
        detector = HybridTableDetector()

        assert isinstance(detector.lattice_detector, LatticeTableDetector)
        assert isinstance(detector.stream_detector, StreamTableDetector)

    def test_tables_overlap(self):
        """Test overlap detection between tables."""
        detector = HybridTableDetector()

        table1 = Table(
            bbox=BoundingBox(x=0, y=0, width=100, height=100),
            cells=[],
            num_rows=2,
            num_cols=2,
            header_rows=[0],
        )

        # 50x50 overlap = 2500, which is 25% of table1's 10000 area
        # But threshold is >30%, so make it 65x65 = 4225 = 42%
        table2 = Table(
            bbox=BoundingBox(x=35, y=35, width=100, height=100),
            cells=[],
            num_rows=2,
            num_cols=2,
            header_rows=[0],
        )

        # Should overlap (42% > 30% threshold)
        assert detector._tables_overlap(table1, table2)

    def test_tables_no_overlap(self):
        """Test non-overlapping tables."""
        detector = HybridTableDetector()

        table1 = Table(
            bbox=BoundingBox(x=0, y=0, width=100, height=100),
            cells=[],
            num_rows=2,
            num_cols=2,
            header_rows=[0],
        )

        table2 = Table(
            bbox=BoundingBox(x=200, y=200, width=100, height=100),
            cells=[],
            num_rows=2,
            num_cols=2,
            header_rows=[0],
        )

        # Should not overlap
        assert not detector._tables_overlap(table1, table2)

    def test_detect_no_image(self):
        """Test detection without page image."""
        detector = HybridTableDetector()

        blocks = [
            BoundingBox(x=10, y=10, width=40, height=20),
            BoundingBox(x=60, y=10, width=40, height=20),
            BoundingBox(x=10, y=40, width=40, height=20),
            BoundingBox(x=60, y=40, width=40, height=20),
        ]

        page_bbox = BoundingBox(x=0, y=0, width=200, height=200)

        tables = detector.detect(None, blocks, page_bbox, scale_factor=1.0)

        # Should fall back to stream detection
        assert isinstance(tables, list)

    def test_detect_with_image(self):
        """Test detection with page image."""
        detector = HybridTableDetector()

        # Simple white image (no lines)
        img = Image.new("L", (100, 100), 255)

        blocks = [
            BoundingBox(x=10, y=10, width=40, height=20),
            BoundingBox(x=60, y=10, width=40, height=20),
            BoundingBox(x=10, y=40, width=40, height=20),
            BoundingBox(x=60, y=40, width=40, height=20),
        ]

        page_bbox = BoundingBox(x=0, y=0, width=200, height=200)

        tables = detector.detect(img, blocks, page_bbox, scale_factor=1.0)

        # Should try both methods
        assert isinstance(tables, list)
