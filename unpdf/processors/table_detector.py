"""Advanced table detection using multiple strategies.

This module implements multiple table detection methods:
1. Lattice Method: For tables with visible borders/lines
2. Stream Method: For borderless tables using text alignment
3. Hybrid Method: Combining both approaches for robustness
"""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from PIL import Image

from unpdf.models.layout import BoundingBox


class TableDetectionMethod(Enum):
    """Method used for table detection."""

    LATTICE = "lattice"
    STREAM = "stream"
    HYBRID = "hybrid"


@dataclass
class TableCell:
    """Represents a single table cell.

    Attributes:
        bbox: Cell bounding box
        row: Row index (0-based)
        col: Column index (0-based)
        row_span: Number of rows cell spans
        col_span: Number of columns cell spans
        content: Text content of the cell
    """

    bbox: BoundingBox
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    content: str = ""


@dataclass
class Table:
    """Represents a detected table with structure.

    Attributes:
        bbox: Overall table bounding box
        cells: List of table cells
        num_rows: Number of rows
        num_cols: Number of columns
        header_rows: Indices of header rows
        caption: Optional table caption
        method: Detection method used
        confidence: Detection confidence score (0-1)
    """

    bbox: BoundingBox
    cells: list[TableCell]
    num_rows: int
    num_cols: int
    header_rows: list[int]
    caption: str | None = None
    method: TableDetectionMethod = TableDetectionMethod.HYBRID
    confidence: float = 0.0


