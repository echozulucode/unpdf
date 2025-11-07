"""PDF structure dumper for debugging.

This module provides functionality to dump the internal structure of PDF files
in a human-readable text format. This is useful for:
- Understanding how PDF content is extracted and structured
- Debugging conversion issues
- Analyzing font properties, positioning, and styles
- Comparing source PDF structure with rendered output
"""

import logging
from pathlib import Path
from typing import Any

import pymupdf

logger = logging.getLogger(__name__)


def dump_pdf_structure(pdf_path: Path, output_path: Path | None = None) -> str:
    """Dump the structure of a PDF file to text format.

    Args:
        pdf_path: Path to PDF file
        output_path: Optional path to save output (if None, returns string)

    Returns:
        String containing formatted structure dump
    """
    logger.info(f"Dumping structure for: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    output_lines = []

    # Document header
    output_lines.append("=" * 80)
    output_lines.append(f"PDF STRUCTURE DUMP: {pdf_path.name}")
    output_lines.append("=" * 80)
    output_lines.append(f"Pages: {len(doc)}")
    output_lines.append(f"File size: {pdf_path.stat().st_size:,} bytes")
    output_lines.append("")

    # Extract metadata
    metadata = doc.metadata
    if metadata:
        output_lines.append("METADATA:")
        for key, value in metadata.items():
            if value:
                output_lines.append(f"  {key}: {value}")
        output_lines.append("")

    # Process each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        output_lines.extend(_dump_page(page, page_num + 1))

    doc.close()

    result = "\n".join(output_lines)

    # Save to file if requested
    if output_path:
        output_path.write_text(result, encoding="utf-8")
        logger.info(f"Structure dump saved to: {output_path}")

    return result


def _dump_page(page: pymupdf.Page, page_num: int) -> list[str]:
    """Dump structure for a single page."""
    lines = []

    # Page header
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"PAGE {page_num} ({page.rect.width:.1f} x {page.rect.height:.1f} pt)")
    lines.append("=" * 80)
    lines.append("")

    # Extract text blocks using PyMuPDF's built-in method
    text_dict = page.get_text("dict", flags=0)
    blocks = text_dict.get("blocks", [])

    # Filter to text blocks only
    text_blocks = [b for b in blocks if b.get("type") == 0]
    lines.append(f"Text Blocks: {len(text_blocks)}")

    # Get font statistics
    font_stats = _analyze_fonts_from_blocks(blocks)
    lines.append("")
    lines.append("FONT STATISTICS:")
    lines.append(f"  Median font size: {font_stats['median_size']:.1f}pt")
    lines.append(f"  Min font size: {font_stats['min_size']:.1f}pt")
    lines.append(f"  Max font size: {font_stats['max_size']:.1f}pt")
    lines.append(f"  Unique fonts: {len(font_stats['unique_fonts'])}")
    for font in sorted(font_stats['unique_fonts']):
        lines.append(f"    - {font}")
    lines.append("")

    # Dump each text block
    for idx, block in enumerate(text_blocks, 1):
        lines.extend(_dump_text_block_dict(idx, block))

    # Extract and dump tables (using find_tables if available)
    try:
        tables = page.find_tables()
        if tables and tables.tables:
            lines.append("")
            lines.append(f"TABLES: {len(tables.tables)}")
            lines.append("")
            for idx, table in enumerate(tables.tables, 1):
                lines.extend(_dump_table_pymupdf(idx, table))
    except Exception as e:
        logger.debug(f"Error extracting tables: {e}")

    # Extract images
    images = page.get_images()
    if images:
        lines.append("")
        lines.append(f"IMAGES: {len(images)}")
        lines.append("")
        for idx, img in enumerate(images, 1):
            lines.extend(_dump_image(idx, img, page))

    return lines


def _dump_text_block_dict(idx: int, block: dict[str, Any]) -> list[str]:
    """Dump a single text block from PyMuPDF dict format."""
    lines = []

    bbox = block["bbox"]
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0

    lines.append("-" * 80)
    lines.append(f"BLOCK #{idx}: TextBlock")
    lines.append(f"  Position: ({x0:.1f}, {y0:.1f}) → ({x1:.1f}, {y1:.1f})")
    lines.append(f"  Size: {width:.1f} x {height:.1f} pt")
    lines.append("")

    # Extract text from lines
    text_lines = block.get("lines", [])
    lines.append(f"  Lines: {len(text_lines)}")

    for line_idx, line in enumerate(text_lines):
        spans = line.get("spans", [])
        line_bbox = line.get("bbox", (0, 0, 0, 0))
        lines.append(f"  Line {line_idx + 1} @ y={line_bbox[3]:.1f}:")

        for span in spans:
            text = span.get("text", "")
            font = span.get("font", "Unknown")
            size = span.get("size", 0)
            color = span.get("color", 0)
            flags = span.get("flags", 0)

            lines.append(f"    Text: {repr(text)}")
            lines.append(f"    Font: {font}, Size: {size:.1f}pt")
            lines.append(f"    Color: {_format_color(color)}")
            lines.append(f"    Flags: {_format_flags(flags)}")

            # Style analysis
            style_props = []
            if flags & 2**4:  # Bold
                style_props.append("bold")
            if flags & 2**1:  # Italic
                style_props.append("italic")
            if flags & 2**0:  # Superscript
                style_props.append("superscript")
            if "mono" in font.lower() or "courier" in font.lower():
                style_props.append("monospace")

            if style_props:
                lines.append(f"    Styles: {', '.join(style_props)}")

    lines.append("")
    return lines


