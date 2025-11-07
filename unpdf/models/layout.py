"""Intermediate layout representation for PDF content.

This module defines data structures for representing parsed PDF layout
before rendering to Markdown. It provides a clean separation between
extraction, analysis, and rendering.
"""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BlockType(Enum):
    """Types of content blocks."""

    TEXT = "text"
    HEADING = "heading"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    IMAGE = "image"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "horizontal_rule"


@dataclass
class Style:
    """Style properties for a text block.

    Attributes:
        font: Font family name
        size: Font size in points
        weight: Font weight (e.g., "normal", "bold", 400-900)
        style: Font style (e.g., "normal", "italic")
        color: RGB color tuple (0.0-1.0)
        monospace: Whether the font is monospace
        strikethrough: Whether text has strikethrough
        underline: Whether text is underlined
    """

    font: str | None = None
    size: float | None = None
    weight: str | int | None = None
    style: str | None = None
    color: tuple[float, float, float] | None = None
    monospace: bool = False
    strikethrough: bool = False
    underline: bool = False


@dataclass
class Span:
    """A text span with formatting.

    Attributes:
        text: The text content
        bold: Whether text is bold
        italic: Whether text is italic
        font_size: Font size in points
        font_name: Font family name
    """

    text: str
    bold: bool = False
    italic: bool = False
    font_size: float | None = None
    font_name: str | None = None


@dataclass
class BoundingBox:
    """Bounding box coordinates.

    Attributes:
        x: Left x coordinate
        y: Bottom y coordinate
        width: Width of box
        height: Height of box
    """

    x: float
    y: float
    width: float
    height: float

    @property
    def x0(self) -> float:
        """Left edge."""
        return self.x

    @property
    def y0(self) -> float:
        """Bottom edge."""
        return self.y

    @property
    def x1(self) -> float:
        """Right edge."""
        return self.x + self.width

    @property
    def y1(self) -> float:
        """Top edge."""
        return self.y + self.height

    @property
    def center_x(self) -> float:
        """Horizontal center."""
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        """Vertical center."""
        return self.y + self.height / 2

    @property
    def center(self) -> tuple[float, float]:
        """Center point (x, y)."""
        return (self.center_x, self.center_y)

    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return self.width * self.height

    def overlaps(self, other: "BoundingBox") -> bool:
        """Check if this box overlaps with another."""
        return not (
            self.x1 < other.x0
            or self.x0 > other.x1
            or self.y1 < other.y0
            or self.y0 > other.y1
        )

    def contains(self, other: "BoundingBox") -> bool:
        """Check if this box contains another."""
        return (
            self.x0 <= other.x0
            and self.y0 <= other.y0
            and self.x1 >= other.x1
            and self.y1 >= other.y1
        )

    def intersection_area(self, other: "BoundingBox") -> float:
        """Calculate the area of intersection with another box.

        Args:
            other: Other bounding box

        Returns:
            Area of intersection in square units
        """
        if not self.overlaps(other):
            return 0.0

        x_overlap = max(0, min(self.x1, other.x1) - max(self.x0, other.x0))
        y_overlap = max(0, min(self.y1, other.y1) - max(self.y0, other.y0))

        return x_overlap * y_overlap

    def overlap_percentage(self, other: "BoundingBox") -> float:
        """Calculate percentage of overlap between boxes.

        Returns:
            Percentage of this box that overlaps with other (0.0-1.0)
        """
        intersection = self.intersection_area(other)

        if self.area == 0:
            return 0.0

        return intersection / self.area

    def contains_point(self, point: tuple[float, float]) -> bool:
        """Check if this box contains a point.

        Args:
            point: (x, y) coordinates

        Returns:
            True if point is inside box
        """
        x, y = point
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


@dataclass
class Block:
    """A content block in the document.

    Attributes:
        block_type: Type of block
        bbox: Bounding box
        content: Text content or structured data
        style: Style properties
        reading_order: Position in reading order (lower = earlier)
        confidence: Confidence score (0.0-1.0)
        metadata: Additional metadata
        children: Child blocks (for hierarchical structures)
        spans: Optional list of formatted spans (for inline formatting)
    """

    block_type: BlockType
    bbox: BoundingBox
    content: str | dict | None = None
    style: Style | None = None
    reading_order: int = 0
    confidence: float = 1.0
    metadata: dict[str, Any] | None = None
    children: list["Block"] | None = None
    spans: list[Span] | None = None


@dataclass
class Page:
    """A page in the document.

    Attributes:
        number: Page number (1-indexed for display)
        width: Page width in points
        height: Page height in points
        blocks: Content blocks on this page
        metadata: Additional metadata
    """

    number: int
    width: float
    height: float
    blocks: list[Block] = field(default_factory=list)
    metadata: dict[str, Any] | None = None


@dataclass
class Document:
    """Complete document representation.

    Attributes:
        pages: List of pages
        metadata: Document-level metadata (title, author, etc.)
    """

    pages: list[Page] = field(default_factory=list)
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pages": [
                {
                    "number": page.number,
                    "width": page.width,
                    "height": page.height,
                    "blocks": [
                        {
                            "type": block.block_type.value,
                            "bbox": {
                                "x": block.bbox.x,
                                "y": block.bbox.y,
                                "width": block.bbox.width,
                                "height": block.bbox.height,
                            },
                            "content": block.content,
                            "style": asdict(block.style) if block.style else None,
                            "reading_order": block.reading_order,
                            "confidence": block.confidence,
                            "metadata": block.metadata,
                        }
                        for block in page.blocks
                    ],
                    "metadata": page.metadata,
                }
                for page in self.pages
            ],
            "metadata": self.metadata,
        }

    def to_json(self, path: str | Path | None = None, indent: int = 2) -> str:
        """Serialize to JSON.

        Args:
            path: Optional file path to write to
            indent: JSON indentation level

        Returns:
            JSON string
        """
        json_str = json.dumps(self.to_dict(), indent=indent)

        if path:
            Path(path).write_text(json_str, encoding="utf-8")

        return json_str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        """Create Document from dictionary."""
        doc = cls(metadata=data.get("metadata"))

        for page_data in data.get("pages", []):
            page = Page(
                number=page_data["number"],
                width=page_data["width"],
                height=page_data["height"],
                metadata=page_data.get("metadata"),
            )

            for block_data in page_data.get("blocks", []):
                bbox = BoundingBox(**block_data["bbox"])
                style = (
                    Style(**block_data["style"]) if block_data.get("style") else None
                )
                block = Block(
                    block_type=BlockType(block_data["type"]),
                    bbox=bbox,
                    content=block_data.get("content"),
                    style=style,
                    reading_order=block_data.get("reading_order", 0),
                    confidence=block_data.get("confidence", 1.0),
                    metadata=block_data.get("metadata"),
                )
                page.blocks.append(block)

            doc.pages.append(page)

        return doc

    @classmethod
    def from_json(
        cls, json_str: str | None = None, path: str | Path | None = None
    ) -> "Document":
        """Load Document from JSON.

        Args:
            json_str: JSON string to parse
            path: Path to JSON file

        Returns:
            Document instance
        """
        if path:
            json_str = Path(path).read_text(encoding="utf-8")
        elif json_str is None:
            raise ValueError("Either json_str or path must be provided")

        data = json.loads(json_str)
        return cls.from_dict(data)
