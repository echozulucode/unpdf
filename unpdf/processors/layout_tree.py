"""Hierarchical layout tree construction from geometric blocks.

This module builds a physical layout tree representing the document structure:
- Page → Blocks → Lines → Words

The tree provides spatial indexing for efficient queries and supports
containment detection, alignment validation, and spatial relationships.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from unpdf.models.layout import BoundingBox


class NodeType(Enum):
    """Types of nodes in the layout tree."""

    PAGE = "page"
    BLOCK = "block"
    LINE = "line"
    WORD = "word"


@dataclass
class LayoutNode:
    """A node in the hierarchical layout tree.

    Attributes:
        node_type: Type of this node (page, block, line, word)
        bbox: Bounding box for this node
        content: Text content (for leaf nodes)
        properties: Additional properties (font, style, etc.)
        children: Child nodes in the tree
        parent: Parent node (None for root)
        reading_order: Position in reading order (0-indexed)
    """

    node_type: NodeType
    bbox: BoundingBox
    content: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    children: list["LayoutNode"] = field(default_factory=list)
    parent: Optional["LayoutNode"] = None
    reading_order: int = -1

    def add_child(self, child: "LayoutNode") -> None:
        """Add a child node and set its parent."""
        child.parent = self
        self.children.append(child)

    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0

    def is_root(self) -> bool:
        """Check if this is the root node."""
        return self.parent is None

    def get_depth(self) -> int:
        """Get depth of this node in the tree (root = 0)."""
        depth = 0
        node = self
        while node.parent is not None:
            depth += 1
            node = node.parent
        return depth

    def contains(self, other: "LayoutNode", tolerance: float = 0.0) -> bool:
        """Check if this node fully contains another node.

        Args:
            other: Node to check for containment
            tolerance: Pixel tolerance for containment (default: 0.0)

        Returns:
            True if other node is within this node's bounds
        """
        if tolerance == 0.0:
            return self.bbox.contains(other.bbox)
        # With tolerance, expand this bbox and check containment
        return (
            self.bbox.x0 - tolerance <= other.bbox.x0
            and self.bbox.y0 - tolerance <= other.bbox.y0
            and self.bbox.x1 + tolerance >= other.bbox.x1
            and self.bbox.y1 + tolerance >= other.bbox.y1
        )

    def aligned_horizontally(self, other: "LayoutNode", tolerance: float = 5.0) -> bool:
        """Check if this node is horizontally aligned with another.

        Args:
            other: Node to check alignment with
            tolerance: Pixel tolerance for alignment (default: 5.0)

        Returns:
            True if nodes have similar vertical position
        """
        return abs(self.bbox.y0 - other.bbox.y0) <= tolerance

    def aligned_vertically(self, other: "LayoutNode", tolerance: float = 5.0) -> bool:
        """Check if this node is vertically aligned with another.

        Args:
            other: Node to check alignment with
            tolerance: Pixel tolerance for alignment (default: 5.0)

        Returns:
            True if nodes have similar horizontal position
        """
        return abs(self.bbox.x0 - other.bbox.x0) <= tolerance

    def distance_to(self, other: "LayoutNode") -> float:
        """Calculate distance between this node and another.

        Uses center-to-center Euclidean distance.

        Args:
            other: Node to calculate distance to

        Returns:
            Distance in pixels
        """
        cx1, cy1 = self.bbox.center_x, self.bbox.center_y
        cx2, cy2 = other.bbox.center_x, other.bbox.center_y
        dx = cx2 - cx1
        dy = cy2 - cy1
        return float((dx * dx + dy * dy) ** 0.5)

    def get_siblings(self) -> list["LayoutNode"]:
        """Get all sibling nodes (nodes with same parent)."""
        if self.parent is None:
            return []
        return [child for child in self.parent.children if child != self]

    def get_ancestors(self) -> list["LayoutNode"]:
        """Get all ancestor nodes from parent to root."""
        ancestors = []
        node = self.parent
        while node is not None:
            ancestors.append(node)
            node = node.parent
        return ancestors

    def get_descendants(self) -> list["LayoutNode"]:
        """Get all descendant nodes (depth-first)."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "type": self.node_type.value,
            "bbox": [self.bbox.x0, self.bbox.y0, self.bbox.x1, self.bbox.y1],
            "content": self.content,
            "properties": self.properties,
            "reading_order": self.reading_order,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class SpatialIndex:
    """Spatial index for efficient layout tree queries.

    Provides fast lookups for nodes in specific regions and nearest
    neighbor searches.
    """

    nodes: list[LayoutNode] = field(default_factory=list)

    def add(self, node: LayoutNode) -> None:
        """Add a node to the spatial index."""
        self.nodes.append(node)

    def query_region(self, bbox: BoundingBox) -> list[LayoutNode]:
        """Find all nodes that overlap with the given bounding box.

        Args:
            bbox: Bounding box to query

        Returns:
            List of nodes that overlap with the query region
        """
        return [node for node in self.nodes if node.bbox.overlaps(bbox)]

    def query_point(self, x: float, y: float) -> list[LayoutNode]:
        """Find all nodes that contain the given point.

        Args:
            x: X-coordinate of the point
            y: Y-coordinate of the point

        Returns:
            List of nodes containing the point, sorted by depth (deepest first)
        """
        containing = [
            node
            for node in self.nodes
            if node.bbox.x0 <= x <= node.bbox.x1 and node.bbox.y0 <= y <= node.bbox.y1
        ]
        # Sort by depth (deepest first) then by area (smallest first)
        containing.sort(key=lambda n: (-n.get_depth(), n.bbox.width * n.bbox.height))
        return containing

    def nearest_neighbor(
        self,
        node: LayoutNode,
        max_distance: float | None = None,
        same_type: bool = False,
    ) -> LayoutNode | None:
        """Find the nearest neighbor to a given node.

        Args:
            node: Reference node
            max_distance: Maximum distance to search (None = unlimited)
            same_type: Only consider nodes of the same type

        Returns:
            Nearest node, or None if no valid neighbor found
        """
        candidates = self.nodes
        if same_type:
            candidates = [n for n in candidates if n.node_type == node.node_type]

        # Exclude the node itself
        candidates = [n for n in candidates if n != node]

        if not candidates:
            return None

        # Find nearest by distance
        nearest = min(candidates, key=lambda n: node.distance_to(n))

        if max_distance is not None and node.distance_to(nearest) > max_distance:
            return None

        return nearest

    def k_nearest_neighbors(
        self,
        node: LayoutNode,
        k: int = 5,
        max_distance: float | None = None,
        same_type: bool = False,
    ) -> list[LayoutNode]:
        """Find the k nearest neighbors to a given node.

        Args:
            node: Reference node
            k: Number of neighbors to return
            max_distance: Maximum distance to search (None = unlimited)
            same_type: Only consider nodes of the same type

        Returns:
            List of up to k nearest nodes, sorted by distance
        """
        candidates = self.nodes
        if same_type:
            candidates = [n for n in candidates if n.node_type == node.node_type]

        # Exclude the node itself
        candidates = [n for n in candidates if n != node]

        if not candidates:
            return []

        # Sort by distance
        candidates_with_dist = [
            (n, node.distance_to(n)) for n in candidates if n != node
        ]
        candidates_with_dist.sort(key=lambda x: x[1])

        # Filter by max_distance
        if max_distance is not None:
            candidates_with_dist = [
                (n, d) for n, d in candidates_with_dist if d <= max_distance
            ]

        # Return top k
        return [n for n, d in candidates_with_dist[:k]]


