# Plan 002: Conversion Quality Fixes

**Status**: In Progress  
**Created**: 2025-11-02  
**Updated**: 2025-11-02 22:47 UTC  
**Priority**: High

## Problem Analysis

Based on comparison of `example-obsidian/obsidian-input.md` (original) vs `example-obsidian/output.md` (converted from PDF), the following major issues were identified:

### 1. **Text Concatenation/Spacing Issues**
- **Problem**: Text runs together without proper spacing
- **Examples**:
  - "headers, bullet lists,tables" → missing space before "tables"
  - "ListOrdered List" → should be separate sections
  - "ApplesFujiGalaBananasOranges" → list items merged
  - "defgreet" → should be "def greet"
- **Root Cause**: PDF text extraction returns individual characters/words with position info, but our code doesn't properly reconstruct word/sentence boundaries
- **Impact**: Critical - makes output unreadable

### 2. **Table Extraction Creates Garbage**
- **Problem**: Tables extracted as malformed/split markdown tables
- **Examples**:
  - Simple tables split across multiple malformed table structures
  - Cell content broken mid-word ("Basic Tab le", "Aligned C olu mns")
  - Excessive empty columns/rows
  - Tables appear twice (once as mangled text, once as table)
- **Root Cause**: 
  - pdfplumber's table detection on Obsidian PDFs creates poor boundaries
  - Text extractor also captures table text, causing duplication
- **Impact**: Critical - tables completely unusable

### 3. **List Formatting Lost**
- **Problem**: Nested lists flattened, checkboxes lost, items merged
- **Examples**:
  - Nested "Fuji, Gala" under "Apples" → lost
  - Checkboxes "- [x]" → lost
  - Ordered list items merged into single line
- **Root Cause**: List detection only checks for markers, doesn't handle nesting or checkboxes
- **Impact**: High - list structure lost

