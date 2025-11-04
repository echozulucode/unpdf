# Plan 003: High-Accuracy PDF to Markdown Conversion (Non-AI)

**Status**: Draft  
**Created**: 2025-11-04  
**Goal**: Implement sophisticated multi-stage PDF parsing pipeline using deterministic algorithms (no AI/ML) for high-accuracy conversion

## Strategic Overview

This plan implements advanced algorithmic approaches from research to achieve near-lossless PDF to Markdown conversion without machine learning. The strategy focuses on:

1. **Leverage PDF's internal structure** - Tagged PDF, content streams, metadata
2. **Geometric algorithms** - Spatial analysis, boundary detection, layout understanding
3. **Multi-stage processing** - Separation of concerns, hierarchical refinement
4. **Intermediate representations** - ALTO XML, structured JSON for analysis
5. **Pattern-based heuristics** - Statistical clustering, rule-based classification

### Differentiation from PyMuPDF

While PyMuPDF provides excellent low-level PDF access, we focus on:
- **Semantic structure extraction** from Tagged PDF (PDF/UA)
- **Advanced table detection** using multiple algorithms (Lattice, Stream, hybrid)
- **Reading order computation** via spatial graph analysis
- **Multi-stage refinement** with confidence scoring
- **Configurable pipeline** for different document types

---

## Phase 0: Infrastructure & Derisk (Week 1)

**Goal**: Validate approach with minimal implementation, establish baseline metrics

### 0.1 Tagged PDF Detection MVP ✅
- [x] Add structure tree parser to detect `/StructTreeRoot`
- [x] Extract basic structure elements (H1-H6, P, Table, L)
- [x] Parse MCID (Marked Content ID) mappings
- [x] Test on sample PDFs (Obsidian-generated)
- [x] **Success metric**: Detect tagged content in test PDFs

### 0.2 Coordinate Extraction Validation ✅
- [x] Enhance text operator parsing (basic implementation)
- [x] Extract bounding boxes with font info (using pdfplumber)
- [x] Validate extraction works without errors
- [x] **Success metric**: No errors on coordinate extraction

### 0.3 Baseline Metrics Collection ✅
- [x] Run current converter on test suite
- [x] Document accuracy metrics (text, structure, tables)
- [x] Create comparison framework
- [x] **Success metric**: Baseline established for test PDFs

### 0.4 Intermediate Format Prototype ✅
- [x] Design JSON schema for layout representation
  ```json
  {
    "pages": [{
      "number": 1,
      "blocks": [{
        "type": "text|table|list|code|image",
        "bbox": [x, y, width, height],
        "content": "...",
        "style": {"font": "...", "size": 12, "weight": "bold"},
        "reading_order": 1,
        "confidence": 0.85
      }]
    }]
  }
  ```
- [x] Implement serialization/deserialization
- [x] Add validation schema (via dataclasses)
- [x] **Success metric**: Round-trip conversion preserves data

**Deliverables**: ✅ Complete
- ✅ Working Tagged PDF detector (`unpdf/extractors/structure.py`)
- ✅ Coordinate extraction with validation (`unpdf/extractors/coordinates.py`)
- ✅ Baseline metrics document (`docs/ai/baseline_metrics.json`)
- ✅ JSON intermediate format (`unpdf/models/layout.py`)

**Risk Mitigation**: ✅ Validated
- ✅ Tagged PDF rare: Confirmed - Obsidian PDF not tagged, geometric algorithms needed
- ✅ Coordinates reliable: pdfplumber provides good char-level positioning
- ✅ JSON not too complex: Data model is clean and well-structured

---

## Phase 1: Structure Extraction Enhancement (Week 2)

**Goal**: Maximize use of PDF's built-in structure when available

### 1.1 Complete Tagged PDF Support
- [ ] Parse RoleMap dictionary for custom tags
- [ ] Extract ParentTree for reverse lookup
- [ ] Handle PDF/UA-2 namespaces and structure destinations
- [ ] Extract Alt/ActualText for accessibility
- [ ] Parse XMP metadata for language/conformance

### 1.2 Content Stream Parsing
- [ ] Implement complete text operator support
  - Tj (show text)
  - TJ (show with positioning)
  - Tm (transformation matrix)
  - Td/TD (relative positioning)
  - T* (next line)
