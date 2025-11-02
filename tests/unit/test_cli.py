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


@pytest.mark.skip(reason="Requires real PDF fixture")
def test_cli_single_file(monkeypatch, tmp_path: Path):
    """Test CLI processes single file.

    Args:
        monkeypatch: Pytest fixture for modifying sys.argv.
        tmp_path: Pytest fixture providing temporary directory.

    Note:
        This test is skipped until we create sample PDF fixtures.
        Fake PDFs don't work with pdfplumber.
    """
    # Will be implemented when we have real PDF fixtures
    pass
