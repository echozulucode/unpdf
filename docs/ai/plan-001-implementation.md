# PDF-to-Markdown Converter: Phased Implementation Plan

**Status**: Phase 9 Complete - Documentation Finalized  
**Last Updated**: 2025-11-02  
**Next**: Phase 10 - Release & Deployment (or Plan 002 Quality Fixes)

## Current Status Summary

✅ **Phases 1-9 Complete**: All core features implemented, tested, and documented
- Text extraction with metadata ✅
- Heading detection ✅  
- List processing (nested, up to 5 levels) ✅
- Code blocks and blockquotes ✅
- Table extraction with validation ✅
- Image extraction with captions ✅
- Link and URL handling ✅
- CLI with advanced features ✅
- Comprehensive test suite (172 passing, 96% coverage) ✅
- **Production-ready documentation (7 comprehensive docs)** ✅

⚠️ **Quality Issues Discovered**: Testing with real-world Obsidian PDF revealed conversion problems:
- Text spacing issues (words merged together)
- Table content duplication (text + table format)
- Code blocks lose line breaks and formatting
- List nesting accuracy varies by PDF source
- See **[plan-002-conversion-quality-fixes.md](plan-002-conversion-quality-fixes.md)** for detailed analysis and resolution plan

🎯 **Next Steps**: 
1. **Option A**: Complete Phase 10 - Release v1.0.0 (core features complete)
2. **Option B**: Address Plan 002 quality fixes before release
3. **Recommended**: Release v1.0.0, address quality issues in v1.0.1+

## Overview
Building a Python package (MIT-licensed) that converts PDF files to Markdown format, focusing on text-based elements: headings, paragraphs, lists, tables, inline formatting, links, and images.

## Key Differentiators from PyMuPDF & Marker

### 1. **MIT License vs AGPL/Commercial**
- **PyMuPDF**: AGPL-licensed (requires AGPL for derivatives) or expensive commercial license
- **Marker**: Modified AI Pubs Open Rail-M (requires licensing for startups >$2M)
- **Our Tool**: Pure MIT license - use freely in any commercial project without restrictions

### 2. **Simplicity & Focus**
- **PyMuPDF/Marker**: Feature-rich, complex pipelines with ML models, multiple converters, extensive APIs
- **Our Tool**: Simple, focused, predictable conversion for common use cases
  - No ML dependencies by default (lightweight)
  - Straightforward CLI: `unpdf input.pdf` → `input.md`
  - Easy to understand and modify codebase

### 3. **Transparency & Explainability**
- **PyMuPDF/Marker**: Black-box deep learning models (surya, texify, layout detection)
- **Our Tool**: Rule-based, heuristic-driven approach
  - Understand *why* conversions happen
  - Predictable, debuggable output
  - No GPU required, no model downloads
  - Deterministic results

### 4. **Configuration & Customization**
- **Marker**: Complex config system, multiple processors, requires understanding internal architecture
- **Our Tool**: Simple, well-documented configuration
  - Easy-to-extend plugin system for custom processors
  - Clear separation: extractors → processors → renderers
  - User-friendly override system

### 5. **Developer Experience**
- **Target Audience**: Developers who want:
  - To understand their tooling
  - Lightweight dependencies (no torch, transformers)
  - Fast installation (no GB of models)
  - Easy integration into existing pipelines
  - MIT license for commercial projects

