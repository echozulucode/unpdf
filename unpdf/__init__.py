"""unpdf: Simple, MIT-licensed PDF-to-Markdown converter.

unpdf is a transparent, rule-based PDF-to-Markdown converter focused on
simplicity and predictability. Unlike complex ML-based tools, unpdf uses
straightforward heuristics to convert common document types (documentation,
business reports, technical content) with excellent quality.

Typical usage:
    from unpdf import convert_pdf

    # Simple conversion
    markdown = convert_pdf("document.pdf")

    # With options
    markdown = convert_pdf(
        "document.pdf",
        output_path="output.md",
        detect_code_blocks=True
    )

Modules:
    core: Main conversion pipeline orchestration.
    extractors: PDF content extraction (text, tables, images).
    processors: Content classification (headings, lists, code).
    renderers: Output generation (Markdown, HTML).
    cli: Command-line interface.
"""

__version__ = "0.1.0"
__author__ = "unpdf contributors"
__license__ = "MIT"

from unpdf.core import convert_pdf

__all__ = ["convert_pdf", "__version__"]
