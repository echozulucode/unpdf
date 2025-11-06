# Plan 007 - Phase 1-2 Progress Summary

## Date: 2025-11-06

## Current Status

### Overall Metrics
| Metric | Baseline | After Phase 1 | Target Phase 2 |
|--------|----------|---------------|----------------|
| Average Accuracy | 54.9% | 67.5% | 75%+ |
| Tests ≥80% | 1/10 | 4/10 | 6/10 |
| Tests <60% | 6/10 | 4/10 | 2/10 |

### Phase 1 Completion ✅

**Goal:** Eliminate phantom table detection

**Changes Made:**
1. Increased `min_words_in_table`: 2 → 6
2. Decreased `max_table_width_ratio`: 0.95 → 0.85
3. Added `min_rows` parameter (default: 3)
4. Increased `edge_min_length`: 3 → 10
5. **Disabled text-based table detection fallback**
6. Disabled blockquote detection (too many false positives in unpdf/core.py)

**Results:**
- Test 1: 26.1% → 83.3% (+57.2%) ✅
- Test 3: 43.8% → 83.7% (+39.9%) ✅
- Test 6: 38.3% → 41.4% (+3.1%) ⚠️
- Test 7: 64.0% → 88.0% (+24.0%) ✅
- Average: 54.9% → 67.5% (+12.6%)
- Phantom tables: ELIMINATED ✅

**Trade-offs:**
- Lost blockquote detection (Test 6 still low)
- Lost borderless table detection (Test 5 still at 24%)

### Phase 2: Next Steps

**Current Challenge:**
Test 5 has 10 tables with no visible borders (Pandoc/LaTeX generated).
Line-based detection finds 0 tables. Need word-position analysis.

**Implementation Plan:**

#### Option 1: Add Word-Position Table Detector (Recommended) ⏭️
Implement intelligent borderless table detection using word alignment analysis:

```python
def _detect_text_tables_with_confidence(page):
    1. Extract words from PDF
    2. Group by y-position (rows)
    3. Analyze column alignment patterns
    4. Score based on:
       - Column position consistency (±10px tolerance)
       - Row regularity (same column count)
       - Minimum 3 rows, 2 columns
       - Content validation (not all single chars)
    5. Only accept tables with confidence > 0.6
```

**Success Criteria:**
- Test 5: 24% → 70%+ (detect 7-10/10 tables)
- Tests 1, 3, 6: maintain 0 phantom tables
- Average: 67.5% → 75%+

#### Option 2: Hybrid pdfplumber Settings
Try text-based detection with even stricter validation:
- Require grid-like structure
- Validate cell content quality
- Check for visual separators

**Risk:** May still produce phantoms

### Next Actions

1. ✅ Restore Phase 1 fixes to table.py
2. ⏭️ Implement `_detect_borderless_tables()` method
3. ⏭️ Add confidence scoring logic  
4. ⏭️ Integrate as fallback after line-based detection
5. ⏭️ Test on Test 5 (should detect 7-10 tables)
6. ⏭️ Validate no new phantoms in Tests 1, 2, 3, 6

## Files Modified

### Phase 1:
- `unpdf/processors/table.py` - stricter table validation
- `unpdf/core.py` - disabled blockquote processing

### Phase 2 (Planned):
- `unpdf/processors/table.py` - add borderless table detector

## Notes

- Text-based pdfplumber detection is too aggressive without validation
- Word-position analysis gives us control over confidence scoring
- Need to balance precision (no phantoms) vs recall (find real tables)
- Different PDF generators have very different characteristics:
  - Pandoc/LaTeX: no table borders, clean alignment
  - Obsidian: uses visible borders, works with line-based
