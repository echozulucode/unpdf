"""Docstrum Clustering for spatial text analysis.

This module implements the Docstrum algorithm (O'Gorman, 1993) for detecting
text lines and blocks through spatial clustering. It works by:
1. Building spatial index (KD-tree) of text components
2. Finding k-nearest neighbors for each component
3. Computing document spectrum (angle/distance histograms)
4. Detecting skew and spacing parameters
5. Forming text lines via transitive closure
6. Merging lines into blocks based on proximity
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy.spatial import KDTree  # type: ignore[import-untyped]


@dataclass
class TextComponent:
    """Represents a connected text component (character or word).

    Attributes:
        x: X-coordinate of component center
        y: Y-coordinate of component center
        width: Component width
        height: Component height
        text: Text content
        bbox: Bounding box (x0, y0, x1, y1)
    """

    x: float
    y: float
    width: float
    height: float
    text: str
    bbox: tuple[float, float, float, float]

    @property
    def center(self) -> tuple[float, float]:
        """Get component center coordinates."""
        return (self.x, self.y)


@dataclass
class TextLine:
    """Represents a detected text line.

    Attributes:
        components: List of text components in reading order
        angle: Line angle in radians
        avg_height: Average component height
        bbox: Line bounding box (x0, y0, x1, y1)
    """

    components: list[TextComponent]
    angle: float
    avg_height: float
    bbox: tuple[float, float, float, float]

    @property
    def text(self) -> str:
        """Get line text with inferred spaces."""
        if not self.components:
            return ""
        # Sort components by x coordinate
        sorted_comps = sorted(self.components, key=lambda c: c.x)
        result = []
        for i, comp in enumerate(sorted_comps):
            result.append(comp.text)
            # Add space if next component is far enough
            if i < len(sorted_comps) - 1:
                next_comp = sorted_comps[i + 1]
                gap = next_comp.x - (comp.x + comp.width)
                avg_width = (comp.width + next_comp.width) / 2
                if gap > avg_width * 0.3:  # Space threshold
                    result.append(" ")
        return "".join(result)


@dataclass
class TextBlock:
    """Represents a detected text block.

    Attributes:
        lines: List of text lines
        bbox: Block bounding box (x0, y0, x1, y1)
        alignment: Text alignment (left, center, right, justify)
    """

    lines: list[TextLine]
    bbox: tuple[float, float, float, float]
    alignment: str = "left"

    @property
    def text(self) -> str:
        """Get block text with line breaks."""
        return "\n".join(line.text for line in self.lines)


class DocstrumClusterer:
    """Implements Docstrum algorithm for spatial text clustering.

    The algorithm detects text lines and blocks by analyzing the spatial
    distribution of text components. It's particularly effective for:
    - Multi-orientation text
    - Skewed documents
    - Complex layouts with varying fonts
    """

    def __init__(
        self,
        k_neighbors: int = 5,
        angle_bins: int = 36,
        distance_bins: int = 50,
        line_merge_factor: float = 2.5,
        block_merge_parallel: float = 1.75,
        block_merge_perpendicular: float = 0.4,
    ):
        """Initialize Docstrum clusterer.

        Args:
            k_neighbors: Number of nearest neighbors to consider (default: 5)
            angle_bins: Number of bins for angle histogram (default: 36 = 10° bins)
            distance_bins: Number of bins for distance histogram (default: 50)
            line_merge_factor: Factor for merging components into lines (default: 2.5)
            block_merge_parallel: Parallel distance factor for block merging (default: 1.75)
            block_merge_perpendicular: Perpendicular distance factor (default: 0.4)
        """
        self.k_neighbors = k_neighbors
        self.angle_bins = angle_bins
        self.distance_bins = distance_bins
        self.line_merge_factor = line_merge_factor
        self.block_merge_parallel = block_merge_parallel
        self.block_merge_perpendicular = block_merge_perpendicular

    def cluster(self, components: list[TextComponent]) -> list[TextBlock]:
        """Cluster text components into blocks.

        Args:
            components: List of text components to cluster

        Returns:
            List of detected text blocks in reading order
        """
        if not components:
            return []

        # Build spatial index
        kdtree = self._build_spatial_index(components)

        # Find k-nearest neighbors for each component
        neighbors_data = self._find_nearest_neighbors(components, kdtree)

        # Compute document spectrum
        angles, distances = self._compute_document_spectrum(components, neighbors_data)

        # Detect dominant parameters
        skew_angle = self._detect_skew(angles)
        char_spacing = self._detect_spacing(distances)

        # Form text lines
        lines = self._form_text_lines(
            components, neighbors_data, skew_angle, char_spacing
        )

        # Merge lines into blocks
        blocks = self._merge_lines_into_blocks(lines, char_spacing)

        return blocks

    def _build_spatial_index(self, components: list[TextComponent]) -> KDTree:
        """Build KD-tree for efficient spatial queries.

        Args:
            components: List of text components

        Returns:
            KD-tree for O(log n) nearest neighbor queries
        """
        points = np.array([comp.center for comp in components])
        return KDTree(points)

    def _find_nearest_neighbors(
        self, components: list[TextComponent], kdtree: KDTree
    ) -> list[list[tuple[int, float, float]]]:
        """Find k-nearest neighbors for each component.

        Args:
            components: List of text components
            kdtree: Spatial index

        Returns:
            For each component, list of (neighbor_idx, distance, angle) tuples
        """
        neighbors_data: list[list[tuple[int, float, float]]] = []
        n = len(components)

        for comp in components:
            # Query k+1 neighbors (includes self), but limit to available components
            k_actual = min(self.k_neighbors + 1, n)
            distances, indices = kdtree.query(comp.center, k=k_actual)

            # Handle single result (not an array)
            if k_actual == 1:
                neighbors_data.append([])
                continue

            # Convert to arrays if needed
            if not isinstance(distances, np.ndarray):
                distances = np.array([distances])
                indices = np.array([indices])

            # Exclude self and compute angles
            neighbors = []
            for j in range(1, len(indices)):  # Skip first (self)
                neighbor_idx = int(indices[j])
                dist = float(distances[j])
                neighbor = components[neighbor_idx]

                # Compute angle from component to neighbor
                dx = neighbor.x - comp.x
                dy = neighbor.y - comp.y
                angle = math.atan2(dy, dx)

                neighbors.append((neighbor_idx, dist, angle))

            neighbors_data.append(neighbors)

        return neighbors_data

    def _compute_document_spectrum(
        self,
        components: list[TextComponent],
        neighbors_data: list[list[tuple[int, float, float]]],
    ) -> tuple[list[float], list[float]]:
        """Compute document spectrum (angle and distance histograms).

        Args:
            components: List of text components
            neighbors_data: Nearest neighbor data

        Returns:
            Tuple of (angles, distances) lists
        """
        angles = []
        distances = []

        for neighbors in neighbors_data:
            for _, dist, angle in neighbors:
                angles.append(angle)
                distances.append(dist)

        return angles, distances

    def _detect_skew(self, angles: list[float]) -> float:
        """Detect document skew from angle histogram.

        Args:
            angles: List of angles between components

        Returns:
            Dominant angle in radians (document skew)
        """
        if not angles:
            return 0.0

        # Create angle histogram
        hist, bin_edges = np.histogram(
            angles, bins=self.angle_bins, range=(-math.pi, math.pi)
        )

        # Find peak (most common angle)
        peak_idx = int(np.argmax(hist))
        peak_angle = float((bin_edges[peak_idx] + bin_edges[peak_idx + 1]) / 2)

        return peak_angle

    def _detect_spacing(self, distances: list[float]) -> float:
        """Detect character spacing from distance histogram.

        Args:
            distances: List of distances between components

        Returns:
            Typical character spacing in pixels
        """
        if not distances:
            return 10.0  # Default fallback

        # Create distance histogram
        hist, bin_edges = np.histogram(distances, bins=self.distance_bins)

        # Find first significant peak (character spacing)
        # Skip first few bins which represent very close characters
        start_idx = 2
        for i in range(start_idx, len(hist)):
            if hist[i] > np.mean(hist) * 1.5:  # Significant peak threshold
                spacing = float((bin_edges[i] + bin_edges[i + 1]) / 2)
                return spacing

        # Fallback to median distance
        return float(np.median(distances))

    def _form_text_lines(
        self,
        components: list[TextComponent],
        neighbors_data: list[list[tuple[int, float, float]]],
        skew_angle: float,
        char_spacing: float,
    ) -> list[TextLine]:
        """Form text lines via transitive closure.

        Args:
            components: List of text components
            neighbors_data: Nearest neighbor data
            skew_angle: Document skew angle
            char_spacing: Typical character spacing

        Returns:
            List of detected text lines
        """
        # Build adjacency graph based on line merge factor
        n = len(components)
        adjacency: list[set[int]] = [set() for _ in range(n)]

        threshold = char_spacing * self.line_merge_factor

        for i, neighbors in enumerate(neighbors_data):
            for neighbor_idx, dist, angle in neighbors:
                # Check if neighbor is on same line
                # Allow ±15° tolerance around skew angle
                angle_diff = abs(angle - skew_angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff

                if dist < threshold and angle_diff < math.pi / 12:  # 15°
                    adjacency[i].add(neighbor_idx)
                    adjacency[neighbor_idx].add(i)

        # Find connected components (transitive closure)
        visited = [False] * n
        lines = []

        for i in range(n):
            if visited[i]:
                continue

            # BFS to find all components in same line
            line_components = []
            queue = [i]
            visited[i] = True

            while queue:
                curr = queue.pop(0)
                line_components.append(components[curr])

                for neighbor in adjacency[curr]:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)

            # Create text line
            if line_components:
                line = self._create_text_line(line_components, skew_angle)
                lines.append(line)

        return lines

    def _create_text_line(
        self, components: list[TextComponent], angle: float
    ) -> TextLine:
        """Create TextLine from components.

        Args:
            components: Components in the line
            angle: Line angle

        Returns:
            TextLine object
        """
        # Sort components by position along line direction
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        sorted_comps = sorted(
            components, key=lambda c: c.x * cos_angle + c.y * sin_angle
        )

        # Compute bounding box
        x0 = min(c.bbox[0] for c in components)
        y0 = min(c.bbox[1] for c in components)
        x1 = max(c.bbox[2] for c in components)
        y1 = max(c.bbox[3] for c in components)

        # Compute average height
        avg_height = sum(c.height for c in components) / len(components)

        return TextLine(
            components=sorted_comps,
            angle=angle,
            avg_height=avg_height,
            bbox=(x0, y0, x1, y1),
        )

    def _merge_lines_into_blocks(
        self, lines: list[TextLine], char_spacing: float
    ) -> list[TextBlock]:
        """Merge text lines into blocks based on proximity.

        Args:
            lines: List of text lines
            char_spacing: Typical character spacing

        Returns:
            List of text blocks
        """
        if not lines:
            return []

        # Build line adjacency graph
        n = len(lines)
        adjacency: list[set[int]] = [set() for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                if self._should_merge_lines(lines[i], lines[j], char_spacing):
                    adjacency[i].add(j)
                    adjacency[j].add(i)

        # Find connected components
        visited = [False] * n
        blocks = []

        for i in range(n):
            if visited[i]:
                continue

            # BFS to find all lines in same block
            block_lines = []
            queue = [i]
            visited[i] = True

            while queue:
                curr = queue.pop(0)
                block_lines.append(lines[curr])

                for neighbor in adjacency[curr]:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)

            # Create text block
            if block_lines:
                block = self._create_text_block(block_lines)
                blocks.append(block)

        return blocks

    def _should_merge_lines(
        self, line1: TextLine, line2: TextLine, char_spacing: float
    ) -> bool:
        """Check if two lines should be merged into same block.

        Args:
            line1: First text line
            line2: Second text line
            char_spacing: Typical character spacing

        Returns:
            True if lines should be merged
        """
        # Compute perpendicular distance (vertical gap)
        y_gap = min(
            abs(line1.bbox[1] - line2.bbox[3]), abs(line2.bbox[1] - line1.bbox[3])
        )

        # Compute parallel distance (horizontal alignment)
        x_overlap = min(line1.bbox[2], line2.bbox[2]) - max(
            line1.bbox[0], line2.bbox[0]
        )

        # Check proximity thresholds
        perpendicular_threshold = (
            (line1.avg_height + line2.avg_height) / 2 * self.block_merge_parallel
        )
        parallel_threshold = char_spacing * self.block_merge_perpendicular

        # Lines should be close vertically and overlap horizontally
        return y_gap < perpendicular_threshold and x_overlap > -parallel_threshold

    def _create_text_block(self, lines: list[TextLine]) -> TextBlock:
        """Create TextBlock from lines.

        Args:
            lines: Lines in the block

        Returns:
            TextBlock object
        """
        # Sort lines by y coordinate (top to bottom)
        sorted_lines = sorted(lines, key=lambda line: line.bbox[1])

        # Compute bounding box
        x0 = min(line.bbox[0] for line in lines)
        y0 = min(line.bbox[1] for line in lines)
        x1 = max(line.bbox[2] for line in lines)
        y1 = max(line.bbox[3] for line in lines)

        # Detect alignment
        alignment = self._detect_alignment(sorted_lines)

        return TextBlock(lines=sorted_lines, bbox=(x0, y0, x1, y1), alignment=alignment)

    def _detect_alignment(self, lines: list[TextLine]) -> str:
        """Detect text alignment from line positions.

        Args:
            lines: List of text lines

        Returns:
            Alignment type: 'left', 'center', 'right', or 'justify'
        """
        if len(lines) < 2:
            return "left"

        # Compute variance of left and right edges
        left_edges = [line.bbox[0] for line in lines]
        right_edges = [line.bbox[2] for line in lines]

        left_var = np.var(left_edges)
        right_var = np.var(right_edges)

        # Threshold for aligned edges (5 pixels variance)
        threshold = 25.0

        if left_var < threshold and right_var < threshold:
            return "justify"
        elif left_var < threshold:
            return "left"
        elif right_var < threshold:
            return "right"
        else:
            # Check if centers are aligned
            centers = [(line.bbox[0] + line.bbox[2]) / 2 for line in lines]
            center_var = np.var(centers)
            if center_var < threshold:
                return "center"
            return "left"  # Default
