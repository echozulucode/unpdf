# unpdf Limitations and Known Issues

**Version:** 1.0.0  
**Last Updated:** 2025-11-02

This document outlines the limitations, unsupported features, and known issues in unpdf. Understanding these limitations helps you decide if unpdf is the right tool for your use case.

---

## Design Philosophy

unpdf follows the **80/20 rule**: Provide excellent quality on 80% of common use cases rather than mediocre quality on 100% of edge cases.

**What this means:**
- ✅ Excellent: Text-based PDFs (documentation, reports, technical content)
- ⚠️ Limited: Complex layouts (magazines, newspapers, forms)
- ❌ Not supported: Scanned PDFs, equations, annotations

---

## Not Supported

These features are **intentionally not supported** and are unlikely to be added in future versions:

### 1. Scanned PDFs (OCR Required)

**Issue:** unpdf only processes text-based PDFs. Scanned documents appear as images.

**Workaround:** Use OCR tools first:
- **Marker** - ML-based PDF converter with OCR
- **Tesseract** - Open-source OCR engine
- **Adobe Acrobat** - Commercial OCR solution

**Example:**
```bash
# Convert scanned PDF with Marker first
marker_single document_scanned.pdf output/
unpdf output/document_scanned.pdf
```

### 2. Mathematical Equations

**Issue:** LaTeX equations, MathML, and equation editor content not recognized.

**Workaround:**
- **Mathpix** - Converts equations to LaTeX
- **Marker** - Detects and preserves equations
- Manual editing after conversion

**Why not supported:** Requires ML models and complex math parsing libraries, contradicting our lightweight philosophy.

### 3. Form Fields

**Issue:** Interactive form elements (checkboxes, text inputs, dropdowns) not extracted.

**Workaround:**
- Fill and flatten forms before conversion
- Use Adobe Acrobat to export filled form as regular text
- Extract form field values separately (use PyPDF2 or similar)

### 4. Annotations and Comments

**Issue:** Sticky notes, highlights, comment threads not preserved.

**Workaround:**
- Export comments to separate document
- Flatten annotations before conversion

### 5. Video, Audio, and 3D Objects

**Issue:** Embedded multimedia not extracted or referenced.

**Workaround:** Extract media manually using dedicated tools.

### 6. Digital Signatures

**Issue:** Signature validation and metadata not preserved.

**Workaround:** Use specialized PDF security tools.

---

## Partially Supported

These features work in simple cases but have limitations:

### 1. Multi-Column Layouts

**Issue:** Reading order may be incorrect (might read horizontally across columns instead of vertically down each column).

**Workaround:**
- Manually reorder sections after conversion
- Use pdfplumber directly with custom column detection

**Status:** Planned improvement in v1.1

**Example Problem:**
```
PDF Layout:          Current Output:      Expected Output:
┌────┬────┐          Text A Text C       Text A
│ A  │ C  │          Text B Text D       Text B
│ B  │ D  │                              Text C
└────┴────┘                              Text D
```

### 2. Nested Lists (> 5 Levels)

**Issue:** Lists nested deeper than 5 levels may be flattened.

**Workaround:** Manually adjust indentation in output.

**Limitation:** Markdown itself has limited nested list support.

### 3. Complex Tables

**Issue:** Tables with merged cells, nested tables, or rotated content may not convert correctly.

**Workaround:**
- Simplify tables before generating PDF
- Manually reconstruct complex tables

**Known Problems:**
- Merged cells: Markdown doesn't support cell spanning
- Nested tables: Only outer table extracted
- Rotated text: May appear garbled or missing

**Example:**
```markdown
# Complex table in PDF:
┌──────┬──────┐
│  A   │   B  │
├──────┴──────┤  ← Merged cells
│  Combined   │
└─────────────┘

# Converted (best effort):
| A | B |
|---|---|
| Combined | |
```

### 4. Footnotes and Endnotes

**Issue:** Footnotes detected as regular text, not linked to references.

**Workaround:** Manually add footnote links using Markdown syntax.

**Status:** Potential future enhancement

