# Plan 009: Strike-Through Detection Implementation

## Overview
Implement strike-through text detection using heuristic line/rect overlay detection with pdfplumber. This will enable proper rendering of struck-through text in markdown output as `~~text~~`.

## Background
PDF doesn't have a native "strikethrough" text attribute. Strike-through appears as:
1. Text Markup annotation `/StrikeOut` (requires pypdf)
2. Thin vector path (line/rect) drawn across text (detectable with pdfplumber)
3. Baked into image (not detectable)

We'll focus on method #2 (heuristic detection) as it works with most generated PDFs and aligns with our current pdfplumber-based approach.

## Status
- [ ] Not started

---

## Phase 1: Core Strike-Through Detection

### Step 1.1: Create Strike-Through Detector Module
**Goal:** Implement the core detection logic for identifying struck text.

**Tasks:**
- Create `unpdf/core/strikethrough_detector.py`
- Implement `is_struck_word()` function with configurable parameters:
  - `y_band_frac`: Vertical band where strike line sits (default: 0.35-0.65)
  - `min_cover`: Minimum horizontal overlap (default: 0.6)
  - `max_thickness_frac`: Maximum line thickness as fraction of word height (default: 0.08)
- Implement horizontal coverage calculation
- Check both lines and flat rectangles
- Add type hints and docstrings (Google style)

**Success Criteria:**
- Function correctly identifies words with overlapping lines/rects
- Configurable thresholds for tuning
- Clean, documented code

### Step 1.2: Enhance PDFElement with Strike-Through Property
**Goal:** Add strike-through tracking to PDFElement data structure.

**Tasks:**
- Add `is_strikethrough: bool = False` field to `PDFElement` dataclass
- Update `PDFElement.__repr__()` to show strike-through status
- Update debug structure output to include strike-through indicator

**Success Criteria:**
- PDFElement can track strike-through state
- Debug output shows strike-through status clearly

---

## Phase 2: Integration with Extraction Pipeline

### Step 2.1: Integrate Detection into Enhanced Extractor
**Goal:** Connect strike-through detection to the extraction pipeline.

**Tasks:**
- Import `strikethrough_detector` in `enhanced_extractor.py`
- In `_extract_from_page()`, after extracting words:
  - Get `page.lines` and `page.rects`
  - For each word, call `is_struck_word()`
  - Store result in a lookup dict `{word_id: is_struck}`
- When creating PDFElements from words, set `is_strikethrough` field
- Ensure character-level elements inherit strike-through from parent word

**Tasks (Character-level detection option):**
- Optionally implement character-level detection for higher precision
- Group chars by word, check if majority have crossing line
- Mark word as struck only if >=70% of chars are crossed

**Success Criteria:**
- Strike-through detection runs during extraction
- PDFElements correctly marked with strike-through status
- No performance degradation

### Step 2.2: Handle Strike-Through in Text Reconstruction
**Goal:** Preserve strike-through information through text flow analysis.

**Tasks:**
- Review `text_flow_analyzer.py` - ensure strike-through property propagates
- Review block formation - strike-through should be preserved in blocks
- Ensure inline elements maintain strike-through state

**Success Criteria:**
- Strike-through property maintained through all analysis stages
- Block elements know which text is struck

---

## Phase 3: Markdown Output

### Step 3.1: Implement Strike-Through in Markdown Generator
**Goal:** Output strike-through text with proper markdown syntax.

**Tasks:**
- Modify `markdown_generator.py` to handle strike-through
- When processing inline elements with `is_strikethrough=True`:
  - Wrap text with `~~` delimiters
  - Example: `~~struck text~~`
- Handle nested formatting (e.g., bold + strikethrough: `**~~text~~**`)
- Handle strike-through across multiple elements
- Add logic to merge adjacent struck elements

**Success Criteria:**
- Struck text outputs as `~~text~~`
- Nested formatting works correctly
- No extra spaces inside delimiters

### Step 3.2: Handle Edge Cases
**Goal:** Ensure robust handling of complex scenarios.

**Tasks:**
- Test and fix: Strike-through with bold/italic
- Test and fix: Strike-through across word boundaries
- Test and fix: Partial word strike-through (treat as whole word)
- Test and fix: Strike-through in headers, lists, tables
- Add configuration option to disable strike-through detection

**Success Criteria:**
- All edge cases handled gracefully
- No crashes or malformed output
- Feature can be toggled via config

---

## Phase 4: Testing and Validation

### Step 4.1: Create Unit Tests
**Goal:** Test strike-through detection logic.

**Tasks:**
- Create `tests/test_strikethrough_detector.py`
- Test `is_struck_word()` with:
  - Word with crossing line (should detect)
  - Word with line above/below (should not detect)
  - Word with thick rect (should not detect)
  - Word with partial coverage (should not detect)
  - Word with no lines (should not detect)
