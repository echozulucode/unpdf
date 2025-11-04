# Plan 004: MVP Verification - Obsidian Example

**Status:** In Progress  
**Created:** 2025-11-04  
**Goal:** Verify MVP quality using the Obsidian example and fix critical issues

## Overview

The Obsidian example provides a comprehensive test case with:
- YAML frontmatter
- Multiple header levels (H1-H6)
- Unordered, ordered, and checklist items
- Tables with alignment
- Code blocks (Python, JSON, Bash)
- Blockquotes
- Horizontal rules
- Links

Current conversion has multiple issues that need to be addressed for MVP quality.

## Current Issues Identified

### Critical Issues (Must Fix for MVP)

1. **Missing YAML Frontmatter**
   - Original has frontmatter with title, author, date
   - Conversion completely drops this metadata

2. **Broken Header Section**
   - Header explanation text is mangled
   - Spurious horizontal rule inserted after H2
   - Should read: "You can use one to six `#` symbols to create headers"
   - Currently reads: "`#  `\nYou can use one to six  \nsymbols to create headers."

3. **List Issues**
   - Spurious horizontal rule inserted between "Bananas" and "Oranges" in unordered list
   - Ordered list numbers all show as "1." instead of incrementing

4. **Table Order Reversed**
   - "Basic Table" and "Aligned Columns" are swapped
   - Table headers/content don't match their section titles

5. **Code Block Indentation**
   - Python code block loses indentation (docstring and return statement)
   - Makes code syntactically invalid

6. **Inline Code Handling**
   - Inline code text is moved after description instead of embedded within
   - Should be: "You can embed inline code using backticks, e.g. `print("Hello, world!")`."
   - Currently: "`print("Hello, world!") `\nYou can embed inline code using backticks, e.g.  \n."

7. **Extra Horizontal Rules**
   - Multiple spurious `---` inserted throughout document
   - Between code blocks, before tables, etc.

### Medium Priority (Should Fix)

8. **Blockquote Formatting**
   - Quote attribution should be on same line with blockquote marker
   - Currently split across two lines

9. **Trailing Whitespace**
   - Excessive trailing spaces on some lines

## Phase 1: Diagnostic Analysis ✓

**Objective:** Understand root causes of conversion issues

### Step 1.1: Add Debug Output ✓
- [x] Add verbose logging to conversion pipeline
- [x] Log reading order decisions
- [x] Log block classification
- [x] Log element merging decisions

### Step 1.2: Analyze Block Detection ✓
- [x] Check if YAML frontmatter is being detected
- [x] Check if inline code is being properly segmented
- [x] Check if list items are being properly grouped
- [x] Check if table detection is correct

### Step 1.3: Document Findings
- [x] Create diagnostic report
- [x] Identify which pipeline stages cause each issue
- [x] Prioritize fixes by impact

## Phase 2: Fix Critical Reading Order Issues

**Objective:** Fix text ordering and block grouping

### Step 2.1: Fix Header Section Text Flow
- [ ] Debug why header explanation text is broken
- [ ] Check text extraction order
- [ ] Fix span merging for inline code within paragraphs
- [ ] Ensure inline elements stay within their context

### Step 2.2: Fix List Grouping
- [ ] Debug spurious horizontal rules in lists
- [ ] Improve list item detection to prevent breaks
- [ ] Ensure nested list items stay grouped
- [ ] Fix ordered list numbering extraction

### Step 2.3: Fix Table Detection
- [ ] Debug why tables are in wrong order
- [ ] Check table caption association
- [ ] Ensure tables are matched to correct headers
- [ ] Verify table content extraction

**Success Criteria:**
- Lists render without spurious breaks
- Headers and paragraphs maintain proper text flow
- Tables appear under correct headings
- Ordered lists show correct numbering

## Phase 3: Fix Frontmatter Detection

**Objective:** Detect and preserve YAML frontmatter

### Step 3.1: Add Frontmatter Detection
- [ ] Detect YAML frontmatter at document start
- [ ] Parse frontmatter key-value pairs
- [ ] Store as document metadata

### Step 3.2: Render Frontmatter
- [ ] Output frontmatter at start of markdown
- [ ] Preserve original formatting
- [ ] Handle edge cases (missing values, etc.)

