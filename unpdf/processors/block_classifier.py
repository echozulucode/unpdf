"""Block classification for determining content types.

This module classifies text blocks into semantic categories like headers,
paragraphs, lists, code blocks, etc., using font analysis and heuristics.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from unpdf.models.layout import Block, BlockType, Style


@dataclass
class FontStatistics:
    """Statistics about font usage in a document.

    Attributes:
        body_size: Most common font size (body text)
        size_counts: Count of blocks at each font size
        monospace_ratio: Proportion of monospace text
    """

    body_size: float
    size_counts: dict[float, int]
    monospace_ratio: float


class BlockClassifier:
    """Classifies text blocks into semantic types.

    Uses font analysis, content patterns, and heuristics to determine
    the appropriate BlockType for each text block.

    Attributes:
        heading_size_ratios: Multipliers for heading detection
        list_patterns: Regex patterns for list item detection
        code_indicators: Patterns suggesting code content
    """

    # Font size ratios relative to body text for header detection
    # Updated to match HeadingProcessor thresholds for consistency
    HEADING_SIZE_RATIOS = {
        1: (1.7, 2.5),  # H1: 1.7-2.5× body (70%+ larger - major heading)
        2: (1.4, 1.7),  # H2: 1.4-1.7× body (40-70% larger - section)
        3: (1.2, 1.4),  # H3: 1.2-1.4× body (20-40% larger - subsection)
        4: (1.08, 1.2),  # H4: 1.08-1.2× body + bold (8-20% larger)
        5: (1.0, 1.08),  # H5: 1.0-1.08× body + bold
        6: (0.9, 1.0),  # H6: 0.9-1.0× body + bold
    }

    # Patterns for detecting list items
    LIST_PATTERNS = [
        r"^[\u2022\u2023\u25E6\u25AA\u2043\u2219]\s+",  # Bullet characters (•◦▪‣⁃)
        r"^\d+\.\s+",  # Numbered list (1. )
        r"^[a-z]\.\s+",  # Lettered list (a. )
        r"^[ivxlcdm]+\.\s+",  # Roman numerals (i. ii. iii.)
        r"^[-*+]\s+",  # Markdown-style bullets
        r"^[☐☑✓✗]\s+",  # Checkboxes
    ]

    # Indicators of code content
    CODE_INDICATORS = [
        r"^\s{4,}",  # Indented 4+ spaces
        r"^[\t]",  # Tab-indented
        r"[{}()\[\];]",  # Code punctuation
        r"(def|class|function|var|let|const|import|from)\s+",  # Keywords
        r"(if|for|while|return|else)\s*[\(\{]",  # Control structures
    ]

    def __init__(self) -> None:
        """Initialize the block classifier."""
        self.list_pattern = re.compile("|".join(self.LIST_PATTERNS))
        self.code_pattern = re.compile("|".join(self.CODE_INDICATORS))

    def compute_font_statistics(self, blocks: Sequence[Block]) -> FontStatistics:
        """Compute font statistics from blocks.

        Args:
            blocks: Sequence of blocks to analyze

        Returns:
            FontStatistics with body size and distribution
        """
        size_counts: dict[float, int] = {}
        monospace_count = 0

        for block in blocks:
            if block.style and block.style.size:
                size = block.style.size
                size_counts[size] = size_counts.get(size, 0) + 1

                if block.style.monospace:
                    monospace_count += 1

        # Most common size is likely body text
        body_size = (
            max(size_counts.items(), key=lambda x: x[1])[0] if size_counts else 12.0
        )

        monospace_ratio = monospace_count / len(blocks) if blocks else 0.0

        return FontStatistics(
            body_size=body_size,
            size_counts=size_counts,
            monospace_ratio=monospace_ratio,
        )

    def classify_block(self, block: Block, font_stats: FontStatistics | float) -> BlockType:
        """Classify a single block.

        Args:
            block: Block to classify (can be Block or TextBlock)
            font_stats: Font statistics for context, or body font size as float

        Returns:
            BlockType classification
        """
        # Convert float to FontStatistics if needed
        if isinstance(font_stats, (int, float)):
            font_stats = FontStatistics(
                body_size=float(font_stats),
                size_counts={float(font_stats): 1},
                monospace_ratio=0.0
            )
            
        # Support both Block (content) and TextBlock (text) types
        text = getattr(block, 'content', None) or getattr(block, 'text', '')
        if not text or not isinstance(text, str):
            return BlockType.TEXT

        content = text.strip()
        if not content:
            return BlockType.TEXT

        # Check for horizontal rule
        if self._is_horizontal_rule(content):
            return BlockType.HORIZONTAL_RULE

        # Check for code block based on monospace font
        # Handle both Block.style and TextBlock.font_name
        is_monospace = False
        if hasattr(block, 'style') and block.style and block.style.monospace:
            is_monospace = True
        elif hasattr(block, 'font_name') and block.font_name:
            # Check if font name suggests monospace
            monospace_fonts = ['courier', 'consolas', 'monaco', 'menlo', 'mono']
            is_monospace = any(font in block.font_name.lower() for font in monospace_fonts)
        
        if is_monospace and self._is_code_content(content):
            return BlockType.CODE

        # Check for list item
        if self._is_list_item(content):
            return BlockType.LIST

        # Check for heading based on font size
        # Handle both Block.style.size and TextBlock.font_size
        font_size = None
        if hasattr(block, 'style') and block.style and block.style.size:
            font_size = block.style.size
        elif hasattr(block, 'font_size'):
            font_size = block.font_size
            
        if font_size:
            # Skip heading detection if block has inline formatting (only for Block type)
            if hasattr(block, 'metadata') and not self._has_inline_formatting(block):
                heading_level = self._detect_heading_level_from_size(font_size, font_stats)
                if heading_level:
                    # Store heading level in metadata if available
                    if block.metadata is None:
                        block.metadata = {}
                    block.metadata["heading_level"] = heading_level
                    return BlockType.HEADING
            else:
                # For TextBlock, just check size
                heading_level = self._detect_heading_level_from_size(font_size, font_stats)
                if heading_level:
                    return BlockType.HEADING

        # Check for blockquote
        if self._is_blockquote(content):
            return BlockType.BLOCKQUOTE

        # Default to text/paragraph
        return BlockType.TEXT
    
    def _detect_heading_level_from_size(self, font_size: float, font_stats: FontStatistics) -> int | None:
        """Detect heading level based on font size.
        
        Args:
            font_size: Font size to check
            font_stats: Font statistics for context
            
        Returns:
            Heading level (1-6) or None if not a heading
        """
        ratio = font_size / font_stats.body_size
        
        # Check each heading level
        for level, (min_ratio, max_ratio) in self.HEADING_SIZE_RATIOS.items():
            if min_ratio <= ratio < max_ratio:
                return level
                
        return None

    def classify_blocks(self, blocks: Sequence[Block]) -> None:
        """Classify all blocks in place.

        Args:
            blocks: Sequence of blocks to classify
        """
        if not blocks:
            return

        # Compute font statistics once
        font_stats = self.compute_font_statistics(blocks)

        # Classify each block
        for block in blocks:
            block.block_type = self.classify_block(block, font_stats)

    def _is_horizontal_rule(self, content: str) -> bool:
        """Check if content is a horizontal rule.

        Args:
            content: Text content to check

        Returns:
            True if content appears to be a horizontal rule
        """
        # Repeated characters that form a visual line
        hr_patterns = [
            r"^[-_*=~]{3,}$",  # ----, ____, ****, ====, ~~~~
            r"^[─━═]{2,}$",  # Box drawing characters
        ]
        return any(re.match(pattern, content.strip()) for pattern in hr_patterns)

    def _is_code_content(self, content: str) -> bool:
        """Check if content appears to be code.

        Args:
            content: Text content to check

        Returns:
            True if content looks like code
        """
        # Multiple indicators increase confidence
        indicator_count = sum(1 for _ in self.code_pattern.finditer(content))

        # At least 2 code indicators, or starts with indentation
        return indicator_count >= 2 or content.startswith(("    ", "\t"))

    def _is_list_item(self, content: str) -> bool:
        """Check if content is a list item.

        Args:
            content: Text content to check

        Returns:
            True if content starts with a list marker
        """
        return bool(self.list_pattern.match(content))

    def _is_blockquote(self, content: str) -> bool:
        """Check if content is a blockquote.

        Args:
            content: Text content to check

        Returns:
            True if content appears to be a blockquote
        """
        # Lines starting with > or common quote indicators
        lines = content.split("\n")
        quote_lines = sum(
            1 for line in lines if line.strip().startswith((">", "»", "❝"))
        )

        # Majority of lines start with quote marker
        return quote_lines > len(lines) / 2 if lines else False

    def _detect_heading_level(
        self, style: Style, font_stats: FontStatistics
    ) -> int | None:
        """Detect heading level from style.

        Args:
            style: Block style with font information
            font_stats: Font statistics for comparison

        Returns:
            Heading level (1-6) or None if not a heading
        """
        if not style.size:
            return None

        ratio = style.size / font_stats.body_size

        # Check each heading level
        for level, (min_ratio, max_ratio) in self.HEADING_SIZE_RATIOS.items():
            if min_ratio <= ratio <= max_ratio:
                # H4-H6 require bold weight or larger size
                if level >= 4:
                    # For H4-H6, require bold OR size > 1.15×
                    if self._is_bold(style) or ratio > 1.15:
                        return level
                else:
                    return level

        return None

    def _has_inline_formatting(self, block: Block) -> bool:
        """Check if block contains inline formatting (mixed bold/italic spans).

        Blocks with inline formatting should not be classified as headers.

        Args:
            block: Block to check

        Returns:
            True if block has mixed formatting spans
        """
        if not block.spans or len(block.spans) <= 1:
            return False

        # Check if spans have different formatting
        first_span = block.spans[0]
        for span in block.spans[1:]:
            if span.bold != first_span.bold or span.italic != first_span.italic:
                return True

        return False

    def _is_bold(self, style: Style) -> bool:
        """Check if style is bold.

        Args:
            style: Style to check

        Returns:
            True if weight indicates bold
        """
        if style.weight is None:
            return False

        if isinstance(style.weight, int):
            return style.weight >= 600
        elif isinstance(style.weight, str):
            return style.weight.lower() in ("bold", "semibold", "black")

        return False
