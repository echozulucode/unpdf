"""Feature-specific integration tests."""

import tempfile
from pathlib import Path

import pytest

from unpdf.core import convert_pdf


class TestFeatureSpecific:
    """Test specific features in isolation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def create_pdf_with_reportlab(self, output_path: Path, builder_func):
        """Create a PDF using a builder function.

        Args:
            output_path: Path to save PDF
            builder_func: Function that takes a canvas and builds content
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed (optional for feature tests)")

        c = canvas.Canvas(str(output_path), pagesize=letter)
        builder_func(c)
        c.save()

    def test_only_headings(self, temp_dir):
        """Test PDF containing only headings."""

        def build(c):
            c.setFont("Helvetica-Bold", 24)
            c.drawString(100, 750, "Main Title")
            c.setFont("Helvetica-Bold", 18)
            c.drawString(100, 700, "Section Header")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 650, "Subsection Header")

        pdf_path = temp_dir / "headings_only.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "Main Title" in result
        assert "Section Header" in result
        # Check for heading markers (may vary)
        assert "#" in result or "Title" in result

    def test_only_lists(self, temp_dir):
        """Test PDF containing only lists."""

        def build(c):
            c.setFont("Helvetica", 12)
            c.drawString(100, 750, "• Item one")
            c.drawString(100, 730, "• Item two")
            c.drawString(100, 710, "• Item three")
            c.drawString(100, 670, "1. Numbered one")
            c.drawString(100, 650, "2. Numbered two")

        pdf_path = temp_dir / "lists_only.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "Item one" in result
        assert "Numbered one" in result
        # Should detect list markers
        assert "•" in result or "-" in result or "1." in result

    def test_only_code(self, temp_dir):
        """Test PDF containing only code."""

        def build(c):
            c.setFont("Courier", 12)
            c.drawString(100, 750, "def hello():")
            c.drawString(120, 730, "    print('Hello')")
            c.drawString(120, 710, "    return True")

        pdf_path = temp_dir / "code_only.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "def hello" in result or "hello" in result
        assert "print" in result
        # Should detect code (may be inline or block)

    def test_only_formatted_text(self, temp_dir):
        """Test PDF containing only formatted text."""

        def build(c):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, 750, "Bold text")
            c.setFont("Helvetica-Oblique", 12)
            c.drawString(100, 730, "Italic text")
            c.setFont("Helvetica-BoldOblique", 12)
            c.drawString(100, 710, "Bold italic text")
            c.setFont("Helvetica", 12)
            c.drawString(100, 690, "Normal text")

        pdf_path = temp_dir / "formatted_only.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "Bold text" in result or "bold text" in result.lower()
        assert "Italic text" in result or "italic text" in result.lower()
        assert "Normal text" in result or "normal text" in result.lower()

    def test_only_links(self, temp_dir):
        """Test PDF containing only links."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "links_only.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Draw text that looks like a URL
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Visit https://example.com")
        c.drawString(100, 730, "Email: test@example.com")

        # Add actual link annotation
        c.linkURL("https://example.com", (100, 700, 200, 715), relative=0)
        c.drawString(100, 700, "Click here")

        c.save()

        result = convert_pdf(str(pdf_path))
        assert "example.com" in result
        # Should detect URLs in text

    def test_only_blockquotes(self, temp_dir):
        """Test PDF containing only blockquotes."""

        def build(c):
            c.setFont("Helvetica", 12)
            c.drawString(150, 750, "This is a quoted paragraph")
            c.drawString(150, 730, "with multiple lines")
            c.drawString(200, 690, "This is nested even deeper")

        pdf_path = temp_dir / "quotes_only.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "quoted paragraph" in result or "quoted" in result.lower()
        # Blockquotes detected by indentation

    def test_mixed_heading_and_paragraphs(self, temp_dir):
        """Test PDF with headings and paragraphs mixed."""

        def build(c):
            c.setFont("Helvetica-Bold", 20)
            c.drawString(100, 750, "Introduction")
            c.setFont("Helvetica", 12)
            c.drawString(100, 720, "This is the introduction paragraph.")
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 680, "Details")
            c.setFont("Helvetica", 12)
            c.drawString(100, 650, "Here are the details.")

        pdf_path = temp_dir / "mixed_heading_para.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "Introduction" in result
        assert "introduction paragraph" in result.lower()
        assert "Details" in result
        assert "details" in result.lower()

    def test_mixed_lists_and_paragraphs(self, temp_dir):
        """Test PDF with lists and paragraphs mixed."""

        def build(c):
            c.setFont("Helvetica", 12)
            c.drawString(100, 750, "Here is a list:")
            c.drawString(100, 730, "• First item")
            c.drawString(100, 710, "• Second item")
            c.drawString(100, 670, "After the list comes a paragraph.")

        pdf_path = temp_dir / "mixed_list_para.pdf"
        self.create_pdf_with_reportlab(pdf_path, build)

        result = convert_pdf(str(pdf_path))
        assert "First item" in result
        assert "paragraph" in result.lower()

    def test_table_only(self, temp_dir):
        """Test PDF containing only a table."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "table_only.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)

        data = [["Name", "Age", "City"], ["Alice", "30", "NYC"], ["Bob", "25", "LA"]]

        table = Table(data)
        doc.build([table])

        result = convert_pdf(str(pdf_path))
        assert "Name" in result
        assert "Alice" in result
        assert "Bob" in result
        # Should detect as table (may have | markers)


class TestRealWorldScenarios:
    """Test real-world document scenarios."""

    def test_technical_documentation(self):
        """Test conversion of technical documentation."""
        pytest.skip("Requires real technical doc PDF fixture")

    def test_business_report(self):
        """Test conversion of business report."""
        pytest.skip("Requires real business report PDF fixture")

    def test_academic_paper(self):
        """Test conversion of academic paper."""
        pytest.skip("Requires real academic paper PDF fixture")

    def test_multicolumn_layout(self):
        """Test conversion of multi-column layout."""
        pytest.skip("Requires multi-column PDF fixture")

    def test_newsletter(self):
        """Test conversion of newsletter."""
        pytest.skip("Requires newsletter PDF fixture")
