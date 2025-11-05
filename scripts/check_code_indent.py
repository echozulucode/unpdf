"""Check code block indentation handling."""

import pymupdf

doc = pymupdf.open('example-obsidian/obsidian-input.pdf')
page = doc[2]  # Page 3

print('=== Python Code Block Spans ===')
text_dict = page.get_text('dict')

in_code_block = False
for block in text_dict['blocks']:
    if 'lines' not in block:
        continue
        
    for line in block['lines']:
        for span in line['spans']:
            txt = span['text']
            font = span['font']
            
            # Check if we're in code block area
            if 'def greet' in txt:
                in_code_block = True
            
            if in_code_block and ('def ' in txt or 'return' in txt or '"""' in txt or 'print(greet' in txt):
                x0 = span['bbox'][0]
                y = span['bbox'][1]
                print(f'{txt!r:40s} x={x0:6.1f} y={y:6.1f} font={font}')
            
            if 'print(greet' in txt:
                in_code_block = False

doc.close()
