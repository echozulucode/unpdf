# Plan 006: Fix Issues Found in Test Suite

## Status: PROPOSED

## Overview
Based on test suite results, we have identified critical issues across multiple test cases. Average accuracy is 54.9% with only 1 test at 100% (code blocks). Key problems identified:

### Critical Issues

1. **Phantom Table Detection** (Highest Priority)
   - Tests 1, 3, 6: Detecting tables where none exist
   - Test 1: 0 expected, 11 detected
   - Test 3: 0 expected, 26 detected
   - Test 6: 0 expected, 22 detected
   - Cause: PDF text spans being incorrectly grouped as table cells

2. **Missing Table Detection** (High Priority)
   - Test 5: 10 tables expected, 0 detected
   - Tables are being rendered as plain text
   - Cause: Table detector not recognizing table structures

3. **Phantom Blockquote Detection** (High Priority)
   - Tests 1, 7: Detecting blockquotes where none exist
   - Test 1: 0 expected, 4 detected
   - Test 7: 0 expected, 5 detected
   - Cause: Indentation or alignment being misinterpreted

4. **Missing Horizontal Rules** (Medium Priority)
   - Test 8: 3 expected, 0 detected
   - Test 9: 1 expected, 0 detected
   - Cause: HR detector not finding horizontal lines in PDF

5. **List Item Detection Issues** (Medium Priority)
   - Test 3: 16 expected, 10 detected (62.5% recall)
   - Test 9: 10 expected, 1 detected (10% recall)
   - Cause: List markers not being properly identified

6. **Excess Paragraph Detection** (Medium Priority)
   - Multiple tests generating paragraphs that should be other elements
   - Test 5: 0 expected, 9 detected
   - Test 10: 0 expected, 11 detected
   - Cause: Table content being converted to paragraphs

7. **Header Level Issues** (Low Priority)
   - Test 2: 4 expected, 8 detected (likely doubling headers)
   - Test 7: 6 expected, 5 detected (one missing)

## Phases

### Phase 1: Fix Phantom Table Detection (CRITICAL)
**Goal:** Stop detecting tables where none exist

#### Step 1.1: Analyze Table Detection Logic
- Review `unpdf/processors/table_detector.py`
- Understand why text spans are being grouped as table cells
- Check table detection thresholds and heuristics

#### Step 1.2: Add Table Confidence Scoring
- Implement confidence scoring for table detection
- Require higher confidence for table classification
- Check for table-like patterns (grid structure, alignment)

#### Step 1.3: Fix False Positive Detection
- Add validation checks:
  - Minimum number of rows/columns
  - Consistent column alignment
  - Proper cell boundaries
  - Table-like spacing patterns

#### Step 1.4: Test and Validate
- Rerun tests 1, 3, 6 to verify phantom tables are gone
- Ensure test 5, 9, 10 still detect real tables

---

### Phase 2: Fix Missing Table Detection (HIGH)
**Goal:** Properly detect and render markdown tables

#### Step 2.1: Review Test 5 Output
- Analyze why tables aren't being detected
- Check if tables are being processed but not rendered
- Review table structure requirements

#### Step 2.2: Improve Table Structure Recognition
- Enhance detection of:
  - Column boundaries
  - Row separators
  - Header rows
  - Grid-like layouts

#### Step 2.3: Fix Table Rendering
- Ensure detected tables are properly converted to markdown
- Include alignment markers when detected
- Preserve cell content and structure

#### Step 2.4: Test and Validate
- Rerun test 5 (should detect all 10 tables)
- Verify tests 9, 10 (should maintain table detection)

---

### Phase 3: Fix Phantom Blockquote Detection (HIGH)
**Goal:** Stop detecting blockquotes where none exist

#### Step 3.1: Analyze Blockquote Detection Logic
- Review `unpdf/processors/blockquote.py`
- Understand why normal text is being marked as blockquotes
- Check indentation and alignment triggers

