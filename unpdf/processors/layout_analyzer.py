"""Layout analysis for PDF to Markdown conversion.

This module implements geometric algorithms for detecting document structure,
including column detection, block segmentation, and reading order determination.
"""

from dataclasses import dataclass


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
    ):
        """Initialize the layout analyzer.

        Args:
            min_column_width_ratio: Minimum column width as ratio of page width
            column_gap_threshold: Minimum gap between columns as ratio of page width
            alignment_tolerance: Tolerance in pixels for alignment detection
        """
        self.min_column_width_ratio = min_column_width_ratio
        self.column_gap_threshold = column_gap_threshold
        self.alignment_tolerance = alignment_tolerance

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
