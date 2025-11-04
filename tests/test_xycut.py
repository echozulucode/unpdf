"""Tests for XY-Cut layout segmentation."""

from unpdf.extractors.xycut import (
    compute_projection_profiles,
    compute_thresholds,
    find_valleys,
    find_widest_valley,
    recursive_xycut,
    segment_page_xycut,
)
from unpdf.models.layout import Block, BlockType, BoundingBox, Style


def create_block(x: float, y: float, width: float, height: float, text: str = "test"):
    """Helper to create a text block."""
    return Block(
        bbox=BoundingBox(x, y, width, height),
        content=text,
        style=Style(font="Arial", size=12.0),
        block_type=BlockType.TEXT,
    )


class TestProjectionProfiles:
    """Tests for projection profile computation."""

    def test_single_block(self):
        """Test projection profile for a single block."""
        blocks = [create_block(10, 10, 40, 20, "test")]
        bbox = BoundingBox(0, 0, 100, 100)
        profile = compute_projection_profiles(blocks, bbox, resolution=1.0)

        assert len(profile.horizontal) == 101
        assert len(profile.vertical) == 101
        # Block spans y=10-30, should have non-zero values there
        assert any(v > 0 for v in profile.horizontal[10:31])
        # Block spans x=10-50, should have non-zero values there
        assert any(v > 0 for v in profile.vertical[10:51])

    def test_two_columns(self):
        """Test projection profile for two-column layout."""
        blocks = [
            create_block(10, 10, 30, 20, "left"),
            create_block(60, 10, 30, 20, "right"),
        ]
        bbox = BoundingBox(0, 0, 100, 100)
        profile = compute_projection_profiles(blocks, bbox, resolution=1.0)

        # Should have gap in vertical profile between x=40 and x=60
        assert any(v == 0 for v in profile.vertical[41:60])

    def test_two_rows(self):
        """Test projection profile for two-row layout."""
        blocks = [
            create_block(10, 10, 80, 20, "top"),
            create_block(10, 50, 80, 20, "bottom"),
        ]
        bbox = BoundingBox(0, 0, 100, 100)
        profile = compute_projection_profiles(blocks, bbox, resolution=1.0)

        # Should have gap in horizontal profile between y=30 and y=50
        assert any(v == 0 for v in profile.horizontal[31:50])


class TestValleyDetection:
    """Tests for valley detection."""

    def test_find_single_valley(self):
        """Test finding a single valley."""
        profile = [10, 10, 0, 0, 0, 10, 10]
        valleys = find_valleys(profile, threshold=0, min_width=1)
        assert valleys == [(2, 4)]

    def test_find_multiple_valleys(self):
        """Test finding multiple valleys."""
        profile = [10, 0, 0, 10, 0, 0, 10]
        valleys = find_valleys(profile, threshold=0, min_width=1)
        assert valleys == [(1, 2), (4, 5)]

    def test_min_width_filter(self):
        """Test that valleys below minimum width are filtered."""
        profile = [10, 0, 10, 0, 0, 0, 10]
        valleys = find_valleys(profile, threshold=0, min_width=2)
        assert valleys == [(3, 5)]

    def test_no_valleys(self):
        """Test when no valleys exist."""
        profile = [10, 10, 10, 10, 10]
        valleys = find_valleys(profile, threshold=0, min_width=1)
        assert valleys == []

    def test_threshold(self):
        """Test threshold filtering."""
        profile = [10, 5, 5, 10, 1, 1, 10]
        valleys = find_valleys(profile, threshold=3, min_width=1)
        assert valleys == [(4, 5)]


class TestWidestValley:
    """Tests for widest valley selection."""

    def test_single_valley(self):
        """Test with single valley."""
        valleys = [(2, 5)]
        assert find_widest_valley(valleys) == 3

    def test_multiple_valleys(self):
        """Test selecting widest from multiple valleys."""
        valleys = [(2, 3), (5, 10), (12, 13)]
        assert find_widest_valley(valleys) == 7  # Midpoint of (5, 10)

    def test_no_valleys(self):
        """Test with no valleys."""
        assert find_widest_valley([]) is None


