"""Text extraction with font metadata for unpdf.

This module extracts text from PDFs along with font information (size, family,
weight, style) needed for downstream classification and formatting.

Example:
    >>> from pathlib import Path
    >>> from unpdf.extractors.text import extract_text_with_metadata
    >>>
    >>> spans = extract_text_with_metadata(Path("document.pdf"))
    >>> for span in spans[:3]:
    ...     print(f"{span['text']}: {span['font_size']}pt")
    Document Title: 24.0pt
    First paragraph text...: 12.0pt
    Second paragraph...: 12.0pt
"""

import logging
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_with_metadata(
    pdf_path: Path, page_numbers: list[int] | None = None
) -> list[dict[str, Any]]:
    """Extract text spans with font metadata from PDF.

    Reads the PDF and extracts each text span along with its font information.
    This metadata is crucial for later classification (headings, code, etc.).

    Args:
        pdf_path: Path to the PDF file to process.
        page_numbers: Optional list of specific page numbers (1-indexed) to process.
            If None, processes all pages.

    Returns:
        List of dictionaries, one per text span, containing:
            - text (str): The actual text content.
            - font_size (float): Font size in points.
            - font_family (str): Font family name (e.g., "Helvetica").
            - is_bold (bool): Whether text appears bold.
            - is_italic (bool): Whether text appears italic.
            - x0 (float): Left x coordinate.
            - y0 (float): Bottom y coordinate.
            - x1 (float): Right x coordinate.
            - y1 (float): Top y coordinate.
            - page_number (int): Page number (1-indexed).

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If PDF is corrupted or unreadable.

    Example:
        >>> spans = extract_text_with_metadata(Path("doc.pdf"))
        >>> print(spans[0])
        {
            'text': 'Document Title',
            'font_size': 24.0,
            'font_family': 'Helvetica-Bold',
            'is_bold': True,
            'is_italic': False,
            'x0': 72.0, 'y0': 720.0, 'x1': 540.0, 'y1': 750.0,
            'page_number': 1
        }

    Note:
        Font detection relies on PDF metadata. Some PDFs may not have
        accurate font information, especially if poorly generated.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    spans: list[dict[str, Any]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Determine which pages to process
            if page_numbers:
                page_indices = [p - 1 for p in page_numbers]  # Convert to 0-indexed
                pages_to_process = [
                    pdf.pages[i] for i in page_indices if i < len(pdf.pages)
                ]
            else:
                pages_to_process = pdf.pages

            logger.info(
                f"Processing {len(pages_to_process)} page(s) from {pdf_path.name}"
            )

            for page_num, page in enumerate(pages_to_process, start=1):
                # Extract characters with detailed metadata
                chars = page.chars

                if not chars:
                    logger.debug(f"Page {page_num}: No text found")
                    continue

                # Group characters into text spans
                # For now, we'll create one span per character run with same formatting
                current_span: dict[str, Any] | None = None

                for char in chars:
                    text = char.get("text", "")
                    if not text.strip():  # Skip pure whitespace
                        # But preserve it in current span if building one
                        if current_span:
                            current_span["text"] += text
                        continue

                    font_name = char.get("fontname", "")
                    font_size = char.get("size", 12.0)

                    # Detect bold and italic from font name
                    is_bold = _is_bold_font(font_name)
                    is_italic = _is_italic_font(font_name)

                    # Check if we should continue current span or start new one
                    if current_span and _should_continue_span(
                        current_span, font_name, font_size, is_bold, is_italic
                    ):
                        # Continue current span
                        current_span["text"] += text
                        current_span["x1"] = char.get("x1", current_span["x1"])
                    else:
                        # Save previous span if exists
                        if current_span and current_span["text"].strip():
                            spans.append(current_span)

                        # Start new span
                        current_span = {
                            "text": text,
                            "font_size": font_size,
                            "font_family": font_name,
                            "is_bold": is_bold,
                            "is_italic": is_italic,
                            "x0": char.get("x0", 0),
                            "y0": char.get("y0", 0),
                            "x1": char.get("x1", 0),
                            "y1": char.get("y1", 0),
                            "page_number": page_num,
                        }

                # Don't forget the last span
                if current_span and current_span["text"].strip():
                    spans.append(current_span)

        logger.info(f"Extracted {len(spans)} text span(s)")
        return spans

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}") from e


def _is_bold_font(font_name: str) -> bool:
    """Detect if font is bold based on font name.

    Args:
        font_name: Font name string.

    Returns:
        True if font appears to be bold.
    """
    font_lower = font_name.lower()
    return any(
        indicator in font_lower
        for indicator in ["bold", "heavy", "black", "semibold", "demibold"]
    )


def _is_italic_font(font_name: str) -> bool:
    """Detect if font is italic based on font name.

    Args:
        font_name: Font name string.

    Returns:
        True if font appears to be italic.
    """
    font_lower = font_name.lower()
    return any(
        indicator in font_lower for indicator in ["italic", "oblique", "cursive"]
    )


def _should_continue_span(
    current_span: dict[str, Any],
    font_name: str,
    font_size: float,
    is_bold: bool,
    is_italic: bool,
) -> bool:
    """Determine if new character should continue current span or start new one.

    Args:
        current_span: Current text span being built.
        font_name: Font name of new character.
        font_size: Font size of new character.
        is_bold: Whether new character is bold.
        is_italic: Whether new character is italic.

    Returns:
        True if should continue current span, False to start new span.
    """
    # Continue if all formatting matches
    return bool(
        current_span["font_family"] == font_name
        and abs(current_span["font_size"] - font_size) < 0.1
        and current_span["is_bold"] == is_bold
        and current_span["is_italic"] == is_italic
    )


def calculate_average_font_size(spans: list[dict[str, Any]]) -> float:
    """Calculate average font size from text spans.

    Args:
        spans: List of text spans with font metadata.

    Returns:
        Average font size in points. Returns 12.0 if no spans.

    Example:
        >>> spans = extract_text_with_metadata(Path("doc.pdf"))
        >>> avg_size = calculate_average_font_size(spans)
        >>> print(f"Average font size: {avg_size:.1f}pt")
        Average font size: 11.5pt
    """
    if not spans:
        return 12.0  # Default

    # Weight by text length to avoid letting small annotations skew average
    total_weighted_size = 0.0
    total_length = 0

    for span in spans:
        text_length = len(span["text"])
        total_weighted_size += span["font_size"] * text_length
        total_length += text_length

    if total_length == 0:
        return 12.0

    return total_weighted_size / total_length
