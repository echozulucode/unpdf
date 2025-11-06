"""Element-level accuracy scoring.

This module calculates precision, recall, and F1 scores for element detection.

Style: Google docstrings, black formatting
"""

from dataclasses import dataclass

from .element_detector import Element, ElementType


@dataclass
class ElementScores:
    """Accuracy scores for element detection.

    Attributes:
        precision: Percentage of detected elements that are correct (0-1)
        recall: Percentage of actual elements that were detected (0-1)
        f1_score: Harmonic mean of precision and recall (0-1)
        true_positives: Number of correctly detected elements
        false_positives: Number of incorrectly detected elements
        false_negatives: Number of missed elements
    """

    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    false_negatives: int

    @property
    def accuracy_percentage(self) -> float:
        """Overall accuracy as a percentage (0-100)."""
        return self.f1_score * 100


@dataclass
class DetailedAccuracy:
    """Detailed accuracy breakdown by element type.

    Attributes:
        overall: Overall accuracy scores across all elements
        by_type: Accuracy scores for each element type
        total_detected: Total number of elements detected
        total_expected: Total number of expected elements
        element_counts: Count of each element type detected vs expected
    """

    overall: ElementScores
    by_type: dict[ElementType, ElementScores]
    total_detected: int
    total_expected: int
    element_counts: dict[ElementType, dict[str, int]]


class ElementScorer:
    """Calculates accuracy scores for element detection.

    This class compares detected elements against expected elements
    and calculates precision, recall, and F1 scores.

    Example:
        >>> scorer = ElementScorer()
        >>> scores = scorer.calculate_scores(detected, expected)
        >>> print(f"Accuracy: {scores.overall.accuracy_percentage:.1f}%")
    """

    def calculate_scores(
        self, detected_elements: list[Element], expected_elements: list[Element]
    ) -> DetailedAccuracy:
        """Calculate accuracy scores by comparing detected vs expected elements.

        Args:
            detected_elements: Elements detected by the system
            expected_elements: Ground truth elements

        Returns:
            DetailedAccuracy object with overall and per-type scores
        """
        # Count elements by type
        detected_counts = self._count_by_type(detected_elements)
        expected_counts = self._count_by_type(expected_elements)

        # Calculate overall scores
        overall_scores = self._calculate_element_scores(
            detected_counts, expected_counts
        )

        # Calculate per-type scores
        by_type_scores = {}
        for elem_type in ElementType:
            detected = detected_counts.get(elem_type, 0)
            expected = expected_counts.get(elem_type, 0)
            by_type_scores[elem_type] = self._calculate_single_type_scores(
                detected, expected
            )

        # Build element counts comparison
        element_counts = {}
        for elem_type in ElementType:
            element_counts[elem_type] = {
                "detected": detected_counts.get(elem_type, 0),
                "expected": expected_counts.get(elem_type, 0),
            }

        return DetailedAccuracy(
            overall=overall_scores,
            by_type=by_type_scores,
            total_detected=len(detected_elements),
            total_expected=len(expected_elements),
            element_counts=element_counts,
        )

    def _count_by_type(self, elements: list[Element]) -> dict[ElementType, int]:
        """Count elements by their type.

        Args:
            elements: List of elements to count

        Returns:
            Dictionary mapping ElementType to count
        """
        counts: dict[ElementType, int] = {}
        for element in elements:
            counts[element.type] = counts.get(element.type, 0) + 1
        return counts

    def _calculate_element_scores(
        self, detected: dict[ElementType, int], expected: dict[ElementType, int]
    ) -> ElementScores:
        """Calculate precision, recall, and F1 for overall element detection.

        Args:
            detected: Counts of detected elements by type
            expected: Counts of expected elements by type

        Returns:
            ElementScores with calculated metrics
        """
        # Calculate true positives (minimum of detected and expected)
        # False positives (detected but not expected)
        # False negatives (expected but not detected)
        tp = 0
        fp = 0
        fn = 0

        all_types = set(detected.keys()) | set(expected.keys())
        for elem_type in all_types:
            detected_count = detected.get(elem_type, 0)
            expected_count = expected.get(elem_type, 0)

            # True positives: the overlap
            tp += min(detected_count, expected_count)

            # False positives: detected more than expected
            if detected_count > expected_count:
                fp += detected_count - expected_count

            # False negatives: expected more than detected
            if expected_count > detected_count:
                fn += expected_count - detected_count

        # Calculate precision, recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return ElementScores(
            precision=precision,
            recall=recall,
            f1_score=f1,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
        )

    def _calculate_single_type_scores(
        self, detected_count: int, expected_count: int
    ) -> ElementScores:
        """Calculate scores for a single element type.

        Args:
            detected_count: Number of elements detected
            expected_count: Number of elements expected

        Returns:
            ElementScores for this type
        """
        tp = min(detected_count, expected_count)
        fp = max(0, detected_count - expected_count)
        fn = max(0, expected_count - detected_count)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return ElementScores(
            precision=precision,
            recall=recall,
            f1_score=f1,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
        )
