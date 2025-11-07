"""Debug utilities for unpdf.

This package provides tools for debugging PDF conversion issues by
exposing the internal structure and element properties of PDF files.
"""

from unpdf.debug.structure_dumper import dump_pdf_structure

__all__ = ["dump_pdf_structure"]

