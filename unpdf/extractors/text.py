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
import pymupdf  # type: ignore[import-untyped]

from unpdf.processors.checkboxes import CheckboxDetector

logger = logging.getLogger(__name__)


def extract_tables(
    pdf_path: Path, page_numbers: list[int] | None = None
) -> list[dict[str, Any]]:
    """Extract tables from PDF with position metadata.

    Args:
        pdf_path: Path to the PDF file to process.
        page_numbers: Optional list of specific page numbers (1-indexed) to process.
            If None, processes all pages.

    Returns:
        List of dictionaries, one per table, containing:
            - data (list[list[str]]): Table data as 2D list.
            - bbox (tuple): Bounding box (x0, y0, x1, y1).
            - page_number (int): Page number (1-indexed).

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If PDF is corrupted or unreadable.

    Example:
        >>> tables = extract_tables(Path("doc.pdf"))
        >>> print(f"Found {len(tables)} table(s)")
        Found 2 table(s)
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    tables: list[dict[str, Any]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Determine which pages to process
            if page_numbers:
                page_indices = [p - 1 for p in page_numbers]
                pages_to_process = [
                    (page_numbers[i], pdf.pages[idx])
                    for i, idx in enumerate(page_indices)
                    if idx < len(pdf.pages)
                ]
            else:
                pages_to_process = [(i + 1, page) for i, page in enumerate(pdf.pages)]

            for page_num, page in pages_to_process:
                page_tables = page.find_tables()

                for table in page_tables:
                    extracted = table.extract()
                    if extracted:
                        tables.append(
                            {
                                "data": extracted,
                                "bbox": table.bbox,
                                "page_number": page_num,
                            }
                        )

        logger.info(f"Extracted {len(tables)} table(s)")
        return tables

    except Exception as e:
        logger.error(f"Error extracting tables from {pdf_path}: {e}")
        raise ValueError(f"Failed to extract tables from PDF: {e}") from e


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
    checkbox_detector = CheckboxDetector()

    # Open PyMuPDF document for checkbox detection
    pymupdf_doc = pymupdf.open(str(pdf_path))

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
                # Detect checkboxes on this page using PyMuPDF
                pymupdf_page = pymupdf_doc[page_num - 1]
                page_checkboxes = checkbox_detector.detect_checkboxes(pymupdf_page)
                logger.debug(
                    f"Page {page_num}: Detected {len(page_checkboxes)} checkboxes"
                )

                # Extract characters with detailed metadata
                chars = page.chars

                if not chars:
                    logger.debug(f"Page {page_num}: No text found")
                    continue

                # Group characters into text spans
                # For now, we'll create one span per character run with same formatting
                current_span: dict[str, Any] | None = None
                prev_char_x1 = None

                for char in chars:
                    text = char.get("text", "")
                    char_x0 = char.get("x0", 0)

                    # Add space between words if there's a horizontal gap
                    if (
                        current_span
                        and prev_char_x1 is not None
                        and char_x0 - prev_char_x1 > 2.0  # Gap threshold
                    ):
                        current_span["text"] += " "

                    if not text.strip():  # Skip pure whitespace
                        # But preserve it in current span if building one
                        if current_span:
                            current_span["text"] += text
                        prev_char_x1 = char.get("x1", prev_char_x1)
                        continue

                    font_name = char.get("fontname", "")
                    font_size = char.get("size", 12.0)

                    # Detect bold and italic from font name
                    is_bold = _is_bold_font(font_name)
                    is_italic = _is_italic_font(font_name)

                    # Check if we should continue current span or start new one
                    if current_span and _should_continue_span(
                        current_span, font_name, font_size, is_bold, is_italic, char
                    ):
                        # Continue current span
                        current_span["text"] += text
                        current_span["x1"] = char.get("x1", current_span["x1"])
                        prev_char_x1 = char.get("x1", prev_char_x1)
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
                        prev_char_x1 = char.get("x1", 0)

                # Don't forget the last span
                if current_span and current_span["text"].strip():
                    spans.append(current_span)

                # Annotate spans with checkboxes for this page
                # Filter spans for this page
                page_start_idx = len(spans) - sum(
                    1 for s in spans if s["page_number"] == page_num
                )
                page_spans = spans[page_start_idx:]

                if page_checkboxes and page_spans:
                    # Get page height for coordinate conversion
                    page_height = page.height
                    annotated = checkbox_detector.annotate_text_with_checkboxes(
                        page_spans, page_checkboxes, page_height
                    )
                    # Update the spans in place
                    spans[page_start_idx:] = annotated

        logger.info(f"Extracted {len(spans)} text span(s) before filtering")
        
        # Filter out page numbers (text near top/bottom margins that are just numbers)
        filtered_spans = _filter_page_numbers(spans, pdf.pages)
        logger.info(f"After filtering: {len(filtered_spans)} text span(s)")
        
        return filtered_spans

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}") from e
    finally:
        pymupdf_doc.close()


def _filter_page_numbers(spans: list[dict[str, Any]], pages: list) -> list[dict[str, Any]]:
    """Filter out likely page numbers from spans.
    
    Page numbers are typically:
    - Short (1-4 characters)
    - Numeric
    - Located near page edges (top or bottom margin)
    - Isolated (not near other text)
    
    Args:
        spans: List of text spans
        pages: List of pages for dimension info
        
    Returns:
        Filtered list of spans without page numbers
    """
    if not spans:
        return spans
    
    # Build page dimensions map
    page_dims = {}
    for i, page in enumerate(pages, start=1):
        page_dims[i] = {
            'width': page.width,
            'height': page.height,
        }
    
    filtered = []
    for span in spans:
        text = span['text'].strip()
        page_num = span['page_number']
        
        # Get page dimensions
        if page_num not in page_dims:
            filtered.append(span)
            continue
        
        page_height = page_dims[page_num]['height']
        y0 = span['y0']  # In pdfplumber, y0 is from top of page (y0=0 at top)
        
        # Check if this looks like a page number
        is_short = len(text) <= 4
        is_numeric = text.isdigit() or text.replace('.', '').isdigit()
        
        # Near top (within 100 points from top edge, y0 < 100)
        near_top = y0 < 100
        
        # Near bottom (within 100 points from bottom edge, y0 > height - 100)
        near_bottom = y0 > (page_height - 100)
        
        # If it's short, numeric, and near an edge, likely a page number
        if is_short and is_numeric and (near_bottom or near_top):
            logger.debug(f"Filtering page number: '{text}' at y={y0} (page height={page_height})")
            continue
        
        filtered.append(span)
    
    return filtered


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
    char: dict[str, Any],
) -> bool:
    """Determine if new character should continue current span or start new one.

    Args:
        current_span: Current text span being built.
        font_name: Font name of new character.
        font_size: Font size of new character.
        is_bold: Whether new character is bold.
        is_italic: Whether new character is italic.
        char: Character dictionary with position info.

    Returns:
        True if should continue current span, False to start new span.
    """
    # Check for line break (significant vertical distance)
    char_y0 = char.get("y0", 0)
    if abs(char_y0 - current_span["y0"]) > 2.0:
        return False

    # Continue if all formatting matches
    return bool(
        current_span["font_family"] == font_name
        and abs(current_span["font_size"] - font_size) < 0.1
        and current_span["is_bold"] == is_bold
        and current_span["is_italic"] == is_italic
    )


def calculate_average_font_size(spans: list[dict[str, Any]]) -> float:
    """Calculate the most common (body) font size from text spans.

    Uses the most frequently occurring font size rather than arithmetic average,
    since we want to identify the body text size, not be skewed by headers.

    Args:
        spans: List of text spans with font metadata.

    Returns:
        Most common font size in points. Returns 12.0 if no spans.

    Example:
        >>> spans = extract_text_with_metadata(Path("doc.pdf"))
        >>> body_size = calculate_average_font_size(spans)
        >>> print(f"Body font size: {body_size:.1f}pt")
        Body font size: 11.5pt
    """
    if not spans:
        return 12.0  # Default

    # Count occurrences of each font size (weighted by character count)
    size_weights: dict[float, int] = {}

    for span in spans:
        size = span["font_size"]
        text_length = len(span["text"])
        size_weights[size] = size_weights.get(size, 0) + text_length

    if not size_weights:
        return 12.0

    # Return the size with the highest total character count
    most_common_size = max(size_weights.items(), key=lambda x: x[1])[0]
    return most_common_size


def calculate_max_font_size(spans: list[dict[str, Any]]) -> float:
    """Calculate the maximum font size from text spans.

    This helps identify the largest heading font in the document.

    Args:
        spans: List of text spans with font metadata.

    Returns:
        Maximum font size in points. Returns 12.0 if no spans.

    Example:
        >>> spans = extract_text_with_metadata(Path("doc.pdf"))
        >>> max_size = calculate_max_font_size(spans)
        >>> print(f"Max font size: {max_size:.1f}pt")
        Max font size: 24.0pt
    """
    if not spans:
        return 12.0  # Default

    max_size = max((span["font_size"] for span in spans), default=12.0)
    return max_size
