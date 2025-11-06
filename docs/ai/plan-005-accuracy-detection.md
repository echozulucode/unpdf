# Plan 005: Element-Level Accuracy Detection

## Overview
Implement element-level accuracy detection to measure the quality of PDF-to-Markdown conversion. This system will compare the extracted elements against ground truth (when available) and provide detailed metrics on conversion accuracy.

## Background
Element-level accuracy detection is a standard practice in document conversion and OCR systems. It's typically offered as an **optional feature** that can be enabled via a flag, because:

1. **Performance Impact**: Requires additional processing and sometimes reverse-rendering
2. **Use Cases Vary**: Production pipelines may not need accuracy metrics, while validation/testing does
3. **Ground Truth Requirement**: Most useful when you have ground truth to compare against

Common industry approaches:
- **Development/Testing**: Always enabled to track quality improvements
- **Production**: Disabled by default, enabled via `--validate` or `--accuracy` flag
- **Benchmarking**: Enabled for specific test suites with known ground truth

## Goals
1. Implement element-level accuracy detection system
2. Support multiple accuracy metrics (element detection, classification, content)
3. Provide optional ground truth comparison
4. Generate detailed accuracy reports
5. Make it easy to use for testing and validation

## Implementation Phases

### Phase 1: Core Accuracy Metrics Framework ✅ (Baseline exists)
**Status**: Basic metrics in `baseline_metrics.json` exist

**Goal**: Establish the foundation for accuracy measurement

**Tasks**:
1. ✅ Create metrics data structures (already exists in baseline_metrics.json)
2. Design accuracy report format
3. Implement accuracy calculator base class
4. Add CLI flag `--accuracy` or `--validate`

**Files to modify**:
- `unpdf/core/metrics.py` (new)
- `unpdf/cli/main.py`

### Phase 2: Element Detection Accuracy
**Goal**: Measure how well we detect and extract elements from the PDF

**Metrics to implement**:
- **Precision**: Percentage of detected elements that are correct
- **Recall**: Percentage of actual elements that were detected
- **F1 Score**: Harmonic mean of precision and recall
- **Element Counts**: Actual vs detected counts by type (headers, paragraphs, tables, lists)

**Tasks**:
1. Implement element counting and classification
2. Create element type mapping/normalization
3. Build element detection scorer
4. Add element-level comparison logic

**Files to create**:
- `unpdf/core/accuracy/element_detector.py`
- `unpdf/core/accuracy/element_scorer.py`

**Files to modify**:
- `unpdf/core/metrics.py`

### Phase 3: Content Accuracy
**Goal**: Measure the accuracy of extracted text content

**Metrics to implement**:
- **Character Error Rate (CER)**: Edit distance at character level
- **Word Error Rate (WER)**: Edit distance at word level
- **Levenshtein Distance**: Character-level edit distance
- **Content Preservation**: Percentage of original content preserved

**Tasks**:
1. Implement edit distance calculations (Levenshtein)
2. Create text normalization utilities (whitespace, punctuation handling)
3. Build content comparison functions
4. Add per-element content accuracy

**Dependencies**:
- May need `python-Levenshtein` package for performance

**Files to create**:
- `unpdf/core/accuracy/content_scorer.py`
- `unpdf/core/accuracy/text_utils.py`

**Files to modify**:
- `unpdf/core/metrics.py`

### Phase 4: Structural Accuracy
**Goal**: Measure how well we preserve document structure

**Metrics to implement**:
- **Hierarchy Accuracy**: Header levels correctly preserved
- **List Structure**: Nesting and ordering preserved
- **Table Structure**: Rows, columns, cells correctly identified
- **Reading Order**: Elements in correct sequence

**Tasks**:
1. Implement hierarchy comparison (tree diff)
2. Create list structure validator
3. Build table structure comparator
4. Add reading order evaluation

**Files to create**:
- `unpdf/core/accuracy/structure_scorer.py`
- `unpdf/core/accuracy/hierarchy_diff.py`

**Files to modify**:
- `unpdf/core/metrics.py`

### Phase 5: Ground Truth Comparison
**Goal**: Enable comparison against known-good conversions

**Tasks**:
1. Define ground truth format (Markdown with annotations?)
2. Implement ground truth loader
3. Create element alignment algorithm (match detected elements to ground truth)
4. Build comparison pipeline
5. Generate detailed diff reports

**Ground Truth Format Options**:
- **Option A**: Clean Markdown file (user provides expected output)
- **Option B**: Annotated Markdown with element IDs/types
- **Option C**: JSON metadata alongside Markdown

**Recommendation**: Start with Option A (clean Markdown), easy for users to create

**Files to create**:
- `unpdf/core/accuracy/ground_truth.py`
- `unpdf/core/accuracy/element_aligner.py`
- `unpdf/core/accuracy/comparator.py`

**Files to modify**:
- `unpdf/cli/main.py` (add `--ground-truth` parameter)

### Phase 6: Accuracy Report Generation
**Goal**: Provide comprehensive, actionable accuracy reports

**Report Sections**:
1. **Summary**: Overall scores, element counts, top issues
2. **Element-Level**: Breakdown by element type
3. **Content-Level**: CER, WER, text preservation
4. **Structural**: Hierarchy, ordering, formatting
5. **Detailed Diff**: Element-by-element comparison (when ground truth available)

**Output Formats**:
- Console (summary)
- JSON (machine-readable)
- HTML (detailed, visual)
- Markdown (human-readable report)

