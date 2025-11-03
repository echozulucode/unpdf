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
    text patterns, indentation, and context. Handles PDFs where bullet
    characters are missing (e.g., Obsidian exports).

    Attributes:
        bullet_chars: Set of characters that indicate bullet points.
        number_pattern: Regex pattern for numbered list items.
        list_indent_x0s: Known x0 coordinates that indicate list items.
        in_list_context: Whether we're currently in a list section.

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

    # Checkbox patterns: "[ ]", "[x]", "[X]"
    CHECKBOX_PATTERN = re.compile(r"^\[([ xX])\]\s+")

    # Pattern for CID (Character ID) references that are often bullet characters
    # e.g., "(cid:127)" which is a placeholder for undecoded character
    CID_PATTERN = re.compile(r"^\(cid:\d+\)\s+")

    # Known list indentation x0 values (from Obsidian PDF analysis)
    # These are typical indentation values for list items
    LIST_INDENT_X0S = {
        71.8,  # First-level unordered list
        98.8,  # Second-level nested list
        58.4,  # Ordered list items
    }

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
        self.checkbox_pattern = self.CHECKBOX_PATTERN
        self.cid_pattern = self.CID_PATTERN
        self.list_indent_x0s = self.LIST_INDENT_X0S
        self.in_list_context = False
        self.last_header = ""

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
        y0 = span.get("y0", 0.0)
        page_number = span.get("page_number", 1)

        # Calculate indent level based on x-coordinate
        indent_level = self._calculate_indent_level(x0)

        # Check for checkbox list items first (e.g., "[ ] Task" or "[x] Done")
        # Only treat as checkbox if the span was annotated by the CheckboxDetector
        # (to avoid false positives on literal "[ ]" text in demonstrations)
        checkbox_match = self.checkbox_pattern.match(text)
        has_checkbox = span.get("has_checkbox", False)
        if checkbox_match and has_checkbox:
            cleaned_text = text[checkbox_match.end() :].strip()
            # Use the checkbox state from the detector, not the text marker
            checked = span.get("checkbox_checked", False)
            list_text = f"[{'x' if checked else ' '}] {cleaned_text}"
            logger.debug(f"Detected checkbox item: '{list_text[:30]}...'")
            return ListItemElement(
                text=list_text,
                is_ordered=False,
                indent_level=indent_level,
                y0=y0,
                page_number=page_number,
            )

        # Check for CID bullet markers (e.g., "(cid:127)" )
        cid_match = self.cid_pattern.match(text)
        if cid_match:
            cleaned_text = text[cid_match.end() :].strip()
            logger.debug(f"Detected CID bullet item: '{cleaned_text[:30]}...'")
            return ListItemElement(
                text=cleaned_text,
                is_ordered=False,
                indent_level=indent_level,
                y0=y0,
                page_number=page_number,
            )

        # Check for bullet list (explicit markers)
        if self._is_bullet_list(text):
            cleaned_text = self._remove_bullet(text)
            logger.debug(f"Detected bullet item: '{cleaned_text[:30]}...'")
            return ListItemElement(
                text=cleaned_text,
                is_ordered=False,
                indent_level=indent_level,
                y0=y0,
                page_number=page_number,
            )

        # Check for numbered list
        numbered_match = self.number_pattern.match(text)
        if numbered_match:
            # Remove the number prefix
            cleaned_text = text[numbered_match.end() :].strip()
            logger.debug(f"Detected numbered item: '{cleaned_text[:30]}...'")
            return ListItemElement(
                text=cleaned_text,
                is_ordered=True,
                indent_level=indent_level,
                y0=y0,
                page_number=page_number,
            )

        # Heuristic detection for lists without bullet markers
        # (e.g., PDFs exported by Obsidian where bullets are stripped)
        # Only use this when we're in a list context to avoid false positives
        if self.in_list_context and self._looks_like_list_item(text, x0):
            logger.debug(f"Detected list item by heuristic: '{text[:30]}...'")
            return ListItemElement(
                text=text,
                is_ordered=False,
                indent_level=indent_level,
                y0=y0,
                page_number=page_number,
            )

        # Not a list item
        return ParagraphElement(text=text, y0=y0, page_number=page_number)

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

    def _looks_like_list_item(self, text: str, x0: float) -> bool:
        """Heuristic to detect list items without bullet markers.

        Used for PDFs where bullet characters are missing (e.g., Obsidian exports).
        Detects list items based on:
        - Indentation matching known list x0 values
        - Short text length (list items are typically concise)
        - Context (being in a list section)

        Args:
            text: Text content to check.
            x0: Left x-coordinate of text.

        Returns:
            True if text appears to be a list item.

        Example:
            >>> processor = ListProcessor()
            >>> processor._looks_like_list_item("Apples", 71.8)
            True
            >>> processor._looks_like_list_item("This is a long paragraph...", 51.7)
            False
        """
        # Check if x0 matches known list indentation (with stricter tolerance)
        for known_x0 in self.list_indent_x0s:
            if (
                abs(x0 - known_x0) < 1.0  # Stricter tolerance: 1pt instead of 2pt
                and len(text) < 80  # List items are typically short
                and len(text.split()) <= 10  # And concise
            ):
                return True

        return False

    def update_context(self, header_text: str) -> None:
        """Update processor context based on section headers.

        This helps improve list detection by tracking whether we're
        in a list section.

        Args:
            header_text: Text of the current header.

        Example:
            >>> processor = ListProcessor()
            >>> processor.update_context("Unordered List")
            >>> processor.in_list_context
            True
        """
        lower_text = header_text.lower()
        self.in_list_context = ("list" in lower_text) or ("checklist" in lower_text)
        self.last_header = header_text