- Test edge cases for thresholds

**Success Criteria:**
- All unit tests pass
- Good test coverage for detection logic

### Step 4.2: Add Integration Tests
**Goal:** Test strike-through through full pipeline.

**Tasks:**
- Add to `tests/test_cases/`:
  - `case_11_strikethrough.md` with various strike-through examples:
    - Simple struck text
    - Struck bold text
    - Struck italic text
    - Struck text in lists
    - Multiple struck words in sequence
- Generate PDF (Obsidian or Pandoc)
- Add to `test_conversion_cases.py`
- Verify accuracy detection handles strike-through

**Success Criteria:**
- Integration tests pass
- Strike-through detected and rendered correctly
- Accuracy metrics include strike-through

### Step 4.3: Update Existing Test Cases
**Goal:** Verify strike-through works with existing examples.

**Tasks:**
- Re-run all test cases
- Check `case_02_obsidian_basic.md` - has strike-through examples
- Update expected output if needed
- Verify accuracy scores improve for case 2

**Success Criteria:**
- All existing tests still pass
- Case 2 shows improved accuracy
- No regressions

---

## Phase 5: Tuning and Optimization

### Step 5.1: Analyze False Positives/Negatives
**Goal:** Tune detection parameters for best results.

**Tasks:**
- Run on all test cases
- Identify false positives (non-struck text detected as struck)
- Identify false negatives (struck text not detected)
- Adjust default thresholds:
  - `y_band_frac`
  - `min_cover`
  - `max_thickness_frac`
- Consider color-based filtering if needed

**Success Criteria:**
- Minimal false positives and negatives
- Good balance of precision and recall

### Step 5.2: Performance Testing
**Goal:** Ensure no significant performance impact.

**Tasks:**
- Profile extraction with strike-through detection
- Optimize if needed (e.g., spatial indexing for lines/rects)
- Document performance characteristics

**Success Criteria:**
- <10% performance impact on extraction
- Acceptable for production use

---

## Phase 6: Documentation

### Step 6.1: Update Documentation
**Goal:** Document strike-through detection feature.

**Tasks:**
- Update README.md with strike-through support
- Add section to conversion guide explaining detection
- Document configuration options
- Add troubleshooting tips for strike-through issues
- Update CHANGELOG.md

**Success Criteria:**
- Complete documentation
- Users understand how feature works
- Configuration options documented

### Step 6.2: Update Debug Output Guide
**Goal:** Help users debug strike-through detection.

**Tasks:**
- Update debug structure documentation
- Explain how to read strike-through indicators
- Add examples of struck text in debug output
- Document how to tune detection parameters

**Success Criteria:**
- Debug output clearly shows strike-through detection
- Users can troubleshoot detection issues

---

## Technical Notes

### Detection Algorithm
```python
# Pseudo-code
for each word in page:
    word_box = (x0, x1, top, bottom)
    word_middle = top + 0.35*height to top + 0.65*height
    
    for each line/rect:
        if line is thin (< 8% of word height):
            if line crosses word horizontally (>60% overlap):
                if line is in middle vertical band:
                    mark word as struck
```

### Markdown Output
```markdown
Regular text ~~struck text~~ more text
**bold ~~struck bold~~** text
```

### Configuration Options
```python
# In unpdf config
strikethrough_detection:
    enabled: true
    y_band_frac: [0.35, 0.65]
    min_coverage: 0.6
    max_thickness_frac: 0.08
```

---

## Risks and Mitigations

**Risk:** False positives from table borders or underlines
**Mitigation:** Tune vertical band to avoid bottom/top regions; optionally filter by color

**Risk:** False negatives from unusual strike-through styles
**Mitigation:** Make thresholds configurable; document limitations

**Risk:** Performance impact from checking all words against all lines
**Mitigation:** Spatial indexing; only check lines/rects near word bounding box

**Risk:** Conflicts with other formatting (bold, italic)
**Mitigation:** Careful ordering of markdown delimiters; test all combinations

---

## Success Metrics

- Strike-through detection works on Obsidian-generated PDFs (case 2)
- Accuracy score for case 2 improves significantly
- Test case 11 (dedicated strike-through test) achieves >95% accuracy
- No false positives in other test cases
- Feature can be disabled if needed
- Performance impact <10%

---

## Follow-up Considerations

1. **Annotation-based detection:** If needed, add pypdf integration for `/StrikeOut` annotations
2. **Character-level detection:** Implement if word-level proves insufficient
3. **Color filtering:** Add if false positives are an issue
4. **Underline detection:** Similar approach could detect underlines
5. **Visual validation:** Tool to visualize detected strike-through regions on PDF
