"""Strike-through text detection for unpdf.

This module detects strike-through text by correlating text spans with nearby
line or rectangle objects that visually cross through the text. PDF doesn't have
native strike-through attributes, so we use heuristic overlay detection.

Example:
    >>> spans = [{"x0": 10, "x1": 50, "top": 100, "bottom": 110}]
    >>> lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
    >>> rects = []
    >>> is_struck_span(spans[0], lines, rects)
    True
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def is_struck_span(
    span_bbox: dict[str, float],
    lines: list[dict[str, Any]],
    rects: list[dict[str, Any]],
    y_band_frac: tuple[float, float] = (0.35, 0.65),
    min_cover: float = 0.6,
    max_thickness_frac: float = 0.08,
) -> bool:
    """Detect if a text span has a strike-through line crossing it.

    Args:
        span_bbox: Text span bounding box with x0, x1, top, bottom coordinates.
        lines: List of line objects from pdfplumber (each has x0, y0, x1, y1).
        rects: List of rectangle objects from pdfplumber (each has x0, top, x1, bottom, height).
        y_band_frac: Tuple of (min, max) fractions defining vertical band where
            strike line sits (e.g., 0.35-0.65 = middle 30% of text height).
        min_cover: Minimum horizontal overlap fraction (0-1) required.
        max_thickness_frac: Maximum thickness as fraction of text height.

    Returns:
        True if strike-through line/rect found, False otherwise.

    Example:
        >>> bbox = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        >>> lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
        >>> is_struck_span(bbox, lines, [])
        True
    """
    x0 = span_bbox["x0"]
    x1 = span_bbox["x1"]
    top = span_bbox["top"]
    bottom = span_bbox["bottom"]

    h = bottom - top
    if h <= 0:
        return False

    # Vertical band where strike line typically sits (middle of text)
    y_min = top + y_band_frac[0] * h
    y_max = top + y_band_frac[1] * h

    # Minimum horizontal overlap length
    min_len = (x1 - x0) * min_cover

    # Maximum line thickness
    max_thickness = h * max_thickness_frac

    def horizontally_covers(obj_x0: float, obj_x1: float) -> bool:
        """Check if object horizontally overlaps text span by min_cover fraction."""
        overlap = max(0, min(x1, obj_x1) - max(x0, obj_x0))
        # Check if overlap is significant relative to EITHER the span OR the object
        # This handles cases where strike line is shorter than the full text span
        span_width = x1 - x0
        obj_width = obj_x1 - obj_x0
        return overlap >= min_len or overlap / obj_width >= min_cover

    # Check lines
    for ln in lines:
        # pdfplumber lines have x0, y0, x1, y1 (y increases downward)
        # For horizontal lines, y0 ≈ y1
        if y_min <= ln["y0"] <= y_max and y_min <= ln["y1"] <= y_max:
            if horizontally_covers(ln["x0"], ln["x1"]):
                logger.debug(
                    f"Strike-through line detected: span=({x0:.1f},{top:.1f},{x1:.1f},{bottom:.1f}), "
                    f"line=({ln['x0']:.1f},{ln['y0']:.1f},{ln['x1']:.1f},{ln['y1']:.1f})"
                )
                return True

    # Check very flat rects used instead of lines
    for rc in rects:
        thickness = rc["height"]
        # Use y0/y1 if available (actual PDF coordinates), otherwise fall back to top/bottom
        rect_y0 = rc.get("y0", rc.get("top"))
        rect_y1 = rc.get("y1", rc.get("bottom"))
        y_mid = (rect_y0 + rect_y1) / 2

        if thickness <= max_thickness and y_min <= y_mid <= y_max:
            if horizontally_covers(rc["x0"], rc["x1"]):
                logger.debug(
                    f"Strike-through rect detected: span=({x0:.1f},{top:.1f},{x1:.1f},{bottom:.1f}), "
                    f"rect=({rc['x0']:.1f},{rect_y0:.1f},{rc['x1']:.1f},{rect_y1:.1f})"
                )
                return True

    return False


def detect_strikethrough_on_page(
    spans: list[dict[str, Any]],
    lines: list[dict[str, Any]],
    rects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect strike-through for all spans on a page.

    Args:
        spans: List of text spans with bbox information.
        lines: List of line objects from pdfplumber.
        rects: List of rectangle objects from pdfplumber.

    Returns:
        List of spans with added 'strikethrough' boolean field.

    Example:
        >>> spans = [{"x0": 10, "x1": 50, "top": 100, "bottom": 110, "text": "test"}]
        >>> lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
        >>> result = detect_strikethrough_on_page(spans, lines, [])
        >>> result[0]["is_strikethrough"]
        True
    """
    for span in spans:
        span["is_strikethrough"] = is_struck_span(span, lines, rects)

    struck_count = sum(1 for s in spans if s.get("is_strikethrough", False))
    if struck_count > 0:
        logger.info(f"Detected {struck_count} strike-through span(s) on page")

    return spans
