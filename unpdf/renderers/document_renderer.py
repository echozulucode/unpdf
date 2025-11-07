"""Markdown renderer for ProcessedDocument output.

This module converts structured ProcessedDocument output into high-quality Markdown,
preserving document structure, semantics, and styling.
"""

import logging
from typing import Any

from unpdf.models.layout import Block, BlockType, Style
from unpdf.processors.document_processor import ProcessedDocument, ProcessedPage

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """Renders ProcessedDocument to Markdown format.

    Converts structured blocks from DocumentProcessor into clean Markdown
    with proper formatting, spacing, and semantic preservation.
    """

    def __init__(
        self,
        include_metadata: bool = True,
        table_format: str = "gfm",
        preserve_styles: bool = True,
    ):
        """Initialize the Markdown renderer.

        Args:
            include_metadata: Whether to include YAML frontmatter with document metadata
            table_format: Table format ('gfm' for GitHub Flavored Markdown, 'html' for HTML tables)
            preserve_styles: Whether to preserve text styles (bold, italic) in output
        """
        self.include_metadata = include_metadata
        self.table_format = table_format
        self.preserve_styles = preserve_styles

    def render(self, document: ProcessedDocument) -> str:
        """Render a ProcessedDocument to Markdown.

        Args:
            document: The processed document to render

        Returns:
            Markdown string representation of the document
        """
        parts: list[str] = []

        # Add frontmatter if enabled
        if self.include_metadata and document.metadata:
            frontmatter = self._render_frontmatter(document.metadata)
            if frontmatter:
                parts.append(frontmatter)
                parts.append("")  # Blank line after frontmatter

        # Render each page
        for page in document.pages:
            page_markdown = self._render_page(page)
            if page_markdown:
                parts.append(page_markdown)

        result = "\n".join(parts)

        # Clean up excessive blank lines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result.strip()

    def _render_frontmatter(self, metadata: dict[str, Any]) -> str:
        """Render document metadata as YAML frontmatter.

        Args:
            metadata: Document metadata dictionary

        Returns:
            YAML frontmatter string
        """
        if not metadata:
            return ""

        lines = ["---"]

        # Common metadata fields in standard order
        field_order = ["title", "author", "date", "subject", "keywords", "source"]

        for field in field_order:
            if field in metadata and metadata[field]:
                value = str(metadata[field])
                # Quote values with special characters
                if any(c in value for c in [":", "#", "[", "]", "{", "}"]):
                    value = f'"{value}"'
                lines.append(f"{field}: {value}")

        # Add remaining fields
        for key, value in metadata.items():
            if key not in field_order and value:
                value_str = str(value)
                if any(c in value_str for c in [":", "#", "[", "]", "{", "}"]):
                    value_str = f'"{value_str}"'
                lines.append(f"{key}: {value_str}")

        lines.append("---")

        return "\n".join(lines)

    def _render_page(self, page: ProcessedPage) -> str:
        """Render a single page to Markdown.

        Args:
            page: The page to render

        Returns:
            Markdown string for the page
        """
        parts: list[str] = []

        # Render blocks in reading order
        for block in page.blocks:
            block_md = self._render_block(block)
            if block_md:
                parts.append(block_md)

        # Render tables
        for table in page.tables:
            table_md = self._render_table(table)
            if table_md:
                parts.append(table_md)
                parts.append("")  # Blank line after table

        return "\n".join(parts)

    def _render_block(self, block: Block) -> str:
        """Render a single block to Markdown.

        Args:
            block: The block to render

        Returns:
            Markdown string for the block
        """
        if block.block_type == BlockType.HEADING:
            return self._render_heading(block)
        elif block.block_type == BlockType.TEXT:
            return self._render_paragraph(block)
        elif block.block_type == BlockType.LIST:
            return self._render_list_item(block)
        elif block.block_type == BlockType.CODE:
            return self._render_code_block(block)
        elif block.block_type == BlockType.BLOCKQUOTE:
            return self._render_blockquote(block)
        elif block.block_type == BlockType.HORIZONTAL_RULE:
            return "\n---\n"
        else:
            # Unknown block type, render as paragraph
            return self._render_paragraph(block)

    def _render_heading(self, block: Block) -> str:
        """Render a heading block.

        Args:
            block: Heading block

        Returns:
            Markdown heading string
        """
        level = (
            block.metadata.get("heading_level", block.metadata.get("level", 1))
            if block.metadata
            else 1
        )
        level = max(1, min(6, level))  # Clamp to 1-6

        # Check if block has span-level formatting
        if block.spans and len(block.spans) > 0:
            text = self._render_spans(block.spans)
        else:
            text = str(block.content or "")
            text = self._apply_styles(text, block.style)
        prefix = "#" * level

        return f"\n{prefix} {text}\n"

    def _render_paragraph(self, block: Block) -> str:
        """Render a paragraph block.

        Args:
            block: Paragraph block

        Returns:
            Markdown paragraph string
        """
        # Check if block has span-level formatting
        if block.spans and len(block.spans) > 0:
            text = self._render_spans(block.spans)
        else:
            text = str(block.content or "")
            text = self._apply_styles(text, block.style)

        # Check if this is a link
        if block.metadata and "url" in block.metadata:
            url = block.metadata["url"]
            return f"[{text}]({url})\n"

        return f"{text}\n"

    def _render_spans(self, spans: list) -> str:
        """Render text with inline formatting from spans.

        Args:
            spans: List of Span objects with formatting information

        Returns:
            Text with markdown inline formatting
        """
        if not self.preserve_styles:
            return "".join(span.text for span in spans)

        parts = []
        for span in spans:
            text = span.text
            
            # Apply inline formatting based on span properties
            if span.bold and span.italic:
                text = f"***{text}***"
            elif span.bold:
                text = f"**{text}**"
            elif span.italic:
                text = f"*{text}*"
            
            parts.append(text)

        return "".join(parts)

    def _render_list_item(self, block: Block) -> str:
        """Render a list item block.

        Args:
            block: List item block

        Returns:
            Markdown list item string
        """
        text = str(block.content or "")
        text = self._apply_styles(text, block.style)

        # Get indent level (0-based)
        level = block.metadata.get("indent_level", 0) if block.metadata else 0
        indent = "  " * level

        # Get list type
        list_type = (
            block.metadata.get("list_type", "bullet") if block.metadata else "bullet"
        )

        if list_type == "ordered":
            # Use number from metadata or default to 1
            number = block.metadata.get("number", 1) if block.metadata else 1
            return f"{indent}{number}. {text}\n"
        elif list_type == "checkbox":
            # Checkbox list item
            checked = block.metadata.get("checked", False) if block.metadata else False
            checkbox = "[x]" if checked else "[ ]"
            return f"{indent}- {checkbox} {text}\n"
        else:
            # Bullet list item
            return f"{indent}- {text}\n"

    def _render_code_block(self, block: Block) -> str:
        """Render a code block.

        Args:
            block: Code block

        Returns:
            Markdown fenced code block string
        """
        language = block.metadata.get("language", "") if block.metadata else ""
        text = str(block.content or "")

        return f"\n```{language}\n{text}\n```\n"

    def _render_blockquote(self, block: Block) -> str:
        """Render a blockquote block.

        Args:
            block: Blockquote block

        Returns:
            Markdown blockquote string
        """
        text = str(block.content or "")
        text = self._apply_styles(text, block.style)

        # Handle multi-line quotes
        lines = text.split("\n")
        quoted_lines = [f"> {line}" for line in lines]

        return "\n".join(quoted_lines) + "\n"

    def _render_table(self, table: Any) -> str:
        """Render a table to Markdown.

        Args:
            table: Table object from table detector

        Returns:
            Markdown table string
        """
        if self.table_format == "html":
            return self._render_table_html(table)
        else:
            return self._render_table_gfm(table)

    def _render_table_gfm(self, table: Any) -> str:
        """Render a table as GitHub Flavored Markdown.

        Args:
            table: Table object

        Returns:
            GFM table string
        """
        if not hasattr(table, "cells") or not table.cells:
            return ""

        rows = table.rows
        cols = table.cols

        # Build grid
        grid: list[list[str]] = [[" " for _ in range(cols)] for _ in range(rows)]

        for cell in table.cells:
            row, col = cell.row, cell.col
            if 0 <= row < rows and 0 <= col < cols:
                grid[row][col] = cell.text.strip()

        # Format as GFM table
        lines: list[str] = []

        # Header row (first row or all rows if no header detected)
        header = grid[0] if grid else []
        lines.append("| " + " | ".join(header) + " |")

        # Separator
        lines.append("| " + " | ".join(["---"] * cols) + " |")

        # Data rows
        for row_data in grid[1:]:
            lines.append("| " + " | ".join(row_data) + " |")

        return "\n".join(lines)

    def _render_table_html(self, table: Any) -> str:
        """Render a table as HTML.

        Args:
            table: Table object

        Returns:
            HTML table string
        """
        if not hasattr(table, "cells") or not table.cells:
            return ""

        rows = table.rows
        cols = table.cols

        # Build grid
        grid: list[list[str]] = [[" " for _ in range(cols)] for _ in range(rows)]

        for cell in table.cells:
            row, col = cell.row, cell.col
            if 0 <= row < rows and 0 <= col < cols:
                grid[row][col] = cell.text.strip()

        # Format as HTML
        lines = ["<table>"]

        # Header row (first row)
        if grid:
            lines.append("  <thead>")
            lines.append("    <tr>")
            for cell_text in grid[0]:
                lines.append(f"      <th>{cell_text}</th>")
            lines.append("    </tr>")
            lines.append("  </thead>")

        # Body rows
        if len(grid) > 1:
            lines.append("  <tbody>")
            for row_data in grid[1:]:
                lines.append("    <tr>")
                for cell_text in row_data:
                    lines.append(f"      <td>{cell_text}</td>")
                lines.append("    </tr>")
            lines.append("  </tbody>")

        lines.append("</table>")

        return "\n".join(lines)

    def _apply_styles(self, text: str, style: Style | None) -> str:
        """Apply text styles (bold, italic, strikethrough, etc.) to text.

        Args:
            text: The text to style
            style: Style object with formatting information

        Returns:
            Text with Markdown/HTML formatting applied
        """
        if not self.preserve_styles or not style:
            return text

        styled_text = text

        # Check if bold (weight is "bold" or numeric >= 700)
        is_bold = False
        if style.weight:
            if isinstance(style.weight, str):
                is_bold = style.weight.lower() == "bold"
            elif isinstance(style.weight, int):
                is_bold = style.weight >= 700

        # Check if italic
        is_italic = style.style and style.style.lower() == "italic"

        # Check for strikethrough
        is_strikethrough = (
            hasattr(style, "strikethrough") and style.strikethrough
        ) or (hasattr(style, "style") and "strikethrough" in str(style.style).lower())

        # Check for underline
        is_underline = (hasattr(style, "underline") and style.underline) or (
            hasattr(style, "style") and "underline" in str(style.style).lower()
        )

        # Apply monospace (code) first - highest priority
        if style.monospace and not styled_text.startswith("`"):
            styled_text = f"`{text}`"
            return styled_text

        # Apply bold and italic together for better handling
        if is_bold and is_italic:
            styled_text = f"***{styled_text}***"
        elif is_bold and not styled_text.startswith("**"):
            styled_text = f"**{styled_text}**"
        elif is_italic and not styled_text.startswith("*"):
            styled_text = f"*{styled_text}*"

        # Apply strikethrough (using HTML since Markdown has limited support)
        if is_strikethrough:
            styled_text = f"~~{styled_text}~~"

        # Apply underline (using HTML since Markdown doesn't support it)
        if is_underline:
            styled_text = f"<u>{styled_text}</u>"

        # Apply color (using HTML span with inline styles)
        if style.color and self._is_non_standard_color(style.color):
            r, g, b = style.color
            # Convert 0-1 range to 0-255
            r_int = int(r * 255)
            g_int = int(g * 255)
            b_int = int(b * 255)
            color_hex = f"#{r_int:02x}{g_int:02x}{b_int:02x}"
            styled_text = f'<span style="color:{color_hex}">{styled_text}</span>'

        return styled_text

    def _is_non_standard_color(self, color: tuple[float, float, float]) -> bool:
        """Check if color is non-standard (not black or very dark).

        Args:
            color: RGB color tuple (0.0-1.0 range)

        Returns:
            True if color should be preserved (not standard black/dark gray)
        """
        r, g, b = color
        # Consider colors black/dark gray if all components are close to 0
        threshold = 0.2
        return not (r < threshold and g < threshold and b < threshold)
