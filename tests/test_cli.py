"""Tests for unpdf CLI module."""

import sys
from unittest.mock import patch

import pytest

from unpdf.cli import main, parse_page_spec


class TestParsePageSpec:
    """Tests for parse_page_spec function."""

    def test_single_page(self):
        """Test parsing single page number."""
        assert parse_page_spec("1") == [1]
        assert parse_page_spec("5") == [5]

    def test_page_range(self):
        """Test parsing page range."""
        assert parse_page_spec("1-3") == [1, 2, 3]
        assert parse_page_spec("5-8") == [5, 6, 7, 8]

    def test_multiple_pages(self):
        """Test parsing multiple page numbers."""
        assert parse_page_spec("1,3,5") == [1, 3, 5]
        assert parse_page_spec("2,4,6,8") == [2, 4, 6, 8]

    def test_mixed_spec(self):
        """Test parsing mixed specification."""
        assert parse_page_spec("1,3,5-7") == [1, 3, 5, 6, 7]
        assert parse_page_spec("1-3,5,7-9") == [1, 2, 3, 5, 7, 8, 9]

    def test_duplicate_removal(self):
        """Test duplicate page numbers are removed."""
        assert parse_page_spec("1,1,2,2") == [1, 2]
        assert parse_page_spec("1-3,2-4") == [1, 2, 3, 4]

    def test_whitespace_handling(self):
        """Test whitespace is handled properly."""
        assert parse_page_spec(" 1 , 3 , 5 ") == [1, 3, 5]
        assert parse_page_spec("1 - 3") == [1, 2, 3]

    def test_invalid_page_number(self):
        """Test invalid page numbers raise ValueError."""
        with pytest.raises(ValueError, match="Invalid page number"):
            parse_page_spec("abc")
        with pytest.raises(ValueError, match="Invalid page number"):
            parse_page_spec("1,abc,3")

    def test_invalid_range(self):
        """Test invalid ranges raise ValueError."""
        with pytest.raises(ValueError, match="Invalid page range"):
            parse_page_spec("1-abc")
        with pytest.raises(ValueError, match="Invalid range: 5-2"):
            parse_page_spec("5-2")

    def test_zero_or_negative(self):
        """Test zero or negative page numbers raise ValueError."""
        with pytest.raises(ValueError, match=r"Page numbers must be >= 1"):
            parse_page_spec("0")
        with pytest.raises(ValueError, match=r"Invalid page range"):
            parse_page_spec("-1")  # Treated as empty-1 range
        with pytest.raises(ValueError, match=r"Page numbers must be >= 1"):
            parse_page_spec("1-0")


