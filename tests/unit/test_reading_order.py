"""Tests for reading order computation."""

import pytest

from unpdf.models.layout import Block, BlockType, BoundingBox
from unpdf.processors.reading_order import (
    ReadingOrderComputer,
    RelationType,
    SpatialEdge,
    SpatialGraph,
    SpatialGraphBuilder,
)


@pytest.fixture
def sample_blocks():
    """Create sample layout blocks for testing."""
    return [
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=10, y=10, width=90, height=20),
        ),
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=10, y=40, width=90, height=20),
        ),
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=10, y=70, width=90, height=20),
        ),
    ]


@pytest.fixture
def two_column_blocks():
    """Create blocks in two-column layout."""
    return [
        # Left column
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=10, y=10, width=90, height=20),
        ),
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=10, y=40, width=90, height=20),
        ),
        # Right column
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=200, y=10, width=90, height=20),
        ),
        Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=200, y=40, width=90, height=20),
        ),
    ]


class TestSpatialGraph:
    """Tests for SpatialGraph class."""

    def test_add_block(self):
        """Test adding a block to the graph."""
        graph = SpatialGraph()
        block = Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=0, y=0, width=10, height=10),
        )
        graph.add_block(0, block)
        assert 0 in graph.blocks
        assert graph.blocks[0] == block

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = SpatialGraph()
        edge = SpatialEdge(
            from_block_id=0,
            to_block_id=1,
            relation=RelationType.BELOW,
            weight=10.0,
        )
        graph.add_edge(edge)
        assert edge in graph.edges
        assert edge in graph.adjacency[0]

    def test_get_outgoing_edges(self):
        """Test retrieving outgoing edges."""
        graph = SpatialGraph()
        edge1 = SpatialEdge(0, 1, RelationType.BELOW, 10.0)
        edge2 = SpatialEdge(0, 2, RelationType.RIGHT, 20.0)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        edges = graph.get_outgoing_edges(0)
        assert len(edges) == 2
        assert edge1 in edges
        assert edge2 in edges

    def test_get_neighbors(self):
        """Test retrieving neighbor IDs."""
        graph = SpatialGraph()
        graph.add_edge(SpatialEdge(0, 1, RelationType.BELOW, 10.0))
        graph.add_edge(SpatialEdge(0, 2, RelationType.RIGHT, 20.0))

        # All neighbors
        neighbors = graph.get_neighbors(0)
        assert len(neighbors) == 2
        assert 1 in neighbors
        assert 2 in neighbors

        # Filtered by relation
        below_neighbors = graph.get_neighbors(0, RelationType.BELOW)
        assert len(below_neighbors) == 1
        assert 1 in below_neighbors


class TestSpatialGraphBuilder:
    """Tests for SpatialGraphBuilder class."""

    def test_build_simple_graph(self, sample_blocks):
        """Test building a graph from simple blocks."""
        builder = SpatialGraphBuilder()
        graph = builder.build(sample_blocks)

        assert len(graph.blocks) == 3
        assert 0 in graph.blocks
        assert 1 in graph.blocks
        assert 2 in graph.blocks

    def test_detect_vertical_relationships(self, sample_blocks):
        """Test detecting above/below relationships."""
        builder = SpatialGraphBuilder()
        graph = builder.build(sample_blocks)

        # Block 0 should be above block 1
        below_neighbors = graph.get_neighbors(0, RelationType.BELOW)
        assert 1 in below_neighbors

        # Block 1 should be above block 2
        below_neighbors = graph.get_neighbors(1, RelationType.BELOW)
        assert 2 in below_neighbors

    def test_detect_horizontal_relationships(self, two_column_blocks):
        """Test detecting left/right relationships."""
        builder = SpatialGraphBuilder()
        graph = builder.build(two_column_blocks)

        # Block 0 (left) should have block 2 (right) as right neighbor
        right_neighbors = graph.get_neighbors(0, RelationType.RIGHT)
        assert 2 in right_neighbors

    def test_contains_relationship(self):
        """Test detecting containment relationships."""
        blocks = [
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=0, y=0, width=100, height=100),
            ),
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=10, y=10, width=40, height=40),
            ),
        ]

        builder = SpatialGraphBuilder()
        graph = builder.build(blocks)

        # Block 0 contains block 1
        contains_neighbors = graph.get_neighbors(0, RelationType.CONTAINS)
        assert 1 in contains_neighbors

        # Block 1 is contained by block 0
        contained_neighbors = graph.get_neighbors(1, RelationType.CONTAINED_BY)
        assert 0 in contained_neighbors

    def test_proximity_relationship(self):
        """Test detecting nearby blocks."""
        blocks = [
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=0, y=0, width=10, height=10),
            ),
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=15, y=15, width=10, height=10),
            ),
        ]

        builder = SpatialGraphBuilder(proximity_threshold=30.0)
        graph = builder.build(blocks)

        # Blocks should be considered near
        near_neighbors = graph.get_neighbors(0, RelationType.NEAR)
        assert 1 in near_neighbors

    def test_confidence_computation(self):
        """Test confidence score computation."""
        builder = SpatialGraphBuilder()

        # At distance 0, confidence should be 1.0
        assert builder._compute_confidence(0.0, 100.0) == 1.0

        # At half threshold, confidence should be 0.5
        assert builder._compute_confidence(50.0, 100.0) == 0.5

        # At threshold, confidence should be 0.0
        assert builder._compute_confidence(100.0, 100.0) == 0.0

        # Beyond threshold, confidence should be 0.0
        assert builder._compute_confidence(150.0, 100.0) == 0.0

    def test_vertical_distance(self, sample_blocks):
        """Test vertical distance computation."""
        builder = SpatialGraphBuilder()

        # Distance between block 0 (y1=30) and block 1 (y0=40) is 10
        distance = builder._vertical_distance(sample_blocks[0], sample_blocks[1])
        assert distance == 10.0

    def test_horizontal_distance(self, two_column_blocks):
        """Test horizontal distance computation."""
        builder = SpatialGraphBuilder()

        # Distance between left column (x1=100) and right column (x0=200) is 100
        distance = builder._horizontal_distance(
            two_column_blocks[0], two_column_blocks[2]
        )
        assert distance == 100.0

    def test_euclidean_distance(self):
        """Test Euclidean distance computation."""
        blocks = [
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=0, y=0, width=10, height=10),
            ),
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=30, y=40, width=10, height=10),
            ),
        ]

        builder = SpatialGraphBuilder()
        distance = builder._euclidean_distance(blocks[0], blocks[1])

        # Center of block 0: (5, 5), center of block 1: (35, 45)
        # Distance = sqrt((35-5)^2 + (45-5)^2) = sqrt(900 + 1600) = 50
        assert abs(distance - 50.0) < 0.01


