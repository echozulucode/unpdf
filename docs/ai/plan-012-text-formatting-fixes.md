# Plan 012: Fix Text Formatting Issues in Test Case 02

## Status: Partially Complete ✓

## Progress Summary

### ✅ FIXED: Header Level Detection
- **Problem**: All H2 headers (`##`) were being detected as H1 (`#`)
- **Root Cause**: Heading threshold was too low (>= 1.5× ratio for H1)
- **Solution**: Adjusted thresholds:
  - H1: >= 1.7× body font size (was 1.5×)
  - H2: >= 1.4× body font size (was 1.2×)
  - H3: >= 1.2× body font size (was 1.08×)
  - H4: >= 1.08× body font size (was 1.0×)
- **File**: `unpdf/processors/headings.py` lines 316-332
- **Result**: ✅ Test case 02 now outputs correct `##` headers

### ✅ FIXED: Strikethrough Key Name
- **Problem**: Strikethrough detector used wrong key name
- **Root Cause**: Detector set `span["strikethrough"]` but code checked `span["is_strikethrough"]`
- **Solution**: Changed detector to use `span["is_strikethrough"]` consistently
- **Files**: 
  - `unpdf/extractors/strikethrough.py` line 131
  - `unpdf/processors/headings.py` line 281
- **Result**: ✅ Strikethrough detection now works

### ✅ VERIFIED: Inline Formatting Works Correctly
- **Bold**: `**bold text**` ✓
- **Italic**: `*italic text*` ✓
- **Combined**: `***bold and italic***` ✓
- **Inline code**: `` `code` `` ✓
- **Merge logic**: `_merge_inline_code_into_paragraphs()` correctly preserves formatting ✓

### ⚠️ REMAINING: Strikethrough Span Boundary
- **Problem**: Strikethrough applies to entire paragraph instead of just struck words
- **Current Output**: `~~This is strikethrough text in a paragraph.~~`
- **Expected Output**: `This is ~~strikethrough text~~ in a paragraph.`
- **Root Cause**: PDF renderer (Obsidian) created ONE span for entire sentence
  - Strikethrough line crosses only middle portion
  - But detector marks entire span as struck
- **Required Solution**: Split spans based on strikethrough line boundaries
  - Detect horizontal extent of strike line (x0_line, x1_line)
  - Estimate character positions within span
  - Split span into: [before] [struck portion] [after]
  - Return 3 separate spans with individual formatting

## Implementation Steps

### ~~Step 1: Find and Fix Span Pre-Merging~~ ✅ NOT NEEDED
**Status**: ✓ COMPLETE - Merge logic was actually correct and preserves formatting

### ~~Step 2: Update Merge Function for Strikethrough~~ ✅ COMPLETE
**Status**: ✓ COMPLETE - Already has strikethrough handling (line 186-188 in core.py)

### ~~Step 3: Fix Header Level Detection~~ ✅ COMPLETE  
**Status**: ✓ COMPLETE - Adjusted thresholds in headings.py

### Step 4: Split Spans by Strikethrough Boundaries
**Status**: 🔲 TODO - More complex than initially thought

**Challenge**: 
- pdfplumber extracts characters but groups them into spans
- We know the line coordinates (x0_line, x1_line, y_line)
- We need to determine which characters are under the line
- Then split the span text accordingly

**Approach Options**:
1. **Character-level analysis**: Re-examine character positions to split spans
2. **Approximate split**: Use line x-coordinates to estimate character boundaries
3. **Accept limitation**: Document that partial-span strikethrough has limitations

**Recommendation**: Option 2 (approximate) is most practical:
- Calculate character width: `(x1_span - x0_span) / len(text)`
- Find which characters fall under line bounds
- Split text at those positions
- Create 3 spans with appropriate formatting

**File to modify**: `unpdf/extractors/strikethrough.py` - `detect_strikethrough_on_page()`

### ~~Step 5: Add Regression Tests~~ 
**Status**: 🔲 DEFERRED - Wait until strikethrough splitting is implemented

## Success Criteria

### ✅ Achieved
- [x] H2 headers rendered as `##`
- [x] Bold text as `**bold text**`
- [x] Italic text as `*italic text*`  
- [x] Mixed formatting preserved: `This text contains **bold text** and *italic text*.`
- [x] Strikethrough detection works and marks spans

### 🔲 Remaining
- [ ] Strikethrough only on struck portion: `This is ~~strikethrough text~~ in a paragraph.`

## Notes

- Test case 02 is now **95% correct** (only strikethrough boundary issue remains)
- All other inline formatting works perfectly
- The strikethrough boundary issue is an edge case that requires span splitting
- This is a known limitation of PDF format - no semantic markup for partial-span formatting
