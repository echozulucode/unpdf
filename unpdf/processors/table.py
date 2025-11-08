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
        y0: Vertical position for ordering. Defaults to bbox[1].
        page_number: Page number where table appears. Defaults to 1.

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
    y0: float = 0.0
    page_number: int = 1

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
        max_table_width_ratio: float = 0.85,
        min_columns: int = 2,
        min_rows: int = 3,
    ) -> None:
        """Initialize table processor.

        Args:
            table_settings: Optional pdfplumber table settings override.
            min_words_in_table: Minimum words required to consider as table. Default: 2.
            max_table_width_ratio: Maximum width ratio (table_width/page_width) to avoid
                detecting full-page content as a table. Default: 0.85 (85% of page).
            min_columns: Minimum number of columns for a valid table. Default: 2.
            min_rows: Minimum number of rows for a valid table. Default: 3.

        Example:
            >>> processor = TableProcessor(
            ...     table_settings={"vertical_strategy": "lines"},
            ...     min_words_in_table=6
            ... )
        """
        # Default table detection settings - only use line-based detection
        # to avoid phantom tables from text-based detection
        self.table_settings = table_settings or {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_tolerance": 3,
            "min_words_vertical": 3,
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 10,
        }
        self.min_words_in_table = min_words_in_table
        self.max_table_width_ratio = max_table_width_ratio
        self.min_columns = min_columns
        self.min_rows = min_rows

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
            # Try line-based detection first (for bordered tables)
            tables = page.find_tables(table_settings=self.table_settings)
            
            # If no tables found, try confidence-based text detection
            # for borderless tables (e.g., LaTeX/Pandoc PDFs)
            if not tables:
                logger.debug("No line-based tables found, trying text-based detection")
                tables = self._detect_text_tables_with_confidence(page)

            page_width = page.width
            table_elements = []

            for table in tables:
                extracted = table.extract()

                # Check minimum row requirement
                if not extracted or len(extracted) < self.min_rows:
                    logger.debug(f"Skipping table: only {len(extracted) if extracted else 0} row(s), need {self.min_rows}")
                    continue

                # Check column count
                max_cols = max(len(row) for row in extracted)
                if max_cols < self.min_columns:
                    logger.debug(f"Skipping table: only {max_cols} column(s)")
                    continue

                # Filter out full-page tables (likely false positives)
                table_width = table.bbox[2] - table.bbox[0]
                width_ratio = table_width / page_width
                if width_ratio > self.max_table_width_ratio:
                    logger.debug(
                        f"Skipping table: too wide ({width_ratio:.2%} of page width)"
                    )
                    continue

                # Check if table has enough content
                total_words = sum(
                    len(str(cell).split()) for row in extracted for cell in row if cell
                )
                if total_words < self.min_words_in_table:
                    logger.debug(f"Skipping table: only {total_words} word(s)")
                    continue

                # Clean cells: None -> empty string, strip whitespace
                cleaned_rows = [
                    [str(cell).strip() if cell else "" for cell in row]
                    for row in extracted
                ]

                # Filter out tables with all empty cells (except header)
                non_empty_cells = sum(
                    1
                    for row in cleaned_rows[1:]
                    for cell in row
                    if cell and len(cell.strip()) > 0
                )
                if non_empty_cells == 0:
                    logger.debug("Skipping table: no content in data rows")
                    continue

                # Filter out tables with too many empty cells (likely false positives)
                total_cells = sum(len(row) for row in cleaned_rows)
                empty_cell_ratio = (
                    1.0 - (non_empty_cells / total_cells) if total_cells > 0 else 1.0
                )
                if empty_cell_ratio > 0.6:  # More than 60% empty cells
                    logger.debug(
                        f"Skipping table: too many empty cells ({empty_cell_ratio:.1%})"
                    )
                    continue

                # Filter out tables where cells are too short (likely broken text)
                avg_cell_length = sum(
                    len(cell) for row in cleaned_rows for cell in row if cell
                ) / max(non_empty_cells, 1)
                if avg_cell_length < 2:  # Average cell has less than 2 characters
                    logger.debug(
                        f"Skipping table: cells too short (avg {avg_cell_length:.1f} chars)"
                    )
                    continue

                table_element = TableElement(
                    rows=cleaned_rows,
                    has_header=self._has_header(cleaned_rows),
                    bbox=table.bbox,
                )
                table_elements.append(table_element)

            logger.info(f"Extracted {len(table_elements)} table(s) from page")
            return table_elements

        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []

    def _detect_text_tables_with_confidence(self, page: Any, min_confidence: float = 0.70) -> list[Any]:
        """Detect borderless tables using text alignment analysis with confidence scoring.
        
        This method analyzes word positions to find aligned text that forms table-like
        structures without visible borders. It's used for PDFs generated by LaTeX/Pandoc
        where tables don't have drawn lines.
        
        Args:
            page: A pdfplumber Page object.
            min_confidence: Minimum confidence score (0-1) to accept a table. Default: 0.70.
            
        Returns:
            List of pdfplumber table objects (or simulated objects) for detected tables.
        """
        words = page.extract_words()
        if not words:
            return []
        
        # Group words by y-position (rows) with tolerance
        y_tolerance = 3  # pixels
        rows_dict = {}
        
        for word in words:
            y_key = round(word['top'] / y_tolerance) * y_tolerance
            if y_key not in rows_dict:
                rows_dict[y_key] = []
            rows_dict[y_key].append(word)
        
        # Sort rows by y-position and convert to list
        sorted_rows = sorted(rows_dict.items(), key=lambda x: x[0])
        
        # Find table candidates by looking for groups of rows with similar structure
        table_candidates = []
        i = 0
        
        while i < len(sorted_rows):
            # Try to build a table starting from this row
            candidate = self._build_table_candidate(sorted_rows, i)
            
            if candidate and len(candidate) >= self.min_rows:
                # Calculate confidence
                confidence = self._calculate_table_confidence_v2(candidate, page)
                
                if confidence >= min_confidence:
                    logger.debug(f"Text-based table candidate: {len(candidate)} rows, confidence {confidence:.2f}")
                    table_candidates.append(candidate)
                    i += len(candidate)  # Skip past this table
                    continue
            
            i += 1
        
        # Convert candidates to table objects
        detected_tables = []
        
        for candidate in table_candidates:
            # Extract table data
            table_data = self._extract_table_from_candidate_v2(candidate)
            
            # Calculate bounding box
            all_words = [w for row_data in candidate for w in row_data['words']]
            if not all_words:
                continue
                
            x0 = min(w['x0'] for w in all_words)
            y0 = min(w['top'] for w in all_words)
            x1 = max(w['x1'] for w in all_words)
            y1 = max(w['bottom'] for w in all_words)
            
            # Create mock table object
            class MockTable:
                def __init__(self, data, bbox):
                    self.data = data
                    self.bbox = bbox
                
                def extract(self):
                    return self.data
            
            detected_tables.append(MockTable(table_data, (x0, y0, x1, y1)))
        
        logger.info(f"Extracted {len(detected_tables)} text-based table(s) from page")
        return detected_tables
    
    def _build_table_candidate(self, sorted_rows: list[tuple], start_idx: int) -> list[dict] | None:
        """Build a table candidate starting from a given row.
        
        Args:
            sorted_rows: List of (y, words) tuples sorted by y.
            start_idx: Index to start building from.
            
        Returns:
            List of row dictionaries with structure info, or None if not a table.
        """
        if start_idx >= len(sorted_rows):
            return None
        
        candidate_rows = []
        y_start, words_start = sorted_rows[start_idx]
        
        # Analyze first row to detect column structure
        words_sorted = sorted(words_start, key=lambda w: w['x0'])
        columns = self._detect_column_positions(words_sorted)
        
        if len(columns) < 2:
            return None  # Need at least 2 columns for a table
        
        # Add first row
        candidate_rows.append({
            'y': y_start,
            'words': words_start,
            'columns': columns
        })
        
        # Try to add consecutive rows with same column structure
        for i in range(start_idx + 1, len(sorted_rows)):
            y, words = sorted_rows[i]
            
            # Check if row spacing is reasonable
            last_y = candidate_rows[-1]['y']
            row_spacing = y - last_y
            
            if row_spacing > 30:  # Too far apart
                break
            
            # Check if this row has similar column structure
            words_sorted = sorted(words, key=lambda w: w['x0'])
            row_columns = self._detect_column_positions(words_sorted)
            
            if self._columns_match(columns, row_columns):
                candidate_rows.append({
                    'y': y,
                    'words': words,
                    'columns': row_columns
                })
                columns = row_columns  # Update expected columns
            else:
                # Different structure, end table
                break
        
        return candidate_rows if len(candidate_rows) >= self.min_rows else None
    
    def _detect_column_positions(self, words_sorted: list[dict]) -> list[float]:
        """Detect column x-positions from sorted words.
        
        Uses gap-based detection: significant gaps indicate column boundaries.
        
        Args:
            words_sorted: Words sorted by x0.
            
        Returns:
            List of column start x-positions.
        """
        if not words_sorted:
            return []
        
        columns = [words_sorted[0]['x0']]
        min_gap = 10  # Minimum gap to consider as column boundary
        
        for word in words_sorted[1:]:
            # Check gap from previous word
            prev_word_end = words_sorted[words_sorted.index(word) - 1]['x1']
            gap = word['x0'] - prev_word_end
            
            if gap >= min_gap:
                # New column
                columns.append(word['x0'])
        
        return columns
    
    def _columns_match(self, cols1: list[float], cols2: list[float], tolerance: float = 15.0) -> bool:
        """Check if two column structures match.
        
        Args:
            cols1: First column x-positions.
            cols2: Second column x-positions.
            tolerance: Maximum difference in pixels.
            
        Returns:
            True if columns match within tolerance.
        """
        if len(cols1) != len(cols2):
            return False
        
        for c1, c2 in zip(cols1, cols2, strict=False):
            if abs(c1 - c2) > tolerance:
                return False
        
        return True
    
    def _calculate_table_confidence_v2(self, candidate_rows: list[dict], page: Any) -> float:
        """Calculate confidence score for a table candidate.
        
        Args:
            candidate_rows: List of row dictionaries.
            page: pdfplumber Page object.
            
        Returns:
            Confidence score from 0.0 to 1.0.
        """
        if not candidate_rows:
            return 0.0
        
        confidence = 0.0
        
        # Factor 1: All rows have same column count (0-0.3)
        column_counts = [len(row['columns']) for row in candidate_rows]
        if len(set(column_counts)) == 1:
            confidence += 0.3
        else:
            return 0.0  # Inconsistent columns
        
        num_cols = column_counts[0]
        
        # Factor 2: At least 2 columns (required)
        if num_cols < 2:
            return 0.0
        
        # Factor 3: Column alignment (0-0.4)
        # Check how well columns align across rows
        max_variance = 0.0
        for col_idx in range(num_cols):
            col_x_values = [row['columns'][col_idx] for row in candidate_rows]
            variance = max(col_x_values) - min(col_x_values)
            max_variance = max(max_variance, variance)
        
        if max_variance < 3:
            confidence += 0.4
        elif max_variance < 8:
            confidence += 0.3
        elif max_variance < 15:
            confidence += 0.2
        else:
            return 0.0  # Poor alignment
        
        # Factor 4: Sufficient rows (0-0.2)
        num_rows = len(candidate_rows)
        if num_rows >= 4:
            confidence += 0.2
        elif num_rows >= 3:
            confidence += 0.1
        
        # Factor 5: Sufficient columns (0-0.1)
        if num_cols >= 3:
            confidence += 0.1
        
        # Factor 6: Reject list markers (check first column)
        list_marker_count = 0
        for row in candidate_rows:
            # Get words in first column (approximately)
            first_col_x = row['columns'][0]
            tolerance = 15
            first_col_words = [w for w in row['words'] if abs(w['x0'] - first_col_x) < tolerance]
            
            if first_col_words:
                text = ' '.join(w['text'] for w in first_col_words).strip()
                if text in ['•', '-', '*', '◦', '▪', '–', '—'] or \
                   (len(text) <= 3 and text.endswith('.') and text[:-1].isdigit()):
                    list_marker_count += 1
        
        if list_marker_count > len(candidate_rows) * 0.5:
            return 0.0  # Likely a list
        
        return min(confidence, 1.0)
    
    def _extract_table_from_candidate_v2(self, candidate_rows: list[dict]) -> list[list[str]]:
        """Extract table data from candidate rows.
        
        Args:
            candidate_rows: List of row dictionaries.
            
        Returns:
            List of rows, where each row is a list of cell strings.
        """
        table_data = []
        
        for row in candidate_rows:
            columns = row['columns']
            words = sorted(row['words'], key=lambda w: w['x0'])
            
            # Assign words to columns
            cells = [[] for _ in columns]
            
            for word in words:
                # Find nearest column
                distances = [abs(word['x0'] - col_x) for col_x in columns]
                col_idx = distances.index(min(distances))
                cells[col_idx].append(word['text'])
            
            # Join words in each cell
            row_data = [' '.join(cell_words) for cell_words in cells]
            table_data.append(row_data)
        
        return table_data
        """Detect borderless tables using text alignment analysis with confidence scoring.
        
        This method analyzes word positions to find aligned text that forms table-like
        structures without visible borders. It's used for PDFs generated by LaTeX/Pandoc
        where tables don't have drawn lines.
        
        Args:
            page: A pdfplumber Page object.
            min_confidence: Minimum confidence score (0-1) to accept a table. Default: 0.75.
            
        Returns:
            List of pdfplumber table objects (or simulated objects) for detected tables.
        """
        words = page.extract_words()
        if not words:
            return []
        
        # Group words by y-position (rows)
        y_tolerance = 5  # pixels
        rows_dict = {}
        
        for word in words:
            y = round(word['top'] / y_tolerance) * y_tolerance
            if y not in rows_dict:
                rows_dict[y] = []
            rows_dict[y].append(word)
        
        # Sort rows by y-position
        sorted_rows = sorted(rows_dict.items(), key=lambda x: x[0])
        
        # Find potential table regions by detecting column patterns
        table_candidates = []
        current_table_rows = []
        current_column_positions = None
        
        for i, (y, row_words) in enumerate(sorted_rows):
            # Sort words in row by x-position
            row_words_sorted = sorted(row_words, key=lambda w: w['x0'])
            
            # Detect column structure by finding consistent x-position clusters
            column_groups = self._group_words_into_columns(row_words_sorted, current_column_positions)
            
            if not current_table_rows:
                # Start new potential table
                current_table_rows.append((y, column_groups, row_words_sorted))
                current_column_positions = [min(w['x0'] for w in group) for group in column_groups]
            else:
                # Check if this row aligns with previous rows
                last_y, last_column_groups, _ = current_table_rows[-1]
                
                # Check row spacing (should be consistent)
                row_spacing = y - last_y
                if row_spacing > 30:  # Too far apart, start new table
                    if len(current_table_rows) >= self.min_rows:
                        table_candidates.append(current_table_rows)
                    current_table_rows = [(y, column_groups, row_words_sorted)]
                    current_column_positions = [min(w['x0'] for w in group) for group in column_groups]
                    continue
                
                # Check column alignment
                if len(column_groups) == len(last_column_groups):
                    # Same column count - check alignment
                    aligned = True
                    for col_idx in range(len(column_groups)):
                        curr_x = min(w['x0'] for w in column_groups[col_idx])
                        last_x = min(w['x0'] for w in last_column_groups[col_idx])
                        if abs(curr_x - last_x) > 15:  # Columns must align within 15 pixels
                            aligned = False
                            break
                    
                    if aligned:
                        current_table_rows.append((y, column_groups, row_words_sorted))
                    else:
                        # Not aligned, end current table
                        if len(current_table_rows) >= self.min_rows:
                            table_candidates.append(current_table_rows)
                        current_table_rows = [(y, column_groups, row_words_sorted)]
                        current_column_positions = [min(w['x0'] for w in group) for group in column_groups]
                else:
                    # Different column count, end current table
                    if len(current_table_rows) >= self.min_rows:
                        table_candidates.append(current_table_rows)
                    current_table_rows = [(y, column_groups, row_words_sorted)]
                    current_column_positions = [min(w['x0'] for w in group) for group in column_groups]
        
        # Don't forget the last table
        if len(current_table_rows) >= self.min_rows:
            table_candidates.append(current_table_rows)
        
        # Score each candidate and create table objects
        detected_tables = []
        
        for candidate in table_candidates:
            confidence = self._calculate_table_confidence(candidate, page)
            
            if confidence >= min_confidence:
                logger.debug(f"Text-based table detected with confidence {confidence:.2f}")
                
                # Create a simulated table object with extract() method
                table_data = self._extract_table_from_candidate(candidate)
                
                # Calculate bounding box
                all_words = [w for _, _, row_words in candidate for w in row_words]
                x0 = min(w['x0'] for w in all_words)
                y0 = min(w['top'] for w in all_words)
                x1 = max(w['x1'] for w in all_words)
                y1 = max(w['bottom'] for w in all_words)
                
                # Create mock table object
                class MockTable:
                    def __init__(self, data, bbox):
                        self.data = data
                        self.bbox = bbox
                    
                    def extract(self):
                        return self.data
                
                detected_tables.append(MockTable(table_data, (x0, y0, x1, y1)))
        
        return detected_tables
    
    def _group_words_into_columns(self, words: list[dict], expected_columns: list[float] | None = None) -> list[list[dict]]:
        """Group words into columns based on x-positions.
        
        Args:
            words: List of word dictionaries sorted by x-position.
            expected_columns: Optional list of expected column x-positions.
            
        Returns:
            List of column groups, where each group is a list of words.
        """
        if not words:
            return []
        
        if expected_columns:
            # Match words to expected columns
            tolerance = 30  # pixels - increased tolerance
            column_groups = [[] for _ in expected_columns]
            
            for word in words:
                # Find nearest column
                distances = [abs(word['x0'] - col_x) for col_x in expected_columns]
                min_dist = min(distances)
                if min_dist <= tolerance:
                    col_idx = distances.index(min_dist)
                    column_groups[col_idx].append(word)
                else:
                    # Word doesn't fit any column - add to nearest anyway
                    col_idx = distances.index(min_dist)
                    column_groups[col_idx].append(word)
            
            # Filter out empty column groups - shouldn't happen now
            return [g for g in column_groups if g]
        else:
            # Auto-detect columns by clustering x-positions  
            # Use a gap-based approach: significant x-gap means new column
            if not words:
                return []
            
            column_groups = [[words[0]]]  # Start with first word in first column
            min_gap = 15  # minimum gap between columns in pixels
            
            for word in words[1:]:
                # Get the rightmost edge of the last word in the last column
                last_column = column_groups[-1]
                last_word_right = max(w['x1'] for w in last_column)
                
                # If there's a significant gap, start new column
                if word['x0'] - last_word_right >= min_gap:
                    column_groups.append([word])
                else:
                    # Add to current column
                    last_column.append(word)
            
            return column_groups
    
    def _calculate_table_confidence(self, candidate_rows: list[tuple], page: Any) -> float:
        """Calculate confidence score for a potential table.
        
        Args:
            candidate_rows: List of (y, column_groups, words) tuples.
            page: pdfplumber Page object.
            
        Returns:
            Confidence score from 0.0 to 1.0.
        """
        if not candidate_rows:
            return 0.0
        
        confidence = 0.0
        
        # Factor 1: Consistent column count (0-0.3)
        column_counts = [len(column_groups) for _, column_groups, _ in candidate_rows]
        if len(set(column_counts)) == 1:  # All rows have same column count
            confidence += 0.3
        elif len(set(column_counts)) <= 2:  # At most 2 different column counts
            confidence += 0.1
        else:
            # Too many different column counts - likely not a table
            return 0.0
        
        # Factor 2: Must have at least 2 columns (reject single-column lists)
        min_columns = min(column_counts)
        if min_columns < 2:
            return 0.0  # Single column is not a table
        
        # Factor 3: Column alignment quality (0-0.3)
        if len(candidate_rows) > 1:
            # Check alignment variance across rows
            max_variance = 0
            num_cols = min(column_counts)
            
            for col_idx in range(num_cols):
                col_x_positions = []
                for _, column_groups, _ in candidate_rows:
                    if col_idx < len(column_groups) and column_groups[col_idx]:
                        # Get minimum x position of words in this column
                        col_x = min(w['x0'] for w in column_groups[col_idx])
                        col_x_positions.append(col_x)
                
                if len(col_x_positions) > 1:
                    variance = max(col_x_positions) - min(col_x_positions)
                    max_variance = max(max_variance, variance)
            
            # Lower variance = better alignment
            if max_variance < 5:
                confidence += 0.3
            elif max_variance < 10:
                confidence += 0.2
            elif max_variance < 20:
                confidence += 0.1
            else:
                # Poor alignment
                return 0.0
        
        # Factor 4: Sufficient columns (0-0.2)
        avg_columns = sum(column_counts) / len(column_counts)
        if avg_columns >= 3:
            confidence += 0.2
        elif avg_columns >= 2:
            confidence += 0.1
        
        # Factor 5: Sufficient rows (0-0.2)
        row_count = len(candidate_rows)
        if row_count >= 5:
            confidence += 0.2
        elif row_count >= 3:
            confidence += 0.1
        
        # Factor 6: Reject list-like patterns (bullet points, numbers)
        # Check first column for list markers
        list_marker_count = 0
        for _, column_groups, _ in candidate_rows:
            if column_groups and column_groups[0]:
                # Get text from first column
                first_col_text = ' '.join(w['text'] for w in column_groups[0]).strip()
                # Common list markers
                if first_col_text in ['•', '-', '*', '◦', '▪', '–', '—'] or \
                   (first_col_text.endswith('.') and len(first_col_text) <= 3 and first_col_text[:-1].isdigit()):
                    list_marker_count += 1
        
        if list_marker_count > len(candidate_rows) * 0.5:
            # More than half the rows start with list markers - likely a list
            return 0.0
        
        return min(confidence, 1.0)
    
    def _extract_table_from_candidate(self, candidate_rows: list[tuple]) -> list[list[str]]:
        """Extract table data from candidate rows.
        
        Args:
            candidate_rows: List of (y, column_groups, words) tuples.
            
        Returns:
            List of rows, where each row is a list of cell strings.
        """
        table_data = []
        
        for y, column_groups, row_words in candidate_rows:
            # Convert each column group to a cell
            row_data = []
            for group in column_groups:
                # Sort words within column by x-position
                sorted_words = sorted(group, key=lambda w: w['x0'])
                # Join words in column with space
                cell_text = ' '.join(w['text'] for w in sorted_words)
                row_data.append(cell_text)
            
            table_data.append(row_data)
        
        return table_data

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
