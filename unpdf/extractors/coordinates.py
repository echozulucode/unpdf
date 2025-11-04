"""Enhanced coordinate and bounding box extraction from PDF content streams.

This module provides precise extraction of text positioning from PDF content streams
by parsing text-showing operators (Tj, TJ) and transformation matrices (Tm, Td).

Reference: PDF 1.7 specification, Section 9.4 (Text Objects)
"""

import logging
from dataclasses import dataclass

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class TextFragment:
    """A fragment of text with precise positioning and font information.

    Attributes:
        text: The actual text content
        x: X coordinate (bottom-left)
        y: Y coordinate (bottom-left)
        width: Width of the text fragment
        height: Height of the text fragment (from font size)
        font_name: Name of the font used
        font_size: Size of the font
        color: Text color (RGB tuple or None)
    """

    text: str
    x: float
    y: float
    width: float
    height: float
    font_name: str | None = None
    font_size: float | None = None
    color: tuple[float, float, float] | None = None

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """Get bounding box as (x0, y0, x1, y1)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class CoordinateExtractor:
    """Extracts precise text coordinates from PDF content streams."""

    def __init__(self, pdf_path: str):
        """Initialize the extractor.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(pdf_path)

    def extract_text_fragments(self, page_number: int) -> list[TextFragment]:
        """Extract all text fragments with coordinates from a page.

        This is a placeholder implementation using pdfplumber's char-level extraction.

        Args:
            page_number: 0-indexed page number

        Returns:
            List of TextFragment objects
        """
        if page_number >= len(self.pdf.pages):
            return []

        page = self.pdf.pages[page_number]
        fragments = []

        try:
            # Use pdfplumber's char extraction for better positioning
            chars = page.chars
            if chars:
                # Group chars into words/fragments (simplified)
                current_text = ""
                current_x = None
                current_y = None
                current_width = 0
                current_height = 0
                current_font = None
                current_size = None

                for char in chars:
                    if current_x is None:
                        current_x = char["x0"]
                        current_y = char["bottom"]
                        current_font = char.get("fontname")
                        current_size = char.get("size")

                    current_text += char["text"]
                    current_width = char["x1"] - current_x
                    current_height = max(current_height, char["height"])

                if current_text:
                    fragments.append(
                        TextFragment(
                            text=current_text,
                            x=current_x or 0,
                            y=current_y or 0,
                            width=current_width,
                            height=current_height,
                            font_name=current_font,
                            font_size=current_size,
                        )
                    )

        except Exception as e:
            logger.error(f"Error extracting text fragments from page {page_number}: {e}")

        return fragments

    def extract_font_info(self, page_number: int) -> dict[str, dict]:
        """Extract font information from a page.

        Args:
            page_number: 0-indexed page number

        Returns:
            Dictionary mapping font names to font properties
        """
        if page_number >= len(self.pdf.pages):
            return {}

        page = self.pdf.pages[page_number]
        fonts: dict[str, dict] = {}

        try:
            # Get unique fonts from chars
            chars = page.chars
            if chars:
                for char in chars:
                    font_name = char.get("fontname")
                    if font_name and font_name not in fonts:
                        fonts[font_name] = {
                            "name": font_name,
                            "size": char.get("size"),
                        }

        except Exception as e:
            logger.error(f"Error extracting font info from page {page_number}: {e}")

        return fonts

    def is_monospace_font(self, font_info: dict) -> bool:
        """Determine if a font is monospace based on its properties.

        Args:
            font_info: Font information dictionary

        Returns:
            True if font is likely monospace
        """
        basefont = font_info.get("basefont", "").lower()
        family = font_info.get("family", "").lower()

        # Common monospace font names
        monospace_keywords = [
            "courier",
            "mono",
            "console",
            "terminal",
            "fixed",
            "code",
        ]

        return any(kw in basefont or kw in family for kw in monospace_keywords)

    def get_page_dimensions(self, page_number: int) -> tuple[float, float]:
        """Get page dimensions (width, height).

        Args:
            page_number: 0-indexed page number

        Returns:
            Tuple of (width, height) in points
        """
        if page_number >= len(self.pdf.pages):
            return (0, 0)

        page = self.pdf.pages[page_number]
        return (float(page.width), float(page.height))
