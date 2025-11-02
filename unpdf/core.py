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

logger = logging.getLogger(__name__)


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
                        # Store y0 from bbox for vertical positioning (y increases downward in PDF)
                        table.y0 = table.bbox[1] if table.bbox else 0.0
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
        from unpdf.extractors.text import calculate_average_font_size
        from unpdf.processors.headings import HeadingProcessor
        from unpdf.processors.lists import ListProcessor

        avg_font_size = calculate_average_font_size(spans) if spans else 12.0
        heading_processor = HeadingProcessor(
            avg_font_size=avg_font_size, heading_ratio=heading_font_ratio
        )
        list_processor = ListProcessor()

        # Phase 4: Import additional processors
        from unpdf.processors.blockquote import BlockquoteProcessor
        from unpdf.processors.code import CodeProcessor

        blockquote_processor = BlockquoteProcessor()
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

            quote_result = blockquote_processor.process(span)
            if quote_result.__class__.__name__ != "ParagraphElement":
                elements.append(quote_result)  # type: ignore[arg-type]
                continue

            # If nothing else matched, it's a paragraph
            elements.append(heading_result)  # type: ignore[arg-type]

        # Merge tables into elements at correct positions
        # Tables should appear in reading order based on page and y-position
        if table_elements:
            # Filter out text elements that overlap with table bounding boxes
            # (to avoid duplicate content - pdfplumber extracts table cells as both text and tables)
            def overlaps_table(elem, tables):
                """Check if element overlaps with any table bounding box."""
                if not hasattr(elem, "y0") or not hasattr(elem, "page_number"):
                    return False

                elem_page = elem.page_number
                elem_y0 = elem.y0

                # Check against all tables on same page
                for table in tables:
                    if table.page_number != elem_page:
                        continue

                    # Table bbox is (x0, y0, x1, y1)
                    # Check if element's y0 falls within table's vertical range
                    table_y0 = table.bbox[1]  # bottom
                    table_y1 = table.bbox[3]  # top

                    # Add small margin (5 points) to avoid edge cases
                    if table_y0 - 5 <= elem_y0 <= table_y1 + 5:
                        return True

                return False

            # Filter out overlapping text elements
            filtered_elements = [
                elem for elem in elements if not overlaps_table(elem, table_elements)
            ]

            # Create a combined list with position info
            all_elements = []

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

            # Sort by page, then by y-position (descending, since higher y0 is at top of page)
            all_elements.sort(key=lambda x: (x[0], -x[1]))

            # Extract just the elements
            elements = [elem for _, _, _, elem in all_elements]
        else:
            # Just add tables at the end if no position info
            elements.extend(table_elements)  # type: ignore[arg-type]

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
