"""Layout analysis for PDF to Markdown conversion.

This module implements geometric algorithms for detecting document structure,
including column detection, block segmentation, and reading order determination.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class BoundingBox:
    """Represents a rectangular bounding box in PDF coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Get the width of the bounding box."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Get the height of the bounding box."""
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        """Get the x-coordinate of the center."""
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        """Get the y-coordinate of the center."""
        return (self.y0 + self.y1) / 2

    def overlaps_horizontally(self, other: "BoundingBox", tolerance: float = 0) -> bool:
        """Check if this box overlaps horizontally with another box."""
        return (self.x0 - tolerance) <= other.x1 and (self.x1 + tolerance) >= other.x0

    def overlaps_vertically(self, other: "BoundingBox", tolerance: float = 0) -> bool:
        """Check if this box overlaps vertically with another box."""
        return (self.y0 - tolerance) <= other.y1 and (self.y1 + tolerance) >= other.y0

    def contains(self, other: "BoundingBox") -> bool:
        """Check if this box contains another box."""
        return (
            self.x0 <= other.x0
            and self.y0 <= other.y0
            and self.x1 >= other.x1
            and self.y1 >= other.y1
        )


@dataclass
class TextBlock:
    """Represents a block of text with position and content."""

    bbox: BoundingBox
    text: str
    font_size: float = 12.0
    font_name: str = ""
    is_bold: bool = False
    is_italic: bool = False
    column_index: int | None = None
    reading_order: int | None = None


@dataclass
class Column:
    """Represents a column in a multi-column layout."""

    bbox: BoundingBox
    index: int
    blocks: list[TextBlock]


