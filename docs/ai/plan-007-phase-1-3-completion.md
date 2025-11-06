# Plan 007 Phase 1-3 Completion Summary

## Date: 2025-11-06

## Overview
Completed Phases 1 and 3 (partial) of Plan 007 to fix test suite accuracy issues.

## Results

### Overall Metrics
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Average Accuracy | 54.9% | 67.5% | **+12.6%** |
| Tests ≥80% | 1/10 | 4/10 | **+3 tests** |
| Tests <60% | 6/10 | 3/10 | **-3 tests** |

### Individual Test Results

| Test | Before | After | Change | Status |
|------|--------|-------|--------|--------|
| 1. basic_text | 26.1% | 83.3% | +57.2% | ✅ **Excellent** |
| 2. text_formatting | 62.5% | 62.5% | 0% | ⚠️  Unchanged |
| 3. lists | 43.8% | 83.7% | +39.9% | ✅ **Excellent** |
| 4. code_blocks | 100.0% | 100.0% | 0% | ✅ **Perfect** |
| 5. tables | 24.0% | 24.0% | 0% | ❌ Critical |
| 6. links_and_quotes | 38.3% | 41.4% | +3.1% | ❌ Needs work |
| 7. headings | 64.0% | 88.0% | +24.0% | ✅ **Excellent** |
| 8. horizontal_rules | 76.9% | 76.9% | 0% | ⚠️  Unchanged |
| 9. complex_document | 57.5% | 54.8% | -2.7% | ⚠️  Slight regression |
| 10. advanced_tables | 55.8% | 60.0% | +4.2% | ⚠️  Improved |

## Changes Made

### Phase 1: Fix Phantom Table Detection ✅ COMPLETED

**Problem:** Tests 1, 3, 6 had 11-26 phantom tables (0 expected)

**Solution:**
1. Disabled text-based table detection fallback (main fix)
2. Increased `min_words_in_table`: 2 → 6
3. Decreased `max_table_width_ratio`: 0.95 → 0.85
4. Added `min_rows` parameter (default: 3)
5. Increased `edge_min_length`: 3 → 10

**Files Modified:**
- `unpdf/processors/table.py`

**Results:**
- Test 1: 11 tables → 0 tables ✅ (26.1% → 83.3%)
- Test 3: 26 tables → 0 tables ✅ (43.8% → 83.7%)  
- Test 6: 22 tables → 0 tables ✅ (38.3% → 41.4%)

### Phase 3: Fix Phantom Blockquote Detection ⚠️ PARTIALLY COMPLETED

**Problem:** Tests 1, 7 had phantom blockquotes (level-3 nesting from normal paragraphs)

**Attempted Solution #1:** Increase quote threshold (15pt → 50pt)
- **Result:** Broke real blockquote detection in Test 6 (89.7% → 48.3%)

**Attempted Solution #2:** Moderate threshold (15pt → 25pt) with context
- **Result:** Still issues balancing false positives vs false negatives

**Final Solution:** Temporarily disable blockquote detection
- Added TODO comment in `unpdf/core.py`
- Blockquotes need smarter detection (e.g., looking for quote patterns, markdown conventions in PDF)

**Files Modified:**
- `unpdf/core.py` - commented out blockquote processing
- `unpdf/processors/blockquote.py` - attempted improvements (currently unused)

**Results:**
- Test 1: 4 blockquotes → 0 blockquotes ✅ (50.0% → 83.3%)
- Test 7: Phantom blockquotes reduced ✅ (64.0% → 88.0%)
- Test 6: Lost real blockquote detection ❌ (needs reimplementation)

## Issues Identified

### 1. Missing Real Tables (Test 5: 24.0%)
**Problem:** 10 tables expected, 0 detected
- Line-based detection fails on LaTeX/Pandoc PDFs
- Text-based detection was disabled to fix phantoms
- **Need:** Smarter hybrid detection

### 2. Missing Blockquotes (Test 6: 41.4%)
**Problem:** 10 blockquotes expected, 0 detected (disabled)
- Current detection too primitive (indent-based only)
- **Need:** Better heuristics:
  - Check for markdown-style `>` patterns if present
  - Look for quote formatting indicators
  - Require consistent indentation across multiple lines

### 3. Missing Horizontal Rules (Test 8: 76.9%)
**Problem:** 3 HRs expected, 0 detected
- Only detects drawn lines via PyMuPDF
- **Need:** Pattern-based detection for `---`, `***`, `___`

### 4. Header Count Issues (Test 2: 62.5%)
**Details:** 4 expected, 8 detected (doubling?)
- Needs investigation

### 5. Complex Document (Test 9: 54.8%)
- Multiple issues: missing lists, blockquotes, HRs
- Regression from 57.5% (investigate)

## Next Steps

### High Priority
1. **Phase 2: Fix Missing Real Table Detection**
   - Implement confidence-scored hybrid detection
   - Smart text-based detection for borderless tables
   - Target: Test 5 from 24% to 70%+

2. **Phase 3 (Continued): Reimplementimpl Blockquote Detection**
   - Pattern-based detection (look for `>` markers)
   - Multi-line consistency checks
   - Target: Test 6 from 41% to 70%+

3. **Phase 4: Fix Horizontal Rule Detection**
   - Add pattern detection (`---`, `***`, etc.)
   - Target: Test 8 from 76.9% to 95%+

### Medium Priority
4. **Investigate Test 2 Header Duplication**
5. **Fix Test 9 Regression**

## Success So Far
- ✅ Eliminated ALL phantom tables (huge win!)
- ✅ 4 tests now above 80% (was 1)
- ✅ Test 1 from worst (26%) to excellent (83%)
- ✅ Test 3 nearly doubled (44% → 84%)
- ✅ Test 7 from 64% to 88%
- ✅ Maintained 100% on code blocks

## Challenges
- Precision vs Recall tradeoff
  - Fixing phantom tables broke real table detection
  - Fixing phantom blockquotes broke real blockquote detection
- Need smarter, context-aware detection
- Different PDF generators (Pandoc vs Obsidian) have very different characteristics

## Recommendation
Continue with Phase 2 (table detection) as it has the biggest potential impact (Test 5 stuck at 24%).
