"""Tests for strike-through detection."""

import pytest

from unpdf.extractors.strikethrough import (
    detect_strikethrough_on_page,
    is_struck_span,
)


class TestIsStruckSpan:
    """Tests for is_struck_span function."""

    def test_horizontal_line_through_middle(self):
        """Test detection with horizontal line through text middle."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
        rects = []

        assert is_struck_span(span, lines, rects) is True

    def test_flat_rect_through_middle(self):
        """Test detection with flat rectangle through text middle."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = []
        rects = [{"x0": 9, "x1": 51, "top": 104.5, "bottom": 105.3, "height": 0.8}]

        assert is_struck_span(span, lines, rects) is True

    def test_no_line_present(self):
        """Test no detection when no lines or rects present."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = []
        rects = []

        assert is_struck_span(span, lines, rects) is False

    def test_line_too_far_above(self):
        """Test no detection when line is above vertical band."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = [{"x0": 9, "x1": 51, "y0": 102, "y1": 102}]  # Too high
        rects = []

        assert is_struck_span(span, lines, rects) is False

    def test_line_too_far_below(self):
        """Test no detection when line is below vertical band."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = [{"x0": 9, "x1": 51, "y0": 108, "y1": 108}]  # Too low
        rects = []

        assert is_struck_span(span, lines, rects) is False

    def test_line_insufficient_overlap(self):
        """Test no detection when horizontal overlap is insufficient."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        # Line only covers 20 out of 40 pixels (50%)
        lines = [{"x0": 10, "x1": 30, "y0": 105, "y1": 105}]
        rects = []

        # Default min_cover is 60%, so this should fail
        assert is_struck_span(span, lines, rects) is False

    def test_rect_too_thick(self):
        """Test no detection when rectangle is too thick (likely not a strike-through)."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = []
        # Rect with height=2 (20% of text height) - too thick
        rects = [{"x0": 9, "x1": 51, "top": 100, "bottom": 112, "height": 12}]

        assert is_struck_span(span, lines, rects) is False

    def test_multiple_lines_one_matches(self):
        """Test detection when one of multiple lines matches."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        lines = [
            {"x0": 9, "x1": 51, "y0": 102, "y1": 102},  # Too high
            {"x0": 9, "x1": 51, "y0": 105, "y1": 105},  # Perfect match
            {"x0": 9, "x1": 51, "y0": 108, "y1": 108},  # Too low
        ]
        rects = []

        assert is_struck_span(span, lines, rects) is True

    def test_underline_not_detected(self):
        """Test that underlines (at bottom of text) are not detected as strike-through."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        # Line at bottom (underline position)
        lines = [{"x0": 9, "x1": 51, "y0": 109, "y1": 109}]
        rects = []

        # Default y_band is 35-65%, so 109 is outside (109 > 106.5)
        assert is_struck_span(span, lines, rects) is False

    def test_overline_not_detected(self):
        """Test that overlines (at top of text) are not detected as strike-through."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        # Line at top (overline position)
        lines = [{"x0": 9, "x1": 51, "y0": 101, "y1": 101}]
        rects = []

        # Default y_band is 35-65%, so 101 is outside (101 < 103.5)
        assert is_struck_span(span, lines, rects) is False

    def test_custom_parameters(self):
        """Test with custom detection parameters."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 110}
        # Line covers only 50% horizontally
        lines = [{"x0": 10, "x1": 30, "y0": 105, "y1": 105}]
        rects = []

        # With min_cover=0.4, should detect
        assert is_struck_span(span, lines, rects, min_cover=0.4) is True

        # With min_cover=0.6, should not detect
        assert is_struck_span(span, lines, rects, min_cover=0.6) is False

    def test_zero_height_span(self):
        """Test handling of malformed span with zero height."""
        span = {"x0": 10, "x1": 50, "top": 100, "bottom": 100}
        lines = [{"x0": 9, "x1": 51, "y0": 100, "y1": 100}]
        rects = []

        assert is_struck_span(span, lines, rects) is False


class TestDetectStrikethroughOnPage:
    """Tests for detect_strikethrough_on_page function."""

    def test_single_span_with_strikethrough(self):
        """Test detection on single span with strike-through."""
        spans = [{"x0": 10, "x1": 50, "top": 100, "bottom": 110, "text": "test"}]
        lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
        rects = []

        result = detect_strikethrough_on_page(spans, lines, rects)

        assert len(result) == 1
        assert result[0]["strikethrough"] is True

    def test_single_span_without_strikethrough(self):
        """Test detection on single span without strike-through."""
        spans = [{"x0": 10, "x1": 50, "top": 100, "bottom": 110, "text": "test"}]
        lines = []
        rects = []

        result = detect_strikethrough_on_page(spans, lines, rects)

        assert len(result) == 1
        assert result[0]["strikethrough"] is False

    def test_multiple_spans_mixed(self):
        """Test detection on multiple spans with mixed strike-through."""
        spans = [
            {"x0": 10, "x1": 50, "top": 100, "bottom": 110, "text": "struck"},
            {"x0": 60, "x1": 100, "top": 100, "bottom": 110, "text": "normal"},
            {"x0": 110, "x1": 150, "top": 100, "bottom": 110, "text": "struck2"},
        ]
        lines = [
            {"x0": 9, "x1": 51, "y0": 105, "y1": 105},  # Strikes first span
            {"x0": 109, "x1": 151, "y0": 105, "y1": 105},  # Strikes third span
        ]
        rects = []

        result = detect_strikethrough_on_page(spans, lines, rects)

        assert len(result) == 3
        assert result[0]["strikethrough"] is True
        assert result[1]["strikethrough"] is False
        assert result[2]["strikethrough"] is True

    def test_empty_spans_list(self):
        """Test handling of empty spans list."""
        spans = []
        lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
        rects = []

        result = detect_strikethrough_on_page(spans, lines, rects)

        assert len(result) == 0

    def test_preserves_existing_fields(self):
        """Test that existing span fields are preserved."""
        spans = [
            {
                "x0": 10,
                "x1": 50,
                "top": 100,
                "bottom": 110,
                "text": "test",
                "font_size": 12,
                "bold": True,
            }
        ]
        lines = [{"x0": 9, "x1": 51, "y0": 105, "y1": 105}]
        rects = []

        result = detect_strikethrough_on_page(spans, lines, rects)

        assert result[0]["text"] == "test"
        assert result[0]["font_size"] == 12
        assert result[0]["bold"] is True
        assert result[0]["strikethrough"] is True
