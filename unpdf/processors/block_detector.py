"""Unified block detection and classification system.

This module integrates all pattern-based classifiers to detect and classify
content blocks from PDF layouts.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from unpdf.processors.block_classifier import BlockClassifier, BlockType
from unpdf.processors.caption_detector import Caption, CaptionDetector
from unpdf.processors.code_detector import CodeDetector
from unpdf.processors.footnote_detector import Footnote, FootnoteDetector
from unpdf.processors.header_classifier import HeaderClassifier, HeaderLevel
from unpdf.processors.list_detector import ListDetector, ListItem


class BlockCategory(Enum):
    """High-level block category."""

    HEADER = "header"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    IMAGE = "image"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    HORIZONTAL_RULE = "horizontal_rule"
    BLOCKQUOTE = "blockquote"
    UNKNOWN = "unknown"


@dataclass
class DetectedBlock:
    """Unified representation of a detected content block."""

    category: BlockCategory
    bbox: Any  # BoundingBox
    text: str
    confidence: float
    page_num: int

    # Type-specific attributes
    block_type: BlockType | None = None
    header_level: HeaderLevel | None = None
    list_item_type: str | None = None  # "bullet", "numbered", "lettered", "roman"
    list_items: list[ListItem] | None = None
    caption: Caption | None = None
    footnote: Footnote | None = None
    metadata: dict[str, Any] | None = None


class BlockDetector:
    """Unified block detector that orchestrates all classifiers."""

    def __init__(
        self,
        use_lists: bool = True,
        use_code: bool = True,
        use_headers: bool = True,
        use_captions: bool = True,
        use_footnotes: bool = True,
    ):
        """Initialize block detector with optional feature flags.

        Args:
            use_lists: Enable list detection
            use_code: Enable code block detection
            use_headers: Enable header classification
            use_captions: Enable caption detection
            use_footnotes: Enable footnote detection
        """
        self.base_classifier = BlockClassifier()
        self.list_detector = ListDetector() if use_lists else None
        self.code_detector = CodeDetector() if use_code else None
        self.header_classifier = HeaderClassifier() if use_headers else None
        self.caption_detector = CaptionDetector() if use_captions else None
        self.footnote_detector = FootnoteDetector() if use_footnotes else None

    def detect_blocks(
        self,
        text_blocks: list[Any],
        body_font_size: float,
        page_num: int = 0,
        images: list[Any] | None = None,
        tables: list[Any] | None = None,
    ) -> list[DetectedBlock]:
        """Detect and classify all blocks on a page.

        Args:
            text_blocks: List of text blocks with bbox, text, font properties
            body_font_size: Document body font size for relative sizing
            page_num: Page number for tracking
            images: Optional list of image regions
            tables: Optional list of table regions

        Returns:
            List of detected blocks with categories and metadata
        """
        detected_blocks: list[DetectedBlock] = []

        # First pass: Base classification
        for block in text_blocks:
            block_type = self.base_classifier.classify_block(block, body_font_size)
            category = self._map_block_type_to_category(block_type)

            detected_block = DetectedBlock(
                category=category,
                bbox=getattr(block, "bbox", None),
                text=getattr(block, "text", ""),
                confidence=0.5,  # Base confidence
                page_num=page_num,
                block_type=block_type,
            )
            detected_blocks.append(detected_block)

        # Second pass: Specialized classification
        detected_blocks = self._classify_headers(detected_blocks, body_font_size)
        detected_blocks = self._detect_lists(detected_blocks)
        detected_blocks = self._detect_code_blocks(detected_blocks)

        # Third pass: Contextual detection (requires other elements)
        if images or tables:
            detected_blocks = self._detect_captions(
                detected_blocks, images or [], tables or []
            )

        # Fourth pass: Footnote detection
        detected_blocks = self._detect_footnotes(detected_blocks)

        return detected_blocks

    def _map_block_type_to_category(self, block_type: BlockType) -> BlockCategory:
        """Map BlockType to BlockCategory."""
        mapping = {
            BlockType.HEADER: BlockCategory.HEADER,
            BlockType.BODY_TEXT: BlockCategory.PARAGRAPH,
            BlockType.LIST_ITEM: BlockCategory.LIST,
            BlockType.CODE: BlockCategory.CODE,
            BlockType.TABLE: BlockCategory.TABLE,
            BlockType.CAPTION: BlockCategory.CAPTION,
            BlockType.FOOTNOTE: BlockCategory.FOOTNOTE,
            BlockType.HORIZONTAL_RULE: BlockCategory.HORIZONTAL_RULE,
            BlockType.BLOCKQUOTE: BlockCategory.BLOCKQUOTE,
        }
        return mapping.get(block_type, BlockCategory.UNKNOWN)

    def _classify_headers(
        self, blocks: list[DetectedBlock], body_font_size: float
    ) -> list[DetectedBlock]:
        """Refine header classification using specialized classifier."""
        if not self.header_classifier:
            return blocks

        for block in blocks:
            if block.category == BlockCategory.HEADER:
                # Extract font size from metadata if available
                font_size = body_font_size * 1.5  # Default assumption
                if block.metadata and "font_size" in block.metadata:
                    font_size = block.metadata["font_size"]

                # Classify header level
                level = self.header_classifier.classify_header(
                    text=block.text,
                    font_size=font_size,
                    body_font_size=body_font_size,
                    is_bold=(
                        block.metadata.get("is_bold", False)
                        if block.metadata
                        else False
                    ),
                    position_y=block.bbox.y0 if block.bbox else 0,
                    page_height=792,  # Standard letter height, should be passed in
                )

                if level:
                    block.header_level = level
                    block.confidence = min(block.confidence + 0.3, 1.0)

        return blocks

    def _detect_lists(self, blocks: list[DetectedBlock]) -> list[DetectedBlock]:
        """Detect and classify list structures."""
        if not self.list_detector:
            return blocks

        # Group blocks by vertical proximity for list detection
        text_blocks_data = []
        for i, block in enumerate(blocks):
            if block.category in (BlockCategory.PARAGRAPH, BlockCategory.LIST):
                text_blocks_data.append(
                    {
                        "index": i,
                        "text": block.text,
                        "x0": block.bbox.x0 if block.bbox else 0,
                        "y0": block.bbox.y0 if block.bbox else 0,
                    }
                )

        # Detect lists
        detected_lists = self.list_detector.detect_lists(text_blocks_data)

        # Update blocks with list information
        for list_items in detected_lists:
            for item in list_items:
                block_index = getattr(item, "block_index", None) or getattr(
                    item, "line_number", None
                )
                if block_index is not None and block_index < len(blocks):
                    block = blocks[block_index]
                    block.category = BlockCategory.LIST
                    block.list_item_type = item.item_type
                    if not block.list_items:
                        block.list_items = []
                    block.list_items.append(item)
                    block.confidence = min(block.confidence + 0.25, 1.0)

        return blocks

    def _detect_code_blocks(self, blocks: list[DetectedBlock]) -> list[DetectedBlock]:
        """Detect code blocks using specialized detector."""
        if not self.code_detector:
            return blocks

        for block in blocks:
            if block.category in (BlockCategory.PARAGRAPH, BlockCategory.CODE):
                # Check if block is a code block
                is_code = self.code_detector.is_code_block(
                    text=block.text,
                    char_widths=[1.0] * len(block.text),  # Placeholder
                    indent=0,  # Would need to extract from block
                )

                if is_code:
                    block.category = BlockCategory.CODE
                    block.confidence = min(block.confidence + 0.35, 1.0)

        return blocks

    def _detect_captions(
        self,
        blocks: list[DetectedBlock],
        images: list[Any],
        tables: list[Any],
    ) -> list[DetectedBlock]:
        """Detect captions and link them to images/tables."""
        if not self.caption_detector:
            return blocks

        # Find potential captions
        for block in blocks:
            if block.category == BlockCategory.PARAGRAPH:
                caption = self.caption_detector.detect_caption(
                    text=block.text,
                    bbox=block.bbox,
                    images=images,
                    tables=tables,
                )

                if caption:
                    block.category = BlockCategory.CAPTION
                    block.caption = caption
                    block.confidence = caption.confidence

        return blocks

    def _detect_footnotes(self, blocks: list[DetectedBlock]) -> list[DetectedBlock]:
        """Detect footnotes and link to references."""
        if not self.footnote_detector:
            return blocks

        # Extract text blocks for footnote detection
        text_blocks = []
        for i, block in enumerate(blocks):
            text_blocks.append(
                {
                    "index": i,
                    "text": block.text,
                    "bbox": block.bbox,
                    "font_size": (
                        block.metadata.get("font_size", 12) if block.metadata else 12
                    ),
                }
            )

        # Detect footnotes
        footnotes = self.footnote_detector.detect_footnotes(
            text_blocks=text_blocks,
            body_font_size=12,  # Should be passed in
            page_height=792,  # Should be passed in
        )

        # Update blocks with footnote information
        for footnote in footnotes:
            if (
                footnote.footer_block_index is not None
                and footnote.footer_block_index < len(blocks)
            ):
                block = blocks[footnote.footer_block_index]
                block.category = BlockCategory.FOOTNOTE
                block.footnote = footnote
                block.confidence = footnote.confidence

        return blocks

    def get_reading_order(self, blocks: list[DetectedBlock]) -> list[DetectedBlock]:
        """Sort blocks into natural reading order.

        Args:
            blocks: List of detected blocks

        Returns:
            Blocks sorted in reading order (top-to-bottom, left-to-right)
        """
        # Simple reading order: sort by y-coordinate (top to bottom)
        # then x-coordinate (left to right) for ties
        return sorted(
            blocks,
            key=lambda b: (
                b.bbox.y0 if b.bbox else 0,
                b.bbox.x0 if b.bbox else 0,
            ),
        )

    def filter_by_confidence(
        self, blocks: list[DetectedBlock], min_confidence: float = 0.6
    ) -> list[DetectedBlock]:
        """Filter blocks by minimum confidence threshold.

        Args:
            blocks: List of detected blocks
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            Filtered list of blocks
        """
        return [b for b in blocks if b.confidence >= min_confidence]

    def group_blocks_by_category(
        self, blocks: list[DetectedBlock]
    ) -> dict[BlockCategory, list[DetectedBlock]]:
        """Group blocks by category for easier processing.

        Args:
            blocks: List of detected blocks

        Returns:
            Dictionary mapping category to list of blocks
        """
        groups: dict[BlockCategory, list[DetectedBlock]] = {}
        for block in blocks:
            if block.category not in groups:
                groups[block.category] = []
            groups[block.category].append(block)
        return groups
