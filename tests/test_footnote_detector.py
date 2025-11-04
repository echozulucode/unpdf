"""Tests for footnote detection."""

import pytest

from unpdf.processors.footnote_detector import (
    Footnote,
    FootnoteContent,
    FootnoteDetector,
    FootnoteReference,
)
from unpdf.processors.layout_analyzer import BoundingBox, TextBlock


class TestFootnoteDetector:
    """Test the FootnoteDetector class."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        detector = FootnoteDetector()
        assert detector.superscript_size_ratio == 0.7
        assert detector.superscript_offset_threshold == 0.3
        assert detector.footer_region_ratio == 0.15
        assert detector.proximity_threshold == 50.0
        assert detector.min_marker_confidence == 0.6

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        detector = FootnoteDetector(
            superscript_size_ratio=0.6,
            superscript_offset_threshold=0.4,
            footer_region_ratio=0.2,
            proximity_threshold=40.0,
            min_marker_confidence=0.7,
        )
        assert detector.superscript_size_ratio == 0.6
        assert detector.superscript_offset_threshold == 0.4
        assert detector.footer_region_ratio == 0.2
        assert detector.proximity_threshold == 40.0
        assert detector.min_marker_confidence == 0.7


class TestSuperscriptDetection:
    """Test superscript detection."""

    def test_is_superscript_small_font(self):
        """Test superscript detection with small font."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="1",
            font_size=6.0,  # 0.5× body font
        )
        assert detector._is_superscript(block, 12.0)

    def test_is_superscript_large_font(self):
        """Test that large fonts are not detected as superscript."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="1",
            font_size=10.0,  # 0.83× body font
        )
        assert not detector._is_superscript(block, 12.0)

    def test_is_superscript_long_text(self):
        """Test that long text is not detected as superscript."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 120, 105),
            text="1234",
            font_size=6.0,
        )
        assert not detector._is_superscript(block, 12.0)

    def test_is_superscript_short_text(self):
        """Test that short text passes length check."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 110, 105),
            text="12",
            font_size=6.0,
        )
        assert detector._is_superscript(block, 12.0)


class TestMarkerClassification:
    """Test marker classification."""

    def test_classify_numeric_marker(self):
        """Test classification of numeric markers."""
        detector = FootnoteDetector()
        assert detector._classify_marker("1") == "numeric"
        assert detector._classify_marker("42") == "numeric"
        assert detector._classify_marker("999") == "numeric"

    def test_classify_symbol_marker(self):
        """Test classification of symbol markers."""
        detector = FootnoteDetector()
        assert detector._classify_marker("*") == "symbol"
        assert detector._classify_marker("†") == "symbol"
        assert detector._classify_marker("‡") == "symbol"
        assert detector._classify_marker("§") == "symbol"

    def test_classify_letter_marker(self):
        """Test classification of letter markers."""
        detector = FootnoteDetector()
        assert detector._classify_marker("a") == "letter"
        assert detector._classify_marker("Z") == "letter"
        assert detector._classify_marker("i") == "letter"
        assert detector._classify_marker("iv") == "letter"

    def test_classify_invalid_marker(self):
        """Test classification of invalid markers."""
        detector = FootnoteDetector()
        assert detector._classify_marker("abc") is None
        assert detector._classify_marker("@") is None
        assert detector._classify_marker("") is None


class TestMarkerConfidence:
    """Test marker confidence calculation."""

    def test_high_confidence_numeric_marker(self):
        """Test high confidence for good numeric marker."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="1",
            font_size=6.0,  # 0.5× body font
        )
        confidence = detector._calculate_marker_confidence(block, 12.0, "numeric")
        assert confidence >= 0.8

    def test_medium_confidence_marker(self):
        """Test medium confidence for acceptable marker."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 110, 105),
            text="12",
            font_size=8.0,  # 0.67× body font
        )
        confidence = detector._calculate_marker_confidence(block, 12.0, "numeric")
        # With 2-digit marker and good font size, confidence is higher
        assert 0.8 <= confidence <= 1.0

    def test_low_confidence_marker(self):
        """Test low confidence for poor marker."""
        detector = FootnoteDetector()
        block = TextBlock(
            bbox=BoundingBox(100, 100, 115, 105),
            text="abc",
            font_size=8.5,  # 0.71× body font
        )
        confidence = detector._calculate_marker_confidence(block, 12.0, "letter")
        assert confidence < 0.7


class TestFooterContentDetection:
    """Test footer content detection."""

    def test_extract_numeric_footer_marker(self):
        """Test extraction of numeric marker from footer."""
        detector = FootnoteDetector()
        result = detector._extract_footer_marker("1. This is a footnote.")
        assert result == ("1", "This is a footnote.")

    def test_extract_numeric_footer_marker_space(self):
        """Test extraction of numeric marker with space separator."""
        detector = FootnoteDetector()
        result = detector._extract_footer_marker("2 Another footnote.")
        assert result == ("2", "Another footnote.")

    def test_extract_symbol_footer_marker(self):
        """Test extraction of symbol marker from footer."""
        detector = FootnoteDetector()
        result = detector._extract_footer_marker("* Footnote with asterisk.")
        assert result == ("*", "Footnote with asterisk.")

    def test_extract_letter_footer_marker(self):
        """Test extraction of letter marker from footer."""
        detector = FootnoteDetector()
        result = detector._extract_footer_marker("a. First footnote.")
        assert result == ("a", "First footnote.")

    def test_extract_no_marker(self):
        """Test that text without marker returns None."""
        detector = FootnoteDetector()
        result = detector._extract_footer_marker("Just regular text.")
        assert result is None


class TestContentConfidence:
    """Test content confidence calculation."""

    def test_high_confidence_content(self):
        """Test high confidence for good content."""
        detector = FootnoteDetector()
        confidence = detector._calculate_content_confidence(
            "1", "This is a well-formed footnote with proper punctuation."
        )
        assert confidence >= 0.8

    def test_medium_confidence_content(self):
        """Test medium confidence for acceptable content."""
        detector = FootnoteDetector()
        confidence = detector._calculate_content_confidence("*", "Short footnote")
        assert 0.5 <= confidence < 0.8

    def test_low_confidence_content(self):
        """Test low confidence for poor content."""
        detector = FootnoteDetector()
        confidence = detector._calculate_content_confidence("x", "short")
        assert confidence < 0.6


class TestFootnoteDetection:
    """Test complete footnote detection."""

    def test_detect_numeric_footnote(self):
        """Test detection of numeric footnote."""
        detector = FootnoteDetector(min_marker_confidence=0.5)

        # Reference in body
        ref_block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="1",
            font_size=6.0,
        )

        # Content in footer
        footer_block = TextBlock(
            bbox=BoundingBox(50, 750, 500, 765),
            text="1. This is the footnote content.",
            font_size=9.0,
        )

        blocks = [ref_block, footer_block]
        footnotes = detector.detect_footnotes(
            blocks, page_height=800.0, body_font_size=12.0
        )

        assert len(footnotes) == 1
        assert footnotes[0].reference.marker == "1"
        assert footnotes[0].content is not None
        assert "footnote content" in footnotes[0].content.text

    def test_detect_symbol_footnote(self):
        """Test detection of symbol footnote."""
        detector = FootnoteDetector(min_marker_confidence=0.5)

        ref_block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="*",
            font_size=6.0,
        )

        footer_block = TextBlock(
            bbox=BoundingBox(50, 750, 500, 765),
            text="* Asterisk footnote.",
            font_size=9.0,
        )

        blocks = [ref_block, footer_block]
        footnotes = detector.detect_footnotes(
            blocks, page_height=800.0, body_font_size=12.0
        )

        assert len(footnotes) == 1
        assert footnotes[0].reference.marker == "*"
        assert footnotes[0].content is not None

    def test_detect_multiple_footnotes(self):
        """Test detection of multiple footnotes."""
        detector = FootnoteDetector(min_marker_confidence=0.5)

        ref1 = TextBlock(bbox=BoundingBox(100, 100, 105, 105), text="1", font_size=6.0)
        ref2 = TextBlock(bbox=BoundingBox(200, 200, 205, 205), text="2", font_size=6.0)

        footer1 = TextBlock(
            bbox=BoundingBox(50, 750, 500, 765),
            text="1. First footnote.",
            font_size=9.0,
        )
        footer2 = TextBlock(
            bbox=BoundingBox(50, 770, 500, 785),
            text="2. Second footnote.",
            font_size=9.0,
        )

        blocks = [ref1, ref2, footer1, footer2]
        footnotes = detector.detect_footnotes(
            blocks, page_height=800.0, body_font_size=12.0
        )

        assert len(footnotes) == 2
        assert footnotes[0].reference.marker == "1"
        assert footnotes[1].reference.marker == "2"

    def test_detect_reference_without_content(self):
        """Test detection of reference without matching content."""
        detector = FootnoteDetector(min_marker_confidence=0.5)

        ref_block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="1",
            font_size=6.0,
        )

        blocks = [ref_block]
        footnotes = detector.detect_footnotes(
            blocks, page_height=800.0, body_font_size=12.0
        )

        assert len(footnotes) == 1
        assert footnotes[0].reference.marker == "1"
        assert footnotes[0].content is None
        # Confidence should be lower without matching content
        assert footnotes[0].confidence < 1.0

    def test_filter_low_confidence_footnotes(self):
        """Test that low confidence footnotes are filtered out."""
        detector = FootnoteDetector(min_marker_confidence=0.8)

        # Create a marker that will have low confidence (large font)
        ref_block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="x",
            font_size=10.0,  # Too large for superscript
        )

        blocks = [ref_block]
        footnotes = detector.detect_footnotes(
            blocks, page_height=800.0, body_font_size=12.0
        )

        # Should be filtered out due to low confidence
        assert len(footnotes) == 0


class TestReferenceStyleExtraction:
    """Test reference style extraction."""

    def test_extract_numeric_style(self):
        """Test extraction of numeric reference style."""
        detector = FootnoteDetector()
        footnotes = [
            Footnote(
                reference=FootnoteReference(
                    marker="1",
                    bbox=BoundingBox(0, 0, 5, 5),
                    marker_type="numeric",
                    confidence=0.9,
                ),
                confidence=0.9,
            ),
            Footnote(
                reference=FootnoteReference(
                    marker="2",
                    bbox=BoundingBox(0, 0, 5, 5),
                    marker_type="numeric",
                    confidence=0.9,
                ),
                confidence=0.9,
            ),
        ]
        style = detector.extract_reference_style(footnotes)
        assert style == "numeric"

    def test_extract_symbol_style(self):
        """Test extraction of symbol reference style."""
        detector = FootnoteDetector()
        footnotes = [
            Footnote(
                reference=FootnoteReference(
                    marker="*",
                    bbox=BoundingBox(0, 0, 5, 5),
                    marker_type="symbol",
                    confidence=0.9,
                ),
                confidence=0.9,
            ),
            Footnote(
                reference=FootnoteReference(
                    marker="†",
                    bbox=BoundingBox(0, 0, 5, 5),
                    marker_type="symbol",
                    confidence=0.9,
                ),
                confidence=0.9,
            ),
        ]
        style = detector.extract_reference_style(footnotes)
        assert style == "symbol"

    def test_extract_mixed_style(self):
        """Test extraction of mixed reference style."""
        detector = FootnoteDetector()
        footnotes = [
            Footnote(
                reference=FootnoteReference(
                    marker="1",
                    bbox=BoundingBox(0, 0, 5, 5),
                    marker_type="numeric",
                    confidence=0.9,
                ),
                confidence=0.9,
            ),
            Footnote(
                reference=FootnoteReference(
                    marker="*",
                    bbox=BoundingBox(0, 0, 5, 5),
                    marker_type="symbol",
                    confidence=0.9,
                ),
                confidence=0.9,
            ),
        ]
        style = detector.extract_reference_style(footnotes)
        assert style == "mixed"

    def test_extract_empty_list(self):
        """Test extraction with empty footnote list."""
        detector = FootnoteDetector()
        style = detector.extract_reference_style([])
        assert style is None


class TestFooterRegionDetection:
    """Test footer region detection."""

    def test_footer_content_in_footer_region(self):
        """Test that content in footer region is detected."""
        detector = FootnoteDetector()

        footer_block = TextBlock(
            bbox=BoundingBox(50, 750, 500, 765),
            text="1. Footnote in footer.",
            font_size=9.0,
        )

        page_height = 800.0
        footer_y = page_height * (1 - detector.footer_region_ratio)

        contents = detector._detect_footer_content([footer_block], footer_y)
        assert len(contents) == 1

    def test_footer_content_outside_footer_region(self):
        """Test that content outside footer region is ignored."""
        detector = FootnoteDetector()

        body_block = TextBlock(
            bbox=BoundingBox(50, 400, 500, 415),
            text="1. Not a footnote.",
            font_size=12.0,
        )

        page_height = 800.0
        footer_y = page_height * (1 - detector.footer_region_ratio)

        contents = detector._detect_footer_content([body_block], footer_y)
        assert len(contents) == 0


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_blocks_list(self):
        """Test with empty blocks list."""
        detector = FootnoteDetector()
        footnotes = detector.detect_footnotes(
            [], page_height=800.0, body_font_size=12.0
        )
        assert len(footnotes) == 0

    def test_no_superscripts(self):
        """Test with no superscript blocks."""
        detector = FootnoteDetector()

        body_block = TextBlock(
            bbox=BoundingBox(50, 100, 500, 115),
            text="Regular body text.",
            font_size=12.0,
        )

        footnotes = detector.detect_footnotes(
            [body_block], page_height=800.0, body_font_size=12.0
        )
        assert len(footnotes) == 0

    def test_no_footer_content(self):
        """Test with references but no footer content."""
        detector = FootnoteDetector(min_marker_confidence=0.5)

        ref_block = TextBlock(
            bbox=BoundingBox(100, 100, 105, 105),
            text="1",
            font_size=6.0,
        )

        footnotes = detector.detect_footnotes(
            [ref_block], page_height=800.0, body_font_size=12.0
        )
        # Should still detect reference even without content
        assert len(footnotes) == 1
        assert footnotes[0].content is None
