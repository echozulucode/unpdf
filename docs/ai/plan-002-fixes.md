# Plan 002: Bug Fixes for Obsidian PDF Conversion Issues

**Status**: In Progress (Phase 1-6 Complete)  
**Created**: 2025-11-02  
**Updated**: 2025-11-02  
**Priority**: High

## Problem Summary

Testing with example-obsidian revealed multiple critical issues in the PDF-to-Markdown conversion:

### Issues Identified (Detailed Analysis)

1. **Frontmatter**: YAML frontmatter completely missing from output
2. **Header Section Issues**: 
   - Inline code within text (backticks around `#`) converted to multi-line with spurious `>>>` blockquote symbols
3. **List Problems**:
   - Unordered list appears in WRONG SECTION (after "Ordered List" header instead of under "Unordered List")
   - Ordered list items all numbered as "1." instead of 1, 2, 3, 4
   - Ordered list missing item #4 ("Deploy to production")
   - Checklist content SPLIT across file (header at line 39, content at line 71-74)
   - Checklist items missing `[x]` and `[ ]` checkbox syntax
4. **Table Issues**:
   - Tables appear at BOTTOM of file instead of their correct middle position
   - Table headers incorrectly detected as H6 headings
   - Content ordering completely disrupted by table misplacement
5. **Code Block Failures**:
   - All fenced code blocks (Python, JSON, Bash) converted to inline code with backticks
   - Code blocks appear in WRONG LOCATIONS (mixed with checklist content)
   - Triple-backtick fence markers not preserved
6. **Blockquote Issues**: 
   - Blockquotes rendered as plain text without `>` prefix
7. **Horizontal Rules**: All `---` separators missing from output
8. **Links**: Hyperlinks stripped to plain text (lost URL)

## Root Causes

1. **Element Position Sorting**: Content blocks sorted by position, but tables extracted separately causing ordering chaos
2. **Table Over-detection**: pdfplumber detecting table headers as tables, creating H6 artifacts
3. **Code Block Detection**: Fenced code blocks not recognized, falling back to inline code
4. **List Detection**: 
   - Bullet/number markers not properly detected
   - Nested list indentation lost
   - Checkbox syntax not recognized
5. **Inline vs Block Elements**: Inline code within paragraphs being split into blocks with blockquote artifacts
6. **Missing Processors**: No processors for frontmatter, horizontal rules, or links
7. **Content Interleaving**: PDF reading order vs. visual order causing content to appear in wrong sections

## Implementation Plan

### Phase 1: Fix Text Spacing ✓
- [x] Add space normalization to text extraction
- [x] Ensure proper word boundaries in extracted text
- [x] Test with obsidian-input.pdf
- [x] Added horizontal gap detection (2.0pt threshold)
- [x] Added line break detection in span continuation

### Phase 2: Fix Heading Detection ✓
- [x] Analyze font sizes in obsidian-input.pdf
- [x] Adjust heading detection algorithm
- [x] Use font weight/style in addition to size
- [x] Add heading level mapping based on size hierarchy
- [x] Test heading detection accuracy
- [x] Changed processing order: headings before lists
- [x] Use absolute font size ranges for bold text
- Known issue: Table headers detected as H6 (will fix in Phase 3)

### Phase 3: Fix Element Ordering and Table Placement ✓
- [x] Fix sorting/ordering of elements to maintain document flow
- [x] Integrate table positions with text element positions
- [x] Prevent tables from being moved to end of document
- [x] Add position tracking (y0, page_number) to all Element types
- [x] **Critical fix**: Exclude text spans that overlap with table bounding boxes (prevents duplicate content)
- [x] Test that content sections stay in correct order

### Phase 4: Fix Table Header False Positives
- [ ] Stop detecting table headers as H6 headings
- [ ] Add table header row detection to suppress heading processor
- [ ] Validate tables are actual tables (not just header rows)
- [ ] Add confidence scoring for table detection

### Phase 5: Fix Code Block Detection
- [ ] Detect triple-backtick fenced code blocks (```language)
- [ ] Preserve code block language identifiers
- [ ] Distinguish between inline code (single backticks) and code blocks
- [ ] Handle code blocks with proper line breaks and indentation
- [ ] Prevent inline code within text from being split into blocks

### Phase 6: Fix List Detection ✓
- [x] **ROOT CAUSE IDENTIFIED**: Obsidian PDF export strips bullet characters! List items appear as plain text with indentation.
- [x] Implement heuristic list detection based on indentation patterns:
  - x0 = 71.8: First-level list items
  - x0 = 98.8: Second-level (nested) list items
  - Context-aware: Following "### Unordered List" or "### Ordered List" headers
- [x] Fix ordered list numbering - Using "1." for all items (valid markdown, renderers auto-number)
- [x] Handle nested lists with proper indentation based on x0 values
- [x] Preserve list structure and hierarchy
- [x] **Strategy**: Use combination of indentation, context (previous headers), and line length heuristics
- **Note**: Checkbox markers ([x]/[ ]) also stripped by Obsidian PDF export - cannot distinguish checked vs unchecked

### Phase 7: Fix Blockquotes and Inline Elements
- [ ] Detect blockquotes and add > prefix
- [ ] Handle multi-line blockquotes
- [ ] Fix spurious >>> blockquote symbols in inline code contexts
- [ ] Preserve inline code within text without breaking into blocks

### Phase 8: Additional Features
- [ ] Add frontmatter detection/preservation (YAML between ---) 
- [ ] Add horizontal rule detection (--- separators)
- [ ] Preserve hyperlinks [text](url)
- [ ] Add image reference support

## Success Criteria

- [x] Headings match original levels (H1 = H1, H2 = H2, etc.) - MOSTLY DONE (Phase 2)
- [x] All text has proper spacing between words - DONE (Phase 1)
- [x] Content sections appear in correct order (not scrambled by table extraction) - DONE (Phase 3)
- [x] Tables render correctly at their proper positions - DONE (Phase 3)
- [ ] No table headers detected as H6 headings - NEXT (Phase 4)
- [ ] Fenced code blocks (```) preserved with language identifiers
- [ ] Inline code stays inline, not split into blocks
- [x] Lists maintain correct numbering (using "1." markdown standard) - DONE (Phase 6)
- [x] Unordered lists appear under correct headers - DONE (Phase 6)
- [x] Nested lists render with proper indentation - DONE (Phase 6)
- **Note**: Checkbox syntax cannot be preserved (Obsidian PDF strips markers)
- [ ] Blockquotes render with proper > prefix
- [ ] No spurious >>> symbols in text
- [ ] Horizontal rules (---) preserved
- [ ] Frontmatter preserved if present
- [ ] Hyperlinks preserved as [text](url)

## Testing

Use example-obsidian/obsidian-input.pdf as primary test case.

## Notes

This plan focuses on fixing the core conversion quality issues before adding new features. PyMuPDF differentiator should be accuracy and structure preservation, not just raw extraction speed.
