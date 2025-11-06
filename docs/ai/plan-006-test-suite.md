# Plan 006: Comprehensive Test Suite with Real-World Examples

**Status**: Not Started  
**Created**: 2025-11-06  
**Goal**: Implement a strategic test suite with real-world Markdown documents of varying complexity to validate PDF-to-Markdown conversion accuracy.

## Overview

This plan creates a comprehensive test suite that validates unpdf's conversion accuracy across documents ranging from simple to complex. Each test will measure element-level accuracy and provide actionable insights.

## Test Document Strategy

### Complexity Levels

1. **Simple** - Basic formatting only
2. **Intermediate** - Multiple formatting types
3. **Advanced** - Complex nested structures
4. **Real-World** - Actual documents with mixed complexity

### Test Coverage Matrix

| Level | Headers | Lists | Tables | Code | Links | Images | Math | Quotes | Bold/Italic | Nested |
|-------|---------|-------|--------|------|-------|--------|------|--------|-------------|--------|
| Simple | ✓ | ✓ | - | - | - | - | - | - | ✓ | - |
| Intermediate | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ | ✓ |
| Advanced | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Real-World | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Phase 1: Test Suite Infrastructure

### Step 1.1: Create Test Directory Structure ✅ (Completed)
- [x] Create `tests/data/` directory structure
- [x] Subdirectories:
  - `tests/data/simple/` - Simple test cases
  - `tests/data/intermediate/` - Intermediate complexity
  - `tests/data/advanced/` - Advanced features
  - `tests/data/real-world/` - Real-world examples
  - `tests/data/baseline/` - Known-good conversions for regression testing

### Step 1.2: Create Test Markdown Documents ✅ (Completed)
Create original Markdown files for each complexity level:

**Simple Tests** (tests/data/simple/):
- [ ] `01-headers.md` - H1-H6 headers only
- [ ] `02-paragraphs.md` - Plain text paragraphs
- [ ] `03-basic-lists.md` - Simple bullet and numbered lists
- [ ] `04-inline-formatting.md` - Bold, italic, code spans
- [ ] `05-links.md` - Basic hyperlinks

**Intermediate Tests** (tests/data/intermediate/):
- [ ] `01-mixed-lists.md` - Nested lists with mixed types
- [ ] `02-simple-tables.md` - Basic tables
- [ ] `03-code-blocks.md` - Fenced code blocks with languages
- [ ] `04-blockquotes.md` - Single and nested blockquotes
- [ ] `05-combined-formatting.md` - Multiple features together

**Advanced Tests** (tests/data/advanced/):
- [ ] `01-complex-tables.md` - Multi-column tables with alignment
- [ ] `02-nested-lists.md` - Deep nesting (3+ levels)
- [ ] `03-mixed-content.md` - Lists with code, tables with formatting
- [ ] `04-special-chars.md` - Special characters, escaping
- [ ] `05-math-equations.md` - LaTeX math (if supported)

**Real-World Tests** (tests/data/real-world/):
- [ ] `01-readme.md` - Typical GitHub README
- [ ] `02-documentation.md` - Technical documentation
- [ ] `03-blog-post.md` - Blog-style article
- [ ] `04-research-paper.md` - Academic-style document

**User Action Required**: 
After this step, convert each `.md` file to PDF using your preferred PDF converter(s):
- Place PDFs in same directory as `.md` file with same name (e.g., `01-headers.pdf`)
- Optionally test multiple PDF converters by naming: `01-headers-obsidian.pdf`, `01-headers-pandoc.pdf`, etc.

### Step 1.3: Create Test Runner Script ✅ (Completed)
- [ ] Create `tests/test_accuracy_suite.py`
- [ ] Implement `TestAccuracySuite` class
- [ ] Auto-discover test cases from directory structure
- [ ] Run conversion + accuracy detection for each test
- [ ] Collect and aggregate results

### Step 1.4: Create Reporting System ✅ (Completed)
- [ ] Generate detailed per-test reports (JSON)
- [ ] Generate summary report (Markdown table)
- [ ] Save reports to `tests/reports/` directory
- [ ] Include:
  - Overall accuracy by category
  - Element-level failures
  - Performance metrics
  - Comparison across PDF converters (if multiple)

