"""Tests for hierarchical layout tree construction."""

import pytest

from unpdf.models.layout import BoundingBox
from unpdf.processors.layout_tree import (
    LayoutNode,
    LayoutTreeBuilder,
    NodeType,
    SpatialIndex,
)


class TestLayoutNode:
    """Tests for LayoutNode."""

    def test_create_node(self):
        """Test basic node creation."""
        bbox = BoundingBox(0, 0, 100, 50)
        node = LayoutNode(node_type=NodeType.BLOCK, bbox=bbox, content="test")

        assert node.node_type == NodeType.BLOCK
        assert node.bbox == bbox
        assert node.content == "test"
        assert len(node.children) == 0
        assert node.parent is None

    def test_add_child(self):
        """Test adding child nodes."""
        parent = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        child = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(10, 10, 90, 30))

        parent.add_child(child)

        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent == parent

    def test_is_leaf(self):
        """Test leaf node detection."""
        parent = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        child = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(10, 10, 90, 30))

        assert child.is_leaf()
        assert parent.is_leaf()  # No children yet

        parent.add_child(child)

        assert child.is_leaf()
        assert not parent.is_leaf()

    def test_is_root(self):
        """Test root node detection."""
        parent = LayoutNode(node_type=NodeType.PAGE, bbox=BoundingBox(0, 0, 612, 792))
        child = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(10, 10, 90, 30))

        assert parent.is_root()
        assert child.is_root()  # No parent yet

        parent.add_child(child)

        assert parent.is_root()
        assert not child.is_root()

    def test_get_depth(self):
        """Test depth calculation."""
        page = LayoutNode(node_type=NodeType.PAGE, bbox=BoundingBox(0, 0, 612, 792))
        block = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        line = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(0, 0, 100, 20))
        word = LayoutNode(node_type=NodeType.WORD, bbox=BoundingBox(0, 0, 50, 20))

        page.add_child(block)
        block.add_child(line)
        line.add_child(word)

        assert page.get_depth() == 0
        assert block.get_depth() == 1
        assert line.get_depth() == 2
        assert word.get_depth() == 3

    def test_contains(self):
        """Test containment detection."""
        parent = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        child_inside = LayoutNode(
            node_type=NodeType.LINE, bbox=BoundingBox(10, 10, 90, 30)
        )
        child_outside = LayoutNode(
            node_type=NodeType.LINE, bbox=BoundingBox(50, 50, 150, 70)
        )

        assert parent.contains(child_inside)
        assert not parent.contains(child_outside)

    def test_contains_with_tolerance(self):
        """Test containment with tolerance."""
        parent = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        child_almost_inside = LayoutNode(
            node_type=NodeType.LINE, bbox=BoundingBox(-2, 10, 90, 30)
        )

        assert not parent.contains(child_almost_inside, tolerance=0.0)
        assert parent.contains(child_almost_inside, tolerance=5.0)

    def test_aligned_horizontally(self):
        """Test horizontal alignment detection."""
        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 100, 50, 120))
        node2 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(60, 102, 110, 122)
        )
        node3 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(120, 200, 170, 220)
        )

        assert node1.aligned_horizontally(node2, tolerance=5.0)
        assert not node1.aligned_horizontally(node3, tolerance=5.0)

    def test_aligned_vertically(self):
        """Test vertical alignment detection."""
        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(100, 0, 120, 50))
        node2 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(102, 60, 122, 110)
        )
        node3 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(200, 120, 220, 170)
        )

        assert node1.aligned_vertically(node2, tolerance=5.0)
        assert not node1.aligned_vertically(node3, tolerance=5.0)

    def test_distance_to(self):
        """Test distance calculation."""
        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 10, 10))
        node2 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(30, 40, 10, 10))

        # Centers: (5, 5) and (35, 45)
        # Distance: sqrt((35-5)^2 + (45-5)^2) = sqrt(900 + 1600) = 50
        distance = node1.distance_to(node2)
        assert abs(distance - 50.0) < 0.01

    def test_get_siblings(self):
        """Test sibling retrieval."""
        parent = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        child1 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(0, 0, 100, 20))
        child2 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(0, 25, 100, 45))
        child3 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(0, 50, 100, 70))

        parent.add_child(child1)
        parent.add_child(child2)
        parent.add_child(child3)

        siblings = child2.get_siblings()
        assert len(siblings) == 2
        assert child1 in siblings
        assert child3 in siblings
        assert child2 not in siblings

    def test_get_ancestors(self):
        """Test ancestor retrieval."""
        page = LayoutNode(node_type=NodeType.PAGE, bbox=BoundingBox(0, 0, 612, 792))
        block = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        line = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(0, 0, 100, 20))

        page.add_child(block)
        block.add_child(line)

        ancestors = line.get_ancestors()
        assert len(ancestors) == 2
        assert ancestors[0] == block
        assert ancestors[1] == page

    def test_get_descendants(self):
        """Test descendant retrieval."""
        page = LayoutNode(node_type=NodeType.PAGE, bbox=BoundingBox(0, 0, 612, 792))
        block = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        line = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(0, 0, 100, 20))
        word = LayoutNode(node_type=NodeType.WORD, bbox=BoundingBox(0, 0, 50, 20))

        page.add_child(block)
        block.add_child(line)
        line.add_child(word)

        descendants = page.get_descendants()
        assert len(descendants) == 3
        assert block in descendants
        assert line in descendants
        assert word in descendants

    def test_to_dict(self):
        """Test dictionary conversion."""
        parent = LayoutNode(
            node_type=NodeType.BLOCK,
            bbox=BoundingBox(0, 0, 100, 50),
            properties={"type": "paragraph"},
            reading_order=1,
        )
        child = LayoutNode(
            node_type=NodeType.LINE,
            bbox=BoundingBox(0, 0, 100, 20),
            content="Hello",
        )
        parent.add_child(child)

        result = parent.to_dict()

        assert result["type"] == "block"
        assert result["bbox"] == [0, 0, 100, 50]
        assert result["properties"] == {"type": "paragraph"}
        assert result["reading_order"] == 1
        assert len(result["children"]) == 1
        assert result["children"][0]["content"] == "Hello"