class LayoutAnalyzer:
    """Analyzes PDF layout to detect columns, blocks, and reading order."""

    def __init__(
        self,
        min_column_width_ratio: float = 0.3,
        column_gap_threshold: float = 0.05,
        alignment_tolerance: float = 10.0,
        method: Literal["whitespace", "xy_cut"] = "whitespace",
        xy_cut_tx_threshold: float = 0.5,
        xy_cut_ty_threshold: float = 1.5,
    ):
        """Initialize the layout analyzer.

        Args:
            min_column_width_ratio: Minimum column width as ratio of page width
            column_gap_threshold: Minimum gap between columns as ratio of page width
            alignment_tolerance: Tolerance in pixels for alignment detection
            method: Layout detection method ("whitespace" or "xy_cut")
            xy_cut_tx_threshold: Horizontal threshold for XY-Cut (multiple of char height)
            xy_cut_ty_threshold: Vertical threshold for XY-Cut (multiple of char width)
        """
        self.min_column_width_ratio = min_column_width_ratio
        self.column_gap_threshold = column_gap_threshold
        self.alignment_tolerance = alignment_tolerance
        self.method = method
        self.xy_cut_tx_threshold = xy_cut_tx_threshold
        self.xy_cut_ty_threshold = xy_cut_ty_threshold

    def detect_columns(
        self, blocks: list[TextBlock], page_width: float
    ) -> list[Column]:
        """Detect columns in a page based on whitespace analysis.

        Args:
            blocks: List of text blocks to analyze
            page_width: Width of the page

        Returns:
            List of detected columns
        """
        if not blocks:
            return []

        # Sort blocks by x-coordinate
        sorted_blocks = sorted(blocks, key=lambda b: b.bbox.x0)

        # Find vertical whitespace gaps
        gaps = self._find_vertical_gaps(sorted_blocks, page_width)

        if not gaps:
            # Single column layout
            column = Column(
                bbox=self._compute_column_bbox(blocks),
                index=0,
                blocks=blocks,
            )
            for block in blocks:
                block.column_index = 0
            return [column]

        # Multi-column layout - partition blocks by gaps
        columns = self._partition_blocks_by_gaps(sorted_blocks, gaps, page_width)

        # Assign column indices to blocks
        for col in columns:
            for block in col.blocks:
                block.column_index = col.index

        return columns

    def _find_vertical_gaps(
        self, sorted_blocks: list[TextBlock], page_width: float
    ) -> list[tuple[float, float]]:
        """Find significant vertical whitespace gaps between blocks.

        Args:
            sorted_blocks: Blocks sorted by x-coordinate
            page_width: Width of the page

        Returns:
            List of (start_x, end_x) tuples representing gaps
        """
        min_gap_width = page_width * self.column_gap_threshold
        gaps: list[tuple[float, float]] = []

        # Find all horizontal gaps between consecutive blocks
        for i in range(len(sorted_blocks) - 1):
            current_block = sorted_blocks[i]
            next_block = sorted_blocks[i + 1]

            # Calculate gap width
            gap_start = current_block.bbox.x1
            gap_end = next_block.bbox.x0
            gap_width = gap_end - gap_start

            if gap_width >= min_gap_width:
                # Merge with previous gap if they overlap
                if gaps and gaps[-1][1] >= gap_start - self.alignment_tolerance:
                    gaps[-1] = (gaps[-1][0], max(gaps[-1][1], gap_end))
                else:
                    gaps.append((gap_start, gap_end))

        return gaps

    def _partition_blocks_by_gaps(
        self,
        sorted_blocks: list[TextBlock],
        gaps: list[tuple[float, float]],
        page_width: float,
    ) -> list[Column]:
        """Partition blocks into columns based on detected gaps.

        Args:
            sorted_blocks: Blocks sorted by x-coordinate
            gaps: List of vertical gaps
            page_width: Width of the page

        Returns:
            List of columns
        """
        min_column_width = page_width * self.min_column_width_ratio

        # Group blocks by column
        columns_dict: dict[int, list[TextBlock]] = {}

        for block in sorted_blocks:
            # Determine which column this block belongs to
            block_column = self._determine_block_column(block, gaps)

            if block_column not in columns_dict:
                columns_dict[block_column] = []
            columns_dict[block_column].append(block)

        # Convert to Column objects
        columns = []
        for col_idx in sorted(columns_dict.keys()):
            col_blocks = columns_dict[col_idx]
            column_bbox = self._compute_column_bbox(col_blocks)

            if column_bbox.width >= min_column_width:
                columns.append(
                    Column(
                        bbox=column_bbox,
                        index=col_idx,
                        blocks=col_blocks,
                    )
                )

        return columns

    def _determine_block_column(
        self, block: TextBlock, gaps: list[tuple[float, float]]
    ) -> int:
        """Determine which column a block belongs to based on gaps.

        Args:
            block: Block to classify
            gaps: List of vertical gaps

        Returns:
            Column index (0-based)
        """
        block_center = block.bbox.center_x
        column = 0

        for _gap_start, gap_end in gaps:
            if block_center > gap_end:
                column += 1
            else:
                break

        return column

    def _compute_column_bbox(self, blocks: list[TextBlock]) -> BoundingBox:
        """Compute the bounding box for a column from its blocks.

        Args:
            blocks: List of blocks in the column

        Returns:
            Bounding box encompassing all blocks
        """
        if not blocks:
            return BoundingBox(0, 0, 0, 0)

        x0 = min(b.bbox.x0 for b in blocks)
        y0 = min(b.bbox.y0 for b in blocks)
        x1 = max(b.bbox.x1 for b in blocks)
        y1 = max(b.bbox.y1 for b in blocks)

        return BoundingBox(x0, y0, x1, y1)

    def determine_reading_order(self, columns: list[Column]) -> list[TextBlock]:
        """Determine reading order for blocks across columns.

        Args:
            columns: List of detected columns

        Returns:
            List of blocks in reading order
        """
        # Sort columns left-to-right
        sorted_columns = sorted(columns, key=lambda c: c.bbox.x0)

        # For single column, sort top-to-bottom
        if len(sorted_columns) == 1:
            blocks = sorted(sorted_columns[0].blocks, key=lambda b: -b.bbox.y1)
            for i, block in enumerate(blocks):
                block.reading_order = i
            return blocks

        # For multiple columns, use balanced reading order
        # Process blocks from top to bottom, alternating between columns
        all_blocks = []
        for col in sorted_columns:
            all_blocks.extend(col.blocks)

        # Sort by y-coordinate (top to bottom)
        sorted_by_y = sorted(all_blocks, key=lambda b: -b.bbox.y1)

        # Assign reading order
        for i, block in enumerate(sorted_by_y):
            block.reading_order = i

        return sorted_by_y

    def xy_cut_segmentation(
        self, blocks: list[TextBlock], page_width: float, page_height: float
    ) -> list[list[TextBlock]]:
        """Segment blocks using Recursive XY-Cut algorithm.

        Args:
            blocks: List of text blocks to segment
            page_width: Width of the page
            page_height: Height of the page

        Returns:
            List of block groups (segments)
        """
        if not blocks:
            return []

        # Estimate average character dimensions from blocks
        avg_char_height = self._estimate_avg_char_height(blocks)
        avg_char_width = self._estimate_avg_char_width(blocks)

        # Set thresholds based on character dimensions
        tx_threshold = self.xy_cut_tx_threshold * avg_char_height
        ty_threshold = self.xy_cut_ty_threshold * avg_char_width

        # Recursive segmentation
        segments = self._xy_cut_recursive(
            blocks, 0, page_width, 0, page_height, tx_threshold, ty_threshold
        )

        return segments

    def _estimate_avg_char_height(self, blocks: list[TextBlock]) -> float:
        """Estimate average character height from blocks."""
        heights = [b.bbox.height for b in blocks if b.bbox.height > 0]
        return sum(heights) / len(heights) if heights else 12.0

    def _estimate_avg_char_width(self, blocks: list[TextBlock]) -> float:
        """Estimate average character width from blocks."""
        widths = []
        for b in blocks:
            if b.text and b.bbox.width > 0:
                char_width = b.bbox.width / len(b.text)
                widths.append(char_width)
        return sum(widths) / len(widths) if widths else 6.0

    def _xy_cut_recursive(
        self,
        blocks: list[TextBlock],
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        tx_threshold: float,
        ty_threshold: float,
    ) -> list[list[TextBlock]]:
        """Recursively segment blocks using XY-Cut algorithm.

        Args:
            blocks: Blocks to segment
            x_min: Minimum x-coordinate of current region
            x_max: Maximum x-coordinate of current region
            y_min: Minimum y-coordinate of current region
            y_max: Maximum y-coordinate of current region
            tx_threshold: Horizontal valley threshold
            ty_threshold: Vertical valley threshold

        Returns:
            List of block segments
        """
        if not blocks:
            return []

        if len(blocks) == 1:
            return [blocks]

        # Filter blocks within the current region
        region_blocks = [
            b
            for b in blocks
            if b.bbox.x0 >= x_min - 1
            and b.bbox.x1 <= x_max + 1
            and b.bbox.y0 >= y_min - 1
            and b.bbox.y1 <= y_max + 1
        ]

        if not region_blocks:
            return []

        # Compute projection profiles
        h_profile = self._compute_horizontal_profile(region_blocks, x_min, x_max)
        v_profile = self._compute_vertical_profile(region_blocks, y_min, y_max)

        # Find valleys
        h_valleys = self._find_valleys(h_profile, ty_threshold)
        v_valleys = self._find_valleys(v_profile, tx_threshold)

        # Choose cut direction (alternate: horizontal first)
        if h_valleys:
            # Find widest horizontal valley
            widest_valley = max(h_valleys, key=lambda v: v[1] - v[0])
            cut_x = (widest_valley[0] + widest_valley[1]) / 2

            # Split blocks into left and right
            left_blocks = [b for b in region_blocks if b.bbox.center_x < cut_x]
            right_blocks = [b for b in region_blocks if b.bbox.center_x >= cut_x]

            # Recurse
            left_segments = self._xy_cut_recursive(
                left_blocks, x_min, cut_x, y_min, y_max, tx_threshold, ty_threshold
            )
            right_segments = self._xy_cut_recursive(
                right_blocks, cut_x, x_max, y_min, y_max, tx_threshold, ty_threshold
            )

            return left_segments + right_segments

        elif v_valleys:
            # Find widest vertical valley
            widest_valley = max(v_valleys, key=lambda v: v[1] - v[0])
            cut_y = (widest_valley[0] + widest_valley[1]) / 2

            # Split blocks into top and bottom
            top_blocks = [b for b in region_blocks if b.bbox.center_y > cut_y]
            bottom_blocks = [b for b in region_blocks if b.bbox.center_y <= cut_y]

            # Recurse
            top_segments = self._xy_cut_recursive(
                top_blocks, x_min, x_max, cut_y, y_max, tx_threshold, ty_threshold
            )
            bottom_segments = self._xy_cut_recursive(
                bottom_blocks, x_min, x_max, y_min, cut_y, tx_threshold, ty_threshold
            )

            return top_segments + bottom_segments

        else:
            # No more valleys, return as single segment
            return [region_blocks]

    def _compute_horizontal_profile(
        self, blocks: list[TextBlock], x_min: float, x_max: float
    ) -> dict[float, int]:
        """Compute horizontal projection profile (count of blocks at each x position).

        Args:
            blocks: Blocks to analyze
            x_min: Minimum x-coordinate of region
            x_max: Maximum x-coordinate of region

        Returns:
            Dictionary mapping x-coordinate to block count
        """
        # Initialize profile with all positions as 0
        profile: dict[float, int] = {
            float(x): 0 for x in range(int(x_min), int(x_max) + 1)
        }

        for b in blocks:
            x_start = int(max(b.bbox.x0, x_min))
            x_end = int(min(b.bbox.x1, x_max))

            for x in range(x_start, x_end + 1):
                profile[float(x)] = profile.get(float(x), 0) + 1

        return profile

    def _compute_vertical_profile(
        self, blocks: list[TextBlock], y_min: float, y_max: float
    ) -> dict[float, int]:
        """Compute vertical projection profile (count of blocks at each y position).

        Args:
            blocks: Blocks to analyze
            y_min: Minimum y-coordinate of region
            y_max: Maximum y-coordinate of region

        Returns:
            Dictionary mapping y-coordinate to block count
        """
        # Initialize profile with all positions as 0
        profile: dict[float, int] = {
            float(y): 0 for y in range(int(y_min), int(y_max) + 1)
        }

        for b in blocks:
            y_start = int(max(b.bbox.y0, y_min))
            y_end = int(min(b.bbox.y1, y_max))

            for y in range(y_start, y_end + 1):
                profile[float(y)] = profile.get(float(y), 0) + 1

        return profile

    def _find_valleys(
        self, profile: dict[float, int], threshold: float
    ) -> list[tuple[float, float]]:
        """Find valleys (gaps) in projection profile.

        Args:
            profile: Projection profile
            threshold: Minimum valley width

        Returns:
            List of (start, end) tuples for each valley
        """
        if not profile:
            return []

        valleys: list[tuple[float, float]] = []
        sorted_coords = sorted(profile.keys())

        valley_start: float | None = None

        for i, coord in enumerate(sorted_coords):
            if profile[coord] == 0:
                # Start or continue valley
                if valley_start is None:
                    valley_start = coord
            else:
                # End valley
                if valley_start is not None:
                    valley_end = sorted_coords[i - 1] if i > 0 else valley_start
                    valley_width = valley_end - valley_start

                    if valley_width >= threshold:
                        valleys.append((valley_start, valley_end))

                    valley_start = None

        # Check if we ended in a valley
        if valley_start is not None:
            valley_end = sorted_coords[-1]
            valley_width = valley_end - valley_start

            if valley_width >= threshold:
                valleys.append((valley_start, valley_end))

        return valleys


def analyze_page_layout(
    blocks: list[TextBlock], page_width: float, page_height: float
) -> tuple[list[Column], list[TextBlock]]:
    """Analyze page layout and determine reading order.

    Args:
        blocks: List of text blocks to analyze
        page_width: Width of the page
        page_height: Height of the page

    Returns:
        Tuple of (columns, ordered_blocks)
    """
    analyzer = LayoutAnalyzer()
    columns = analyzer.detect_columns(blocks, page_width)
    ordered_blocks = analyzer.determine_reading_order(columns)
    return columns, ordered_blocks
