"""Core conversion pipeline for unpdf.

This module orchestrates the PDF-to-Markdown conversion process through
a simple three-stage pipeline:
    1. Extract: Pull content from PDF (text, tables, images)
    2. Process: Classify and transform content (headings, lists, code)
    3. Render: Output as Markdown

Example:
    >>> from unpdf import convert_pdf
    >>> markdown = convert_pdf("document.pdf")
    >>> print(markdown[:100])
    # Document Title

    First paragraph of the document...
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unpdf.processors.code import CodeBlockElement, InlineCodeElement
    from unpdf.processors.headings import ParagraphElement
    from unpdf.processors.table import TableElement

logger = logging.getLogger(__name__)


def _merge_spans_on_same_line(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge consecutive spans that are on the same line ONLY when appropriate.

    This merges spans in specific cases:
    - List markers (bullets/numbers) with adjacent text
    - Checkboxes with adjacent text
    
    Regular text with different formatting (bold, italic) is kept separate
    to preserve inline formatting.

    Args:
        spans: List of text span dictionaries

    Returns:
        List of merged spans
    """
    if not spans:
        return spans

    merged = []
    i = 0
    
    while i < len(spans):
        current = spans[i]
        
        # Check if this is a list marker or checkbox that should be merged with next span
        should_merge_with_next = False
        if i + 1 < len(spans):
            next_span = spans[i + 1]
            
            # Check if on same line
            same_line = (
                abs(current.get("y0", 0) - next_span.get("y0", 0)) < 2
                and current.get("page_number", 1) == next_span.get("page_number", 1)
            )
            
            if same_line:
                current_text = current["text"].strip()
                
                # Merge if current is a list marker
                import re
                is_bullet = current_text in ["•", "●", "○", "◦", "▪", "▫", "–", "-", "·", "►", "➢"]
                is_number = bool(re.match(r"^\d+\.$", current_text))
                is_checkbox = current_text.startswith("☐") or current_text.startswith("☑") or current_text.startswith("☒")
                
                should_merge_with_next = is_bullet or is_number or is_checkbox
        
        if should_merge_with_next:
            # Merge current with next
            next_span = spans[i + 1]
            merged_span = {
                "text": current["text"] + next_span["text"],
                "font_size": next_span.get("font_size", current.get("font_size", 12.0)),
                "font_family": next_span.get("font_family", current.get("font_family", "")),
                "is_bold": next_span.get("is_bold", False),
                "is_italic": next_span.get("is_italic", False),
                "x0": current.get("x0", 0),
                "y0": current.get("y0", 0),
                "x1": next_span.get("x1", 0),
                "y1": next_span.get("y1", 0),
                "page_number": current.get("page_number", 1),
            }
            # Copy other fields from next span (like strikethrough, etc.)
            for key in next_span:
                if key not in merged_span:
                    merged_span[key] = next_span[key]
            
            merged.append(merged_span)
            i += 2  # Skip both spans
        else:
            # Keep span as-is
            merged.append(current)
            i += 1

    return merged


