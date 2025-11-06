# Plan 007 - Phase 2 Start

## Date: 2025-11-06

## Current Status

### Overall Metrics
| Metric | Current | Target (Phase 2) |
|--------|---------|------------------|
| Average Accuracy | 68.8% | 75%+ |
| Tests ≥80% | 4/10 | 6/10 |
| Tests <60% | 4/10 | 2/10 |

### Test Results
| Test | Score | Status | Notes |
|------|-------|--------|-------|
| 1. basic_text | 83.3% | ✅ Good | Stable |
| 2. text_formatting | 62.5% | ⚠️  | Needs work |
| 3. lists | 83.7% | ✅ Good | Stable |
| 4. code_blocks | 100.0% | ✅ Perfect | Don't break! |
| 5. tables | 24.0% | ❌ Critical | 0/10 tables detected |
| 6. links_and_quotes | 41.4% | ❌ Critical | Missing blockquotes |
| 7. headings | 88.0% | ✅ Good | Stable |
| 8. horizontal_rules | 76.9% | ⚠️  | 0/3 HRs detected |
| 9. complex_document | 54.8% | ⚠️  | Multiple issues |
| 10. advanced_tables | 73.2% | ⚠️  | 7/7 tables detected but extra paragraphs |

### Completed Work

#### Phase 1: Phantom Table Detection ✅
- Disabled text-based table fallback (main fix)
- Strengthened validation filters
- Result: Eliminated all phantom tables in tests 1, 2, 3, 6

### Phase 2: Real Table Detection Strategy

**Problem:** Test 5 has 10 tables in PDF, but 0 detected with line-based method.

**Root Cause Analysis:**
- Pandoc/LaTeX PDFs often don't have visible borders
- Line-based detection (`vertical_strategy: "lines"`) requires visible lines
- Text-based fallback was disabled to prevent phantoms
- Need intelligent borderless table detection

**Approach Options:**

1. **Pattern-Based Text Analysis** (Recommended)
   - Analyze word positions for alignment patterns
   - Look for:
     - Multiple rows with same column count
     - Consistent column alignment (x-positions)
     - Regular spacing between columns
     - Header row (different font/size)
   - Confidence scoring before acceptance

2. **Hybrid with Confidence**
   - Use line-based for bordered tables (high confidence)
   - Use strict text-based with confidence scoring
   - Only accept tables with score > 0.75

3. **Machine Learning** (Future)
   - Train classifier on table vs non-table text blocks
   - Requires training data and infrastructure

### Next Steps

#### Step 2.1: Analyze Test 5 Manually ⏭️ NEXT
- Open `tests/test_cases/05_tables.pdf`
- Inspect table structures
- Understand why line-based detection fails
- Document table characteristics

#### Step 2.2: Implement Confidence-Scored Table Detector
- Create `_detect_text_tables_with_confidence()` method
- Implement alignment analysis
- Score based on:
  - Column alignment consistency
  - Row regularity
  - Cell content patterns
  - Header detection

#### Step 2.3: Integrate Hybrid Detection
- Try line-based first (existing)
- If no tables, try confidence-based text detection
- Apply strict validation to both

#### Step 2.4: Test and Tune
- Run Test 5 - target: 7-10 tables detected
- Ensure tests 1-3, 6 still have 0 phantom tables
- Tune confidence threshold

## Success Criteria (Phase 2)
- Test 5: 24% → 70%+ (detect 7-10 tables)
- Test 10: maintain or improve 73.2%
- Tests 1, 2, 3, 6: maintain 0 phantom tables
- Average: 68.8% → 75%+

## Notes
- Text-based detection is powerful but dangerous
- Need balance between precision (no phantoms) and recall (find real tables)
- Confidence scoring is key to this balance
- May need different strategies for Pandoc vs Obsidian PDFs
