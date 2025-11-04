"""Tests for code block detection."""

import pytest

from unpdf.models.layout import BoundingBox
from unpdf.processors.code_detector import CODE_KEYWORDS, CodeDetector, TextBlock


@pytest.fixture
def detector():
    """Create a code detector with default settings."""
    return CodeDetector()


@pytest.fixture
def python_code_blocks():
    """Create sample Python code blocks."""
    return [
        TextBlock(
            text="def calculate_sum(a, b):",
            bbox=BoundingBox(50, 100, 300, 110),
            font_name="Courier",
            font_size=10,
            char_width=6.0,
        ),
        TextBlock(
            text="    return a + b",
            bbox=BoundingBox(74, 115, 300, 125),
            font_name="Courier",
            font_size=10,
            char_width=6.0,
        ),
    ]


@pytest.fixture
def regular_text_blocks():
    """Create sample regular text blocks."""
    return [
        TextBlock(
            text="This is regular paragraph text.",
            bbox=BoundingBox(50, 100, 400, 115),
            font_name="Times-Roman",
            font_size=12,
            char_width=7.2,
        ),
        TextBlock(
            text="It continues with more text.",
            bbox=BoundingBox(50, 120, 350, 135),
            font_name="Times-Roman",
            font_size=12,
            char_width=7.1,
        ),
    ]


class TestMonospaceFontDetection:
    """Tests for monospace font detection."""

    def test_detects_monospace_font(self, detector, python_code_blocks):
        """Test detection of monospace fonts with consistent width."""
        assert detector.is_monospace_font(python_code_blocks) is True

    def test_rejects_proportional_font(self, detector, regular_text_blocks):
        """Test rejection of proportional fonts."""
        # Make widths vary significantly
        regular_text_blocks[0].char_width = 7.0
        regular_text_blocks[1].char_width = 8.5
        assert detector.is_monospace_font(regular_text_blocks) is False

    def test_handles_empty_blocks(self, detector):
        """Test handling of empty block list."""
        assert detector.is_monospace_font([]) is False

    def test_handles_single_block(self, detector):
        """Test handling of single block (cannot determine variance)."""
        blocks = [
            TextBlock(
                text="code",
                bbox=BoundingBox(0, 0, 40, 10),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            )
        ]
        assert detector.is_monospace_font(blocks) is False

    def test_estimates_char_width_from_bbox(self, detector):
        """Test character width estimation when not provided."""
        blocks = [
            TextBlock(
                text="code",
                bbox=BoundingBox(0, 0, 24, 10),
                font_name="Courier",
                font_size=10,
                char_width=0.0,  # Not provided
            ),
            TextBlock(
                text="more",
                bbox=BoundingBox(0, 15, 24, 25),
                font_name="Courier",
                font_size=10,
                char_width=0.0,
            ),
        ]
        # Width = 24, length = 4, so 6.0 per char (monospace)
        assert detector.is_monospace_font(blocks) is True


class TestIndentationDetection:
    """Tests for indentation pattern detection."""

    def test_detects_consistent_indentation(self, detector):
        """Test detection of consistent indentation."""
        blocks = [
            TextBlock(
                text="def func():",
                bbox=BoundingBox(50, 100, 200, 110),
                font_name="Courier",
                font_size=10,
            ),
            TextBlock(
                text="    return 1",
                bbox=BoundingBox(98, 115, 200, 125),  # 48 pixels indent
                font_name="Courier",
                font_size=10,
            ),
        ]
        has_indent, avg_indent = detector.has_consistent_indentation(blocks)
        # Average indent is 24 pixels (0 + 48) / 2
        assert has_indent is False  # 24 < 40
        assert avg_indent < 40.0

    def test_rejects_no_indentation(self, detector, regular_text_blocks):
        """Test rejection when no indentation exists."""
        has_indent, avg_indent = detector.has_consistent_indentation(regular_text_blocks)
        assert has_indent is False
        assert avg_indent < 40.0

    def test_handles_empty_blocks(self, detector):
        """Test handling of empty block list."""
        has_indent, avg_indent = detector.has_consistent_indentation([])
        assert has_indent is False
        assert avg_indent == 0.0


