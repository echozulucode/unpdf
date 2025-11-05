#!/usr/bin/env python3
"""Compare original markdown with PDF conversion output."""

import sys
from pathlib import Path

if len(sys.argv) >= 3:
    original = Path(sys.argv[1]).read_text(encoding="utf-8")
    output = Path(sys.argv[2]).read_text(encoding="utf-8")
else:
    original = Path("example-obsidian/obsidian-input.md").read_text(encoding="utf-8")
    output = Path("example-obsidian/output-mvp.md").read_text(encoding="utf-8")

print("=== CRITICAL ISSUES ===\n")

issues = []

# 1. YAML frontmatter missing
if "---\ntitle:" in original and "---\ntitle:" not in output:
    issues.append("❌ YAML frontmatter completely missing (lines 1-5)")

# 2. Checkbox artifacts in Headers section
if "`[ ] #  `" in output:
    issues.append("❌ Checkbox artifacts in Headers section (lines 8-10)")
    issues.append('   Expected: "You can use one to six # symbols to create headers."')
    issues.append(
        '   Got: "`[ ] #  `\\n- [ ] You can use one to six\\n- [ ] symbols to create headers."'
    )

# 3. Ordered list numbering
if "1. Install dependencies\n1. Build" in output:
    issues.append("❌ Ordered list numbering broken (lines 36-39)")
    issues.append('   All items numbered as "1." instead of 1, 2, 3, 4')

# 4. Tables swapped
orig_basic_pos = original.find("### Basic Table")
orig_aligned_pos = original.find("### Aligned Columns")
out_basic_pos = output.find("### Basic Table")
out_aligned_pos = output.find("### Aligned Columns")

if orig_basic_pos < orig_aligned_pos and out_basic_pos > out_aligned_pos:
    issues.append("❌ Table sections swapped (lines 49-63)")
    issues.append('   "Basic Table" should appear before "Aligned Columns"')

# 5. Inline code broken
if "You can embed inline code using backticks, e.g." in original:
    orig_idx = original.find("You can embed inline code")
    orig_section = original[orig_idx : orig_idx + 100]
    out_idx = output.find("You can embed inline code")
    if out_idx > 0:
        out_section = output[out_idx : out_idx + 100]
        if (
            '`print("Hello, world!")`' in orig_section
            and '`print("Hello, world!") `' in out_section
        ):
            issues.append("❌ Inline code formatting broken (lines 69-71)")
            issues.append("   Sentence structure corrupted")

# 6. Python code block
if "def greet(name: str) -> str:" in output:
    idx = output.find("def greet")
    section = output[idx - 50 : idx + 200]
    if '"""Return a greeting."""' not in section or section.count("\n") < 3:
        issues.append("❌ Python code block docstring on wrong line (line 79)")

# 7. Print statement outside code block
if output.count('`print(greet("Markdown"))`') > 0:
    idx = output.find('`print(greet("Markdown"))`')
    # Check if it's after the code block
    code_end = output.find("```", output.find("def greet"))
    if idx > code_end:
        issues.append(
            "❌ print(greet(...)) statement outside Python code block (line 82)"
        )
        issues.append("   Should be inside the ```python block")

# 8. JSON missing language identifier
json_idx = output.find('"name": "Sample Project"')
if json_idx > 0:
    section = output[max(0, json_idx - 50) : json_idx]
    if "```json" not in section and "```\n{" in section:
        issues.append("❌ JSON code block missing language identifier (line 86)")
        issues.append("   Should be ```json not just ```")

# 9. Links lost
if (
    "[Visit GitHub](https://github.com/)" in original
    and "Visit GitHub" in output
    and "[Visit GitHub]" not in output
):
    issues.append("❌ Link markdown syntax lost (line 119)")
    issues.append("   Expected: [Visit GitHub](https://github.com/)")
    issues.append("   Got: Visit GitHub (plain text)")

# 10. Horizontal rule missing before section 7
orig_hr_idx = original.find("## 7. Links")
orig_before = original[max(0, orig_hr_idx - 20) : orig_hr_idx]
out_hr_idx = output.find("## 7. Links")
out_before = output[max(0, out_hr_idx - 20) : out_hr_idx] if out_hr_idx > 0 else ""

if "---" in orig_before and "---" not in out_before:
    issues.append('❌ Horizontal rule missing before "7. Links and Images"')

for issue in issues:
    print(issue)

print("\n=== SUMMARY ===")
print(f"Total issues found: {len([i for i in issues if i.startswith('❌')])}")
print(f"\nOriginal: {len(original.split(chr(10)))} lines")
print(f"Output:   {len(output.split(chr(10)))} lines")
