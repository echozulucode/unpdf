"""Run Length Smoothing Algorithm (RLSA) for block detection.

The RLSA algorithm detects text blocks by smoothing runs of white pixels
in a binary representation of the document. It operates in three phases:
1. Horizontal smoothing with threshold hsv
2. Vertical smoothing with threshold vsv
3. Logical AND + additional horizontal smoothing

This helps identify coherent text regions and separate them from whitespace.
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from unpdf.models.layout import Block, BoundingBox


@dataclass
class RLSAConfig:
    """Configuration for RLSA algorithm.

    Attributes:
        hsv: Horizontal smoothing value (pixels). Typical: 10-50.
        vsv: Vertical smoothing value (pixels). Typical: 3-10.
        hsv2: Second horizontal smoothing value. Typical: same as hsv.
    """

    hsv: int = 20
    vsv: int = 5
    hsv2: int = 20


def compute_adaptive_thresholds(
    blocks: list[Block],
) -> RLSAConfig:
    """Compute adaptive RLSA thresholds from document statistics.

    Thresholds are derived from:
    - Mean character width (for hsv)
    - Mean line spacing (for vsv)

    Args:
        blocks: List of text blocks with bounding boxes.

    Returns:
        RLSA configuration with adaptive thresholds.
    """
    if not blocks:
        return RLSAConfig()

    # Estimate character width from block widths and content length
    char_widths = []
    line_heights = []

    for block in blocks:
        content = block.content if isinstance(block.content, str) else ""
        if content and len(content.strip()) > 0:
            # Estimate average character width
            text_len = len(content.strip())
            if text_len > 0:
                char_width = block.bbox.width / text_len
                char_widths.append(char_width)

        # Estimate line height from block height
        line_count = max(1, content.count("\n") + 1) if content else 1
        line_height = block.bbox.height / line_count
        line_heights.append(line_height)

    if not char_widths or not line_heights:
        return RLSAConfig()

    mean_char_width = np.mean(char_widths)
    mean_line_height = np.mean(line_heights)

    # HSV: Smooths spaces within words/lines (typically 5-10 character widths)
    hsv = int(mean_char_width * 8)
    hsv = max(10, min(50, hsv))  # Clamp to reasonable range

    # VSV: Smooths vertical gaps between lines (typically 1-2 line heights)
    vsv = int(mean_line_height * 1.5)
    vsv = max(3, min(10, vsv))  # Clamp to reasonable range

    return RLSAConfig(hsv=hsv, vsv=vsv, hsv2=hsv)


def blocks_to_binary_image(
    blocks: list[Block],
    width: float,
    height: float,
    resolution: float = 1.0,
) -> npt.NDArray[np.uint8]:
    """Convert blocks to binary image representation.

    Creates a 2D binary array where 1 represents text and 0 represents whitespace.

    Args:
        blocks: List of text blocks.
        width: Page width in points.
        height: Page height in points.
        resolution: Scaling factor for image resolution (default: 1.0).

    Returns:
        Binary image as numpy array (0 = white, 1 = black/text).
    """
    # Scale dimensions by resolution
    img_width = int(width * resolution)
    img_height = int(height * resolution)

    # Initialize empty image (all white)
    image = np.zeros((img_height, img_width), dtype=np.uint8)

    # Fill in text regions
    for block in blocks:
        x1 = int(block.bbox.x * resolution)
        y1 = int(block.bbox.y * resolution)
        x2 = int((block.bbox.x + block.bbox.width) * resolution)
        y2 = int((block.bbox.y + block.bbox.height) * resolution)

        # Clamp to image bounds
        x1 = max(0, min(img_width - 1, x1))
        x2 = max(0, min(img_width, x2))
        y1 = max(0, min(img_height - 1, y1))
        y2 = max(0, min(img_height, y2))

        if x2 > x1 and y2 > y1:
            image[y1:y2, x1:x2] = 1

    return image


def smooth_horizontal(
    image: npt.NDArray[np.uint8],
    threshold: int,
) -> npt.NDArray[np.uint8]:
    """Apply horizontal run length smoothing.

    Fills white runs shorter than threshold with black pixels.

    Args:
        image: Binary image (0 = white, 1 = black).
        threshold: Maximum run length to smooth.

    Returns:
        Smoothed binary image.
    """
    result = image.copy()
    img_height, img_width = image.shape

    for y in range(img_height):
        x = 0
        while x < img_width:
            # Find start of white run
            if image[y, x] == 0:
                run_start = x
                run_length = 0

                # Count white pixels
                while x < img_width and image[y, x] == 0:
                    run_length += 1
                    x += 1

                # Smooth if run is short enough
                if run_length <= threshold and run_start > 0 and x < img_width:
                    result[y, run_start:x] = 1
            else:
                x += 1

    return result  # type: ignore[no-any-return]


def smooth_vertical(
    image: npt.NDArray[np.uint8],
    threshold: int,
) -> npt.NDArray[np.uint8]:
    """Apply vertical run length smoothing.

    Fills white runs shorter than threshold with black pixels.

    Args:
        image: Binary image (0 = white, 1 = black).
        threshold: Maximum run length to smooth.

    Returns:
        Smoothed binary image.
    """
    result = image.copy()
    img_height, img_width = image.shape

    for x in range(img_width):
        y = 0
        while y < img_height:
            # Find start of white run
            if image[y, x] == 0:
                run_start = y
                run_length = 0

                # Count white pixels
                while y < img_height and image[y, x] == 0:
                    run_length += 1
                    y += 1

                # Smooth if run is short enough
                if run_length <= threshold and run_start > 0 and y < img_height:
                    result[run_start:y, x] = 1
            else:
                y += 1

    return result  # type: ignore[no-any-return]


def apply_rlsa(
    image: npt.NDArray[np.uint8],
    config: RLSAConfig,
) -> npt.NDArray[np.uint8]:
    """Apply full RLSA algorithm.

    Three-phase process:
    1. Horizontal smoothing with hsv
    2. Vertical smoothing with vsv
    3. Logical AND + horizontal smoothing with hsv2

    Args:
        image: Binary input image (0 = white, 1 = black).
        config: RLSA configuration.

    Returns:
        Smoothed binary image with detected blocks.
    """
    # Phase 1: Horizontal smoothing
    h_smooth = smooth_horizontal(image, config.hsv)

    # Phase 2: Vertical smoothing
    v_smooth = smooth_vertical(image, config.vsv)

    # Phase 3: Logical AND + additional horizontal smoothing
    combined = np.logical_and(h_smooth, v_smooth).astype(np.uint8)
    final = smooth_horizontal(combined, config.hsv2)

    return final


def extract_blocks_from_image(
    image: npt.NDArray[np.uint8],
    resolution: float = 1.0,
    min_width: int = 10,
    min_height: int = 10,
) -> list[BoundingBox]:
    """Extract bounding boxes from binary image.

    Uses connected component analysis to find contiguous regions.

    Args:
        image: Binary image (0 = white, 1 = black).
        resolution: Scaling factor used to create image.
        min_width: Minimum block width to keep.
        min_height: Minimum block height to keep.

    Returns:
        List of bounding boxes for detected blocks.
    """
    from scipy import ndimage  # type: ignore[import-untyped]

    # Label connected components
    labeled, num_features = ndimage.label(image)

    boxes = []

    for i in range(1, num_features + 1):
        # Find pixels belonging to this component
        coords = np.argwhere(labeled == i)

        if len(coords) == 0:
            continue

        # Get bounding box
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        # Convert back to original coordinates
        x = x_min / resolution
        y = y_min / resolution
        width = (x_max - x_min + 1) / resolution
        height = (y_max - y_min + 1) / resolution

        # Filter small boxes
        if width >= min_width and height >= min_height:
            boxes.append(BoundingBox(x=x, y=y, width=width, height=height))

    return boxes


def detect_blocks_rlsa(
    blocks: list[Block],
    page_width: float,
    page_height: float,
    config: RLSAConfig | None = None,
    resolution: float = 1.0,
) -> list[BoundingBox]:
    """Detect text blocks using RLSA algorithm.

    Converts input blocks to binary image, applies RLSA smoothing,
    and extracts resulting block regions.

    Args:
        blocks: Input text blocks from PDF.
        page_width: Page width in points.
        page_height: Page height in points.
        config: RLSA configuration (auto-computed if None).
        resolution: Image resolution scaling factor.

    Returns:
        List of detected block bounding boxes.
    """
    if not blocks:
        return []

    # Compute adaptive thresholds if not provided
    if config is None:
        config = compute_adaptive_thresholds(blocks)

    # Convert blocks to binary image
    image = blocks_to_binary_image(blocks, page_width, page_height, resolution)

    # Apply RLSA smoothing
    smoothed = apply_rlsa(image, config)

    # Extract blocks from smoothed image
    detected_boxes = extract_blocks_from_image(
        smoothed,
        resolution=resolution,
        min_width=10,
        min_height=10,
    )

    return detected_boxes
