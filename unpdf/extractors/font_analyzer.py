"""Font analysis system for PDF text classification.

This module extracts font metrics and performs clustering analysis to identify
document structure based on font characteristics.
"""

from collections import defaultdict
from dataclasses import dataclass

import numpy as np


@dataclass
class FontMetrics:
    """Metrics for a specific font instance."""

    family: str
    size: float
    weight: str  # 'normal', 'bold', etc.
    style: str  # 'normal', 'italic', etc.
    is_monospace: bool
    char_width_mean: float
    char_width_variance: float


@dataclass
class FontCluster:
    """Cluster of similar font usages."""

    representative_size: float
    font_family: str
    weight: str
    style: str
    occurrences: int
    confidence: float
    inferred_role: str | None = None  # 'h1', 'h2', 'body', 'code', etc.


class FontAnalyzer:
    """Analyzes font usage patterns in PDF documents."""

    # Thresholds for monospace detection
    MONOSPACE_VARIANCE_THRESHOLD = 0.05

    # Size ratios for header detection (relative to body font size)
    H1_SIZE_RATIO = (2.0, 2.5)
    H2_SIZE_RATIO = (1.5, 1.8)
    H3_SIZE_RATIO = (1.2, 1.4)
    H4_SIZE_RATIO = (1.1, 1.15)

    def __init__(self) -> None:
        """Initialize the font analyzer."""
        self.fonts: dict[str, FontMetrics] = {}
        self.clusters: list[FontCluster] = []
        self.body_font_size: float | None = None

    def extract_font_metrics(
        self, chars: list[dict], font_name: str
    ) -> FontMetrics:
        """Extract metrics for a font from character data.

        Args:
            chars: List of character dictionaries with 'width' and other properties
            font_name: Name of the font

        Returns:
            FontMetrics object with calculated statistics
        """
        widths = [c.get("width", 0) for c in chars if c.get("width", 0) > 0]

        if not widths:
            return FontMetrics(
                family=font_name,
                size=0.0,
                weight="normal",
                style="normal",
                is_monospace=False,
                char_width_mean=0.0,
                char_width_variance=0.0,
            )

        mean_width = np.mean(widths)
        variance = np.var(widths)
        coefficient_of_variation = (
            np.sqrt(variance) / mean_width if mean_width > 0 else 1.0
        )

        # Extract font properties from name
        weight = self._extract_weight(font_name)
        style = self._extract_style(font_name)
        size = chars[0].get("size", 0.0) if chars else 0.0

        is_monospace = bool(coefficient_of_variation < self.MONOSPACE_VARIANCE_THRESHOLD)

        return FontMetrics(
            family=self._normalize_font_family(font_name),
            size=float(size),
            weight=weight,
            style=style,
            is_monospace=is_monospace,
            char_width_mean=float(mean_width),
            char_width_variance=float(variance),
        )

    def _extract_weight(self, font_name: str) -> str:
        """Extract font weight from font name."""
        name_lower = font_name.lower()
        if any(w in name_lower for w in ["bold", "heavy", "black"]):
            return "bold"
        if any(w in name_lower for w in ["light", "thin"]):
            return "light"
        return "normal"

    def _extract_style(self, font_name: str) -> str:
        """Extract font style from font name."""
        name_lower = font_name.lower()
        if "italic" in name_lower or "oblique" in name_lower:
            return "italic"
        return "normal"

    def _normalize_font_family(self, font_name: str) -> str:
        """Normalize font family name by removing weight/style suffixes."""
        # Remove common suffixes
        suffixes = [
            "-Bold",
            "-Italic",
            "-BoldItalic",
            "-Regular",
            "-Light",
            ",Bold",
            ",Italic",
        ]
        normalized = font_name
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
        return normalized

    def build_font_clusters(
        self, font_usages: dict[str, list[dict]]
    ) -> list[FontCluster]:
        """Build clusters of similar fonts.

        Args:
            font_usages: Dictionary mapping font keys to lists of usage instances
                        Each instance should have 'size', 'family', 'weight', 'style'

        Returns:
            List of FontCluster objects sorted by occurrence frequency
        """
        # Group by (family, weight, style) first, collecting all sizes
        clusters_dict: dict[tuple[str, str, str], list[float]] = defaultdict(list)

        for instances in font_usages.values():
            for instance in instances:
                key = (
                    instance.get("family", ""),
                    instance.get("weight", "normal"),
                    instance.get("style", "normal"),
                )
                clusters_dict[key].append(instance.get("size", 0.0))

        # Convert to FontCluster objects
        clusters = []
        for (family, weight, style), sizes in clusters_dict.items():
            median_size = float(np.median(sizes))
            std_size = float(np.std(sizes))

            # Calculate confidence: 1.0 for no variance, lower for higher variance
            if median_size > 0 and len(sizes) > 1:
                confidence = float(1.0 - min(1.0, std_size / median_size))
            else:
                confidence = 1.0

            cluster = FontCluster(
                representative_size=median_size,
                font_family=family,
                weight=weight,
                style=style,
                occurrences=len(sizes),
                confidence=confidence,
            )
            clusters.append(cluster)

        # Sort by occurrence count (descending)
        clusters.sort(key=lambda c: c.occurrences, reverse=True)
        self.clusters = clusters

        # Identify body font (most common, normal weight)
        self._identify_body_font(clusters)

        # Infer roles for each cluster
        self._infer_cluster_roles(clusters)

        return clusters

    def _identify_body_font(self, clusters: list[FontCluster]) -> None:
        """Identify the body font size from clusters."""
        # Body font is typically the most common normal-weight font
        for cluster in clusters:
            if cluster.weight == "normal" and cluster.style == "normal":
                self.body_font_size = cluster.representative_size
                cluster.inferred_role = "body"
                break

        # Fallback: use most common font
        if self.body_font_size is None and clusters:
            self.body_font_size = clusters[0].representative_size
            clusters[0].inferred_role = "body"

    def _infer_cluster_roles(self, clusters: list[FontCluster]) -> None:
        """Infer structural roles for font clusters based on size ratios."""
        if self.body_font_size is None or self.body_font_size == 0:
            return

        for cluster in clusters:
            if cluster.inferred_role:  # Already assigned (e.g., 'body')
                continue

            size_ratio = cluster.representative_size / self.body_font_size

            # Check if monospace-like characteristics suggest code
            # (Note: would need is_monospace flag in cluster for this)

            # Check header ratios
            if self.H1_SIZE_RATIO[0] <= size_ratio <= self.H1_SIZE_RATIO[1]:
                cluster.inferred_role = "h1"
            elif self.H2_SIZE_RATIO[0] <= size_ratio <= self.H2_SIZE_RATIO[1]:
                cluster.inferred_role = "h2"
            elif self.H3_SIZE_RATIO[0] <= size_ratio <= self.H3_SIZE_RATIO[1]:
                cluster.inferred_role = "h3"
            elif self.H4_SIZE_RATIO[0] <= size_ratio <= self.H4_SIZE_RATIO[1]:
                cluster.inferred_role = "h4"
            elif size_ratio < 0.9:
                cluster.inferred_role = "small"  # Footnotes, captions, etc.
            elif cluster.weight == "bold" or cluster.style == "italic":
                cluster.inferred_role = "emphasis"
            else:
                cluster.inferred_role = "body"

    def get_font_role(
        self, family: str, size: float, weight: str = "normal", style: str = "normal"
    ) -> str:
        """Get the inferred role for a specific font instance.

        Args:
            family: Font family name
            size: Font size in points
            weight: Font weight
            style: Font style

        Returns:
            Inferred role string (e.g., 'h1', 'body', 'code')
        """
        # Find matching cluster
        best_match = None
        min_distance = float("inf")

        for cluster in self.clusters:
            # Calculate distance metric
            size_diff = abs(cluster.representative_size - size)
            family_match = (
                0 if self._normalize_font_family(family) == cluster.font_family else 1
            )
            weight_match = 0 if weight == cluster.weight else 0.5
            style_match = 0 if style == cluster.style else 0.5

            distance = size_diff + family_match * 10 + weight_match + style_match

            if distance < min_distance:
                min_distance = distance
                best_match = cluster

        if best_match and best_match.inferred_role:
            return best_match.inferred_role

        # Fallback: use size ratio
        if self.body_font_size and self.body_font_size > 0:
            ratio = size / self.body_font_size
            if ratio >= 2.0:
                return "h1"
            elif ratio >= 1.5:
                return "h2"
            elif ratio >= 1.2:
                return "h3"

        return "body"

    def detect_monospace_fonts(
        self, char_data: dict[str, list[dict]]
    ) -> list[str]:
        """Detect which fonts are monospace.

        Args:
            char_data: Dictionary mapping font names to character data

        Returns:
            List of font names that are monospace
        """
        monospace_fonts = []

        for font_name, chars in char_data.items():
            metrics = self.extract_font_metrics(chars, font_name)
            if metrics.is_monospace:
                monospace_fonts.append(font_name)

        return monospace_fonts