class TestReadingOrderComputer:
    """Tests for ReadingOrderComputer class."""

    def test_simple_sort_single_column(self, sample_blocks):
        """Test simple top-to-bottom sort."""
        graph = SpatialGraph()
        for idx, block in enumerate(sample_blocks):
            graph.add_block(idx, block)

        computer = ReadingOrderComputer()
        order = computer.compute_order(graph, prefer_columns=False)

        # Should be sorted top-to-bottom: 0, 1, 2
        assert order == [0, 1, 2]

    def test_multi_column_detection(self, two_column_blocks):
        """Test column detection in two-column layout."""
        computer = ReadingOrderComputer()
        blocks = [(idx, block) for idx, block in enumerate(two_column_blocks)]

        columns = computer._detect_columns(blocks)

        # Should detect 2 columns
        assert len(columns) == 2

    def test_multi_column_sort(self, two_column_blocks):
        """Test sorting in multi-column layout."""
        graph = SpatialGraph()
        for idx, block in enumerate(two_column_blocks):
            graph.add_block(idx, block)

        computer = ReadingOrderComputer()
        order = computer.compute_order(graph, prefer_columns=True)

        # Should read left column first (0, 1), then right column (2, 3)
        assert order == [0, 1, 2, 3]

    def test_single_column_detection_no_gaps(self):
        """Test that single column is detected when no gaps exist."""
        blocks = [
            (
                0,
                Block(
                    block_type=BlockType.TEXT,
                    bbox=BoundingBox(x=10, y=10, width=90, height=20),
                ),
            ),
            (
                1,
                Block(
                    block_type=BlockType.TEXT,
                    bbox=BoundingBox(x=10, y=40, width=90, height=20),
                ),
            ),
        ]

        computer = ReadingOrderComputer()
        columns = computer._detect_columns(blocks)

        # Should detect 1 column
        assert len(columns) == 1

    def test_complex_layout(self):
        """Test sorting with mixed horizontal and vertical layout."""
        blocks = [
            # Top row (left to right)
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=10, y=10, width=40, height=20),
            ),
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=60, y=10, width=40, height=20),
            ),
            # Bottom row (left to right)
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=10, y=40, width=40, height=20),
            ),
            Block(
                block_type=BlockType.TEXT,
                bbox=BoundingBox(x=60, y=40, width=40, height=20),
            ),
        ]

        graph = SpatialGraph()
        for idx, block in enumerate(blocks):
            graph.add_block(idx, block)

        computer = ReadingOrderComputer()
        order = computer.compute_order(graph, prefer_columns=False)

        # Should be sorted top-to-bottom, left-to-right: 0, 1, 2, 3
        assert order == [0, 1, 2, 3]

    def test_empty_blocks(self):
        """Test handling of empty block list."""
        graph = SpatialGraph()
        computer = ReadingOrderComputer()
        order = computer.compute_order(graph)

        assert order == []

    def test_single_block(self):
        """Test handling of single block."""
        block = Block(
            block_type=BlockType.TEXT,
            bbox=BoundingBox(x=0, y=0, width=10, height=10),
        )

        graph = SpatialGraph()
        graph.add_block(0, block)

        computer = ReadingOrderComputer()
        order = computer.compute_order(graph)

        assert order == [0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
