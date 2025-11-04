"""List detection module using pattern matching and spatial analysis.

This module detects bulleted and numbered lists by analyzing text patterns,
spatial positioning, and indentation consistency.
"""

import re
from dataclasses import dataclass

from unpdf.models.layout import BoundingBox


@dataclass
class TextBlock:
    """Represents a text block with content and positioning."""

    text: str
    bbox: BoundingBox
    font_size: float
    font_name: str
    is_bold: bool = False


@dataclass
class ListItem:
    """Represents a detected list item."""

    text: str
    level: int
    item_type: str  # "bullet", "numbered", "lettered", "roman"
    marker: str
    confidence: float
    bbox: BoundingBox
    line_number: int


class ListDetector:
    """Detects lists in text blocks using pattern matching and spatial analysis.

    Detects:
    - Bulleted lists (•●○◦■□◆◇-–—→►✓*)
    - Numbered lists (1. 2. 3.)
    - Lettered lists (a. b. c. or A. B. C.)
    - Roman numeral lists (i. ii. iii.)
    - Multi-level indentation
    """

    # Common bullet characters
    BULLET_CHARS = "•●○◦■□◆◇-–—→►✓✗✔✘×★☐☑☒"

    # Numbering patterns
    ARABIC_PATTERN = re.compile(r"^\s*(\d+)[\.):]\s+")
    LOWERCASE_PATTERN = re.compile(r"^\s*([a-z])[\.):]\s+")
    UPPERCASE_PATTERN = re.compile(r"^\s*([A-Z])[\.):]\s+")
    ROMAN_PATTERN = re.compile(
        r"^\s*(i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv)[\.):]\s+",
        re.IGNORECASE,
    )

    def __init__(
        self,
        indent_tolerance: float = 5.0,
        min_spacing_ratio: float = 1.2,
        max_spacing_ratio: float = 2.0,
        hanging_indent_min: float = 10.0,
        hanging_indent_max: float = 30.0,
    ):
        """Initialize list detector with configurable parameters.

        Args:
            indent_tolerance: Pixels of tolerance for indent alignment
            min_spacing_ratio: Minimum vertical spacing as ratio of line height
            max_spacing_ratio: Maximum vertical spacing as ratio of line height
            hanging_indent_min: Minimum hanging indent in pixels
            hanging_indent_max: Maximum hanging indent in pixels
        """
        self.indent_tolerance = indent_tolerance
        self.min_spacing_ratio = min_spacing_ratio
        self.max_spacing_ratio = max_spacing_ratio
        self.hanging_indent_min = hanging_indent_min
        self.hanging_indent_max = hanging_indent_max

    def detect_lists(self, blocks: list[TextBlock]) -> list[ListItem]:
        """Detect list items in text blocks.

        Args:
            blocks: List of text blocks to analyze

        Returns:
            List of detected list items with confidence scores
        """
        if not blocks:
            return []

        list_items = []

        for i, block in enumerate(blocks):
            # Try bullet detection first
            bullet_result = self._detect_bullet(block, i)
            if bullet_result:
                list_items.append(bullet_result)
                continue

            # Try numbered list detection
            numbered_result = self._detect_numbered(block, i)
            if numbered_result:
                list_items.append(numbered_result)
                continue

        # Assign levels based on indentation
        list_items = self._assign_levels(list_items)

        # Validate sequences for numbered lists
        list_items = self._validate_sequences(list_items)

        return list_items

    def _detect_bullet(self, block: TextBlock, line_num: int) -> ListItem | None:
        """Detect bullet list item.

        Args:
            block: Text block to analyze
            line_num: Line number in document

        Returns:
            ListItem if detected, None otherwise
        """
        text = block.text.lstrip()
        if not text:
            return None

        # Check if first character is a bullet
        first_char = text[0]
        if first_char not in self.BULLET_CHARS:
            return None

        # Check if followed by whitespace
        if len(text) < 2 or not text[1].isspace():
            return None

        # Extract content after bullet
        content = text[2:].strip()
        if not content:
            return None

        # Calculate confidence based on:
        # - Bullet character presence (0.5)
        # - Whitespace after bullet (0.3)
        # - Non-empty content (0.2)
        confidence = 0.5 + 0.3 + 0.2

        return ListItem(
            text=content,
            level=0,  # Will be assigned later
            item_type="bullet",
            marker=first_char,
            confidence=confidence,
            bbox=block.bbox,
            line_number=line_num,
        )

    def _detect_numbered(self, block: TextBlock, line_num: int) -> ListItem | None:
        """Detect numbered list item.

        Args:
            block: Text block to analyze
            line_num: Line number in document

        Returns:
            ListItem if detected, None otherwise
        """
        text = block.text

        # Try arabic numbers first
        match = self.ARABIC_PATTERN.match(text)
        if match:
            marker = match.group(1)
            content = text[match.end() :].strip()
            return ListItem(
                text=content,
                level=0,
                item_type="numbered",
                marker=marker,
                confidence=0.9,
                bbox=block.bbox,
                line_number=line_num,
            )

        # Try roman numerals before single letters (i, v, x can be both)
        match = self.ROMAN_PATTERN.match(text)
        if match:
            marker = match.group(1)
            content = text[match.end() :].strip()
            return ListItem(
                text=content,
                level=0,
                item_type="roman",
                marker=marker,
                confidence=0.8,
                bbox=block.bbox,
                line_number=line_num,
            )

        # Try lowercase letters
        match = self.LOWERCASE_PATTERN.match(text)
        if match:
            marker = match.group(1)
            content = text[match.end() :].strip()
            return ListItem(
                text=content,
                level=0,
                item_type="lettered",
                marker=marker,
                confidence=0.85,
                bbox=block.bbox,
                line_number=line_num,
            )

        # Try uppercase letters
        match = self.UPPERCASE_PATTERN.match(text)
        if match:
            marker = match.group(1)
            content = text[match.end() :].strip()
            return ListItem(
                text=content,
                level=0,
                item_type="lettered",
                marker=marker,
                confidence=0.85,
                bbox=block.bbox,
                line_number=line_num,
            )

        return None

    def _assign_levels(self, items: list[ListItem]) -> list[ListItem]:
        """Assign indentation levels to list items.

        Levels based on x-coordinate clustering:
        - Level 1: 0-10 pixels indent
        - Level 2: 20-40 pixels indent
        - Level 3: 40-60 pixels indent

        Args:
            items: List items to assign levels

        Returns:
            List items with updated levels
        """
        if not items:
            return items

        # Collect all x-coordinates
        x_coords = [item.bbox.x1 for item in items]

        # Cluster x-coordinates into levels
        level_boundaries = self._cluster_indents(x_coords)

        # Assign levels
        for item in items:
            x = item.bbox.x1
            for level, (min_x, max_x) in enumerate(level_boundaries):
                if min_x - self.indent_tolerance <= x <= max_x + self.indent_tolerance:
                    item.level = level
                    break

        return items

    def _cluster_indents(self, x_coords: list[float]) -> list[tuple[float, float]]:
        """Cluster x-coordinates into indent levels.

        Args:
            x_coords: List of x-coordinates

        Returns:
            List of (min, max) tuples for each level
        """
        if not x_coords:
            return []

        sorted_coords = sorted(set(x_coords))
        clusters = []
        current_cluster = [sorted_coords[0]]

        for x in sorted_coords[1:]:
            if x - current_cluster[-1] <= self.indent_tolerance * 2:
                current_cluster.append(x)
            else:
                clusters.append((min(current_cluster), max(current_cluster)))
                current_cluster = [x]

        if current_cluster:
            clusters.append((min(current_cluster), max(current_cluster)))

        return clusters

    def _validate_sequences(self, items: list[ListItem]) -> list[ListItem]:
        """Validate numbering sequences and adjust confidence.

        For numbered lists, verify that n+1 follows n. Reduce confidence
        for items that don't follow expected sequence.

        Args:
            items: List items to validate

        Returns:
            List items with updated confidence scores
        """
        # Group by type and level
        groups: dict[tuple[str, int], list[ListItem]] = {}
        for item in items:
            key = (item.item_type, item.level)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        # Validate each group
        for key, group in groups.items():
            item_type, level = key

            if item_type == "numbered":
                self._validate_arabic_sequence(group)
            elif item_type == "lettered":
                self._validate_letter_sequence(group)
            elif item_type == "roman":
                self._validate_roman_sequence(group)

        return items

    def _validate_arabic_sequence(self, items: list[ListItem]) -> None:
        """Validate arabic number sequence."""
        if not items:
            return

        # Sort by line number
        sorted_items = sorted(items, key=lambda x: x.line_number)

        for i in range(len(sorted_items) - 1):
            current = sorted_items[i]
            next_item = sorted_items[i + 1]

            try:
                current_num = int(current.marker)
                next_num = int(next_item.marker)

                # Check if sequence is consecutive
                if next_num != current_num + 1:
                    # Reduce confidence for non-consecutive items
                    next_item.confidence *= 0.8
            except ValueError:
                # Invalid number, reduce confidence
                current.confidence *= 0.5

    def _validate_letter_sequence(self, items: list[ListItem]) -> None:
        """Validate letter sequence (a, b, c or A, B, C)."""
        if not items:
            return

        sorted_items = sorted(items, key=lambda x: x.line_number)

        for i in range(len(sorted_items) - 1):
            current = sorted_items[i]
            next_item = sorted_items[i + 1]

            if len(current.marker) == 1 and len(next_item.marker) == 1:
                current_ord = ord(current.marker)
                next_ord = ord(next_item.marker)

                if next_ord != current_ord + 1:
                    next_item.confidence *= 0.8

    def _validate_roman_sequence(self, items: list[ListItem]) -> None:
        """Validate roman numeral sequence."""
        roman_to_int = {
            "i": 1,
            "ii": 2,
            "iii": 3,
            "iv": 4,
            "v": 5,
            "vi": 6,
            "vii": 7,
            "viii": 8,
            "ix": 9,
            "x": 10,
            "xi": 11,
            "xii": 12,
            "xiii": 13,
            "xiv": 14,
            "xv": 15,
        }

        if not items:
            return

        sorted_items = sorted(items, key=lambda x: x.line_number)

        for i in range(len(sorted_items) - 1):
            current = sorted_items[i]
            next_item = sorted_items[i + 1]

            current_val = roman_to_int.get(current.marker.lower())
            next_val = roman_to_int.get(next_item.marker.lower())

            if current_val and next_val and next_val != current_val + 1:
                next_item.confidence *= 0.8