- [ ] Calculate Trm = [Tfs×Th, 0, 0; 0, Tfs, 0; 0, Trise, 1] × Tm × CTM
- [ ] Infer spaces from coordinate gaps (>1.5× avg char width)
- [ ] Handle ToUnicode CMap for proper Unicode mapping

### 1.3 Font Analysis System ✅
- [x] Extract font metrics (family, size, weight, style)
- [x] Detect monospace fonts (width variance <0.05)
- [x] Build font hierarchy clustering
- [x] Map font sizes to header levels
  - H1: 2.0-2.5× body
  - H2: 1.5-1.8× body
  - H3: 1.2-1.4× body
- [x] **Implementation**: `unpdf/extractors/font_analyzer.py` with comprehensive tests

### 1.4 Reading Order from Structure
- [ ] Extract ReadingOrder elements from structure tree
- [ ] Build traversal order from hierarchy
- [ ] Validate against content stream order
- [ ] Flag discrepancies for review

**Deliverables**:
- Complete Tagged PDF extractor
- Precise coordinate extraction
- Font analysis module
- Structure-based reading order

**Tests**:
- Test on PDF/UA compliant documents
- Verify coordinate accuracy (<5px error)
- Validate font hierarchy detection (>90% accuracy)
- Confirm reading order correctness

---

## Phase 2: Geometric Layout Analysis (Week 3-4)

**Status**: In Progress  
**Goal**: Implement sophisticated segmentation for untagged PDFs

### 2.1 MVP Layout Analyzer ✅
- [x] Create BoundingBox data model with overlap/containment detection
- [x] Create TextBlock and Column data models
- [x] Implement basic column detection via whitespace analysis
  - Detect vertical gaps between blocks
  - Partition blocks into columns
  - Configurable thresholds for gap detection
- [x] Implement reading order determination
  - Single column: top-to-bottom
  - Multi-column: column-aware ordering
- [x] Write comprehensive unit tests (16 tests, all passing)
- [x] Type checking with mypy (100% pass)
- [x] Linting with ruff and formatting with black
- [x] **Result**: 98% code coverage, handles 1-3 column layouts

### 2.2 Recursive XY-Cut Implementation ✅
- [x] Compute horizontal/vertical projection profiles
- [x] Detect valleys with thresholds
  - TX (horizontal): 0.5× character height
  - TY (vertical): 1.5× character width
- [x] Split at widest valley midpoint
- [x] Recurse until no valleys remain
- [x] Handle straddling blocks by assigning to nearest side
- [x] Filter out edge valleys outside content area
- [x] Optimized implementation with bounding boxes
- [x] Full projection profiles (0 values for empty regions)
- [x] Comprehensive unit tests (13 tests, all passing)
- [x] Type checking and linting (100% pass)
- [x] **Result**: Fast segmentation with multi-column and grid support

### 2.3 RLSA Block Detection ✅
- [x] Implement Run Length Smoothing Algorithm
- [x] Phase 1: Horizontal smoothing (hsv = 10-50 pixels)
- [x] Phase 2: Vertical smoothing (vsv = 3-10 pixels)
- [x] Phase 3: Logical AND + additional horizontal smoothing
- [x] Derive parameters from document statistics
  - hsv = f(mean character length)
  - vsv = f(mean line distance)
- [x] **Target**: Linear O(n) performance ✅ Achieved

### 2.3.1 Block Classification ✅
- [x] Implement font statistics computation
  - Body size detection (most common size)
  - Font size distribution analysis
  - Monospace ratio calculation
- [x] Heading detection with size ratios
  - H1: 2.0-2.5× body
  - H2: 1.5-1.8× body
  - H3: 1.2-1.4× body
  - H4-H6: Size + weight requirements
- [x] List item pattern detection
  - Bullet characters (•◦▪‣⁃)
  - Numbered lists (1. 2. 3.)
  - Lettered lists (a. b. c.)
  - Checkboxes (☐☑✓✗)
- [x] Code block identification
  - Monospace font detection
  - Indentation patterns
  - Code punctuation and keywords