class LayoutTreeBuilder:
    """Builder for constructing hierarchical layout trees."""

    def __init__(self, page_bbox: BoundingBox):
        """Initialize builder with page dimensions.

        Args:
            page_bbox: Bounding box of the page
        """
        self.page_bbox = page_bbox
        self.root = LayoutNode(node_type=NodeType.PAGE, bbox=page_bbox)
        self.spatial_index = SpatialIndex()
        self.spatial_index.add(self.root)

    def add_block(
        self,
        bbox: BoundingBox,
        properties: dict[str, Any] | None = None,
        reading_order: int = -1,
    ) -> LayoutNode:
        """Add a block node to the tree.

        Args:
            bbox: Bounding box of the block
            properties: Block properties (type, style, etc.)
            reading_order: Position in reading order

        Returns:
            The created block node
        """
        block = LayoutNode(
            node_type=NodeType.BLOCK,
            bbox=bbox,
            properties=properties or {},
            reading_order=reading_order,
        )
        self.root.add_child(block)
        self.spatial_index.add(block)
        return block

    def add_line(
        self,
        parent: LayoutNode,
        bbox: BoundingBox,
        properties: dict[str, Any] | None = None,
    ) -> LayoutNode:
        """Add a line node to a parent block.

        Args:
            parent: Parent block node
            bbox: Bounding box of the line
            properties: Line properties (font, style, etc.)

        Returns:
            The created line node
        """
        if parent.node_type != NodeType.BLOCK:
            raise ValueError("Line parent must be a BLOCK node")

        line = LayoutNode(
            node_type=NodeType.LINE, bbox=bbox, properties=properties or {}
        )
        parent.add_child(line)
        self.spatial_index.add(line)
        return line

    def add_word(
        self,
        parent: LayoutNode,
        bbox: BoundingBox,
        content: str,
        properties: dict[str, Any] | None = None,
    ) -> LayoutNode:
        """Add a word node to a parent line.

        Args:
            parent: Parent line node
            bbox: Bounding box of the word
            content: Text content of the word
            properties: Word properties (font, style, etc.)

        Returns:
            The created word node
        """
        if parent.node_type != NodeType.LINE:
            raise ValueError("Word parent must be a LINE node")

        word = LayoutNode(
            node_type=NodeType.WORD,
            bbox=bbox,
            content=content,
            properties=properties or {},
        )
        parent.add_child(word)
        self.spatial_index.add(word)
        return word

    def validate_containment(
        self, parent: LayoutNode, child: LayoutNode, tolerance: float = 5.0
    ) -> bool:
        """Validate that a child is properly contained within a parent.

        Args:
            parent: Parent node
            child: Child node
            tolerance: Pixel tolerance for containment

        Returns:
            True if child is within parent bounds
        """
        return parent.contains(child, tolerance)

    def get_tree(self) -> LayoutNode:
        """Get the root of the layout tree."""
        return self.root

    def get_spatial_index(self) -> SpatialIndex:
        """Get the spatial index for the tree."""
        return self.spatial_index