### 5. Headers and Footers

**Issue:** Page headers/footers included in output, may appear repetitively.

**Workaround:**
- Process specific pages: `unpdf doc.pdf --pages 1-10`
- Manually remove repetitive headers after conversion

### 6. Images as Backgrounds

**Issue:** Images used as page backgrounds or watermarks extracted alongside content images.

**Workaround:** Manually review and remove unwanted image files.

---

## Known Quality Issues

Issues that affect output quality but don't break functionality:

### 1. Text Spacing

**Issue:** Some PDFs (especially Obsidian exports) have poor text spacing:
- Words merged together: "ListOrdered" instead of "List Ordered"
- Extra spaces: "hel  lo" instead of "hello"

**Root Cause:** PDF character positioning requires reconstruction of word boundaries.

**Status:** ⚠️ **Active Fix** - See [plan-002-conversion-quality-fixes.md](ai/plan-002-conversion-quality-fixes.md)

**Workaround:** Use PDFs from standard tools (Microsoft Word, LaTeX, Google Docs) which have better text extraction.

### 2. Code Block Formatting

**Issue:** Code blocks sometimes lose line breaks or indentation.

**Root Cause:** PDF doesn't preserve semantic "newline" information, only visual positioning.

**Status:** ⚠️ **Active Fix** - Phase 3 of Plan 002

**Workaround:** Manually reformat code blocks after conversion.

### 3. Heading Level Accuracy

**Issue:** Heading levels (H1-H6) may not match original document hierarchy.

**Adjustment:** Use `--heading-ratio` flag:
```bash
# More aggressive (detects more headings)
unpdf doc.pdf --heading-ratio 1.1

# More conservative (fewer headings)
unpdf doc.pdf --heading-ratio 1.5
```

**Why:** Font size heuristic works well for Word/LaTeX but struggles with some PDF generators.

### 4. Table Detection False Positives

**Issue:** Sometimes plain text detected as tables, creating malformed pipe tables.

**Root Cause:** Aligned text (like code indentation) can look like table columns.

**Status:** Improved in v1.0 with validation checks

**Workaround:** Review tables in output and manually fix if needed.

### 5. List Nesting Accuracy

**Issue:** Nested list indentation may not perfectly match source document.

**Root Cause:** PDF indentation measurements are approximate.

**Workaround:** Manually adjust indentation (Markdown allows 2-4 spaces per level).

---

## Performance Limitations

### 1. Large Files (>100 Pages)

**Memory Usage:** ~1-2MB per page in memory during processing.

**Recommendation:**
- Process in batches: `--pages 1-50`, then `--pages 51-100`
- Close other applications if memory-constrained
- Consider splitting large PDFs before conversion

**Example:**
```bash
# Split large PDF
unpdf manual.pdf --pages 1-50 -o part1.md
unpdf manual.pdf --pages 51-100 -o part2.md
unpdf manual.pdf --pages 101-150 -o part3.md

# Combine after
cat part*.md > complete.md  # Linux/Mac
type part*.md > complete.md  # Windows
```

### 2. Image-Heavy Documents

**Disk I/O:** Each image is extracted and saved separately, which is slow on HDDs.

**Recommendation:** Use SSD storage for better performance.

### 3. Complex Table Extraction

**Processing Time:** Table detection can be slow (0.5-2s per page with tables).

**Recommendation:** If tables aren't needed, use `--no-tables` flag (future feature).

---

## Comparison with Alternatives

When to use **unpdf** vs other tools:

### Use unpdf When:
- ✅ You need MIT licensing (no AGPL restrictions)
- ✅ Converting documentation, reports, technical content
- ✅ You want fast, predictable, explainable conversions
- ✅ You prefer lightweight dependencies (no ML/GPU)
- ✅ You're okay with 80% accuracy on common cases

### Use Marker When:
- 📊 Converting academic papers with equations
- 📊 Scanned PDFs (requires OCR)
- 📊 Complex layouts (multi-column, magazines)
- 📊 You need 95%+ accuracy on edge cases
- 📊 You have GPU resources available