**Tasks**:
1. Design report templates
2. Implement report generators for each format
3. Add visualization for HTML reports (charts, diff highlighting)
4. Create summary statistics calculator

**Files to create**:
- `unpdf/core/accuracy/reporter.py`
- `unpdf/core/accuracy/templates/` (HTML/Markdown templates)

**Files to modify**:
- `unpdf/cli/main.py` (add `--accuracy-format` parameter)

### Phase 7: Integration and CLI
**Goal**: Make accuracy detection easy to use

**CLI Interface Design**:
```bash
# Basic accuracy metrics (no ground truth)
unpdf input.pdf --accuracy

# Compare against ground truth
unpdf input.pdf --accuracy --ground-truth expected.md

# Specify report format
unpdf input.pdf --accuracy --accuracy-format json

# Save accuracy report
unpdf input.pdf --accuracy --accuracy-report accuracy.json

# Verbose accuracy output
unpdf input.pdf --accuracy --verbose
```

**Tasks**:
1. Add CLI flags and parameters
2. Integrate accuracy pipeline into main conversion flow
3. Add automatic accuracy calculation for test suite
4. Update documentation

**Files to modify**:
- `unpdf/cli/main.py`
- `unpdf/core/converter.py`
- `README.md`
- `docs/USAGE.md`

### Phase 8: Test Suite Integration
**Goal**: Automatically track accuracy across test cases

**Tasks**:
1. Create test fixtures with ground truth
2. Add accuracy assertions to test suite
3. Implement regression tracking (compare against baseline)
4. Generate test accuracy reports

**Test Cases to Add**:
- Simple document (headers, paragraphs)
- Complex formatting (tables, lists, code blocks)
- Multi-column layouts
- Mathematical content
- Images and captions

**Files to create**:
- `tests/fixtures/ground_truth/` (directory)
- `tests/test_accuracy.py`

**Files to modify**:
- `tests/conftest.py` (add accuracy fixtures)

## Recommendations for This Project

### Phased Rollout
1. **Phase 1-3 First**: Core metrics without ground truth (easy to implement)
2. **Phase 5 Next**: Ground truth comparison (valuable for validation)
3. **Phase 4, 6-8 Last**: Advanced features and integration

### Default Behavior
- **Disabled by default** in CLI (no performance impact for normal use)
- **Always enabled** in test suite (track quality)
- **Easy to enable** with single flag: `--accuracy`

### Configuration
Add to `.copilot-cli.json`:
```json
{
  "accuracy": {
    "default_enabled": false,
    "report_format": "console",
    "save_reports": true,
    "report_dir": "accuracy_reports"
  }
}
```

### Ground Truth Strategy
For the Obsidian example:
- `example-obsidian/obsidian-input.md` is perfect ground truth
- Can compare `output.md` against `obsidian-input.md`
- Measure how much of the original formatting is preserved

## Success Criteria

### Phase 1-3 (MVP)
- [ ] `--accuracy` flag implemented
- [ ] Basic metrics calculated (precision, recall, CER, WER)
- [ ] Console report generated
- [ ] No ground truth needed (self-analysis)

### Phase 5 (Ground Truth)
- [ ] Can specify ground truth file
- [ ] Elements aligned between detected and ground truth
- [ ] Detailed comparison report generated
- [ ] Works with Obsidian example

### Phase 6-8 (Complete)
- [ ] Multiple report formats (console, JSON, HTML, Markdown)
- [ ] Integrated into test suite
- [ ] Documentation complete
- [ ] Regression tracking implemented

## Technical Considerations

### Performance
- Accuracy calculation adds 10-30% overhead
- Use lazy evaluation where possible
- Cache calculations for repeated metrics

### Accuracy vs Complexity
- Start simple (element counts, text comparison)
- Add sophisticated metrics later (structure, semantics)
- Don't over-engineer early

### User Experience
- Make it opt-in (flag-based)
- Provide useful defaults
- Clear, actionable output

## Dependencies
```toml
# Add to pyproject.toml [project.dependencies]
python-Levenshtein = ">=0.21.0"  # Fast edit distance
difflib = "built-in"  # Text diffing
```

## Implementation Status

### Completed
- [x] **Phase 2: Element Detection Accuracy** (Completed)
  - Created `unpdf/accuracy/` module
  - Implemented `ElementDetector` class for parsing Markdown and detecting:
    - Headers (with levels)
    - Paragraphs
    - Lists (with nesting detection)
    - Code blocks (with language detection)
    - Tables
    - Images
    - Blockquotes
    - Horizontal rules
    - Inline elements (bold, italic, code, links)
  - Implemented `ElementScorer` class for calculating:
    - Precision, Recall, F1 scores
    - Overall and per-type accuracy
    - True positives, false positives, false negatives
  - Added comprehensive test suite: 16 tests, all passing
  - Passed mypy type checking and ruff linting

### Next Steps
1. **Phase 3**: Content Accuracy (text comparison with CER/WER)
2. **Phase 4**: Structural Accuracy (hierarchy, nesting preservation)
3. **Phase 5**: Ground Truth Comparison (compare with original Markdown)
4. **Phase 6**: CLI Integration (`--accuracy` flag)
5. Test with Obsidian example

## Notes
- This is a common feature in document conversion tools (Tesseract, Adobe, etc.)
- **Industry standard**: Optional flag, not always-on
- **Value**: Essential for measuring improvements and catching regressions
- **Obsidian example**: Perfect test case with ground truth available
