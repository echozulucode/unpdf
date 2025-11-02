"""Heading detection processor for unpdf.

This module classifies text spans as headings based on font size relative
to the document average. Larger text is mapped to Markdown heading levels.

Example:
    >>> from unpdf.processors.headings import HeadingProcessor
    >>> processor = HeadingProcessor(avg_font_size=12.0)
    >>> result = processor.process(
    ...     {"text": "Title", "font_size": 24.0, "is_bold": True}
    ... )
    >>> result.to_markdown()
    '# Title'
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Element:
    """Base class for document elements."""

    text: str

    def to_markdown(self) -> str:
        """Convert element to Markdown string.

        Returns:
            Markdown representation of element.
        """
        raise NotImplementedError


@dataclass
class HeadingElement(Element):
    """Heading element with level (H1-H6).

    Attributes:
        text: Heading text content.
        level: Heading level from 1 (largest) to 6 (smallest).
    """

    level: int

    def to_markdown(self) -> str:
        """Convert heading to Markdown.

        Returns:
            Markdown heading like "# Title" or "## Section".

        Example:
            >>> heading = HeadingElement("Title", level=1)
            >>> heading.to_markdown()
            '# Title'
        """
        prefix = "#" * self.level
        return f"{prefix} {self.text}"


@dataclass
class ParagraphElement(Element):
    """Plain paragraph element.

    Attributes:
        text: Paragraph text content.
    """

    def to_markdown(self) -> str:
        """Convert paragraph to Markdown.

        Returns:
            Plain text without markup.

        Example:
            >>> para = ParagraphElement("This is text.")
            >>> para.to_markdown()
            'This is text.'
        """
        return self.text


class HeadingProcessor:
    """Process text spans and detect headings based on font size.

    Compares each span's font size to the document average. Text significantly
    larger than average is classified as a heading, with the level determined
    by relative size.

    Attributes:
        avg_font_size: Average font size in the document (in points).
        heading_ratio: Multiplier threshold for heading detection.
            Text with font_size > avg * ratio is a heading.
        max_level: Maximum heading level to generate (1-6).

    Example:
        >>> processor = HeadingProcessor(avg_font_size=12.0)
        >>> span = {"text": "Title", "font_size": 24.0, "is_bold": True}
        >>> result = processor.process(span)
        >>> isinstance(result, HeadingElement)
        True
        >>> result.level
        1
    """

    def __init__(
        self,
        avg_font_size: float,
        heading_ratio: float = 1.3,
        max_level: int = 6,
    ):
        """Initialize HeadingProcessor.

        Args:
            avg_font_size: Average font size in document (in points).
            heading_ratio: Font size multiplier for heading threshold.
                Default 1.3 means text 30% larger is a heading.
            max_level: Maximum heading level (1-6). Default 6.

        Raises:
            ValueError: If max_level not between 1 and 6.
            ValueError: If avg_font_size <= 0.
            ValueError: If heading_ratio <= 1.0.

        Example:
            >>> processor = HeadingProcessor(12.0, heading_ratio=1.5)
            >>> processor.threshold
            18.0
        """
        if not 1 <= max_level <= 6:
            raise ValueError(f"max_level must be 1-6, got {max_level}")
        if avg_font_size <= 0:
            raise ValueError(f"avg_font_size must be positive, got {avg_font_size}")
        if heading_ratio <= 1.0:
            raise ValueError(f"heading_ratio must be > 1.0, got {heading_ratio}")

        self.avg_font_size = avg_font_size
        self.heading_ratio = heading_ratio
        self.max_level = max_level
        self.threshold = avg_font_size * heading_ratio

        logger.debug(
            f"HeadingProcessor initialized: avg={avg_font_size:.1f}pt, "
            f"threshold={self.threshold:.1f}pt"
        )

    def process(self, span: dict[str, Any]) -> HeadingElement | ParagraphElement:
        """Process text span and classify as heading or paragraph.

        Args:
            span: Text span dictionary with keys:
                - text (str): Text content
                - font_size (float): Font size in points
                - is_bold (bool): Whether text is bold
                - is_italic (bool): Whether text is italic

        Returns:
            HeadingElement if detected as heading, otherwise ParagraphElement.

        Example:
            >>> processor = HeadingProcessor(avg_font_size=12.0)
            >>> span = {"text": "Section", "font_size": 18.0, "is_bold": True}
            >>> result = processor.process(span)
            >>> result.level
            2
            >>> result.to_markdown()
            '## Section'
        """
        text = span["text"]
        font_size = span["font_size"]
        is_bold = span.get("is_bold", False)

        # Check if text is large enough to be a heading
        if font_size >= self.threshold:
            level = self._calculate_level(font_size, is_bold)
            logger.debug(
                f"Detected heading: '{text[:30]}...' "
                f"(size={font_size:.1f}pt, level={level})"
            )
            return HeadingElement(text=text, level=level)

        # Regular paragraph
        return ParagraphElement(text=text)

    def _calculate_level(self, font_size: float, is_bold: bool) -> int:
        """Calculate heading level based on font size.

        Larger text gets lower level numbers (H1 = largest).
        Bold text gets slight priority in level assignment.

        Args:
            font_size: Font size of the text in points.
            is_bold: Whether the text is bold.

        Returns:
            Heading level from 1 (largest) to max_level.

        Note:
            Uses a simple heuristic:
            - Calculate size ratio relative to threshold
            - Map to level inversely (larger = lower level number)
            - Bold text gets ~0.5 level boost
        """
        # Calculate how much larger than threshold
        size_ratio = font_size / self.threshold

        # Map ratio to level (larger = lower level number)
        # Ratio 2.0+ -> H1, 1.5-2.0 -> H2, etc.
        if size_ratio >= 2.0:
            level = 1
        elif size_ratio >= 1.7:
            level = 2
        elif size_ratio >= 1.4:
            level = 3
        elif size_ratio >= 1.2:
            level = 4
        elif size_ratio >= 1.1:
            level = 5
        else:
            level = 6

        # Bold text gets slight priority (reduce level by 1)
        if is_bold and level > 1:
            level -= 1

        # Ensure within max_level
        level = min(level, self.max_level)

        return level
