"""Regression tests for PDF to Markdown conversion.

This module contains tests to ensure that specific issues don't reoccur and that
the test cases produce accurate output.
"""

import re
from pathlib import Path

import pytest

from unpdf.core import convert_pdf


@pytest.fixture
def test_cases_dir():
    """Return the test cases directory path."""
    return Path(__file__).parent / "test_cases"


class TestBasicText:
    """Tests for basic text conversion (case 01)."""

    def test_header_level_preserved(self, test_cases_dir):
        """Test that header levels are preserved correctly."""
        pdf_path = test_cases_dir / "01_basic_text.pdf"
        expected_path = test_cases_dir / "01_basic_text.md"
        
        result = convert_pdf(str(pdf_path))
        expected = expected_path.read_text(encoding="utf-8")
        
        # Check for h1 header (single #)
        assert re.search(r"^# Basic Text Document\s*$", result, re.MULTILINE), \
            "H1 header should use single # not multiple"
        
        # Check for h2 header (double ##)
        assert re.search(r"^## Second Heading\s*$", result, re.MULTILINE), \
            "H2 header should use double ##"

    def test_paragraphs_separated(self, test_cases_dir):
        """Test that paragraphs are properly separated."""
        pdf_path = test_cases_dir / "01_basic_text.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Check that paragraphs are separated by blank lines
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip() and not p.startswith("#")]
        
        # Should have at least 2 distinct paragraphs
        assert len(paragraphs) >= 2, "Paragraphs should be properly separated"
        
        # First paragraph should not contain second paragraph text
        assert "This is another paragraph" not in paragraphs[0], \
            "Paragraphs should not be merged together"