### Use PyMuPDF When:
- 🔧 Building a commercial product with budget for licensing
- 🔧 Need comprehensive PDF manipulation (not just conversion)
- 🔧 Require pixel-perfect rendering
- 🔧 Can accept AGPL licensing terms

---

## Unsupported PDF Generators

Some PDF generators produce PDFs that are difficult to parse:

### ⚠️ Known Issues:

1. **Obsidian PDF Export**
   - Text spacing problems (words merge)
   - Table detection creates duplicates
   - **Status:** Active fixes in progress (Plan 002)

2. **Older PDF Versions (< 1.4)**
   - Limited metadata support
   - **Workaround:** Re-export as PDF 1.7+ in Adobe Acrobat

3. **Password-Protected PDFs**
   - Cannot open encrypted PDFs
   - **Workaround:** Remove password first using `qpdf` or Adobe Acrobat

4. **Linearized (Web-Optimized) PDFs**
   - May have incorrect page order
   - **Workaround:** Re-save as regular PDF

---

## Feature Requests: Not Planned

These features are **not planned** as they conflict with unpdf's design goals:

### ❌ GUI Application
**Reason:** CLI-first philosophy. Use wrapper scripts or integrate into existing workflows.

### ❌ Cloud/SaaS Version
**Reason:** Privacy and local-first design. Run unpdf on your own infrastructure.

### ❌ Real-Time Conversion
**Reason:** PDF parsing is inherently slow. For real-time needs, pre-convert documents.

### ❌ AI/ML Improvements
**Reason:** Contradicts transparency and lightweight goals. Use Marker for ML-based conversion.

### ❌ Full PDF Editor
**Reason:** Out of scope. Use dedicated PDF editors (PyMuPDF, Adobe Acrobat).

---

## Reporting Issues

If you encounter a limitation not listed here:

1. **Check existing issues:** [GitHub Issues](https://github.com/yourusername/unpdf/issues)
2. **Provide a sample:** Share the problematic PDF (if not confidential)
3. **Describe expected behavior:** What should happen vs what actually happens
4. **Environment details:** OS, Python version, unpdf version

### Bug Report Template:

```markdown
**Issue:** Brief description

**PDF Source:** [Word, LaTeX, Obsidian, etc.]

**Command:**
```bash
unpdf document.pdf -o output.md
```

**Expected Output:**
[Describe what should appear]

**Actual Output:**
[What actually appeared]

**Environment:**
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Python: 3.10 / 3.11 / 3.12
- unpdf: 1.0.0
```

---

## Workarounds and Best Practices

### General Tips:

1. **Test on a single page first:**
   ```bash
   unpdf doc.pdf --pages 1 -o test.md
   ```

2. **Use verbose mode for debugging:**
   ```bash
   unpdf doc.pdf --verbose
   ```

3. **Adjust thresholds for your document type:**
   ```bash
   # Technical docs (lots of headings)
   unpdf doc.pdf --heading-ratio 1.2
   
   # Business reports (fewer headings)
   unpdf doc.pdf --heading-ratio 1.5
   ```

4. **Process in batches for large documents:**
   ```bash
   for i in {1..10}; do
       start=$((($i-1)*10+1))
       end=$(($i*10))
       unpdf large.pdf --pages $start-$end -o part$i.md
   done
   ```

5. **Validate output quality:**
   - Always review first conversion
   - Spot-check tables, code blocks, lists
   - Verify links work

6. **Pre-process PDFs for better results:**
   - Flatten forms and annotations
   - Remove password protection
   - Re-export from source application if possible

---

## Future Improvements

See [docs/ai/plan-001-implementation.md](ai/plan-001-implementation.md) for planned enhancements.

**Roadmap highlights:**
- v1.1: Plugin system, better column detection, streaming API
- v2.0: Optional OCR plugin, watch mode, VS Code extension

---

**Questions?** See [USER_GUIDE.md](USER_GUIDE.md) or ask in [GitHub Discussions](https://github.com/yourusername/unpdf/discussions).
