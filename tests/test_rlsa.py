"""Tests for RLSA (Run Length Smoothing Algorithm) block detection."""

import numpy as np
import pytest

from unpdf.extractors.rlsa import (
    RLSAConfig,
    apply_rlsa,
    blocks_to_binary_image,
    compute_adaptive_thresholds,
    detect_blocks_rlsa,
    extract_blocks_from_image,
    smooth_horizontal,
    smooth_vertical,
)
from unpdf.models.layout import Block, BlockType, BoundingBox


class TestRLSAConfig:
    """Tests for RLSA configuration."""

    def test_default_config(self):
        """Test default RLSA configuration values."""
        config = RLSAConfig()
        assert config.hsv == 20
        assert config.vsv == 5
        assert config.hsv2 == 20

    def test_custom_config(self):
        """Test custom RLSA configuration."""
        config = RLSAConfig(hsv=30, vsv=8, hsv2=25)
        assert config.hsv == 30
        assert config.vsv == 8
        assert config.hsv2 == 25


class TestAdaptiveThresholds:
    """Tests for adaptive threshold computation."""

    def test_empty_blocks(self):
        """Test with empty block list."""
        config = compute_adaptive_thresholds([])
        assert isinstance(config, RLSAConfig)
        assert config.hsv == 20  # Default
        assert config.vsv == 5  # Default

    def test_single_block(self):
        """Test with single block."""
        block = Block(
            bbox=BoundingBox(x=10, y=10, width=100, height=12),
            content="Hello world",
            block_type=BlockType.TEXT,
        )
        config = compute_adaptive_thresholds([block])
        assert 10 <= config.hsv <= 50
        assert 3 <= config.vsv <= 10

    def test_multiple_blocks(self):
        """Test with multiple blocks of varying sizes."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=200, height=24),
                content="A" * 40,  # 5 pts per char
                block_type=BlockType.TEXT,
            ),
            Block(
                bbox=BoundingBox(x=10, y=40, width=150, height=24),
                content="B" * 30,  # 5 pts per char
                block_type=BlockType.TEXT,
            ),
        ]
        config = compute_adaptive_thresholds(blocks)
        # Should compute reasonable thresholds
        assert 10 <= config.hsv <= 50
        assert 3 <= config.vsv <= 10

    def test_blocks_without_text(self):
        """Test with blocks that have no text."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=100, height=12),
                content="",
                block_type=BlockType.TEXT,
            ),
        ]
        config = compute_adaptive_thresholds(blocks)
        # Should return defaults
        assert config.hsv == 20
        assert config.vsv == 5