#### Step 3.2: Add Blockquote Validation
- Require stronger evidence for blockquote classification:
  - Check for actual indentation differences
  - Look for quote-like characteristics
  - Verify consistent indentation across lines

#### Step 3.3: Fix False Positives
- Adjust threshold for blockquote detection
- Add context checking (paragraphs aren't blockquotes)
- Disable blockquote detection if unreliable

#### Step 3.4: Test and Validate
- Rerun tests 1, 7 (should have 0 blockquotes)
- Verify test 6 still detects real blockquotes

---

### Phase 4: Fix Horizontal Rule Detection (MEDIUM)
**Goal:** Detect horizontal lines in PDFs

#### Step 4.1: Review HR Detection
- Check `unpdf/processors/horizontal_rule.py`
- Understand current detection method
- Analyze test 8 PDF structure

#### Step 4.2: Enhance HR Detection
- Look for:
  - Long horizontal lines in PDF
  - Repeated dash/underscore patterns
  - Visual separators
  - Border elements

#### Step 4.3: Test and Validate
- Rerun test 8 (should detect 3 HRs)
- Rerun test 9 (should detect 1 HR)

---

### Phase 5: Fix List Detection (MEDIUM)
**Goal:** Improve list item detection accuracy

#### Step 5.1: Analyze List Detection
- Review `unpdf/processors/list_detector.py`
- Check why list items are being missed
- Analyze test 3 and 9 structures

#### Step 5.2: Improve List Markers
- Enhance detection of:
  - Bullet points (•, -, *, etc.)
  - Numbered lists (1., 2., etc.)
  - Nested lists
  - List continuation

#### Step 5.3: Test and Validate
- Rerun test 3 (should detect all 16 items)
- Rerun test 9 (should detect all 10 items)

---

### Phase 6: Fix Paragraph Over-generation (MEDIUM)
**Goal:** Stop creating paragraphs from non-paragraph content

#### Step 6.1: Analyze Paragraph Logic
- Review how paragraphs are created
- Check why table content becomes paragraphs
- Review element classification

#### Step 6.2: Improve Element Classification
- Ensure tables are recognized before paragraphs
- Don't create paragraphs for table content
- Better distinguish element types

#### Step 6.3: Test and Validate
- Rerun tests 5, 10 (should have 0 paragraphs)
- Ensure other tests maintain proper paragraph counts

---

### Phase 7: Fix Header Detection (LOW)
**Goal:** Correct header level detection and count

#### Step 7.1: Analyze Header Issues
- Review why headers are doubled in test 2
- Check why one header is missing in test 7
- Review font-based header detection

#### Step 7.2: Fix Header Logic
- Prevent header duplication
- Ensure all headers are detected
- Verify level assignment

#### Step 7.3: Test and Validate
- Rerun tests 2, 7 (should have correct header counts)

---

### Phase 8: Comprehensive Testing
**Goal:** Validate all fixes across test suite

#### Step 8.1: Run Full Test Suite
- Execute all 10 tests
- Document accuracy scores
- Identify remaining issues

#### Step 8.2: Target 80% Average Accuracy
- Focus on tests below 80%
- Iteratively improve weak areas
- Balance precision vs recall

#### Step 8.3: Update Documentation
- Document known limitations
- Update test expectations
- Create troubleshooting guide

## Success Criteria

### Minimum Goals
- Average test accuracy: ≥ 80%
- No phantom tables in tests 1, 3, 6
- Table detection in test 5: ≥ 8/10 tables
- No phantom blockquotes in tests 1, 7
- All tests ≥ 60% accuracy

### Stretch Goals
- Average test accuracy: ≥ 90%
- All individual tests ≥ 75% accuracy
- Perfect scores on simple tests (1, 4, 8)

## Notes

- FontBBox warnings appear in Obsidian-generated PDFs (tests 2, 4, 9, 10) - non-critical
- Test 4 (code blocks) already at 100% - don't break it!
- Focus on high-impact issues first (phantom tables, missing tables)
- Some accuracy loss may be acceptable to fix false positives
