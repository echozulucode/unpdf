# unpdf User Guide

Complete guide to using unpdf for PDF-to-Markdown conversion.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Command-Line Interface](#command-line-interface)
4. [Python API](#python-api)
5. [Features & Examples](#features--examples)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Installation

### Requirements

- **Python 3.10+**
- **Operating System:** Windows, macOS, Linux

### Basic Installation

```bash
pip install unpdf
```

### With Optional Features

```bash
# Include table extraction support
pip install unpdf[tables]

# Install development dependencies
pip install unpdf[dev]
```

### From Source

```bash
git clone https://github.com/yourusername/unpdf.git
cd unpdf
pip install -e .
```

### Verify Installation

```bash
unpdf --version
```

---

## Quick Start

### Convert a Single PDF

```bash
unpdf document.pdf
```

This creates `document.md` in the same directory.

### Specify Output Location

```bash
unpdf input.pdf -o output/result.md
```

### Convert Specific Pages

```bash
# Single page
unpdf document.pdf --pages 3

# Multiple pages
unpdf document.pdf --pages 1,3,5

# Page ranges
unpdf document.pdf --pages 1-5,10,15-20
```

### Batch Processing

```bash
# Convert all PDFs in a directory
unpdf documents/

# Recursive processing
unpdf documents/ --recursive
```

---

## Command-Line Interface

### Basic Usage

```bash
unpdf [OPTIONS] INPUT [OUTPUT]
```

### Arguments

- **INPUT**: Path to PDF file or directory
- **OUTPUT** (optional): Output path for Markdown file

### Options

#### Input/Output

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output file path | `-o result.md` |
| `--recursive` | `-r` | Process directories recursively | `-r` |

#### Content Processing

| Option | Default | Description | Example |
|--------|---------|-------------|---------|
| `--pages` | All | Specific pages to convert | `--pages 1,3-5` |
| `--no-code-blocks` | Enabled | Disable code block detection | `--no-code-blocks` |
| `--heading-ratio` | 1.3 | Font size ratio for headings | `--heading-ratio 1.5` |

#### Output Control

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable debug logging |
| `--version` | | Show version and exit |
| `--help` | `-h` | Show help message |

### Examples

#### Convert with Verbose Output

```bash
unpdf document.pdf --verbose
```

#### Custom Heading Detection

```bash
# More aggressive heading detection (smaller ratio)
unpdf document.pdf --heading-ratio 1.2

# More conservative (larger ratio)
unpdf document.pdf --heading-ratio 1.5
```

#### Disable Code Block Detection

```bash
unpdf document.pdf --no-code-blocks
```

#### Complex Page Selection

```bash
# Pages 1, 3, 5-10, and 15
unpdf document.pdf --pages "1,3,5-10,15"
```

#### Batch Processing with Options

```bash
# Convert all PDFs recursively with custom settings
unpdf docs/ -r --heading-ratio 1.4 -v
```

---

## Python API

### Basic Usage

```python
from unpdf import convert_pdf

# Convert PDF to Markdown string
markdown = convert_pdf("document.pdf")

# Save to file
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown)
```

### With Options

```python
from unpdf import convert_pdf

markdown = convert_pdf(
    "document.pdf",
    detect_code_blocks=True,
    heading_font_ratio=1.3,
    pages=[1, 3, 5]  # Specific pages
)
```

### Error Handling

```python
from unpdf import convert_pdf

try:
    markdown = convert_pdf("document.pdf")
except FileNotFoundError:
    print("PDF file not found")
except Exception as e:
    print(f"Conversion failed: {e}")
```

### Advanced: Page-by-Page Processing

```python
from unpdf.extractors.text import extract_text_with_metadata
from unpdf.renderers.markdown import MarkdownRenderer
import pdfplumber

renderer = MarkdownRenderer()

with pdfplumber.open("document.pdf") as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        elements = extract_text_with_metadata(page)
        markdown = renderer.render(elements)
        
        # Process each page
        print(f"Page {page_num}:")
        print(markdown)
```

---

## Features & Examples

### Text Formatting

**Input PDF contains:**
- **Bold text**
- *Italic text*
- ***Bold and italic***

**Output Markdown:**
```markdown
- **Bold text**
- *Italic text*
- ***Bold and italic***
```

### Headings

unpdf detects headings based on font size. Default ratio: 1.3x average font size.

**Example output:**
```markdown
# Main Heading

## Subheading

### Sub-subheading

Regular text paragraph.
```

### Lists

**Bullet lists:**
```markdown
- Item 1
- Item 2
  - Nested item (if indented)
- Item 3
```

**Numbered lists:**
```markdown
1. First item
2. Second item
3. Third item
```

### Code Blocks

Monospace fonts are automatically detected:

```markdown
`inline code`

```
# Code block
def hello():
    print("Hello, world!")
```
```

### Tables

**Pipe-table format:**

```markdown
| Name | Age | City |
|------|-----|------|
| Alice | 30 | NYC |
| Bob | 25 | LA |
```

**Features:**
- Automatic header detection
- Column width adjustment
- Handles empty cells
- Uneven row normalization

### Images

**Extracted and referenced:**

```markdown
![Caption text](document_page1_img1.png)
```

**Image handling:**
- Saved to output directory (or same as PDF)
- Unique MD5-based filenames
- Caption detection (within 50pt below image)
- Supported formats: JPEG, PNG

### Hyperlinks

**PDF links converted:**

```markdown
[Visit our website](https://example.com)
```

**Plain URLs detected:**

```markdown
See: https://github.com/user/repo
```

### Blockquotes

```markdown
> This is a quoted paragraph
> that spans multiple lines.
```

---

## Configuration

### Heading Detection Threshold

Control heading sensitivity with `--heading-ratio`:

```bash
# Default (1.3x average font size)
unpdf document.pdf

# More headings detected (lower threshold)
unpdf document.pdf --heading-ratio 1.2

# Fewer headings (higher threshold)
unpdf document.pdf --heading-ratio 1.5
```

### Code Block Detection

Disable if monospace fonts cause false positives:

```bash
unpdf document.pdf --no-code-blocks
```

### Page Selection

Only convert specific pages:

```bash
# Pages 1-10 only
unpdf large.pdf --pages 1-10

# Skip introduction, convert rest
unpdf document.pdf --pages 11-
```

---

## Troubleshooting

### Issue: Headings Not Detected

**Symptom:** All text appears as paragraphs.

**Solution:** Lower the heading ratio threshold:

```bash
unpdf document.pdf --heading-ratio 1.1
```

### Issue: Too Many Headings

**Symptom:** Regular text converted to headings.

**Solution:** Increase the heading ratio:

```bash
unpdf document.pdf --heading-ratio 1.5
```

### Issue: Code Blocks Incorrect

**Symptom:** Regular text marked as code.

**Solution:** Disable code block detection:

```bash
unpdf document.pdf --no-code-blocks
```

### Issue: Tables Not Detected

**Symptom:** Table data appears as plain text.

**Solution:** Ensure pdfplumber is installed:

```bash
pip install unpdf[tables]
```

### Issue: Images Not Extracted

**Symptom:** No image files created.

**Possible causes:**
1. Images embedded as vector graphics (not supported)
2. Permission issues (check output directory permissions)
3. Unsupported image format

**Debug:**
```bash
unpdf document.pdf --verbose
```

### Issue: Garbled Text

**Symptom:** Special characters appear incorrectly.

**Solution:** Ensure output file uses UTF-8 encoding:

```python
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown)
```

### Issue: Memory Error with Large PDFs

**Symptom:** Program crashes or system runs out of memory.

**Solution:** Process pages in batches:

```bash
# Process first 50 pages
unpdf large.pdf --pages 1-50 -o part1.md

# Process next 50 pages
unpdf large.pdf --pages 51-100 -o part2.md
```

---

## Best Practices

### 1. Test on Sample Pages First

```bash
# Convert first page to verify settings
unpdf document.pdf --pages 1 -o test.md
```

### 2. Use Verbose Mode for Debugging

```bash
unpdf document.pdf --verbose
```

### 3. Process Large Documents in Batches

```bash
# Split into smaller chunks
unpdf doc.pdf --pages 1-25 -o part1.md
unpdf doc.pdf --pages 26-50 -o part2.md
```

### 4. Organize Output Files

```bash
# Create output directory structure
mkdir -p output/images
unpdf document.pdf -o output/document.md
```

### 5. Version Control Friendly

```bash
# Use consistent formatting for diffs
unpdf document.pdf --heading-ratio 1.3
```

### 6. Verify Output Quality

Always review the first conversion to ensure:
- Headings are properly detected
- Tables are formatted correctly
- Images are extracted
- Links are preserved

### 7. Automate Batch Processing

**Bash script:**
```bash
#!/bin/bash
for pdf in docs/*.pdf; do
    unpdf "$pdf" -o "output/$(basename "$pdf" .pdf).md"
done
```

**PowerShell script:**
```powershell
Get-ChildItem docs\*.pdf | ForEach-Object {
    unpdf $_.FullName -o "output\$($_.BaseName).md"
}
```

### 8. Handle Errors Gracefully

```python
import os
from pathlib import Path
from unpdf import convert_pdf

pdf_dir = Path("documents")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

for pdf_file in pdf_dir.glob("*.pdf"):
    try:
        markdown = convert_pdf(str(pdf_file))
        output_file = output_dir / f"{pdf_file.stem}.md"
        output_file.write_text(markdown, encoding="utf-8")
        print(f"✓ Converted {pdf_file.name}")
    except Exception as e:
        print(f"✗ Failed {pdf_file.name}: {e}")
```

---

## Performance Tips

### 1. Memory Usage

- Process large PDFs in page batches
- Close file handles when using API
- Use `--pages` to limit memory footprint

### 2. Speed Optimization

- Disable unused features (`--no-code-blocks`)
- Process multiple files in parallel (external script)
- Use SSD storage for faster I/O

### 3. Quality vs Speed

**Fast conversion (lower quality):**
```bash
unpdf doc.pdf --no-code-blocks --heading-ratio 1.5
```

**High quality (slower):**
```bash
unpdf doc.pdf --heading-ratio 1.2
```

---

## Limitations

### Not Supported

- **Mathematical equations** (LaTeX, MathML)
- **Form fields** (input boxes, checkboxes)
- **Annotations** (comments, highlights)
- **Scanned PDFs** (requires OCR)
- **Vector graphics** (only raster images)
- **Audio/video** embeddings
- **3D objects**
- **Digital signatures**

### Partially Supported

- **Footnotes** (detected as regular text)
- **Multi-column layouts** (reading order may be incorrect)
- **Merged table cells** (Markdown limitation)
- **Nested lists** (limited depth support)

### Workarounds

For unsupported features, consider:
- **OCR**: Use [Marker](https://github.com/VikParuchuri/marker) for scanned PDFs
- **Equations**: Use [Mathpix](https://mathpix.com/) for LaTeX conversion
- **Forms**: Export as flattened PDF first

---

## Getting Help

- **Documentation**: [docs/](https://github.com/yourusername/unpdf/tree/main/docs)
- **Issues**: [GitHub Issue Tracker](https://github.com/yourusername/unpdf/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/unpdf/discussions)

### Reporting Bugs

Include:
1. unpdf version (`unpdf --version`)
2. Python version (`python --version`)
3. Operating system
4. Command or code that triggered the issue
5. Sample PDF (if possible) or description
6. Error message / unexpected output

### Feature Requests

Check existing issues first, then open a new issue with:
1. Use case description
2. Expected behavior
3. Example PDF characteristics
4. Why existing options don't work

---

**Last Updated:** 2025-11-02  
**Version:** 1.0.0
