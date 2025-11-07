"""Debug strikethrough coordinate matching."""

import pdfplumber

pdf_path = "tests/test_cases/02_text_formatting.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    # Get text with coordinates
    chars = page.chars
    
    # Find text that should be struck through (based on markdown)
    print("Looking for 'This is strikethrough text' - searching all text:")
    for char in chars:
        text = char.get("text", "")
        if text.strip() and char.get('doctop', 0) > 340:  # Near the rect
            print(f"  '{text}': doctop={char.get('doctop'):.2f}, x0={char.get('x0'):.2f}, x1={char.get('x1'):.2f}, top={char.get('top'):.2f}, bottom={char.get('bottom'):.2f}")
    
    # Get rects
    print(f"\nRects ({len(page.rects)} total):")
    for i, rect in enumerate(page.rects):
        print(f"\nRect {i}:")
        print(f"  x0={rect.get('x0'):.2f}, y0={rect.get('y0'):.2f}")
        print(f"  x1={rect.get('x1'):.2f}, y1={rect.get('y1'):.2f}")
        print(f"  height={rect.get('height'):.2f}")
        print(f"  top={rect.get('top'):.2f}, bottom={rect.get('bottom'):.2f}")
        print(f"  doctop={rect.get('doctop'):.2f}")
        
        # Check if this could be the strikethrough line
        if rect.get('height', 0) < 2:  # Thin rect
            print(f"  -> THIN RECT - could be strikethrough")
    
    print(f"\nLines ({len(page.lines)} total):")
    for i, line in enumerate(page.lines):
        print(f"Line {i}: {line}")
