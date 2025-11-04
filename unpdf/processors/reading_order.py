"""Reading order computation using spatial graph analysis.

This module implements sophisticated reading order determination using
directed spatial graphs, topological sorting, and multi-column detection.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unpdf.models.layout import Block

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """Types of spatial relationships between blocks."""

    ABOVE = "above"
    BELOW = "below"
    LEFT = "left"
    RIGHT = "right"
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"
    NEAR = "near"


@dataclass
class SpatialEdge:
    """Edge in the spatial graph representing a relationship between blocks."""

    from_block_id: int
    to_block_id: int
    relation: RelationType
    weight: float  # Distance-based weight
    confidence: float = 1.0  # Confidence in this relationship


@dataclass
class SpatialGraph:
    """Directed graph of spatial relationships between layout blocks."""

    blocks: dict[int, "Block"] = field(default_factory=dict)
    edges: list[SpatialEdge] = field(default_factory=list)
    adjacency: dict[int, list[SpatialEdge]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add_block(self, block_id: int, block: "Block") -> None:
        """Add a block to the graph.

        Args:
            block_id: Unique identifier for the block.
            block: Layout block to add.
        """
        self.blocks[block_id] = block

    def add_edge(self, edge: SpatialEdge) -> None:
        """Add an edge to the graph.

        Args:
            edge: Spatial edge to add.
        """
        self.edges.append(edge)
        self.adjacency[edge.from_block_id].append(edge)

    def get_outgoing_edges(self, block_id: int) -> list[SpatialEdge]:
        """Get all outgoing edges from a block.

        Args:
            block_id: Block identifier.

        Returns:
            List of outgoing edges.
        """
        return self.adjacency.get(block_id, [])

    def get_neighbors(
        self, block_id: int, relation: RelationType | None = None
    ) -> list[int]:
        """Get neighboring block IDs.

        Args:
            block_id: Block identifier.
            relation: Optional relation type to filter by.

        Returns:
            List of neighboring block IDs.
        """
        edges = self.get_outgoing_edges(block_id)
        if relation is not None:
            edges = [e for e in edges if e.relation == relation]
        return [e.to_block_id for e in edges]


class SpatialGraphBuilder:
    """Builds spatial graphs from layout blocks."""

    def __init__(
        self,
        vertical_threshold: float = 10.0,
        horizontal_threshold: float = 10.0,
        proximity_threshold: float = 50.0,
    ):
        """Initialize the spatial graph builder.

        Args:
            vertical_threshold: Max vertical distance for above/below relations (pixels).
            horizontal_threshold: Max horizontal distance for left/right relations (pixels).
            proximity_threshold: Max distance for "near" relation (pixels).
        """
        self.vertical_threshold = vertical_threshold
        self.horizontal_threshold = horizontal_threshold
        self.proximity_threshold = proximity_threshold

    def build(self, blocks: list["Block"]) -> SpatialGraph:
        """Build a spatial graph from layout blocks.

        Args:
            blocks: List of layout blocks.

        Returns:
            Spatial graph with relationships.
        """
        graph = SpatialGraph()

        # Add all blocks to graph
        for idx, block in enumerate(blocks):
            graph.add_block(idx, block)

        # Build relationships between all pairs
        for i, block_i in enumerate(blocks):
            for j, block_j in enumerate(blocks):
                if i == j:
                    continue

                # Check containment
                if self._contains(block_i, block_j):
                    edge = SpatialEdge(
                        from_block_id=i,
                        to_block_id=j,
                        relation=RelationType.CONTAINS,
                        weight=0.0,
                        confidence=1.0,
                    )
                    graph.add_edge(edge)
                    continue

                if self._contains(block_j, block_i):
                    edge = SpatialEdge(
                        from_block_id=i,
                        to_block_id=j,
                        relation=RelationType.CONTAINED_BY,
                        weight=0.0,
                        confidence=1.0,
                    )
                    graph.add_edge(edge)
                    continue

                # Check vertical relationships (above/below)
                if self._is_above(block_i, block_j):
                    distance = self._vertical_distance(block_i, block_j)
                    edge = SpatialEdge(
                        from_block_id=i,
                        to_block_id=j,
                        relation=RelationType.BELOW,
                        weight=distance,
                        confidence=self._compute_confidence(
                            distance, self.vertical_threshold
                        ),
                    )
                    graph.add_edge(edge)

                # Check horizontal relationships (left/right)
                if self._is_left_of(block_i, block_j):
                    distance = self._horizontal_distance(block_i, block_j)
                    edge = SpatialEdge(
                        from_block_id=i,
                        to_block_id=j,
                        relation=RelationType.RIGHT,
                        weight=distance,
                        confidence=self._compute_confidence(
                            distance, self.horizontal_threshold
                        ),
                    )
                    graph.add_edge(edge)

                # Check proximity
                distance = self._euclidean_distance(block_i, block_j)
                if distance < self.proximity_threshold:
                    edge = SpatialEdge(
                        from_block_id=i,
                        to_block_id=j,
                        relation=RelationType.NEAR,
                        weight=distance,
                        confidence=self._compute_confidence(
                            distance, self.proximity_threshold
                        ),
                    )
                    graph.add_edge(edge)

        return graph

    def _contains(self, block_i: "Block", block_j: "Block") -> bool:
        """Check if block_i contains block_j."""
        return (
            block_i.bbox.x0 <= block_j.bbox.x0
            and block_i.bbox.y0 <= block_j.bbox.y0
            and block_i.bbox.x1 >= block_j.bbox.x1
            and block_i.bbox.y1 >= block_j.bbox.y1
        )

    def _is_above(self, block_i: "Block", block_j: "Block") -> bool:
        """Check if block_i is above block_j with horizontal overlap."""
        # Block i is above if its bottom is above block j's top
        is_vertically_above = block_i.bbox.y1 < block_j.bbox.y0
        # Check if they have horizontal overlap (aligned vertically)
        horizontal_overlap = (
            block_i.bbox.x0 < block_j.bbox.x1 + self.horizontal_threshold
            and block_i.bbox.x1 > block_j.bbox.x0 - self.horizontal_threshold
        )
        return is_vertically_above and horizontal_overlap

    def _is_left_of(self, block_i: "Block", block_j: "Block") -> bool:
        """Check if block_i is left of block_j with vertical overlap."""
        # Block i is left if its right edge is left of block j's left edge
        is_horizontally_left = block_i.bbox.x1 < block_j.bbox.x0
        # Check if they have vertical overlap (aligned horizontally)
        vertical_overlap = (
            block_i.bbox.y0 < block_j.bbox.y1 + self.vertical_threshold
            and block_i.bbox.y1 > block_j.bbox.y0 - self.vertical_threshold
        )
        return is_horizontally_left and vertical_overlap

    def _vertical_distance(self, block_i: "Block", block_j: "Block") -> float:
        """Compute vertical distance between blocks."""
        return abs(block_i.bbox.y1 - block_j.bbox.y0)

    def _horizontal_distance(self, block_i: "Block", block_j: "Block") -> float:
        """Compute horizontal distance between blocks."""
        return abs(block_i.bbox.x1 - block_j.bbox.x0)

    def _euclidean_distance(self, block_i: "Block", block_j: "Block") -> float:
        """Compute Euclidean distance between block centers."""
        center_i_x = (block_i.bbox.x0 + block_i.bbox.x1) / 2.0
        center_i_y = (block_i.bbox.y0 + block_i.bbox.y1) / 2.0
        center_j_x = (block_j.bbox.x0 + block_j.bbox.x1) / 2.0
        center_j_y = (block_j.bbox.y0 + block_j.bbox.y1) / 2.0
        return float(
            ((center_i_x - center_j_x) ** 2 + (center_i_y - center_j_y) ** 2) ** 0.5
        )

    def _compute_confidence(self, distance: float, threshold: float) -> float:
        """Compute confidence score based on distance.

        Confidence decreases linearly from 1.0 at distance 0
        to 0.0 at the threshold distance.

        Args:
            distance: Distance between blocks.
            threshold: Maximum distance threshold.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if distance <= 0:
            return 1.0
        if distance >= threshold:
            return 0.0
        return 1.0 - (distance / threshold)