class TestSpatialIndex:
    """Tests for SpatialIndex."""

    def test_add_and_query_region(self):
        """Test adding nodes and querying by region."""
        index = SpatialIndex()

        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 50, 50))
        node2 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(60, 60, 50, 50)
        )  # (60,60) to (110,110)
        node3 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(30, 30, 50, 50)
        )  # (30,30) to (80,80)

        index.add(node1)
        index.add(node2)
        index.add(node3)

        # Query region that overlaps node1 and node3
        query_bbox = BoundingBox(25, 25, 30, 30)  # (25,25) to (55,55)
        results = index.query_region(query_bbox)

        assert len(results) == 2
        assert node1 in results
        assert node3 in results

    def test_query_point(self):
        """Test querying by point."""
        index = SpatialIndex()

        # Create nested boxes
        outer = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 100, 100))
        inner = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(20, 20, 80, 80))
        word = LayoutNode(node_type=NodeType.WORD, bbox=BoundingBox(30, 30, 50, 50))

        outer.add_child(inner)
        inner.add_child(word)

        index.add(outer)
        index.add(inner)
        index.add(word)

        # Query point inside all three
        results = index.query_point(40, 40)

        assert len(results) == 3
        # Should be sorted by depth (deepest first)
        assert results[0] == word
        assert results[1] == inner
        assert results[2] == outer

    def test_nearest_neighbor(self):
        """Test nearest neighbor search."""
        index = SpatialIndex()

        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 10, 10))
        node2 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(20, 0, 30, 10)
        )  # 15 units away
        node3 = LayoutNode(
            node_type=NodeType.BLOCK, bbox=BoundingBox(100, 0, 110, 10)
        )  # 95 units away

        index.add(node1)
        index.add(node2)
        index.add(node3)

        nearest = index.nearest_neighbor(node1)
        assert nearest == node2

    def test_nearest_neighbor_with_max_distance(self):
        """Test nearest neighbor with distance limit."""
        index = SpatialIndex()

        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 10, 10))
        node2 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(100, 0, 110, 10))

        index.add(node1)
        index.add(node2)

        # With max_distance that excludes node2
        nearest = index.nearest_neighbor(node1, max_distance=50)
        assert nearest is None

        # With max_distance that includes node2
        nearest = index.nearest_neighbor(node1, max_distance=200)
        assert nearest == node2

    def test_nearest_neighbor_same_type(self):
        """Test nearest neighbor with type filtering."""
        index = SpatialIndex()

        block = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 10, 10))
        line1 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(20, 0, 30, 10))
        line2 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(50, 0, 60, 10))

        index.add(block)
        index.add(line1)
        index.add(line2)

        # Nearest to block (ignoring type)
        nearest = index.nearest_neighbor(block, same_type=False)
        assert nearest == line1

        # Nearest block to block (same type only)
        nearest = index.nearest_neighbor(block, same_type=True)
        assert nearest is None  # No other blocks

    def test_k_nearest_neighbors(self):
        """Test k-nearest neighbors search."""
        index = SpatialIndex()

        center = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(50, 50, 60, 60))
        node1 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(40, 50, 45, 60))
        node2 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(65, 50, 70, 60))
        node3 = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(30, 50, 35, 60))

        index.add(center)
        index.add(node1)
        index.add(node2)
        index.add(node3)

        neighbors = index.k_nearest_neighbors(center, k=2)

        assert len(neighbors) == 2
        # Should be sorted by distance (closest first)
        assert neighbors[0] in [node1, node2]  # Both about same distance
        assert neighbors[1] in [node1, node2]

    def test_k_nearest_neighbors_with_filters(self):
        """Test k-nearest neighbors with distance and type filters."""
        index = SpatialIndex()

        block = LayoutNode(node_type=NodeType.BLOCK, bbox=BoundingBox(0, 0, 10, 10))
        line1 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(20, 0, 30, 10))
        line2 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(50, 0, 60, 10))
        line3 = LayoutNode(node_type=NodeType.LINE, bbox=BoundingBox(200, 0, 210, 10))

        index.add(block)
        index.add(line1)
        index.add(line2)
        index.add(line3)

        # k=3 nearest lines to block with max_distance=100
        neighbors = index.k_nearest_neighbors(
            block, k=3, max_distance=100, same_type=False
        )

        assert len(neighbors) == 2  # line3 excluded by distance
        assert line1 in neighbors
        assert line2 in neighbors


