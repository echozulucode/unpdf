"""Run conversion on all test case PDFs with debug output.

This script processes all PDF test cases in tests/test_cases/ and generates:
- {test_case}_output.md - The converted markdown output
- {test_case}_debug.txt - Structured debug info showing PDF structure

These files are automatically ignored by .gitignore and will be regenerated
each time this script runs.

Usage:
    python run_test_cases.py

The script will process all test cases and display a summary at the end.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from unpdf import convert_pdf
from unpdf.debug.structure_dumper import dump_pdf_structure

# Test cases to process
TEST_CASES = [
    "01_basic_text",
    "02_text_formatting",
    "03_lists",
    "04_code_blocks",
    "05_tables",
    "06_links_and_quotes",
    "07_headings",
    "08_horizontal_rules",
    "09_complex_document",
    "10_advanced_tables",
]

def main():
    """Process all test cases."""
    test_cases_dir = Path("tests/test_cases")
    results = []
    
    for test_case in TEST_CASES:
        print(f"\n{'='*60}")
        print(f"Processing: {test_case}")
        print('='*60)
        
        pdf_path = test_cases_dir / f"{test_case}.pdf"
        output_path = test_cases_dir / f"{test_case}_output.md"
        debug_path = test_cases_dir / f"{test_case}_debug.txt"
        
        if not pdf_path.exists():
            print(f"PDF not found: {pdf_path}")
            results.append(f"{test_case}: PDF NOT FOUND")
            continue
        
        try:
            # Convert PDF
            print(f"Converting {pdf_path}...")
            result = convert_pdf(str(pdf_path))
            
            # Save conversion output
            output_path.write_text(result, encoding='utf-8')
            
            # Generate structured debug output
            print(f"Generating debug structure...")
            debug_output = dump_pdf_structure(pdf_path)
            debug_path.write_text(debug_output, encoding='utf-8')
            
            print(f"SUCCESS: {len(result)} characters")
            print(f"  Output: {output_path}")
            print(f"  Debug: {debug_path}")
            results.append(f"{test_case}: SUCCESS ({len(result)} chars)")
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append(f"{test_case}: ERROR - {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for result in results:
        print(result)

if __name__ == "__main__":
    main()
