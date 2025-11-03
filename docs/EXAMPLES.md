# unpdf Examples and Use Cases

**Version:** 1.0.0  
**Last Updated:** 2025-11-02

Practical examples and real-world use cases for unpdf.

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Advanced CLI Examples](#advanced-cli-examples)
3. [Python API Examples](#python-api-examples)
4. [Batch Processing](#batch-processing)
5. [Integration Examples](#integration-examples)
6. [Real-World Use Cases](#real-world-use-cases)

---

## Basic Usage

### Convert a Single PDF

**Simplest command:**
```bash
unpdf document.pdf
```

**Output:** Creates `document.md` in the same directory.

**Example:**
```bash
$ unpdf manual.pdf
Converting: manual.pdf
Output saved to: manual.md
✓ Conversion complete
```

### Specify Output Path

```bash
unpdf input.pdf -o output/result.md
```

**Example:**
```bash
$ unpdf report.pdf -o converted/report.md
Converting: report.pdf
Output saved to: converted/report.md
```

### Convert with Verbose Output

```bash
unpdf document.pdf --verbose
```

**Example output:**
```
DEBUG: Loading PDF: document.pdf
DEBUG: Pages: 10
DEBUG: Processing page 1/10...
DEBUG: Detected 3 headings, 5 paragraphs, 1 table
DEBUG: Processing page 2/10...
...
INFO: Conversion complete
```

---

## Advanced CLI Examples

### Convert Specific Pages

**Single page:**
```bash
unpdf document.pdf --pages 5
```

**Multiple pages:**
```bash
unpdf document.pdf --pages 1,3,5,7
```

**Page range:**
```bash
unpdf document.pdf --pages 10-20
```

**Mixed (ranges and individual):**
```bash
unpdf document.pdf --pages 1,5-10,15,20-25
```

**Example: Extract table of contents (pages 1-3):**
```bash
unpdf book.pdf --pages 1-3 -o toc.md
```

**Example: Skip intro and conclusion:**
```bash
unpdf thesis.pdf --pages 10-80 -o main_content.md
```

### Custom Heading Detection

**More aggressive (detect more headings):**
```bash
unpdf document.pdf --heading-ratio 1.1
```

**More conservative (fewer headings):**
```bash
unpdf document.pdf --heading-ratio 1.5
```

**Example: Technical documentation (many section headings):**
```bash
unpdf api_docs.pdf --heading-ratio 1.2 -o api_docs.md
```

**Example: Novel or prose (few headings):**
```bash
unpdf novel.pdf --heading-ratio 1.8 -o novel.md
```

### Disable Code Block Detection

```bash
unpdf document.pdf --no-code-blocks
```

**When to use:** Document has monospace fonts that aren't code (e.g., typewriter-style headings).

---

## Python API Examples

### Basic Conversion

```python
from unpdf import convert_pdf

# Convert PDF to string
markdown = convert_pdf("document.pdf")
print(markdown)
```

### Save to File

```python
from unpdf import convert_pdf
from pathlib import Path

markdown = convert_pdf("document.pdf")
Path("output.md").write_text(markdown, encoding="utf-8")
```

### Convert with Options

```python
from unpdf import convert_pdf

markdown = convert_pdf(
    "document.pdf",
    detect_code_blocks=True,
    heading_font_ratio=1.3,
    pages=[1, 2, 3, 10, 15]  # Specific pages
)
```

### Error Handling

```python
from unpdf import convert_pdf
import sys

try:
    markdown = convert_pdf("document.pdf")
    print(markdown)
except FileNotFoundError:
    print("Error: PDF file not found", file=sys.stderr)
    sys.exit(1)
except PermissionError:
    print("Error: Cannot read PDF file", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error: Conversion failed - {e}", file=sys.stderr)
    sys.exit(1)
```

### Process Multiple PDFs

```python
from unpdf import convert_pdf
from pathlib import Path

pdf_dir = Path("documents")
output_dir = Path("markdown")
output_dir.mkdir(exist_ok=True)

for pdf_file in pdf_dir.glob("*.pdf"):
    print(f"Converting {pdf_file.name}...")
    try:
        markdown = convert_pdf(str(pdf_file))
        output_file = output_dir / f"{pdf_file.stem}.md"
        output_file.write_text(markdown, encoding="utf-8")
        print(f"  ✓ Saved to {output_file}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
```

### Page-by-Page Processing

```python
import pdfplumber
from unpdf.core import convert_page, calculate_average_font_size
from unpdf.extractors.text import extract_text_with_metadata

pdf_path = "large_document.pdf"

with pdfplumber.open(pdf_path) as pdf:
    # Calculate average font size across all pages
    all_elements = []
    for page in pdf.pages:
        elements = extract_text_with_metadata(page)
        all_elements.extend(elements)
    
    avg_font_size = calculate_average_font_size(all_elements)
    
    # Process pages individually
    for i, page in enumerate(pdf.pages, start=1):
        print(f"Processing page {i}/{len(pdf.pages)}...")
        markdown = convert_page(page, avg_font_size)
        
        # Save each page separately
        with open(f"page_{i:03d}.md", "w", encoding="utf-8") as f:
            f.write(markdown)
```

---

## Batch Processing

### Process Directory (Non-Recursive)

```bash
unpdf documents/
```

Converts all PDFs in `documents/` directory, creating `.md` files alongside PDFs.

### Process Directory Recursively

```bash
unpdf documents/ --recursive
```

Processes all PDFs in `documents/` and subdirectories.

### Bash Script: Batch with Custom Output

```bash
#!/bin/bash
# convert_all.sh - Convert all PDFs to separate output directory

INPUT_DIR="pdfs"
OUTPUT_DIR="markdown"

mkdir -p "$OUTPUT_DIR"

for pdf in "$INPUT_DIR"/*.pdf; do
    filename=$(basename "$pdf" .pdf)
    echo "Converting $filename..."
    unpdf "$pdf" -o "$OUTPUT_DIR/$filename.md"
done

echo "All conversions complete!"
```

**Usage:**
```bash
chmod +x convert_all.sh
./convert_all.sh
```

### PowerShell Script: Batch with Error Handling

```powershell
# convert_all.ps1 - Convert PDFs with error handling and logging

$InputDir = "pdfs"
$OutputDir = "markdown"
$LogFile = "conversion.log"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$pdfs = Get-ChildItem -Path $InputDir -Filter "*.pdf"
$total = $pdfs.Count
$success = 0
$failed = 0

"Starting conversion of $total files..." | Tee-Object -FilePath $LogFile

foreach ($pdf in $pdfs) {
    $outputName = [System.IO.Path]::GetFileNameWithoutExtension($pdf.Name) + ".md"
    $outputPath = Join-Path $OutputDir $outputName
    
    Write-Host "Converting: $($pdf.Name)..." -NoNewline
    
    try {
        unpdf $pdf.FullName -o $outputPath 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            "SUCCESS: $($pdf.Name)" | Add-Content $LogFile
            $success++
        } else {
            Write-Host " ✗" -ForegroundColor Red
            "FAILED: $($pdf.Name)" | Add-Content $LogFile
            $failed++
        }
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        "ERROR: $($pdf.Name) - $($_.Exception.Message)" | Add-Content $LogFile
        $failed++
    }
}

""
"Conversion complete!"
"Success: $success / $total"
"Failed: $failed / $total"
"See $LogFile for details"
```

**Usage:**
```powershell
.\convert_all.ps1
```

### Python Script: Parallel Processing

```python
#!/usr/bin/env python3
"""parallel_convert.py - Convert multiple PDFs in parallel"""

import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from unpdf import convert_pdf

def convert_single(pdf_path, output_dir):
    """Convert a single PDF and return result."""
    try:
        markdown = convert_pdf(str(pdf_path))
        output_file = output_dir / f"{pdf_path.stem}.md"
        output_file.write_text(markdown, encoding="utf-8")
        return pdf_path.name, True, None
    except Exception as e:
        return pdf_path.name, False, str(e)

def main():
    if len(sys.argv) < 3:
        print("Usage: python parallel_convert.py INPUT_DIR OUTPUT_DIR [WORKERS]")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    
    output_dir.mkdir(exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    total = len(pdf_files)
    
    print(f"Converting {total} PDFs using {workers} workers...")
    
    success_count = 0
    failed_count = 0
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(convert_single, pdf, output_dir): pdf
            for pdf in pdf_files
        }
        
        for future in as_completed(futures):
            name, success, error = future.result()
            if success:
                print(f"✓ {name}")
                success_count += 1
            else:
                print(f"✗ {name}: {error}")
                failed_count += 1
    
    print(f"\nComplete: {success_count}/{total} succeeded, {failed_count} failed")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python parallel_convert.py pdfs/ markdown/ 8
```

---

## Integration Examples

### Git Pre-Commit Hook

Convert PDFs to Markdown automatically on commit:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Find staged PDF files
STAGED_PDFS=$(git diff --cached --name-only --diff-filter=ACM | grep '\.pdf$')

if [ -n "$STAGED_PDFS" ]; then
    echo "Converting staged PDFs to Markdown..."
    
    for pdf in $STAGED_PDFS; do
        if [ -f "$pdf" ]; then
            md_file="${pdf%.pdf}.md"
            unpdf "$pdf" -o "$md_file"
            git add "$md_file"
            echo "  ✓ $pdf -> $md_file"
        fi
    done
fi
```

**Setup:**
```bash
chmod +x .git/hooks/pre-commit
```

### Makefile Integration

```makefile
# Makefile - Convert PDFs as part of build process

PDFS := $(wildcard docs/*.pdf)
MARKDOWN := $(PDFS:.pdf=.md)

.PHONY: all clean docs

all: docs

docs: $(MARKDOWN)

%.md: %.pdf
	@echo "Converting $<..."
	@unpdf $< -o $@

clean:
	rm -f $(MARKDOWN)

watch:
	@while true; do \
		make docs; \
		sleep 5; \
	done
```

**Usage:**
```bash
make docs      # Convert all PDFs
make clean     # Remove generated Markdown
make watch     # Continuously monitor and convert
```

### GitHub Actions Workflow

```yaml
# .github/workflows/convert-pdfs.yml

name: Convert PDFs to Markdown

on:
  push:
    paths:
      - '**.pdf'

jobs:
  convert:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install unpdf
        run: pip install unpdf[tables]
      
      - name: Convert PDFs
        run: |
          find . -name "*.pdf" -type f | while read pdf; do
            md="${pdf%.pdf}.md"
            echo "Converting $pdf to $md"
            unpdf "$pdf" -o "$md"
          done
      
      - name: Commit converted files
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add "*.md"
          git diff --staged --quiet || git commit -m "Convert PDFs to Markdown"
          git push
```

### Flask Web Service

```python
from flask import Flask, request, send_file
from unpdf import convert_pdf
import tempfile
from pathlib import Path

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    """Convert uploaded PDF to Markdown."""
    if 'file' not in request.files:
        return {'error': 'No file uploaded'}, 400
    
    pdf_file = request.files['file']
    
    if not pdf_file.filename.endswith('.pdf'):
        return {'error': 'File must be a PDF'}, 400
    
    # Save uploaded file temporarily
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / pdf_file.filename
        pdf_file.save(pdf_path)
        
        # Convert
        try:
            markdown = convert_pdf(str(pdf_path))
            
            # Save result
            md_path = pdf_path.with_suffix('.md')
            md_path.write_text(markdown, encoding='utf-8')
            
            # Send back to client
            return send_file(
                md_path,
                as_attachment=True,
                download_name=f"{pdf_path.stem}.md"
            )
        except Exception as e:
            return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
```

**Usage:**
```bash
# Start server
python app.py

# Convert via curl
curl -F "file=@document.pdf" http://localhost:5000/convert -o output.md
```

---

## Real-World Use Cases

### Use Case 1: Documentation Pipeline

**Scenario:** Convert product manuals from PDF to Markdown for website.

```python
#!/usr/bin/env python3
"""docs_pipeline.py - Convert documentation PDFs to web-ready Markdown"""

from pathlib import Path
from unpdf import convert_pdf
import yaml

def add_frontmatter(markdown, metadata):
    """Add YAML frontmatter to Markdown."""
    frontmatter = yaml.dump(metadata, default_flow_style=False)
    return f"---\n{frontmatter}---\n\n{markdown}"

def process_manual(pdf_path, version, category):
    """Convert manual and add metadata."""
    markdown = convert_pdf(str(pdf_path))
    
    metadata = {
        'title': pdf_path.stem.replace('_', ' ').title(),
        'version': version,
        'category': category,
        'source': pdf_path.name,
        'generated': True
    }
    
    return add_frontmatter(markdown, metadata)

def main():
    manuals = [
        ('manuals/user_guide.pdf', '2.0', 'User Documentation'),
        ('manuals/api_reference.pdf', '2.0', 'Developer Documentation'),
        ('manuals/admin_guide.pdf', '2.0', 'Administration'),
    ]
    
    output_dir = Path('website/docs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for pdf_path, version, category in manuals:
        pdf_path = Path(pdf_path)
        print(f"Processing {pdf_path.name}...")
        
        markdown = process_manual(pdf_path, version, category)
        
        output_file = output_dir / f"{pdf_path.stem}.md"
        output_file.write_text(markdown, encoding='utf-8')
        print(f"  ✓ Saved to {output_file}")

if __name__ == '__main__':
    main()
```

### Use Case 2: Research Paper Archive

**Scenario:** Convert research papers to Markdown for full-text search.

```python
#!/usr/bin/env python3
"""archive_papers.py - Build searchable archive of research papers"""

from pathlib import Path
from unpdf import convert_pdf
import re
import json

def extract_metadata(markdown):
    """Extract paper metadata from converted text."""
    lines = markdown.split('\n')
    
    # Simple heuristics - adjust for your papers
    title = lines[0].strip('#').strip() if lines else "Unknown"
    
    # Find author line (usually follows title)
    authors = []
    for line in lines[1:5]:
        if re.match(r'^[A-Z][a-z]+ [A-Z]', line):
            authors.append(line.strip())
    
    return {
        'title': title,
        'authors': authors
    }

def process_paper(pdf_path):
    """Convert paper and extract metadata."""
    markdown = convert_pdf(str(pdf_path), detect_code_blocks=False)
    metadata = extract_metadata(markdown)
    
    return {
        'file': pdf_path.stem,
        'metadata': metadata,
        'content': markdown
    }

def main():
    papers_dir = Path('papers')
    output_dir = Path('archive')
    output_dir.mkdir(exist_ok=True)
    
    index = []
    
    for pdf_file in papers_dir.glob('*.pdf'):
        print(f"Processing {pdf_file.name}...")
        
        try:
            paper = process_paper(pdf_file)
            
            # Save Markdown
            md_file = output_dir / f"{pdf_file.stem}.md"
            md_file.write_text(paper['content'], encoding='utf-8')
            
            # Add to index
            index.append({
                'file': paper['file'],
                'title': paper['metadata']['title'],
                'authors': paper['metadata']['authors']
            })
            
            print(f"  ✓ {paper['metadata']['title']}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    # Save searchable index
    index_file = output_dir / 'index.json'
    index_file.write_text(json.dumps(index, indent=2), encoding='utf-8')
    print(f"\nIndexed {len(index)} papers")

if __name__ == '__main__':
    main()
```

### Use Case 3: Invoice Processing

**Scenario:** Extract invoice data for accounting.

```python
#!/usr/bin/env python3
"""process_invoices.py - Extract invoice data from PDFs"""

from pathlib import Path
from unpdf import convert_pdf
import re
from decimal import Decimal

def extract_invoice_data(markdown):
    """Extract structured data from invoice Markdown."""
    data = {}
    
    # Invoice number
    inv_match = re.search(r'Invoice #?(\S+)', markdown, re.I)
    if inv_match:
        data['invoice_number'] = inv_match.group(1)
    
    # Date
    date_match = re.search(r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})', markdown)
    if date_match:
        data['date'] = date_match.group(1)
    
    # Total
    total_match = re.search(r'Total:\s*\$?([\d,]+\.\d{2})', markdown)
    if total_match:
        data['total'] = Decimal(total_match.group(1).replace(',', ''))
    
    return data

def main():
    invoices_dir = Path('invoices')
    output_dir = Path('processed')
    output_dir.mkdir(exist_ok=True)
    
    report = []
    
    for pdf_file in sorted(invoices_dir.glob('*.pdf')):
        print(f"Processing {pdf_file.name}...")
        
        try:
            markdown = convert_pdf(str(pdf_file))
            data = extract_invoice_data(markdown)
            
            # Save Markdown for records
            md_file = output_dir / f"{pdf_file.stem}.md"
            md_file.write_text(markdown, encoding='utf-8')
            
            report.append({
                'file': pdf_file.name,
                **data
            })
            
            print(f"  ✓ Invoice {data.get('invoice_number', 'N/A')}: ${data.get('total', 0)}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    # Generate summary report
    total_amount = sum(item.get('total', 0) for item in report)
    
    report_md = "# Invoice Processing Report\n\n"
    report_md += f"**Total Invoices:** {len(report)}\n"
    report_md += f"**Total Amount:** ${total_amount:.2f}\n\n"
    report_md += "## Details\n\n"
    report_md += "| Invoice | Date | Amount |\n"
    report_md += "|---------|------|--------|\n"
    
    for item in report:
        report_md += f"| {item.get('invoice_number', 'N/A')} "
        report_md += f"| {item.get('date', 'N/A')} "
        report_md += f"| ${item.get('total', 0):.2f} |\n"
    
    Path('invoice_report.md').write_text(report_md, encoding='utf-8')
    print(f"\nReport saved to invoice_report.md")

if __name__ == '__main__':
    main()
```

---

## Tips and Tricks

### 1. Preview First Page

```bash
unpdf document.pdf --pages 1 -o preview.md && cat preview.md
```

### 2. Extract Table of Contents

```bash
unpdf book.pdf --pages 1-5 -o toc.md
```

### 3. Convert Without Code Detection

For documents with monospace fonts that aren't code:

```bash
unpdf document.pdf --no-code-blocks
```

### 4. Batch Convert with Quality Check

```bash
for pdf in *.pdf; do
    unpdf "$pdf" -o "${pdf%.pdf}.md"
    wc -w "${pdf%.pdf}.md"  # Word count
done
```

### 5. Combine Multiple PDF Outputs

```bash
unpdf doc1.pdf -o part1.md
unpdf doc2.pdf -o part2.md
unpdf doc3.pdf -o part3.md

cat part*.md > combined.md
```

### 6. Convert with Custom Settings per Document Type

```bash
# Technical documentation
unpdf api.pdf --heading-ratio 1.2 -o api.md

# Business reports
unpdf report.pdf --heading-ratio 1.5 --no-code-blocks -o report.md

# Academic papers
unpdf paper.pdf --heading-ratio 1.3 -o paper.md
```

---

## More Examples

For more examples, see:
- [USER_GUIDE.md](USER_GUIDE.md) - Comprehensive usage guide
- [API_REFERENCE.md](API_REFERENCE.md) - Python API documentation
- [GitHub Discussions](https://github.com/yourusername/unpdf/discussions) - Community examples

---

**Questions?** Open an issue or discussion on GitHub!