**Success Criteria:**
- YAML frontmatter appears in output
- Frontmatter values match original

## Phase 4: Fix Code Block Indentation

**Objective:** Preserve code formatting and indentation

### Step 4.1: Improve Code Block Extraction
- [ ] Debug indentation loss in code blocks
- [ ] Check if spans preserve leading whitespace
- [ ] Verify font detection for monospace
- [ ] Test with multiple code block languages

### Step 4.2: Fix Whitespace Preservation
- [ ] Preserve leading/trailing spaces in code
- [ ] Maintain proper line structure
- [ ] Handle tabs vs spaces consistently

**Success Criteria:**
- Python code block is syntactically valid
- Indentation matches original
- All code blocks maintain structure

## Phase 5: Fix Inline Element Handling

**Objective:** Keep inline code within paragraph context

### Step 5.1: Improve Inline Code Detection
- [ ] Detect backtick-enclosed inline code
- [ ] Keep inline elements with their parent paragraph
- [ ] Fix text reordering issues

### Step 5.2: Test Edge Cases
- [ ] Multiple inline code spans in one paragraph
- [ ] Inline code at start/end of paragraph
- [ ] Mixed inline formatting (bold, italic, code)

**Success Criteria:**
- Inline code appears in correct position
- Paragraph text flows naturally
- No orphaned inline elements

## Phase 6: Remove Spurious Horizontal Rules

**Objective:** Only output intentional horizontal rules

### Step 6.1: Debug Horizontal Rule Detection
- [ ] Check why extra horizontal rules appear
- [ ] Review horizontal rule detection logic
- [ ] Identify false positives

### Step 6.2: Fix Detection Logic
- [ ] Refine horizontal rule detection criteria
- [ ] Add context awareness (not in lists, etc.)
- [ ] Test with various document structures

**Success Criteria:**
- Only 7 horizontal rules appear (matching original)
- No spurious rules in lists or between code blocks
- Rules appear in correct positions

## Phase 7: Polish and Validation

**Objective:** Final cleanup and verification

### Step 7.1: Fix Minor Issues
- [ ] Fix blockquote attribution formatting
- [ ] Remove excessive trailing whitespace
- [ ] Clean up spacing around elements

### Step 7.2: Create Comparison Tool
- [ ] Build structured diff tool
- [ ] Compare semantic structure, not just text
- [ ] Generate quality metrics

### Step 7.3: Final Validation
- [ ] Run full conversion
- [ ] Compare against original
- [ ] Verify all critical issues resolved
- [ ] Document remaining known issues

**Success Criteria:**
- All critical issues resolved
- 90%+ structural similarity to original
- Document is readable and properly formatted

## Testing Strategy

### Regression Testing
- [ ] Create automated test for Obsidian example
- [ ] Run existing test suite after each phase
- [ ] Ensure no regressions in other test cases

### Quality Metrics
- [ ] Measure structural similarity (headers, lists, tables)
- [ ] Count formatting errors
- [ ] Validate markdown syntax
- [ ] Check code block validity

## Success Criteria for MVP

1. **Structural Accuracy:** All major document structures present (headers, lists, tables, code blocks)
2. **Text Fidelity:** Content matches original (no missing text, minimal reordering)
3. **Formatting Preservation:** Code is valid, lists are clean, tables are correct
4. **Metadata Handling:** YAML frontmatter preserved
5. **Readability:** Output is human-readable and properly formatted

## Out of Scope (Post-MVP)

- Perfect character-for-character reproduction
- Advanced table alignment optimization
- Image extraction and embedding
- Custom Obsidian syntax (callouts, etc.)
- Font style detection (bold, italic)
- Link URL resolution
- Complex nested structures

## Notes

- Focus on getting the core structure right
- Prioritize fixes by user impact
- Maintain backward compatibility with tests
- Document any architectural decisions
- Keep changes minimal and focused

## References

- Original: `example-obsidian/obsidian-input.md`
- PDF: `example-obsidian/obsidian-input.pdf`
- Current output: `example-obsidian/output-mvp.md`
- Comparison tool: `compare_output.py`
