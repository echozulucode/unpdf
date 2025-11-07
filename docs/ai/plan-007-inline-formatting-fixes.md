# Plan 007: Fix Inline Formatting and Header Detection

## Problem Analysis

### Case 1: Header Level Detection Issues
- **Current Behavior**: H1 (14.3pt) → H5, H2 (12.0pt) → H6
- **Body size**: ~10pt
- **Font size ratios**: H1=1.43×, H2=1.20×
- **Root Cause**: Heading size ratios are too strict/high for PDFs generated with smaller fonts
- **Additional Issue**: Paragraphs are merging into single lines

### Case 2: Bold/Italic as Headers
- **Current Behavior**: Bold text at body size (12pt, flag=16) → classified as H6
- **Root Cause**: Text extraction splits bold/italic spans into separate blocks, then classifier sees "bold at body size" and classifies as header
- **Expected**: Bold/italic should remain inline formatting within paragraphs

## Root Causes

1. **Block Detector Issue**: PyMuPDF extracts each span (including inline formatting) as separate "lines" within blocks. Our block detector may be splitting these into separate blocks instead of keeping them together.

2. **Header Classification**: The `_detect_heading_level` function classifies ANY bold text as potential header, even when it's at body font size and mid-paragraph.

3. **Font Size Ratios**: The heading detection ratios (H1: 2.0-2.5×, H2: 1.5-1.8×) are calibrated for documents with large headers. Many PDFs use more subtle size differences.

4. **Paragraph Merging**: Line breaks within paragraphs are being preserved when they should be joined.

## Solution Strategy

### Priority 1: Fix Inline Formatting (Case 2)
**Goal**: Keep bold/italic text inline within paragraphs, not as separate blocks

**Approach**:
1. Modify `block_detector.py` to group consecutive spans within the same line/block
2. Track inline formatting (bold/italic) as span-level metadata
3. Update `document_renderer.py` to apply markdown formatting (`**bold**`, `*italic*`) when rendering
4. Only classify as HEADING if:
   - Font size is significantly larger than body (ratio > 1.15), OR
   - Block is standalone (not part of a paragraph with other text), AND
   - Block is bold/larger

### Priority 2: Improve Header Detection (Case 1)
**Goal**: Correctly detect header levels with more lenient thresholds

**Approach**:
1. Adjust heading size ratios to be more lenient:
   - H1: 1.4-2.5× (was 2.0-2.5×)
   - H2: 1.15-1.4× (was 1.5-1.8×)
   - H3: 1.05-1.15× (was 1.2-1.4×)
   - H4-H6: Use bold weight + position if size ≤ 1.05×

2. Add context awareness:
   - First bold/large text on page → likely H1
   - Bold text followed by body text → likely header
   - Bold text in mid-paragraph → inline formatting

### Priority 3: Fix Paragraph Separation
**Goal**: Merge lines within paragraphs but keep separate paragraphs distinct

**Approach**:
1. In `document_renderer.py`, detect paragraph breaks vs line wraps:
   - Line wrap: small Y-distance, similar X-alignment
   - Paragraph break: larger Y-distance or significant X-shift
2. Join wrapped lines with spaces
3. Keep paragraph breaks as double newlines

## Implementation Steps

### Step 1: Enhance Span Extraction with Inline Formatting
**File**: `unpdf/extractors/text_extractor.py`
- Modify `extract_text_blocks()` to preserve span-level formatting
- Add `spans` field to Block model with formatting flags (bold/italic/size)
- Group consecutive spans on same baseline into single block

### Step 2: Update Block Classification Logic
**File**: `unpdf/processors/block_classifier.py`
- Modify `_detect_heading_level()` to:
  - Check if block contains mixed formatting (indicates inline, not header)
  - Require minimum size ratio (>1.15×) for header classification
  - Consider block position and isolation
- Add `_has_inline_formatting()` helper method

### Step 3: Adjust Heading Size Ratios
**File**: `unpdf/processors/block_classifier.py`
- Update `HEADING_SIZE_RATIOS` to more lenient values
- Add fallback logic for bold-only headers (H4-H6)

### Step 4: Implement Inline Formatting Rendering
**File**: `unpdf/renderers/document_renderer.py`
- Modify `_render_text_block()` to check for spans with formatting
- Wrap bold spans with `**text**`
- Wrap italic spans with `*text*`
- Wrap bold+italic with `**_text_**`

### Step 5: Fix Paragraph Line Joining
**File**: `unpdf/renderers/document_renderer.py`
- Add method `_should_join_lines()` to detect line wraps vs paragraph breaks
- In paragraph rendering, join wrapped lines with space, keep breaks as double newline

### Step 6: Add Span Model
**File**: `unpdf/models/layout.py`
- Add `Span` dataclass with: text, bold, italic, font_size, font_name
- Add `spans: list[Span] | None` to Block model

### Step 7: Update Tests
- Add test for inline bold/italic formatting preservation
- Add test for correct header level detection with various size ratios
- Update existing tests that may expect old behavior

### Step 8: Test with Cases 1 & 2
- Run conversion on both test cases
- Verify headers are correctly leveled
- Verify bold/italic stays inline
- Verify paragraphs are properly separated

## Success Criteria

- ❌ Case 1: H1 → `#`, H2 → `##`, paragraphs properly separated
- ❌ Case 2: "**bold text**" and "*italic text*" remain inline, not headers
- ⏳ All existing tests pass
- ⏳ No regression in table/list/code detection

## Status

✅ Step 1-2: Added Span model to layout.py
✅ Step 3: Updated block classifier with lenient heading ratios and inline formatting detection
✅ Step 4: Updated document_renderer.py to render inline formatting
✅ Discovered current pipeline uses OLD path (core.py → headings.py), not document_processor
✅ Updated headings.py to:
  - Not classify bold text at body size as headers (requires ratio >= 1.15 or bold + >= 1.4)
  - Use lenient size ratios for header levels
  - Store bold/italic in ParagraphElement and apply in to_markdown()
✅ Updated core.py to merge consecutive ParagraphElements on same line

## Results

**Case 2 (inline formatting)**: ✅ WORKING
- Bold and italic text now rendered as `**bold**` and `*italic*`
- Inline formatting no longer classified as headers
- Paragraphs properly merged

**Case 1 (headers/paragraphs)**: ⚠️ MOSTLY WORKING
- Paragraphs merge correctly
- Headers detected but levels slightly off (H3 instead of H1, H3 instead of H2)
- Need to adjust size ratio thresholds

##Next Steps

1. ✅ Test and verify fixes work for cases 1 & 2
2. Fine-tune header level detection ratios if needed
3. Run full test suite to check for regressions
4. Update plan-001-implementation.md with completion status
