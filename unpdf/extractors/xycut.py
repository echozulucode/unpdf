"""Recursive XY-Cut algorithm for document layout segmentation.

This module implements the XY-Cut algorithm for hierarchical page segmentation.
The algorithm recursively splits the page into regions using projection profiles.
"""

import statistics
from dataclasses import dataclass

from unpdf.models.layout import Block, BoundingBox


@dataclass
class ProjectionProfile:
    """Projection profile for XY-Cut algorithm."""

    horizontal: list[int]  # Sum of text widths at each y-coordinate
    vertical: list[int]  # Sum of text heights at each x-coordinate
    resolution: float = 1.0  # Pixels per coordinate unit


def compute_projection_profiles(
    blocks: list[Block], bbox: BoundingBox, resolution: float = 1.0
) -> ProjectionProfile:
    """Compute horizontal and vertical projection profiles.

    Args:
        blocks: List of text blocks to analyze
        bbox: Bounding box of the region
        resolution: Resolution for binning (pixels per unit)

    Returns:
        ProjectionProfile with horizontal and vertical histograms
    """
    h_bins = int((bbox.y1 - bbox.y0) / resolution) + 1
    v_bins = int((bbox.x1 - bbox.x0) / resolution) + 1

    horizontal = [0] * h_bins
    vertical = [0] * v_bins

    for block in blocks:
        # Horizontal profile: sum text widths at each y
        y_start = int((block.bbox.y - bbox.y) / resolution)
        y_end = int((block.bbox.y + block.bbox.height - bbox.y) / resolution)
        for y in range(max(0, y_start), min(h_bins, y_end + 1)):
            horizontal[y] += int(block.bbox.width)

        # Vertical profile: sum text heights at each x
        x_start = int((block.bbox.x - bbox.x) / resolution)
        x_end = int((block.bbox.x + block.bbox.width - bbox.x) / resolution)
        for x in range(max(0, x_start), min(v_bins, x_end + 1)):
            vertical[x] += int(block.bbox.height)

    return ProjectionProfile(
        horizontal=horizontal, vertical=vertical, resolution=resolution
    )


def find_valleys(
    profile: list[int], threshold: float, min_width: int = 1
) -> list[tuple[int, int]]:
    """Find valleys (low-density regions) in a projection profile.

    Args:
        profile: Projection profile histogram
        threshold: Maximum value to consider a valley
        min_width: Minimum width of a valley

    Returns:
        List of (start, end) tuples for each valley
    """
    valleys = []
    in_valley = False
    valley_start = 0

    for i, value in enumerate(profile):
        if value <= threshold and not in_valley:
            in_valley = True
            valley_start = i
        elif value > threshold and in_valley:
            if i - valley_start >= min_width:
                valleys.append((valley_start, i - 1))
            in_valley = False

    # Handle valley at end
    if in_valley and len(profile) - valley_start >= min_width:
        valleys.append((valley_start, len(profile) - 1))

    return valleys


def find_widest_valley(valleys: list[tuple[int, int]]) -> int | None:
    """Find the midpoint of the widest valley.

    Args:
        valleys: List of (start, end) tuples

    Returns:
        Midpoint coordinate of widest valley, or None if no valleys
    """
    if not valleys:
        return None

    widest = max(valleys, key=lambda v: v[1] - v[0])
    return (widest[0] + widest[1]) // 2


def compute_thresholds(blocks: list[Block]) -> tuple[float, float]:
    """Compute adaptive thresholds for valley detection.

    Args:
        blocks: List of text blocks

    Returns:
        Tuple of (horizontal_threshold, vertical_threshold)
    """
    if not blocks:
        return (0.0, 0.0)

    # Compute average character size
    heights = [block.bbox.height for block in blocks]
    widths = [
        block.bbox.width / max(1, len(str(block.content).strip()))
        for block in blocks
        if block.content and str(block.content).strip()
    ]

    avg_height = statistics.mean(heights) if heights else 10.0
    avg_width = statistics.mean(widths) if widths else 5.0

    # Horizontal threshold: 0.5-2.0× character height
    # Vertical threshold: 1.5-3.0× character width
    # Use lower multipliers for more sensitive detection
    h_threshold = avg_height * 0.5
    v_threshold = avg_width * 1.5

    return (h_threshold, v_threshold)