class TestLayoutTreeBuilder:
    """Tests for LayoutTreeBuilder."""

    def test_create_builder(self):
        """Test builder creation."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        assert builder.root.node_type == NodeType.PAGE
        assert builder.root.bbox == page_bbox

    def test_add_block(self):
        """Test adding blocks."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        block = builder.add_block(
            BoundingBox(0, 0, 200, 50),
            properties={"type": "paragraph"},
            reading_order=0,
        )

        assert block.node_type == NodeType.BLOCK
        assert block.parent == builder.root
        assert len(builder.root.children) == 1
        assert block.reading_order == 0

    def test_add_line(self):
        """Test adding lines to blocks."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        block = builder.add_block(BoundingBox(0, 0, 200, 50))
        line = builder.add_line(block, BoundingBox(0, 0, 200, 15))

        assert line.node_type == NodeType.LINE
        assert line.parent == block
        assert len(block.children) == 1

    def test_add_line_wrong_parent(self):
        """Test that adding line to non-block parent fails."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        with pytest.raises(ValueError, match="Line parent must be a BLOCK node"):
            builder.add_line(builder.root, BoundingBox(0, 0, 200, 15))

    def test_add_word(self):
        """Test adding words to lines."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        block = builder.add_block(BoundingBox(0, 0, 200, 50))
        line = builder.add_line(block, BoundingBox(0, 0, 200, 15))
        word = builder.add_word(line, BoundingBox(0, 0, 50, 15), "Hello")

        assert word.node_type == NodeType.WORD
        assert word.content == "Hello"
        assert word.parent == line
        assert len(line.children) == 1

    def test_add_word_wrong_parent(self):
        """Test that adding word to non-line parent fails."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        block = builder.add_block(BoundingBox(0, 0, 200, 50))

        with pytest.raises(ValueError, match="Word parent must be a LINE node"):
            builder.add_word(block, BoundingBox(0, 0, 50, 15), "Hello")

    def test_validate_containment(self):
        """Test containment validation."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        block = builder.add_block(BoundingBox(0, 0, 200, 50))
        line_inside = LayoutNode(
            node_type=NodeType.LINE, bbox=BoundingBox(10, 10, 190, 25)
        )
        line_outside = LayoutNode(
            node_type=NodeType.LINE, bbox=BoundingBox(10, 10, 250, 25)
        )

        assert builder.validate_containment(block, line_inside)
        assert not builder.validate_containment(block, line_outside)

    def test_spatial_index_integration(self):
        """Test that spatial index is populated correctly."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        block = builder.add_block(BoundingBox(0, 0, 200, 50))
        line = builder.add_line(block, BoundingBox(0, 0, 200, 15))
        word = builder.add_word(line, BoundingBox(0, 0, 50, 15), "Hello")

        index = builder.get_spatial_index()

        # Should have page, block, line, word
        assert len(index.nodes) == 4

        # Query point should find word
        results = index.query_point(25, 7)
        assert word in results

    def test_complex_tree(self):
        """Test building a complex tree structure."""
        page_bbox = BoundingBox(0, 0, 612, 792)
        builder = LayoutTreeBuilder(page_bbox)

        # Add multiple blocks
        block1 = builder.add_block(BoundingBox(0, 0, 300, 100), reading_order=0)
        builder.add_block(BoundingBox(0, 120, 300, 220), reading_order=1)

        # Add lines to first block
        line1_1 = builder.add_line(block1, BoundingBox(0, 0, 300, 20))
        builder.add_line(block1, BoundingBox(0, 25, 300, 45))

        # Add words to first line
        builder.add_word(line1_1, BoundingBox(0, 0, 50, 20), "Hello")
        builder.add_word(line1_1, BoundingBox(55, 0, 105, 20), "World")

        tree = builder.get_tree()

        assert len(tree.children) == 2  # Two blocks
        assert len(tree.children[0].children) == 2  # Two lines in block1
        assert len(tree.children[0].children[0].children) == 2  # Two words in line1_1
