"""Horizontal rule detection processor for unpdf.

This module detects horizontal rules (---) based on PDF drawing objects.

Example:
    >>> from unpdf.processors.horizontal_rule import HorizontalRuleProcessor
    >>> processor = HorizontalRuleProcessor()
    >>> # Detect HRs from PDF drawing objects
"""

import logging
from dataclasses import dataclass
from typing import Any

from unpdf.processors.headings import Element

logger = logging.getLogger(__name__)


@dataclass
class HorizontalRuleElement(Element):
    """Horizontal rule element (---).

    Attributes:
        text: Always "---" for horizontal rules.
    """

    text: str = "---"

    def to_markdown(self) -> str:
        """Convert horizontal rule to Markdown.

        Returns:
            Markdown horizontal rule (---).
        """
        return "---"


class HorizontalRuleProcessor:
    """Detects horizontal rules from PDF drawing objects."""

    def __init__(
        self,
        min_width: float = 400.0,
        max_height: float = 3.0,
    ) -> None:
        """Initialize horizontal rule processor.

        Args:
            min_width: Minimum width for horizontal rule (default 400pt).
            max_height: Maximum height for horizontal rule (default 3pt).
        """
        self.min_width = min_width
        self.max_height = max_height
        logger.debug(
            f"Initialized HorizontalRuleProcessor (min_width={min_width}, max_height={max_height})"
        )

    def detect_horizontal_rules(
        self, drawings: list[dict[str, Any]], page_number: int
    ) -> list[HorizontalRuleElement]:
        """Detect horizontal rules from PDF drawing objects.

        Args:
            drawings: List of drawing dictionaries from page.get_drawings().
            page_number: Current page number.

        Returns:
            List of HorizontalRuleElement objects.
        """
        hr_elements = []

        for drawing in drawings:
            rect = drawing.get("rect")
            if not rect:
                continue

            width = rect.x1 - rect.x0
            height = rect.y1 - rect.y0

            # Horizontal rule criteria:
            # 1. Wide (spans most of page width)
            # 2. Very thin (just a line)
            if width >= self.min_width and height <= self.max_height:
                hr_elem = HorizontalRuleElement(
                    text="---",
                    y0=rect.y0,
                    page_number=page_number,
                )
                hr_elements.append(hr_elem)
                logger.debug(
                    f"Detected horizontal rule at page={page_number}, y={rect.y0}"
                )

        return hr_elements
