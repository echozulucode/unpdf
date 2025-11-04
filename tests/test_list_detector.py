"""Tests for list_detector module."""

import pytest

from unpdf.models.layout import BoundingBox
from unpdf.processors.list_detector import ListDetector, ListItem, TextBlock


@pytest.fixture
def detector():
    """Create list detector with default parameters."""
    return ListDetector()


@pytest.fixture
def sample_blocks():
    """Create sample text blocks for testing."""
    return [
        TextBlock("• First item", BoundingBox(10, 100, 200, 110), 12, "Arial"),
        TextBlock("• Second item", BoundingBox(10, 115, 200, 125), 12, "Arial"),
        TextBlock("• Third item", BoundingBox(10, 130, 200, 140), 12, "Arial"),
    ]


class TestBulletDetection:
    """Tests for bullet list detection."""

    def test_basic_bullet_detection(self, detector):
        """Test detection of simple bullet list."""
        block = TextBlock("• Item text", BoundingBox(10, 100, 200, 110), 12, "Arial")
        result = detector._detect_bullet(block, 0)

        assert result is not None
        assert result.text == "Item text"
        assert result.item_type == "bullet"
        assert result.marker == "•"
        assert result.confidence == 1.0

    def test_various_bullet_chars(self, detector):
        """Test detection of different bullet characters."""
        bullet_chars = ["•", "●", "○", "◦", "■", "□", "◆", "◇", "-", "–", "—", "✓"]

        for char in bullet_chars:
            block = TextBlock(
                f"{char} Item", BoundingBox(10, 100, 200, 110), 12, "Arial"
            )
            result = detector._detect_bullet(block, 0)

            assert result is not None
            assert result.marker == char
            assert result.item_type == "bullet"

    def test_bullet_with_leading_whitespace(self, detector):
        """Test bullet detection with leading spaces."""
        block = TextBlock(
            "  • Indented item", BoundingBox(20, 100, 200, 110), 12, "Arial"
        )
        result = detector._detect_bullet(block, 0)

        assert result is not None
        assert result.text == "Indented item"

    def test_no_bullet_without_whitespace(self, detector):
        """Test that bullet without whitespace is not detected."""
        block = TextBlock("•NoSpace", BoundingBox(10, 100, 200, 110), 12, "Arial")
        result = detector._detect_bullet(block, 0)

        assert result is None

    def test_no_bullet_empty_content(self, detector):
        """Test that bullet without content is not detected."""
        block = TextBlock("• ", BoundingBox(10, 100, 200, 110), 12, "Arial")
        result = detector._detect_bullet(block, 0)

        assert result is None


class TestNumberedDetection:
    """Tests for numbered list detection."""

    def test_arabic_numbered_list(self, detector):
        """Test detection of arabic numbered list."""
        block = TextBlock("1. First item", BoundingBox(10, 100, 200, 110), 12, "Arial")
        result = detector._detect_numbered(block, 0)

        assert result is not None
        assert result.text == "First item"
        assert result.item_type == "numbered"
        assert result.marker == "1"
        assert result.confidence == 0.9

    def test_numbered_with_parenthesis(self, detector):
        """Test numbered list with different punctuation."""
        test_cases = ["1. Item", "1) Item", "1: Item"]

        for text in test_cases:
            block = TextBlock(text, BoundingBox(10, 100, 200, 110), 12, "Arial")
            result = detector._detect_numbered(block, 0)

            assert result is not None
            assert result.text == "Item"

    def test_lowercase_lettered_list(self, detector):
        """Test detection of lowercase lettered list."""
        block = TextBlock("a. First item", BoundingBox(10, 100, 200, 110), 12, "Arial")
        result = detector._detect_numbered(block, 0)

        assert result is not None
        assert result.item_type == "lettered"
        assert result.marker == "a"

    def test_uppercase_lettered_list(self, detector):
        """Test detection of uppercase lettered list."""
        block = TextBlock("A. First item", BoundingBox(10, 100, 200, 110), 12, "Arial")
        result = detector._detect_numbered(block, 0)

        assert result is not None
        assert result.item_type == "lettered"
        assert result.marker == "A"

    def test_roman_numeral_list(self, detector):
        """Test detection of roman numeral list."""
        numerals = ["i", "ii", "iii", "iv", "v"]

        for numeral in numerals:
            block = TextBlock(
                f"{numeral}. Item", BoundingBox(10, 100, 200, 110), 12, "Arial"
            )
            result = detector._detect_numbered(block, 0)

            assert result is not None
            assert result.item_type == "roman"
            assert result.marker.lower() == numeral


