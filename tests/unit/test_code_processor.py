"""Unit tests for unpdf.processors.code module."""

from unpdf.processors.code import (
    CodeBlockElement,
    CodeProcessor,
    InlineCodeElement,
)
from unpdf.processors.headings import ParagraphElement


def test_code_block_element_to_markdown():
    """Test CodeBlockElement markdown generation."""
    code = CodeBlockElement("print('hello')")
    assert code.to_markdown() == "```\nprint('hello')\n```"


def test_code_block_element_with_language():
    """Test CodeBlockElement with language hint."""
    code = CodeBlockElement("def foo():\n    pass", language="python")
    assert code.to_markdown() == "```python\ndef foo():\n    pass\n```"


def test_inline_code_element_to_markdown():
    """Test InlineCodeElement markdown generation."""
    code = InlineCodeElement("print(x)")
    assert code.to_markdown() == "`print(x)`"


def test_inline_code_element_escapes_backticks():
    """Test InlineCodeElement escapes backticks in code."""
    code = InlineCodeElement("use `backticks`")
    assert code.to_markdown() == "`use \\`backticks\\``"


def test_code_processor_initialization():
    """Test CodeProcessor initialization."""
    processor = CodeProcessor(block_threshold=50)
    assert processor.block_threshold == 50


def test_code_processor_detects_courier():
    """Test detection of Courier font."""
    processor = CodeProcessor()

    span = {"text": "code", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, InlineCodeElement)
    assert result.text == "code"


def test_code_processor_detects_various_monospace_fonts():
    """Test detection of various monospace fonts."""
    processor = CodeProcessor()

    fonts = [
        "Courier",
        "Courier-Bold",
        "Consolas",
        "Monaco",
        "Menlo",
        "DejaVuSansMono",
        "UbuntuMono",
        "SourceCodePro",
        "FiraCode",
    ]

    for font in fonts:
        span = {"text": "x", "font_family": font}
        result = processor.process(span)
        assert isinstance(result, InlineCodeElement), f"Failed for font: {font}"


def test_code_processor_rejects_non_monospace():
    """Test that non-monospace fonts are not detected as code."""
    processor = CodeProcessor()

    span = {"text": "normal text", "font_family": "Arial"}
    result = processor.process(span)

    assert isinstance(result, ParagraphElement)
    assert result.text == "normal text"


def test_code_processor_inline_vs_block():
    """Test distinction between inline code and code blocks."""
    processor = CodeProcessor(block_threshold=20)

    # Short = inline
    short_span = {"text": "x = 1", "font_family": "Courier"}
    short_result = processor.process(short_span)
    assert isinstance(short_result, InlineCodeElement)

    # Long = block
    long_span = {
        "text": "def foo():\n    x = 1\n    y = 2\n    return x + y",
        "font_family": "Courier",
    }
    long_result = processor.process(long_span)
    assert isinstance(long_result, CodeBlockElement)


def test_code_processor_infers_python():
    """Test Python language inference."""
    processor = CodeProcessor(block_threshold=10)

    span = {"text": "def foo():\n    pass", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == "python"


def test_code_processor_infers_javascript():
    """Test JavaScript language inference."""
    processor = CodeProcessor(block_threshold=10)

    span = {"text": "function foo() { return 1; }", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == "javascript"


def test_code_processor_infers_java():
    """Test Java language inference."""
    processor = CodeProcessor(block_threshold=10)

    span = {"text": "public class Foo { }", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == "java"


def test_code_processor_infers_cpp():
    """Test C++ language inference."""
    processor = CodeProcessor(block_threshold=10)

    span = {"text": "#include <iostream>\nint main() {}", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == "cpp"


def test_code_processor_infers_bash():
    """Test Bash language inference."""
    processor = CodeProcessor(block_threshold=10)

    span = {"text": "#!/bin/bash\necho hello", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == "bash"


def test_code_processor_infers_sql():
    """Test SQL language inference."""
    processor = CodeProcessor(block_threshold=10)

    span = {
        "text": "SELECT * FROM users WHERE id = 1",
        "font_family": "Courier",
    }
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == "sql"


def test_code_processor_unknown_language():
    """Test unknown language returns empty string."""
    processor = CodeProcessor(block_threshold=10)

    span = {"text": "unknown code syntax here", "font_family": "Courier"}
    result = processor.process(span)

    assert isinstance(result, CodeBlockElement)
    assert result.language == ""


def test_code_processor_is_monospace_font():
    """Test monospace font detection method."""
    processor = CodeProcessor()

    assert processor._is_monospace_font("Courier") is True
    assert processor._is_monospace_font("Courier-Bold") is True
    assert processor._is_monospace_font("consolas") is True
    assert processor._is_monospace_font("Arial") is False
    assert processor._is_monospace_font("") is False


def test_code_processor_infer_language():
    """Test language inference method."""
    processor = CodeProcessor()

    assert processor._infer_language("def foo():") == "python"
    assert processor._infer_language("function foo() {}") == "javascript"
    assert processor._infer_language("public class Foo {}") == "java"
    assert processor._infer_language("#include <stdio.h>") == "cpp"
    assert processor._infer_language("echo hello") == "bash"
    assert processor._infer_language("SELECT * FROM users") == "sql"
    assert processor._infer_language("unknown syntax") == ""
