"""Unit tests for unpdf.cli module."""

from pathlib import Path

import pytest

from unpdf.cli import main


def test_cli_version(monkeypatch, capsys):
    """Test --version flag displays version.

    Args:
        monkeypatch: Pytest fixture for modifying sys.argv.
        capsys: Pytest fixture for capturing stdout/stderr.
    """
    monkeypatch.setattr("sys.argv", ["unpdf", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "unpdf" in captured.out
    assert "0.1.0" in captured.out


def test_cli_help(monkeypatch, capsys):
    """Test --help flag displays help.

    Args:
        monkeypatch: Pytest fixture for modifying sys.argv.
        capsys: Pytest fixture for capturing stdout/stderr.
    """
    monkeypatch.setattr("sys.argv", ["unpdf", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()
    assert "PDF" in captured.out


def test_cli_file_not_found(monkeypatch, caplog):
    """Test CLI returns error for non-existent file.

    Args:
        monkeypatch: Pytest fixture for modifying sys.argv.
        caplog: Pytest fixture for capturing log output.
    """
    monkeypatch.setattr("sys.argv", ["unpdf", "nonexistent.pdf"])

    exit_code = main()

    assert exit_code == 1
    assert "not found" in caplog.text.lower() or "error" in caplog.text.lower()


def test_cli_single_file(monkeypatch, tmp_path: Path):
    """Test CLI processes single file.

    Args:
        monkeypatch: Pytest fixture for modifying sys.argv.
        tmp_path: Pytest fixture providing temporary directory.
    """
    # Create fake PDF
    input_pdf = tmp_path / "test.pdf"
    input_pdf.write_text("%PDF-1.4\n%placeholder", encoding="latin-1")

    output_md = tmp_path / "test.md"

    monkeypatch.setattr("sys.argv", ["unpdf", str(input_pdf), "-o", str(output_md)])

    exit_code = main()

    assert exit_code == 0
    assert output_md.exists()