def _merge_inline_code_into_paragraphs(elements: list[Any]) -> list[Any]:
    """Merge inline code elements into adjacent paragraphs.

    When inline code appears on the same line as paragraph text, it should
    be embedded within the paragraph rather than being a separate element.

    Args:
        elements: List of processed elements

    Returns:
        List with inline code elements merged into paragraphs where appropriate
    """
    from unpdf.processors.code import InlineCodeElement
    from unpdf.processors.headings import ParagraphElement

    if not elements:
        return elements

    # First pass: merge consecutive paragraph elements on same line
    merged_paras: list[Any] = []
    i = 0
    while i < len(elements):
        current = elements[i]

        # Check if this is a paragraph that can be merged with next paragraphs
        if isinstance(current, ParagraphElement):
            # Collect all consecutive paragraphs on the same line
            line_paras = [current]
            j = i + 1
            while j < len(elements):
                next_elem = elements[j]
                if isinstance(next_elem, ParagraphElement):
                    # Check if on same line (within 5 points vertically)
                    if (
                        hasattr(current, "y0")
                        and hasattr(next_elem, "y0")
                        and abs(current.y0 - next_elem.y0) < 5
                        and getattr(current, "page_number", 0)
                        == getattr(next_elem, "page_number", 0)
                    ):
                        line_paras.append(next_elem)
                        j += 1
                    else:
                        break
                else:
                    break

            # Merge if we found multiple paragraphs on same line
            if len(line_paras) > 1:
                # Build inline formatted text by combining spans intelligently
                # Key insight: PDF extracts spaces as part of spans, so we need to
                # normalize spacing between formatted pieces
                parts = []
                for idx, para in enumerate(line_paras):
                    text = para.text
                    stripped = text.strip()

                    # Skip empty spans
                    if not stripped:
                        # Keep single space between non-empty spans
                        if parts and idx < len(line_paras) - 1:
                            # Check if next span has content
                            next_text = line_paras[idx + 1].text.strip()
                            if next_text:
                                # Add space only if we don't already have one
                                if not parts[-1].endswith(" "):
                                    parts.append(" ")
                        continue

                    # Apply formatting to stripped text
                    if para.is_bold and para.is_italic:
                        formatted = f"***{stripped}***"
                    elif para.is_bold:
                        formatted = f"**{stripped}**"
                    elif para.is_italic:
                        formatted = f"*{stripped}*"
                    else:
                        formatted = stripped
                    
                    # Apply strikethrough on top of other formatting
                    if para.is_strikethrough:
                        formatted = f"~~{formatted}~~"

                    # Add space before if needed (not first part, and previous doesn't end with space)
                    if parts and not parts[-1].endswith(" ") and text.startswith(" "):
                        parts.append(" ")

                    parts.append(formatted)

                    # Add space after if original had trailing space and not last part
                    if text.endswith(" ") and idx < len(line_paras) - 1:
                        # Check if next part starts with space or is empty
                        next_text = line_paras[idx + 1].text
                        if not next_text.startswith(" ") and next_text.strip():
                            parts.append(" ")

                # Join parts
                combined_text = "".join(parts)

                # Create merged paragraph with NO formatting (already applied)
                merged_para = ParagraphElement(
                    text=combined_text,
                    y0=current.y0,
                    x0=getattr(current, "x0", 0),
                    page_number=getattr(current, "page_number", 1),
                    is_bold=False,  # Already formatted
                    is_italic=False,
                )
                merged_paras.append(merged_para)
                i = j
            else:
                merged_paras.append(current)
                i += 1
        else:
            merged_paras.append(current)
            i += 1

    # Second pass: merge inline code into paragraphs
    merged: list[Any] = []
    i = 0

    while i < len(merged_paras):
        current = merged_paras[i]

        # Check if this is a paragraph followed by inline code on same line
        if isinstance(current, ParagraphElement) and i + 1 < len(merged_paras):
            next_elem = merged_paras[i + 1]

            if isinstance(next_elem, InlineCodeElement):
                # Check if they're on the same line (within 5 points vertically)
                if (
                    hasattr(current, "y0")
                    and hasattr(next_elem, "y0")
                    and abs(current.y0 - next_elem.y0) < 5
                    and getattr(current, "page_number", 0)
                    == getattr(next_elem, "page_number", 0)
                ):
                    # Merge inline code into paragraph
                    # Clean up whitespace around code
                    before_text = current.text.rstrip()
                    code_text = next_elem.text.strip()
                    merged_text = f"{before_text} `{code_text}`"

                    # Check if there's more text after the inline code
                    if i + 2 < len(merged_paras):
                        after_elem = merged_paras[i + 2]
                        if (
                            isinstance(after_elem, ParagraphElement)
                            and hasattr(after_elem, "y0")
                            and abs(next_elem.y0 - after_elem.y0) < 5
                            and getattr(next_elem, "page_number", 0)
                            == getattr(after_elem, "page_number", 0)
                        ):
                            # Merge all three: para + code + para
                            after_text = after_elem.text.lstrip()
                            # Check if we need a space before after_text
                            if after_text and after_text[0] not in ".,;:!?)]}":
                                merged_text = f"{before_text} `{code_text}` {after_text}"
                            else:
                                merged_text = f"{before_text} `{code_text}`{after_text}"
                            merged_para = ParagraphElement(
                                text=merged_text,
                                y0=current.y0,
                                x0=getattr(current, "x0", 0),
                                page_number=getattr(current, "page_number", 1),
                            )
                            merged.append(merged_para)
                            i += 3
                            continue

                    # Just para + code
                    merged_para = ParagraphElement(
                        text=merged_text,
                        y0=current.y0,
                        x0=getattr(current, "x0", 0),
                        page_number=getattr(current, "page_number", 1),
                    )
                    merged.append(merged_para)
                    i += 2
                    continue

        # Check if this is inline code followed by paragraph on same line
        if isinstance(current, InlineCodeElement) and i + 1 < len(merged_paras):
            next_elem = merged_paras[i + 1]

            if isinstance(next_elem, ParagraphElement):
                # Check if they're on the same line
                if (
                    hasattr(current, "y0")
                    and hasattr(next_elem, "y0")
                    and abs(current.y0 - next_elem.y0) < 5
                    and getattr(current, "page_number", 0)
                    == getattr(next_elem, "page_number", 0)
                ):
                    # Merge inline code into paragraph
                    code_text = current.text.strip()
                    after_text = next_elem.text.lstrip()
                    # Check if we need a space before after_text
                    if after_text and after_text[0] not in ".,;:!?)]}":
                        merged_text = f"`{code_text}` {after_text}"
                    else:
                        merged_text = f"`{code_text}`{after_text}"
                    merged_para = ParagraphElement(
                        text=merged_text,
                        y0=current.y0,
                        x0=getattr(current, "x0", 0),
                        page_number=getattr(current, "page_number", 1),
                    )
                    merged.append(merged_para)
                    i += 2
                    continue

        # No merging, keep as-is
        merged.append(current)
        i += 1

    return merged


