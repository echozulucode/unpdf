"""Command-line interface for unpdf.

Provides a simple CLI for converting PDF files to Markdown.

Usage:
    unpdf document.pdf
    unpdf input.pdf -o output.md
    unpdf docs/ --recursive
"""

import argparse
import logging
import sys
from pathlib import Path

from unpdf import __version__, convert_pdf

logger = logging.getLogger(__name__)


def parse_page_spec(spec: str) -> list[int]:
    """Parse page specification string into list of page numbers.

    Args:
        spec: Page specification (e.g., '1', '1-3', '1,3,5-7').

    Returns:
        List of page numbers (1-indexed).

    Raises:
        ValueError: If specification is invalid.

    Examples:
        >>> parse_page_spec('1')
        [1]
        >>> parse_page_spec('1-3')
        [1, 2, 3]
        >>> parse_page_spec('1,3,5-7')
        [1, 3, 5, 6, 7]
    """
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            try:
                start_num = int(start.strip())
                end_num = int(end.strip())
                if start_num < 1 or end_num < 1:
                    raise ValueError("Page numbers must be >= 1")
                if start_num > end_num:
                    raise ValueError(f"Invalid range: {start_num}-{end_num}")
                pages.extend(range(start_num, end_num + 1))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid page range: {part}") from e
                raise
        else:
            try:
                page_num = int(part)
                if page_num < 1:
                    raise ValueError("Page numbers must be >= 1")
                pages.append(page_num)
            except ValueError as e:
                if "Page numbers must be >= 1" in str(e):
                    raise
                raise ValueError(f"Invalid page number: {part}") from e
    return sorted(set(pages))  # Remove duplicates and sort


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI.

    Args:
        verbose: If True, sets logging to DEBUG level. Otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = argparse.ArgumentParser(
        prog="unpdf",
        description="Simple, MIT-licensed PDF-to-Markdown converter",
        epilog="For more information: https://github.com/yourusername/unpdf",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="PDF file or directory to convert",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file or directory (default: same name with .md extension)",
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )

    parser.add_argument(
        "--pages",
        type=str,
        help="Specific pages to convert (e.g., '1', '1-3', '1,3,5-7')",
    )

    parser.add_argument(
        "--no-code-blocks",
        action="store_true",
        help="Disable code block detection",
    )

    parser.add_argument(
        "--heading-ratio",
        type=float,
        default=1.3,
        help="Font size ratio for heading detection (default: 1.3)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"unpdf {__version__}",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Parse page specification if provided
    page_numbers = None
    if args.pages:
        try:
            page_numbers = parse_page_spec(args.pages)
        except ValueError as e:
            logger.error(f"Invalid page specification: {e}")
            return 1

    try:
        # Single file
        if args.input.is_file():
            output_path = args.output or args.input.with_suffix(".md")
            logger.info(f"Converting: {args.input}")

            convert_pdf(
                args.input,
                output_path=output_path,
                detect_code_blocks=not args.no_code_blocks,
                heading_font_ratio=args.heading_ratio,
                page_numbers=page_numbers,
            )

            logger.info(f"✓ Converted: {output_path}")
            return 0

        # Directory
        elif args.input.is_dir():
            pattern = "**/*.pdf" if args.recursive else "*.pdf"
            pdf_files = list(args.input.glob(pattern))

            if not pdf_files:
                logger.error(f"No PDF files found in: {args.input}")
                return 1

            logger.info(f"Found {len(pdf_files)} PDF file(s)")

            output_dir = args.output or args.input
            success_count = 0
            error_count = 0

            for pdf_file in pdf_files:
                try:
                    # Preserve relative path structure
                    relative = pdf_file.relative_to(args.input)
                    output_path = output_dir / relative.with_suffix(".md")

                    logger.info(f"Converting: {pdf_file.name}")
                    convert_pdf(
                        pdf_file,
                        output_path=output_path,
                        detect_code_blocks=not args.no_code_blocks,
                        heading_font_ratio=args.heading_ratio,
                        page_numbers=page_numbers,
                    )
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to convert {pdf_file.name}: {e}")
                    error_count += 1

            logger.info(
                f"✓ Converted {success_count}/{len(pdf_files)} files "
                f"({error_count} errors)"
            )
            return 0 if error_count == 0 else 1

        else:
            logger.error(f"Input not found: {args.input}")
            return 1

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except ValueError as e:
        logger.error(str(e))
        return 1
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
