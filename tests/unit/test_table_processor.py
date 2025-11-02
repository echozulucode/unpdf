"""Unit tests for table processor."""

import pytest

from unpdf.processors.table import TableElement, TableProcessor


def test_table_element_to_markdown():
    """Test basic table to Markdown conversion."""
    table = TableElement(
        rows=[["Name", "Age"], ["Alice", "30"], ["Bob", "25"]], has_header=True
    )

    result = table.to_markdown()

    assert "| Name" in result
    assert "| Age" in result
    assert "---" in result  # Separator line
    assert "| Alice" in result
    assert "| Bob" in result


def test_table_element_no_header():
    """Test table without header row."""
    table = TableElement(rows=[["A", "B"], ["C", "D"]], has_header=False)

    result = table.to_markdown()

    # Should not have separator line
    assert result.count("|") > 0
    assert "---" not in result


def test_table_element_empty():
    """Test empty table."""
    table = TableElement(rows=[], has_header=True)

    result = table.to_markdown()

    assert result == ""


def test_table_element_with_none_cells():
    """Test table with None values."""
    table = TableElement(rows=[["A", None], [None, "D"]], has_header=True)

    result = table.to_markdown()

    # None should be converted to empty string
    assert "| A" in result
    assert "| D" in result
    # Empty cells should be present (padded spaces)
    lines = result.split("\n")
    assert all("|" in line for line in lines)


def test_table_element_uneven_rows():
    """Test table with rows of different lengths."""
    table = TableElement(rows=[["A", "B", "C"], ["1", "2"], ["X"]], has_header=True)

    result = table.to_markdown()

    # Should normalize to 3 columns
    lines = result.split("\n")
    assert all(line.count("|") == 4 for line in lines)  # 4 pipes = 3 columns


def test_table_element_column_alignment():
    """Test column width calculation and alignment."""
    table = TableElement(
        rows=[["Short", "Very Long Text"], ["A", "B"]], has_header=True
    )

    result = table.to_markdown()

    # Long text should determine column width
    assert "Very Long Text" in result
    lines = result.split("\n")
    # All data lines should have same width
    assert len(lines[0]) == len(lines[2])


def test_table_processor_initialization():
    """Test table processor initialization."""
    processor = TableProcessor()

    assert processor.table_settings is not None
    assert processor.min_words_in_table == 2


def test_table_processor_custom_settings():
    """Test table processor with custom settings."""
    settings = {"vertical_strategy": "text"}
    processor = TableProcessor(table_settings=settings, min_words_in_table=5)

    assert processor.table_settings == settings
    assert processor.min_words_in_table == 5


def test_table_processor_has_header_heuristic():
    """Test header detection heuristic."""
    processor = TableProcessor()

    # Good header
    rows = [["Name", "Age", "City"], ["Alice", "30", "NYC"]]
    assert processor._has_header(rows) is True

    # Empty first row - not a good header
    rows = [["", "", ""], ["Alice", "30", "NYC"]]
    assert processor._has_header(rows) is False

    # Single row - default to header
    rows = [["Name", "Age"]]
    assert processor._has_header(rows) is True


def test_table_format_row():
    """Test row formatting with padding."""
    table = TableElement(rows=[[]])
    result = table._format_row(["A", "BB"], [5, 5])

    assert result == "| A     | BB    |"
    assert result.count("|") == 3


def test_table_element_multiline_content():
    """Test table with multi-line cell content."""
    table = TableElement(
        rows=[["Header 1", "Header 2"], ["Line\nBreak", "Normal"]], has_header=True
    )

    result = table.to_markdown()

    # Should contain the content (line break as \n in string)
    assert "Header 1" in result
    assert "Header 2" in result


def test_table_element_special_characters():
    """Test table with special Markdown characters."""
    table = TableElement(
        rows=[["Column|Name", "Value"], ["Data|1", "100"]], has_header=True
    )

    result = table.to_markdown()

    # Pipes in content should be preserved (not escaped in this version)
    assert "Column|Name" in result
    assert "Data|1" in result


def test_table_element_numeric_data():
    """Test table with numeric data."""
    table = TableElement(
        rows=[["Item", "Price"], ["Apple", "1.50"], ["Banana", "0.75"]],
        has_header=True,
    )

    result = table.to_markdown()

    assert "1.50" in result
    assert "0.75" in result


def test_table_element_bbox():
    """Test table with bounding box."""
    bbox = (100.0, 200.0, 500.0, 400.0)
    table = TableElement(rows=[["A", "B"]], has_header=True, bbox=bbox)

    assert table.bbox == bbox


@pytest.mark.skip(reason="Requires PDF file fixture")
def test_table_processor_extract_from_page():
    """Test extracting tables from actual PDF page."""
    # This would need a real pdfplumber page object
    pass


def test_table_minimum_column_width():
    """Test that columns have minimum width for separators."""
    table = TableElement(rows=[["A", "B"], ["C", "D"]], has_header=True)

    result = table.to_markdown()
    lines = result.split("\n")

    # Separator should have at least 3 dashes per column
    separator_line = lines[1]
    assert "---" in separator_line