class LatticeTableDetector:
    """Detects tables with visible borders using line detection.

    This method is highly accurate for ruled tables but won't detect
    borderless tables.
    """

    def __init__(
        self,
        min_line_length: int = 50,
        line_confidence_threshold: float = 0.7,
        cell_min_size: tuple[int, int] = (10, 10),
    ):
        """Initialize lattice detector.

        Args:
            min_line_length: Minimum line length in pixels
            line_confidence_threshold: Hough transform confidence threshold
            cell_min_size: Minimum cell (width, height) in pixels
        """
        self.min_line_length = min_line_length
        self.line_confidence_threshold = line_confidence_threshold
        self.cell_min_size = cell_min_size

    def detect(self, page_image: Image.Image, scale_factor: float = 1.0) -> list[Table]:
        """Detect tables with visible borders in the page image.

        Args:
            page_image: PIL Image of the PDF page
            scale_factor: Ratio of PDF coordinates to image pixels

        Returns:
            List of detected tables
        """
        # Convert to grayscale and detect edges
        gray = page_image.convert("L")
        edges = self._detect_edges(gray)

        # Detect horizontal and vertical lines
        h_lines = self._detect_horizontal_lines(edges)
        v_lines = self._detect_vertical_lines(edges)

        # Find line intersections (cell corners)
        intersections = self._find_intersections(h_lines, v_lines)

        # Build table grids from intersections
        tables = self._construct_tables(intersections, scale_factor)

        return tables

    def _detect_edges(self, gray_image: Image.Image) -> np.ndarray:
        """Apply edge detection to find lines."""
        # Convert to numpy array
        img_array = np.array(gray_image)

        # Simple threshold-based edge detection
        # In production, could use Canny edge detection
        threshold = 200
        edges = (img_array < threshold).astype(np.uint8) * 255

        return edges

    def _detect_horizontal_lines(self, edges: np.ndarray) -> list[tuple[int, int]]:
        """Detect horizontal lines in edge image.

        Returns:
            List of (y_position, line_length) tuples
        """
        lines = []
        height, width = edges.shape

        # Scan each row
        for y in range(height):
            row = edges[y, :]
            # Find continuous sequences of edge pixels
            line_start = None
            for x in range(width):
                if row[x] > 0:
                    if line_start is None:
                        line_start = x
                else:
                    if line_start is not None:
                        line_length = x - line_start
                        if line_length >= self.min_line_length:
                            lines.append((y, line_length))
                        line_start = None

            # Check end of row
            if line_start is not None:
                line_length = width - line_start
                if line_length >= self.min_line_length:
                    lines.append((y, line_length))

        return lines

    def _detect_vertical_lines(self, edges: np.ndarray) -> list[tuple[int, int]]:
        """Detect vertical lines in edge image.

        Returns:
            List of (x_position, line_length) tuples
        """
        lines = []
        height, width = edges.shape

        # Scan each column
        for x in range(width):
            col = edges[:, x]
            # Find continuous sequences of edge pixels
            line_start = None
            for y in range(height):
                if col[y] > 0:
                    if line_start is None:
                        line_start = y
                else:
                    if line_start is not None:
                        line_length = y - line_start
                        if line_length >= self.min_line_length:
                            lines.append((x, line_length))
                        line_start = None

            # Check end of column
            if line_start is not None:
                line_length = height - line_start
                if line_length >= self.min_line_length:
                    lines.append((x, line_length))

        return lines

    def _find_intersections(
        self,
        h_lines: list[tuple[int, int]],
        v_lines: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Find intersection points between horizontal and vertical lines.

        Args:
            h_lines: Horizontal lines (y, length)
            v_lines: Vertical lines (x, length)

        Returns:
            List of (x, y) intersection points
        """
        intersections = []

        h_positions = [y for y, _ in h_lines]
        v_positions = [x for x, _ in v_lines]

        # Find all crossing points
        for x in v_positions:
            for y in h_positions:
                intersections.append((x, y))

        return intersections

    def _construct_tables(
        self, intersections: list[tuple[int, int]], scale_factor: float
    ) -> list[Table]:
        """Construct table structures from intersection points.

        Args:
            intersections: List of (x, y) intersection points
            scale_factor: Scale from image to PDF coordinates

        Returns:
            List of detected tables
        """
        if len(intersections) < 4:  # Need at least 2x2 grid
            return []

        # Sort intersections
        intersections = sorted(intersections, key=lambda p: (p[1], p[0]))

        # Group into rows
        rows = self._group_into_rows(intersections)

        if len(rows) < 2:
            return []

        # Build table cells
        cells = []
        for row_idx in range(len(rows) - 1):
            row = rows[row_idx]
            next_row = rows[row_idx + 1]

            for col_idx in range(len(row) - 1):
                x1, y1 = row[col_idx]
                x2 = row[col_idx + 1][0]
                y2 = next_row[0][1]

                # Scale coordinates
                x1_pdf = x1 * scale_factor
                y1_pdf = y1 * scale_factor
                x2_pdf = x2 * scale_factor
                y2_pdf = y2 * scale_factor

                width = x2_pdf - x1_pdf
                height = y2_pdf - y1_pdf

                # Check minimum cell size
                if width >= self.cell_min_size[0] and height >= self.cell_min_size[1]:
                    bbox = BoundingBox(x1_pdf, y1_pdf, width, height)
                    cell = TableCell(
                        bbox=bbox,
                        row=row_idx,
                        col=col_idx,
                    )
                    cells.append(cell)

        if not cells:
            return []

        # Create table from cells
        num_rows = max(c.row for c in cells) + 1
        num_cols = max(c.col for c in cells) + 1

        # Calculate overall bounding box
        all_x0 = [c.bbox.x0 for c in cells]
        all_y0 = [c.bbox.y0 for c in cells]
        all_x1 = [c.bbox.x1 for c in cells]
        all_y1 = [c.bbox.y1 for c in cells]

        min_x = min(all_x0)
        min_y = min(all_y0)
        max_x = max(all_x1)
        max_y = max(all_y1)

        table_bbox = BoundingBox(min_x, min_y, max_x - min_x, max_y - min_y)

        table = Table(
            bbox=table_bbox,
            cells=cells,
            num_rows=num_rows,
            num_cols=num_cols,
            header_rows=[0],  # Assume first row is header
            method=TableDetectionMethod.LATTICE,
            confidence=0.9,  # High confidence for line-based detection
        )

        return [table]

    def _group_into_rows(
        self, intersections: list[tuple[int, int]], tolerance: int = 5
    ) -> list[list[tuple[int, int]]]:
        """Group intersections into rows based on y-coordinate.

        Args:
            intersections: List of (x, y) points
            tolerance: Y-coordinate tolerance for grouping

        Returns:
            List of rows, each containing sorted points
        """
        if not intersections:
            return []

        rows = []
        current_row = [intersections[0]]
        current_y = intersections[0][1]

        for point in intersections[1:]:
            if abs(point[1] - current_y) <= tolerance:
                current_row.append(point)
            else:
                rows.append(sorted(current_row, key=lambda p: p[0]))
                current_row = [point]
                current_y = point[1]

        # Add last row
        if current_row:
            rows.append(sorted(current_row, key=lambda p: p[0]))

        return rows


class StreamTableDetector:
    """Detects borderless tables using text alignment patterns.

    This method works well for tables without visible borders by
    analyzing text positioning and alignment.
    """

    def __init__(
        self,
        alignment_tolerance: float = 10.0,
        min_rows: int = 2,
        min_cols: int = 2,
        min_silhouette_score: float = 0.5,
    ):
        """Initialize stream detector.

        Args:
            alignment_tolerance: Pixel tolerance for alignment
            min_rows: Minimum number of rows for a valid table
            min_cols: Minimum number of columns for a valid table
            min_silhouette_score: Minimum clustering quality score
        """
        self.alignment_tolerance = alignment_tolerance
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.min_silhouette_score = min_silhouette_score

    def detect(
        self, text_blocks: list[BoundingBox], page_bbox: BoundingBox
    ) -> list[Table]:
        """Detect tables from text block positions.

        Args:
            text_blocks: List of text block bounding boxes
            page_bbox: Overall page bounding box

        Returns:
            List of detected tables
        """
        if len(text_blocks) < self.min_rows * self.min_cols:
            return []

        # Cluster x-coordinates for columns
        x_positions = [block.x1 for block in text_blocks]
        x_clusters = self._cluster_coordinates(x_positions)

        # Cluster y-coordinates for rows
        y_positions = [block.y1 for block in text_blocks]
        y_clusters = self._cluster_coordinates(y_positions)

        if len(x_clusters) < self.min_cols or len(y_clusters) < self.min_rows:
            return []

        # Build grid structure
        table = self._build_table_from_clusters(text_blocks, x_clusters, y_clusters)

        return [table] if table else []

    def _cluster_coordinates(self, coordinates: list[float]) -> list[float]:
        """Cluster coordinate values to find column/row positions.

        Args:
            coordinates: List of x or y coordinates

        Returns:
            List of cluster centers (sorted)
        """
        if not coordinates:
            return []

        # Simple clustering: group coordinates within tolerance
        sorted_coords = sorted(coordinates)
        clusters = []
        current_cluster = [sorted_coords[0]]

        for coord in sorted_coords[1:]:
            if coord - current_cluster[-1] <= self.alignment_tolerance:
                current_cluster.append(coord)
            else:
                # Finish current cluster
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [coord]

        # Add last cluster
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))

        return clusters

    def _build_table_from_clusters(
        self,
        text_blocks: list[BoundingBox],
        x_clusters: list[float],
        y_clusters: list[float],
    ) -> Table | None:
        """Build table structure from clustered coordinates.

        Args:
            text_blocks: Text blocks to assign to cells
            x_clusters: Column x-positions
            y_clusters: Row y-positions

        Returns:
            Constructed table or None if invalid
        """
        cells = []

        # Assign each text block to a grid cell
        for block in text_blocks:
            # Find nearest column
            col = self._find_nearest_cluster(block.x1, x_clusters)
            if col is None:
                continue

            # Find nearest row
            row = self._find_nearest_cluster(block.y1, y_clusters)
            if row is None:
                continue

            # Create cell
            cell = TableCell(
                bbox=block,
                row=row,
                col=col,
                content="",  # Content would be extracted separately
            )
            cells.append(cell)

        if len(cells) < self.min_rows * self.min_cols:
            return None

        # Calculate table bounding box
        all_x0 = [c.bbox.x0 for c in cells]
        all_y0 = [c.bbox.y0 for c in cells]
        all_x1 = [c.bbox.x1 for c in cells]
        all_y1 = [c.bbox.y1 for c in cells]

        min_x = min(all_x0)
        min_y = min(all_y0)
        max_x = max(all_x1)
        max_y = max(all_y1)

        table_bbox = BoundingBox(min_x, min_y, max_x - min_x, max_y - min_y)

        table = Table(
            bbox=table_bbox,
            cells=cells,
            num_rows=len(y_clusters),
            num_cols=len(x_clusters),
            header_rows=[0],
            method=TableDetectionMethod.STREAM,
            confidence=0.75,  # Lower confidence than lattice
        )

        return table

    def _find_nearest_cluster(
        self, coordinate: float, clusters: list[float]
    ) -> int | None:
        """Find the nearest cluster index for a coordinate.

        Args:
            coordinate: Coordinate value
            clusters: List of cluster centers

        Returns:
            Cluster index or None if too far from all clusters
        """
        min_distance = float("inf")
        nearest_idx = None

        for idx, cluster_center in enumerate(clusters):
            distance = abs(coordinate - cluster_center)
            if distance < min_distance and distance <= self.alignment_tolerance:
                min_distance = distance
                nearest_idx = idx

        return nearest_idx


class HybridTableDetector:
    """Combines lattice and stream methods for robust detection.

    Uses lattice method first (high precision), falls back to stream
    method for borderless tables.
    """

    def __init__(self) -> None:
        """Initialize hybrid detector with sub-detectors."""
        self.lattice_detector = LatticeTableDetector()
        self.stream_detector = StreamTableDetector()

    def detect(
        self,
        page_image: Image.Image | None,
        text_blocks: list[BoundingBox],
        page_bbox: BoundingBox,
        scale_factor: float = 1.0,
    ) -> list[Table]:
        """Detect tables using multiple methods.

        Args:
            page_image: Optional page image for lattice detection
            text_blocks: Text blocks for stream detection
            page_bbox: Page bounding box
            scale_factor: Image to PDF coordinate scale

        Returns:
            List of detected tables with confidence scores
        """
        tables = []

        # Try lattice method first if image available
        if page_image is not None:
            lattice_tables = self.lattice_detector.detect(page_image, scale_factor)
            tables.extend(lattice_tables)

        # Try stream method for remaining regions
        stream_tables = self.stream_detector.detect(text_blocks, page_bbox)

        # Filter out stream tables that overlap with lattice tables
        for stream_table in stream_tables:
            overlaps = False
            for lattice_table in tables:
                if self._tables_overlap(stream_table, lattice_table):
                    overlaps = True
                    break

            if not overlaps:
                stream_table.method = TableDetectionMethod.HYBRID
                tables.append(stream_table)

        return tables

    def _tables_overlap(self, table1: Table, table2: Table) -> bool:
        """Check if two tables overlap significantly.

        Args:
            table1: First table
            table2: Second table

        Returns:
            True if tables overlap by >30%
        """
        return table1.bbox.overlap_percentage(table2.bbox) > 0.3