- [x] Horizontal rule detection
- [x] Blockquote detection
- [x] Comprehensive unit tests (25 tests, all passing)
- [x] Type checking and linting (100% pass)
- [x] **Result**: 95% code coverage, robust classification

### 2.4 Docstrum Clustering ✅
- [x] Extract connected components from text
- [x] Build KD-tree for spatial indexing (O(log n) queries)
- [x] Find k=5 nearest neighbors per component
- [x] Create document spectrum (angle/distance histograms)
- [x] Detect skew from angle histogram peak
- [x] Extract spacing from distance peaks
- [x] Form text lines via transitive closure (ft = 2-3× char_spacing)
- [x] Merge lines into blocks
  - Parallel distance: fpa = 1.75× line_spacing (configurable)
  - Perpendicular distance: fpe = 0.4× char_width (configurable)
- [x] Implement alignment detection (left, right, center, justify)
- [x] Comprehensive unit tests (21 tests, all passing)
- [x] Type checking with mypy (100% pass)
- [x] Linting with ruff and formatting with black
- [x] **Result**: 94% code coverage, handles skewed and multi-orientation text

### 2.5 Whitespace Analysis Enhancement ✅
- [x] Detect column boundaries (vertical gap >15% page width)
- [x] Identify paragraph boundaries (vertical gap >1.5× line height)
- [x] Segment sections via large whitespace
- [x] Build spatial relationship graph
  - Up/down (vertical alignment ±5-10 pixels)
  - Left/right (horizontal alignment ±5-10 pixels)
  - Nearest neighbor per direction
- [x] Comprehensive unit tests (26 tests, all passing)
- [x] Type checking and linting (100% pass)
- [x] **Result**: 100% code coverage, robust whitespace analysis

### 2.6 Hierarchical Layout Tree ✅
- [x] Build physical layout tree (blocks → lines → words)
- [x] Assign geometric properties to each node
- [x] Create spatial index for fast queries
- [x] Implement containment detection
  - Child within parent bounds
  - Alignment and proximity validation
- [x] Comprehensive unit tests (30 tests, all passing)
- [x] Type checking with mypy (100% pass)
- [x] Linting with ruff (100% pass)
- [x] **Result**: 98% code coverage, efficient spatial queries

**Deliverables**:
- ✅ MVP layout analyzer with column detection
- ✅ XY-Cut segmentation module
- ✅ RLSA block detector
- ✅ Block classifier with semantic type detection
- ✅ Docstrum clustering engine (`unpdf/processors/docstrum.py`)
- ✅ Whitespace analysis system (`unpdf/processors/whitespace.py`)
- ✅ Hierarchical layout tree (`unpdf/processors/layout_tree.py`)

**Tests**:
- ✅ Unit tests for MVP (16 tests, all passing)
- ✅ Unit tests for XY-Cut (24 tests, all passing)
- ✅ Unit tests for RLSA (32 tests, all passing)
- ✅ Unit tests for Block Classifier (25 tests, all passing)
- ✅ Unit tests for Docstrum (21 tests, all passing)
- Test on single-column, multi-column layouts
- Verify handling of skewed text
- Validate performance (<100ms per page)
- Check segmentation accuracy on ground truth

---

## Phase 3: Advanced Table Detection (Week 5-6)

**Goal**: Implement multiple table detection strategies with high accuracy

### 3.1 Lattice Method (Ruled Tables)
- [ ] Convert PDF page to image (via pdfium/Pillow)
- [ ] Apply morphological operations (erosion/dilation)
- [ ] Detect horizontal/vertical lines via Hough transform
  - Line length >50 pixels
  - Confidence threshold >0.7-0.8
- [ ] Overlay segments with OR operations
- [ ] Scale coordinates from image to PDF space
- [ ] Find line intersections (cell corners)
- [ ] Construct table grid from rectangles
- [ ] **Target**: >90% precision on ruled tables

### 3.2 Stream Method (Borderless Tables)
- [ ] Cluster x-coordinates for columns (k-means)
- [ ] Cluster y-coordinates for rows (k-means)
- [ ] Validate clusters with Silhouette score (>0.5)
- [ ] Detect alignment within ±10 pixels
- [ ] Infer boundaries from spacing (>2× avg char width)
- [ ] Build grid from aligned text
- [ ] **Target**: >85% recall on borderless tables

