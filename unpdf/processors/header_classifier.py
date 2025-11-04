"""Header classification using font size, weight, position, and alignment analysis.

This module classifies text blocks as headers (H1-H6) based on:
- Font size ratios compared to body text
- Font weight (bold/normal)
- Position on page (top 20% for H1)
- Line count (headers are typically single line)
- Horizontal centering/alignment
"""

from dataclasses import dataclass
from enum import Enum

from unpdf.models.layout import BoundingBox


@dataclass
class TextBlock:
    """Text block with font and layout information."""

    text: str
    bbox: BoundingBox
    font_name: str
    font_size: float
    is_bold: bool = False
    is_italic: bool = False
    page_width: float = 612.0  # Default US Letter width
    page_height: float = 792.0  # Default US Letter height


class HeaderLevel(Enum):
    """Header level enumeration."""

    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6
    BODY = 0  # Not a header


class HeaderClassifier:
    """Classifies text blocks as headers based on font and layout analysis."""

    def __init__(
        self,
        body_font_size: float = 12.0,
        h1_min_ratio: float = 2.0,
        h2_min_ratio: float = 1.5,
        h2_max_ratio: float = 1.8,
        h3_min_ratio: float = 1.2,
        h3_max_ratio: float = 1.4,
        h4_max_ratio: float = 1.15,
        bold_weight: float = 0.3,
        size_weight: float = 0.5,
        position_weight: float = 0.1,
        alignment_weight: float = 0.1,
        min_confidence: float = 0.6,
    ):
        """Initialize header classifier.

        Args:
            body_font_size: Base body text font size
            h1_min_ratio: Minimum font size ratio for H1 (>2.0× body)
            h2_min_ratio: Minimum font size ratio for H2 (1.5-1.8× body)
            h2_max_ratio: Maximum font size ratio for H2
            h3_min_ratio: Minimum font size ratio for H3 (1.2-1.4× body)
            h3_max_ratio: Maximum font size ratio for H3
            h4_max_ratio: Maximum font size ratio for H4-H6
            bold_weight: Weight for bold font in confidence
            size_weight: Weight for font size in confidence
            position_weight: Weight for position in confidence
            alignment_weight: Weight for alignment in confidence
            min_confidence: Minimum confidence to classify as header
        """
        self.body_font_size = body_font_size
        self.h1_min_ratio = h1_min_ratio
        self.h2_min_ratio = h2_min_ratio
        self.h2_max_ratio = h2_max_ratio
        self.h3_min_ratio = h3_min_ratio
        self.h3_max_ratio = h3_max_ratio
        self.h4_max_ratio = h4_max_ratio
        self.bold_weight = bold_weight
        self.size_weight = size_weight
        self.position_weight = position_weight
        self.alignment_weight = alignment_weight
        self.min_confidence = min_confidence

    def calculate_font_size_ratio(self, block: TextBlock) -> float:
        """Calculate font size ratio relative to body text.

        Args:
            block: Text block to analyze

        Returns:
            Font size ratio (1.0 = same as body, 2.0 = twice body size)
        """
        if self.body_font_size == 0:
            return 1.0
        return block.font_size / self.body_font_size

    def is_single_line(self, block: TextBlock) -> bool:
        """Check if block is a single line.

        Args:
            block: Text block to analyze

        Returns:
            True if block appears to be single line
        """
        # Count newlines in text
        line_count = block.text.count("\n") + 1

        # Also check if height suggests multiple lines (with some tolerance)
        # Allow up to 1.5× font size for single line (accounts for line spacing)
        estimated_lines = (
            int(block.bbox.height / (block.font_size * 1.5))
            if block.font_size > 0
            else 1
        )

        return line_count == 1 and estimated_lines <= 1

    def is_in_top_region(self, block: TextBlock, threshold: float = 0.2) -> bool:
        """Check if block is in top region of page.

        Args:
            block: Text block to analyze
            threshold: Top region threshold (0.2 = top 20%)

        Returns:
            True if block is in top region
        """
        if block.page_height == 0:
            return False
        relative_position = block.bbox.y0 / block.page_height
        return relative_position < threshold

    def is_centered(self, block: TextBlock, tolerance: float = 0.1) -> bool:
        """Check if block is horizontally centered.

        Args:
            block: Text block to analyze
            tolerance: Center tolerance (0.1 = within 10% of center)

        Returns:
            True if block appears centered
        """
        if block.page_width == 0:
            return False

        # Calculate center of block
        block_center = (block.bbox.x0 + block.bbox.x1) / 2
        page_center = block.page_width / 2

        # Calculate relative distance from center
        distance_from_center = abs(block_center - page_center) / block.page_width

        return distance_from_center < tolerance

    def classify_by_size_ratio(self, ratio: float) -> HeaderLevel:
        """Classify header level based on font size ratio.

        Args:
            ratio: Font size ratio relative to body text

        Returns:
            Header level classification
        """
        if ratio >= self.h1_min_ratio:
            return HeaderLevel.H1
        elif self.h2_min_ratio <= ratio <= self.h2_max_ratio:
            return HeaderLevel.H2
        elif self.h3_min_ratio <= ratio <= self.h3_max_ratio:
            return HeaderLevel.H3
        elif ratio <= self.h4_max_ratio:
            # H4-H6 determined by other factors (bold, position)
            return HeaderLevel.H4
        else:
            return HeaderLevel.BODY

    def calculate_confidence(
        self,
        block: TextBlock,
        size_ratio: float,
        level: HeaderLevel,
    ) -> float:
        """Calculate confidence score for header classification.

        Args:
            block: Text block being classified
            size_ratio: Font size ratio
            level: Proposed header level

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Size score based on expected ratio for level
        if level == HeaderLevel.H1:
            size_score = min(1.0, (size_ratio - self.h1_min_ratio) / 0.5)
        elif level == HeaderLevel.H2:
            # How well does it fit in H2 range?
            if self.h2_min_ratio <= size_ratio <= self.h2_max_ratio:
                size_score = 1.0
            else:
                size_score = 0.5
        elif level == HeaderLevel.H3:
            if self.h3_min_ratio <= size_ratio <= self.h3_max_ratio:
                size_score = 1.0
            else:
                size_score = 0.5
        else:
            # H4-H6 or body
            size_score = 0.3 if size_ratio > 1.0 else 0.0

        # Bold score
        bold_score = 1.0 if block.is_bold else 0.0

        # Position score (top of page boosts confidence)
        position_score = 1.0 if self.is_in_top_region(block) else 0.5

        # Alignment score (centered headers boost confidence)
        alignment_score = 1.0 if self.is_centered(block) else 0.5

        # Weighted combination
        confidence = (
            self.size_weight * size_score
            + self.bold_weight * bold_score
            + self.position_weight * position_score
            + self.alignment_weight * alignment_score
        )

        return confidence

    def classify_header(self, block: TextBlock) -> tuple[HeaderLevel, float]:
        """Classify a text block as a header.

        Args:
            block: Text block to classify

        Returns:
            Tuple of (header_level, confidence)
        """
        # Check if single line (headers are typically single line)
        if not self.is_single_line(block):
            return HeaderLevel.BODY, 0.0

        # Calculate font size ratio
        size_ratio = self.calculate_font_size_ratio(block)

        # Classify by size
        level = self.classify_by_size_ratio(size_ratio)

        # Refine H4-H6 classification based on other factors
        if level == HeaderLevel.H4:
            if block.is_bold:
                if self.is_in_top_region(block):
                    level = HeaderLevel.H4
                else:
                    level = HeaderLevel.H5
            else:
                level = HeaderLevel.H6

        # Calculate confidence
        confidence = self.calculate_confidence(block, size_ratio, level)

        # Return BODY if confidence too low
        if confidence < self.min_confidence and level != HeaderLevel.BODY:
            return HeaderLevel.BODY, confidence

        return level, confidence

    def classify_headers(
        self, blocks: list[TextBlock]
    ) -> list[tuple[TextBlock, HeaderLevel, float]]:
        """Classify multiple text blocks as headers.

        Args:
            blocks: List of text blocks to classify

        Returns:
            List of (block, header_level, confidence) tuples
        """
        results: list[tuple[TextBlock, HeaderLevel, float]] = []
        for block in blocks:
            level, confidence = self.classify_header(block)
            if level != HeaderLevel.BODY:
                results.append((block, level, confidence))
        return results
