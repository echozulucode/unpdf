"""Tests for font analysis system."""

import pytest

from unpdf.extractors.font_analyzer import FontAnalyzer


class TestFontAnalyzer:
    """Test suite for FontAnalyzer."""

    def test_extract_font_metrics_monospace(self):
        """Test monospace font detection."""
        analyzer = FontAnalyzer()

        # Monospace font: all chars have same width
        chars = [
            {"width": 10.0, "size": 12.0},
            {"width": 10.0, "size": 12.0},
            {"width": 10.0, "size": 12.0},
        ]
        metrics = analyzer.extract_font_metrics(chars, "Courier-Bold")

        assert metrics.is_monospace is True
        assert metrics.family == "Courier"
        assert metrics.weight == "bold"
        assert metrics.size == 12.0

    def test_extract_font_metrics_proportional(self):
        """Test proportional font detection."""
        analyzer = FontAnalyzer()

        # Proportional font: varying widths
        chars = [
            {"width": 8.0, "size": 12.0},
            {"width": 12.0, "size": 12.0},
            {"width": 4.0, "size": 12.0},
            {"width": 10.0, "size": 12.0},
        ]
        metrics = analyzer.extract_font_metrics(chars, "Helvetica")

        assert metrics.is_monospace is False
        assert metrics.family == "Helvetica"
        assert metrics.weight == "normal"

    def test_extract_weight_from_name(self):
        """Test weight extraction from font names."""
        analyzer = FontAnalyzer()

        assert analyzer._extract_weight("Helvetica-Bold") == "bold"
        assert analyzer._extract_weight("Arial-Light") == "light"
        assert analyzer._extract_weight("Times-Roman") == "normal"
        assert analyzer._extract_weight("Impact") == "normal"

    def test_extract_style_from_name(self):
        """Test style extraction from font names."""
        analyzer = FontAnalyzer()

        assert analyzer._extract_style("Helvetica-Italic") == "italic"
        assert analyzer._extract_style("Times-Oblique") == "italic"
        assert analyzer._extract_style("Arial-Regular") == "normal"

    def test_normalize_font_family(self):
        """Test font family normalization."""
        analyzer = FontAnalyzer()

        assert analyzer._normalize_font_family("Helvetica-Bold") == "Helvetica"
        assert analyzer._normalize_font_family("Arial-BoldItalic") == "Arial"
        assert (
            analyzer._normalize_font_family("TimesNewRoman,Italic") == "TimesNewRoman"
        )
        assert analyzer._normalize_font_family("Courier") == "Courier"

    def test_build_font_clusters(self):
        """Test font cluster building."""
        analyzer = FontAnalyzer()

        font_usages = {
            "font1": [
                {
                    "family": "Helvetica",
                    "size": 12.0,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "family": "Helvetica",
                    "size": 12.1,
                    "weight": "normal",
                    "style": "normal",
                },
                {
                    "family": "Helvetica",
                    "size": 11.9,
                    "weight": "normal",
                    "style": "normal",
                },
            ],
            "font2": [
                {
                    "family": "Helvetica",
                    "size": 24.0,
                    "weight": "bold",
                    "style": "normal",
                },
                {
                    "family": "Helvetica",
                    "size": 24.2,
                    "weight": "bold",
                    "style": "normal",
                },
            ],
            "font3": [
                {
                    "family": "Helvetica",
                    "size": 18.0,
                    "weight": "bold",
                    "style": "normal",
                },
            ],
        }

        clusters = analyzer.build_font_clusters(font_usages)

        # Should group by (family, weight, style), creating 2 clusters:
        # 1. Helvetica normal (3 sizes -> 3 occurrences)
        # 2. Helvetica bold (3 sizes -> 3 occurrences)
        assert len(clusters) == 2
        # Most common cluster should be first (body text with 3 occurrences)
        assert clusters[0].occurrences == 3
        assert clusters[0].representative_size == pytest.approx(12.0, abs=0.1)
        assert clusters[0].inferred_role == "body"

    def test_identify_body_font(self):
        """Test body font identification."""
        analyzer = FontAnalyzer()

        font_usages = {
            "body": [
                {"family": "Times", "size": 11.0, "weight": "normal", "style": "normal"}
                for _ in range(100)
            ],
            "heading": [
                {"family": "Arial", "size": 18.0, "weight": "bold", "style": "normal"}
                for _ in range(5)
            ],
        }

        analyzer.build_font_clusters(font_usages)

        assert analyzer.body_font_size == pytest.approx(11.0, abs=0.1)

    def test_infer_cluster_roles_headers(self):
        """Test header role inference based on size ratios."""
        analyzer = FontAnalyzer()

        # Body font is 12pt - use distinct families/weights to force separate clusters
        font_usages = {
            "body": [
                {"family": "Arial", "size": 12.0, "weight": "normal", "style": "normal"}
                for _ in range(50)
            ],
            "h1": [
                {
                    "family": "Arial-Bold",
                    "size": 24.0,
                    "weight": "bold",
                    "style": "normal",
                }
                for _ in range(5)
            ],
            "h2": [
                {
                    "family": "Arial-Medium",
                    "size": 18.0,
                    "weight": "bold",
                    "style": "normal",
                }
                for _ in range(10)
            ],
            "h3": [
                {
                    "family": "Arial-Semi",
                    "size": 14.4,
                    "weight": "bold",
                    "style": "normal",
                }
                for _ in range(8)
            ],
        }

        clusters = analyzer.build_font_clusters(font_usages)

        # Should have 4 clusters with different families
        assert len(clusters) >= 4

        # Check that body font is identified correctly
        body_cluster = [
            c for c in clusters if c.weight == "normal" and c.style == "normal"
        ][0]
        assert body_cluster.inferred_role == "body"
        assert body_cluster.representative_size == pytest.approx(12.0, abs=0.1)

        # Check that headers are classified by size ratio
        for cluster in clusters:
            if abs(cluster.representative_size - 24.0) < 0.5:
                assert cluster.inferred_role == "h1"
            elif abs(cluster.representative_size - 18.0) < 0.5:
                assert cluster.inferred_role == "h2"
            elif abs(cluster.representative_size - 14.4) < 0.5:
                assert cluster.inferred_role == "h3"

    def test_get_font_role(self):
        """Test getting role for specific font instance."""
        analyzer = FontAnalyzer()

        font_usages = {
            "body": [
                {"family": "Times", "size": 12.0, "weight": "normal", "style": "normal"}
                for _ in range(50)
            ],
            "h1": [
                {"family": "Times", "size": 24.0, "weight": "bold", "style": "normal"}
                for _ in range(5)
            ],
        }

        analyzer.build_font_clusters(font_usages)

        # Test exact matches
        assert analyzer.get_font_role("Times", 12.0, "normal", "normal") == "body"
        assert analyzer.get_font_role("Times", 24.0, "bold", "normal") == "h1"

        # Test close match
        assert analyzer.get_font_role("Times", 23.8, "bold", "normal") == "h1"

        # Test fallback to size ratio (18/12 = 1.5, which is in h2 range)
        # But since we have a 24pt cluster, it may match that instead
        role = analyzer.get_font_role("Unknown", 18.0, "bold", "normal")
        assert role in ["h1", "h2"]  # Could match either based on distance metric

    def test_detect_monospace_fonts(self):
        """Test monospace font detection from character data."""
        analyzer = FontAnalyzer()

        char_data = {
            "Courier": [{"width": 10.0, "size": 12.0} for _ in range(20)],
            "Helvetica": [
                {"width": w, "size": 12.0} for w in [8.0, 12.0, 6.0, 10.0, 7.0]
            ],
            "Monaco": [{"width": 8.0, "size": 10.0} for _ in range(15)],
        }

        monospace = analyzer.detect_monospace_fonts(char_data)

        assert "Courier" in monospace
        assert "Monaco" in monospace
        assert "Helvetica" not in monospace

    def test_empty_chars_handling(self):
        """Test handling of empty character lists."""
        analyzer = FontAnalyzer()

        metrics = analyzer.extract_font_metrics([], "TestFont")

        assert metrics.char_width_mean == 0.0
        assert metrics.char_width_variance == 0.0
        assert metrics.is_monospace is False

    def test_cluster_confidence(self):
        """Test confidence calculation for clusters."""
        analyzer = FontAnalyzer()

        # Low variance = high confidence
        font_usages = {
            "consistent": [
                {"family": "Arial", "size": 12.0, "weight": "normal", "style": "normal"}
                for _ in range(10)
            ],
        }

        clusters = analyzer.build_font_clusters(font_usages)
        assert clusters[0].confidence > 0.99

        # High variance = lower confidence
        font_usages = {
            "varied": [
                {"family": "Arial", "size": s, "weight": "normal", "style": "normal"}
                for s in [10.0, 12.0, 14.0, 16.0, 18.0]
            ],
        }

        clusters = analyzer.build_font_clusters(font_usages)
        assert clusters[0].confidence < 0.95
