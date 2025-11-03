"""Checkbox detection from PDF drawing objects.

This module detects checkboxes rendered as vector graphics in PDFs
(common in Obsidian exports) and annotates text with checkbox markers.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CheckboxDrawing:
    """Represents a checkbox detected from PDF drawings.

    Attributes:
        x: X-coordinate of checkbox center.
        y: Y-coordinate of checkbox center.
        is_checked: Whether the checkbox is checked.
    """

    x: float
    y: float
    is_checked: bool


class CheckboxDetector:
    """Detects checkboxes from PDF drawing objects.

    Obsidian and other PDF exporters render checkboxes as vector graphics
    rather than text. This detector analyzes drawing objects to find checkboxes
    and determine if they're checked or unchecked.

    Checked boxes typically have:
    - Filled colored circle/square
    - Checkmark shape inside
    - Multiple layered drawings

    Unchecked boxes typically have:
    - Outline only (no fill or minimal fill)
    - Simpler structure

    Attributes:
        checkbox_size_range: (min, max) size in points for checkbox shapes.
        vertical_tolerance: How close (in points) text must be to checkbox.
    """

    # Checkbox size range in points (typical checkbox is 10-15pt)
    CHECKBOX_SIZE_RANGE = (8.0, 20.0)

    # How close text needs to be vertically to be associated with checkbox
    VERTICAL_TOLERANCE = 8.0

    # Common checkbox colors (RGB tuples)
    # Purple/violet used in Obsidian for checked boxes
    CHECKED_COLORS = [
        (0.597, 0.451, 0.967),  # Purple from Obsidian
    ]

    def __init__(
        self,
        size_range: tuple[float, float] | None = None,
        vertical_tolerance: float | None = None,
    ):
        """Initialize CheckboxDetector.

        Args:
            size_range: Optional (min, max) size range for checkboxes.
            vertical_tolerance: Optional tolerance for vertical alignment.
        """
        self.checkbox_size_range = size_range or self.CHECKBOX_SIZE_RANGE
        self.vertical_tolerance = vertical_tolerance or self.VERTICAL_TOLERANCE

    def _is_monospace_font(self, font_name: str) -> bool:
        """Check if font is monospace/code font.

        Args:
            font_name: Font family name.

        Returns:
            True if monospace font.
        """
        monospace_patterns = [
            "courier",
            "consolas",
            "monaco",
            "menlo",
            "cascadia",
            "roboto mono",
            "source code",
            "fira code",
            "jetbrains mono",
            "inconsolata",
            "dejavu sans mono",
            "ubuntu mono",
        ]
        font_lower = font_name.lower()
        return any(pattern in font_lower for pattern in monospace_patterns)

    def detect_checkboxes(self, page: Any) -> list[CheckboxDrawing]:
        """Detect all checkboxes on a PDF page.

        Args:
            page: PyMuPDF page object.

        Returns:
            List of detected CheckboxDrawing objects.
        """
        drawings = page.get_drawings()
        checkboxes = []
        min_size, max_size = self.checkbox_size_range

        # Group drawings by approximate position (checkboxes are multi-layered)
        drawing_groups = self._group_drawings_by_position(drawings, tolerance=5.0)

        for group in drawing_groups:
            # Check if group looks like a checkbox
            if not self._is_checkbox_group(group, min_size, max_size):
                continue

            # Determine if checked based on fill colors and checkmark presence
            is_checked = self._is_checked(group)

            # Get center position
            rect = group[0]["rect"]
            cx = (rect.x0 + rect.x1) / 2
            cy = (rect.y0 + rect.y1) / 2

            checkbox = CheckboxDrawing(x=cx, y=cy, is_checked=is_checked)
            checkboxes.append(checkbox)
            logger.debug(
                f"Detected {'checked' if is_checked else 'unchecked'} "
                f"checkbox at ({cx:.1f}, {cy:.1f})"
            )

        return checkboxes

    def annotate_text_with_checkboxes(
        self,
        text_spans: list[dict[str, Any]],
        checkboxes: list[CheckboxDrawing],
        page_height: float | None = None,
    ) -> list[dict[str, Any]]:
        """Annotate text spans with checkbox markers.

        Args:
            text_spans: List of text span dictionaries with 'text', 'y0', 'y1'.
            checkboxes: List of detected CheckboxDrawing objects (PyMuPDF coords).
            page_height: PDF page height for coordinate conversion. If provided,
                assumes text_spans use pdfplumber coords (bottom-left origin) and
                converts checkbox coords from PyMuPDF (top-left origin).

        Returns:
            Text spans with checkbox markers added to text content.
        """
        # Create a copy to avoid modifying original
        annotated_spans = [span.copy() for span in text_spans]

        for span in annotated_spans:
            # Get span y-center (in pdfplumber coords if page_height provided)
            span_y_center = (span["y0"] + span["y1"]) / 2
            span_x0 = span["x0"]

            for checkbox in checkboxes:
                # Convert checkbox y-coordinate if needed
                # PyMuPDF: origin top-left, y increases downward
                # pdfplumber: origin bottom-left, y increases upward
                checkbox_y = checkbox.y
                if page_height:
                    checkbox_y = page_height - checkbox.y

                # Check vertical AND horizontal alignment
                # Checkbox should be:
                # 1. Vertically aligned with text (same line)
                # 2. At left margin (not mid-sentence) - real checkboxes are < 100pts from left
                # 3. Close to text horizontally (within 30pts)
                horizontal_distance = abs(checkbox.x - span_x0)
                is_left_margin = checkbox.x < 100.0
                if (
                    abs(checkbox_y - span_y_center) <= self.vertical_tolerance
                    and horizontal_distance <= 30.0
                    and is_left_margin
                ):
                    # Skip monospace fonts - they're likely inline code demonstrations
                    # of checkbox syntax, not actual checkboxes
                    font_family = span.get("font_family", "")
                    if self._is_monospace_font(font_family):
                        logger.debug(
                            f"Skipping checkbox for monospace span: {span['text'][:40]}..."
                        )
                        continue

                    # Add checkbox marker to beginning of text
                    marker = "[x]" if checkbox.is_checked else "[ ]"
                    span["text"] = f"{marker} {span['text']}"
                    span["has_checkbox"] = True
                    span["checkbox_checked"] = checkbox.is_checked
                    logger.debug(
                        f"Added checkbox marker '{marker}' to text at "
                        f"y={span_y_center:.1f}: {span['text'][:40]}..."
                    )
                    break  # Only one checkbox per line

        return annotated_spans

    def _group_drawings_by_position(
        self, drawings: list[dict[str, Any]], tolerance: float
    ) -> list[list[dict[str, Any]]]:
        """Group drawings that are at approximately the same position.

        Checkboxes are typically rendered as multiple overlapping shapes.

        Args:
            drawings: List of drawing dictionaries.
            tolerance: Maximum distance for grouping (in points).

        Returns:
            List of drawing groups.
        """
        groups: list[list[dict[str, Any]]] = []

        for drawing in drawings:
            rect = drawing["rect"]
            cx = (rect.x0 + rect.x1) / 2
            cy = (rect.y0 + rect.y1) / 2

            # Find existing group this belongs to
            found_group = False
            for group in groups:
                group_rect = group[0]["rect"]
                group_cx = (group_rect.x0 + group_rect.x1) / 2
                group_cy = (group_rect.y0 + group_rect.y1) / 2

                if abs(cx - group_cx) <= tolerance and abs(cy - group_cy) <= tolerance:
                    group.append(drawing)
                    found_group = True
                    break

            if not found_group:
                groups.append([drawing])

        return groups

    def _is_checkbox_group(
        self, group: list[dict[str, Any]], min_size: float, max_size: float
    ) -> bool:
        """Check if a group of drawings looks like a checkbox.

        Args:
            group: List of drawings at similar position.
            min_size: Minimum checkbox size.
            max_size: Maximum checkbox size.

        Returns:
            True if group appears to be a checkbox.
        """
        if not group:
            return False

        # Check size of primary shape
        rect = group[0]["rect"]
        width = rect.x1 - rect.x0
        height = rect.y1 - rect.y0

        # Checkbox should be roughly square and within size range
        is_square = 0.7 <= (width / height) <= 1.3 if height > 0 else False
        is_right_size = min_size <= width <= max_size and min_size <= height <= max_size

        # Checkboxes typically have multiple layers
        # Checked: 2-7 drawings (outline + fill + checkmark)
        # Unchecked: 1-2 drawings (just outline, sometimes with fill)
        has_valid_structure = 1 <= len(group) <= 7

        return is_square and is_right_size and has_valid_structure

    def _is_checked(self, group: list[dict[str, Any]]) -> bool:
        """Determine if a checkbox group represents a checked box.

        Checked boxes have colored fill and/or checkmark shapes.

        Args:
            group: List of drawings in checkbox group.

        Returns:
            True if checkbox is checked.
        """
        # Look for colored fills (indicating checked state)
        for drawing in group:
            fill = drawing.get("fill")
            if fill:
                # Check if fill color matches known checked colors
                for checked_color in self.CHECKED_COLORS:
                    if self._colors_match(fill, checked_color, tolerance=0.1):
                        return True

                # Also check for non-white/non-gray fills (likely checkmark)
                # Black checkmark: (0.13, 0.13, 0.13)
                if fill[0] < 0.3 and fill[1] < 0.3 and fill[2] < 0.3 and len(group) > 2:
                    # Checkmark with other shapes indicates checked
                    return True

        # No clear indication of checked state
        return False

    def _colors_match(
        self,
        color1: tuple[float, float, float],
        color2: tuple[float, float, float],
        tolerance: float,
    ) -> bool:
        """Check if two RGB colors match within tolerance.

        Args:
            color1: First RGB color (0-1 range).
            color2: Second RGB color (0-1 range).
            tolerance: Maximum difference per channel.

        Returns:
            True if colors match within tolerance.
        """
        return all(
            abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2, strict=True)
        )