def _reconstruct_code_with_indent(code_elements: list[Any]) -> str:
    """Reconstruct code block text with proper indentation.

    Calculates relative indentation from x0 positions and converts to spaces.

    Args:
        code_elements: List of InlineCodeElement instances

    Returns:
        Code text with proper indentation
    """
    if not code_elements:
        return ""

    # Find the minimum x0 (leftmost position) as the baseline
    min_x0 = min(getattr(elem, "x0", 0) for elem in code_elements)

    # Reconstruct lines with indentation
    lines = []
    for elem in code_elements:
        x0 = getattr(elem, "x0", 0)
        # Calculate indent in points, convert to spaces (~6pt per space for monospace)
        indent_pts = x0 - min_x0
        indent_spaces = int(round(indent_pts / 6.0))
        indented_line = " " * indent_spaces + elem.text
        lines.append(indented_line)

    return "\n".join(lines)


def _group_code_blocks(elements: list[Any]) -> list[Any]:
    """Group consecutive inline code elements into code blocks.

    Args:
        elements: List of processed elements (InlineCodeElement, ParagraphElement, etc.)

    Returns:
        List with consecutive inline code elements merged into CodeBlockElement instances.
    """
    from unpdf.processors.code import CodeBlockElement, InlineCodeElement
    from unpdf.processors.headings import ParagraphElement

    if not elements:
        return elements

    grouped: list[CodeBlockElement | InlineCodeElement | ParagraphElement] = []
    code_buffer: list[InlineCodeElement] = []
    prev_y0: float | None = None
    prev_page = None

    for elem in elements:
        if isinstance(elem, InlineCodeElement):
            # Check if this code element is consecutive (same page, close y-position)
            current_y0 = getattr(elem, "y0", 0)
            current_page = getattr(elem, "page_number", 1)

            if (
                code_buffer
                and prev_y0 is not None
                and (prev_page != current_page or abs(current_y0 - prev_y0) > 40)
            ):
                # Gap too large or different page - flush buffer as code block
                if len(code_buffer) >= 3:  # At least 3 lines for a code block
                    text = _reconstruct_code_with_indent(code_buffer)
                    # Try to infer language from first few lines
                    from unpdf.processors.code import CodeProcessor

                    lang = CodeProcessor()._infer_language(text)
                    grouped.append(
                        CodeBlockElement(
                            text=text,
                            language=lang,
                            y0=code_buffer[0].y0,
                            page_number=code_buffer[0].page_number,
                        )
                    )
                else:
                    # Keep as inline code if too short
                    grouped.extend(code_buffer)
                code_buffer = []

            code_buffer.append(elem)
            prev_y0 = current_y0
            prev_page = current_page
        else:
            # Non-code element - flush buffer first
            if code_buffer:
                if len(code_buffer) >= 3:
                    text = _reconstruct_code_with_indent(code_buffer)
                    from unpdf.processors.code import CodeProcessor

                    lang = CodeProcessor()._infer_language(text)
                    grouped.append(
                        CodeBlockElement(
                            text=text,
                            language=lang,
                            y0=code_buffer[0].y0,
                            page_number=code_buffer[0].page_number,
                        )
                    )
                else:
                    grouped.extend(code_buffer)
                code_buffer = []
                prev_y0 = None
                prev_page = None

            grouped.append(elem)

    # Flush remaining code buffer
    if code_buffer:
        if len(code_buffer) >= 3:
            text = _reconstruct_code_with_indent(code_buffer)
            from unpdf.processors.code import CodeProcessor

            lang = CodeProcessor()._infer_language(text)
            grouped.append(
                CodeBlockElement(
                    text=text,
                    language=lang,
                    y0=code_buffer[0].y0,
                    page_number=code_buffer[0].page_number,
                )
            )
        else:
            grouped.extend(code_buffer)

    return grouped


