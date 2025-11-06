"""Blockquote detection processor for unpdf.

This module detects blockquotes based on indentation and quote characters.

Example:
    >>> from unpdf.processors.blockquote import BlockquoteProcessor
    >>> processor = BlockquoteProcessor()
    >>> span = {"text": "Quote text", "x0": 120}
    >>> result = processor.process(span)
    >>> result.to_markdown()
    '> Quote text'
"""

import logging
from dataclasses import dataclass
from typing import Any

from unpdf.processors.headings import Element, ParagraphElement

logger = logging.getLogger(__name__)


@dataclass
class BlockquoteElement(Element):
    """Blockquote element.

    Attributes:
        text: Quote text content.
        level: Nesting level (0 = top level, 1 = nested once, etc.).
    """

    level: int = 0

    def to_markdown(self) -> str:
        """Convert blockquote to Markdown.

        Returns:
            Text prefixed with `>` symbols.

        Example:
            >>> quote = BlockquoteElement("Quote text", level=0)
            >>> quote.to_markdown()
            '> Quote text'
            >>> nested = BlockquoteElement("Nested", level=1)
            >>> nested.to_markdown()
            '> > Nested'
        """
        prefix = "> " * (self.level + 1)
        return f"{prefix}{self.text}"


class BlockquoteProcessor:
    """Process text spans and detect blockquotes.

    Blockquotes are detected by:
    1. Large left indentation (significantly beyond normal margin)
    2. Optional quote marks at start

    Attributes:
        base_indent: Normal left margin for body text (in points).
        quote_threshold: Minimum indent beyond base to be a quote.
        nested_threshold: Additional indent per nesting level.

    Example:
        >>> processor = BlockquoteProcessor()
        >>> span = {"text": "Quote", "x0": 150}
        >>> result = processor.process(span)
        >>> isinstance(result, BlockquoteElement)
        True
    """

    # Quote mark characters (regular, smart quotes, and guillemets)
    QUOTE_CHARS = {'"', "'", "»", "«"}

    def __init__(
        self,
        base_indent: float = 52.0,
        quote_threshold: float = 25.0,
        nested_threshold: float = 30.0,
        max_indent: float = 200.0,
        require_multiple_lines: bool = False,
    ):
        """Initialize BlockquoteProcessor.

        Args:
            base_indent: Normal left margin in points (default 52pt).
            quote_threshold: Minimum indent beyond base for blockquote.
                Default 25pt (balanced to reduce false positives while detecting real quotes).
            nested_threshold: Additional indent per nesting level.
                Default 30pt.
            max_indent: Maximum indent to consider as blockquote. Text with
                indent beyond this is likely misplaced/formatted differently.
                Default 200pt.
            require_multiple_lines: If True, only detect blockquotes that span
                multiple consecutive lines. Default False.

        Example:
            >>> processor = BlockquoteProcessor(base_indent=100.0)
            >>> processor.base_indent
            100.0
        """
        self.base_indent = base_indent
        self.quote_threshold = quote_threshold
        self.nested_threshold = nested_threshold
        self.max_indent = max_indent
        self.require_multiple_lines = require_multiple_lines
        self.quote_chars = self.QUOTE_CHARS
        self.consecutive_quote_lines = 0
        self.last_was_quote = False

    def process(self, span: dict[str, Any]) -> BlockquoteElement | ParagraphElement:
        """Process text span and detect blockquotes.

        Args:
            span: Text span dictionary with keys:
                - text (str): Text content
                - x0 (float): Left x-coordinate

        Returns:
            BlockquoteElement if detected, otherwise ParagraphElement.

        Example:
            >>> processor = BlockquoteProcessor()
            >>> span = {"text": '"Quote"', "x0": 120}
            >>> result = processor.process(span)
            >>> isinstance(result, BlockquoteElement)
            True
            >>> result.text
            'Quote'
        """
        text = span["text"]
        x0 = span.get("x0", 0)
        y0 = span.get("y0", 0.0)
        page_number = span.get("page_number", 1)

        # Calculate indent relative to base
        indent = x0 - self.base_indent

        # Check if indented enough to be a quote
        if indent < self.quote_threshold:
            return ParagraphElement(text=text, y0=y0, x0=x0, page_number=page_number)

        # Check if indented TOO much (likely not a blockquote but misplaced text)
        if indent > self.max_indent:
            logger.debug(
                f"Skipping blockquote detection: indent={indent:.1f} > max={self.max_indent}"
            )
            return ParagraphElement(text=text, y0=y0, x0=x0, page_number=page_number)

        # Calculate nesting level
        level = int((indent - self.quote_threshold) / self.nested_threshold)
        level = max(0, min(level, 5))  # Cap at 5 levels

        # Remove leading/trailing quote marks if present
        cleaned_text = self._remove_quote_marks(text)

        logger.debug(f"Detected blockquote (level={level}): '{cleaned_text[:30]}...'")
        return BlockquoteElement(
            text=cleaned_text, level=level, y0=y0, x0=x0, page_number=page_number
        )

    def _remove_quote_marks(self, text: str) -> str:
        """Remove leading and trailing quote marks from text.

        Args:
            text: Text that may have quote marks.

        Returns:
            Text with quote marks removed.

        Example:
            >>> processor = BlockquoteProcessor()
            >>> processor._remove_quote_marks('"Quote"')
            'Quote'
            >>> processor._remove_quote_marks('"Quote')
            'Quote'
            >>> processor._remove_quote_marks('No quotes')
            'No quotes'
        """
        text = text.strip()

        # Remove leading quote
        if text and text[0] in self.quote_chars:
            text = text[1:].lstrip()

        # Remove trailing quote
        if text and text[-1] in self.quote_chars:
            text = text[:-1].rstrip()

        return text