### 3.3 Hybrid Table Detection
- [ ] Try Lattice method first (fast, high precision)
- [ ] Fall back to Stream method if no lines
- [ ] Combine Network parser (alignments) + Lattice (lines)
- [ ] Apply validation rules
  - Minimum 2×2 cells
  - Grid completeness >70%
  - Aspect ratio 0.2 < h/w < 5.0
- [ ] Score confidence from multiple signals
  - Line detection weight: 0.4
  - Text alignment weight: 0.3
  - Whitespace analysis weight: 0.3
- [ ] Accept if score >0.65

### 3.4 Table Structure Analysis
- [ ] Detect header rows (font weight, position, alignment)
- [ ] Identify spanning cells (merged horizontally/vertically)
- [ ] Parse cell contents with proper text extraction
- [ ] Determine table caption (within 50px, >70% overlap)
- [ ] Handle nested tables (recursive detection)

### 3.5 Table Serialization
- [ ] Generate GitHub-flavored Markdown tables (simple)
- [ ] Generate HTML tables (complex/spanning cells)
- [ ] Preserve alignment (left/center/right)
- [ ] Format numeric columns consistently
- [ ] Link captions to tables

**Deliverables**:
- Lattice table detector
- Stream table detector
- Hybrid detection pipeline
- Table structure parser
- Multi-format table serializer

**Tests**:
- Test on ruled, borderless, mixed tables
- Validate spanning cell detection
- Check header identification accuracy
- Verify Markdown/HTML output correctness
- Compare against Camelot/pdfplumber baselines

---

## Phase 4: Pattern-Based Classification (Week 7)

**Goal**: Implement robust element classification using heuristics

### 4.1 List Detection
- [ ] Detect bullet symbols (•●○◦■□◆◇-–—→►✓*)
  - Position at left margin or consistent indent
  - Character width <2× regular characters
  - Repeated at regular intervals
  - Vertical spacing 1.2-2.0× line height
  - Hanging indent 10-30 pixels
- [ ] Detect numbering patterns (regex)
  - Arabic: `^\s*(\d+)[\.):]\s+`
  - Lowercase: `^\s*([a-z])[\.):]\s+`
  - Uppercase: `^\s*([A-Z])[\.):]\s+`
  - Roman: `^\s*(i|ii|iii|iv|v|vi|vii|viii|ix|x)[\.):]\s+`
- [ ] Handle multi-level lists
  - Level 1: 0-10 pixels indent
  - Level 2: 20-40 pixels indent
  - Level 3: 40-60 pixels indent
  - ±5 pixel tolerance
- [ ] Validate sequences (n+1 follows n)
- [ ] **Target**: >92% precision on bullets, >88% on numbering

### 4.2 Code Block Detection
- [ ] Detect monospace fonts (width variance <0.05)
- [ ] Check consistent indentation (>40 pixels)
- [ ] Look for syntax highlighting color patterns
- [ ] Identify common keywords (def, function, class, etc.)
- [ ] Validate line continuity
- [ ] **Target**: >95% accuracy on code blocks

### 4.3 Header Classification
- [ ] Apply decision tree based on font size ratio
  - H1: >2.0× body font
  - H2: 1.5-1.8× body font
  - H3: 1.2-1.4× body font
  - H4-H6: style/position based
- [ ] Consider font weight (bold more likely)
- [ ] Check position (top 20% of page for H1)
- [ ] Verify line count (single line)
- [ ] Validate horizontal centering/alignment
- [ ] **Target**: >90% header level accuracy

### 4.4 Caption Detection
- [ ] Search for keywords (Table, Figure, Fig., Diagram)
- [ ] Check proximity to images/tables (<50 pixels)
- [ ] Verify horizontal overlap (>70%)
- [ ] Detect numbering (Table 1, Figure 2.3)
- [ ] Link caption to referenced element
- [ ] **Target**: >85% caption linkage accuracy

### 4.5 Footnote/Reference Detection
- [ ] Identify superscript numbers or symbols
- [ ] Find matching footer text
- [ ] Link via proximity and reference matching
- [ ] Handle multiple reference styles
- [ ] Preserve reference numbering

