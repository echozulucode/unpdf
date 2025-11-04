"""Collect baseline conversion metrics for test PDFs.

This script runs the current unpdf converter on a test suite and collects
metrics for comparison against future improvements.
"""

import argparse
import json
import time
from pathlib import Path

from unpdf import convert_pdf
from unpdf.extractors.structure import TaggedPDFExtractor


def collect_metrics_for_pdf(pdf_path: Path) -> dict:
    """Collect metrics for a single PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary of metrics
    """
    metrics = {
        "file": str(pdf_path),
        "file_size_bytes": pdf_path.stat().st_size,
    }

    try:
        # Check if tagged
        extractor = TaggedPDFExtractor(str(pdf_path))
        metrics["is_tagged"] = extractor.is_tagged()

        if metrics["is_tagged"]:
            structure_summary = extractor.get_structure_summary()
            metrics["structure_elements"] = structure_summary
        else:
            metrics["structure_elements"] = {}

        # Convert and measure time
        start_time = time.time()
        markdown = convert_pdf(str(pdf_path))
        conversion_time = time.time() - start_time

        metrics["conversion_time_seconds"] = round(conversion_time, 3)
        metrics["output_length_chars"] = len(markdown)
        metrics["output_lines"] = len(markdown.splitlines())

        # Count markdown elements
        lines = markdown.splitlines()
        metrics["markdown_elements"] = {
            "headers": sum(1 for line in lines if line.strip().startswith("#")),
            "lists": sum(
                1
                for line in lines
                if line.strip().startswith(("-", "*", "+"))
                or (
                    len(line.strip()) > 0
                    and line.strip()[0].isdigit()
                    and "." in line[:10]
                )
            ),
            "code_blocks": markdown.count("```"),
            "tables": markdown.count("|"),
            "blockquotes": sum(1 for line in lines if line.strip().startswith(">")),
        }

        metrics["success"] = True
        metrics["error"] = None

    except Exception as e:
        metrics["success"] = False
        metrics["error"] = str(e)
        metrics["conversion_time_seconds"] = None
        metrics["output_length_chars"] = 0
        metrics["markdown_elements"] = {}

    return metrics


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect baseline metrics")
    parser.add_argument(
        "pdf_dir",
        type=Path,
        help="Directory containing PDFs to test",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("baseline_metrics.json"),
        help="Output JSON file",
    )

    args = parser.parse_args()

    if not args.pdf_dir.exists():
        print(f"Error: Directory {args.pdf_dir} does not exist")
        return 1

    # Find all PDFs
    pdf_files = list(args.pdf_dir.rglob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {args.pdf_dir}")
        return 1

    print(f"Found {len(pdf_files)} PDF files")
    print("Collecting metrics...\n")

    all_metrics = []
    for pdf_path in sorted(pdf_files):
        print(f"Processing {pdf_path.name}...")
        metrics = collect_metrics_for_pdf(pdf_path)
        all_metrics.append(metrics)

        if metrics["success"]:
            print(f"  ✓ Converted in {metrics['conversion_time_seconds']}s")
            print(f"    Tagged: {metrics['is_tagged']}")
            print(f"    Output: {metrics['output_length_chars']} chars")
        else:
            print(f"  ✗ Error: {metrics['error']}")
        print()

    # Save results
    output_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_pdfs": len(pdf_files),
        "successful": sum(1 for m in all_metrics if m["success"]),
        "failed": sum(1 for m in all_metrics if not m["success"]),
        "metrics": all_metrics,
    }

    args.output.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    print(f"Metrics saved to {args.output}")

    # Print summary
    print("\n=== Summary ===")
    print(f"Total PDFs: {output_data['total_pdfs']}")
    print(f"Successful: {output_data['successful']}")
    print(f"Failed: {output_data['failed']}")

    tagged_count = sum(1 for m in all_metrics if m.get("is_tagged"))
    print(f"Tagged PDFs: {tagged_count}")

    if output_data["successful"] > 0:
        avg_time = (
            sum(
                m["conversion_time_seconds"]
                for m in all_metrics
                if m["success"] and m["conversion_time_seconds"]
            )
            / output_data["successful"]
        )
        print(f"Average conversion time: {avg_time:.3f}s")

    return 0


if __name__ == "__main__":
    exit(main())
