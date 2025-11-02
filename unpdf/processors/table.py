"""Table detection and conversion processor for unpdf.

This module detects tables using pdfplumber's built-in table detection
and converts them to Markdown pipe tables.

Example:
    >>> from unpdf.processors.table import TableProcessor
    >>> processor = TableProcessor()
    >>> # Extract from PDF page
    >>> tables = processor.extract_tables(page)
    >>> for table_element in tables:
    ...     print(table_element.to_markdown())
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TableElement:
    r"""Represents a table element with rows and columns.

    Attributes:
        rows: List of rows, where each row is a list of cell values.
        has_header: Whether the first row should be treated as a header.
        bbox: Bounding box (x0, y0, x1, y1) of the table in the PDF.

    Example:
        >>> table = TableElement(
        ...     rows=[["Name", "Age"], ["Alice", "30"], ["Bob", "25"]],
        ...     has_header=True
        ... )
        >>> table.to_markdown()
        '| Name | Age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |'
    """

    rows: list[list[str]]
    has_header: bool = True
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)

    def to_markdown(self) -> str:
        """Convert table to Markdown pipe table format.

        Returns:
            Markdown-formatted table string.

        Example:
            >>> table = TableElement(rows=[["A", "B"], ["1", "2"]])
            >>> print(table.to_markdown())
            | A | B |
            |---|---|
            | 1 | 2 |
        """
        if not self.rows:
            return ""

        # Normalize: ensure all rows have same column count
        max_cols = max(len(row) for row in self.rows) if self.rows else 0
        normalized_rows = [row + [""] * (max_cols - len(row)) for row in self.rows]

        # Calculate column widths for alignment
        col_widths = [0] * max_cols
        for row in normalized_rows:
            for i, cell in enumerate(row):
                cell_text = str(cell) if cell is not None else ""
                col_widths[i] = max(col_widths[i], len(cell_text))

        # Ensure minimum width of 3 for separator
        col_widths = [max(3, w) for w in col_widths]

        lines = []

        # Header row (if applicable)
        if self.has_header and normalized_rows:
            header = normalized_rows[0]
            header_line = self._format_row(header, col_widths)
            lines.append(header_line)

            # Separator row
            separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
            lines.append(separator)

            # Data rows
            for row in normalized_rows[1:]:
                lines.append(self._format_row(row, col_widths))
        else:
            # No header - all rows are data
            for row in normalized_rows:
                lines.append(self._format_row(row, col_widths))

        return "\n".join(lines)

    def _format_row(self, row: list[str], col_widths: list[int]) -> str:
        """Format a single table row with proper padding.

        Args:
            row: List of cell values.
            col_widths: List of column widths for alignment.

        Returns:
            Formatted row string with pipe separators.

        Example:
            >>> table = TableElement(rows=[[]])
            >>> table._format_row(["A", "B"], [3, 5])
            '| A   | B     |'
        """
        cells = []
        for cell, width in zip(row, col_widths, strict=False):
            cell_text = str(cell) if cell is not None else ""
            # Left-align text, pad to width
            padded = cell_text.ljust(width)
            cells.append(f" {padded} ")

        return "|" + "|".join(cells) + "|"


class TableProcessor:
    """Processor for detecting and converting tables from PDFs.

    Uses pdfplumber's table detection to find tables in PDF pages
    and converts them to Markdown pipe table format.

    Attributes:
        table_settings: Configuration dict for pdfplumber table detection.

    Example:
        >>> processor = TableProcessor()
        >>> # Process a PDF page
        >>> import pdfplumber
        >>> pdf = pdfplumber.open("document.pdf")
        >>> page = pdf.pages[0]
        >>> tables = processor.extract_tables(page)
        >>> for table in tables:
        ...     print(table.to_markdown())
    """

    def __init__(
        self,
        table_settings: dict[str, Any] | None = None,
        min_words_in_table: int = 2,
    ) -> None:
        """Initialize table processor.

        Args:
            table_settings: Optional pdfplumber table settings override.
            min_words_in_table: Minimum words required to consider as table.

        Example:
            >>> processor = TableProcessor(
            ...     table_settings={"vertical_strategy": "lines"},
            ...     min_words_in_table=3
            ... )
        """
        # Default table detection settings
        self.table_settings = table_settings or {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "intersection_tolerance": 3,
            "min_words_vertical": 3,
        }
        self.min_words_in_table = min_words_in_table

        logger.debug(f"TableProcessor initialized with settings: {self.table_settings}")

    def extract_tables(self, page: Any) -> list[TableElement]:
        """Extract all tables from a PDF page.

        Args:
            page: A pdfplumber Page object.

        Returns:
            List of TableElement objects found on the page.

        Example:
            >>> import pdfplumber
            >>> pdf = pdfplumber.open("document.pdf")
            >>> processor = TableProcessor()
            >>> tables = processor.extract_tables(pdf.pages[0])
            >>> len(tables)
            2
        """
        try:
            # First try strict line-based detection
            tables = page.find_tables(table_settings=self.table_settings)

            if not tables:
                # Fallback: try text-based detection (for borderless tables)
                relaxed_settings = {
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                    "intersection_tolerance": 5,
                    "min_words_vertical": 2,
                }
                tables = page.find_tables(table_settings=relaxed_settings)
                logger.debug("Using relaxed (text-based) table detection")

            table_elements = []
            for table in tables:
                extracted = table.extract()

                # Filter out empty or too-small tables
                if not extracted or len(extracted) < 2:
                    continue

                # Check if table has enough content
                total_words = sum(
                    len(str(cell).split()) for row in extracted for cell in row if cell
                )
                if total_words < self.min_words_in_table:
                    logger.debug(f"Skipping small table with {total_words} words")
                    continue

                # Create TableElement
                # Clean cells: None -> empty string
                cleaned_rows = [
                    [str(cell).strip() if cell else "" for cell in row]
                    for row in extracted
                ]

                table_element = TableElement(
                    rows=cleaned_rows,
                    has_header=self._has_header(cleaned_rows),
                    bbox=table.bbox,
                )
                table_elements.append(table_element)

            logger.info(f"Extracted {len(table_elements)} tables from page")
            return table_elements

        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []

    def _has_header(self, rows: list[list[str]]) -> bool:
        """Heuristic to determine if first row is a header.

        Checks if the first row has distinct formatting characteristics
        compared to subsequent rows (e.g., all cells have content).

        Args:
            rows: Table rows to analyze.

        Returns:
            True if first row appears to be a header.

        Example:
            >>> processor = TableProcessor()
            >>> rows = [["Name", "Age"], ["Alice", "30"]]
            >>> processor._has_header(rows)
            True
            >>> rows = [["", ""], ["Alice", "30"]]
            >>> processor._has_header(rows)
            False
        """
        if not rows or len(rows) < 2:
            return True  # Default to treating first row as header

        first_row = rows[0]

        # Header heuristic: first row should have content in most cells
        non_empty_in_first = sum(1 for cell in first_row if cell.strip())
        # Return True if at least 50% of cells have content
        return non_empty_in_first >= len(first_row) * 0.5
