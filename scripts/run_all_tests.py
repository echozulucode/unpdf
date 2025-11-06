"""Run all test cases and generate accuracy reports.

This script processes all test PDF files, converts them to Markdown,
and calculates accuracy scores against the reference Markdown files.

Style: Google docstrings, black formatting
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unpdf.core import convert_pdf
from unpdf.accuracy.element_detector import ElementDetector, ElementType
from unpdf.accuracy.element_scorer import ElementScorer


def run_test(test_number: int, test_name: str) -> dict:
    """Run a single test case and return results.
    
    Args:
        test_number: Test case number (1-10)
        test_name: Name of the test case
        
    Returns:
        Dictionary with test results
    """
    test_dir = Path("tests/test_cases")
    pdf_file = test_dir / f"{test_number:02d}_{test_name}.pdf"
    ref_file = test_dir / f"{test_number:02d}_{test_name}.md"
    output_file = test_dir / f"{test_number:02d}_output.md"
    
    if not pdf_file.exists():
        return {"error": f"PDF not found: {pdf_file}"}
    
    if not ref_file.exists():
        return {"error": f"Reference not found: {ref_file}"}
    
    # Convert PDF
    try:
        convert_pdf(str(pdf_file), str(output_file))
    except Exception as e:
        return {"error": f"Conversion failed: {e}"}
    
    # Read files
    with open(ref_file, "r", encoding="utf-8") as f:
        reference = f.read()
    with open(output_file, "r", encoding="utf-8") as f:
        generated = f.read()
    
    # Calculate accuracy
    detector = ElementDetector()
    scorer = ElementScorer()
    
    ref_elements = detector.detect(reference)
    gen_elements = detector.detect(generated)
    
    ref_counts = len(ref_elements)
    gen_counts = len(gen_elements)
    
    ref_by_type = detector.count_by_type(ref_elements)
    gen_by_type = detector.count_by_type(gen_elements)
    
    accuracy = scorer.calculate_scores(gen_elements, ref_elements)
    
    # Build type scores dict
    type_scores = {}
    for elem_type in ElementType:
        if elem_type in accuracy.by_type:
            type_scores[elem_type.value] = accuracy.by_type[elem_type].accuracy_percentage
        else:
            type_scores[elem_type.value] = 0.0
    
    return {
        "test_number": test_number,
        "test_name": test_name,
        "score": accuracy.overall.accuracy_percentage,
        "ref_total": ref_counts,
        "gen_total": gen_counts,
        "ref_by_type": {k.value: v for k, v in ref_by_type.items()},
        "gen_by_type": {k.value: v for k, v in gen_by_type.items()},
        "type_scores": type_scores,
        "output_file": str(output_file),
    }


def main():
    """Run all tests and print results."""
    tests = [
        (1, "basic_text"),
        (2, "text_formatting"),
        (3, "lists"),
        (4, "code_blocks"),
        (5, "tables"),
        (6, "links_and_quotes"),
        (7, "headings"),
        (8, "horizontal_rules"),
        (9, "complex_document"),
        (10, "advanced_tables"),
    ]
    
    print("=" * 80)
    print("PDF to Markdown Conversion Test Suite")
    print("=" * 80)
    print()
    
    results = []
    for test_num, test_name in tests:
        print(f"Running Test {test_num}: {test_name}...")
        result = run_test(test_num, test_name)
        results.append(result)
        
        if "error" in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Score: {result['score']:.1f}%")
            print(f"    Reference: {result['ref_total']} elements")
            print(f"    Generated: {result['gen_total']} elements")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful_tests = [r for r in results if "error" not in r]
    if successful_tests:
        avg_score = sum(r["score"] for r in successful_tests) / len(successful_tests)
        print(f"Average Score: {avg_score:.1f}%")
        print(f"Tests Passed: {len(successful_tests)}/{len(tests)}")
        print()
        
        # Show failing tests
        failing = [r for r in successful_tests if r["score"] < 80]
        if failing:
            print("Tests Below 80%:")
            for r in failing:
                print(f"  {r['test_number']:02d}. {r['test_name']}: {r['score']:.1f}%")
            print()
        
        # Detailed breakdown
        print("Detailed Breakdown:")
        print(f"{'Test':<25} {'Score':>7} {'Ref':>6} {'Gen':>6}")
        print("-" * 50)
        for r in results:
            if "error" in r:
                print(f"{r.get('test_name', 'Unknown'):<25} {'ERROR':>7}")
            else:
                print(
                    f"{r['test_name']:<25} {r['score']:>6.1f}% "
                    f"{r['ref_total']:>6} {r['gen_total']:>6}"
                )
    else:
        print("No tests completed successfully")
    
    # Save detailed results
    results_file = Path("tests/test_cases/test_results.txt")
    with open(results_file, "w", encoding="utf-8") as f:
        f.write("PDF to Markdown Conversion Test Results\n")
        f.write("=" * 80 + "\n\n")
        
        for r in results:
            if "error" in r:
                f.write(f"Test {r.get('test_number', '?')}: ERROR\n")
                f.write(f"  {r['error']}\n\n")
            else:
                f.write(f"Test {r['test_number']}: {r['test_name']}\n")
                f.write(f"  Overall Score: {r['score']:.1f}%\n")
                f.write(f"  Elements - Ref: {r['ref_total']}, Gen: {r['gen_total']}\n")
                f.write(f"  Output: {r['output_file']}\n")
                f.write(f"\n  Element Breakdown:\n")
                for elem_type, score in r['type_scores'].items():
                    ref_count = r['ref_by_type'].get(elem_type, 0)
                    gen_count = r['gen_by_type'].get(elem_type, 0)
                    f.write(
                        f"    {elem_type:20s}: {score:>5.1f}% "
                        f"(Ref: {ref_count:3d}, Gen: {gen_count:3d})\n"
                    )
                f.write("\n")
    
    print(f"\nDetailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