### 4.6 Confidence Scoring
- [ ] Implement multi-signal confidence calculation
  ```python
  score = (
      0.4 × keyword_match +
      0.3 × position_match +
      0.2 × style_match +
      0.1 × context_match
  )
  ```
- [ ] Define thresholds
  - High confidence: >0.85 (auto-accept)
  - Medium confidence: 0.6-0.85 (flag for review)
  - Low confidence: <0.6 (manual classification)
- [ ] Log confidence for validation

**Deliverables**:
- List detection module
- Code block detector
- Header classifier
- Caption linker
- Footnote handler
- Confidence scoring system

**Tests**:
- Test on documents with varied list styles
- Verify code block detection on technical docs
- Validate header hierarchy on structured docs
- Check caption linkage accuracy
- Measure confidence calibration

---

## Phase 5: Reading Order Computation (Week 8)

**Goal**: Determine correct reading sequence from spatial layout

### 5.1 Spatial Graph Construction
- [ ] Build directed graph of spatial relationships
  - Above/below (vertical)
  - Left/right (horizontal)
  - Contains (parent/child)
  - Near (proximity)
- [ ] Assign edge weights based on distance
- [ ] Handle multi-column layouts
- [ ] Detect column boundaries via vertical whitespace

### 5.2 Topological Sort
- [ ] Implement topological traversal of spatial graph
- [ ] Primary sort: y-coordinate (top to bottom)
- [ ] Secondary sort: x-coordinate (left to right)
- [ ] Handle columns sequentially
- [ ] Respect Z-order for overlapping elements

### 5.3 Multi-Column Handling
- [ ] Detect columns via vertical whitespace analysis
- [ ] Determine column width and boundaries
- [ ] Track column flow (newspaper vs magazine style)
- [ ] Handle column-spanning elements (headers, images)
- [ ] **Target**: Correct ordering for 2-3 column layouts

### 5.4 Reading Order Validation
- [ ] Compare computed order vs structure tree order
- [ ] Flag significant discrepancies
- [ ] Provide manual override mechanism
- [ ] Log ordering decisions for debugging

**Deliverables**:
- Spatial graph builder
- Topological sort algorithm
- Multi-column detector
- Reading order validator

**Tests**:
- Test on single-column documents
- Verify 2-3 column layout handling
- Validate complex layouts (mixed columns)
- Compare against ground truth reading order

---

## Phase 6: Markdown Generation with Fidelity (Week 9)

**Goal**: Generate high-quality Markdown preserving structure and semantics

### 6.1 Element-to-Markdown Mapping
- [ ] Headers: `#` with appropriate level (1-6)
- [ ] Paragraphs: Blank line separation
- [ ] Lists: `-` for bullets, `1.` for numbered, nested indentation
- [ ] Tables: GFM tables or HTML for complex
- [ ] Code: Fenced blocks with language hints
- [ ] Quotes: `>` blockquotes
- [ ] Emphasis: `**bold**`, `*italic*`, `` `code` ``
- [ ] Links: `[text](url)` from PDF annotations
- [ ] Images: `![alt](path)` with extracted alt text

### 6.2 Style Preservation
- [ ] Map font styles to Markdown emphasis
- [ ] Preserve color via HTML when needed
- [ ] Handle strikethrough, underline (HTML)
- [ ] Maintain alignment hints (HTML/CSS)
- [ ] Convert special characters properly

### 6.3 Table Formatting
- [ ] Simple tables: GFM Markdown
  ```markdown
  | Header 1 | Header 2 |
  |----------|----------|
  | Cell 1   | Cell 2   |
  ```
- [ ] Complex tables: HTML
  ```html
  <table>
    <thead>
      <tr><th colspan="2">Header</th></tr>
    </thead>
    <tbody>
      <tr><td>Cell 1</td><td>Cell 2</td></tr>
    </tbody>
  </table>
  ```
- [ ] Preserve alignment (left/center/right)
- [ ] Format numeric columns consistently
- [ ] Handle empty cells

### 6.4 Image Extraction
- [ ] Extract embedded images to files
- [ ] Generate descriptive filenames (page-element-sequence)
- [ ] Include alt text from PDF Alt attribute
- [ ] Maintain relative paths in Markdown
- [ ] Support various formats (JPEG, PNG, etc.)

