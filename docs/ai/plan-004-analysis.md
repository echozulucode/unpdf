# Plan-004 Detection Issues Analysis

## Date: 2025-11-04

## Current Test Output vs Expected

### Issues Identified

1. **FRONTMATTER MISSING**
   - Expected: YAML frontmatter with title, author, date
   - Actual: Missing entirely
   - Cause: No frontmatter detection implemented

2. **INLINE CODE MISPLACED**
   - Expected: `#` inline within sentence
   - Actual: `` `#  ` `` on separate line, sentence broken
   - Section: Headers section intro
   - Cause: Inline code detection breaking sentence flow

3. **HORIZONTAL RULES MISPLACED**
   - Expected: Horizontal rules between major sections
   - Actual: Appearing within sections, breaking content flow
   - Multiple locations: After H2 Section, in middle of lists, etc.
   - Cause: Over-aggressive horizontal rule detection

4. **LIST INDENTATION WRONG**
   - Expected: 2-space indentation for nested list items
   - Actual: 4-space indentation
   - Section: Unordered List (Fuji, Gala)
   - Cause: Incorrect indentation multiplier

5. **LIST ITEM SEPARATOR**
   - Expected: "Oranges" as third top-level item
   - Actual: Horizontal rule between "Bananas" and "Oranges"
   - Cause: False positive horizontal rule detection

6. **ORDERED LIST NUMBERS**
   - Expected: Sequential numbering (1, 2, 3, 4)
   - Actual: All items numbered as 1
   - Cause: Markdown rendering would fix this, but original has proper numbers

7. **TABLE ORDER SWAPPED**
   - Expected: "Name/Role/Active/Notes" table first, then "Left/Center/Right" table
   - Actual: Reversed order
   - Cause: Reading order or table detection issue

8. **CODE BLOCK INDENTATION LOST**
   - Expected: 4-space indentation in Python code
   - Actual: No indentation
   - Section: Python code block
   - Cause: Indentation not preserved from PDF

9. **SPURIOUS HORIZONTAL RULES IN CODE SECTION**
   - Expected: Clean code blocks
   - Actual: `---` separators between code blocks
   - Cause: Over-detection of horizontal rules

10. **BLOCKQUOTE ENCODING ISSUE**
    - Expected: Smart quotes and em dash (", ", —)
    - Actual: Garbled characters (ô, ö, ù)
    - Cause: Character encoding not handled correctly

11. **SECTION 6 MISSING HORIZONTAL RULE**
    - Expected: Demonstration horizontal rule after text
    - Actual: Missing
    - Cause: Not detected or filtered out incorrectly

12. **STDERR NOISE IN OUTPUT**
    - Issue: FontBBox warnings appearing in output
    - Cause: Warnings not redirected to stderr properly

## Priority Ranking

### P0 (Critical - Breaks Structure)
1. Frontmatter detection
2. Horizontal rule over-detection
3. Table order issue
4. Inline code breaking sentences

### P1 (High - Correctness Issues)
5. List indentation (2-space not 4-space)
6. Ordered list numbering
7. Code block indentation
8. Character encoding (blockquotes)

### P2 (Medium - Polish)
9. Stderr warnings in output
10. Missing demonstration horizontal rule

## Root Causes

1. **No metadata extraction**: Need frontmatter detector
2. **Over-aggressive pattern matching**: Horizontal rules detected from visual artifacts
3. **Reading order issues**: Tables extracted in wrong order
4. **Text flow preservation**: Inline code breaks sentence continuity
5. **Whitespace handling**: Indentation not preserved correctly
6. **Character encoding**: Unicode characters not decoded properly from PDF

## Next Steps

1. Add frontmatter detection (check for key-value pairs at document start)
2. Improve horizontal rule detection (require visual evidence + position context)
3. Fix list indentation to use 2 spaces
4. Fix inline code to preserve sentence flow
5. Investigate table reading order
6. Improve character encoding handling
7. Preserve code block indentation
8. Fix stderr handling for warnings
