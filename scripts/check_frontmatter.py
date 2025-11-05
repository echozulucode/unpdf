"""Check if YAML frontmatter exists in the PDF."""

import pymupdf
import sys

doc = pymupdf.open('example-obsidian/obsidian-input.pdf')
page = doc[0]

print('=== First 500 chars ===')
text = page.get_text('text')
print(text[:500])

print('\n=== All text spans (first 30) ===')
count = 0
for block in page.get_text('dict')['blocks']:
    if 'lines' in block:
        for line in block['lines']:
            for span in line['spans']:
                y = span['bbox'][1]
                txt = span['text']
                font = span['font']
                print(f'{txt!r:50s} @ y={y:6.1f} font={font}')
                count += 1
                if count >= 30:
                    break
            if count >= 30:
                break
    if count >= 30:
        break

doc.close()
