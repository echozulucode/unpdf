"""Element detection and counting for Markdown documents.

This module provides functionality to detect and count different element types
in Markdown documents for accuracy measurement.

Style: Google docstrings, black formatting
"""

import re
from dataclasses import dataclass
from enum import Enum


class ElementType(Enum):
    """Types of elements that can be detected in Markdown."""

    HEADER = "header"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    IMAGE = "image"
    LINK = "link"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "horizontal_rule"
    INLINE_CODE = "inline_code"
    BOLD = "bold"
    ITALIC = "italic"


@dataclass
class Element:
    """Represents a detected element in a Markdown document.

    Attributes:
        type: The type of element (header, paragraph, etc.)
        content: The text content of the element
        line_number: The line number where this element starts
        level: Optional level information (e.g., header level, list nesting)
        metadata: Additional element-specific metadata
    """

    type: ElementType
    content: str
    line_number: int
    level: int = 0
    metadata: dict | None = None

    def __post_init__(self) -> None:
        """Initialize metadata dict if None."""
        if self.metadata is None:
            self.metadata = {}


class ElementDetector:
    r"""Detects and counts elements in Markdown documents.

    This class analyzes Markdown text and identifies different element types,
    their positions, and characteristics for accuracy measurement.

    Example:
        >>> detector = ElementDetector()
        >>> elements = detector.detect("# Hello\n\nWorld")
        >>> len(elements)
        2
    """

    def __init__(self) -> None:
        """Initialize the element detector."""
        self._in_code_block = False
        self._code_block_fence = None

    def detect(self, markdown_text: str) -> list[Element]:
        """Detect all elements in the given Markdown text.

        Args:
            markdown_text: The Markdown text to analyze

        Returns:
            List of detected Element objects
        """
        elements = []
        lines = markdown_text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for code blocks first (they contain other syntax)
            if self._is_code_fence(line):
                code_block, block_length = self._extract_code_block(lines, i)
                if code_block:
                    elements.append(code_block)
                    i += block_length
                    continue

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Try to detect element type
            element = self._detect_line_element(line, i + 1)
            if element:
                elements.append(element)

            i += 1

        return elements

    def count_by_type(self, elements: list[Element]) -> dict:
        """Count elements by their type.

        Args:
            elements: List of elements to count

        Returns:
            Dictionary mapping ElementType to count
        """
        counts = dict.fromkeys(ElementType, 0)
        for element in elements:
            counts[element.type] += 1
        return counts

    def _detect_line_element(self, line: str, line_number: int) -> Element:
        """Detect what type of element a line represents.

        Args:
            line: The line to analyze
            line_number: The line number in the document

        Returns:
            Element object or None if no element detected
        """
        stripped = line.strip()

        # Headers (ATX style: # Header)
        if match := re.match(r"^(#{1,6})\s+(.+)$", stripped):
            level = len(match.group(1))
            content = match.group(2)
            return Element(
                type=ElementType.HEADER,
                content=content,
                line_number=line_number,
                level=level,
            )

        # Horizontal rule
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", stripped):
            return Element(
                type=ElementType.HORIZONTAL_RULE,
                content=stripped,
                line_number=line_number,
            )

        # List items (unordered and ordered)
        if match := re.match(r"^(\s*)([-*+]|\d+\.)\s+(.+)$", stripped):
            indent = len(match.group(1))
            level = indent // 2  # Assume 2 spaces per level
            content = match.group(3)
            return Element(
                type=ElementType.LIST_ITEM,
                content=content,
                line_number=line_number,
                level=level,
            )

        # Blockquote
        if match := re.match(r"^>\s*(.*)$", stripped):
            content = match.group(1)
            return Element(
                type=ElementType.BLOCKQUOTE,
                content=content,
                line_number=line_number,
            )

        # Table row (contains |)
        if "|" in stripped:
            return Element(
                type=ElementType.TABLE,
                content=stripped,
                line_number=line_number,
            )

        # Image
        if match := re.match(r"!\[([^\]]*)\]\(([^\)]+)\)", stripped):
            alt_text = match.group(1)
            url = match.group(2)
            return Element(
                type=ElementType.IMAGE,
                content=alt_text,
                line_number=line_number,
                metadata={"url": url, "alt": alt_text},
            )

        # Regular paragraph (default)
        return Element(
            type=ElementType.PARAGRAPH,
            content=stripped,
            line_number=line_number,
        )

    def _is_code_fence(self, line: str) -> bool:
        """Check if a line is a code fence (``` or ~~~).

        Args:
            line: The line to check

        Returns:
            True if the line is a code fence
        """
        stripped = line.strip()
        return bool(re.match(r"^(`{3,}|~{3,})", stripped))

    def _extract_code_block(
        self, lines: list[str], start_index: int
    ) -> tuple[Element | None, int]:
        """Extract a complete code block starting at the given index.

        Args:
            lines: All lines in the document
            start_index: Index of the opening fence

        Returns:
            Tuple of (Element, number of lines consumed) or (None, 0)
        """
        opening_line = lines[start_index].strip()
        fence_match = re.match(r"^(`{3,}|~{3,})(\w+)?", opening_line)
        if not fence_match:
            return None, 0

        fence_char = fence_match.group(1)[0]
        language = fence_match.group(2) or ""

        # Find closing fence
        content_lines: list[str] = []
        i = start_index + 1
        while i < len(lines):
            line = lines[i]
            if re.match(f"^{fence_char}{{3,}}\\s*$", line.strip()):
                # Found closing fence
                content = "\n".join(content_lines)
                element = Element(
                    type=ElementType.CODE_BLOCK,
                    content=content,
                    line_number=start_index + 1,
                    metadata={"language": language},
                )
                return element, i - start_index + 1
            content_lines.append(line)
            i += 1

        # No closing fence found, treat as malformed
        return None, 0

    def count_inline_elements(self, markdown_text: str) -> dict:
        """Count inline formatting elements (bold, italic, code, links).

        Args:
            markdown_text: The Markdown text to analyze

        Returns:
            Dictionary with counts of inline elements
        """
        counts = {
            "bold": 0,
            "italic": 0,
            "inline_code": 0,
            "links": 0,
        }

        # Bold: **text** or __text__
        counts["bold"] = len(re.findall(r"\*\*[^*]+\*\*|__[^_]+__", markdown_text))

        # Italic: *text* or _text_ (but not bold)
        counts["italic"] = len(
            re.findall(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)|(?<!_)_(?!_)([^_]+)_(?!_)", markdown_text)
        )

        # Inline code: `code`
        counts["inline_code"] = len(re.findall(r"`[^`]+`", markdown_text))

        # Links: [text](url)
        counts["links"] = len(re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", markdown_text))

        return counts