### 4. **Code Block Formatting Destroyed**
- **Problem**: Code blocks lose formatting, line breaks, and language tags
- **Examples**:
  - Multi-line Python function → single line with no spaces
  - "defgreet(name:str)->str:"""Return a greeting."""returnf"Hello, {name}!"" 
  - JSON structure flattened
  - Bash script on one line
- **Root Cause**: 
  - Code detection identifies monospace font but doesn't preserve line breaks
  - Language tags not detected from fenced code blocks
- **Impact**: Critical - code completely unreadable

### 5. **Heading Level Detection Poor**
- **Problem**: Heading levels don't match original
- **Examples**:
  - "H1 - Top Level" detected as H3 instead of H1
  - Sub-headings like "Unordered List" detected as H5
  - Numbered sections "1. Headers" detected as list items not headings
- **Root Cause**: 
  - Only uses font size heuristic, not markdown syntax
  - Obsidian PDF doesn't preserve # symbols well
- **Impact**: Medium - structure degraded but readable

### 6. **Horizontal Rules Lost**
- **Problem**: `---` separators not detected
- **Examples**: All horizontal rules in original are missing
- **Root Cause**: Not implemented in any processor
- **Impact**: Low - cosmetic issue

### 7. **Blockquote Misdetection**
- **Problem**: Random text detected as blockquotes (using ">>>>>")
- **Examples**: "symbols to create headers" marked as blockquote
- **Root Cause**: Indent-based detection triggers on table cells or centered text
- **Impact**: Medium - adds incorrect formatting

### 8. **Links Not Preserved**
- **Problem**: Hyperlinks lose URL, only text remains
- **Examples**: "[Visit GitHub](https://github.com/)" → "Visit GitHub"
- **Root Cause**: Links not yet implemented (Phase 8 incomplete)
- **Impact**: Medium - lose clickable links

### 9. **YAML Frontmatter Lost**
- **Problem**: Document metadata not extracted
- **Examples**: Original has title/author/date frontmatter, output doesn't
- **Root Cause**: Text extraction starts after page 1 header, or YAML rendered as text
- **Impact**: Low - metadata preservation not critical for most use cases

## Root Cause Summary

The conversion quality issues stem from three architectural problems:

1. **Character-by-character extraction without proper text reconstruction**
   - PyMuPDF extracts text as individual characters with coordinates
   - Our code doesn't properly determine word boundaries
   - Need to implement smart spacing based on char positions

2. **Table detection conflicts with text extraction**
   - Same content extracted twice (as text and as table)
   - Need region-based exclusion: if table detected, skip text extraction in that bbox
   - Or: better table detection to avoid false positives

3. **Format detection relies on heuristics that don't work for Obsidian PDFs**
   - Obsidian's PDF export doesn't preserve markdown syntax visually
   - Font-based heuristics fail (code blocks, headings)
   - Need better structural analysis

## Resolution Plan

### Phase 1: Text Spacing Fix (Critical)
**Goal**: Properly reconstruct sentences and words from character stream

**Tasks**:
1. Modify `unpdf/extractors/text.py`:
   - Calculate horizontal gaps between characters
   - Insert space when gap > threshold (e.g., 0.5 * average char width)
   - Insert newline when vertical gap > threshold
   - Group characters into words, words into lines

2. Test on example-obsidian PDF
3. Verify: "headers, bullet lists, tables" appears correctly spaced

**Success Criteria**: Text reads naturally with proper spacing

---

### Phase 2: Table Deduplication (Critical) ✅ COMPLETED
**Goal**: Prevent tables from being extracted as both text and tables

**Status**: Completed - 2025-11-02

**Implementation**:
- Implemented Option A: Improved table detection with better filtering
- Added multiple validation checks in `unpdf/processors/table.py`:
  1. Max table width ratio (0.95) to reject full-page false positives
  2. Minimum column count (2) validation
  3. Empty cell ratio check (reject if >60% empty)
  4. Average cell length check (reject if <2 chars per cell)
  5. Changed default strategy from "lines_strict" to "lines" for better detection

**Results**:
- False positive tables eliminated (was detecting entire document as table)
- Two actual tables now correctly extracted: "Basic Table" and "Aligned Columns"
- Tables properly formatted as Markdown pipe tables
- Test command: `unpdf example-obsidian/obsidian-input.pdf -o example-obsidian/output-test2.md`

**Known Limitation**:
- ⚠️ **Tables still appearing as mangled text + properly formatted tables at end**
- Text extractor captures table content, creating duplication
- Need to implement bbox-based exclusion: skip text spans inside table regions

**Next Step**: Implement Option B - Region-based exclusion
- Extract table bboxes first
- Filter out text spans that fall within table regions
- This will prevent duplication while keeping proper table formatting

**Success Criteria**: ⚠️ Partial - Tables formatted correctly but duplicated with text

---

### Phase 3: Code Block Line Breaks (Critical)
**Goal**: Preserve line breaks and indentation in code blocks

**Tasks**:
1. Modify `unpdf/processors/code.py`:
   - Track Y-position of code spans
   - Detect line breaks (Y-position change)
   - Preserve indentation (X-position offset)
   - Store as multi-line CodeBlockElement

2. Modify `CodeBlockElement.to_markdown()`:
   - Use triple backticks with newlines
   - Preserve line structure

3. Test on Python/JSON/Bash examples

**Success Criteria**: Code blocks are formatted with proper line breaks and indentation

---

### Phase 4: List Nesting & Checkboxes (High)
**Goal**: Preserve list hierarchy and checkbox states

**Tasks**:
1. Modify `unpdf/processors/lists.py`:
   - Detect indentation level (X-position)
   - Support checkbox markers `[x]` and `[ ]`
   - Store nesting level in ListItemElement
   - Group consecutive list items into ListElement

2. Modify ListItemElement.to_markdown():
   - Add proper indentation (2 or 4 spaces per level)
   - Render checkboxes

3. Test on nested lists example

**Success Criteria**: Lists preserve nesting, checkboxes appear correctly

---

### Phase 5: Table Quality Improvement (Medium)
**Goal**: Better table structure detection

**Tasks**:
1. Add post-processing to TableProcessor:
   - Validate column consistency
   - Merge split cells
   - Remove excess whitespace
   - Detect alignment from cell content

2. Add table quality scoring:
   - Score based on: column consistency, content/empty ratio, structure
   - If score < threshold, don't extract as table

3. Test on example tables

**Success Criteria**: Tables properly formatted with correct columns

---

### Phase 6: Link Extraction (Medium)
**Goal**: Preserve hyperlinks with URLs

**Tasks**:
1. Modify `unpdf/extractors/text.py`:
   - Use PyMuPDF's link extraction API
   - Associate link annotations with text spans
   - Return link info with spans

2. Create `unpdf/processors/links.py`:
   - Detect link text spans
   - Format as `[text](url)`

3. Test on GitHub link example

**Success Criteria**: Links rendered as `[text](url)` format

---

### Phase 7: Horizontal Rule Detection (Low)
**Goal**: Detect and render horizontal dividers

**Tasks**:
1. Create `unpdf/processors/horizontal_rule.py`:
   - Detect long horizontal lines in PDF (using drawing operations)
   - Or: detect patterns like "---" or "___"
   - Create HorizontalRuleElement

2. Add to core.py pipeline

**Success Criteria**: `---` appears between sections

---

### Phase 8: Improved Heading Detection (Medium)
**Goal**: Better heading level accuracy

**Tasks**:
1. Enhance HeadingProcessor:
   - Add multi-factor scoring: font size, bold, position, whitespace
   - Detect numbered headings (1., 1.1., etc.)
   - Normalize levels (H1 for largest, not always H3)

2. Test and tune thresholds

**Success Criteria**: Heading levels match original more closely

---

## Priority & Sequencing

**Immediate (Critical issues)**:
1. Phase 1: Text Spacing → Makes output readable
2. Phase 3: Code Block Formatting → Makes code usable
3. Phase 2: Table Deduplication → Fixes major structural problem

**High Priority (Significant quality improvements)**:
4. Phase 4: List Nesting → Restores document structure
5. Phase 5: Table Quality → Improves table accuracy

**Medium Priority (Nice to have)**:
6. Phase 8: Better Headings → Improves navigation
7. Phase 6: Links → Restores interactivity

**Low Priority (Cosmetic)**:
8. Phase 7: Horizontal Rules → Visual improvement

## Testing Strategy

1. **Reference Document**: Use `example-obsidian/obsidian-input.pdf` as test case
2. **Ground Truth**: Compare to `example-obsidian/obsidian-input.md`
3. **Metrics**:
   - Text readability (manual inspection)
   - Structure preservation (heading count, list items)
   - Table accuracy (column count, cell content)
   - Code formatting (line count, indentation)

4. **Regression Testing**: After each phase, re-run all tests to ensure no breakage

## Differentiation from PyMuPDF

These fixes will differentiate unpdf from PyMuPDF4LLM:

1. **Better Text Reconstruction**: Smart spacing vs character-by-character
2. **Table Intelligence**: Quality scoring vs blind extraction
3. **Code Preservation**: Line breaks and indentation vs flattened
4. **List Structure**: Nesting and checkboxes vs flat bullets
5. **Obsidian-Friendly**: Handles Obsidian PDFs better (common use case)

## Success Metrics

**Phase 1 Success**: 
- No merged words (e.g., "lists,tables" → "lists, tables")
- Natural sentence flow

**Overall Success**:
- example-obsidian output 80%+ similar to original markdown
- All test cases pass visual inspection
- Users can read and use converted documents without manual cleanup

---

## Notes

- Start with Phase 1 (text spacing) as it's foundational
- Phases can be implemented in parallel if desired
- Each phase should include unit tests
- May need to adjust table detection settings per-PDF (future: auto-tuning)
