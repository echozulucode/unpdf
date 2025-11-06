# Test Cases

This directory contains test markdown files for accuracy testing.

## Test Case Files

1. **01_basic_text.md** - Simple paragraphs and headings
2. **02_text_formatting.md** - Bold, italic, inline code, strikethrough
3. **03_lists.md** - Ordered, unordered, and nested lists
4. **04_code_blocks.md** - Code blocks with and without syntax highlighting
5. **05_tables.md** - Simple and aligned tables
6. **06_links_and_quotes.md** - Links and blockquotes
7. **07_headings.md** - All heading levels (H1-H6)
8. **08_horizontal_rules.md** - Horizontal rules
9. **09_complex_document.md** - Multiple features combined
10. **10_advanced_tables.md** - Tables with formatting and various sizes

## PDF Conversion

### Instructions for Manual PDF Conversion

After creating PDFs from each markdown file, place them in this directory with the same name but `.pdf` extension:

- `01_basic_text.pdf`
- `02_text_formatting.pdf`
- `03_lists.pdf`
- etc.

### Recommended PDF Converters

You can use any of the following tools to convert markdown to PDF:

1. **Obsidian** - Consistent with existing test case
2. **Pandoc** - `pandoc input.md -o output.pdf`
3. **VS Code with Markdown PDF extension**
4. **Typora** - Commercial markdown editor with PDF export
5. **Marked 2** (macOS) - Markdown previewer with PDF export

### Converting All Files

You can use this PowerShell script to convert all files with Pandoc:

```powershell
Get-ChildItem *.md -Exclude README.md | ForEach-Object {
    $pdfName = $_.BaseName + ".pdf"
    pandoc $_.Name -o $pdfName
}
```

## Running Tests

After PDFs are created, run the accuracy tests:

```bash
python -m unpdf --accuracy tests/test_cases/01_basic_text.pdf
python -m unpdf --accuracy tests/test_cases/02_text_formatting.pdf
# ... etc
```

Or run all tests:

```bash
python scripts/run_test_suite.py
```

## Expected Results

Each test case targets specific markdown features. The accuracy detector will report:

- Overall accuracy percentage
- Element-level accuracy for each feature
- Specific issues or differences found

Track results in a spreadsheet or test report to identify patterns and areas for improvement.
