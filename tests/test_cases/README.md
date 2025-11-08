# Test Cases

This directory contains test markdown files and PDFs for accuracy testing.

## Test Case Files

1. **01_basic_text** - Simple paragraphs and headings
2. **02_text_formatting** - Bold, italic, inline code, strikethrough
3. **03_lists** - Ordered, unordered, and nested lists
4. **04_code_blocks** - Code blocks with and without syntax highlighting
5. **05_tables** - Simple and aligned tables
6. **06_links_and_quotes** - Links and blockquotes
7. **07_headings** - All heading levels (H1-H6)
8. **08_horizontal_rules** - Horizontal rules
9. **09_complex_document** - Multiple features combined
10. **10_advanced_tables** - Tables with formatting and various sizes

## Running Test Cases

### Automated Test Runner

Run all test cases with debug output:

```bash
python run_test_cases.py
```

This will:
- Convert all PDFs in this directory
- Generate `{test_case}_output.md` files with conversion results
- Generate `{test_case}_debug.txt` files with detailed debug logs
- Display a summary of results

**Note:** Output files (`*_output.md` and `*_debug.txt`) are automatically ignored by git.

### Running Individual Tests

```bash
python -m unpdf tests/test_cases/01_basic_text.pdf
```

### Running Pytest Tests

```bash
pytest tests/test_regression.py -v
```

## Generated Files

Each test run generates two files per test case:

- `{test_case}_output.md` - The converted markdown output
- `{test_case}_debug.txt` - Debug log with detailed processing information

These files are automatically regenerated on each run and are ignored by git.

## PDF Source Files

The PDF files in this directory were generated from the corresponding `.md` files using various converters to ensure consistent testing across different PDF generation methods.
