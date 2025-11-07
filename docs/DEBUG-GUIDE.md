# Debug Structure Output Guide

## Overview

The `--debug-structure` flag generates a detailed text representation of the PDF's internal structure, making it easy to debug conversion issues and understand how the PDF is organized.

## Usage

### Basic Usage

```bash
# Convert PDF and generate structure dump
unpdf input.pdf --debug-structure

# Specify output location
unpdf input.pdf -o output.md --debug-structure
# Creates: output.md and output.structure.txt
```

### With Directories

```bash
# Process all PDFs in directory with structure dumps
unpdf docs/ --debug-structure --recursive
```

## What's in the Structure Dump

The structure dump file (`.structure.txt`) contains:

### 1. Document Metadata
- File size
- PDF version
- Creator/producer information
- Creation/modification dates

### 2. Page-Level Information
- Page dimensions (width x height in points)
- Number of text blocks
- Font statistics (median, min, max sizes)
- List of unique fonts used

### 3. Text Block Details
For each text block on the page:
- **Position**: Bounding box coordinates (x0, y0) → (x1, y1)
- **Size**: Width x height in points
- **Content**: Line-by-line text extraction
- **Font Properties**: Family name, size in points
- **Color**: Hex color code
- **Flags**: Decoded style flags (bold, italic, monospace, etc.)

### 4. Tables
- Position and dimensions
- Row x column count
- Cell content preview

### 5. Images
- Position and dimensions
- Format and color space
- Resolution (width x height in pixels)

## Example Structure Dump

```
================================================================================
PDF STRUCTURE DUMP: document.pdf
================================================================================
Pages: 1
File size: 55,815 bytes

METADATA:
  format: PDF 1.5
  creator: LaTeX via pandoc
  producer: MiKTeX pdfTeX-1.40.27

================================================================================
PAGE 1 (612.0 x 792.0 pt)
================================================================================

Text Blocks: 6

FONT STATISTICS:
  Median font size: 10.0pt
  Min font size: 10.0pt
  Max font size: 14.3pt
  Unique fonts: 2
    - LMRoman10-Regular
    - LMRoman12-Bold

--------------------------------------------------------------------------------
BLOCK #1: TextBlock
  Position: (133.8, 123.6) → (286.6, 137.9)
  Size: 152.8 x 14.3 pt

  Lines: 1
  Line 1 @ y=137.9:
    Text: 'Basic Text Document'
    Font: LMRoman12-Bold, Size: 14.3pt
    Color: #000000
    Flags: serifed, bold
    Styles: bold
```

## Debugging Workflow

### 1. Identify Conversion Issues
First, compare the original markdown, converted markdown, and notice differences:
```bash
# Convert with structure dump
unpdf input.pdf --debug-structure

# Compare files
diff original.md output.md
```

### 2. Examine PDF Structure
Open the `.structure.txt` file to understand the source PDF:
- What fonts and sizes are used?
- How is text positioned and grouped?
- Are there multiple fonts/styles on the same line?
- What's the median font size vs heading sizes?

### 3. Diagnose Problems

**Example: Header level wrong**
- Check font size in structure dump
- Compare to median font size
- Verify heading detection ratio (`--heading-ratio`)
- Font size 14.3pt with median 10.0pt = 1.43 ratio (should be detected as H1)

**Example: Paragraphs merged**
- Look at block positions and vertical spacing
- Check if blocks are on separate lines (different y-coordinates)
- Verify paragraph separation logic

**Example: Missing inline formatting**
- Examine spans within a line
- Look for style flag changes (bold, italic, monospace)
- Check if multiple fonts appear on same line

**Example: Table not detected**
- Look for table structure in dump
- Check if cells are properly organized
- Verify table dimensions match expected

### 4. Report Issues
When reporting bugs or asking for help, include:
- Original markdown (if available)
- Converted markdown output
- Structure dump (`.structure.txt`)
- Specific blocks or sections with issues

This gives developers the complete picture to reproduce and fix the issue.

## Common Patterns to Look For

### Heading Detection
Headings typically have:
- Larger font size than body text
- Bold font weight
- Standalone blocks (not mixed with other content)

Example:
```
Font: LMRoman12-Bold, Size: 14.3pt  (Heading)
Font: LMRoman10-Regular, Size: 10.0pt  (Body text)
Ratio: 14.3 / 10.0 = 1.43 (>1.3 threshold = heading detected)
```

### Inline Formatting
Look for multiple spans in a single line with different styles:
```
Line 1:
  Text: 'This is '
  Font: Arial, Size: 12.0pt, Flags: none
  Text: 'bold'
  Font: Arial-Bold, Size: 12.0pt, Flags: bold
  Text: ' text'
  Font: Arial, Size: 12.0pt, Flags: none
```

### Code Blocks
Code blocks typically have:
- Monospace font (Courier, Consolas, Monaco, etc.)
- Different background color or indentation
- Multiple consecutive lines with monospace font

### Lists
Lists typically have:
- Bullet characters (•, ◦, ▪)
- Numbered prefixes (1., 2., 3.)
- Consistent indentation
- May use special Unicode characters

### Tables
Tables show as:
- TABLES section with row x column count
- Cell content with [row, col] coordinates
- Bounding box encompassing all cells

## Tips

1. **Compare font sizes**: Always look at median font size first, then compare heading sizes to understand the document's typography hierarchy

2. **Check positioning**: Y-coordinates decrease from bottom to top in PDF coordinate system. Higher y-value = higher on page.

3. **Look for special fonts**: Type3 fonts (Unnamed-T3) are often used for symbols, bullets, or special characters

4. **Color analysis**: Different colors might indicate links, emphasis, or code

5. **Spacing matters**: Large gaps in y-coordinates indicate paragraph breaks or section separations

## Technical Details

### Coordinate System
PDFs use a bottom-left origin coordinate system:
- X increases left to right
- Y increases bottom to top
- Points are 1/72 inch (standard PDF unit)
- Letter size page: 612 x 792 points (8.5" x 11")

### Font Flags
The `Flags` field is decoded from PyMuPDF's font flags:
- **Bold** (bit 4): Font weight is bold
- **Italic** (bit 1): Font style is italic
- **Superscript** (bit 0): Text is superscript
- **Serifed** (bit 2): Font has serifs
- **Monospaced** (bit 3): Fixed-width font

### Style Detection
The dumper automatically detects common styles:
- **bold**: Flag bit 4 set or font name contains "Bold"
- **italic**: Flag bit 1 set or font name contains "Italic"
- **monospace**: Flag bit 3 set or font name contains "Courier", "Mono", "Console"

## Further Reading

- [PDF Coordinate System](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf) - Adobe PDF Reference
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/) - PDF parsing library docs
- [PDF-CHALLENGES.md](PDF-CHALLENGES.md) - Known challenges with PDF format
