"""Extract and structure content from detected tables.

This module populates table cells with their text content by mapping
text blocks to cell boundaries, handling multi-line cells, and detecting
header rows.
"""

from dataclasses import dataclass

from unpdf.models.layout import BoundingBox
from unpdf.processors.table_detector import Table, TableCell


@dataclass
class TextBlock:
    """Represents a text block with content and position.

    Attributes:
        bbox: Bounding box of the text
        content: Text content
        font_size: Font size in points
        is_bold: Whether text is bold
    """

    bbox: BoundingBox
    content: str
    font_size: float = 12.0
    is_bold: bool = False


class TableContentExtractor:
    """Extracts text content and structure from detected tables.

    This class:
    - Maps text blocks to table cells
    - Concatenates multi-line cell content
    - Detects header rows based on formatting
    - Identifies spanning cells
    """

    def __init__(
        self,
        cell_overlap_threshold: float = 0.5,
        header_font_size_ratio: float = 1.1,
        merge_spacing_threshold: float = 2.0,
    ):
        """Initialize content extractor.

        Args:
            cell_overlap_threshold: Minimum overlap ratio to assign text to cell
            header_font_size_ratio: Header font size must be >= ratio × body font
            merge_spacing_threshold: Max spacing (in char widths) to merge text
        """
        self.cell_overlap_threshold = cell_overlap_threshold
        self.header_font_size_ratio = header_font_size_ratio
        self.merge_spacing_threshold = merge_spacing_threshold

    def extract_content(self, table: Table, text_blocks: list[TextBlock]) -> Table:
        """Extract text content for all cells in a table.

        Args:
            table: Detected table with empty cells
            text_blocks: All text blocks on the page

        Returns:
            Table with populated cell content
        """
        # Assign text blocks to cells
        for cell in table.cells:
            cell_text_blocks = self._find_cell_text(cell, text_blocks)
            cell.content = self._merge_text_blocks(cell_text_blocks)

        # Detect header rows based on formatting
        header_rows = self._detect_header_rows(table, text_blocks)
        table.header_rows = header_rows

        # Detect and mark spanning cells
        self._detect_spanning_cells(table)

        return table

    def _find_cell_text(
        self, cell: TableCell, text_blocks: list[TextBlock]
    ) -> list[TextBlock]:
        """Find all text blocks that belong to a cell.

        Args:
            cell: Table cell to populate
            text_blocks: Available text blocks

        Returns:
            List of text blocks within the cell, sorted top-to-bottom, left-to-right
        """
        cell_blocks = []

        for block in text_blocks:
            # Calculate overlap between cell and text block
            overlap_area = cell.bbox.intersection_area(block.bbox)
            block_area = block.bbox.area

            if block_area > 0:
                overlap_ratio = overlap_area / block_area
                if overlap_ratio >= self.cell_overlap_threshold:
                    cell_blocks.append(block)

        # Sort by position: top to bottom, then left to right
        cell_blocks.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))

        return cell_blocks

    def _merge_text_blocks(self, text_blocks: list[TextBlock]) -> str:
        """Merge multiple text blocks into single cell content.

        Handles:
        - Multi-line text (add newlines)
        - Inline text (add spaces)
        - Empty cells

        Args:
            text_blocks: Text blocks in the cell

        Returns:
            Merged text content
        """
        if not text_blocks:
            return ""

        if len(text_blocks) == 1:
            return text_blocks[0].content.strip()

        # Group blocks into lines based on vertical position
        lines = []
        current_line = [text_blocks[0]]
        current_y = text_blocks[0].bbox.y0

        for block in text_blocks[1:]:
            # Check if block is on the same line (within half font size)
            y_diff = abs(block.bbox.y0 - current_y)
            avg_height = (current_line[0].bbox.height + block.bbox.height) / 2

            if y_diff < avg_height * 0.5:
                # Same line
                current_line.append(block)
            else:
                # New line
                lines.append(self._merge_line(current_line))
                current_line = [block]
                current_y = block.bbox.y0

        # Add last line
        if current_line:
            lines.append(self._merge_line(current_line))

        return "\n".join(lines).strip()

    def _merge_line(self, line_blocks: list[TextBlock]) -> str:
        """Merge text blocks on the same line with appropriate spacing.

        Args:
            line_blocks: Text blocks on the same line

        Returns:
            Merged line text
        """
        if not line_blocks:
            return ""

        if len(line_blocks) == 1:
            return line_blocks[0].content.strip()

        # Sort left to right
        line_blocks.sort(key=lambda b: b.bbox.x0)

        result = [line_blocks[0].content.strip()]

        for i in range(1, len(line_blocks)):
            prev_block = line_blocks[i - 1]
            curr_block = line_blocks[i]

            # Calculate gap between blocks
            gap = curr_block.bbox.x0 - prev_block.bbox.x1

            # Estimate character width
            char_width = prev_block.bbox.width / max(len(prev_block.content), 1)

            # Add space if gap is significant
            if gap > char_width * self.merge_spacing_threshold:
                result.append(" ")

            result.append(curr_block.content.strip())

        return " ".join(result)

    def _detect_header_rows(
        self, table: Table, text_blocks: list[TextBlock]
    ) -> list[int]:
        """Detect header rows based on font formatting.

        Heuristics:
        - Bold text
        - Larger font size
        - Position (top rows more likely)

        Args:
            table: Table to analyze
            text_blocks: All text blocks for font analysis

        Returns:
            List of header row indices
        """
        if table.num_rows == 0:
            return []

        # Calculate median font size from all text blocks
        font_sizes = [b.font_size for b in text_blocks if b.font_size > 0]
        if not font_sizes:
            return [0]  # Default to first row

        median_font_size = sorted(font_sizes)[len(font_sizes) // 2]

        header_rows = []

        # Check each row
        for row_idx in range(min(3, table.num_rows)):  # Only check first 3 rows
            row_cells = [c for c in table.cells if c.row == row_idx]

            # Count formatting indicators
            bold_count = 0
            large_font_count = 0
            total_cells = len(row_cells)

            for cell in row_cells:
                # Find text blocks in this cell
                cell_blocks = [
                    b for b in text_blocks if cell.bbox.contains_point(b.bbox.center)
                ]

                for block in cell_blocks:
                    if block.is_bold:
                        bold_count += 1
                    if (
                        block.font_size
                        >= median_font_size * self.header_font_size_ratio
                    ):
                        large_font_count += 1

            # If majority of cells are bold or large, mark as header
            if total_cells > 0:
                bold_ratio = bold_count / total_cells
                large_ratio = large_font_count / total_cells

                if bold_ratio >= 0.5 or large_ratio >= 0.5:
                    header_rows.append(row_idx)

        # If no headers detected, default to first row
        if not header_rows:
            header_rows = [0]

        return header_rows

    def _detect_spanning_cells(self, table: Table) -> None:
        """Detect cells that span multiple rows or columns.

        Identifies empty cells that should be merged with neighbors.
        Updates row_span and col_span in-place.

        Args:
            table: Table to analyze
        """
        # Build grid of cells
        grid: dict[tuple[int, int], TableCell] = {}
        for cell in table.cells:
            grid[(cell.row, cell.col)] = cell

        # Track cells to remove
        cells_to_remove: list[TableCell] = []

        # Check for empty cells that indicate spanning
        for row in range(table.num_rows):
            for col in range(table.num_cols):
                maybe_cell = grid.get((row, col))
                if maybe_cell is None or maybe_cell.content.strip():
                    continue  # Skip non-empty cells or missing cells

                # We now know this cell exists and is empty
                empty_cell: TableCell = maybe_cell

                # Check if cell to the left has content and could span
                left_cell = grid.get((row, col - 1))
                if (
                    left_cell is not None
                    and left_cell.content.strip()
                    and self._cells_should_merge_horizontal(left_cell, empty_cell)
                ):
                    left_cell.col_span += 1
                    cells_to_remove.append(empty_cell)
                    continue

                # Check if cell above has content and could span
                above_cell = grid.get((row - 1, col))
                if (
                    above_cell is not None
                    and above_cell.content.strip()
                    and self._cells_should_merge_vertical(above_cell, empty_cell)
                ):
                    above_cell.row_span += 1
                    cells_to_remove.append(empty_cell)

        # Remove merged cells
        for cell in cells_to_remove:
            if cell in table.cells:
                table.cells.remove(cell)

    def _cells_should_merge_horizontal(
        self, left_cell: TableCell, right_cell: TableCell
    ) -> bool:
        """Check if two horizontally adjacent cells should merge.

        Args:
            left_cell: Cell on the left
            right_cell: Cell on the right (empty)

        Returns:
            True if cells should merge
        """
        # Simple heuristic: merge if right cell is empty and cells are aligned
        if right_cell.content.strip():
            return False

        # Check vertical alignment (same row)
        return abs(left_cell.bbox.y0 - right_cell.bbox.y0) < 2.0

    def _cells_should_merge_vertical(
        self, top_cell: TableCell, bottom_cell: TableCell
    ) -> bool:
        """Check if two vertically adjacent cells should merge.

        Args:
            top_cell: Cell on top
            bottom_cell: Cell below (empty)

        Returns:
            True if cells should merge
        """
        # Simple heuristic: merge if bottom cell is empty and cells are aligned
        if bottom_cell.content.strip():
            return False

        # Check horizontal alignment (same column)
        return abs(top_cell.bbox.x0 - bottom_cell.bbox.x0) < 2.0
