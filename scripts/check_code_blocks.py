"""Check code block text in the PDF."""

import pymupdf

doc = pymupdf.open('example-obsidian/obsidian-input.pdf')

# Find code block sections
for page_num in range(len(doc)):
    page = doc[page_num]
    text_dict = page.get_text('dict')
    
    for block in text_dict['blocks']:
        if 'lines' not in block:
            continue
            
        for line in block['lines']:
            for span in line['spans']:
                txt = span['text']
                
                # Look for code block content
                if 'def greet' in txt or 'Return a greeting' in txt or 'return f' in txt:
                    font = span['font']
                    size = span['size']
                    bbox = span['bbox']
                    x0 = bbox[0]
                    print(f'Page {page_num + 1}:')
                    print(f'  Text: {txt!r}')
                    print(f'  Font: {font}')
                    print(f'  Size: {size:.1f}')
                    print(f'  X-position: {x0:.1f}')
                    print(f'  BBox: {bbox}')
                    print()

doc.close()
