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
        min_width: float = 450.0,
        max_height: float = 2.0,
        min_spacing_before: float = 10.0,
        min_spacing_after: float = 10.0,
    ) -> None:
        """Initialize horizontal rule processor.

        Args:
            min_width: Minimum width for horizontal rule (default 450pt).
            max_height: Maximum height for horizontal rule (default 2pt).
            min_spacing_before: Minimum vertical space before HR (default 10pt).
            min_spacing_after: Minimum vertical space after HR (default 10pt).
        """
        self.min_width = min_width
        self.max_height = max_height
        self.min_spacing_before = min_spacing_before
        self.min_spacing_after = min_spacing_after
        logger.debug(
            f"Initialized HorizontalRuleProcessor (min_width={min_width}, max_height={max_height})"
        )

    def detect_horizontal_rules(
        self, drawings: list[dict[str, Any]], page_number: int, text_blocks: list[Any] = None
    ) -> list[HorizontalRuleElement]:
        """Detect horizontal rules from PDF drawing objects.

        Args:
            drawings: List of drawing dictionaries from page.get_drawings().
            page_number: Current page number.
            text_blocks: Optional list of text blocks to check spacing.

        Returns:
            List of HorizontalRuleElement objects.
        """
        # DISABLED: Horizontal rule detection from drawings is too unreliable
        # PDF drawing objects include many visual artifacts that aren't semantic HRs
        # Better approach: detect from text "---" markers in markdown context
        # or use explicit section separators
        
        logger.debug(f"Skipping drawing-based HR detection for page {page_number}")
        return []
