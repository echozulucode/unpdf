"""Code block detection using font and layout analysis.

This module detects code blocks in PDFs based on:
- Monospace font detection (consistent character width)
- Indentation patterns (>40 pixels, consistent spacing)
- Syntax highlighting colors
- Common programming keywords
- Line continuity within blocks
"""

import re
from dataclasses import dataclass

from unpdf.models.layout import BoundingBox


@dataclass
class TextBlock:
    """Text block with font and layout information."""

    text: str
    bbox: BoundingBox
    font_name: str
    font_size: float
    color: tuple[int, int, int] = (0, 0, 0)
    char_width: float = 0.0


# Common programming keywords across languages
CODE_KEYWORDS: set[str] = {
    # Python
    "def",
    "class",
    "import",
    "from",
    "return",
    "if",
    "elif",
    "else",
    "for",
    "while",
    "try",
    "except",
    "finally",
    "with",
    "async",
    "await",
    "lambda",
    # JavaScript/TypeScript
    "function",
    "const",
    "let",
    "var",
    "export",
    "interface",
    "type",
    # Java/C/C++
    "public",
    "private",
    "protected",
    "static",
    "void",
    "int",
    "float",
    "double",
    "char",
    "boolean",
    "struct",
    "typedef",
    "namespace",
    # General
    "true",
    "false",
    "null",
    "undefined",
    "this",
    "self",
    "super",
}


