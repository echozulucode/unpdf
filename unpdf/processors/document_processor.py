"""Integrated document processor orchestrating all extraction strategies.

This module combines layout analysis, block classification, and content-specific
processors to extract structured content from PDFs with high accuracy.
"""

from dataclasses import dataclass
from typing import Any

import pymupdf

from unpdf.models.layout import Block, BlockType, Style
from unpdf.processors.block_classifier import BlockClassifier, FontStatistics
from unpdf.processors.checkboxes import CheckboxDetector
from unpdf.processors.code import CodeProcessor
from unpdf.processors.docstrum import DocstrumClusterer
from unpdf.processors.horizontal_rule import HorizontalRuleProcessor
from unpdf.processors.layout_analyzer import LayoutAnalyzer, TextBlock
from unpdf.processors.lists import ListProcessor
from unpdf.processors.table_detector import HybridTableDetector
from unpdf.processors.whitespace import WhitespaceAnalyzer


@dataclass
class ProcessedDocument:
    """Represents a fully processed PDF document.

    Attributes:
        pages: Processed content for each page
        metadata: Document-level metadata
        font_stats: Font statistics across the document
    """

    pages: list["ProcessedPage"]
    metadata: dict[str, Any]
    font_stats: FontStatistics


@dataclass
class ProcessedPage:
    """Represents a single processed page.

    Attributes:
        page_number: Page number (1-indexed)
        blocks: Ordered sequence of content blocks
        tables: Detected tables on this page
        images: Detected images on this page
        layout_info: Layout analysis results
    """

    page_number: int
    blocks: list[Block]
    tables: list[Any]
    images: list[Any]
    layout_info: dict[str, Any]