class TestLevelAssignment:
    """Tests for indentation level assignment."""

    def test_single_level_list(self, detector):
        """Test that single level list gets level 0."""
        items = [
            ListItem(
                "Item 1", 0, "bullet", "•", 1.0, BoundingBox(10, 100, 200, 110), 0
            ),
            ListItem(
                "Item 2", 0, "bullet", "•", 1.0, BoundingBox(10, 115, 200, 125), 1
            ),
            ListItem(
                "Item 3", 0, "bullet", "•", 1.0, BoundingBox(10, 130, 200, 140), 2
            ),
        ]

        result = detector._assign_levels(items)

        for item in result:
            assert item.level == 0

    def test_multi_level_list(self, detector):
        """Test multi-level list with different indents."""
        items = [
            ListItem(
                "L1 Item", 0, "bullet", "•", 1.0, BoundingBox(10, 100, 200, 110), 0
            ),
            ListItem(
                "L2 Item", 0, "bullet", "○", 1.0, BoundingBox(30, 115, 200, 125), 1
            ),
            ListItem(
                "L2 Item", 0, "bullet", "○", 1.0, BoundingBox(30, 130, 200, 140), 2
            ),
            ListItem(
                "L1 Item", 0, "bullet", "•", 1.0, BoundingBox(10, 145, 200, 155), 3
            ),
        ]

        result = detector._assign_levels(items)

        assert result[0].level == 0
        assert result[1].level == 1
        assert result[2].level == 1
        assert result[3].level == 0

    def test_three_level_list(self, detector):
        """Test three-level nested list."""
        items = [
            ListItem("L1", 0, "bullet", "•", 1.0, BoundingBox(10, 100, 200, 110), 0),
            ListItem("L2", 0, "bullet", "○", 1.0, BoundingBox(30, 115, 200, 125), 1),
            ListItem("L3", 0, "bullet", "■", 1.0, BoundingBox(50, 130, 200, 140), 2),
        ]

        result = detector._assign_levels(items)

        assert result[0].level == 0
        assert result[1].level == 1
        assert result[2].level == 2


class TestSequenceValidation:
    """Tests for numbering sequence validation."""

    def test_valid_arabic_sequence(self, detector):
        """Test validation of correct arabic sequence."""
        items = [
            ListItem("One", 0, "numbered", "1", 0.9, BoundingBox(10, 100, 200, 110), 0),
            ListItem("Two", 0, "numbered", "2", 0.9, BoundingBox(10, 115, 200, 125), 1),
            ListItem(
                "Three", 0, "numbered", "3", 0.9, BoundingBox(10, 130, 200, 140), 2
            ),
        ]

        result = detector._validate_sequences(items)

        for item in result:
            assert item.confidence >= 0.9

    def test_invalid_arabic_sequence(self, detector):
        """Test validation of incorrect arabic sequence."""
        items = [
            ListItem("One", 0, "numbered", "1", 0.9, BoundingBox(10, 100, 200, 110), 0),
            ListItem(
                "Three", 0, "numbered", "3", 0.9, BoundingBox(10, 115, 200, 125), 1
            ),
        ]

        result = detector._validate_sequences(items)

        assert result[0].confidence == 0.9
        assert result[1].confidence < 0.9  # Reduced due to gap

    def test_valid_letter_sequence(self, detector):
        """Test validation of correct letter sequence."""
        items = [
            ListItem("A", 0, "lettered", "a", 0.85, BoundingBox(10, 100, 200, 110), 0),
            ListItem("B", 0, "lettered", "b", 0.85, BoundingBox(10, 115, 200, 125), 1),
            ListItem("C", 0, "lettered", "c", 0.85, BoundingBox(10, 130, 200, 140), 2),
        ]

        result = detector._validate_sequences(items)

        for item in result:
            assert item.confidence >= 0.85

    def test_valid_roman_sequence(self, detector):
        """Test validation of correct roman numeral sequence."""
        items = [
            ListItem("I", 0, "roman", "i", 0.8, BoundingBox(10, 100, 200, 110), 0),
            ListItem("II", 0, "roman", "ii", 0.8, BoundingBox(10, 115, 200, 125), 1),
            ListItem("III", 0, "roman", "iii", 0.8, BoundingBox(10, 130, 200, 140), 2),
        ]

        result = detector._validate_sequences(items)

        for item in result:
            assert item.confidence >= 0.8


class TestFullDetection:
    """Tests for full list detection pipeline."""

    def test_detect_simple_bullet_list(self, detector, sample_blocks):
        """Test detection of complete bullet list."""
        result = detector.detect_lists(sample_blocks)

        assert len(result) == 3
        for item in result:
            assert item.item_type == "bullet"
            assert item.level == 0

    def test_detect_mixed_list(self, detector):
        """Test detection of mixed bullet and numbered list."""
        blocks = [
            TextBlock("1. First", BoundingBox(10, 100, 200, 110), 12, "Arial"),
            TextBlock("2. Second", BoundingBox(10, 115, 200, 125), 12, "Arial"),
            TextBlock("• Bullet", BoundingBox(10, 130, 200, 140), 12, "Arial"),
        ]

        result = detector.detect_lists(blocks)

        assert len(result) == 3
        assert result[0].item_type == "numbered"
        assert result[1].item_type == "numbered"
        assert result[2].item_type == "bullet"

    def test_detect_empty_blocks(self, detector):
        """Test detection with empty block list."""
        result = detector.detect_lists([])

        assert result == []

    def test_detect_no_lists(self, detector):
        """Test detection with blocks containing no lists."""
        blocks = [
            TextBlock("Regular text", BoundingBox(10, 100, 200, 110), 12, "Arial"),
            TextBlock("More text", BoundingBox(10, 115, 200, 125), 12, "Arial"),
        ]

        result = detector.detect_lists(blocks)

        assert len(result) == 0


class TestIndentClustering:
    """Tests for indent clustering logic."""

    def test_cluster_single_indent(self, detector):
        """Test clustering with single indent level."""
        x_coords = [10.0, 10.5, 11.0, 10.2]

        result = detector._cluster_indents(x_coords)

        assert len(result) == 1
        assert result[0][0] <= 10.0
        assert result[0][1] >= 11.0

    def test_cluster_multiple_indents(self, detector):
        """Test clustering with multiple indent levels."""
        x_coords = [10.0, 10.5, 30.0, 30.5, 50.0, 51.0]

        result = detector._cluster_indents(x_coords)

        assert len(result) == 3

    def test_cluster_empty(self, detector):
        """Test clustering with no coordinates."""
        result = detector._cluster_indents([])

        assert result == []
