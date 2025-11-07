"""Debug script to check strikethrough detection in test case 02."""

import pdfplumber
import pymupdf

pdf_path = "tests/test_cases/02_text_formatting.pdf"

print("=" * 80)
print("Checking pdfplumber extraction")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    print(f"\nLines found: {len(page.lines)}")
    for i, line in enumerate(page.lines[:10]):  # Show first 10
        print(f"  Line {i}: {line}")
    
    print(f"\nRects found: {len(page.rects)}")
    for i, rect in enumerate(page.rects[:10]):  # Show first 10
        print(f"  Rect {i}: {rect}")
    
    print(f"\nCurves found: {len(page.curves)}")
    for i, curve in enumerate(page.curves[:10]):  # Show first 10
        print(f"  Curve {i}: {curve}")

print("\n" + "=" * 80)
print("Checking PyMuPDF extraction")
print("=" * 80)

doc = pymupdf.open(pdf_path)
page = doc[0]

# Get drawing commands
drawings = page.get_drawings()
print(f"\nDrawings found: {len(drawings)}")
for i, drawing in enumerate(drawings[:10]):  # Show first 10
    print(f"  Drawing {i}:")
    print(f"    Type: {drawing.get('type', 'unknown')}")
    print(f"    Rect: {drawing.get('rect', 'N/A')}")
    print(f"    Items: {len(drawing.get('items', []))}")
    if 'items' in drawing:
        for j, item in enumerate(drawing['items'][:3]):  # Show first 3 items
            print(f"      Item {j}: {item[0]} - {item[1:]}")

# Also check text extraction with details
text_dict = page.get_text("dict")
print(f"\nText blocks: {len(text_dict.get('blocks', []))}")

for block_idx, block in enumerate(text_dict.get('blocks', [])):
    if block.get('type') == 0:  # Text block
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text = span.get('text', '')
                if 'strikethrough' in text.lower() or 'strike' in text.lower():
                    print(f"\nBlock {block_idx}, Span text: {repr(text)}")
                    print(f"  Font: {span.get('font')}")
                    print(f"  Flags: {span.get('flags')}")
                    print(f"  Bbox: {span.get('bbox')}")

doc.close()