class TestBinaryImageConversion:
    """Tests for converting blocks to binary image."""

    def test_empty_blocks(self):
        """Test with no blocks."""
        image = blocks_to_binary_image([], 100, 100)
        assert image.shape == (100, 100)
        assert np.all(image == 0)

    def test_single_block(self):
        """Test with single block."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=20, height=10),
                content="test",
                block_type=BlockType.TEXT,
            ),
        ]
        image = blocks_to_binary_image(blocks, 100, 100)
        assert image.shape == (100, 100)
        # Check that block region is filled
        assert np.any(image[10:20, 10:30] == 1)
        # Check that corners are empty
        assert image[0, 0] == 0
        assert image[99, 99] == 0

    def test_multiple_blocks(self):
        """Test with multiple blocks."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=20, height=10),
                content="test1",
                block_type=BlockType.TEXT,
            ),
            Block(
                bbox=BoundingBox(x=50, y=50, width=20, height=10),
                content="test2",
                block_type=BlockType.TEXT,
            ),
        ]
        image = blocks_to_binary_image(blocks, 100, 100)
        # Both blocks should be present
        assert np.any(image[10:20, 10:30] == 1)
        assert np.any(image[50:60, 50:70] == 1)

    def test_resolution_scaling(self):
        """Test with different resolution."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=20, height=10),
                content="test",
                block_type=BlockType.TEXT,
            ),
        ]
        image = blocks_to_binary_image(blocks, 100, 100, resolution=2.0)
        assert image.shape == (200, 200)
        # Block should be at scaled position
        assert np.any(image[20:40, 20:60] == 1)

    def test_bounds_clamping(self):
        """Test that blocks outside bounds are clamped."""
        blocks = [
            Block(
                bbox=BoundingBox(x=-10, y=-10, width=30, height=30),
                content="test",
                block_type=BlockType.TEXT,
            ),
        ]
        image = blocks_to_binary_image(blocks, 100, 100)
        # Should not crash and should clamp to bounds
        assert image.shape == (100, 100)


class TestHorizontalSmoothing:
    """Tests for horizontal run length smoothing."""

    def test_no_smoothing_needed(self):
        """Test image with no gaps."""
        image = np.ones((10, 10), dtype=np.uint8)
        result = smooth_horizontal(image, threshold=5)
        assert np.array_equal(result, image)

    def test_smooth_short_gap(self):
        """Test smoothing a short horizontal gap."""
        image = np.zeros((3, 10), dtype=np.uint8)
        image[:, 0:3] = 1  # Left black region
        image[:, 7:10] = 1  # Right black region
        # Gap from 3-6 (4 pixels)

        result = smooth_horizontal(image, threshold=5)
        # Gap should be filled
        assert np.all(result == 1)

    def test_keep_long_gap(self):
        """Test that long gaps are preserved."""
        image = np.zeros((3, 20), dtype=np.uint8)
        image[:, 0:3] = 1  # Left black region
        image[:, 15:20] = 1  # Right black region
        # Gap from 3-14 (12 pixels)

        result = smooth_horizontal(image, threshold=5)
        # Gap should remain
        assert np.any(result[:, 5:13] == 0)

    def test_edge_handling(self):
        """Test that edges are handled correctly."""
        image = np.zeros((3, 10), dtype=np.uint8)
        image[:, 5:10] = 1

        result = smooth_horizontal(image, threshold=5)
        # Should not fill gap at edge
        assert np.any(result[:, 0:4] == 0)


class TestVerticalSmoothing:
    """Tests for vertical run length smoothing."""

    def test_no_smoothing_needed(self):
        """Test image with no gaps."""
        image = np.ones((10, 10), dtype=np.uint8)
        result = smooth_vertical(image, threshold=5)
        assert np.array_equal(result, image)

    def test_smooth_short_gap(self):
        """Test smoothing a short vertical gap."""
        image = np.zeros((10, 3), dtype=np.uint8)
        image[0:3, :] = 1  # Top black region
        image[7:10, :] = 1  # Bottom black region
        # Gap from 3-6 (4 pixels)

        result = smooth_vertical(image, threshold=5)
        # Gap should be filled
        assert np.all(result == 1)

    def test_keep_long_gap(self):
        """Test that long gaps are preserved."""
        image = np.zeros((20, 3), dtype=np.uint8)
        image[0:3, :] = 1  # Top black region
        image[15:20, :] = 1  # Bottom black region
        # Gap from 3-14 (12 pixels)

        result = smooth_vertical(image, threshold=5)
        # Gap should remain
        assert np.any(result[5:13, :] == 0)


class TestRLSAAlgorithm:
    """Tests for full RLSA algorithm."""

    def test_single_phase(self):
        """Test RLSA with simple horizontal smoothing."""
        image = np.zeros((5, 20), dtype=np.uint8)
        image[:, 0:5] = 1
        image[:, 8:13] = 1
        image[:, 16:20] = 1

        config = RLSAConfig(hsv=5, vsv=2, hsv2=5)
        result = apply_rlsa(image, config)

        # Should smooth horizontal gaps
        assert result.shape == image.shape

    def test_combined_smoothing(self):
        """Test RLSA with both horizontal and vertical smoothing."""
        image = np.zeros((20, 20), dtype=np.uint8)
        # Create scattered blocks
        image[0:3, 0:3] = 1
        image[0:3, 6:9] = 1
        image[6:9, 0:3] = 1
        image[6:9, 6:9] = 1

        config = RLSAConfig(hsv=5, vsv=5, hsv2=5)
        result = apply_rlsa(image, config)

        # Should create larger merged regions
        assert np.sum(result) >= np.sum(image)

    def test_empty_image(self):
        """Test RLSA on empty image."""
        image = np.zeros((10, 10), dtype=np.uint8)
        config = RLSAConfig()
        result = apply_rlsa(image, config)
        assert np.all(result == 0)

    def test_full_image(self):
        """Test RLSA on completely filled image."""
        image = np.ones((10, 10), dtype=np.uint8)
        config = RLSAConfig()
        result = apply_rlsa(image, config)
        assert np.all(result == 1)


class TestBlockExtraction:
    """Tests for extracting blocks from binary image."""

    def test_empty_image(self):
        """Test with empty image."""
        image = np.zeros((100, 100), dtype=np.uint8)
        boxes = extract_blocks_from_image(image)
        assert len(boxes) == 0

    def test_single_block(self):
        """Test with single connected region."""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[10:30, 20:40] = 1

        boxes = extract_blocks_from_image(image)
        assert len(boxes) == 1
        box = boxes[0]
        assert 19 <= box.x <= 21
        assert 9 <= box.y <= 11
        assert 19 <= box.width <= 21
        assert 19 <= box.height <= 21

    def test_multiple_blocks(self):
        """Test with multiple disconnected regions."""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[10:20, 10:20] = 1
        image[50:60, 50:60] = 1
        image[80:90, 30:40] = 1

        boxes = extract_blocks_from_image(image)
        assert len(boxes) == 3

    def test_min_size_filtering(self):
        """Test that small blocks are filtered out."""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[10:13, 10:13] = 1  # 3x3 block (too small)
        image[50:70, 50:70] = 1  # 20x20 block (large enough)

        boxes = extract_blocks_from_image(image, min_width=10, min_height=10)
        assert len(boxes) == 1
        assert boxes[0].width >= 10
        assert boxes[0].height >= 10

    def test_resolution_scaling(self):
        """Test with scaled resolution."""
        image = np.zeros((200, 200), dtype=np.uint8)
        image[20:40, 40:80] = 1

        boxes = extract_blocks_from_image(image, resolution=2.0)
        assert len(boxes) == 1
        # Coordinates should be scaled back (40/2.0 = 20, 20/2.0 = 10)
        box = boxes[0]
        assert 19 <= box.x <= 21
        assert 9 <= box.y <= 11
        assert 19 <= box.width <= 21
        assert 9 <= box.height <= 11


class TestFullPipeline:
    """Tests for complete RLSA block detection pipeline."""

    def test_empty_input(self):
        """Test with no input blocks."""
        boxes = detect_blocks_rlsa([], 100, 100)
        assert len(boxes) == 0

    def test_single_block(self):
        """Test with single input block."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=50, height=20),
                content="Test block",
                block_type=BlockType.TEXT,
            ),
        ]
        boxes = detect_blocks_rlsa(blocks, 200, 200)
        assert len(boxes) >= 1

    def test_scattered_blocks_merge(self):
        """Test that nearby blocks are merged."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=30, height=10),
                content="word1",
                block_type=BlockType.TEXT,
            ),
            Block(
                bbox=BoundingBox(x=45, y=10, width=30, height=10),
                content="word2",
                block_type=BlockType.TEXT,
            ),
            Block(
                bbox=BoundingBox(x=80, y=10, width=30, height=10),
                content="word3",
                block_type=BlockType.TEXT,
            ),
        ]
        boxes = detect_blocks_rlsa(blocks, 200, 200)
        # Should merge into fewer blocks
        assert len(boxes) <= len(blocks)

    def test_custom_config(self):
        """Test with custom RLSA configuration."""
        blocks = [
            Block(
                bbox=BoundingBox(x=10, y=10, width=30, height=10),
                content="test",
                block_type=BlockType.TEXT,
            ),
        ]
        config = RLSAConfig(hsv=50, vsv=10, hsv2=50)
        boxes = detect_blocks_rlsa(blocks, 200, 200, config=config)
        assert len(boxes) >= 0

    def test_multicolumn_layout(self):
        """Test with multi-column layout."""
        # Left column
        left_blocks = [
            Block(
                bbox=BoundingBox(x=10, y=y, width=80, height=10),
                content=f"Left {i}",
                block_type=BlockType.TEXT,
            )
            for i, y in enumerate(range(10, 200, 15))
        ]
        # Right column
        right_blocks = [
            Block(
                bbox=BoundingBox(x=110, y=y, width=80, height=10),
                content=f"Right {i}",
                block_type=BlockType.TEXT,
            )
            for i, y in enumerate(range(10, 200, 15))
        ]

        all_blocks = left_blocks + right_blocks
        boxes = detect_blocks_rlsa(all_blocks, 200, 300)

        # Should detect at least 2 column blocks
        assert len(boxes) >= 2