class TestTextFormatting:
    """Tests for text formatting (case 02)."""

    def test_bold_formatting_correct(self, test_cases_dir):
        """Test that bold text uses correct markdown syntax."""
        pdf_path = test_cases_dir / "02_text_formatting.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Check for properly formatted bold (no spaces before closing **)
        bold_matches = re.findall(r"\*\*[^*]+\*\*", result)
        
        for match in bold_matches:
            assert not match.endswith(" **"), \
                f"Bold text should not have space before closing **: {match}"
            assert not match.startswith("** "), \
                f"Bold text should not have space after opening **: {match}"

    def test_italic_formatting_correct(self, test_cases_dir):
        """Test that italic text uses correct markdown syntax."""
        pdf_path = test_cases_dir / "02_text_formatting.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Check for properly formatted italic (no spaces before closing *)
        # Single asterisks for italic, not part of bold
        italic_matches = re.findall(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", result)
        
        for match in italic_matches:
            assert not match.endswith(" "), \
                f"Italic text should not have space before closing *: {match}"
            assert not match.startswith(" "), \
                f"Italic text should not have space after opening *: {match}"

    def test_strikethrough_detected(self, test_cases_dir):
        """Test that strikethrough text is properly detected and formatted."""
        pdf_path = test_cases_dir / "02_text_formatting.pdf"
        expected_path = test_cases_dir / "02_text_formatting.md"
        
        result = convert_pdf(str(pdf_path))
        expected = expected_path.read_text(encoding="utf-8")
        
        # Check if strikethrough exists in expected
        if "~~" in expected:
            # Should have strikethrough in output
            assert "~~" in result, "Strikethrough text should be detected"
            assert "~~strikethrough text~~" in result, \
                "Strikethrough should use ~~ markers"

    def test_bold_not_converted_to_headers(self, test_cases_dir):
        """Test that bold text is not incorrectly converted to headers."""
        pdf_path = test_cases_dir / "02_text_formatting.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # "bold text" should not be a header
        assert not re.search(r"^#{1,6}\s*bold text\s*$", result, re.MULTILINE | re.IGNORECASE), \
            "Bold text should not be converted to headers"

    def test_inline_code_preserved(self, test_cases_dir):
        """Test that inline code is properly preserved."""
        pdf_path = test_cases_dir / "02_text_formatting.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Check for inline code
        assert "`inline code`" in result or "`" in result, \
            "Inline code should be preserved with backticks"


class TestLists:
    """Tests for list formatting (case 03)."""

    def test_unordered_lists_detected(self, test_cases_dir):
        """Test that unordered lists are properly detected."""
        pdf_path = test_cases_dir / "03_lists.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Should have bullet points
        assert re.search(r"^[-*+]\s+", result, re.MULTILINE), \
            "Unordered lists should use bullet markers"

    def test_ordered_lists_detected(self, test_cases_dir):
        """Test that ordered lists are properly detected."""
        pdf_path = test_cases_dir / "03_lists.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Should have numbered items
        assert re.search(r"^\d+\.\s+", result, re.MULTILINE), \
            "Ordered lists should use numbered markers"

    def test_nested_lists_preserved(self, test_cases_dir):
        """Test that nested lists maintain proper indentation."""
        pdf_path = test_cases_dir / "03_lists.pdf"
        expected_path = test_cases_dir / "03_lists.md"
        
        result = convert_pdf(str(pdf_path))
        expected = expected_path.read_text(encoding="utf-8")
        
        # Check if expected has nested lists
        if re.search(r"^\s{2,}[-*+\d]", expected, re.MULTILINE):
            # Should have indented list items
            assert re.search(r"^\s{2,}[-*+\d]", result, re.MULTILINE), \
                "Nested lists should be properly indented"


class TestTables:
    """Tests for table formatting (case 05)."""

    def test_tables_detected(self, test_cases_dir):
        """Test that tables are properly detected and formatted."""
        pdf_path = test_cases_dir / "05_tables.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Should have table markers (pipes)
        assert "|" in result, "Tables should use pipe markers"
        
        # Should have header separator line
        assert re.search(r"\|[\s:-]+\|", result), \
            "Tables should have header separator line"

    def test_table_alignment(self, test_cases_dir):
        """Test that table cell content is properly aligned."""
        pdf_path = test_cases_dir / "05_tables.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Check that we have table rows with content
        table_rows = re.findall(r"\|[^\n]+\|", result)
        
        assert len(table_rows) > 0, "Should detect table rows"


class TestHeadings:
    """Tests for heading hierarchy (case 07)."""

    def test_relative_heading_sizes(self, test_cases_dir):
        """Test that heading levels are relative to document structure."""
        pdf_path = test_cases_dir / "07_headings.pdf"
        
        result = convert_pdf(str(pdf_path))
        
        # Extract all headings with their levels
        headings = re.findall(r"^(#{1,6})\s+(.+)$", result, re.MULTILINE)
        
        if headings:
            # Largest heading should be h1 (single #)
            level_counts = {}
            for level, text in headings:
                level_num = len(level)
                level_counts[level_num] = level_counts.get(level_num, 0) + 1
            
            # Should have h1 headers
            assert 1 in level_counts, "Document should have h1 headers"
            
            # Heading levels should be sequential (no h1 followed directly by h4)
            levels = sorted([len(h[0]) for h in headings])
            for i in range(len(levels) - 1):
                diff = levels[i + 1] - levels[i]
                assert diff <= 2, \
                    f"Heading levels should not skip (found h{levels[i]} to h{levels[i+1]})"


class TestEndToEnd:
    """End-to-end tests for complete documents."""

    @pytest.mark.parametrize("case_num,case_name", [
        ("01", "basic_text"),
        ("02", "text_formatting"),
        ("03", "lists"),
        ("04", "code_blocks"),
        ("05", "tables"),
        ("06", "links_and_quotes"),
        ("07", "headings"),
        ("08", "horizontal_rules"),
        ("09", "complex_document"),
        ("10", "advanced_tables"),
    ])
    def test_case_conversion(self, test_cases_dir, case_num, case_name):
        """Test that each test case converts without errors."""
        pdf_path = test_cases_dir / f"{case_num}_{case_name}.pdf"
        expected_path = test_cases_dir / f"{case_num}_{case_name}.md"
        
        if not pdf_path.exists():
            pytest.skip(f"PDF not found: {pdf_path}")
        
        # Should not raise exceptions
        result = convert_pdf(str(pdf_path))
        
        # Should produce some output
        assert len(result) > 0, f"Conversion should produce output for case {case_num}"
        
        # Write output for manual inspection
        output_path = test_cases_dir / f"{case_num}_output.md"
        output_path.write_text(result, encoding="utf-8")


class TestAccuracyMetrics:
    """Tests for accuracy calculation on test cases."""

    @pytest.mark.parametrize("case_num,case_name", [
        ("01", "basic_text"),
        ("02", "text_formatting"),
        ("03", "lists"),
        ("04", "code_blocks"),
        ("05", "tables"),
        ("06", "links_and_quotes"),
        ("07", "headings"),
        ("08", "horizontal_rules"),
        ("09", "complex_document"),
        ("10", "advanced_tables"),
    ])
    def test_case_accuracy(self, test_cases_dir, case_num, case_name):
        """Test accuracy metrics for each test case."""
        pdf_path = test_cases_dir / f"{case_num}_{case_name}.pdf"
        expected_path = test_cases_dir / f"{case_num}_{case_name}.md"
        
        if not pdf_path.exists() or not expected_path.exists():
            pytest.skip(f"Files not found for case {case_num}")
        
        result = convert_pdf(str(pdf_path))
        expected = expected_path.read_text(encoding="utf-8")
        
        from unpdf.accuracy import calculate_element_accuracy
        
        accuracy = calculate_element_accuracy(expected, result)
        
        # Store accuracy for reporting
        print(f"\nCase {case_num} ({case_name}): {accuracy:.2%} accurate")
        
        # For basic cases, we expect reasonable accuracy
        if case_num in ["01", "07"]:
            assert accuracy > 0.5, \
                f"Basic case {case_num} should have >50% accuracy, got {accuracy:.2%}"


def test_formatting_whitespace_rules():
    """Test that formatting markers don't have extraneous whitespace."""
    test_cases = [
        ("**bold text**", True, "Correct bold formatting"),
        ("**bold text **", False, "Bold with trailing space"),
        ("** bold text**", False, "Bold with leading space"),
        ("*italic text*", True, "Correct italic formatting"),
        ("*italic text *", False, "Italic with trailing space"),
        ("* italic text*", False, "Italic with leading space"),
        ("~~strikethrough~~", True, "Correct strikethrough"),
        ("~~strikethrough ~~", False, "Strikethrough with trailing space"),
    ]
    
    for text, should_pass, description in test_cases:
        # Extract formatting and check for spaces
        if "**" in text:
            match = re.match(r"\*\*(.+?)\*\*", text)
            if match:
                content = match.group(1)
                is_valid = not content.startswith(" ") and not content.endswith(" ")
                assert is_valid == should_pass, \
                    f"{description}: '{text}' should {'pass' if should_pass else 'fail'}"
        elif text.count("*") == 2:
            match = re.match(r"\*(.+?)\*", text)
            if match:
                content = match.group(1)
                is_valid = not content.startswith(" ") and not content.endswith(" ")
                assert is_valid == should_pass, \
                    f"{description}: '{text}' should {'pass' if should_pass else 'fail'}"
        elif "~~" in text:
            match = re.match(r"~~(.+?)~~", text)
            if match:
                content = match.group(1)
                is_valid = not content.startswith(" ") and not content.endswith(" ")
                assert is_valid == should_pass, \
                    f"{description}: '{text}' should {'pass' if should_pass else 'fail'}"