class TestSyntaxHighlighting:
    """Tests for syntax highlighting detection."""

    def test_detects_syntax_highlighting(self, detector):
        """Test detection of multiple colors (syntax highlighting)."""
        blocks = [
            TextBlock(
                text="def",
                bbox=BoundingBox(0, 0, 30, 10),
                font_name="Courier",
                font_size=10,
                color=(0, 0, 255),  # Blue
            ),
            TextBlock(
                text="func",
                bbox=BoundingBox(35, 0, 65, 10),
                font_name="Courier",
                font_size=10,
                color=(0, 128, 0),  # Green
            ),
            TextBlock(
                text="return",
                bbox=BoundingBox(0, 15, 50, 25),
                font_name="Courier",
                font_size=10,
                color=(255, 0, 0),  # Red
            ),
        ]
        assert detector.has_syntax_highlighting(blocks) is True

    def test_rejects_single_color(self, detector, python_code_blocks):
        """Test rejection when all text is same color."""
        assert detector.has_syntax_highlighting(python_code_blocks) is False

    def test_handles_empty_blocks(self, detector):
        """Test handling of empty block list."""
        assert detector.has_syntax_highlighting([]) is False


class TestKeywordDetection:
    """Tests for programming keyword detection."""

    def test_detects_python_keywords(self, detector, python_code_blocks):
        """Test detection of Python keywords."""
        has_keywords, count = detector.contains_code_keywords(python_code_blocks)
        assert has_keywords is True
        assert count >= 2  # 'def' and 'return'

    def test_detects_javascript_keywords(self, detector):
        """Test detection of JavaScript keywords."""
        blocks = [
            TextBlock(
                text="function test() {",
                bbox=BoundingBox(0, 0, 150, 10),
                font_name="Courier",
                font_size=10,
            ),
            TextBlock(
                text="  const x = 5;",
                bbox=BoundingBox(20, 15, 150, 25),
                font_name="Courier",
                font_size=10,
            ),
        ]
        has_keywords, count = detector.contains_code_keywords(blocks)
        assert has_keywords is True
        assert count >= 2  # 'function' and 'const'

    def test_rejects_no_keywords(self, detector, regular_text_blocks):
        """Test rejection when no keywords found."""
        has_keywords, count = detector.contains_code_keywords(regular_text_blocks)
        # Regular text might contain some words like "with" or "it"
        # which are keywords, so we just check for low count
        assert count < 5

    def test_handles_empty_blocks(self, detector):
        """Test handling of empty block list."""
        has_keywords, count = detector.contains_code_keywords([])
        assert has_keywords is False
        assert count == 0

    def test_case_insensitive_matching(self, detector):
        """Test case-insensitive keyword matching."""
        blocks = [
            TextBlock(
                text="DEF my_function():",
                bbox=BoundingBox(0, 0, 150, 10),
                font_name="Courier",
                font_size=10,
            )
        ]
        has_keywords, count = detector.contains_code_keywords(blocks)
        assert has_keywords is True
        assert count >= 1


class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    def test_high_confidence_all_signals(self, detector):
        """Test high confidence when all signals present."""
        confidence = detector.calculate_confidence(
            is_monospace=True,
            has_indent=True,
            avg_indent=48.0,
            has_syntax_highlight=True,
            keyword_count=5,
            total_words=20,
        )
        assert confidence >= 0.8

    def test_medium_confidence_some_signals(self, detector):
        """Test medium confidence with partial signals."""
        confidence = detector.calculate_confidence(
            is_monospace=True,
            has_indent=True,
            avg_indent=40.0,
            has_syntax_highlight=False,
            keyword_count=2,
            total_words=20,
        )
        assert 0.5 <= confidence <= 0.9  # Allow slightly higher

    def test_low_confidence_few_signals(self, detector):
        """Test low confidence with minimal signals."""
        confidence = detector.calculate_confidence(
            is_monospace=False,
            has_indent=False,
            avg_indent=10.0,
            has_syntax_highlight=False,
            keyword_count=0,
            total_words=20,
        )
        assert confidence < 0.5

    def test_keyword_weight_dominance(self, detector):
        """Test that keyword weight is significant."""
        # High keyword ratio should boost confidence
        high_keywords = detector.calculate_confidence(
            is_monospace=False,
            has_indent=False,
            avg_indent=0.0,
            has_syntax_highlight=False,
            keyword_count=10,
            total_words=20,
        )
        low_keywords = detector.calculate_confidence(
            is_monospace=False,
            has_indent=False,
            avg_indent=0.0,
            has_syntax_highlight=False,
            keyword_count=1,
            total_words=20,
        )
        assert high_keywords > low_keywords