def recursive_xycut(
    blocks: list[Block],
    bbox: BoundingBox,
    depth: int = 0,
    max_depth: int = 10,
) -> list[list[Block]]:
    """Recursively segment blocks using XY-Cut algorithm.

    Args:
        blocks: List of text blocks to segment
        bbox: Bounding box of the region
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        List of block groups, each representing a region
    """
    if not blocks or depth >= max_depth:
        return [blocks] if blocks else []

    # Compute projection profiles
    resolution = 1.0
    profiles = compute_projection_profiles(blocks, bbox, resolution)

    # Compute adaptive thresholds
    h_threshold, v_threshold = compute_thresholds(blocks)

    # Find valleys in both directions
    h_valleys = find_valleys(profiles.horizontal, h_threshold, min_width=3)
    v_valleys = find_valleys(profiles.vertical, v_threshold, min_width=3)

    # Filter out valleys that are mostly outside content area
    # Compute content bounds
    min_y = min(b.bbox.y for b in blocks)
    max_y = max(b.bbox.y + b.bbox.height for b in blocks)
    min_x = min(b.bbox.x for b in blocks)
    max_x = max(b.bbox.x + b.bbox.width for b in blocks)

    # Filter horizontal valleys (should be between min_y and max_y)
    # Valley must start at or after min_y and end at or before max_y
    h_valleys = [
        v
        for v in h_valleys
        if v[0] >= (min_y - bbox.y) / resolution
        and v[1] <= (max_y - bbox.y) / resolution
    ]

    # Filter vertical valleys (should be between min_x and max_x)
    # Valley must start at or after min_x and end at or before max_x
    v_valleys = [
        v
        for v in v_valleys
        if v[0] >= (min_x - bbox.x) / resolution
        and v[1] <= (max_x - bbox.x) / resolution
    ]

    # Find widest valley
    h_split = find_widest_valley(h_valleys)
    v_split = find_widest_valley(v_valleys)

    # Determine split direction
    split_horizontal = False
    split_coord = None

    if h_split is not None and v_split is not None:
        # Compare valley widths
        h_width = max(v[1] - v[0] for v in h_valleys)
        v_width = max(v[1] - v[0] for v in v_valleys)
        if h_width > v_width:
            split_horizontal = True
            split_coord = h_split
        else:
            split_coord = v_split
    elif h_split is not None:
        split_horizontal = True
        split_coord = h_split
    elif v_split is not None:
        split_coord = v_split
    else:
        # No valleys found, return as single region
        return [blocks]

    # Convert split coordinate to actual coordinate
    if split_horizontal:
        split_pos = bbox.y + split_coord * resolution
        # Split blocks into above and below
        above = [b for b in blocks if b.bbox.y + b.bbox.height <= split_pos]
        below = [b for b in blocks if b.bbox.y >= split_pos]

        # Blocks that straddle - assign to closer side
        straddling = [b for b in blocks if b not in above and b not in below]
        for b in straddling:
            mid = b.bbox.y + b.bbox.height / 2
            if mid < split_pos:
                above.append(b)
            else:
                below.append(b)

        # If split didn't partition, return as single region
        if not above or not below:
            return [blocks]

        # Create sub-bounding boxes
        bbox_above = BoundingBox(bbox.x, bbox.y, bbox.width, split_pos - bbox.y)
        bbox_below = BoundingBox(
            bbox.x, split_pos, bbox.width, bbox.y + bbox.height - split_pos
        )

        # Recurse
        result = []
        result.extend(recursive_xycut(above, bbox_above, depth + 1, max_depth))
        result.extend(recursive_xycut(below, bbox_below, depth + 1, max_depth))
        return result
    else:
        split_pos = bbox.x + split_coord * resolution
        # Split blocks into left and right
        left = [b for b in blocks if b.bbox.x + b.bbox.width <= split_pos]
        right = [b for b in blocks if b.bbox.x >= split_pos]

        # Blocks that straddle - assign to closer side
        straddling = [b for b in blocks if b not in left and b not in right]
        for b in straddling:
            mid = b.bbox.x + b.bbox.width / 2
            if mid < split_pos:
                left.append(b)
            else:
                right.append(b)

        # If split didn't partition, return as single region
        if not left or not right:
            return [blocks]

        # Create sub-bounding boxes
        bbox_left = BoundingBox(bbox.x, bbox.y, split_pos - bbox.x, bbox.height)
        bbox_right = BoundingBox(
            split_pos, bbox.y, bbox.x + bbox.width - split_pos, bbox.height
        )

        # Recurse
        result = []
        result.extend(recursive_xycut(left, bbox_left, depth + 1, max_depth))
        result.extend(recursive_xycut(right, bbox_right, depth + 1, max_depth))
        return result


def segment_page_xycut(blocks: list[Block]) -> list[list[Block]]:
    """Segment page blocks using XY-Cut algorithm.

    Args:
        blocks: List of text blocks on the page

    Returns:
        List of block groups, each representing a segmented region
    """
    if not blocks:
        return []

    # Compute overall bounding box
    x_min = min(b.bbox.x for b in blocks)
    y_min = min(b.bbox.y for b in blocks)
    x_max = max(b.bbox.x + b.bbox.width for b in blocks)
    y_max = max(b.bbox.y + b.bbox.height for b in blocks)
    bbox = BoundingBox(x_min, y_min, x_max - x_min, y_max - y_min)

    # Run recursive XY-Cut
    regions = recursive_xycut(blocks, bbox)

    return regions