class TestThresholdComputation:
    """Tests for adaptive threshold computation."""

    def test_single_block(self):
        """Test threshold computation with single block."""
        blocks = [create_block(0, 0, 100, 20, "a" * 10)]
        h_thresh, v_thresh = compute_thresholds(blocks)
        assert h_thresh > 0
        assert v_thresh > 0

    def test_varying_sizes(self):
        """Test threshold computation with varying block sizes."""
        blocks = [
            create_block(0, 0, 100, 10, "small"),
            create_block(0, 20, 100, 30, "large"),
        ]
        h_thresh, v_thresh = compute_thresholds(blocks)
        # Should be based on average (avg height is 20, thresh is 0.5x = 10)
        assert 5 <= h_thresh <= 15

    def test_empty_blocks(self):
        """Test threshold computation with no blocks."""
        h_thresh, v_thresh = compute_thresholds([])
        assert h_thresh == 0.0
        assert v_thresh == 0.0


class TestRecursiveXYCut:
    """Tests for recursive XY-Cut algorithm."""

    def test_single_block(self):
        """Test with single block (no split needed)."""
        blocks = [create_block(10, 10, 80, 20)]
        bbox = BoundingBox(0, 0, 100, 100)
        regions = recursive_xycut(blocks, bbox)
        assert len(regions) == 1
        assert regions[0] == blocks

    def test_two_columns(self):
        """Test splitting two columns."""
        blocks = [
            create_block(10, 10, 30, 20, "left"),
            create_block(60, 10, 30, 20, "right"),
        ]
        bbox = BoundingBox(0, 0, 100, 100)
        regions = recursive_xycut(blocks, bbox)
        # Should split into two regions
        assert len(regions) == 2

    def test_two_rows(self):
        """Test splitting two rows."""
        blocks = [
            create_block(10, 10, 80, 10, "top"),
            create_block(10, 50, 80, 10, "bottom"),
        ]
        bbox = BoundingBox(0, 0, 100, 100)
        regions = recursive_xycut(blocks, bbox)
        # Should split into two regions
        assert len(regions) == 2

    def test_grid_layout(self):
        """Test splitting grid layout (2x2)."""
        blocks = [
            create_block(10, 10, 30, 20, "top-left"),
            create_block(60, 10, 30, 20, "top-right"),
            create_block(10, 50, 30, 20, "bottom-left"),
            create_block(60, 50, 30, 20, "bottom-right"),
        ]
        bbox = BoundingBox(0, 0, 100, 100)
        regions = recursive_xycut(blocks, bbox)
        # Should split into four regions
        assert len(regions) == 4

    def test_max_depth(self):
        """Test that max depth is respected."""
        blocks = [create_block(i * 10, i * 10, 5, 5) for i in range(20)]
        bbox = BoundingBox(0, 0, 200, 200)
        regions = recursive_xycut(blocks, bbox, max_depth=2)
        # Should stop at depth 2
        assert len(regions) <= 4

    def test_empty_blocks(self):
        """Test with empty block list."""
        bbox = BoundingBox(0, 0, 100, 100)
        regions = recursive_xycut([], bbox)
        assert regions == []


class TestSegmentPageXYCut:
    """Tests for page segmentation wrapper."""

    def test_simple_layout(self):
        """Test segmenting a simple layout."""
        blocks = [
            create_block(10, 10, 30, 20, "left"),
            create_block(60, 10, 30, 20, "right"),
        ]
        regions = segment_page_xycut(blocks)
        assert len(regions) >= 1

    def test_empty_page(self):
        """Test segmenting empty page."""
        regions = segment_page_xycut([])
        assert regions == []

    def test_preserves_all_blocks(self):
        """Test that all blocks are preserved in output."""
        blocks = [
            create_block(10, 10, 30, 20, "1"),
            create_block(60, 10, 30, 20, "2"),
            create_block(10, 50, 30, 20, "3"),
        ]
        regions = segment_page_xycut(blocks)

        # Flatten regions and check all blocks present
        all_blocks = [b for region in regions for b in region]
        assert len(all_blocks) == len(blocks)
        assert {b.content for b in all_blocks} == {b.content for b in blocks}


class TestXYCutPerformance:
    """Performance tests for XY-Cut algorithm."""

    def test_large_document(self):
        """Test performance on large document."""
        # Create 100 blocks in a grid
        blocks = []
        for i in range(10):
            for j in range(10):
                blocks.append(create_block(j * 100, i * 50, 80, 40, f"block-{i}-{j}"))

        import time

        start = time.time()
        regions = segment_page_xycut(blocks)
        elapsed = time.time() - start

        # Should complete in under 100ms (target from plan)
        assert elapsed < 0.1
        assert len(regions) > 0
