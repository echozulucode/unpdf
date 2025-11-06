# Plan 007: Test Suite Accuracy Fixes

## Status: IN PROGRESS

## Overview
Fix critical accuracy issues identified in test suite analysis. Current average accuracy is 54.9% with only 1/10 tests scoring 100%. Main issues are phantom tables (0 expected, 11-26 detected), missing real tables (10 expected, 0 detected), phantom blockquotes, and missing horizontal rules.

## Root Cause Analysis

### 1. Phantom Table Detection (Critical)
**Problem:** Test 1: 0 expected tables, 11 detected; Test 3: 0 expected, 26 detected; Test 6: 0 expected, 22 detected

**Root Cause:** 
- pdfplumber's text-based fallback table detection is too aggressive
- Using `vertical_strategy: "text"` and `horizontal_strategy: "text"` without sufficient validation
- No minimum row/column requirement being enforced despite having the fields
- Width ratio check (95%) allows nearly full-width tables
- `min_words_in_table: 2` is too low

**Evidence from output:**
```markdown
| Basic Text D         | ocument           |       |              |
|----------------------|-------------------|-------|--------------|
| This is a simple par | agraph with basic | text  | formatting.  |
```
Normal paragraph text split into table cells by word boundaries.

### 2. Missing Real Tables (Critical)
**Problem:** Test 5: 10 tables expected, 0 detected

**Root Cause:**
- Tables in Pandoc/LaTeX PDFs may not have visible lines
- Line-based detection (`vertical_strategy: "lines"`) fails
- Text-based fallback is being blocked by overly restrictive filters or not running
- Possible conflict: same filters blocking phantom tables also blocking real ones

### 3. Phantom Blockquotes (High Priority)  
**Problem:** Test 1: 0 expected, 4 detected; Test 7: 0 expected, 5 detected

**Root Cause:**
- `BlockquoteProcessor` likely misinterpreting normal indentation
- PDFs may have slight indents for paragraph formatting
- No validation of quote-like characteristics

**Evidence:**
```markdown
> > > This is a simple paragraph with basic text formatting.
```
Triple-nested blockquotes from normal text.

### 4. Missing Horizontal Rules
**Problem:** Test 8: 3 expected, 0 detected

**Root Cause:**
- HR detection looking for drawn lines via PyMuPDF drawings
- Pandoc PDFs may render HRs as text patterns (---, ***) not drawings
- Missing pattern-based detection for text-based HRs

## Implementation Phases

### Phase 1: Fix Phantom Table Detection ✓ COMPLETED

**Results:**
- Test 1: 11 tables → 0 tables ✓ (score: 26.1% → 50.0%)
- Test 3: 26 tables → 0 tables ✓ (score: 43.8% → 83.7%)
- Test 6: 22 tables → 0 tables ✓ (score: 38.3% → 89.7%)
- Average accuracy: 54.9% → 66.4%

**Changes made:**
1. Increased `min_words_in_table` from 2 to 6
2. Reduced `max_table_width_ratio` from 0.95 to 0.85
3. Added `min_rows` parameter (default: 3)
4. Increased `edge_min_length` from 3 to 10
5. **Disabled text-based table detection fallback** - this was the main cause
6. Now only uses line-based detection for bordered tables

#### Step 1.1: Strengthen table validation filters ✓
**Changes to `unpdf/processors/table.py`:**
1. Increase `min_words_in_table` from 2 to 6
2. Reduce `max_table_width_ratio` from 0.95 to 0.85 (85%)
3. Increase `min_columns` validation
4. Add minimum row requirement (at least 3 rows for valid table)
5. Add column alignment check: ensure columns are actually aligned
6. Add grid structure validation: check for consistent column widths

#### Step 1.2: Disable overly aggressive text-based fallback ✓
1. Remove or severely restrict the text-based detection fallback
2. Only use line-based detection for bordered tables
3. Add confidence scoring before accepting text-based tables

**Success Criteria:**
- Test 1: 0-1 tables detected (down from 11)
- Test 3: 0-2 tables detected (down from 26)
- Test 6: 0-1 tables detected (down from 22)
- Test 5: Still detect at least 5/10 real tables

---

### Phase 2: Fix Missing Real Table Detection

#### Step 2.1: Analyze Test 5 table structures
1. Manually inspect `tests/test_cases/05_tables.pdf`
2. Check if tables have visible borders or are text-aligned
3. Determine why pdfplumber isn't detecting them

#### Step 2.2: Add smarter text-based detection
1. Create confidence-scored table detector
2. Look for:
   - Multiple rows with same number of whitespace-separated columns
   - Consistent column alignment across rows
   - Header row (often bold/larger font)
   - Minimum 3 rows, 2 columns

3. Only accept tables with high confidence (>0.75)

#### Step 2.3: Hybrid approach
1. Try line-based first (high confidence)
2. Try smart text-based on remaining regions
3. Validate all detections with strict criteria

**Success Criteria:**
- Test 5: Detect at least 8/10 tables
- Tests 1, 3, 6: Maintain low phantom table count (0-2)

---

