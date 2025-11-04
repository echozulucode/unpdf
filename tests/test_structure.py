"""Tests for Tagged PDF structure extraction."""

from unpdf.extractors.structure import TaggedPDFExtractor


def test_tagged_pdf_detection_obsidian():
    """Test if obsidian PDF is detected as tagged or not."""
    extractor = TaggedPDFExtractor("example-obsidian/obsidian-input.pdf")
    is_tagged = extractor.is_tagged()
    # Just check it doesn't crash, we'll see what the actual value is
    assert isinstance(is_tagged, bool)


def test_extract_structure_tree_obsidian():
    """Test structure tree extraction from obsidian PDF."""
    extractor = TaggedPDFExtractor("example-obsidian/obsidian-input.pdf")
    structure = extractor.extract_structure_tree()
    # Should return a list (may be empty if not tagged)
    assert isinstance(structure, list)


def test_structure_summary_obsidian():
    """Test structure summary extraction from obsidian PDF."""
    extractor = TaggedPDFExtractor("example-obsidian/obsidian-input.pdf")
    summary = extractor.get_structure_summary()
    # Should return a dict
    assert isinstance(summary, dict)
    print(f"Structure summary: {summary}")