def convert_pdf(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
    detect_code_blocks: bool = True,
    extract_tables: bool = True,
    heading_font_ratio: float = 1.3,
    page_numbers: list[int] | None = None,
) -> str:
    """Convert PDF file to Markdown.

    This is the main entry point for PDF-to-Markdown conversion. It
    processes the PDF through extraction, processing, and rendering stages.

    Args:
        pdf_path: Path to the PDF file to convert.
        output_path: Optional output path. If None, returns Markdown as string.
            If provided, writes to file and returns the content.
        detect_code_blocks: Whether to detect and format code blocks.
            Default: True.
        extract_tables: Whether to extract and convert tables.
            Default: True.
        heading_font_ratio: Font size multiplier for heading detection.
            Text with font_size > avg_font_size * ratio is treated as heading.
            Default: 1.3 (30% larger than average).
        page_numbers: Optional list of specific page numbers to convert (1-indexed).
            If None, converts all pages. Default: None.

    Returns:
        Markdown content as string.

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If PDF is corrupted or unreadable.
        PermissionError: If PDF is password-protected.

    Example:
        >>> markdown = convert_pdf("report.pdf")
        >>> print(markdown[:50])
        # Annual Report 2024

        ## Executive Summary
        ...

        >>> convert_pdf("doc.pdf", output_path="doc.md")
        '# Document Title...'
    """
    pdf_path = Path(pdf_path)

    # Validate extension first (before checking existence)
    if not pdf_path.suffix.lower() == ".pdf":
        raise ValueError(f"File must be a PDF, got: {pdf_path.suffix}")

    # Then check if file exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    logger.info(f"Converting PDF: {pdf_path}")

    # TODO: Phase 2 - Implement extraction
    # from unpdf.extractors.text import extract_text_with_metadata
    # spans = extract_text_with_metadata(pdf_path)

    # TODO: Phase 3 - Implement processing
    # from unpdf.processors.headings import HeadingProcessor
    # processor = HeadingProcessor(avg_font_size=12, heading_ratio=heading_font_ratio)
    # elements = [processor.process(span) for span in spans]

    # TODO: Phase 4+ - Implement rendering
    # from unpdf.renderers.markdown import MarkdownRenderer
    # renderer = MarkdownRenderer()
    # markdown = renderer.render(elements)

    # Phase 2: Extract text with metadata and tables
    from unpdf.extractors.text import extract_text_with_metadata

    spans = extract_text_with_metadata(pdf_path, page_numbers=page_numbers)

    # Extract and annotate links
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                if hasattr(page, "annots") and page.annots:
                    for annot in page.annots:
                        url = annot.get("uri")
                        if not url:
                            continue

                        # Get annotation bounding box
                        x0 = annot.get("x0", 0)
                        y0 = annot.get("y0", 0)
                        x1 = annot.get("x1", 0)
                        y1 = annot.get("y1", 0)

                        # Find overlapping text spans
                        for span in spans:
                            if span["page_number"] != page_num:
                                continue

                            # Check if span overlaps with link annotation
                            span_x0 = span["x0"]
                            span_y0 = span["y0"]
                            span_x1 = span["x1"]
                            span_y1 = span["y1"]

                            # Check for overlap
                            if (
                                span_x0 <= x1
                                and span_x1 >= x0
                                and span_y0 <= y1
                                and span_y1 >= y0
                            ):
                                # Annotate span with URL
                                span["link_url"] = url
                                logger.debug(
                                    f"Annotated span '{span['text']}' with link {url}"
                                )
    except Exception as e:
        logger.warning(f"Failed to extract links: {e}")

    # Extract horizontal rules from PDF drawings
    hr_elements: list[Any] = []
    try:
        import pymupdf  # type: ignore[import-untyped]

        from unpdf.processors.horizontal_rule import HorizontalRuleProcessor

        hr_processor = HorizontalRuleProcessor()

        doc = pymupdf.open(pdf_path)
        pages_to_process = (
            [doc[i - 1] for i in page_numbers if i <= len(doc)] if page_numbers else doc
        )
        page_num_offset = page_numbers[0] if page_numbers else 1
        for page_idx, page in enumerate(pages_to_process):
            drawings = page.get_drawings()
            page_hrs = hr_processor.detect_horizontal_rules(
                drawings, page_num_offset + page_idx
            )
            hr_elements.extend(page_hrs)

        logger.info(f"Detected {len(hr_elements)} horizontal rule(s)")
    except Exception as e:
        logger.warning(f"Failed to extract horizontal rules: {e}")

    # Extract tables if enabled (with position info)
    table_elements = []
    if extract_tables:
        try:
            import pdfplumber

            from unpdf.processors.table import TableProcessor

            table_processor = TableProcessor()

            with pdfplumber.open(pdf_path) as pdf:
                pages_to_process = (
                    [pdf.pages[i - 1] for i in page_numbers if i <= len(pdf.pages)]
                    if page_numbers
                    else pdf.pages
                )
                page_num_offset = page_numbers[0] if page_numbers else 1
                for page_idx, page in enumerate(pages_to_process):
                    page_tables = table_processor.extract_tables(page)
                    # Add page number to each table for proper ordering
                    for table in page_tables:
                        # Convert pdfplumber coords to PyMuPDF coords
                        # pdfplumber: y=0 at top, bbox=(x0, top, x1, bottom)
                        # PyMuPDF: y=0 at bottom, so y0 = page_height - pdfplumber_top
                        # Use top edge for reading order positioning
                        if table.bbox:
                            table.y0 = page.height - table.bbox[1]  # Convert top to PyMuPDF coords
                        else:
                            table.y0 = 0.0
                        table.page_number = page_num_offset + page_idx
                    table_elements.extend(page_tables)

            logger.info(f"Extracted {len(table_elements)} table(s)")
        except Exception as e:
            logger.warning(f"Failed to extract tables: {e}")

    if not spans and not table_elements:
        logger.warning(f"No content extracted from {pdf_path}")
        markdown = ""
    else:
        # Phase 3: Process spans into structured elements
        from unpdf.extractors.text import (
            calculate_average_font_size,
            calculate_max_font_size,
        )
        from unpdf.processors.headings import HeadingProcessor
        from unpdf.processors.lists import ListProcessor

        avg_font_size = calculate_average_font_size(spans) if spans else 12.0
        max_font_size = calculate_max_font_size(spans) if spans else 12.0

        # Analyze heading structure in the document
        # Find distinct heading font sizes (bold text that's larger than body)
        heading_font_sizes = set()
        for span in spans:
            if span.get("is_bold", False):
                font_size = span.get("font_size", 0)
                # Consider as potential heading if noticeably larger than body
                if font_size >= avg_font_size * 1.05:  # At least 5% larger
                    heading_font_sizes.add(round(font_size, 1))

        # Sort from largest to smallest
        font_size_levels = sorted(heading_font_sizes, reverse=True) if heading_font_sizes else None

        if font_size_levels:
            logger.debug(f"Detected {len(font_size_levels)} heading font size levels: {font_size_levels}")
        else:
            logger.debug("No distinct heading levels detected")

        # Merge spans on the same line (within 2 points vertically)
        # This fixes issues where list markers and text are separate spans
        spans = _merge_spans_on_same_line(spans)

        # Calculate base indent for list detection
        # Find the leftmost x0 that appears to be a list item
        list_x0_candidates = []
        for span in spans:
            text = span["text"].strip()
            # Check if it looks like a list item (has bullet or number prefix)
            import re
            has_bullet = any(text.startswith(c) for c in ["•", "●", "○", "◦", "▪", "▫", "–", "-", "·", "►", "➢"])
            has_number = re.match(r"^\d+\.\s+", text)
            if has_bullet or has_number:
                list_x0_candidates.append(span.get("x0", 72.0))
        
        # Use the minimum list item x0 as base, or fall back to global min
        if list_x0_candidates:
            base_list_indent = min(list_x0_candidates)
        else:
            base_list_indent = min((span.get("x0", 72.0) for span in spans), default=72.0) if spans else 72.0

        heading_processor = HeadingProcessor(
            avg_font_size=avg_font_size,
            heading_ratio=heading_font_ratio,
            max_font_size=max_font_size,
            font_size_levels=font_size_levels,
        )
        list_processor = ListProcessor(base_indent=base_list_indent, indent_threshold=20.0)

        # Phase 4: Import additional processors
        from unpdf.processors.code import (
            CodeProcessor,
        )

        code_processor = CodeProcessor()

        elements = []
        for span in spans:
            # Process in priority order (most specific first):
            # 1. Code (monospace fonts)
            # 2. Headings (large/bold fonts) - must be before lists
            # 3. Lists (bullet/number markers)
            # 4. Blockquotes (large indents)
            # 5. Paragraphs (default)

            code_result = code_processor.process(span)
            if code_result.__class__.__name__ != "ParagraphElement":
                elements.append(code_result)
                continue

            heading_result = heading_processor.process(span)
            if heading_result.__class__.__name__ != "ParagraphElement":
                elements.append(heading_result)  # type: ignore[arg-type]
                # Update list processor context when we hit a heading
                list_processor.update_context(span["text"])
                continue

            list_result = list_processor.process(span)
            if list_result.__class__.__name__ != "ParagraphElement":
                elements.append(list_result)  # type: ignore[arg-type]
                continue

            # Blockquote detection disabled - too many false positives
            # TODO: Improve blockquote detection accuracy before re-enabling
            # quote_result = blockquote_processor.process(span)
            # if quote_result.__class__.__name__ != "ParagraphElement":
            #     elements.append(quote_result)  # type: ignore[arg-type]
            #     continue

            # Check if span has a link annotation
            if span.get("link_url"):
                from unpdf.processors.headings import LinkElement

                link_elem = LinkElement(
                    text=span["text"],
                    url=span["link_url"],
                    y0=span.get("y0", 0),
                    x0=span.get("x0", 0),
                    page_number=span.get("page_number", 1),
                )
                elements.append(link_elem)  # type: ignore[arg-type]
                continue

            # If nothing else matched, it's a paragraph
            elements.append(heading_result)  # type: ignore[arg-type]

        # Merge inline code into adjacent paragraphs on same line
        elements = _merge_inline_code_into_paragraphs(elements)

        # Group consecutive inline code elements into code blocks
        elements = _group_code_blocks(elements)

        # Merge tables and horizontal rules into elements at correct positions
        # All should appear in reading order based on page and y-position
        
        # Filter out text elements that overlap with table bounding boxes
        # (to avoid duplicate content - pdfplumber extracts table cells as both text and tables)
        def overlaps_table(elem: Any, tables: list[Any]) -> bool:
            """Check if element overlaps with any table bounding box."""
            if not hasattr(elem, "y0") or not hasattr(elem, "page_number"):
                return False

            elem_page = elem.page_number
            elem_y0 = elem.y0  # PyMuPDF coords (y=0 at bottom)

            # Check against all tables on same page
            for table in tables:
                if table.page_number != elem_page:
                    continue

                # Table bbox is in pdfplumber format: (x0, top, x1, bottom)
                # Need to convert to PyMuPDF coords for comparison
                # PyMuPDF: y=0 at bottom, so y0_pymupdf = page_height - y_pdfplumber
                # We need page height - but we don't have it here
                # Alternative: use table.y0 which is already converted
                # table.y0 is the TOP of the table in PyMuPDF coords
                
                if not hasattr(table, 'bbox') or not table.bbox:
                    continue
                    
                # Calculate table's vertical range in PyMuPDF coords
                # table.bbox = (x0, top_pdfplumber, x1, bottom_pdfplumber)
                # Assume page height of 792 (US Letter) - should work for most PDFs
                # Better: calculate from bbox if possible
                table_height_pdfplumber = table.bbox[3] - table.bbox[1]
                table_y0_top = table.y0  # Top edge in PyMuPDF
                table_y0_bottom = table_y0_top - table_height_pdfplumber  # Bottom edge in PyMuPDF

                # Add small margin (5 points) to avoid edge cases
                if table_y0_bottom - 5 <= elem_y0 <= table_y0_top + 5:
                    return True

            return False

        # Filter out overlapping text elements
        filtered_elements = [
            elem for elem in elements if not overlaps_table(elem, table_elements)
        ]

        # Create a combined list with position info for ALL elements
        all_elements: list[
            tuple[
                int,
                float,
                str,
                CodeBlockElement
                | InlineCodeElement
                | ParagraphElement
                | TableElement,
            ]
        ] = []

        for elem in filtered_elements:
            # Add position info for text elements
            if hasattr(elem, "y0"):
                all_elements.append((elem.page_number, elem.y0, "text", elem))
            else:
                # Fallback if no position info
                all_elements.append((1, 0, "text", elem))

        for table in table_elements:
            # Tables already have page_number and y0 from extraction
            all_elements.append((table.page_number, table.y0, "table", table))

        for hr in hr_elements:
            # Horizontal rules already have page_number and y0
            all_elements.append((hr.page_number, hr.y0, "hr", hr))

        # Always sort by page, then by y-position (descending, since y=0 is at bottom in PDF coords)
        all_elements.sort(key=lambda x: (x[0], -x[1]))

        # Extract just the elements
        elements = [elem for _, _, _, elem in all_elements]  # type: ignore[misc]

        # Phase 3: Render elements to Markdown
        from unpdf.renderers.markdown import render_elements_to_markdown

        markdown = render_elements_to_markdown(elements)

        logger.info(
            f"Converted {len(spans)} span(s) to {len(elements)} element(s), "
            f"{len(markdown)} character(s)"
        )

    # Write to file if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info(f"Written to: {output_path}")

    return markdown
