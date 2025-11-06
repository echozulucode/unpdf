#!/usr/bin/env python
"""Test accuracy on all test case PDFs and generate report."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unpdf.accuracy.element_detector import ElementDetector
from unpdf.accuracy.element_scorer import ElementScorer
from unpdf import convert_pdf

# Test cases directory
TEST_CASES_DIR = Path(__file__).parent.parent / "tests" / "test_cases"

# Test case definitions
TEST_CASES = [
    {"name": "01_basic_text", "desc": "Basic text paragraphs"},
    {"name": "02_text_formatting", "desc": "Bold, italic, and formatting"},
    {"name": "03_lists", "desc": "Ordered and unordered lists"},
    {"name": "04_code_blocks", "desc": "Code blocks and inline code"},
    {"name": "05_tables", "desc": "Basic tables"},
    {"name": "06_links_and_quotes", "desc": "Links and blockquotes"},
    {"name": "07_headings", "desc": "Heading hierarchy"},
    {"name": "08_horizontal_rules", "desc": "Horizontal rules"},
    {"name": "09_complex_document", "desc": "Complex mixed content"},
    {"name": "10_advanced_tables", "desc": "Advanced table layouts"},
]


def main():
    """Run accuracy tests on all test cases."""
    print("=" * 80)
    print("PDF to Markdown Conversion Accuracy Report")
    print("=" * 80)
    print()

    all_results = []

    for test_case in TEST_CASES:
        name = test_case["name"]
        desc = test_case["desc"]
        
        md_path = TEST_CASES_DIR / f"{name}.md"
        pdf_path = TEST_CASES_DIR / f"{name}.pdf"
        
        # Check if files exist
        if not md_path.exists():
            print(f"WARNING: {name}: Source markdown not found")
            continue
        if not pdf_path.exists():
            print(f"WARNING: {name}: PDF not found")
            continue
        
        # Read reference markdown
        with open(md_path, "r", encoding="utf-8") as f:
            reference_md = f.read()
        
        # Convert PDF to markdown
        try:
            output_md = convert_pdf(str(pdf_path))
        except Exception as e:
            print(f"ERROR: {name}: Conversion failed - {e}")
            continue
        
        # Detect elements
        detector = ElementDetector()
        ref_elements = detector.detect(reference_md)
        output_elements = detector.detect(output_md)
        
        # Score
        scorer = ElementScorer()
        score = scorer.calculate_scores(ref_elements, output_elements)
        
        # Store result
        all_results.append({
            "name": name,
            "desc": desc,
            "score": score,
            "ref_elements": ref_elements,
            "output_elements": output_elements,
        })
        
        # Print result
        print(f"[{name}]")
        print(f"   {desc}")
        print(f"   Overall Score: {score.overall.accuracy_percentage:.1f}%")
        print(f"   Precision: {score.overall.precision * 100:.1f}%")
        print(f"   Recall: {score.overall.recall * 100:.1f}%")
        print(f"   F1 Score: {score.overall.f1_score * 100:.1f}%")
        
        # Print element-level scores
        if score.by_type:
            print(f"   Element Scores:")
            for elem_type, type_score in sorted(score.by_type.items(), key=lambda x: x[0].value):
                if type_score.true_positives > 0 or type_score.false_positives > 0 or type_score.false_negatives > 0:
                    print(f"      {elem_type.value}: {type_score.accuracy_percentage:.1f}%")
        
        print()
    
    # Summary
    if all_results:
        print("=" * 80)
        print("Summary")
        print("=" * 80)
        avg_score = sum(r["score"].overall.accuracy_percentage for r in all_results) / len(all_results)
        avg_precision = sum(r["score"].overall.precision * 100 for r in all_results) / len(all_results)
        avg_recall = sum(r["score"].overall.recall * 100 for r in all_results) / len(all_results)
        avg_f1 = sum(r["score"].overall.f1_score * 100 for r in all_results) / len(all_results)
        
        print(f"Average Overall Score: {avg_score:.1f}%")
        print(f"Average Precision: {avg_precision:.1f}%")
        print(f"Average Recall: {avg_recall:.1f}%")
        print(f"Average F1 Score: {avg_f1:.1f}%")
        print()
        
        # Best and worst
        best = max(all_results, key=lambda r: r["score"].overall.accuracy_percentage)
        worst = min(all_results, key=lambda r: r["score"].overall.accuracy_percentage)
        
        print(f"Best Performance: {best['name']} ({best['score'].overall.accuracy_percentage:.1f}%)")
        print(f"Worst Performance: {worst['name']} ({worst['score'].overall.accuracy_percentage:.1f}%)")
        print()


if __name__ == "__main__":
    main()