class TestCLIMain:
    """Tests for CLI main function."""

    @patch("unpdf.cli.convert_pdf")
    def test_single_file_conversion(self, mock_convert, tmp_path):
        """Test converting a single PDF file."""
        # Create test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        # Mock sys.argv
        with patch.object(sys, "argv", ["unpdf", str(pdf_file)]):
            exit_code = main()

        # Verify convert_pdf was called
        assert mock_convert.call_count == 1
        call_args = mock_convert.call_args
        assert call_args[0][0] == pdf_file
        assert str(call_args[1]["output_path"]).endswith(".md")

        # Verify success exit
        assert exit_code == 0

    @patch("unpdf.cli.convert_pdf")
    def test_single_file_with_output(self, mock_convert, tmp_path):
        """Test converting with custom output path."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")
        output_file = tmp_path / "output.md"

        with patch.object(
            sys, "argv", ["unpdf", str(pdf_file), "-o", str(output_file)]
        ):
            exit_code = main()

        # Verify output path
        call_args = mock_convert.call_args
        assert call_args[1]["output_path"] == output_file
        assert exit_code == 0

    @patch("unpdf.cli.convert_pdf")
    def test_directory_conversion(self, mock_convert, tmp_path):
        """Test converting directory of PDFs."""
        # Create test PDF files
        (tmp_path / "doc1.pdf").write_text("dummy1")
        (tmp_path / "doc2.pdf").write_text("dummy2")
        (tmp_path / "ignore.txt").write_text("ignore")

        with patch.object(sys, "argv", ["unpdf", str(tmp_path)]):
            exit_code = main()

        # Verify convert_pdf called for each PDF
        assert mock_convert.call_count == 2
        assert exit_code == 0

    @patch("unpdf.cli.convert_pdf")
    def test_recursive_directory(self, mock_convert, tmp_path):
        """Test recursive directory conversion."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "doc1.pdf").write_text("dummy1")
        (subdir / "doc2.pdf").write_text("dummy2")

        with patch.object(sys, "argv", ["unpdf", str(tmp_path), "--recursive"]):
            exit_code = main()

        # Verify both PDFs processed
        assert mock_convert.call_count == 2
        assert exit_code == 0

    @patch("unpdf.cli.convert_pdf")
    def test_page_spec_parsing(self, mock_convert, tmp_path):
        """Test page specification is parsed correctly."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        with patch.object(sys, "argv", ["unpdf", str(pdf_file), "--pages", "1,3,5-7"]):
            exit_code = main()

        # Verify page_numbers passed to convert_pdf
        call_args = mock_convert.call_args
        assert call_args[1]["page_numbers"] == [1, 3, 5, 6, 7]
        assert exit_code == 0

    def test_invalid_page_spec(self, tmp_path):
        """Test invalid page specification returns error."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        with patch.object(sys, "argv", ["unpdf", str(pdf_file), "--pages", "invalid"]):
            exit_code = main()

        # Verify error exit
        assert exit_code == 1

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with patch.object(sys, "argv", ["unpdf", "nonexistent.pdf"]):
            exit_code = main()

        assert exit_code == 1

    @patch("unpdf.cli.convert_pdf")
    def test_conversion_error(self, mock_convert, tmp_path):
        """Test handling of conversion errors."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        # Mock conversion failure
        mock_convert.side_effect = ValueError("Corrupted PDF")

        with patch.object(sys, "argv", ["unpdf", str(pdf_file)]):
            exit_code = main()

        assert exit_code == 1

    @patch("unpdf.cli.convert_pdf")
    def test_permission_error(self, mock_convert, tmp_path):
        """Test handling of permission errors."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        # Mock permission error
        mock_convert.side_effect = PermissionError("Access denied")

        with patch.object(sys, "argv", ["unpdf", str(pdf_file)]):
            exit_code = main()

        assert exit_code == 1

    @patch("unpdf.cli.convert_pdf")
    def test_keyboard_interrupt(self, mock_convert, tmp_path):
        """Test handling of keyboard interrupt."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        # Mock keyboard interrupt
        mock_convert.side_effect = KeyboardInterrupt()

        with patch.object(sys, "argv", ["unpdf", str(pdf_file)]):
            exit_code = main()

        assert exit_code == 130

    @patch("unpdf.cli.convert_pdf")
    def test_batch_with_errors(self, mock_convert, tmp_path):
        """Test batch conversion with some errors."""
        (tmp_path / "doc1.pdf").write_text("dummy1")
        (tmp_path / "doc2.pdf").write_text("dummy2")

        # First conversion succeeds, second fails
        mock_convert.side_effect = [None, ValueError("Error")]

        with patch.object(sys, "argv", ["unpdf", str(tmp_path)]):
            exit_code = main()

        # Should exit with error code
        assert exit_code == 1

    def test_empty_directory(self, tmp_path):
        """Test handling of empty directory."""
        with patch.object(sys, "argv", ["unpdf", str(tmp_path)]):
            exit_code = main()

        assert exit_code == 1

    @patch("unpdf.cli.convert_pdf")
    def test_verbose_flag(self, mock_convert, tmp_path):
        """Test verbose flag enables debug logging."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        with (
            patch.object(sys, "argv", ["unpdf", str(pdf_file), "--verbose"]),
            patch.object(sys, "exit"),
        ):
            main()

        # Just verify it doesn't crash with verbose
        assert mock_convert.call_count == 1

    @patch("unpdf.cli.convert_pdf")
    def test_no_code_blocks_flag(self, mock_convert, tmp_path):
        """Test --no-code-blocks flag is passed correctly."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        with patch.object(sys, "argv", ["unpdf", str(pdf_file), "--no-code-blocks"]):
            exit_code = main()

        call_args = mock_convert.call_args
        assert call_args[1]["detect_code_blocks"] is False
        assert exit_code == 0

    @patch("unpdf.cli.convert_pdf")
    def test_heading_ratio_flag(self, mock_convert, tmp_path):
        """Test --heading-ratio flag is passed correctly."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        with patch.object(
            sys, "argv", ["unpdf", str(pdf_file), "--heading-ratio", "1.5"]
        ):
            exit_code = main()

        call_args = mock_convert.call_args
        assert call_args[1]["heading_font_ratio"] == 1.5
        assert exit_code == 0

    def test_version_flag(self):
        """Test --version flag displays version."""
        with (
            patch.object(sys, "argv", ["unpdf", "--version"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        # argparse exits with 0 for --version
        assert exc_info.value.code == 0
