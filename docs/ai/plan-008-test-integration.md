# Plan 008: Test Case Integration and Regression Prevention

## Overview
Integrate test cases into the unit test suite to ensure conversion accuracy and prevent regressions. This plan addresses failures discovered during test execution.

## Test Results Summary

### Passing Tests (19/34 - 56%)
- ✅ Bold formatting correct (no spaces)
- ✅ Italic formatting correct (no spaces)
- ✅ Bold not converted to headers  
- ✅ Inline code preserved
- ✅ Nested lists preserved
- ✅ Tables detected
- ✅ Table alignment
- ✅ All 10 end-to-end conversion tests
- ✅ Formatting whitespace rules

### Failing Tests (15/34 - 44%)

#### Critical Issues
1. **Header Level Preservation** (Case 01)
   - Issue: H1 headers being converted to H2
   - Expected: `# Basic Text Document`
   - Actual: `## Basic Text Document`
   - Root cause: Heading detection using absolute font size instead of relative size

2. **Paragraph Separation** (Case 01)
   - Issue: Paragraphs being merged into single block
   - Expected: Separate paragraphs with blank lines
   - Actual: Multiple paragraphs merged with line breaks only

3. **Strikethrough Detection** (Case 02)
   - Issue: Strikethrough text not detected from PDF
   - Expected: `~~strikethrough text~~`
   - Actual: Plain text "strikethrough text"
   - Note: PDFs may use text annotations or special formatting

4. **List Detection** (Case 03)
   - Issue: Excessive indentation on list items
   - Expected: `- First item` or `1. First item`
   - Actual: `      - First item` (6 spaces)

5. **Heading Hierarchy** (Case 07)
   - Issue: No H1 headers in document
   - All headers detected as H2 or lower
   - Root cause: Relative heading detection thresholds

## Implementation Plan

### Phase 1: Fix Heading Level Detection ✅ (Next)
**Objective**: Ensure largest headings in document start at H1

**Steps**:
1. ✅ Review `processors/headings.py` heading classification
2. ✅ Implement relative sizing based on document font statistics
3. ✅ Ensure largest heading font → H1, scale others relatively
4. ✅ Add tests for heading hierarchy

**Files to modify**:
- `unpdf/processors/headings.py`
- `unpdf/extractors/font_analyzer.py` (if needed)

### Phase 2: Fix Paragraph Separation
**Objective**: Properly separate paragraphs with blank lines

**Steps**:
1. Review paragraph detection in `processors/headings.py`
2. Check vertical spacing between text blocks
3. Implement paragraph boundary detection based on spacing
4. Add tests for paragraph separation

**Files to modify**:
- `unpdf/processors/headings.py`
- `unpdf/extractors/text.py` (if needed)

### Phase 3: Improve List Indentation
**Objective**: Remove excessive indentation from list items

**Steps**:
1. Review list rendering in `renderers/markdown.py`
2. Fix indentation calculation for list levels
3. Ensure standard 2-space or 4-space indentation
4. Update nested list handling

**Files to modify**:
- `unpdf/renderers/markdown.py`
- `unpdf/processors/lists.py`

### Phase 4: Strikethrough Detection (Future)
**Objective**: Detect strikethrough text from PDFs

**Steps**:
1. Research PDF strikethrough representation
2. Check for text rendering mode flags
3. Implement strikethrough detection in text extractor
4. Add rendering support

**Note**: This may be challenging as PDFs don't have native strikethrough;
it's often implemented as a line over text or annotation.

**Files to modify**:
- `unpdf/extractors/text.py`
- `unpdf/renderers/markdown.py`

### Phase 5: Accuracy Metrics Integration
**Objective**: Run accuracy tests on all test cases

**Steps**:
1. Update accuracy tests to use correct import
2. Run accuracy calculations on all 10 test cases
3. Document baseline accuracy metrics
4. Set minimum accuracy thresholds for each case type

**Files to modify**:
- `tests/test_regression.py`
- Add accuracy reporting to test output

## Testing Strategy

### Regression Tests
- Tests run automatically with `pytest tests/test_regression.py`
- Each test case validated individually
- Output files generated for manual inspection

### Test Categories
1. **Basic Text** - Header levels, paragraph separation
2. **Text Formatting** - Bold, italic, inline code, strikethrough
3. **Lists** - Ordered, unordered, nested
4. **Tables** - Detection, alignment, formatting
5. **Code Blocks** - Inline and fenced code
6. **Links & Quotes** - URL detection, blockquotes
7. **Headings** - Hierarchy and relative sizing
8. **Horizontal Rules** - Section separators
9. **Complex Documents** - Multiple elements
10. **Advanced Tables** - Complex table structures

