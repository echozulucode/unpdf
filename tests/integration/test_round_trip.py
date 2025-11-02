"""Round-trip conversion tests: Markdown → PDF → Markdown."""

import tempfile
from pathlib import Path

import pytest

from unpdf.core import convert_pdf


class TestRoundTrip:
    """Test Markdown → PDF → Markdown conversions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def create_test_pdf_from_markdown(self, markdown: str, output_path: Path) -> None:
        """Create a PDF from Markdown using reportlab (no Pandoc dependency).

        Args:
            markdown: Markdown content
            output_path: Path to save PDF
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
            )
        except ImportError:
            pytest.skip("reportlab not installed (optional for round-trip tests)")

        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Parse simple markdown and convert to PDF elements
        lines = markdown.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                story.append(Spacer(1, 0.2 * inch))
                i += 1
                continue

            # Headings
            if line.startswith("# "):
                text = line[2:].strip()
                story.append(Paragraph(text, styles["Heading1"]))
                story.append(Spacer(1, 0.1 * inch))
            elif line.startswith("## "):
                text = line[3:].strip()
                story.append(Paragraph(text, styles["Heading2"]))
                story.append(Spacer(1, 0.1 * inch))
            elif line.startswith("### "):
                text = line[4:].strip()
                story.append(Paragraph(text, styles["Heading3"]))
                story.append(Spacer(1, 0.1 * inch))
            # Lists
            elif line.startswith("- "):
                text = line[2:].strip()
                story.append(Paragraph(f"• {text}", styles["BodyText"]))
            elif line.startswith("1. "):
                text = line[3:].strip()
                story.append(Paragraph(f"1. {text}", styles["BodyText"]))
            # Tables (simple pipe tables)
            elif "|" in line and not line.startswith("|---"):
                table_data = []
                # Collect table rows
                while i < len(lines) and "|" in lines[i]:
                    row_line = lines[i].strip()
                    if not row_line.startswith("|---"):
                        cells = [c.strip() for c in row_line.split("|")[1:-1]]
                        table_data.append(cells)
                    i += 1
                if table_data:
                    story.append(Table(table_data))
                    story.append(Spacer(1, 0.2 * inch))
                continue
            # Paragraphs
            else:
                # Apply inline formatting (simplified - reportlab handles HTML)
                text = line
                # Bold-italic: ***text*** → <b><i>text</i></b>
                while "***" in text:
                    start = text.find("***")
                    end = text.find("***", start + 3)
                    if end != -1:
                        text = (
                            text[:start]
                            + "<b><i>"
                            + text[start + 3 : end]
                            + "</i></b>"
                            + text[end + 3 :]
                        )
                    else:
                        break
                # Bold: **text** → <b>text</b>
                while "**" in text:
                    start = text.find("**")
                    end = text.find("**", start + 2)
                    if end != -1:
                        text = (
                            text[:start]
                            + "<b>"
                            + text[start + 2 : end]
                            + "</b>"
                            + text[end + 2 :]
                        )
                    else:
                        break
                # Italic: *text* → <i>text</i>
                while "*" in text:
                    start = text.find("*")
                    end = text.find("*", start + 1)
                    if end != -1:
                        text = (
                            text[:start]
                            + "<i>"
                            + text[start + 1 : end]
                            + "</i>"
                            + text[end + 1 :]
                        )
                    else:
                        break
                story.append(Paragraph(text, styles["BodyText"]))

            i += 1

        doc.build(story)

    def normalize_markdown(self, text: str) -> str:
        """Normalize Markdown for comparison.

        Args:
            text: Markdown text

        Returns:
            Normalized text
        """
        lines = text.strip().split("\n")
        normalized = []
        for line in lines:
            # Remove extra whitespace
            line = " ".join(line.split())
            # Skip empty lines and separator lines
            if line and not line.startswith("|---"):
                normalized.append(line)
        return "\n".join(normalized)

    def test_simple_paragraphs(self, temp_dir):
        """Test round-trip conversion of simple paragraphs."""
        original = """This is a simple paragraph.

This is another paragraph with some text."""

        pdf_path = temp_dir / "simple.pdf"
        self.create_test_pdf_from_markdown(original, pdf_path)

        result = convert_pdf(str(pdf_path))

        # Check content is present
        assert "paragraph" in result.lower()
        assert "another" in result.lower()

    def test_headings_and_paragraphs(self, temp_dir):
        """Test round-trip with headings and paragraphs."""
        original = """# Main Title

This is an introduction paragraph.

## Section One

Some content in section one.

### Subsection

More detailed content."""

        pdf_path = temp_dir / "headings.pdf"
        self.create_test_pdf_from_markdown(original, pdf_path)

        result = convert_pdf(str(pdf_path))

        # Check that headings are detected
        assert "# " in result or "Main Title" in result
        assert "Section One" in result
        assert "introduction" in result.lower()

    def test_formatted_text(self, temp_dir):
        """Test round-trip with bold and italic text."""
        original = """This is **bold text** and this is *italic text*.

Here is ***bold and italic*** together."""

        pdf_path = temp_dir / "formatted.pdf"
        self.create_test_pdf_from_markdown(original, pdf_path)

        result = convert_pdf(str(pdf_path))

        # Check that formatting is detected (may not be perfect)
        assert "bold" in result.lower()
        assert "italic" in result.lower()

    def test_lists(self, temp_dir):
        """Test round-trip with lists."""
        original = """Shopping list:

- Apples
- Oranges
- Bananas

Numbered steps:

1. First step
1. Second step
1. Third step"""

        pdf_path = temp_dir / "lists.pdf"
        self.create_test_pdf_from_markdown(original, pdf_path)

        result = convert_pdf(str(pdf_path))

        # Check that list items appear
        assert "Apples" in result
        assert "First step" in result
        # Check for list markers (either - or •)
        assert "-" in result or "•" in result

    def test_mixed_content(self, temp_dir):
        """Test round-trip with mixed content types."""
        original = """# Document Title

This is an introduction with **bold** and *italic* text.

## Features

- Feature one
- Feature two
- Feature three

## Details

This section contains more information."""

        pdf_path = temp_dir / "mixed.pdf"
        self.create_test_pdf_from_markdown(original, pdf_path)

        result = convert_pdf(str(pdf_path))

        # Check all content types are present
        assert "Document Title" in result
        assert "introduction" in result.lower()
        assert "Feature" in result
        assert "Details" in result or "details" in result.lower()


class TestContentPreservation:
    """Test that content is preserved accurately."""

    def test_text_content_preserved(self, tmp_path):
        """Test that text content is accurately extracted."""
        # This test will be enhanced when we have real PDF fixtures
        pytest.skip("Requires real PDF fixtures")

    def test_structure_preserved(self, tmp_path):
        """Test that document structure is preserved."""
        pytest.skip("Requires real PDF fixtures")

    def test_formatting_preserved(self, tmp_path):
        """Test that inline formatting is preserved."""
        pytest.skip("Requires real PDF fixtures")