def _dump_table_pymupdf(idx: int, table: Any) -> list[str]:
    """Dump a single PyMuPDF table."""
    lines = []

    bbox = table.bbox
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0

    lines.append("-" * 80)
    lines.append(f"TABLE #{idx}")
    lines.append(f"  Position: ({x0:.1f}, {y0:.1f}) → ({x1:.1f}, {y1:.1f})")
    lines.append(f"  Size: {width:.1f} x {height:.1f} pt")

    # Get table content
    try:
        extract = table.extract()
        if extract:
            rows = len(extract)
            cols = len(extract[0]) if extract else 0
            lines.append(f"  Dimensions: {rows} rows x {cols} columns")
            lines.append("")

            # Show first few rows
            for row_idx, row in enumerate(extract[:5]):  # Limit to first 5 rows
                lines.append(f"  Row {row_idx}:")
                for col_idx, cell in enumerate(row):
                    if cell:
                        cell_str = str(cell).strip()[:50]  # Limit length
                        lines.append(f"    [{row_idx},{col_idx}]: {repr(cell_str)}")
            if len(extract) > 5:
                lines.append(f"  ... ({len(extract) - 5} more rows)")
    except Exception as e:
        lines.append(f"  Error extracting content: {e}")

    lines.append("")
    return lines


def _dump_table(idx: int, table: dict[str, Any]) -> list[str]:
    """Dump a single table."""
    lines = []

    bbox = table.get("bbox", (0, 0, 0, 0))
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0

    lines.append("-" * 80)
    lines.append(f"TABLE #{idx}")
    lines.append(f"  Position: ({x0:.1f}, {y0:.1f}) → ({x1:.1f}, {y1:.1f})")
    lines.append(f"  Size: {width:.1f} x {height:.1f} pt")

    cells = table.get("cells", [])
    if cells:
        # Determine table dimensions
        max_row = max(cell[0] for cell in cells) + 1 if cells else 0
        max_col = max(cell[1] for cell in cells) + 1 if cells else 0
        lines.append(f"  Dimensions: {max_row} rows x {max_col} columns")
        lines.append("")

        # Show cell content
        for row in range(max_row):
            lines.append(f"  Row {row}:")
            for col in range(max_col):
                cell_data = next((c for c in cells if c[0] == row and c[1] == col), None)
                if cell_data:
                    content = cell_data[4] if len(cell_data) > 4 else ""
                    lines.append(f"    [{row},{col}]: {repr(content[:50])}")
    lines.append("")

    return lines


def _dump_image(idx: int, img: tuple, page: pymupdf.Page) -> list[str]:
    """Dump a single image."""
    lines = []

    xref = img[0]
    lines.append("-" * 80)
    lines.append(f"IMAGE #{idx}")
    lines.append(f"  XRef: {xref}")

    # Get image info
    try:
        img_info = page.parent.extract_image(xref)
        lines.append(f"  Format: {img_info.get('ext', 'unknown')}")
        lines.append(f"  Size: {img_info.get('width', 0)} x {img_info.get('height', 0)} px")
        lines.append(f"  Color Space: {img_info.get('colorspace', 'unknown')}")
        lines.append(f"  BPP: {img_info.get('bpc', 0)}")
    except Exception as e:
        lines.append(f"  Error extracting info: {e}")

    # Get image placement on page
    img_rects = page.get_image_rects(xref)
    if img_rects:
        for rect in img_rects:
            lines.append(f"  Position: ({rect.x0:.1f}, {rect.y0:.1f}) → ({rect.x1:.1f}, {rect.y1:.1f})")
            lines.append(f"  Size: {rect.width:.1f} x {rect.height:.1f} pt")

    lines.append("")

    return lines


def _analyze_fonts_from_blocks(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze font usage in text blocks from PyMuPDF dict format."""
    sizes = []
    fonts = set()

    for block in blocks:
        if block.get("type") == 0:  # Text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    if size > 0:
                        sizes.append(size)
                    font = span.get("font", "")
                    if font:
                        fonts.add(font)

    if not sizes:
        sizes = [12.0]  # Default

    sizes.sort()
    median_size = sizes[len(sizes) // 2]

    return {
        "median_size": median_size,
        "min_size": min(sizes),
        "max_size": max(sizes),
        "unique_fonts": fonts,
    }


def _format_color(color: tuple[float, ...] | int) -> str:
    """Format color as hex string."""
    if isinstance(color, int):
        # Single value - grayscale
        return f"#{color:02x}{color:02x}{color:02x}"
    elif len(color) >= 3:
        # RGB tuple (0.0-1.0)
        r = int(color[0] * 255)
        g = int(color[1] * 255)
        b = int(color[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    return "#000000"


def _format_flags(flags: int) -> str:
    """Format font flags as human-readable string."""
    flag_names = []

    if flags & 2**0:
        flag_names.append("superscript")
    if flags & 2**1:
        flag_names.append("italic")
    if flags & 2**2:
        flag_names.append("serifed")
    if flags & 2**3:
        flag_names.append("monospaced")
    if flags & 2**4:
        flag_names.append("bold")

    return ", ".join(flag_names) if flag_names else "none"