class CodeDetector:
    """Detects code blocks in PDF documents."""

    def __init__(
        self,
        monospace_variance_threshold: float = 0.05,
        min_indent_pixels: float = 40.0,
        min_block_lines: int = 2,
        keyword_weight: float = 0.4,
        font_weight: float = 0.3,
        indent_weight: float = 0.2,
        color_weight: float = 0.1,
    ):
        """Initialize code detector.

        Args:
            monospace_variance_threshold: Max variance in character width for monospace
            min_indent_pixels: Minimum indentation to consider as code
            min_block_lines: Minimum lines to form a code block
            keyword_weight: Weight for keyword matching in confidence
            font_weight: Weight for monospace font in confidence
            indent_weight: Weight for indentation in confidence
            color_weight: Weight for syntax highlighting in confidence
        """
        self.monospace_variance_threshold = monospace_variance_threshold
        self.min_indent_pixels = min_indent_pixels
        self.min_block_lines = min_block_lines
        self.keyword_weight = keyword_weight
        self.font_weight = font_weight
        self.indent_weight = indent_weight
        self.color_weight = color_weight

    def is_monospace_font(self, blocks: list[TextBlock]) -> bool:
        """Check if blocks use monospace font based on character width variance.

        Args:
            blocks: List of text blocks to analyze

        Returns:
            True if character widths are consistent (monospace)
        """
        if not blocks:
            return False

        # Collect character widths
        widths = []
        for block in blocks:
            if block.char_width > 0:
                widths.append(block.char_width)
            elif block.text and block.bbox.width > 0:
                # Estimate character width
                char_count = len(block.text)
                if char_count > 0:
                    widths.append(block.bbox.width / char_count)

        if len(widths) < 2:
            return False

        # Calculate coefficient of variation (std / mean)
        mean_width = sum(widths) / len(widths)
        if mean_width == 0:
            return False

        variance = sum((w - mean_width) ** 2 for w in widths) / len(widths)
        std_dev = variance**0.5
        coefficient_of_variation = std_dev / mean_width

        return bool(coefficient_of_variation < self.monospace_variance_threshold)

    def has_consistent_indentation(self, blocks: list[TextBlock]) -> tuple[bool, float]:
        """Check for consistent indentation pattern.

        Args:
            blocks: List of text blocks to analyze

        Returns:
            Tuple of (has_indent, average_indent)
        """
        if not blocks:
            return False, 0.0

        # Get left edge positions
        left_edges = [block.bbox.x0 for block in blocks]
        if not left_edges:
            return False, 0.0

        min_left = min(left_edges)
        indents = [edge - min_left for edge in left_edges]

        # Check if there's significant indentation
        avg_indent = sum(indents) / len(indents)
        has_indent = avg_indent >= self.min_indent_pixels

        return has_indent, avg_indent

    def has_syntax_highlighting(self, blocks: list[TextBlock]) -> bool:
        """Check for syntax highlighting color patterns.

        Args:
            blocks: List of text blocks to analyze

        Returns:
            True if multiple colors are used (suggesting syntax highlighting)
        """
        if not blocks:
            return False

        # Collect unique colors
        colors = set()
        for block in blocks:
            colors.add(block.color)

        # If we have 3+ colors, likely syntax highlighting
        return len(colors) >= 3

    def contains_code_keywords(self, blocks: list[TextBlock]) -> tuple[bool, int]:
        """Check for programming keywords.

        Args:
            blocks: List of text blocks to analyze

        Returns:
            Tuple of (has_keywords, keyword_count)
        """
        if not blocks:
            return False, 0

        keyword_count = 0
        text = " ".join(block.text for block in blocks).lower()

        # Split into tokens
        tokens = re.findall(r"\b\w+\b", text)

        for token in tokens:
            if token in CODE_KEYWORDS:
                keyword_count += 1

        return keyword_count > 0, keyword_count

    def calculate_confidence(
        self,
        is_monospace: bool,
        has_indent: bool,
        avg_indent: float,
        has_syntax_highlight: bool,
        keyword_count: int,
        total_words: int,
    ) -> float:
        """Calculate confidence score for code block detection.

        Args:
            is_monospace: Whether font is monospace
            has_indent: Whether consistent indentation exists
            avg_indent: Average indentation in pixels
            has_syntax_highlight: Whether syntax highlighting detected
            keyword_count: Number of code keywords found
            total_words: Total word count

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Font score
        font_score = 1.0 if is_monospace else 0.0

        # Indent score (normalize by expected indent)
        indent_score = (
            min(1.0, avg_indent / self.min_indent_pixels) if has_indent else 0.0
        )

        # Color score
        color_score = 1.0 if has_syntax_highlight else 0.0

        # Keyword score (ratio of keywords to words)
        keyword_ratio = keyword_count / total_words if total_words > 0 else 0.0
        keyword_score = min(1.0, keyword_ratio * 10)  # Scale up

        # Weighted combination
        confidence = (
            self.keyword_weight * keyword_score
            + self.font_weight * font_score
            + self.indent_weight * indent_score
            + self.color_weight * color_score
        )

        return confidence

    def detect_code_blocks(
        self, blocks: list[TextBlock], page_height: float
    ) -> list[tuple[list[TextBlock], float]]:
        """Detect code blocks from text blocks.

        Args:
            blocks: List of text blocks to analyze
            page_height: Page height for vertical grouping

        Returns:
            List of (code_block_texts, confidence) tuples
        """
        if not blocks:
            return []

        # Sort blocks by vertical position
        sorted_blocks = sorted(blocks, key=lambda b: (b.bbox.y0, b.bbox.x0))

        # Group into potential code blocks by continuity
        code_blocks = []
        current_block = []
        prev_y = None
        line_height_threshold = 20.0  # Pixels between lines

        for block in sorted_blocks:
            if prev_y is None:
                current_block = [block]
                prev_y = block.bbox.y0
                continue

            # Check vertical continuity
            y_gap = abs(block.bbox.y0 - prev_y)
            if y_gap <= line_height_threshold:
                current_block.append(block)
            else:
                # Start new block
                if len(current_block) >= self.min_block_lines:
                    code_blocks.append(current_block)
                current_block = [block]

            prev_y = block.bbox.y0

        # Add last block
        if len(current_block) >= self.min_block_lines:
            code_blocks.append(current_block)

        # Analyze each potential code block
        results = []
        for block_group in code_blocks:
            is_monospace = self.is_monospace_font(block_group)
            has_indent, avg_indent = self.has_consistent_indentation(block_group)
            has_syntax_highlight = self.has_syntax_highlighting(block_group)
            has_keywords, keyword_count = self.contains_code_keywords(block_group)

            # Count total words
            total_text = " ".join(b.text for b in block_group)
            total_words = len(re.findall(r"\b\w+\b", total_text))

            confidence = self.calculate_confidence(
                is_monospace=is_monospace,
                has_indent=has_indent,
                avg_indent=avg_indent,
                has_syntax_highlight=has_syntax_highlight,
                keyword_count=keyword_count,
                total_words=total_words,
            )

            # Only include blocks with reasonable confidence
            if confidence >= 0.5:
                results.append((block_group, confidence))

        return results
