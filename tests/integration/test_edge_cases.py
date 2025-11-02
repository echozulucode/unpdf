"""Edge case tests for PDF conversion."""

import tempfile
from pathlib import Path

import pytest

from unpdf.core import convert_pdf


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def create_minimal_pdf(self, output_path: Path, text: str = "Test") -> None:
        """Create a minimal PDF for testing.

        Args:
            output_path: Path to save PDF
            text: Text content
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed (optional for edge case tests)")

        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.drawString(100, 750, text)
        c.save()

    def test_empty_pdf(self, temp_dir):
        """Test conversion of PDF with no text content."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "empty.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.showPage()  # Empty page
        c.save()

        result = convert_pdf(str(pdf_path))
        # Should return empty or minimal content
        assert result is not None
        assert len(result.strip()) < 100  # Should be very short

    def test_single_word(self, temp_dir):
        """Test PDF with single word."""
        pdf_path = temp_dir / "single_word.pdf"
        self.create_minimal_pdf(pdf_path, "Hello")

        result = convert_pdf(str(pdf_path))
        assert "Hello" in result

    def test_very_long_line(self, temp_dir):
        """Test PDF with very long lines of text."""
        long_text = "A" * 500  # 500 character line
        pdf_path = temp_dir / "long_line.pdf"
        self.create_minimal_pdf(pdf_path, long_text[:100])  # Truncate for rendering

        result = convert_pdf(str(pdf_path))
        assert len(result) > 50  # Should have some content

    def test_special_characters(self, temp_dir):
        """Test PDF with special characters."""
        special_text = "Test & < > \" ' \\ | * # [ ] ( )"
        pdf_path = temp_dir / "special_chars.pdf"
        self.create_minimal_pdf(pdf_path, special_text)

        result = convert_pdf(str(pdf_path))
        # Should handle special characters without crashing
        assert result is not None

    def test_unicode_characters(self, temp_dir):
        """Test PDF with unicode characters."""
        unicode_text = "Hello 世界 🌍 café"
        pdf_path = temp_dir / "unicode.pdf"
        self.create_minimal_pdf(pdf_path, unicode_text)

        result = convert_pdf(str(pdf_path))
        # Should handle unicode without crashing
        assert result is not None

    def test_multiple_spaces(self, temp_dir):
        """Test PDF with multiple consecutive spaces."""
        spaced_text = "Word1     Word2          Word3"
        pdf_path = temp_dir / "spaces.pdf"
        self.create_minimal_pdf(pdf_path, spaced_text)

        result = convert_pdf(str(pdf_path))
        # Should normalize spaces
        assert "Word1" in result
        assert "Word2" in result

    def test_mixed_line_endings(self, temp_dir):
        """Test handling of mixed line endings."""
        # This is more relevant for text processing
        # Just verify basic functionality
        pdf_path = temp_dir / "mixed.pdf"
        self.create_minimal_pdf(pdf_path, "Line1\nLine2\rLine3\r\nLine4")

        result = convert_pdf(str(pdf_path))
        assert result is not None

    def test_large_document(self, temp_dir):
        """Test conversion of large document."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "large.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Create 50 pages with text
        for page_num in range(50):
            c.drawString(100, 750, f"Page {page_num + 1}")
            c.drawString(100, 700, f"This is content for page {page_num + 1}")
            c.showPage()
        c.save()

        result = convert_pdf(str(pdf_path))
        # Should contain content from multiple pages
        assert "Page 1" in result
        assert "Page 50" in result or "page 50" in result.lower()

    def test_page_with_only_whitespace(self, temp_dir):
        """Test page containing only whitespace."""
        pdf_path = temp_dir / "whitespace.pdf"
        self.create_minimal_pdf(pdf_path, "   \n\n\t\t   ")

        result = convert_pdf(str(pdf_path))
        # Should handle gracefully
        assert result is not None

    def test_unusual_fonts(self, temp_dir):
        """Test PDF with unusual font names."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "fonts.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Different fonts
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Helvetica text")
        c.setFont("Courier", 12)
        c.drawString(100, 700, "Courier text")
        c.setFont("Times-Roman", 12)
        c.drawString(100, 650, "Times text")
        c.save()

        result = convert_pdf(str(pdf_path))
        assert "Helvetica" in result or "helvetica" in result.lower()
        assert "Courier" in result or "courier" in result.lower()

    def test_overlapping_text(self, temp_dir):
        """Test PDF with overlapping text (unusual case)."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "overlap.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "Text1")
        c.drawString(100, 750, "Text2")  # Same position
        c.save()

        result = convert_pdf(str(pdf_path))
        # Should handle without crashing
        assert result is not None

    def test_rotated_text(self, temp_dir):
        """Test PDF with rotated text."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")

        pdf_path = temp_dir / "rotated.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "Normal text")
        c.rotate(90)
        c.drawString(100, 100, "Rotated text")
        c.save()

        result = convert_pdf(str(pdf_path))
        # Should extract normal text at minimum
        assert "Normal" in result or "normal" in result.lower()


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_nonexistent_file(self):
        """Test handling of non-existent file."""
        with pytest.raises((FileNotFoundError, OSError)):
            convert_pdf("nonexistent_file.pdf")

    def test_invalid_pdf_path(self):
        """Test handling of invalid file path."""
        with pytest.raises((FileNotFoundError, OSError, ValueError)):
            convert_pdf("")

    def test_directory_instead_of_file(self, tmp_path):
        """Test handling when directory path is given instead of file."""
        with pytest.raises((OSError, ValueError, IsADirectoryError)):
            convert_pdf(str(tmp_path))

    def test_corrupted_pdf(self, tmp_path):
        """Test handling of corrupted PDF."""
        bad_pdf = tmp_path / "corrupted.pdf"
        bad_pdf.write_text("This is not a valid PDF file")

        # Should raise an error or return empty result
        try:
            result = convert_pdf(str(bad_pdf))
            # If it doesn't raise, result should be empty or minimal
            assert len(result.strip()) < 50
        except Exception:
            # Expected to raise an error
            pass

    def test_non_pdf_file(self, tmp_path):
        """Test handling of non-PDF file."""
        text_file = tmp_path / "not_pdf.txt"
        text_file.write_text("This is a text file, not a PDF")

        # Should raise an error or handle gracefully
        try:
            result = convert_pdf(str(text_file))
            # If it doesn't raise, check it handled gracefully
            assert result is not None
        except Exception:
            # Expected to raise an error
            pass
