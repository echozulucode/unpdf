"""Debug script to check span extraction."""

from pathlib import Path
from unpdf.extractors.text import extract_text_with_metadata

pdf_path = Path("tests/test_cases/02_text_formatting.pdf")

# Extract with our code
spans = extract_text_with_metadata(pdf_path)

print("=" * 80)
print("SPANS containing 'This text contains':")
print("=" * 80)
for i, span in enumerate(spans):
    text = span.get('text', '')
    if 'This text contains' in text:
        print(f"\nSpan {i}:")
        print(f"  text: {repr(text)}")
        print(f"  is_bold: {span.get('is_bold', False)}")
        print(f"  is_italic: {span.get('is_italic', False)}")
        print(f"  y0={span.get('y0'):.2f}")
        
# Look for the individual parts
print("\n" + "=" * 80)
print("ALL SPANS on same y-coordinate as 'This text contains':")
print("=" * 80)
target_y = None
for span in spans:
    if 'This text contains' in span.get('text', ''):
        target_y = span.get('y0')
        break

if target_y:
    for i, span in enumerate(spans):
        if abs(span.get('y0', 0) - target_y) < 1:  # Same line
            print(f"\nSpan {i}:")
            print(f"  text: {repr(span.get('text', ''))}")
            print(f"  is_bold: {span.get('is_bold', False)}")
            print(f"  is_italic: {span.get('is_italic', False)}")
