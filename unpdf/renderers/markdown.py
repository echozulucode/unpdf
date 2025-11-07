"""Markdown rendering for unpdf.

This module converts text spans with metadata into formatted Markdown output.

Example:
    >>> from unpdf.renderers.markdown import render_spans_to_markdown
    >>> markdown = render_spans_to_markdown(spans)
    >>> print(markdown)
    # Document Title

    This is **bold** text and this is *italic* text.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def render_elements_to_markdown(elements: list[Any]) -> str:
    """Render document elements to Markdown format.

    Converts structured elements (headings, lists, paragraphs, tables) to Markdown.

    Args:
        elements: List of Element objects (HeadingElement, ListItemElement,
                 TableElement, etc.).

    Returns:
        Formatted Markdown string.

    Example:
        >>> from unpdf.processors.headings import HeadingElement, ParagraphElement
        >>> elements = [
        ...     HeadingElement("Title", level=1),
        ...     ParagraphElement("Text here")
        ... ]
        >>> print(render_elements_to_markdown(elements))
        # Title
        <BLANKLINE>
        Text here
    """
    if not elements:
        return ""

    markdown_parts: list[str] = []

    for idx, element in enumerate(elements):
        # Get markdown representation from element
        md_text = element.to_markdown()

        element_type = element.__class__.__name__

        # Add spacing logic:
        # - Blank lines around headings and tables
        # - Blank lines between paragraphs on different lines
        if element_type in ("HeadingElement", "TableElement"):
            # Blank line before (except first element)
            if markdown_parts:
                markdown_parts.append("")
            markdown_parts.append(md_text)
            # Blank line after
            markdown_parts.append("")
        elif element_type == "ParagraphElement":
            # Add blank line between consecutive paragraphs if on different lines
            if idx > 0:
                prev_element = elements[idx - 1]
                if prev_element.__class__.__name__ == "ParagraphElement":
                    # Check vertical distance
                    curr_y = getattr(element, "y0", 0)
                    prev_y = getattr(prev_element, "y0", 0)

                    # If vertical distance > 5 points, separate paragraphs
                    if abs(curr_y - prev_y) > 5:
                        markdown_parts.append("")
            markdown_parts.append(md_text)
        else:
            markdown_parts.append(md_text)

    # Join with newlines
    result = "\n".join(markdown_parts)

    # Clean up multiple consecutive blank lines
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")

    return result.strip()


def render_spans_to_markdown(spans: list[dict[str, Any]]) -> str:
    """Render text spans with metadata to Markdown format.

    Applies inline formatting (bold, italic, strikethrough) based on font metadata.
    Groups text into paragraphs with blank line separation.

    Args:
        spans: List of text spans with font metadata from extractor.

    Returns:
        Formatted Markdown string.

    Example:
        >>> spans = [
        ...     {'text': 'Hello', 'is_bold': True, 'is_italic': False},
        ...     {'text': ' world', 'is_bold': False, 'is_italic': True}
        ... ]
        >>> print(render_spans_to_markdown(spans))
        **Hello** *world*
    """
    if not spans:
        return ""

    markdown_parts: list[str] = []
    current_paragraph: list[str] = []
    last_y_position = None

    for span in spans:
        text = span["text"]
        is_bold = span.get("is_bold", False)
        is_italic = span.get("is_italic", False)
        is_strikethrough = span.get("strikethrough", False)
        y_position = span.get("y0", 0)

        # Detect paragraph break (significant vertical gap)
        if last_y_position is not None:
            # Negative because PDF coordinates go bottom-up
            vertical_gap = last_y_position - y_position
            # Significant gap = new paragraph
            if vertical_gap > 10 and current_paragraph:
                markdown_parts.append("".join(current_paragraph))
                current_paragraph = []

        # Apply inline formatting
        formatted_text = _apply_inline_formatting(text, is_bold, is_italic, is_strikethrough)
        current_paragraph.append(formatted_text)

        last_y_position = y_position

    # Don't forget last paragraph
    if current_paragraph:
        markdown_parts.append("".join(current_paragraph))

    # Join paragraphs with blank lines
    return "\n\n".join(markdown_parts)


def _apply_inline_formatting(
    text: str, is_bold: bool, is_italic: bool, is_strikethrough: bool = False
) -> str:
    """Apply Markdown inline formatting to text.

    Preserves leading/trailing whitespace outside the formatting markers.

    Args:
        text: Text to format.
        is_bold: Whether to apply bold formatting.
        is_italic: Whether to apply italic formatting.
        is_strikethrough: Whether to apply strikethrough formatting.

    Returns:
        Text with Markdown formatting applied.

    Example:
        >>> _apply_inline_formatting("Hello", True, False, False)
        '**Hello**'
        >>> _apply_inline_formatting("Hello", True, True, False)
        '***Hello***'
        >>> _apply_inline_formatting("Hello", False, False, True)
        '~~Hello~~'
        >>> _apply_inline_formatting(" Hello ", True, False, False)
        ' **Hello** '
    """
    if not text.strip():
        return text

    # Preserve leading/trailing whitespace
    stripped = text.strip()
    leading_space = text[: len(text) - len(text.lstrip())]
    trailing_space = text[len(text.rstrip()) :]

    # Handle combined formatting (order: strikethrough > bold > italic)
    formatted = stripped
    
    if is_italic:
        formatted = f"*{formatted}*"
    if is_bold:
        formatted = f"**{formatted}**"
    if is_strikethrough:
        formatted = f"~~{formatted}~~"

    return leading_space + formatted + trailing_space
