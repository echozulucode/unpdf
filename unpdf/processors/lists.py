"""List detection processor for unpdf.

This module detects and converts bullet and numbered lists from PDFs to
Markdown list format.

Example:
    >>> from unpdf.processors.lists import ListProcessor
    >>> processor = ListProcessor()
    >>> span = {"text": "• First item", "x0": 72}
    >>> result = processor.process(span)
    >>> result.to_markdown()
    '- First item'
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from unpdf.processors.headings import Element, ParagraphElement

logger = logging.getLogger(__name__)


@dataclass
class ListItemElement(Element):
    """List item element (bullet or numbered).

    Attributes:
        text: List item text content (without bullet/number).
        is_ordered: True for numbered lists, False for bullet lists.
        indent_level: Nesting level (0 = top level).
    """

    is_ordered: bool = False
    indent_level: int = 0

    def to_markdown(self) -> str:
        """Convert list item to Markdown.

        Returns:
            Markdown list item like "- Item" or "1. Item".

        Example:
            >>> item = ListItemElement("First", is_ordered=False)
            >>> item.to_markdown()
            '- First'
            >>> item2 = ListItemElement("Second", is_ordered=True, indent_level=1)
            >>> item2.to_markdown()
            '    1. Second'
        """
        indent = "    " * self.indent_level  # 4 spaces per level
        prefix = "1." if self.is_ordered else "-"
        return f"{indent}{prefix} {self.text}"


class ListProcessor:
    """Process text spans and detect list items.

    Detects bullet points, numbered lists, and nested lists based on
    text patterns and indentation.

    Attributes:
        bullet_chars: Set of characters that indicate bullet points.
        number_pattern: Regex pattern for numbered list items.

    Example:
        >>> processor = ListProcessor()
        >>> span = {"text": "• Item one", "x0": 100}
        >>> result = processor.process(span)
        >>> result.to_markdown()
        '- Item one'
    """

    # Common bullet characters in PDFs
    BULLET_CHARS = {"•", "●", "○", "◦", "▪", "▫", "–", "-", "·", "►", "➢"}

    # Pattern for numbered lists: "1.", "a)", "i.", etc.
    NUMBER_PATTERN = re.compile(r"^(\d+\.|[a-z]\)|[ivxlcdm]+\.)\s+", re.IGNORECASE)

    def __init__(self, base_indent: float = 72.0, indent_threshold: float = 20.0):
        """Initialize ListProcessor.

        Args:
            base_indent: Base x-coordinate for top-level items (in points).
                Default 72pt = 1 inch margin.
            indent_threshold: Minimum x-coordinate difference to detect
                increased indent level (in points). Default 20pt.

        Example:
            >>> processor = ListProcessor(base_indent=100.0)
            >>> processor.base_indent
            100.0
        """
        self.base_indent = base_indent
        self.indent_threshold = indent_threshold
        self.bullet_chars = self.BULLET_CHARS
        self.number_pattern = self.NUMBER_PATTERN

    def process(self, span: dict[str, Any]) -> ListItemElement | ParagraphElement:
        """Process text span and detect list items.

        Args:
            span: Text span dictionary with keys:
                - text (str): Text content
                - x0 (float): Left x-coordinate

        Returns:
            ListItemElement if list detected, otherwise ParagraphElement.

        Example:
            >>> processor = ListProcessor()
            >>> span = {"text": "1. First item", "x0": 72}
            >>> result = processor.process(span)
            >>> result.is_ordered
            True
            >>> result.text
            'First item'
        """
        text = span["text"].strip()
        x0 = span.get("x0", 0)

        # Calculate indent level based on x-coordinate
        indent_level = self._calculate_indent_level(x0)

        # Check for bullet list
        if self._is_bullet_list(text):
            cleaned_text = self._remove_bullet(text)
            logger.debug(f"Detected bullet item: '{cleaned_text[:30]}...'")
            return ListItemElement(
                text=cleaned_text, is_ordered=False, indent_level=indent_level
            )

        # Check for numbered list
        numbered_match = self.number_pattern.match(text)
        if numbered_match:
            # Remove the number prefix
            cleaned_text = text[numbered_match.end() :].strip()
            logger.debug(f"Detected numbered item: '{cleaned_text[:30]}...'")
            return ListItemElement(
                text=cleaned_text, is_ordered=True, indent_level=indent_level
            )

        # Not a list item
        return ParagraphElement(text=text)

    def _is_bullet_list(self, text: str) -> bool:
        """Check if text starts with a bullet character.

        Args:
            text: Text to check.

        Returns:
            True if text starts with bullet character.

        Example:
            >>> processor = ListProcessor()
            >>> processor._is_bullet_list("• Item")
            True
            >>> processor._is_bullet_list("Not a list")
            False
        """
        if not text:
            return False

        # Check first character
        first_char = text[0]
        return first_char in self.bullet_chars

    def _remove_bullet(self, text: str) -> str:
        """Remove bullet character from start of text.

        Args:
            text: Text with bullet character.

        Returns:
            Text with bullet and following whitespace removed.

        Example:
            >>> processor = ListProcessor()
            >>> processor._remove_bullet("• Item text")
            'Item text'
            >>> processor._remove_bullet("- Another item")
            'Another item'
        """
        # Remove first character (bullet) and any following whitespace
        return text[1:].lstrip()

    def _calculate_indent_level(self, x0: float) -> int:
        """Calculate list indent level from x-coordinate.

        Args:
            x0: Left x-coordinate of text in points.

        Returns:
            Indent level (0 = top level, 1 = first nested, etc.).

        Example:
            >>> processor = ListProcessor(base_indent=72.0, indent_threshold=20.0)
            >>> processor._calculate_indent_level(72.0)
            0
            >>> processor._calculate_indent_level(100.0)
            1
        """
        if x0 <= self.base_indent:
            return 0

        # Calculate how many indent_threshold units beyond base
        indent_offset = x0 - self.base_indent
        level = int(indent_offset / self.indent_threshold)

        # Cap at reasonable maximum
        return min(level, 5)
