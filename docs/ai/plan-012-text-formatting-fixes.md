# Plan 012: Fix Text Formatting Issues in Test Case 02

## Status: In Progress

## Root Cause Identified

**CRITICAL FINDING**: Spans are being extracted correctly with individual formatting (bold, italic), but somewhere between extraction and element creation, consecutive spans on the same line are being MERGED, losing their individual formatting.

Investigation shows:
- **24 spans extracted** with correct individual formatting
- Only **12 elements created** - spans have been pre-merged
- Spans 3-7 (one line with mixed formatting) become ONE element losing formatting

## Problems Identified

### 1. Spans Being Pre-Merged (ROOT CAUSE - CRITICAL)
- **Problem**: Consecutive text spans on same line are merged before formatting can be applied
- **Evidence**: "This text contains" + "bold text" + "and" + "italic text" → single element
- **Root Cause**: Unknown merge happening between span extraction and element creation
- **Impact**: Loses all inline formatting (bold, italic, strikethrough boundaries)

### 2. Header Level Detection (CRITICAL)
- **Problem**: All H2 headers (`##`) are being detected as H1 (`#`)
- **Source**: `## Bold and Italic` 
- **Output**: `# Bold and Italic`
- **Root Cause**: Font size-based heading detection may not be calibrated correctly for relative sizes

### 3. Strikethrough Span Boundary (DEPENDS ON #1)
- **Problem**: Strikethrough applied to entire paragraph instead of just struck text
- **Source**: `This is ~~strikethrough text~~ in a paragraph.`
- **Output**: `~~This is strikethrough text in a paragraph.~~`
- **Root Cause**: Same as #1 - spans are being merged

### 4. Inline Code (WORKING) ✓
- Inline code detection works correctly

## Implementation Steps

### Step 1: Find and Fix Span Pre-Merging (CRITICAL)
**Files**: `unpdf/extractors/text.py` or `unpdf/core.py`

**Task**: Identify where spans are being merged before formatting can be applied

**Actions**:
1. Add detailed logging to trace span count through the pipeline
2. Find the merge point between extraction (24 spans) and elements (12 items)
3. Either:
   a. Prevent premature merging, OR
   b. Preserve formatting flags during merge, OR  
   c. Split merged spans back into formatted pieces

**Priority**: MUST FIX FIRST - blocks all inline formatting

### Step 2: Update Merge Function for Strikethrough  
**File**: `unpdf/core.py` line ~182-195

**Task**: Add strikethrough handling to existing merge logic

**Status**: ✓ COMPLETED - Added strikethrough formatting

### Step 3: Fix Header Level Detection
**Files**: `unpdf/processors/headings.py`

**Task**: Improve relative font size detection for headers

**Actions**:
1. Review heading classification logic
2. Check if median font size calculation is correct  
3. Implement relative sizing - H1 should be largest, H2 next, etc.
4. Consider font size ratios between heading levels

### Step 4: Add Regression Tests
**File**: `tests/test_text_extraction.py` or similar

**Task**: Ensure these issues don't reoccur

**Actions**:
1. Add test for bold/italic inline formatting preservation
2. Add test for correct header level detection
3. Add test for strikethrough span boundaries
4. Add test verifying span count through pipeline

## Success Criteria

Test case 02 output should match:
- H2 headers rendered as `##`
- Bold text as `**bold text**`
- Italic text as `*italic text*`
- Strikethrough only on struck portion: `This is ~~strikethrough text~~ in a paragraph.`
- Mixed formatting preserved: `This text contains **bold text** and *italic text*.`

## Debug Evidence

```
Spans extracted: 24
- Span 3: 'This text contains ' (plain)
- Span 4: 'bold text ' (is_bold=True)
- Span 5: 'and ' (plain)
- Span 6: 'italic text' (is_italic=True)
- Span 7: '.' (plain)

Elements created: 12  ← PRE-MERGED!
- Element 3: 'This text contains bold text a...' (single paragraph, no formatting)
```

## Notes

- Strikethrough **detection** works correctly
- Inline code works perfectly
- Span extraction with formatting works correctly
- **The bug is in span merging between extraction and element creation**