### 6. **Use Case Focus**
- **Primary**: Documentation, technical content, business reports
- **Secondary**: Academic papers (without complex math)
- **Not targeting**: Forms, equations, scanned PDFs (vs Marker's broader scope)
- **Advantage**: Better quality for common cases by not trying to do everything

### 7. **Performance Trade-offs**
- **Marker**: Slower (ML models), higher accuracy on complex layouts
- **Our Tool**: Faster (no ML), excellent quality on standard layouts
  - Sub-second conversion for typical documents
  - Lower memory footprint
  - No GPU/VRAM requirements

### 8. **Integration & Ecosystem**
- Python-first library design (not just CLI)
- Easy to embed in larger applications
- Streaming API for large documents
- Clean programmatic interface:
  ```python
  from unpdf import convert_pdf
  markdown = convert_pdf("doc.pdf")
  ```

### 9. **Quality Philosophy**
- **Marker**: "Works on everything" - ML handles edge cases
- **Our Tool**: "Excellent on common cases" - clear about limitations
  - Fail gracefully with informative messages
  - Clear documentation on what works vs doesn't
  - Fallback strategies clearly documented

### 10. **Community & Contribution**
- Beginner-friendly codebase (no deep learning knowledge needed)
- Well-documented architecture
- Easy to add new features
- Lower barrier to contribution

## Positioning Statement
**"unpdf is the simple, MIT-licensed PDF-to-Markdown converter for developers who value transparency, predictability, and ease of use over handling every edge case. Perfect for documentation, technical content, and business reports where you want fast, reliable conversion without ML dependencies or licensing restrictions."**

---

## Phase 1: Project Setup & Foundation (Week 1) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-1-completion.md](phase-1-completion.md)

### 1.1 Project Structure ✅
- [x] Initialize Git repository (already done)
- [x] Create Python package structure (`unpdf/`)
  - `unpdf/__init__.py` - Package entry point with `convert_pdf` export
  - `unpdf/cli.py` - Full CLI implementation with argparse
  - `unpdf/core.py` - Main conversion pipeline (placeholder)
  - `unpdf/extractors/` - Text, tables, images (structure created)
  - `unpdf/processors/` - Headings, lists, code, etc. (structure created)
  - `unpdf/renderers/` - Markdown, HTML output (structure created)
- [x] Setup `pyproject.toml` with MIT license (already done)
- [x] Configure entry point: `unpdf` CLI command (working)
- [x] Create `README.md` highlighting differentiators (already done)

### 1.2 Development Environment ✅
- [x] Setup Python 3.13.1 environment (exceeds 3.10+ requirement)
- [x] Core dependencies configured in pyproject.toml:
  - `pdfplumber>=0.10.0` (MIT-licensed) - PDF parsing
  - `pdfminer.six>=20221105` (MIT-licensed) - Text extraction
  - Optional: `camelot-py[cv]>=0.11.0` for table detection (Phase 5)
- [x] Setup pytest for testing (8 tests passing)
- [x] Configure GitHub Actions for CI/CD (already done)

### 1.3 Documentation ✅
- [x] Document supported features vs unsupported (README.md)
- [x] Create contribution guidelines (CONTRIBUTING.md, already done)
- [x] Setup issue templates (deferred to when needed)

**Deliverable:** ✅ Working project skeleton with build system
- Package installable: `pip install -e ".[dev]"` ✅
- CLI working: `unpdf --version` ✅
- Tests passing: 8/8 (59% coverage) ✅
- Code quality: Black, Ruff, Mypy all passing ✅

---

## Phase 2: Basic Text Extraction (Week 2) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-2-completion.md](phase-2-completion.md)

### 2.1 Simple Text Extraction ✅
- [x] Implement basic PDF text extraction using pdfplumber
- [x] Detect and preserve reading order (character-by-character)
- [x] Handle paragraph separation with blank lines (10pt+ vertical gap)
- [x] Manage whitespace normalization (preserved within spans)

### 2.2 Font Style Detection ✅
- [x] Extract font metadata (family, size, weight)
- [x] Detect bold text (wrap in `**bold**`)
- [x] Detect italic text (wrap in `*italic*`)
- [x] Handle combined bold-italic formatting (`***text***`)

### 2.3 Testing ✅
- [x] Unit tests for text extraction (8 tests)
- [x] Test paragraph separation (renderer tests)
- [x] Test font style detection (bold/italic detection)
- [x] Edge cases handled (empty PDFs, whitespace, missing metadata)

**Deliverable:** ✅ Basic converter that handles plain text with inline formatting
- Text extraction: `unpdf/extractors/text.py` ✅
- Markdown rendering: `unpdf/renderers/markdown.py` ✅
- Tests: 25 passing (4 skipped pending PDF fixtures) ✅
- Coverage: 52% (will improve with real PDF fixtures) ✅

---

## Phase 3: Structural Elements (Week 3) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-3-completion.md](phase-3-completion.md)

### 3.1 Heading Detection ✅
- [x] Implement font-size based heading detection
- [x] Compare text span font size to document average
- [x] Map heading levels to Markdown (#, ##, ###)
- [x] Handle title and section headers
- [x] Bold text priority in level assignment

### 3.2 List Detection ✅
- [x] Detect bullet characters (•, –, -, ●, ○, ▪, etc.)
- [x] Convert to Markdown unordered lists (`- Item`)
- [x] Detect numbered lists (1., a), i., etc.)
- [x] Convert to Markdown ordered lists (`1. Item`)
- [x] Handle nested lists with proper indentation (up to 5 levels)
- [x] Preserve list hierarchy based on x-coordinates

### 3.3 Blockquotes ⏭️
- [ ] Detect quoted paragraphs (deferred to Phase 4)
- [ ] Prepend `>` to blockquote lines
- [ ] Handle nested blockquotes

### 3.4 Testing ✅
- [x] Test heading detection with various font sizes (9 tests)
- [x] Test bullet list conversion (12 tests)
- [x] Test numbered list conversion (included)
- [x] Test nested lists (indent levels)
- [ ] Test blockquotes (deferred to Phase 4)

**Deliverable:** ✅ Converter handles headings and lists
- Heading processor: `unpdf/processors/headings.py` ✅
- List processor: `unpdf/processors/lists.py` ✅
- Element-based architecture ✅
- Tests: 46 passing (4 skipped) ✅
- Coverage: 62% (+10% from Phase 2) ✅

---

## Phase 4: Code Blocks & Blockquotes (Week 4) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-4-completion.md](phase-4-completion.md)

### 4.1 Code Detection ✅
- [x] Detect monospaced fonts (Courier, Consolas, Monaco, etc.)
- [x] Pattern matching for 12 common monospace fonts
- [x] Distinguish inline code vs code blocks (length-based)
- [ ] Identify framed/boxed code regions (deferred - not common)

### 4.2 Code Conversion ✅
- [x] Wrap multi-line code in triple backticks (```)
- [x] Wrap inline code in single backticks (`)
- [x] Attempt language inference from context
- [x] Support 6 languages: Python, JavaScript, Java, C++, Bash, SQL
- [x] Escape special characters in inline code

### 4.3 Blockquote Detection ✅
- [x] Detect indented paragraphs as blockquotes
- [x] Calculate nesting levels (up to 5)
- [x] Remove quote marks from text
- [x] Convert to Markdown `>` prefix format

### 4.4 Testing ✅
- [x] Test code block detection (18 tests)
- [x] Test inline code detection (included)
- [x] Test various monospaced fonts (9 fonts)
- [x] Test language inference (6 languages)
- [x] Test blockquote detection (9 tests)
- [x] Test blockquote nesting

**Deliverable:** ✅ Converter handles code blocks, inline code, and blockquotes
- Code processor: `unpdf/processors/code.py` ✅
- Blockquote processor: `unpdf/processors/blockquote.py` ✅
- Language inference (6 languages) ✅
- Tests: 73 passing (4 skipped) ✅
- Coverage: 68% (+6% from Phase 3) ✅

---

## Phase 5: Table Extraction (Week 5-6) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-5-completion.md](phase-5-completion.md)

### 5.1 Table Detection ✅
- [x] Integrate pdfplumber table detection
- [x] Detect tables via PDF lines/grids (strict strategy)
- [x] Detect tables via column alignment patterns (text strategy)
- [x] Handle tables without explicit cell borders (fallback)
- [x] Configurable table detection settings

### 5.2 Table Conversion ✅
- [x] Convert to Markdown pipe tables
- [x] Create header row with separator (`|---|---|`)
- [x] Format data rows with proper alignment
- [x] Handle uneven rows (normalize to max column count)
- [x] Handle None/null cells
- [x] Auto-calculate column widths
- [ ] Handle merged cells (deferred - Markdown limitation)
- [ ] Fallback for complex tables (deferred - rare case)

### 5.3 Testing ✅
- [x] Test simple tables with borders (16 unit tests)
- [x] Test tables without borders (text-based detection)
- [x] Test uneven rows and empty cells
- [x] Test header detection heuristics
- [x] Test column alignment
- [ ] Test merged cells (deferred)
- [ ] Test complex multi-row headers (deferred)

**Deliverable:** ✅ Converter handles tables and outputs pipe-table Markdown
- Table processor: `unpdf/processors/table.py` ✅
- pdfplumber integration ✅
- Two-strategy detection (lines + text) ✅
- Header detection heuristic ✅
- Tests: 88 passing (5 skipped) ✅
- Coverage: 66% (stable) ✅

---

## Phase 6: Images & Links (Week 7) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-6-completion.md](phase-6-completion.md)

### 6.1 Image Extraction ✅
- [x] Extract embedded images (JPEG, PNG)
- [x] Save images as separate files
- [x] Generate unique filenames for images (MD5-based)
- [x] Insert Markdown image references: `![alt](image.png)`
- [x] Detect and extract image captions (50pt below image)
- [x] Handle extraction failures gracefully
- [x] Support multiple images across pages

### 6.2 Hyperlink Detection ✅
- [x] Detect PDF URI annotations
- [x] Extract link text and URL
- [x] Convert to Markdown links: `[text](url)`
- [x] Handle plain text URLs (regex-based)
- [x] Escape special characters in link text
- [x] Remove duplicate URLs
- [x] Fallback to URL as text when needed

### 6.3 Testing ✅
- [x] Test image extraction and saving (16 tests)
- [x] Test image reference generation
- [x] Test hyperlink detection (16 tests)
- [x] Test plain URL handling
- [x] Test caption detection
- [x] Test error handling

**Deliverable:** ✅ Converter handles images and hyperlinks
- Image extractor: `unpdf/extractors/images.py` ✅
- Link processor: `unpdf/processors/links.py` ✅
- Caption detection ✅
- Tests: 121 passing (5 skipped) ✅
- Coverage: 72% (100% for new modules) ✅

---

## Phase 7: CLI Implementation (Week 8) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-7-completion.md](phase-7-completion.md)

### 7.1 Command-Line Interface ✅
- [x] Implement main CLI entry point (`unpdf.cli:main`)
- [x] Add argument parsing:
  - Input file/directory path
  - `-o/--output` - output path
  - `--pages` - specific pages to convert (e.g., '1,3,5-7')
  - `-r/--recursive` - process directories recursively
  - `--no-code-blocks` - disable code detection
  - `--heading-ratio` - heading detection threshold
  - `-v/--verbose` - debug logging
- [x] Default output: input basename with `.md` extension
- [x] Handle single file conversion
- [x] Handle batch directory conversion
- [x] Page specification parsing (single, ranges, mixed)

### 7.2 Error Handling ✅
- [x] Validate input files exist
- [x] Check file permissions
- [x] Handle corrupted PDFs gracefully
- [x] Provide meaningful error messages
- [x] Handle keyboard interrupts (Ctrl+C)
- [x] Proper exit codes (0=success, 1=error, 130=interrupt)
- [x] Batch mode continues on errors with summary

### 7.3 Testing ✅
- [x] Test CLI with single file
- [x] Test CLI with directory
- [x] Test default output naming
- [x] Test custom output path
- [x] Test error conditions (25 tests total)
- [x] Test page specification parsing
- [x] Test batch error handling
- [x] Test all CLI flags

**Deliverable:** ✅ Fully functional CLI tool with advanced features
- Page selection: `--pages 1,3,5-7` ✅
- Error handling: Comprehensive with proper exit codes ✅
- Tests: 25 CLI tests, 141 total passing ✅
- Coverage: 94% for CLI module, 78% overall ✅
- Code quality: Black, Ruff, Mypy all passing ✅

---

## Phase 8: Comprehensive Testing (Week 9) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)  
**Completion Report:** [phase-8-completion.md](phase-8-completion.md)

### 8.1 Round-Trip Tests ✅
- [x] Convert Markdown → PDF (using reportlab)
- [x] Convert PDF → Markdown (using our tool)
- [x] Compare result to original (normalize whitespace)
- [x] Test simple documents (paragraphs, headings)
- [x] Test complex documents (mixed content)
- [x] Test formatted text (bold, italic)
- [x] Test lists (bullet and numbered)
- [ ] Test with real PDF fixtures (deferred - 3 tests pending)

### 8.2 Feature-Specific Tests ✅
- [x] One test per feature (tables, code, lists, images, links)
- [x] Test PDFs with only specific feature (9 tests)
- [x] Test mixed content scenarios
- [x] Validate feature isolation
- [ ] Real-world scenarios (5 tests pending fixtures)

### 8.3 Edge Cases ✅
- [x] Empty PDFs
- [x] Unusual fonts (Helvetica, Courier, Times)
- [x] Extra whitespace normalization
- [x] Empty pages
- [x] Large documents (50 pages)
- [x] Special characters and unicode
- [x] Overlapping and rotated text
- [x] Very long lines
- [ ] Multiple columns (deferred to Phase 12)
- [ ] Scanned PDFs (out of scope)

### 8.4 Integration Tests ✅
- [x] Test full pipeline with programmatic PDFs
- [x] Test error handling (5 comprehensive tests)
- [x] Verify conversion correctness
- [ ] Test various PDF generators (deferred - need fixtures)
- [ ] Verify reading order (covered in unit tests)

**Deliverable:** ✅ Comprehensive test suite with 96% coverage
- Total tests: 185 (39 new integration tests)
- Passed: 172 (100% pass rate)
- Skipped: 13 (awaiting real PDF fixtures)
- Coverage: 96% (up from 78%)
- Files: `test_round_trip.py`, `test_edge_cases.py`, `test_feature_specific.py`

---

## Phase 9: Documentation & Polish (Week 10) ✅ COMPLETE

**Status:** ✅ Complete (2025-11-02)

### 9.1 User Documentation ✅
- [x] Comprehensive README with examples - Updated with current feature status
- [x] Installation instructions - Complete in README.md
- [x] Usage guide with CLI examples - docs/USER_GUIDE.md (comprehensive)
- [x] Feature support matrix - Updated in README.md
- [x] Troubleshooting guide - Added to README.md and USER_GUIDE.md
- [x] Examples document - docs/EXAMPLES.md (20+ real-world examples)
- [x] Limitations document - docs/LIMITATIONS.md (comprehensive)

### 9.2 Developer Documentation ✅
- [x] Architecture overview - docs/ARCHITECTURE.md (complete)
- [x] Module documentation - Comprehensive API docs
- [x] API reference - docs/API_REFERENCE.md (full coverage)
- [x] Contributing guide - CONTRIBUTING.md (with Google-style docstrings)
- [x] Code style guide - docs/STYLE_GUIDE.md
- [x] Agent instructions - AGENTS.md (mission and guidelines)

### 9.3 Limitations Documentation ✅
- [x] Clearly document unsupported features:
  - Video/audio/3D objects ✅
  - Form fields ✅
  - Mathematical equations ✅
  - Annotations ✅
  - Footnotes (limited) ✅
  - Scanned PDFs (OCR required) ✅
  - Multi-column layouts (partial) ✅
- [x] Provide workarounds where possible ✅
- [x] Comparison with alternatives (PyMuPDF, Marker) ✅

### 9.4 Polish ✅
- [x] Code quality - 96% test coverage, all linters passing
- [x] Documentation complete - 7 comprehensive docs created
- [x] Examples provided - 20+ use cases documented
- [x] Troubleshooting guides - Common issues documented
- [x] Ready for v1.0 release

**Note:** Performance optimization and memory usage optimization deferred to v1.1 per Plan 002.

**Deliverable:** ✅ Production-ready documentation complete
- Total documentation: 7 files (README, USER_GUIDE, API_REFERENCE, ARCHITECTURE, EXAMPLES, LIMITATIONS, CONTRIBUTING)
- Coverage: Installation, usage, API, architecture, troubleshooting, limitations, examples
- Ready for Phase 10: Release & Deployment

---

## Phase 10: Release & Deployment (Week 11)

### 10.1 Package Preparation
- [ ] Finalize version number (v1.0.0)
- [ ] Update changelog
- [ ] Verify all dependencies have compatible licenses
- [ ] Create requirements.txt and lock file

### 10.2 PyPI Publication
- [ ] Setup PyPI account
- [ ] Test package installation from TestPyPI
- [ ] Publish to PyPI as `pdf2md`
- [ ] Verify installation: `pip install pdf2md`

### 10.3 GitHub Release
- [ ] Create GitHub release with notes
- [ ] Tag release version
- [ ] Include example PDFs and outputs
- [ ] Setup issue tracking

### 10.4 Community Engagement
- [ ] Announce on relevant forums/communities
- [ ] Setup discussions for questions
- [ ] Create initial issues for future enhancements

**Deliverable:** Published package on PyPI and GitHub

---

## Future Enhancements (Post v1.0)

### Phase 11: Advanced Features (Future)
- [ ] **Optional** OCR plugin (keeps base lightweight)
- [ ] Plugin system for custom processors
- [ ] Streaming API for very large documents
- [ ] Watch mode (auto-convert on PDF changes)
- [ ] Diff mode (show what changed between PDF versions)
- [ ] Custom output templates
- [ ] Configuration file support
- [ ] Parallel processing for large batches
- [ ] Simple web UI (local only, privacy-focused)

### Phase 12: Quality Improvements (Future)
- [ ] Benchmark suite vs PyMuPDF/Marker on common documents
- [ ] Performance profiling and optimization
- [ ] Better column detection (newspaper layouts)
- [ ] Enhanced list detection (complex nested structures)
- [ ] Export to other formats (HTML, reStructuredText)
- [ ] Memory-efficient streaming for huge PDFs

### Phase 13: Developer Experience (Future)
- [ ] VS Code extension (preview PDFs as Markdown)
- [ ] GitHub Action for CI/CD pipelines
- [ ] Pre-commit hook integration
- [ ] Docker image for reproducible environments
- [ ] Comprehensive plugin development guide

---

## Success Criteria

1. **Functionality**: Converts text-based PDFs to readable Markdown preserving structure
2. **Accuracy**: Round-trip tests show content equivalence (≥95% match)
3. **Usability**: Simple CLI with sensible defaults
4. **Quality**: Test coverage ≥80%, all CI checks passing
5. **Documentation**: Clear README, examples, and API docs
6. **License**: MIT-licensed with compatible dependencies only
7. **Community**: Published on PyPI, ready for contributions

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| License incompatibility (PyMuPDF is AGPL) | Use MIT-licensed alternatives (pdfplumber, pdfminer.six) |
| Complex PDF layouts (multi-column, rotated text) | Start with simple layouts, iterate on edge cases |
| Table detection accuracy | Provide fallback to plain text, allow manual hints |
| Large file memory usage | Stream processing, page-by-page conversion |
| Dependency conflicts | Pin versions, use virtual environments, test on clean installs |

---

## Team & Resources

- **Development**: 1-2 developers
- **Duration**: 11 weeks (core), ongoing maintenance
- **Tools**: Python 3.10+, pytest, GitHub Actions, PyPI
- **Libraries**: pdfplumber, pdfminer.six, camelot-py
- **Budget**: Open source (no cost for tools)

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|----------------|
| 1 | Week 1 | Project skeleton |
| 2 | Week 2 | Basic text extraction |
| 3 | Week 3 | Structural elements |
| 4 | Week 4 | Code blocks |
| 5-6 | Week 5-6 | Table extraction |
| 7 | Week 7 | Images & links |
| 8 | Week 8 | CLI implementation |
| 9 | Week 9 | Comprehensive testing |
| 10 | Week 10 | Documentation |
| 11 | Week 11 | Release & deployment |

**Total:** 11 weeks to v1.0 release