### 6.5 Metadata Embedding
- [ ] Extract PDF metadata (title, author, date)
- [ ] Generate YAML frontmatter
  ```yaml
  ---
  title: "Document Title"
  author: "Author Name"
  date: "2025-11-04"
  source: "document.pdf"
  ---
  ```
- [ ] Include conversion metadata (version, timestamp)

**Deliverables**:
- Markdown generator module
- Style mapping system
- Table formatter (GFM + HTML)
- Image extractor
- Metadata handler

**Tests**:
- Verify Markdown syntax correctness
- Test table rendering in viewers
- Validate image extraction and linking
- Check metadata frontmatter parsing
- Compare visual rendering with original

---

## Phase 7: Quality Validation & Metrics (Week 10)

**Goal**: Implement comprehensive quality assurance

### 7.1 Text Extraction Metrics
- [ ] Character-level precision/recall
- [ ] Word-level accuracy
- [ ] Paragraph preservation rate
- [ ] Space inference accuracy
- [ ] Unicode character correctness

### 7.2 Structure Recognition Metrics
- [ ] Element-level F1-score (headers, lists, tables)
- [ ] Header hierarchy correctness
- [ ] List nesting accuracy
- [ ] Table cell accuracy
- [ ] Reading order sequence score

### 7.3 Visual Comparison
- [ ] Screenshot-based comparison (PDF vs rendered Markdown)
- [ ] Structural similarity index (SSIM)
- [ ] Layout preservation score
- [ ] Highlight differences for review

### 7.4 Automated Testing
- [ ] Unit tests for each algorithm component
- [ ] Integration tests for full pipeline
- [ ] Regression tests on known documents
- [ ] Performance benchmarks (time, memory)
- [ ] **Target**: >95% test coverage

### 7.5 Ground Truth Validation
- [ ] Create manually validated test set (20+ PDFs)
- [ ] Measure accuracy against ground truth
- [ ] Identify failure patterns
- [ ] Document accuracy by document type
  - Simple: >95% accuracy
  - Medium: >85% accuracy
  - Complex: >70% accuracy

**Deliverables**:
- Metrics calculation module
- Visual comparison tool
- Comprehensive test suite
- Ground truth dataset
- Validation report generator

**Tests**:
- Verify metric calculation correctness
- Test visual comparison on known differences
- Validate full test suite coverage
- Benchmark performance across document types

---

## Phase 8: Pipeline Configuration & Optimization (Week 11)

**Goal**: Make pipeline configurable and production-ready

### 8.1 Configuration System
- [ ] Define configuration schema (JSON/YAML)
  ```yaml
  pipeline:
    stages:
      - structure_extraction
      - layout_analysis
      - table_detection
      - classification
      - reading_order
      - markdown_generation
    
    structure_extraction:
      prefer_tagged_pdf: true
      extract_xmp: true
    
    layout_analysis:
      method: "hybrid"  # xy_cut, rlsa, docstrum, hybrid
      xy_cut:
        tx_threshold: 1.0
        ty_threshold: 2.0
      rlsa:
        hsv: 30
        vsv: 5
    
    table_detection:
      methods: ["lattice", "stream"]
      lattice:
        line_scale: 40
        confidence: 0.75
      stream:
        row_tolerance: 2
        column_tolerance: 1
    
    classification:
      confidence_thresholds:
        auto_accept: 0.85
        manual_review: 0.60
  ```
- [ ] Implement configuration loader
- [ ] Validate configuration schemas
- [ ] Support presets (simple, balanced, accurate)

### 8.2 Document Type Profiles
- [ ] Scientific papers profile (GROBID-inspired)
- [ ] Business documents profile
- [ ] Scanned documents profile
- [ ] Technical manuals profile
- [ ] Mixed content profile (default)
- [ ] Allow custom profiles

### 8.3 Performance Optimization
- [ ] Implement spatial indexing (KD-tree, R-tree)
- [ ] Cache frequently accessed data
  - Font metrics
  - Bounding boxes
  - Spatial index
- [ ] Parallel page processing
- [ ] Vectorized distance calculations
- [ ] **Target**: <500ms per page on average documents