### Phase 3: Fix Phantom Blockquote Detection

#### Step 3.1: Analyze blockquote detection logic
Review `unpdf/processors/blockquote.py`:
1. Check indentation threshold
2. Check what constitutes "quote-like"
3. Understand current logic

#### Step 3.2: Add validation rules
Strengthen blockquote detection:
1. Require significant indentation (>20% of page width)
2. Check for quote markers or special formatting
3. Don't mark regular paragraphs as blockquotes
4. May need to disable blockquote detection entirely if too unreliable

#### Step 3.3: Test and refine
1. Ensure Test 1, 7 have 0 blockquotes
2. Verify Test 6 still detects real blockquotes (if any)

**Success Criteria:**
- Test 1: 0 blockquotes (down from 4)
- Test 7: 0 blockquotes (down from 5)
- Test 6: Maintain real blockquote detection

---

### Phase 4: Fix Horizontal Rule Detection

#### Step 4.1: Add pattern-based HR detection
Enhance `unpdf/processors/horizontal_rule.py`:
1. Detect text patterns: `---`, `***`, `___` (3+ repeated)
2. Detect long horizontal lines in drawings (current method)
3. Check for runs of underscores or dashes across page

#### Step 4.2: Integrate with text extraction
1. During text span processing, detect HR patterns
2. Mark spans as HR elements
3. Merge with drawing-based HRs

**Success Criteria:**
- Test 8: Detect 3/3 HRs
- Test 9: Detect 1/1 HR
- No false HR detection in other tests

---

### Phase 5: Improve List Detection

#### Step 5.1: Enhance list marker detection
Review `unpdf/processors/lists.py`:
1. Detect more bullet types: •, -, *, ◦, ▪, etc.
2. Handle nested lists better
3. Detect numbered lists: 1., a., i., etc.

#### Step 5.2: Fix list continuation
1. Handle multi-line list items
2. Detect indented continuation
3. Properly group list items

**Success Criteria:**
- Test 3: Detect 15-16/16 list items (up from 10)
- Test 9: Detect 8-10/10 list items (up from 1)

---

### Phase 6: Reduce Excess Paragraphs

#### Step 6.1: Improve element classification order
Ensure tables are detected before creating paragraphs:
1. Tables should be filtered from text spans first
2. Don't create paragraph elements for table content
3. Review element classification priority

**Success Criteria:**
- Test 5: 0-1 paragraphs (down from 9)
- Test 10: 0-2 paragraphs (down from 11)
- Maintain paragraph detection in other tests

---

### Phase 7: Fix Header Count Issues

#### Step 7.1: Debug header duplication
Test 2: 4 expected, 8 detected (doubling?)
1. Check if headers are being counted twice
2. Review font-based header detection
3. Check for duplicate elements in output

#### Step 7.2: Fix missing headers
Test 7: 6 expected, 5 detected
1. Check which header is missing
2. Verify font size thresholds
3. Check header level assignment

**Success Criteria:**
- Test 2: 4/4 headers detected
- Test 7: 6/6 headers detected

---

### Phase 8: Comprehensive Validation

#### Step 8.1: Run full test suite
Execute all 10 tests after each phase and document:
- Individual test scores
- Average accuracy
- Regressions (any tests that got worse)

#### Step 8.2: Iterative refinement
For each test below 80%:
1. Analyze specific failures
2. Implement targeted fixes
3. Retest

#### Step 8.3: Documentation
1. Update test expectations if needed
2. Document known limitations
3. Add troubleshooting guide for future issues

**Success Criteria:**
- Average accuracy: ≥ 80% (up from 54.9%)
- At least 7/10 tests ≥ 80%
- Test 4 (code blocks) remains at 100%
- No test below 60%

---

## Success Metrics

### Minimum Acceptable Results (Phase 8)
| Metric | Current | Target |
|--------|---------|--------|
| Average Accuracy | 54.9% | ≥80% |
| Tests ≥80% | 1/10 | ≥7/10 |
| Tests <60% | 6/10 | 0/10 |
| Phantom Tables (Test 1) | 11 | ≤1 |
| Phantom Tables (Test 3) | 26 | ≤2 |
| Real Tables (Test 5) | 0/10 | ≥8/10 |
| Phantom Blockquotes (Test 1) | 4 | 0 |

### Stretch Goals
- Average accuracy: ≥ 90%
- All tests ≥ 75%
- Perfect scores on simple tests (1, 4, 8)

## Notes
- Focus on precision over recall for false positives (tables, blockquotes)
- Some accuracy loss acceptable to eliminate phantom elements
- Test 4 (code blocks) is perfect - don't break it!
- FontBBox warnings are cosmetic only (Obsidian PDFs)
- Different PDF generators (Pandoc vs Obsidian) have different characteristics

## Testing Strategy
1. After each phase, run: `python scripts/run_all_tests.py`
2. Review `tests/test_cases/test_results.txt` for detailed breakdown
3. Check specific outputs in `tests/test_cases/XX_output.md`
4. Track accuracy deltas per phase
5. Validate no regressions in previously passing tests
