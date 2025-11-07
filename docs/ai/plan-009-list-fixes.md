# Plan 009: List Detection and Formatting Fixes ✅ COMPLETED

## Issues Identified in Test Case 3

### 1. Nested List Items Breaking Incorrectly ✅ FIXED
**Problem**: Nested items show as "- \nNested item 1" instead of "  - Nested item 1"
- The dash/bullet and text are being treated as separate elements
- Block #4 shows nested items with a bold dash "–" followed by regular text
- These are on the same line but being split

**Solution**: Added `_merge_spans_on_same_line()` function in core.py to merge spans with same y-coordinate before processing

### 2. Ordered Lists Using "1." Repeatedly ✅ FIXED
**Problem**: All ordered list items show as "1." instead of incrementing (1., 2., 3., ...)
- Current logic resets numbering or doesn't track item position
- Need to track list item sequence and increment numbers

**Solution**: Added `number` field to ListItemElement and list counter tracking in ListProcessor

### 3. Extra "1" at Bottom of Page ✅ FIXED
**Problem**: Block #11 contains just "1" which is likely a page number
- Position: (303.1, 694.9) - very close to bottom of page (792.0)
- Need to filter out page numbers based on position and context

**Solution**: Added `_filter_page_numbers()` function in text extraction that filters numeric text near page edges

### 4. Excessive Indentation ✅ FIXED
**Problem**: List items have 2 spaces of indentation instead of 0
- Top-level list items should have no indentation
- Nested items should have 2-4 spaces

**Solution**: Improved base_indent calculation to find leftmost list item x0 rather than global minimum x0

## Implementation Steps - All Completed

### Step 1: Fix Page Number Detection ✅ DONE
**File**: `unpdf/extractors/text.py`
- Added page number filtering based on:
  - Position near page edges (within 100 points of top/bottom)
  - Short text (1-4 characters)
  - Numeric content
- Filters applied before span processing

### Step 2: Fix List Item Line Continuation ✅ DONE
**File**: `unpdf/core.py`
- Added `_merge_spans_on_same_line()` to merge spans within 2 points vertically
- Added `_merge_span_group()` helper to combine text, bounding boxes, and formatting
- Spans merged before list processing to preserve list item integrity

### Step 3: Fix Ordered List Numbering ✅ DONE
**File**: `unpdf/processors/lists.py`
- Added `number` field to ListItemElement dataclass
- Added `list_counters` dict to track numbers per indent level
- Extract actual numbers from PDF text using regex
- Update counters as items are processed
- Reset counters when entering new section (via update_context)

### Step 4: Fix List Indentation Calculation ✅ DONE
**File**: `unpdf/core.py` and `unpdf/processors/lists.py`
- Calculate base_list_indent by finding minimum x0 of actual list items (not all spans)
- Improved `_calculate_indent_level()` with tolerance for base indent matching
- Top-level lists now have 0 spaces indentation
- Nested items properly indented at 2-space intervals

## Results

Test case 3 (03_lists.pdf) now produces correct output:
- ✅ Page number "1" filtered out
- ✅ Ordered lists numbered correctly: 1., 2., 3., 4.
- ✅ Nested items on single lines: "  - Nested item 1"
- ✅ Proper indentation: 0 spaces for top-level, 2 spaces for nested
- ✅ All list tests passing in test suite

### Output Quality
The converted output now matches the original markdown structure with only minor formatting differences (3 spaces vs 2 spaces for nested ordered lists, both valid).
