"""Whitespace analysis for document layout understanding.

This module implements advanced whitespace analysis to detect structural boundaries
and spatial relationships in PDF documents.
"""

from dataclasses import dataclass

from unpdf.processors.layout_analyzer import BoundingBox, TextBlock


@dataclass
class WhitespaceRegion:
    """Represents a region of whitespace in the document."""

    bbox: BoundingBox
    type: str  # "column_gap", "paragraph_gap", "section_gap"
    confidence: float


@dataclass
class SpatialRelationship:
    """Represents a spatial relationship between two blocks."""

    source_id: int
    target_id: int
    direction: str  # "up", "down", "left", "right"
    distance: float
    confidence: float


class WhitespaceAnalyzer:
    """Analyzes whitespace to detect structure and relationships."""

    def __init__(
        self,
        column_gap_threshold: float = 0.15,
        paragraph_gap_multiplier: float = 1.5,
        alignment_tolerance: float = 10.0,
    ):
        """Initialize whitespace analyzer.

        Args:
            column_gap_threshold: Minimum gap as fraction of page width for column boundary
            paragraph_gap_multiplier: Multiple of line height for paragraph boundary
            alignment_tolerance: Maximum pixel difference for alignment detection
        """
        self.column_gap_threshold = column_gap_threshold
        self.paragraph_gap_multiplier = paragraph_gap_multiplier
        self.alignment_tolerance = alignment_tolerance

    def detect_column_boundaries(
        self, blocks: list[TextBlock], page_width: float
    ) -> list[float]:
        """Detect column boundaries from vertical whitespace gaps.

        Args:
            blocks: List of text blocks
            page_width: Width of the page

        Returns:
            List of x-coordinates representing column boundaries
        """
        if not blocks:
            return []

        # Collect left and right edges separately
        left_edges = sorted([block.bbox.x0 for block in blocks])
        right_edges = sorted([block.bbox.x1 for block in blocks])

        # Find gaps between rightmost edges and leftmost edges of adjacent columns
        min_gap = page_width * self.column_gap_threshold
        boundaries: list[float] = []

        # For each right edge, find the nearest left edge to its right
        for right_edge in right_edges:
            for left_edge in left_edges:
                if left_edge > right_edge:
                    gap = left_edge - right_edge
                    if gap >= min_gap:
                        # Column boundary is in the middle of the gap
                        boundary = (right_edge + left_edge) / 2
                        # Avoid duplicates
                        if not boundaries or abs(boundary - boundaries[-1]) > 1.0:
                            boundaries.append(boundary)
                    break

        return boundaries

    def detect_paragraph_boundaries(
        self, blocks: list[TextBlock], avg_line_height: float
    ) -> list[tuple[int, int]]:
        """Detect paragraph boundaries from vertical spacing.

        Args:
            blocks: List of text blocks sorted by reading order
            avg_line_height: Average line height in the document

        Returns:
            List of (block_index, next_block_index) tuples marking paragraph breaks
        """
        if not blocks or avg_line_height <= 0:
            return []

        min_gap = avg_line_height * self.paragraph_gap_multiplier
        boundaries = []

        for i in range(len(blocks) - 1):
            current = blocks[i]
            next_block = blocks[i + 1]

            # Calculate vertical gap
            vertical_gap = next_block.bbox.y0 - current.bbox.y1

            if vertical_gap >= min_gap:
                boundaries.append((i, i + 1))

        return boundaries

    def detect_section_boundaries(
        self, blocks: list[TextBlock], avg_line_height: float
    ) -> list[int]:
        """Detect major section boundaries from large whitespace.

        Section boundaries are identified by gaps significantly larger than
        paragraph boundaries (typically 3-4x line height).

        Args:
            blocks: List of text blocks sorted by reading order
            avg_line_height: Average line height in the document

        Returns:
            List of block indices that start new sections
        """
        if not blocks or avg_line_height <= 0:
            return []

        # Section gap is much larger than paragraph gap
        min_gap = avg_line_height * self.paragraph_gap_multiplier * 2
        section_starts = []

        for i in range(len(blocks) - 1):
            current = blocks[i]
            next_block = blocks[i + 1]

            vertical_gap = next_block.bbox.y0 - current.bbox.y1

            if vertical_gap >= min_gap:
                section_starts.append(i + 1)

        return section_starts

    def build_spatial_graph(
        self, blocks: list[TextBlock]
    ) -> dict[int, dict[str, int | None]]:
        """Build spatial relationship graph between blocks.

        For each block, finds the nearest neighbor in each direction (up, down, left, right).

        Args:
            blocks: List of text blocks

        Returns:
            Dictionary mapping block index to nearest neighbors in each direction
        """
        if not blocks:
            return {}

        graph: dict[int, dict[str, int | None]] = {}

        for i, block in enumerate(blocks):
            neighbors: dict[str, int | None] = {
                "up": None,
                "down": None,
                "left": None,
                "right": None,
            }

            # Find nearest neighbor in each direction
            min_dist_up = float("inf")
            min_dist_down = float("inf")
            min_dist_left = float("inf")
            min_dist_right = float("inf")

            for j, other in enumerate(blocks):
                if i == j:
                    continue

                # Check if blocks are vertically aligned
                if self._is_vertically_aligned(block.bbox, other.bbox):
                    if other.bbox.y1 < block.bbox.y0:  # Above
                        dist = block.bbox.y0 - other.bbox.y1
                        if dist < min_dist_up:
                            min_dist_up = dist
                            neighbors["up"] = j
                    elif other.bbox.y0 > block.bbox.y1:  # Below
                        dist = other.bbox.y0 - block.bbox.y1
                        if dist < min_dist_down:
                            min_dist_down = dist
                            neighbors["down"] = j

                # Check if blocks are horizontally aligned
                if self._is_horizontally_aligned(block.bbox, other.bbox):
                    if other.bbox.x1 < block.bbox.x0:  # Left
                        dist = block.bbox.x0 - other.bbox.x1
                        if dist < min_dist_left:
                            min_dist_left = dist
                            neighbors["left"] = j
                    elif other.bbox.x0 > block.bbox.x1:  # Right
                        dist = other.bbox.x0 - block.bbox.x1
                        if dist < min_dist_right:
                            min_dist_right = dist
                            neighbors["right"] = j

            graph[i] = neighbors

        return graph

    def get_spatial_relationships(
        self, blocks: list[TextBlock]
    ) -> list[SpatialRelationship]:
        """Get detailed spatial relationships between blocks.

        Args:
            blocks: List of text blocks

        Returns:
            List of spatial relationships with confidence scores
        """
        graph = self.build_spatial_graph(blocks)
        relationships = []

        for source_idx, neighbors in graph.items():
            for direction, target_idx in neighbors.items():
                if target_idx is not None:
                    # Calculate distance and confidence
                    source = blocks[source_idx]
                    target = blocks[target_idx]

                    if direction in ("up", "down"):
                        distance = abs(
                            target.bbox.y0 - source.bbox.y1
                            if direction == "down"
                            else source.bbox.y0 - target.bbox.y1
                        )
                        # Confidence based on alignment quality
                        overlap = self._calculate_horizontal_overlap(
                            source.bbox, target.bbox
                        )
                        confidence = min(1.0, overlap / max(source.bbox.width, 1.0))
                    else:  # left, right
                        distance = abs(
                            target.bbox.x0 - source.bbox.x1
                            if direction == "right"
                            else source.bbox.x0 - target.bbox.x1
                        )
                        # Confidence based on alignment quality
                        overlap = self._calculate_vertical_overlap(
                            source.bbox, target.bbox
                        )
                        confidence = min(1.0, overlap / max(source.bbox.height, 1.0))

                    relationships.append(
                        SpatialRelationship(
                            source_id=source_idx,
                            target_id=target_idx,
                            direction=direction,
                            distance=distance,
                            confidence=confidence,
                        )
                    )

        return relationships

    def _is_vertically_aligned(self, bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        """Check if two bounding boxes are vertically aligned (share horizontal overlap)."""
        # Check if there's horizontal overlap
        overlap = min(bbox1.x1, bbox2.x1) - max(bbox1.x0, bbox2.x0)
        return overlap > 0 or abs(bbox1.x0 - bbox2.x0) <= self.alignment_tolerance

    def _is_horizontally_aligned(self, bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        """Check if two bounding boxes are horizontally aligned (share vertical overlap)."""
        # Check if there's vertical overlap
        overlap = min(bbox1.y1, bbox2.y1) - max(bbox1.y0, bbox2.y0)
        return overlap > 0 or abs(bbox1.y0 - bbox2.y0) <= self.alignment_tolerance

    def _calculate_horizontal_overlap(
        self, bbox1: BoundingBox, bbox2: BoundingBox
    ) -> float:
        """Calculate the horizontal overlap between two bounding boxes."""
        return max(0.0, min(bbox1.x1, bbox2.x1) - max(bbox1.x0, bbox2.x0))

    def _calculate_vertical_overlap(
        self, bbox1: BoundingBox, bbox2: BoundingBox
    ) -> float:
        """Calculate the vertical overlap between two bounding boxes."""
        return max(0.0, min(bbox1.y1, bbox2.y1) - max(bbox1.y0, bbox2.y0))


def calculate_avg_line_height(blocks: list[TextBlock]) -> float:
    """Calculate average line height from text blocks.

    Args:
        blocks: List of text blocks

    Returns:
        Average line height, or 0.0 if no blocks
    """
    if not blocks:
        return 0.0

    heights = [block.bbox.height for block in blocks if block.bbox.height > 0]
    if not heights:
        return 0.0

    return sum(heights) / len(heights)
