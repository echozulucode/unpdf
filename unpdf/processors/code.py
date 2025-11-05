r"""Code block detection processor for unpdf.

This module detects code blocks and inline code based on monospace fonts
and other heuristics.

Example:
    >>> from unpdf.processors.code import CodeProcessor
    >>> processor = CodeProcessor()
    >>> span = {"text": "print('hello')", "font_family": "Courier"}
    >>> result = processor.process(span)
    >>> result.to_markdown()
    '`print(\'hello\')`'
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from unpdf.processors.headings import Element, ParagraphElement

logger = logging.getLogger(__name__)


@dataclass
class CodeBlockElement(Element):
    """Code block element (fenced with triple backticks).

    Attributes:
        text: Code content.
        language: Optional language hint for syntax highlighting.
    """

    language: str = ""

    def to_markdown(self) -> str:
        r"""Convert code block to Markdown.

        Returns:
            Fenced code block with triple backticks.

        Example:
            >>> code = CodeBlockElement("print('hello')", language="python")
            >>> code.to_markdown()
            "```python\nprint('hello')\n```"
        """
        fence = "```"
        if self.language:
            return f"{fence}{self.language}\n{self.text}\n{fence}"
        return f"{fence}\n{self.text}\n{fence}"


@dataclass
class InlineCodeElement(Element):
    """Inline code element (single backticks).

    Attributes:
        text: Code content.
    """

    def to_markdown(self) -> str:
        """Convert inline code to Markdown.

        Returns:
            Code wrapped in single backticks.

        Example:
            >>> code = InlineCodeElement("print(x)")
            >>> code.to_markdown()
            "`print(x)`"
        """
        # Escape backticks in code if present
        escaped_text = self.text.replace("`", "\\`")
        return f"`{escaped_text}`"


class CodeProcessor:
    """Process text spans and detect code based on monospace fonts.

    Detects both inline code and code blocks. Code blocks are typically
    multi-line monospace text, while inline code is shorter.

    Attributes:
        monospace_patterns: Font name patterns indicating monospace fonts.
        block_threshold: Minimum characters for code block vs inline.

    Example:
        >>> processor = CodeProcessor()
        >>> span = {"text": "def foo():", "font_family": "Courier-Bold"}
        >>> result = processor.process(span)
        >>> isinstance(result, InlineCodeElement)
        True
    """

    # Common monospace font patterns
    MONOSPACE_PATTERNS = [
        r"courier",
        r"consolas",
        r"monaco",
        r"menlo",
        r"mono",
        r"code",
        r"source\s*code",
        r"ubuntu\s*mono",
        r"dejavu\s*sans\s*mono",
        r"liberation\s*mono",
        r"fira\s*code",
        r"inconsolata",
    ]

    def __init__(self, block_threshold: int = 40):
        """Initialize CodeProcessor.

        Args:
            block_threshold: Minimum character count to treat as code block
                vs inline code. Default 40 characters.

        Example:
            >>> processor = CodeProcessor(block_threshold=50)
            >>> processor.block_threshold
            50
        """
        self.block_threshold = block_threshold
        self.monospace_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.MONOSPACE_PATTERNS
        ]

    def process(
        self, span: dict[str, Any]
    ) -> CodeBlockElement | InlineCodeElement | ParagraphElement:
        """Process text span and detect code.

        Args:
            span: Text span dictionary with keys:
                - text (str): Text content
                - font_family (str): Font name
                - font_size (float): Optional font size

        Returns:
            CodeBlockElement, InlineCodeElement, or ParagraphElement.

        Example:
            >>> processor = CodeProcessor()
            >>> span = {"text": "x = 1", "font_family": "Courier"}
            >>> result = processor.process(span)
            >>> isinstance(result, InlineCodeElement)
            True
        """
        text = span["text"]
        font_family = span.get("font_family", "")
        y0 = span.get("y0", 0.0)
        x0 = span.get("x0", 0.0)
        page_number = span.get("page_number", 1)

        # Check if font is monospace
        if not self._is_monospace_font(font_family):
            return ParagraphElement(text=text, y0=y0, x0=x0, page_number=page_number)

        # Determine if block or inline based on length
        if len(text) >= self.block_threshold:
            # Try to infer language from content
            language = self._infer_language(text)
            logger.debug(
                f"Detected code block: '{text[:30]}...' (lang={language or 'none'})"
            )
            return CodeBlockElement(
                text=text, language=language, y0=y0, x0=x0, page_number=page_number
            )
        else:
            logger.debug(f"Detected inline code: '{text}'")
            return InlineCodeElement(text=text, y0=y0, x0=x0, page_number=page_number)

    def _is_monospace_font(self, font_name: str) -> bool:
        """Check if font name indicates monospace font.

        Args:
            font_name: Font family name from PDF.

        Returns:
            True if font appears to be monospace.

        Example:
            >>> processor = CodeProcessor()
            >>> processor._is_monospace_font("Courier-Bold")
            True
            >>> processor._is_monospace_font("Arial")
            False
        """
        if not font_name:
            return False

        # Check against all patterns
        return any(pattern.search(font_name) for pattern in self.monospace_patterns)

    def _infer_language(self, text: str) -> str:
        r"""Attempt to infer programming language from code content.

        Uses simple heuristics based on common keywords and patterns.
        More specific patterns are checked first to avoid false positives.

        Args:
            text: Code text content.

        Returns:
            Language identifier (e.g., "python", "javascript") or empty string.

        Example:
            >>> processor = CodeProcessor()
            >>> processor._infer_language("def foo():\n    pass")
            'python'
            >>> processor._infer_language("function foo() {}")
            'javascript'
        """
        text_lower = text.lower()

        # C/C++ indicators (check before others due to 'class' keyword)
        if any(
            keyword in text_lower
            for keyword in ["#include", "int main", "printf", "std::", "cout"]
        ):
            return "cpp"

        # Java indicators (check before Python due to 'class' keyword)
        if "public class" in text_lower or "public static" in text_lower:
            return "java"
        if "private " in text_lower and "void " in text_lower:
            return "java"

        # Python indicators
        if any(
            keyword in text_lower
            for keyword in ["def ", "import ", "elif ", "self.", "__init__"]
        ):
            return "python"
        # Python class without 'public' keyword
        if "class " in text_lower and "public" not in text_lower:
            return "python"

        # JavaScript/TypeScript indicators
        if any(
            keyword in text_lower
            for keyword in [
                "function ",
                "const ",
                "let ",
                "var ",
                "=> ",
                "console.",
            ]
        ):
            return "javascript"

        # JSON indicators (check before bash to avoid confusion with quotes)
        if (
            text.strip().startswith("{")
            and text.strip().endswith("}")
            and '"' in text
            and ":" in text
        ):
            return "json"
        if (
            text.strip().startswith("[")
            and text.strip().endswith("]")
            and ('"' in text or "{" in text)
        ):
            return "json"

        # Shell/Bash indicators
        if any(
            keyword in text_lower
            for keyword in ["#!/bin/", "echo ", "export ", "grep ", "sed "]
        ):
            return "bash"

        # SQL indicators (check after others to avoid false positives with 'from')
        if "select " in text_lower and "from " in text_lower:
            return "sql"
        if any(
            keyword in text_lower
            for keyword in ["insert into", "update ", "delete from"]
        ):
            return "sql"

        # Unknown language
        return ""