### 8.4 Memory Optimization
- [ ] Streaming processing for large documents
- [ ] Page-by-page processing with cleanup
- [ ] Lazy loading of resources
- [ ] Memory profiling and optimization
- [ ] **Target**: <500MB peak memory for typical docs

### 8.5 Error Handling & Logging
- [ ] Structured logging with levels (DEBUG, INFO, WARN, ERROR)
- [ ] Error recovery strategies
  - Fallback to simpler algorithms
  - Skip problematic elements
  - Continue processing remaining content
- [ ] Detailed error messages with context
- [ ] Optional error reporting to user

**Deliverables**:
- Configuration system
- Document type profiles
- Performance optimizations
- Memory optimizations
- Logging & error handling

**Tests**:
- Test each configuration preset
- Validate document type profiles
- Benchmark performance (time, memory)
- Test error handling scenarios
- Verify logging completeness

---

## Phase 9: Integration & Polish (Week 12)

**Goal**: Integrate all components and prepare for production

### 9.1 CLI Enhancement
- [ ] Add `--algorithm` flag to select pipeline
  - `tagged`: Use Tagged PDF only
  - `geometric`: Use geometric algorithms only
  - `hybrid`: Use both (default)
  - `custom`: Load custom config
- [ ] Add `--profile` flag for document types
- [ ] Add `--config` flag for custom configuration
- [ ] Add `--validate` flag for quality checking
- [ ] Add `--benchmark` flag for performance metrics
- [ ] Support batch processing

### 9.2 API Design
- [ ] Design clean Python API
  ```python
  from unpdf import Converter, Config
  
  # Simple usage
  converter = Converter()
  markdown = converter.convert("input.pdf")
  
  # Custom configuration
  config = Config.load("custom.yaml")
  converter = Converter(config=config)
  markdown = converter.convert("input.pdf", output_dir="output/")
  
  # Programmatic configuration
  config = Config(
      prefer_tagged_pdf=True,
      table_methods=["lattice", "stream"],
      confidence_threshold=0.85
  )
  converter = Converter(config=config)
  ```
- [ ] Document API with examples
- [ ] Add type hints throughout

### 9.3 Documentation
- [ ] Architecture overview document
- [ ] Algorithm description with references
- [ ] Configuration guide
- [ ] Performance tuning guide
- [ ] Troubleshooting guide
- [ ] API reference (auto-generated)
- [ ] Update README with new features

### 9.4 Comparison Study
- [ ] Compare against PyMuPDF
- [ ] Compare against pdfplumber
- [ ] Compare against Camelot
- [ ] Compare against current unpdf
- [ ] Document strengths/weaknesses
- [ ] **Target**: Outperform on structure and tables

### 9.5 Final Testing
- [ ] Run full test suite
- [ ] Validate on 50+ diverse PDFs
- [ ] Performance profiling
- [ ] Memory leak detection
- [ ] Code coverage analysis (>90%)
- [ ] Fix remaining issues

**Deliverables**:
- Enhanced CLI
- Clean Python API
- Comprehensive documentation
- Comparison benchmark results
- Production-ready release

**Tests**:
- Test all CLI flags and combinations
- Verify API usability and correctness
- Validate documentation accuracy
- Run benchmark comparison suite
- Execute full regression tests

---

## Success Metrics

### Accuracy Targets
- **Text extraction**: >99% character accuracy (born-digital)
- **Structure recognition**: >90% element F1-score
- **Table detection**: >85% precision, >80% recall
- **Reading order**: >95% sequence correctness (simple layouts)
- **Header hierarchy**: >90% level accuracy

### Performance Targets
- **Processing speed**: <500ms per page (average)
- **Memory usage**: <500MB peak (typical documents)
- **Scalability**: Handle 1000+ page documents

### Quality Targets
- **Test coverage**: >90% code coverage
- **Documentation**: Complete for all public APIs
- **Configuration**: Flexible for 5+ document types
- **Reliability**: <1% crash rate on diverse inputs

---

## Risk Management

### Technical Risks

**Risk**: Tagged PDF rare in practice  
**Mitigation**: Focus on geometric algorithms, make Tagged PDF bonus