class DocumentProcessor:
    """Orchestrates all extraction strategies for high-accuracy PDF processing.

    This processor integrates:
    - Layout analysis (columns, reading order)
    - Block classification (headers, lists, code)
    - Table detection (lattice and stream methods)
    - Content-specific processors (links, checkboxes, etc.)

    The processing pipeline:
    1. Extract raw text blocks with PyMuPDF
    2. Analyze layout (columns, whitespace, reading order)
    3. Classify blocks (headers, paragraphs, lists, code)
    4. Detect tables using hybrid method
    5. Apply content-specific processors
    6. Assemble final structured output

    Attributes:
        layout_analyzer: Column detection and reading order
        block_classifier: Semantic type classification
        table_detector: Table detection (lattice + stream)
        content_processors: Specialized processors for specific content types
    """

    def __init__(
        self,
        detect_columns: bool = True,
        detect_tables: bool = True,
        detect_lists: bool = True,
        detect_code: bool = True,
        detect_checkboxes: bool = True,
    ):
        """Initialize the document processor.

        Args:
            detect_columns: Enable column detection
            detect_tables: Enable table detection
            detect_lists: Enable list detection
            detect_code: Enable code block detection
            detect_checkboxes: Enable checkbox detection
        """
        self.detect_columns = detect_columns
        self.detect_tables = detect_tables
        self.detect_lists = detect_lists
        self.detect_code = detect_code
        self.detect_checkboxes = detect_checkboxes

        # Initialize processors
        self.layout_analyzer = LayoutAnalyzer()
        self.block_classifier = BlockClassifier()
        self.docstrum = DocstrumClusterer()
        self.whitespace_analyzer = WhitespaceAnalyzer()
        # LayoutTreeBuilder is created per-page with page_bbox

        # Table detection
        if self.detect_tables:
            self.table_detector = HybridTableDetector()

        # Content-specific processors (initialized per-page with context)
        self.hr_processor = HorizontalRuleProcessor()

        if self.detect_lists:
            self.list_processor = ListProcessor()

        if self.detect_code:
            self.code_processor = CodeProcessor()

        if self.detect_checkboxes:
            self.checkbox_detector = CheckboxDetector()

    def process_document(self, pdf_path: str) -> ProcessedDocument:
        """Process a complete PDF document.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ProcessedDocument with structured content
        """
        doc = pymupdf.open(pdf_path)
        pages = []
        all_blocks = []

        # First pass: extract all blocks for font statistics
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_blocks = self._extract_blocks_from_page(page)
            all_blocks.extend(page_blocks)

        # Compute font statistics across entire document
        font_stats = self._compute_font_statistics(all_blocks)

        # Second pass: process each page with font statistics
        for page_num in range(len(doc)):
            page = doc[page_num]
            processed_page = self._process_page(page, page_num + 1, font_stats)
            pages.append(processed_page)

        doc.close()

        return ProcessedDocument(
            pages=pages,
            metadata=self._extract_metadata(pdf_path),
            font_stats=font_stats,
        )

    def _process_page(
        self, page: pymupdf.Page, page_number: int, font_stats: FontStatistics
    ) -> ProcessedPage:
        """Process a single page.

        Args:
            page: PyMuPDF page object
            page_number: Page number (1-indexed)
            font_stats: Document-wide font statistics

        Returns:
            ProcessedPage with structured content
        """
        # Extract raw blocks
        raw_blocks = self._extract_blocks_from_page(page)

        # Detect tables first (they take priority)
        tables = []
        if self.detect_tables:
            tables = self.table_detector.detect(page)  # type: ignore

        # Analyze layout
        layout_info: dict[str, Any] = {}
        if self.detect_columns:
            text_blocks = self._blocks_to_text_blocks(raw_blocks)
            columns = self.layout_analyzer.detect_columns(
                text_blocks, page.width  # type: ignore
            )
            ordered_blocks = self.layout_analyzer.determine_reading_order(columns)
            layout_info["columns"] = [str(c) for c in columns]
            layout_info["reading_order"] = [str(tb) for tb in ordered_blocks]
        else:
            ordered_blocks = self._blocks_to_text_blocks(raw_blocks)

        # Classify blocks
        classified_blocks = self._classify_blocks(ordered_blocks, font_stats)

        # Apply content-specific processors
        processed_blocks = self._apply_content_processors(classified_blocks, page)

        # Detect images
        images = self._extract_images(page)

        return ProcessedPage(
            page_number=page_number,
            blocks=processed_blocks,
            tables=tables,
            images=images,
            layout_info=layout_info,
        )

    def _extract_blocks_from_page(self, page: pymupdf.Page) -> list[dict[str, Any]]:
        """Extract raw text blocks from a page using PyMuPDF.

        Args:
            page: PyMuPDF page object

        Returns:
            List of block dictionaries with text and formatting info
        """
        blocks = []
        text_dict = page.get_text("dict")

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        blocks.append(
                            {
                                "text": span.get("text", ""),
                                "bbox": span.get("bbox", (0, 0, 0, 0)),
                                "font": span.get("font", ""),
                                "size": span.get("size", 12.0),
                                "flags": span.get("flags", 0),
                                "color": span.get("color", 0),
                            }
                        )

        return blocks

    def _blocks_to_text_blocks(
        self, raw_blocks: list[dict[str, Any]]
    ) -> list[TextBlock]:
        """Convert raw blocks to TextBlock objects.

        Args:
            raw_blocks: Raw block dictionaries from PyMuPDF

        Returns:
            List of TextBlock objects
        """
        from unpdf.processors.layout_analyzer import BoundingBox

        text_blocks = []
        for block in raw_blocks:
            bbox_tuple = block["bbox"]
            bbox = BoundingBox(
                x0=bbox_tuple[0],
                y0=bbox_tuple[1],
                x1=bbox_tuple[2],
                y1=bbox_tuple[3],
            )
            text_blocks.append(
                TextBlock(
                    bbox=bbox,
                    text=block["text"],
                    font_size=block.get("size", 12.0),
                    font_name=block.get("font", ""),
                )
            )
        return text_blocks

    def _compute_font_statistics(self, blocks: list[dict[str, Any]]) -> FontStatistics:
        """Compute font statistics from blocks.

        Args:
            blocks: Raw block dictionaries

        Returns:
            FontStatistics object
        """
        size_counts: dict[float, int] = {}
        monospace_count = 0

        for block in blocks:
            size = block.get("size", 12.0)
            size_counts[size] = size_counts.get(size, 0) + 1

            font = block.get("font", "").lower()
            if any(
                keyword in font for keyword in ["mono", "courier", "consolas", "code"]
            ):
                monospace_count += 1

        # Find most common size (body text)
        body_size = (
            max(size_counts, key=size_counts.get) if size_counts else 12.0  # type: ignore
        )

        monospace_ratio = monospace_count / len(blocks) if blocks else 0.0

        return FontStatistics(
            body_size=body_size,
            size_counts=size_counts,
            monospace_ratio=monospace_ratio,
        )

    def _classify_blocks(
        self, text_blocks: list[TextBlock], font_stats: FontStatistics
    ) -> list[Block]:
        """Classify text blocks into semantic types.

        Args:
            text_blocks: Ordered text blocks
            font_stats: Font statistics for classification

        Returns:
            List of classified Block objects
        """
        # This is a placeholder - full implementation would use block_classifier
        from unpdf.models.layout import BoundingBox

        classified = []
        for tb in text_blocks:
            # Create a basic Block object
            bbox = BoundingBox(
                x=tb.bbox.x0,
                y=tb.bbox.y0,
                width=tb.bbox.x1 - tb.bbox.x0,
                height=tb.bbox.y1 - tb.bbox.y0,
            )
            block = Block(
                block_type=BlockType.TEXT,
                bbox=bbox,
                content=tb.text,
                style=Style(),
            )
            classified.append(block)

        return classified

    def _apply_content_processors(
        self, blocks: list[Block], page: pymupdf.Page
    ) -> list[Block]:
        """Apply content-specific processors to refine blocks.

        Args:
            blocks: Classified blocks
            page: PyMuPDF page for additional context

        Returns:
            Refined list of blocks
        """
        # For now, return blocks as-is
        # Full integration of processors would happen here
        # This is a placeholder for the orchestration logic
        return blocks[:]

    def _extract_images(self, page: pymupdf.Page) -> list[dict[str, Any]]:
        """Extract images from a page.

        Args:
            page: PyMuPDF page object

        Returns:
            List of image information dictionaries
        """
        images = []
        image_list = page.get_images()

        for img_index, img in enumerate(image_list):
            xref = img[0]
            bbox = page.get_image_bbox(img)
            images.append(
                {
                    "xref": xref,
                    "bbox": bbox,
                    "index": img_index,
                }
            )

        return images

    def _extract_metadata(self, pdf_path: str) -> dict[str, Any]:
        """Extract document metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary of metadata
        """
        doc = pymupdf.open(pdf_path)
        metadata = doc.metadata.copy()
        metadata["page_count"] = len(doc)
        doc.close()
        return metadata