class ReadingOrderComputer:
    """Computes reading order from spatial graph using topological sort."""

    def compute_order(
        self, graph: SpatialGraph, prefer_columns: bool = True
    ) -> list[int]:
        """Compute reading order using topological sort.

        Args:
            graph: Spatial graph.
            prefer_columns: If True, sort columns first before vertical ordering.

        Returns:
            List of block IDs in reading order.
        """
        blocks = list(graph.blocks.items())

        if prefer_columns:
            # Detect columns first
            columns = self._detect_columns(blocks)
            if len(columns) > 1:
                return self._sort_multi_column(blocks, columns, graph)

        # Single column or no column preference - simple top-to-bottom, left-to-right
        return self._sort_simple(blocks)

    def _sort_simple(self, blocks: list[tuple[int, "Block"]]) -> list[int]:
        """Simple sort: top-to-bottom, then left-to-right.

        Args:
            blocks: List of (block_id, block) tuples.

        Returns:
            Sorted list of block IDs.
        """
        # Sort by y0 (top), then by x0 (left)
        sorted_blocks = sorted(
            blocks, key=lambda item: (item[1].bbox.y0, item[1].bbox.x0)
        )
        return [block_id for block_id, _ in sorted_blocks]

    def _detect_columns(
        self, blocks: list[tuple[int, "Block"]]
    ) -> list[tuple[float, float]]:
        """Detect column boundaries.

        Args:
            blocks: List of (block_id, block) tuples.

        Returns:
            List of (x_min, x_max) tuples for each column.
        """
        if not blocks:
            return []

        # Collect all left and right edges
        all_x0 = [block.bbox.x0 for _, block in blocks]
        all_x1 = [block.bbox.x1 for _, block in blocks]

        # Build a coverage map to find gaps between columns
        # For each position, track how many blocks overlap
        events = []
        for _, block in blocks:
            events.append((block.bbox.x0, 1))  # Start of block
            events.append((block.bbox.x1, -1))  # End of block

        events.sort()

        # Find gaps where coverage is 0
        gaps = []
        coverage = 0
        gap_start = None

        for x, delta in events:
            if coverage == 0 and delta > 0:
                # End of gap
                if gap_start is not None and x - gap_start > 50:
                    gaps.append((gap_start, x))
                gap_start = None
            coverage += delta
            if coverage == 0 and delta < 0:
                # Start of gap
                gap_start = x

        # If no significant gaps, treat as single column
        if not gaps:
            return [(min(all_x0), max(all_x1))]

        # Build columns from gaps
        columns = []
        col_start = min(all_x0)

        for gap_start, gap_end in gaps:
            columns.append((col_start, gap_start))
            col_start = gap_end

        # Add final column
        columns.append((col_start, max(all_x1)))

        return columns

    def _sort_multi_column(
        self,
        blocks: list[tuple[int, "Block"]],
        columns: list[tuple[float, float]],
        graph: SpatialGraph,
    ) -> list[int]:
        """Sort blocks in multi-column layout.

        Args:
            blocks: List of (block_id, block) tuples.
            columns: List of column boundaries.
            graph: Spatial graph (for future use).

        Returns:
            Sorted list of block IDs.
        """
        # Assign blocks to columns
        column_blocks: dict[int, list[tuple[int, Block]]] = {
            i: [] for i in range(len(columns))
        }

        for block_id, block in blocks:
            block_center_x = (block.bbox.x0 + block.bbox.x1) / 2
            assigned = False

            for col_idx, (col_x0, col_x1) in enumerate(columns):
                if col_x0 <= block_center_x <= col_x1:
                    column_blocks[col_idx].append((block_id, block))
                    assigned = True
                    break

            if not assigned:
                # Assign to nearest column
                distances = [
                    min(abs(block_center_x - col_x0), abs(block_center_x - col_x1))
                    for col_x0, col_x1 in columns
                ]
                nearest_col = distances.index(min(distances))
                column_blocks[nearest_col].append((block_id, block))

        # Sort each column top-to-bottom
        sorted_ids = []
        for col_idx in range(len(columns)):
            col_blocks = column_blocks[col_idx]
            col_sorted = sorted(col_blocks, key=lambda item: item[1].bbox.y0)
            sorted_ids.extend([block_id for block_id, _ in col_sorted])

        return sorted_ids
