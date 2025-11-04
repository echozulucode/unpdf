"""Footnote and reference detection for PDF to Markdown conversion.

This module detects footnotes and references in PDFs by identifying superscript
markers and matching them with footer text or reference lists.
"""

import re
from dataclasses import dataclass
from typing import Literal

from unpdf.processors.layout_analyzer import BoundingBox, TextBlock


@dataclass
class FootnoteReference:
    """Represents a footnote reference marker in the text."""

    marker: str
    bbox: BoundingBox
    marker_type: Literal["numeric", "symbol", "letter"]
    confidence: float = 0.0


@dataclass
class FootnoteContent:
    """Represents the content of a footnote."""

    marker: str
    text: str
    bbox: BoundingBox
    confidence: float = 0.0


@dataclass
class Footnote:
    """Represents a complete footnote with reference and content."""

    reference: FootnoteReference
    content: FootnoteContent | None = None
    confidence: float = 0.0


class FootnoteDetector:
    """Detects footnotes and references in PDF documents."""

    # Common footnote symbols in order of preference
    FOOTNOTE_SYMBOLS = ["*", "†", "‡", "§", "¶", "‖", "#", "**", "††", "‡‡"]

    # Regex patterns for different marker types
    NUMERIC_PATTERN = re.compile(r"^\d+$")
    LETTER_PATTERN = re.compile(r"^[a-z]$", re.IGNORECASE)
    ROMAN_PATTERN = re.compile(r"^(?:i{1,3}|iv|vi{0,3}|ix|x)$", re.IGNORECASE)

    def __init__(
        self,
        superscript_size_ratio: float = 0.7,
        superscript_offset_threshold: float = 0.3,
        footer_region_ratio: float = 0.15,
        proximity_threshold: float = 50.0,
        min_marker_confidence: float = 0.6,
    ):
        """Initialize the footnote detector.

        Args:
            superscript_size_ratio: Maximum font size ratio for superscript
            superscript_offset_threshold: Minimum vertical offset ratio for superscript
            footer_region_ratio: Ratio of page height for footer region
            proximity_threshold: Maximum distance for marker-content matching (pixels)
            min_marker_confidence: Minimum confidence for marker detection
        """
        self.superscript_size_ratio = superscript_size_ratio
        self.superscript_offset_threshold = superscript_offset_threshold
        self.footer_region_ratio = footer_region_ratio
        self.proximity_threshold = proximity_threshold
        self.min_marker_confidence = min_marker_confidence

    def detect_footnotes(
        self,
        blocks: list[TextBlock],
        page_height: float,
        body_font_size: float = 12.0,
    ) -> list[Footnote]:
        """Detect all footnotes on a page.

        Args:
            blocks: List of text blocks to analyze
            page_height: Height of the page for footer detection
            body_font_size: Body font size for comparison

        Returns:
            List of detected footnotes
        """
        # Step 1: Detect reference markers
        references = self._detect_reference_markers(blocks, body_font_size)

        # Step 2: Detect footer content
        footer_y = page_height * (1 - self.footer_region_ratio)
        footer_contents = self._detect_footer_content(blocks, footer_y)

        # Step 3: Match references to content
        footnotes = self._match_references_to_content(references, footer_contents)

        # Step 4: Filter by confidence
        footnotes = [
            fn for fn in footnotes if fn.confidence >= self.min_marker_confidence
        ]

        return footnotes

    def _detect_reference_markers(
        self, blocks: list[TextBlock], body_font_size: float
    ) -> list[FootnoteReference]:
        """Detect footnote reference markers in text blocks.

        Args:
            blocks: List of text blocks to analyze
            body_font_size: Body font size for comparison

        Returns:
            List of detected reference markers
        """
        markers = []

        for block in blocks:
            # Check for superscript characteristics
            if not self._is_superscript(block, body_font_size):
                continue

            # Extract marker text
            marker_text = block.text.strip()
            if not marker_text:
                continue

            # Classify marker type
            marker_type = self._classify_marker(marker_text)
            if not marker_type:
                continue

            # Calculate confidence
            confidence = self._calculate_marker_confidence(
                block, body_font_size, marker_type
            )

            markers.append(
                FootnoteReference(
                    marker=marker_text,
                    bbox=block.bbox,
                    marker_type=marker_type,
                    confidence=confidence,
                )
            )

        return markers

    def _is_superscript(self, block: TextBlock, body_font_size: float) -> bool:
        """Check if a text block is a superscript.

        Args:
            block: Text block to check
            body_font_size: Body font size for comparison

        Returns:
            True if block appears to be superscript
        """
        # Check font size
        size_ratio = block.font_size / body_font_size
        if size_ratio > self.superscript_size_ratio:
            return False

        # Check if text is short (typically 1-3 characters)
        return not len(block.text.strip()) > 3

    def _classify_marker(
        self, text: str
    ) -> Literal["numeric", "symbol", "letter"] | None:
        """Classify the type of footnote marker.

        Args:
            text: Marker text to classify

        Returns:
            Marker type or None if not recognized
        """
        # Check for numeric markers
        if self.NUMERIC_PATTERN.match(text):
            return "numeric"

        # Check for symbol markers
        if text in self.FOOTNOTE_SYMBOLS:
            return "symbol"

        # Check for letter markers (lowercase or uppercase)
        if self.LETTER_PATTERN.match(text):
            return "letter"

        # Check for Roman numeral markers
        if self.ROMAN_PATTERN.match(text):
            return "letter"

        return None

    def _calculate_marker_confidence(
        self,
        block: TextBlock,
        body_font_size: float,
        marker_type: Literal["numeric", "symbol", "letter"],
    ) -> float:
        """Calculate confidence score for a reference marker.

        Args:
            block: Text block containing the marker
            body_font_size: Body font size for comparison
            marker_type: Type of marker detected

        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0

        # Font size signal (30% weight)
        size_ratio = block.font_size / body_font_size
        if size_ratio <= 0.6:
            confidence += 0.30
        elif size_ratio <= 0.7:
            confidence += 0.20
        else:
            confidence += 0.10

        # Marker type signal (30% weight)
        if marker_type == "numeric":
            confidence += 0.30
        elif marker_type == "symbol":
            confidence += 0.25
        else:  # letter
            confidence += 0.20

        # Text length signal (20% weight)
        text_length = len(block.text.strip())
        if text_length == 1:
            confidence += 0.20
        elif text_length == 2:
            confidence += 0.15
        else:
            confidence += 0.05

        # Position signal (20% weight)
        # Superscripts are typically positioned slightly above baseline
        # This would require baseline information, so we approximate
        confidence += 0.20

        return min(confidence, 1.0)

    def _detect_footer_content(
        self, blocks: list[TextBlock], footer_y: float
    ) -> list[FootnoteContent]:
        """Detect footnote content in the footer region.

        Args:
            blocks: List of text blocks to analyze
            footer_y: Y-coordinate where footer region begins

        Returns:
            List of detected footnote content blocks
        """
        contents = []

        for block in blocks:
            # Check if block is in footer region
            if block.bbox.y0 < footer_y:
                continue

            # Look for footnote marker at the start
            text = block.text.strip()
            marker_match = self._extract_footer_marker(text)

            if marker_match:
                marker, content_text = marker_match
                confidence = self._calculate_content_confidence(marker, content_text)

                contents.append(
                    FootnoteContent(
                        marker=marker,
                        text=content_text,
                        bbox=block.bbox,
                        confidence=confidence,
                    )
                )

        return contents

    def _extract_footer_marker(self, text: str) -> tuple[str, str] | None:
        """Extract footnote marker from footer text.

        Args:
            text: Footer text to analyze

        Returns:
            Tuple of (marker, content) or None if no marker found
        """
        # Try numeric markers (e.g., "1. Content" or "1 Content")
        match = re.match(r"^(\d+)[.\s:]\s*(.+)", text)
        if match:
            return match.group(1), match.group(2)

        # Try symbol markers
        for symbol in self.FOOTNOTE_SYMBOLS:
            if text.startswith(symbol):
                content = text[len(symbol) :].lstrip()
                if content:
                    return symbol, content

        # Try letter markers (e.g., "a. Content")
        match = re.match(r"^([a-z])[.\s:]\s*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)

        # Try Roman numeral markers
        match = re.match(r"^(i{1,3}|iv|vi{0,3}|ix|x)[.\s:]\s*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)

        return None

    def _calculate_content_confidence(self, marker: str, content: str) -> float:
        """Calculate confidence score for footnote content.

        Args:
            marker: Footnote marker
            content: Footnote content text

        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0

        # Marker validity (40% weight)
        if self.NUMERIC_PATTERN.match(marker):
            confidence += 0.40
        elif marker in self.FOOTNOTE_SYMBOLS:
            confidence += 0.35
        elif self.LETTER_PATTERN.match(marker) or self.ROMAN_PATTERN.match(marker):
            confidence += 0.30

        # Content length (30% weight)
        if len(content) > 20:
            confidence += 0.30
        elif len(content) > 10:
            confidence += 0.20
        else:
            confidence += 0.10

        # Content characteristics (30% weight)
        # Good footnotes typically have proper punctuation and capitalization
        if content[0].isupper():
            confidence += 0.15
        if content.endswith((".", "!", "?")):
            confidence += 0.15

        return min(confidence, 1.0)

    def _match_references_to_content(
        self,
        references: list[FootnoteReference],
        contents: list[FootnoteContent],
    ) -> list[Footnote]:
        """Match reference markers to their content.

        Args:
            references: List of reference markers
            contents: List of footnote contents

        Returns:
            List of matched footnotes
        """
        footnotes = []

        # Create a map of markers to contents for quick lookup
        content_map = {content.marker: content for content in contents}

        for reference in references:
            # Try exact marker match
            content = content_map.get(reference.marker)

            if content:
                # Calculate combined confidence
                combined_confidence = (reference.confidence + content.confidence) / 2

                footnotes.append(
                    Footnote(
                        reference=reference,
                        content=content,
                        confidence=combined_confidence,
                    )
                )
            else:
                # Reference without matching content (still valid)
                footnotes.append(
                    Footnote(
                        reference=reference,
                        content=None,
                        confidence=reference.confidence * 0.7,  # Penalty for no match
                    )
                )

        return footnotes

    def extract_reference_style(
        self, footnotes: list[Footnote]
    ) -> Literal["numeric", "symbol", "letter", "mixed"] | None:
        """Determine the reference style used in the document.

        Args:
            footnotes: List of detected footnotes

        Returns:
            Dominant reference style or None if unclear
        """
        if not footnotes:
            return None

        # Count marker types
        type_counts = {"numeric": 0, "symbol": 0, "letter": 0}

        for footnote in footnotes:
            type_counts[footnote.reference.marker_type] += 1

        # Find dominant type
        max_count = max(type_counts.values())
        if max_count == 0:
            return None

        # Check if one type dominates (>80%)
        total = sum(type_counts.values())
        for marker_type, count in type_counts.items():
            if count == max_count and count / total > 0.8:
                return marker_type  # type: ignore

        return "mixed"
