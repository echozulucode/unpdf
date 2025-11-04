"""Unit tests for caption detection."""

import pytest

from unpdf.models.layout import BoundingBox
from unpdf.processors.caption_detector import Caption, CaptionDetector, CaptionLink


class TestCaptionDetection:
    """Test caption detection functionality."""

    def test_detect_table_caption(self):
        """Test detection of table captions."""
        detector = CaptionDetector()
        text_blocks = [
            ("Table 1: Sample Data", BoundingBox(100, 100, 200, 20)),
            ("Regular paragraph text", BoundingBox(100, 150, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        assert captions[0].caption_type == "table"
        assert captions[0].number == "1"
        assert captions[0].text == "Table 1: Sample Data"

    def test_detect_figure_caption(self):
        """Test detection of figure captions."""
        detector = CaptionDetector()
        text_blocks = [
            ("Figure 2.3: Process Flow", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        assert captions[0].caption_type == "figure"
        assert captions[0].number == "2.3"

    def test_detect_fig_abbreviation(self):
        """Test detection of abbreviated figure caption."""
        detector = CaptionDetector()
        text_blocks = [
            ("Fig. 5: User Interface", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        assert captions[0].caption_type == "figure"
        assert captions[0].number == "5"

    def test_detect_diagram_caption(self):
        """Test detection of diagram captions."""
        detector = CaptionDetector()
        text_blocks = [
            ("Diagram 1: Architecture", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        assert captions[0].caption_type == "diagram"
        assert captions[0].number == "1"

    def test_detect_chart_caption(self):
        """Test detection of chart captions."""
        detector = CaptionDetector()
        text_blocks = [
            ("Chart 3: Sales Trends", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        assert captions[0].caption_type == "chart"
        assert captions[0].number == "3"

    def test_no_caption_in_regular_text(self):
        """Test that regular text is not detected as caption."""
        detector = CaptionDetector()
        text_blocks = [
            ("This is a regular paragraph", BoundingBox(100, 100, 200, 20)),
            ("Another line of text", BoundingBox(100, 130, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 0

    def test_caption_without_number(self):
        """Test caption detection without explicit numbering."""
        detector = CaptionDetector()
        text_blocks = [
            ("Table: Sample Data", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        assert captions[0].caption_type == "table"
        assert captions[0].number is None

    def test_caption_confidence_with_number(self):
        """Test confidence calculation for caption with number."""
        detector = CaptionDetector()
        text_blocks = [
            ("Table 1: Data", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        # Should have high confidence (keyword + number + short + single line)
        assert captions[0].confidence >= 0.8

    def test_caption_confidence_without_number(self):
        """Test confidence calculation for caption without number."""
        detector = CaptionDetector()
        text_blocks = [
            ("Table: Sample Data", BoundingBox(100, 100, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 1
        # Lower confidence without number
        assert 0.5 <= captions[0].confidence < 0.8

    def test_case_insensitive_detection(self):
        """Test case-insensitive caption detection."""
        detector = CaptionDetector()
        text_blocks = [
            ("TABLE 1: Data", BoundingBox(100, 100, 200, 20)),
            ("figure 2: Image", BoundingBox(100, 130, 200, 20)),
        ]

        captions = detector.detect_captions(text_blocks)

        assert len(captions) == 2
        assert captions[0].caption_type == "table"
        assert captions[1].caption_type == "figure"


class TestCaptionLinking:
    """Test caption-to-element linking."""

    def test_link_caption_above_element(self):
        """Test linking caption positioned above element."""
        detector = CaptionDetector()

        caption = Caption(
            text="Table 1: Data",
            bbox=BoundingBox(100, 100, 200, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        element_bbox = BoundingBox(100, 140, 200, 160)

        links = detector.link_captions([caption], [element_bbox])

        assert len(links) == 1
        assert links[0].caption == caption
        assert links[0].element_bbox == element_bbox
        assert links[0].distance == 20  # 140 - 120
        assert links[0].confidence >= 0.6

    def test_link_caption_below_element(self):
        """Test linking caption positioned below element."""
        detector = CaptionDetector()

        element_bbox = BoundingBox(100, 100, 200, 100)

        caption = Caption(
            text="Figure 1: Diagram",
            bbox=BoundingBox(100, 220, 200, 20),
            caption_type="figure",
            number="1",
            confidence=0.9,
        )

        links = detector.link_captions([caption], [element_bbox])

        assert len(links) == 1
        assert links[0].distance == 20  # 220 - 200

    def test_link_with_high_overlap(self):
        """Test linking with high horizontal overlap."""
        detector = CaptionDetector()

        caption = Caption(
            text="Table 1: Data",
            bbox=BoundingBox(100, 100, 200, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        # Element directly below with same horizontal position
        element_bbox = BoundingBox(100, 140, 200, 160)

        links = detector.link_captions([caption], [element_bbox])

        assert len(links) == 1
        assert links[0].overlap >= 0.7  # High overlap

    def test_no_link_with_low_overlap(self):
        """Test that captions with low overlap are not linked."""
        detector = CaptionDetector()

        caption = Caption(
            text="Table 1: Data",
            bbox=BoundingBox(100, 100, 100, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        # Element far to the right (low overlap)
        element_bbox = BoundingBox(400, 140, 100, 160)

        links = detector.link_captions([caption], [element_bbox])

        assert len(links) == 0  # No link due to low overlap

    def test_no_link_when_too_far(self):
        """Test that distant elements are not linked."""
        detector = CaptionDetector(max_distance=50.0)

        caption = Caption(
            text="Table 1: Data",
            bbox=BoundingBox(100, 100, 200, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        # Element too far below (>50 pixels)
        element_bbox = BoundingBox(100, 200, 200, 100)

        links = detector.link_captions([caption], [element_bbox])

        assert len(links) == 0

    def test_link_closest_element(self):
        """Test that caption links to closest matching element."""
        detector = CaptionDetector()

        caption = Caption(
            text="Table 1: Data",
            bbox=BoundingBox(100, 100, 200, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        # Two elements at different distances
        element1 = BoundingBox(100, 140, 200, 60)  # Closer
        element2 = BoundingBox(100, 250, 200, 100)  # Farther

        links = detector.link_captions([caption], [element1, element2])

        assert len(links) == 1
        assert links[0].element_bbox == element1  # Links to closer element

    def test_multiple_captions_multiple_elements(self):
        """Test linking multiple captions to multiple elements."""
        detector = CaptionDetector()

        caption1 = Caption(
            text="Table 1: First",
            bbox=BoundingBox(100, 100, 200, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        caption2 = Caption(
            text="Table 2: Second",
            bbox=BoundingBox(100, 350, 200, 20),
            caption_type="table",
            number="2",
            confidence=0.9,
        )

        element1 = BoundingBox(100, 140, 200, 160)
        element2 = BoundingBox(100, 390, 200, 110)

        links = detector.link_captions([caption1, caption2], [element1, element2])

        assert len(links) == 2
        # Check that each caption links to its corresponding element
        caption1_link = next(l for l in links if l.caption == caption1)
        caption2_link = next(l for l in links if l.caption == caption2)
        assert caption1_link.element_bbox == element1
        assert caption2_link.element_bbox == element2

    def test_custom_thresholds(self):
        """Test custom distance and overlap thresholds."""
        detector = CaptionDetector(max_distance=30.0, min_overlap=0.8)

        caption = Caption(
            text="Table 1: Data",
            bbox=BoundingBox(100, 100, 200, 20),
            caption_type="table",
            number="1",
            confidence=0.9,
        )

        # Element at 40 pixels distance (>30)
        element = BoundingBox(100, 160, 200, 140)

        links = detector.link_captions([caption], [element])

        assert len(links) == 0  # No link due to custom threshold


class TestHelperMethods:
    """Test helper methods."""

    def test_vertical_distance_gap_below(self):
        """Test vertical distance when there's a gap below."""
        detector = CaptionDetector()

        bbox1 = BoundingBox(100, 100, 200, 20)  # y from 100 to 120
        bbox2 = BoundingBox(100, 150, 200, 50)  # y from 150 to 200

        distance = detector._vertical_distance(bbox1, bbox2)

        assert distance == 30  # 150 - 120

    def test_vertical_distance_gap_above(self):
        """Test vertical distance when there's a gap above."""
        detector = CaptionDetector()

        bbox1 = BoundingBox(100, 150, 200, 50)  # y from 150 to 200
        bbox2 = BoundingBox(100, 100, 200, 20)  # y from 100 to 120

        distance = detector._vertical_distance(bbox1, bbox2)

        assert distance == 30  # 150 - 120

    def test_vertical_distance_overlapping(self):
        """Test vertical distance when boxes overlap."""
        detector = CaptionDetector()

        bbox1 = BoundingBox(100, 100, 200, 50)  # y from 100 to 150
        bbox2 = BoundingBox(100, 130, 200, 70)  # y from 130 to 200

        distance = detector._vertical_distance(bbox1, bbox2)

        assert distance == 0  # Overlapping

    def test_horizontal_overlap_full(self):
        """Test horizontal overlap when fully aligned."""
        detector = CaptionDetector()

        bbox1 = BoundingBox(100, 100, 200, 20)  # x from 100 to 300
        bbox2 = BoundingBox(100, 150, 200, 50)  # x from 100 to 300

        overlap = detector._horizontal_overlap(bbox1, bbox2)

        assert overlap == 1.0  # Perfect overlap

    def test_horizontal_overlap_partial(self):
        """Test horizontal overlap when partially aligned."""
        detector = CaptionDetector()

        bbox1 = BoundingBox(100, 100, 100, 20)  # x from 100 to 200
        bbox2 = BoundingBox(150, 150, 100, 50)  # x from 150 to 250

        overlap = detector._horizontal_overlap(bbox1, bbox2)

        # Overlap width: 50 (200 - 150)
        # Average width: 100 ((100 + 100) / 2)
        assert overlap == 0.5

    def test_horizontal_overlap_none(self):
        """Test horizontal overlap when not aligned."""
        detector = CaptionDetector()

        bbox1 = BoundingBox(100, 100, 100, 20)  # x from 100 to 200
        bbox2 = BoundingBox(300, 150, 100, 50)  # x from 300 to 400

        overlap = detector._horizontal_overlap(bbox1, bbox2)

        assert overlap == 0.0  # No overlap

    def test_extract_number_simple(self):
        """Test extracting simple number."""
        detector = CaptionDetector()

        number = detector._extract_number("Table 1: Data")

        assert number == "1"

    def test_extract_number_decimal(self):
        """Test extracting decimal number."""
        detector = CaptionDetector()

        number = detector._extract_number("Figure 2.3: Diagram")

        assert number == "2.3"

    def test_extract_number_none(self):
        """Test extracting number when none present."""
        detector = CaptionDetector()

        number = detector._extract_number("Table: Data")

        assert number is None

    def test_get_caption_type_table(self):
        """Test identifying table caption type."""
        detector = CaptionDetector()

        caption_type = detector._get_caption_type("Table 1: Sample Data")

        assert caption_type == "table"

    def test_get_caption_type_figure(self):
        """Test identifying figure caption type."""
        detector = CaptionDetector()

        caption_type = detector._get_caption_type("Figure 2: Sample Image")

        assert caption_type == "figure"

    def test_get_caption_type_none(self):
        """Test identifying no caption type."""
        detector = CaptionDetector()

        caption_type = detector._get_caption_type("Regular text")

        assert caption_type is None
