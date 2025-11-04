"""Caption detection for tables and figures in PDFs.

This module detects and links captions to tables and figures using:
- Keyword matching (Table, Figure, Fig., Diagram)
- Proximity analysis (<50 pixels)
- Horizontal overlap (>70%)
- Numbering pattern detection

Google Style docstrings.
"""

import re
from dataclasses import dataclass

from unpdf.models.layout import BoundingBox


@dataclass
class Caption:
    """Represents a detected caption."""

    text: str
    bbox: BoundingBox
    caption_type: str  # 'table', 'figure', 'diagram', etc.
    number: str | None = None  # e.g., '1', '2.3'
    confidence: float = 0.0


@dataclass
class CaptionLink:
    """Links a caption to its referenced element."""

    caption: Caption
    element_bbox: BoundingBox
    distance: float
    overlap: float
    confidence: float


class CaptionDetector:
    """Detects and links captions to tables and figures."""

    # Keywords that indicate captions
    CAPTION_KEYWORDS = [
        r"\bTable\b",
        r"\bFigure\b",
        r"\bFig\b\.",
        r"\bDiagram\b",
        r"\bChart\b",
        r"\bGraph\b",
        r"\bImage\b",
        r"\bPhoto\b",
        r"\bIllustration\b",
    ]

    # Numbering patterns (e.g., "Table 1", "Figure 2.3")
    NUMBERING_PATTERN = re.compile(
        r"(?:Table|Figure|Fig\.|Diagram|Chart|Graph)\s+(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    def __init__(
        self,
        max_distance: float = 50.0,
        min_overlap: float = 0.7,
        confidence_threshold: float = 0.6,
    ):
        """Initialize caption detector.

        Args:
            max_distance: Maximum vertical distance in pixels between caption and element
            min_overlap: Minimum horizontal overlap ratio (0-1)
            confidence_threshold: Minimum confidence for linking
        """
        self.max_distance = max_distance
        self.min_overlap = min_overlap
        self.confidence_threshold = confidence_threshold

        # Compile keyword patterns
        self.keyword_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.CAPTION_KEYWORDS
        ]

    def detect_captions(
        self, text_blocks: list[tuple[str, BoundingBox]]
    ) -> list[Caption]:
        """Detect caption candidates in text blocks.

        Args:
            text_blocks: List of (text, bbox) tuples

        Returns:
            List of detected captions
        """
        captions = []

        for text, bbox in text_blocks:
            # Check for caption keywords
            caption_type = self._get_caption_type(text)
            if not caption_type:
                continue

            # Extract numbering
            number = self._extract_number(text)

            # Calculate confidence based on multiple signals
            confidence = self._calculate_caption_confidence(text, bbox)

            captions.append(
                Caption(
                    text=text,
                    bbox=bbox,
                    caption_type=caption_type,
                    number=number,
                    confidence=confidence,
                )
            )

        return captions

    def link_captions(
        self,
        captions: list[Caption],
        element_bboxes: list[BoundingBox],
    ) -> list[CaptionLink]:
        """Link captions to their referenced elements.

        Args:
            captions: List of detected captions
            element_bboxes: List of element bounding boxes (tables, figures, etc.)

        Returns:
            List of caption-element links
        """
        links = []

        for caption in captions:
            best_link = self._find_best_match(caption, element_bboxes)
            if best_link and best_link.confidence >= self.confidence_threshold:
                links.append(best_link)

        return links

    def _get_caption_type(self, text: str) -> str | None:
        """Determine caption type from text.

        Args:
            text: Caption text

        Returns:
            Caption type ('table', 'figure', etc.) or None
        """
        text_lower = text.lower()

        # Check for explicit caption keywords at the start (higher priority)
        if re.match(r"^\s*table\b", text_lower):
            return "table"
        elif re.match(r"^\s*(?:figure|fig\.\s)", text_lower):
            return "figure"
        elif re.match(r"^\s*diagram\b", text_lower):
            return "diagram"
        elif re.match(r"^\s*chart\b", text_lower):
            return "chart"
        elif re.match(r"^\s*graph\b", text_lower):
            return "graph"

        # Fallback to anywhere in text (lower priority)
        if re.search(r"\btable\b", text_lower):
            return "table"
        elif re.search(r"\b(?:figure|fig\.\s)", text_lower):
            return "figure"
        elif re.search(r"\bdiagram\b", text_lower):
            return "diagram"
        elif re.search(r"\bchart\b", text_lower):
            return "chart"
        elif re.search(r"\bgraph\b", text_lower):
            return "graph"
        elif re.search(r"\b(?:image|photo|illustration)\b", text_lower):
            return "image"

        return None

    def _extract_number(self, text: str) -> str | None:
        """Extract numbering from caption text.

        Args:
            text: Caption text

        Returns:
            Number string or None
        """
        match = self.NUMBERING_PATTERN.search(text)
        if match:
            return match.group(1)
        return None

    def _calculate_caption_confidence(self, text: str, bbox: BoundingBox) -> float:
        """Calculate confidence score for caption detection.

        Args:
            text: Caption text
            bbox: Caption bounding box

        Returns:
            Confidence score (0-1)
        """
        score = 0.0

        # Keyword match (40%)
        if any(pattern.search(text) for pattern in self.keyword_patterns):
            score += 0.4

        # Has numbering (30%)
        if self._extract_number(text):
            score += 0.3

        # Short text length (20%) - captions are typically concise
        # Consider <150 chars as typical caption length
        if len(text) < 150:
            score += 0.2 * min(1.0, (150 - len(text)) / 150)

        # Single line (10%) - most captions are single line
        if "\n" not in text:
            score += 0.1

        return min(1.0, score)

    def _find_best_match(
        self, caption: Caption, element_bboxes: list[BoundingBox]
    ) -> CaptionLink | None:
        """Find the best matching element for a caption.

        Args:
            caption: Caption to match
            element_bboxes: List of element bounding boxes

        Returns:
            Best caption link or None
        """
        best_link = None
        best_score = 0.0

        for elem_bbox in element_bboxes:
            # Calculate vertical distance
            distance = self._vertical_distance(caption.bbox, elem_bbox)
            if distance > self.max_distance:
                continue

            # Calculate horizontal overlap
            overlap = self._horizontal_overlap(caption.bbox, elem_bbox)
            if overlap < self.min_overlap:
                continue

            # Calculate confidence
            confidence = self._calculate_link_confidence(
                caption, elem_bbox, distance, overlap
            )

            if confidence > best_score:
                best_score = confidence
                best_link = CaptionLink(
                    caption=caption,
                    element_bbox=elem_bbox,
                    distance=distance,
                    overlap=overlap,
                    confidence=confidence,
                )

        return best_link

    def _vertical_distance(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate vertical distance between two bounding boxes.

        Args:
            bbox1: First bounding box
            bbox2: Second bounding box

        Returns:
            Vertical distance in pixels (0 if overlapping)
        """
        # If they overlap vertically, distance is 0
        if bbox1.y0 <= bbox2.y1 and bbox2.y0 <= bbox1.y1:
            return 0.0

        # Otherwise, measure gap between closest edges
        if bbox1.y0 > bbox2.y1:
            return bbox1.y0 - bbox2.y1
        else:
            return bbox2.y0 - bbox1.y1

    def _horizontal_overlap(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate horizontal overlap ratio between two bounding boxes.

        Args:
            bbox1: First bounding box
            bbox2: Second bounding box

        Returns:
            Overlap ratio (0-1)
        """
        # Calculate overlap width
        overlap_left = max(bbox1.x0, bbox2.x0)
        overlap_right = min(bbox1.x1, bbox2.x1)
        overlap_width = max(0.0, overlap_right - overlap_left)

        # Calculate average width
        width1 = bbox1.width
        width2 = bbox2.width
        avg_width = (width1 + width2) / 2

        if avg_width == 0:
            return 0.0

        return overlap_width / avg_width

    def _calculate_link_confidence(
        self,
        caption: Caption,
        elem_bbox: BoundingBox,
        distance: float,
        overlap: float,
    ) -> float:
        """Calculate confidence score for caption-element link.

        Scoring formula:
        - 40% keyword match
        - 30% position match (distance)
        - 20% style match (overlap)
        - 10% context match (numbering)

        Args:
            caption: Caption object
            elem_bbox: Element bounding box
            distance: Vertical distance
            overlap: Horizontal overlap ratio

        Returns:
            Confidence score (0-1)
        """
        score = 0.0

        # Keyword match (40%) - already in caption.confidence
        score += 0.4 * caption.confidence

        # Position match (30%) - closer is better
        distance_score = max(0.0, 1.0 - (distance / self.max_distance))
        score += 0.3 * distance_score

        # Style match (20%) - overlap ratio
        score += 0.2 * overlap

        # Context match (10%) - has numbering
        if caption.number:
            score += 0.1

        return min(1.0, score)
