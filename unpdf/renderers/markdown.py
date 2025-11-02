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


def render_spans_to_markdown(spans: list[dict[str, Any]]) -> str:
    """Render text spans with metadata to Markdown format.

    Applies inline formatting (bold, italic) based on font metadata.
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
        formatted_text = _apply_inline_formatting(text, is_bold, is_italic)
        current_paragraph.append(formatted_text)

        last_y_position = y_position

    # Don't forget last paragraph
    if current_paragraph:
        markdown_parts.append("".join(current_paragraph))

    # Join paragraphs with blank lines
    return "\n\n".join(markdown_parts)


def _apply_inline_formatting(text: str, is_bold: bool, is_italic: bool) -> str:
    """Apply Markdown inline formatting to text.

    Args:
        text: Text to format.
        is_bold: Whether to apply bold formatting.
        is_italic: Whether to apply italic formatting.

    Returns:
        Text with Markdown formatting applied.

    Example:
        >>> _apply_inline_formatting("Hello", True, False)
        '**Hello**'
        >>> _apply_inline_formatting("Hello", True, True)
        '***Hello***'
    """
    if not text.strip():
        return text

    # Handle combined formatting
    if is_bold and is_italic:
        return f"***{text}***"
    elif is_bold:
        return f"**{text}**"
    elif is_italic:
        return f"*{text}*"
    else:
        return text
