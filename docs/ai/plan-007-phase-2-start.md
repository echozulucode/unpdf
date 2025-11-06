# Plan 007 - Phase 2 Start

## Date: 2025-11-06

## Current Status - Step 2.3 NEXT

### Overall Metrics
| Metric | Before Phase 2 | After Step 2.2 | Target (Phase 2) |
|--------|----------------|----------------|------------------|
| Average Accuracy | 68.8% | 72.1% | 75%+ |
| Tests ≥80% | 4/10 | 4/10 | 6/10 |
| Tests <60% | 4/10 | 3/10 | 2/10 |

### Test Results
| Test | Score | Status | Notes |
|------|-------|--------|-------|
| 1. basic_text | 83.3% | ✅ Good | Stable |
| 2. text_formatting | 62.5% | ⚠️  | Needs work |
| 3. lists | 83.7% | ✅ Good | Stable (phantom tables rejected) |
| 4. code_blocks | 100.0% | ✅ Perfect | Don't break! |
| 5. tables | 70.6% | ⚠️  | ✅ Major improvement! (was 24%) |
| 6. links_and_quotes | 41.4% | ❌ Critical | Missing blockquotes |
| 7. headings | 88.0% | ✅ Good | Stable |
| 8. horizontal_rules | 76.9% | ⚠️  | 0/3 HRs detected |
| 9. complex_document | 54.8% | ⚠️  | Multiple issues |
| 10. advanced_tables | 60.0% | ⚠️  | Needs investigation |

### Work Completed

#### Step 2.1: Analyze Test 5 ✅ COMPLETED
Analyzed Test 5 PDF structure:
- Pandoc PDF has 6 drawings but 0 line-based tables detected
- Tables are borderless (no visible lines)
- Words are aligned in columns (e.g., x=213, 279, 345 for 3-column table)
- Consistent row spacing (~12 pixels)
- pdfplumber's text-based detection finds 1 table with vertical/horizontal strategy="text"
- Our line-based detection finds 0 (correct - no borders)

#### Step 2.2: Implement Confidence-Scored Text Detector ✅ COMPLETED
**Implementation:**
Completely rewrote the text-based detection with a simpler, more robust approach:

1. **`_detect_text_tables_with_confidence()`**: Main entry point
   - Groups words by y-position into rows
   - Builds table candidates using `_build_table_candidate()`
   - Scores each candidate and returns high-confidence tables

2. **`_build_table_candidate()`**: Builds table from consecutive rows
   - Detects column structure from first row
   - Adds subsequent rows if they match the column pattern
   - Returns candidate if it has minimum rows

3. **`_detect_column_positions()`**: Gap-based column detection
   - Analyzes gaps between words to find column boundaries
   - Uses 10px minimum gap as column separator

4. **`_columns_match()`**: Validates column alignment
   - Checks if two rows have same number of columns
   - Verifies columns align within 15px tolerance

5. **`_calculate_table_confidence_v2()`**: Confidence scoring
   - Same column count across rows (0-0.3)
   - Minimum 2 columns required
   - Column alignment quality (0-0.4)
   - Sufficient rows (0-0.2)
   - Sufficient columns (0-0.1)
   - Reject list markers (returns 0.0)

6. **`_extract_table_from_candidate_v2()`**: Data extraction
   - Assigns words to nearest column
   - Joins words within each cell

**Results:**
- Test 5: 24% → 70.6% ✅ (target: 70%+)
- Average: 68.8% → 72.1% (target: 75%+, almost there!)
- Test 3 (lists): Maintained 83.7% (no phantom tables)
- 2 tables detected in Test 5 (correct count for first page)

**Known Issues:**
- Column boundaries not perfect (words sometimes split incorrectly)
- First table has wrong cell structure (multiple words per cell not recognized)
- Need to refine column detection to handle multi-word cells

**Success Criteria Met:**
- ✅ Test 5: 24% → 70.6% (met 70%+ target)
- ✅ Tests 1, 2, 3, 6: Maintained 0 phantom tables
- ⚠️  Average: 72.1% vs 75%+ target (close, 2.9% short)
