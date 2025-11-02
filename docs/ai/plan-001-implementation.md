# PDF-to-Markdown Converter: Phased Implementation Plan

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

## Phase 5: Table Extraction (Week 5-6)

### 5.1 Table Detection
- [ ] Integrate Camelot or pdfplumber table detection
- [ ] Detect tables via PDF lines/grids
- [ ] Detect tables via column alignment patterns
- [ ] Handle tables without explicit cell borders

### 5.2 Table Conversion
- [ ] Convert to Markdown pipe tables
- [ ] Create header row with separator (`|---|---|`)
- [ ] Format data rows with proper alignment
- [ ] Handle merged cells (best effort)
- [ ] Fallback: plain text for complex tables

### 5.3 Testing
- [ ] Test simple tables with borders
- [ ] Test tables without borders
- [ ] Test merged cells
- [ ] Test complex multi-row headers
- [ ] Test table alignment

**Deliverable:** Converter handles tables and outputs pipe-table Markdown

---

## Phase 6: Images & Links (Week 7)

### 6.1 Image Extraction
- [ ] Extract embedded images (JPEG, PNG)
- [ ] Save images as separate files
- [ ] Generate unique filenames for images
- [ ] Insert Markdown image references: `![alt](image.png)`
- [ ] Detect and extract image captions (if available)

### 6.2 Hyperlink Detection
- [ ] Detect PDF URI annotations
- [ ] Extract link text and URL
- [ ] Convert to Markdown links: `[text](url)`
- [ ] Handle plain text URLs

### 6.3 Testing
- [ ] Test image extraction and saving
- [ ] Test image reference generation
- [ ] Test hyperlink detection
- [ ] Test plain URL handling

**Deliverable:** Converter handles images and hyperlinks

---

## Phase 7: CLI Implementation (Week 8)

### 7.1 Command-Line Interface
- [ ] Implement main CLI entry point (`pdf2md.cli:main`)
- [ ] Add argument parsing:
  - Input file/directory path
  - `-o/--output` - output path
  - `--pages` - specific pages to convert
  - `-r/--recursive` - process directories recursively
- [ ] Default output: input basename with `.md` extension
- [ ] Handle single file conversion
- [ ] Handle batch directory conversion

### 7.2 Error Handling
- [ ] Validate input files exist
- [ ] Check file permissions
- [ ] Handle corrupted PDFs gracefully
- [ ] Provide meaningful error messages

### 7.3 Testing
- [ ] Test CLI with single file
- [ ] Test CLI with directory
- [ ] Test default output naming
- [ ] Test custom output path
- [ ] Test error conditions

**Deliverable:** Fully functional CLI tool

---

## Phase 8: Comprehensive Testing (Week 9)

### 8.1 Round-Trip Tests
- [ ] Convert Markdown → PDF (using Pandoc)
- [ ] Convert PDF → Markdown (using our tool)
- [ ] Compare result to original (ignoring whitespace)
- [ ] Test simple documents (paragraphs, headings)
- [ ] Test complex documents (mixed content)

### 8.2 Feature-Specific Tests
- [ ] One test per feature (tables, code, lists, images)
- [ ] Test PDFs with only specific feature
- [ ] Compare output to expected Markdown

### 8.3 Edge Cases
- [ ] Multiple columns
- [ ] Unusual fonts
- [ ] Extra whitespace
- [ ] Empty pages
- [ ] Large documents
- [ ] Scanned PDFs (text-based only)

### 8.4 Integration Tests
- [ ] Test full pipeline on real-world PDFs
- [ ] Test various PDF generators (LaTeX, Word, etc.)
- [ ] Verify reading order correctness

**Deliverable:** Comprehensive test suite with high coverage

---

## Phase 9: Documentation & Polish (Week 10)

### 9.1 User Documentation
- [ ] Comprehensive README with examples
- [ ] Installation instructions
- [ ] Usage guide with CLI examples
- [ ] Feature support matrix
- [ ] Troubleshooting guide

### 9.2 Developer Documentation
- [ ] Architecture overview
- [ ] Module documentation
- [ ] API reference (if exposing library functions)
- [ ] Contributing guide
- [ ] Code style guide

### 9.3 Limitations Documentation
- [ ] Clearly document unsupported features:
  - Video/audio/3D objects
  - Form fields
  - Mathematical equations (without OCR)
  - Annotations
  - Footnotes (limited)
- [ ] Provide workarounds where possible

### 9.4 Polish
- [ ] Code cleanup and refactoring
- [ ] Performance optimization
- [ ] Memory usage optimization for large PDFs
- [ ] Progress indicators for batch processing

**Deliverable:** Production-ready documentation

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