## Phase 2: Test Document Creation

### Step 2.1: Create Simple Test Documents ✅ (Completed)
Create the 5 simple test Markdown files with clear, focused content.

### Step 2.2: Create Intermediate Test Documents ✅ (Completed)
Create the 5 intermediate test Markdown files with combined features.

### Step 2.3: Create Advanced Test Documents ✅ (Completed)
Create the 5 advanced test Markdown files with complex structures.

### Step 2.4: Create Real-World Test Documents ✅ (Completed)
Create the 4 real-world test Markdown files based on common use cases.

**User Action Required After Step 2.4**:
Convert all created `.md` files to PDF format:
1. Use Obsidian, Pandoc, or your preferred Markdown→PDF converter
2. Place each PDF in the same directory as its source `.md` file
3. Naming convention: `{name}.pdf` or `{name}-{converter}.pdf`

## Phase 3: Test Execution & Analysis

### Step 3.1: Run Initial Test Suite ✅ (Completed)
- [ ] Run test suite against all test documents
- [ ] Generate initial accuracy reports
- [ ] Identify categories with lowest accuracy

### Step 3.2: Analyze Results ✅ (Completed)
- [ ] Review detailed element-level failures
- [ ] Categorize failure patterns
- [ ] Prioritize issues by:
  - Frequency (affects multiple tests)
  - Severity (complete failures vs. minor issues)
  - Complexity level (simple issues first)

### Step 3.3: Create Improvement Plan ✅ (Completed)
- [ ] Document top 10 failure patterns
- [ ] Create plan for addressing each
- [ ] Estimate effort for fixes

## Phase 4: Continuous Integration

### Step 4.1: Add to Pytest Suite ✅ (Completed)
- [ ] Integrate accuracy tests with existing pytest suite
- [ ] Add markers: `@pytest.mark.accuracy`, `@pytest.mark.slow`
- [ ] Configure CI to run accuracy tests

### Step 4.2: Define Success Criteria ✅ (Completed)
- [ ] Set minimum accuracy thresholds:
  - Simple tests: 95%+
  - Intermediate tests: 90%+
  - Advanced tests: 85%+
  - Real-world tests: 80%+
- [ ] Configure tests to fail if below threshold

### Step 4.3: Baseline Establishment ✅ (Completed)
- [ ] Run tests on current implementation
- [ ] Save results as baseline in `tests/data/baseline/`
- [ ] Track improvements over time

## Phase 5: Documentation

### Step 5.1: Document Test Suite Usage ✅ (Completed)
- [ ] Add section to README.md
- [ ] Create `docs/testing.md` with:
  - How to run accuracy tests
  - How to add new test cases
  - How to interpret reports
  - How to convert Markdown to PDF

### Step 5.2: Document Current Limitations ✅ (Completed)
- [ ] Based on test results, document known limitations
- [ ] Add to README or docs/limitations.md
- [ ] Include workarounds if available

## Expected Outcomes

1. **Quantifiable Accuracy**: Exact accuracy measurements for each feature category
2. **Regression Detection**: Automated detection of accuracy degradation
3. **Targeted Improvements**: Data-driven prioritization of fixes
4. **User Confidence**: Clear documentation of capabilities and limitations
5. **Benchmark Comparisons**: Ability to compare against other converters

## Success Criteria

- [ ] At least 19 test documents created (5+5+5+4)
- [ ] All tests automatically discoverable and executable
- [ ] Detailed reports generated after each run
- [ ] Minimum 80% overall accuracy on intermediate tests
- [ ] Test suite runs in <30 seconds
- [ ] CI integration complete
- [ ] Documentation complete

## Notes

- PDF conversion tools to consider:
  - Obsidian (primary target)
  - Pandoc (`pandoc input.md -o output.pdf`)
  - wkhtmltopdf (via markdown-pdf)
  - Chrome/Chromium print to PDF
  - VSCode Markdown PDF extension
  
- Consider creating a helper script to batch-convert all `.md` files to PDF

- Test documents should be version controlled (both `.md` and `.pdf`)

- Consider adding a `--update-baseline` flag to save current output as expected

- For images in test documents, use simple placeholder images or reference public URLs
