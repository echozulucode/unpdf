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
    y0: float = 0.0
    page_number: int = 1
    x0: float = 0.0

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

    level: int = 1

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
        is_bold: Whether text is bold.
        is_italic: Whether text is italic.
        is_strikethrough: Whether text has strikethrough.
    """

    is_bold: bool = False
    is_italic: bool = False
    is_strikethrough: bool = False

    def to_markdown(self) -> str:
        """Convert paragraph to Markdown.

        Preserves leading/trailing whitespace outside formatting markers.

        Returns:
            Text with inline formatting applied.

        Example:
            >>> para = ParagraphElement("This is text.", is_bold=True)
            >>> para.to_markdown()
            '**This is text.**'
            >>> para = ParagraphElement(" text ", is_bold=True)
            >>> para.to_markdown()
            ' **text** '
        """
        text = self.text

        # If no formatting needed, return as-is
        if not self.is_bold and not self.is_italic and not self.is_strikethrough:
            return text

        # Preserve leading/trailing whitespace
        stripped = text.strip()
        if not stripped:
            return text

        leading_space = text[: len(text) - len(text.lstrip())]
        trailing_space = text[len(text.rstrip()) :]

        # Apply inline formatting to stripped text
        if self.is_bold and self.is_italic:
            formatted = f"***{stripped}***"
        elif self.is_bold:
            formatted = f"**{stripped}**"
        elif self.is_italic:
            formatted = f"*{stripped}*"
        else:
            formatted = stripped
        
        # Apply strikethrough on top of other formatting
        if self.is_strikethrough:
            formatted = f"~~{formatted}~~"

        return leading_space + formatted + trailing_space


@dataclass
class LinkElement(Element):
    """Hyperlink element.

    Attributes:
        text: Link text (anchor text).
        url: URL target.
    """

    url: str = ""

    def to_markdown(self) -> str:
        """Convert link to Markdown.

        Returns:
            Markdown link [text](url).

        Example:
            >>> link = LinkElement("GitHub", url="https://github.com/")
            >>> link.to_markdown()
            '[GitHub](https://github.com/)'
        """
        return f"[{self.text}]({self.url})"


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
        max_font_size: float | None = None,
    ):
        """Initialize HeadingProcessor.

        Args:
            avg_font_size: Average font size in document (in points).
            heading_ratio: Font size multiplier for heading threshold.
                Default 1.3 means text 30% larger is a heading.
            max_level: Maximum heading level (1-6). Default 6.
            max_font_size: Maximum font size in document. If provided, ensures
                the largest heading font becomes H1.

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
        self.max_font_size = max_font_size
        self.threshold = avg_font_size * heading_ratio

        logger.debug(
            f"HeadingProcessor initialized: avg={avg_font_size:.1f}pt, "
            f"max={max_font_size:.1f}pt, threshold={self.threshold:.1f}pt"
            if max_font_size
            else f"HeadingProcessor initialized: avg={avg_font_size:.1f}pt, "
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
        y0 = span.get("y0", 0.0)
        x0 = span.get("x0", 0.0)
        page_number = span.get("page_number", 1)

        # Calculate size ratio
        size_ratio = font_size / self.avg_font_size

        # Only classify as heading if:
        # 1. Size is significantly larger (>= 1.15× body size), OR
        # 2. Bold AND size ratio >= 1.4 (40% larger)
        # This prevents inline bold/italic at body size from being headers
        is_heading = False
        if size_ratio >= 1.15:
            # Text is noticeably larger - likely a header
            is_heading = True
        elif is_bold and size_ratio >= 1.4:
            # Bold AND significantly larger - likely a header
            is_heading = True

        if is_heading:
            level = self._calculate_level(font_size, is_bold)
            logger.debug(
                f"Detected heading: '{text[:30]}...' "
                f"(size={font_size:.1f}pt, ratio={size_ratio:.2f}, level={level})"
            )
            return HeadingElement(
                text=text, level=level, y0=y0, x0=x0, page_number=page_number
            )

        # Regular paragraph (including inline bold/italic at body size)
        is_italic = span.get("is_italic", False)
        is_strikethrough = span.get("is_strikethrough", False)
        return ParagraphElement(
            text=text,
            y0=y0,
            x0=x0,
            page_number=page_number,
            is_bold=is_bold,
            is_italic=is_italic,
            is_strikethrough=is_strikethrough,
        )

    def _calculate_level(self, font_size: float, is_bold: bool) -> int:
        """Calculate heading level based on font size.

        Larger text gets lower level numbers (H1 = largest).
        Uses relative size ratios for better adaptability.

        Args:
            font_size: Font size of the text in points.
            is_bold: Whether the text is bold.

        Returns:
            Heading level from 1 (largest) to max_level.

        Note:
            Size ratio mapping (relative to body font):
            - >= 1.7× -> H1 (70% larger - major heading)
            - >= 1.4× -> H2 (40% larger - section)
            - >= 1.2× -> H3 (20% larger - subsection)
            - >= 1.08× -> H4 (8% larger)
            - >= 1.0× and bold -> H5 (same size, bold)
            - >= 0.95× and bold -> H6 (slightly smaller, bold)

            If max_font_size is provided, ensures the largest heading becomes H1.
        """
        size_ratio = font_size / self.avg_font_size

        # If max_font_size provided, check if this is the largest heading
        if self.max_font_size and font_size >= self.max_font_size * 0.95:
            # This is the largest (or nearly largest) font - make it H1
            return 1

        # Use ratio-based classification
        # Thresholds balanced for common PDF generators (Pandoc, Obsidian, etc.)
        if size_ratio >= 1.7:
            level = 1
        elif size_ratio >= 1.4:
            level = 2
        elif size_ratio >= 1.2:
            level = 3
        elif size_ratio >= 1.08:
            level = 4
        elif size_ratio >= 1.0 and is_bold:
            level = 5
        elif size_ratio >= 0.95 and is_bold:
            level = 6
        elif is_bold:
            level = 6
        else:
            # Not bold and not significantly larger - should not be a heading
            # This shouldn't happen because process() filters these out
            level = 6

        # Ensure within max_level
        level = min(level, self.max_level)

        return level