### Success Criteria
- All basic tests pass (Cases 01, 02, 07)
- 80%+ tests passing overall
- No regressions in existing functionality
- Output files match expected structure

## Current Status
- [x] Test suite created and integrated
- [x] Initial test run completed
- [x] Issues identified and documented
- [x] Phase 1: Header level detection (COMPLETED)
- [x] Phase 2: Paragraph separation (COMPLETED)
- [x] Phase 3: List indentation (COMPLETED)
- [ ] Phase 4: Strikethrough detection (DEFERRED - PDF limitation)
- [x] Phase 5: Accuracy metrics (COMPLETED - all accuracy tests passing)

## Recent Progress (Current Session)
1. ✅ Fixed calculate_element_accuracy import - added function to element_scorer.py and export in __init__.py
2. ✅ Fixed heading level detection - added max_font_size tracking to ensure largest heading is H1
3. ✅ Fixed paragraph separation - added vertical spacing detection in markdown renderer based on y0 coordinates
4. ✅ Fixed list indentation issue - calculate dynamic base_indent from document's minimum x0 value

## Tests Status
- **Passing: 33/34 (97%)**
- **Failing: 1/34 (3%)**
  - Strikethrough detection (known PDF limitation - see Phase 4 notes)

## Key Improvements Made

### 1. Heading Level Detection
**Problem**: H1 headers were being classified as H2 because heading levels were based on fixed ratio thresholds (e.g., 1.5x body text = H1). Documents where the largest heading was only 1.3x body text would never have H1 headers.

**Solution**: 
- Added `calculate_max_font_size()` function to track the largest font in the document
- Modified `HeadingProcessor.__init__()` to accept `max_font_size` parameter
- Updated `_calculate_level()` to check if font size is within 95% of max_font_size and assign H1 level
- This ensures the largest heading in any document becomes H1, with others scaled relatively

**Files Modified**:
- `unpdf/extractors/text.py` - Added `calculate_max_font_size()`
- `unpdf/processors/headings.py` - Added max_font_size parameter and logic
- `unpdf/core.py` - Calculate and pass max_font_size to HeadingProcessor

### 2. Paragraph Separation
**Problem**: Multiple paragraphs were being merged into a single block with only line breaks (`\n`) instead of blank lines (`\n\n`) between them.

**Solution**:
- Modified `render_elements_to_markdown()` in markdown renderer to track previous element type
- Added logic to check vertical distance (y0 coordinates) between consecutive ParagraphElements
- If vertical distance > 5 points, insert blank line between paragraphs
- This preserves inline formatting on same line while separating distinct paragraphs

**Files Modified**:
- `unpdf/renderers/markdown.py` - Updated spacing logic in render_elements_to_markdown()

### 3. List Indentation
**Problem**: List items had excessive indentation (6 spaces for top-level items) because the base_indent was hardcoded to 72.0 points (1 inch), which doesn't match all PDF generators. Pandoc/MiKTeX PDFs use ~134-146 point left margins.

**Solution**:
- Calculate dynamic base_indent from document's minimum x0 value
- Pass this to ListProcessor constructor instead of using default 72.0
- With document-specific base_indent, list items at the actual left margin get indent_level=0 (no indentation)
- Nested lists still properly increment indent levels based on their x0 offsets

**Files Modified**:
- `unpdf/core.py` - Calculate min_x0 from spans and pass to ListProcessor

### 4. Accuracy Metrics
**Problem**: `calculate_element_accuracy()` function was being imported but didn't exist.

**Solution**:
- Implemented `calculate_element_accuracy()` function in element_scorer.py
- Function uses ElementDetector to parse markdown into elements
- Uses ElementScorer to calculate precision/recall/F1 scores
- Returns F1 score as overall accuracy metric
- Added to __init__.py exports

**Files Modified**:
- `unpdf/accuracy/element_scorer.py` - Added calculate_element_accuracy()
- `unpdf/accuracy/__init__.py` - Added function to exports

## Notes
- Test cases located in `tests/test_cases/`
- Each case has: `.md` (source), `.pdf` (converted), `_output.md` (generated)
- Run specific test: `pytest tests/test_regression.py::TestBasicText -v`
- Generate coverage: `pytest tests/test_regression.py --cov=unpdf`
