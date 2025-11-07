"""Test full PDF to Markdown conversion for case 02."""

from pathlib import Path
from unpdf.core import pdf_to_markdown

pdf_path = Path("tests/test_cases/02_text_formatting.pdf")
result = pdf_to_markdown(pdf_path)

print("FULL MARKDOWN OUTPUT:")
print("=" * 80)
print(result)
print("=" * 80)

# Show specific lines
lines = result.strip().split('\n')
for i, line in enumerate(lines):
    if 'bold' in line.lower() or 'italic' in line.lower():
        print(f"Line {i}: {repr(line)}")