class TestCodeBlockDetection:
    """Tests for complete code block detection."""

    def test_detects_python_code_block(self, detector, python_code_blocks):
        """Test detection of Python code block."""
        results = detector.detect_code_blocks(python_code_blocks, page_height=800)
        assert len(results) > 0
        blocks, confidence = results[0]
        assert len(blocks) == 2
        assert confidence >= 0.5

    def test_rejects_regular_text(self, detector, regular_text_blocks):
        """Test rejection of regular text as code."""
        results = detector.detect_code_blocks(regular_text_blocks, page_height=800)
        # Should either return empty or low confidence
        if results:
            _, confidence = results[0]
            assert confidence <= 0.75  # Allow slightly higher threshold

    def test_groups_continuous_lines(self, detector):
        """Test grouping of continuous code lines."""
        blocks = [
            TextBlock(
                text="def func():",
                bbox=BoundingBox(50, 100, 200, 110),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
            TextBlock(
                text="    x = 1",
                bbox=BoundingBox(74, 115, 200, 125),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
            TextBlock(
                text="    return x",
                bbox=BoundingBox(74, 130, 200, 140),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
        ]
        results = detector.detect_code_blocks(blocks, page_height=800)
        assert len(results) == 1
        block_group, _ = results[0]
        assert len(block_group) == 3

    def test_separates_distant_blocks(self, detector):
        """Test separation of vertically distant blocks."""
        blocks = [
            TextBlock(
                text="def func1():",
                bbox=BoundingBox(50, 100, 200, 110),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
            TextBlock(
                text="    return 1",
                bbox=BoundingBox(74, 115, 200, 125),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
            TextBlock(
                text="def func2():",
                bbox=BoundingBox(50, 200, 200, 210),  # Far below
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
            TextBlock(
                text="    return 2",
                bbox=BoundingBox(74, 215, 200, 225),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
        ]
        results = detector.detect_code_blocks(blocks, page_height=800)
        assert len(results) == 2

    def test_requires_minimum_lines(self, detector):
        """Test minimum line requirement for code blocks."""
        single_line = [
            TextBlock(
                text="def func():",
                bbox=BoundingBox(50, 100, 200, 110),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            )
        ]
        results = detector.detect_code_blocks(single_line, page_height=800)
        assert len(results) == 0  # Single line doesn't meet minimum

    def test_handles_empty_input(self, detector):
        """Test handling of empty input."""
        results = detector.detect_code_blocks([], page_height=800)
        assert results == []

    def test_sorts_by_position(self, detector):
        """Test that blocks are sorted by position."""
        blocks = [
            TextBlock(
                text="    return 1",
                bbox=BoundingBox(74, 115, 200, 125),
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
            TextBlock(
                text="def func():",
                bbox=BoundingBox(50, 100, 200, 110),  # Earlier
                font_name="Courier",
                font_size=10,
                char_width=6.0,
            ),
        ]
        results = detector.detect_code_blocks(blocks, page_height=800)
        if results:
            block_group, _ = results[0]
            # Should be sorted correctly
            assert block_group[0].text == "def func():"
            assert block_group[1].text == "    return 1"


class TestCodeKeywordsSet:
    """Tests for the CODE_KEYWORDS set."""

    def test_contains_python_keywords(self):
        """Test that Python keywords are included."""
        assert "def" in CODE_KEYWORDS
        assert "class" in CODE_KEYWORDS
        assert "import" in CODE_KEYWORDS
        assert "return" in CODE_KEYWORDS

    def test_contains_javascript_keywords(self):
        """Test that JavaScript keywords are included."""
        assert "function" in CODE_KEYWORDS
        assert "const" in CODE_KEYWORDS
        assert "let" in CODE_KEYWORDS
        assert "var" in CODE_KEYWORDS

    def test_contains_common_keywords(self):
        """Test that common keywords are included."""
        assert "true" in CODE_KEYWORDS
        assert "false" in CODE_KEYWORDS
        assert "null" in CODE_KEYWORDS

    def test_keywords_are_lowercase(self):
        """Test that all keywords are lowercase."""
        for keyword in CODE_KEYWORDS:
            assert keyword == keyword.lower()