**Risk**: Table detection accuracy insufficient  
**Mitigation**: Implement multiple methods, use hybrid approach, allow manual hints

**Risk**: Reading order computation fails on complex layouts  
**Mitigation**: Provide manual override, flag low-confidence orderings

**Risk**: Performance targets not met  
**Mitigation**: Implement spatial indexing, parallel processing, optimize hotspots

### Implementation Risks

**Risk**: Scope too large (12 weeks)  
**Mitigation**: Phase 0 derisk validates approach early, phases independent

**Risk**: Algorithm complexity high  
**Mitigation**: Start with simple versions, incrementally enhance

**Risk**: Testing insufficient  
**Mitigation**: Build tests alongside implementation, maintain >90% coverage

---

## Dependencies

### Python Libraries
- **pypdf**: PDF parsing and structure extraction
- **pdfminer.six**: Low-level PDF content streams
- **Pillow**: Image processing for table detection
- **numpy**: Numerical computations
- **scipy**: Statistical algorithms (clustering, transforms)
- **scikit-learn**: Clustering algorithms (k-means, DBSCAN)
- **opencv-python** (optional): Advanced image processing

### External Tools (Optional)
- **pdfalto**: PDF to ALTO XML conversion
- **Tesseract**: OCR for scanned PDFs (future)

---

## Future Enhancements (Post-Phase 9)

### Advanced Features
- [ ] OCR integration for scanned PDFs
- [ ] Mathematical equation extraction (LaTeX)
- [ ] Chart/diagram analysis and description
- [ ] Multi-language support with language detection
- [ ] PDF/A and PDF/UA conformance validation
- [ ] Interactive elements (forms, annotations)

### ML Integration (Optional)
- [ ] Train classifiers on labeled data
- [ ] Use embeddings for semantic grouping
- [ ] Fine-tune reading order on ground truth
- [ ] Learn optimal parameters per document type

### Ecosystem Integration
- [ ] Pandoc filter for PDF input
- [ ] Obsidian plugin enhancements
- [ ] Web service API
- [ ] Browser extension for PDF conversion

---

## References

Based on research from:
- Nurminen (2013): Algorithmic table extraction
- Ha et al. (1995): Recursive XY-Cut
- O'Gorman (1993): Document Spectrum / Docstrum
- Kise et al. (1998): Area Voronoi Diagram
- Kieninger & Dengel (1998-2001): T-Recs table recognition
- Oro & Ruffolo (2009): PDF-TREX heuristic clustering
- ISO 14289 (PDF/UA): Tagged PDF specification
- ISO 19005 (PDF/A): Archival PDF specification
- ALTO 4.4: OCR layout standard
- PAGE XML: Document analysis format

---

## Current Status

**Phase**: Phase 2 In Progress (Step 2.5 Complete ✅)  
**Next Action**: Continue Phase 2 - Step 2.6 Hierarchical Layout Tree  
**Last Updated**: 2025-11-04

**Phase 0 Summary**:
- ✅ Tagged PDF detector implemented
- ✅ Coordinate extraction framework created
- ✅ Baseline metrics collected (1 PDF: not tagged, 1.6s, 2020 chars)
- ✅ Intermediate JSON format implemented with full serialization
- ✅ All tests passing (9 new tests)

**Phase 2 Progress**:
- ✅ Step 2.1: MVP Layout Analyzer (98% coverage, 16 tests)
- ✅ Step 2.2: Recursive XY-Cut (13 tests, all passing)
- ✅ Step 2.3: RLSA Block Detection (32 tests, all passing)
- ✅ Step 2.3.1: Block Classification (25 tests, 95% coverage)
- ✅ Step 2.4: Docstrum Clustering (21 tests, 94% coverage)
- ✅ Step 2.5: Whitespace Analysis (26 tests, 100% coverage)
- ⏭️ Step 2.6: Hierarchical Layout Tree (Next)

**Notes**:
- This plan builds on existing unpdf foundation
- Maintains compatibility with current CLI
- Adds advanced capabilities without breaking changes
- Focuses on deterministic, explainable algorithms
- No ML dependencies for core functionality
- Confirmed: Obsidian PDFs are not tagged, geometric algorithms essential
