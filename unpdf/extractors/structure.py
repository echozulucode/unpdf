"""Tagged PDF structure extraction.

This module extracts semantic structure from Tagged PDFs (PDF/UA compliant).
Tagged PDFs contain a structure tree that describes document hierarchy
(headings, paragraphs, lists, tables, etc.) independent of visual layout.

Reference: ISO 14289 (PDF/UA) specification
"""

import logging
from dataclasses import dataclass
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class StructureElement:
    """Represents a node in the PDF structure tree.

    Attributes:
        element_type: Structure type (e.g., H1, P, Table, L)
        mcid: Marked Content ID linking to actual content
        alt_text: Alternative text for accessibility
        actual_text: Actual text replacement
        attributes: Additional attributes from the structure
        children: Child structure elements
        page_number: Page where this element appears (0-indexed)
    """

    element_type: str
    mcid: int | None = None
    alt_text: str | None = None
    actual_text: str | None = None
    attributes: dict[str, Any] | None = None
    children: list["StructureElement"] | None = None
    page_number: int | None = None


class TaggedPDFExtractor:
    """Extracts semantic structure from Tagged PDFs."""

    def __init__(self, pdf_path: str):
        """Initialize the extractor.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(pdf_path)

    def is_tagged(self) -> bool:
        """Check if the PDF contains a structure tree.

        Returns:
            True if PDF has structure tree (is tagged), False otherwise
        """
        try:
            # Access the underlying PDF document
            pdf_doc = self.pdf.pdf
            if hasattr(pdf_doc, "catalog"):
                catalog = pdf_doc.catalog
                # Check for StructTreeRoot in catalog
                struct_tree = catalog.get("StructTreeRoot")
                return struct_tree is not None
            return False
        except Exception as e:
            logger.debug(f"Error checking if PDF is tagged: {e}")
            return False

    def extract_structure_tree(self) -> list[StructureElement]:
        """Extract the complete structure tree from the PDF.

        Returns:
            List of root structure elements. Empty if PDF is not tagged.
        """
        if not self.is_tagged():
            logger.info("PDF is not tagged, skipping structure extraction")
            return []

        try:
            pdf_doc = self.pdf.pdf
            catalog = pdf_doc.catalog
            struct_tree_root = catalog.get("StructTreeRoot")

            if struct_tree_root is None:
                return []

            # Parse RoleMap if present (maps custom tags to standard types)
            role_map = {}
            if "RoleMap" in struct_tree_root:
                role_map_obj = struct_tree_root["RoleMap"]
                if hasattr(role_map_obj, "items"):
                    role_map = {k: str(v) for k, v in role_map_obj.items()}

            # Get the root structure elements (K entry)
            k_entry = struct_tree_root.get("K")
            if k_entry is None:
                return []

            # K can be a single dict or an array
            root_elements = [k_entry] if not isinstance(k_entry, list) else k_entry

            # Parse each root element
            structures = []
            for elem in root_elements:
                parsed = self._parse_structure_element(elem, role_map)
                if parsed:
                    structures.append(parsed)

            return structures

        except Exception as e:
            logger.error(f"Error extracting structure tree: {e}")
            return []

    def _parse_structure_element(
        self, elem: Any, role_map: dict[str, str], page_number: int | None = None
    ) -> StructureElement | None:
        """Recursively parse a structure element.

        Args:
            elem: PDF structure element object
            role_map: Mapping of custom tags to standard types
            page_number: Current page number (0-indexed)

        Returns:
            Parsed StructureElement or None if parsing fails
        """
        try:
            # Get element type (S entry)
            elem_type = elem.get("S")
            if elem_type is None:
                return None

            elem_type_str = str(elem_type).lstrip("/")

            # Map custom types to standard types using RoleMap
            if elem_type_str in role_map:
                elem_type_str = role_map[elem_type_str].lstrip("/")

            # Get MCID (Marked Content ID)
            mcid = elem.get("MCID")

            # Get alternative text
            alt_text = elem.get("Alt")
            if alt_text and isinstance(alt_text, bytes):
                alt_text = alt_text.decode("utf-8", errors="ignore")
            elif alt_text:
                alt_text = str(alt_text)

            # Get actual text
            actual_text = elem.get("ActualText")
            if actual_text and isinstance(actual_text, bytes):
                actual_text = actual_text.decode("utf-8", errors="ignore")
            elif actual_text:
                actual_text = str(actual_text)

            # Get page reference if available
            pg = elem.get("Pg")
            if pg and hasattr(self.pdf, "pages"):
                # Page number tracking would require more complex resolution
                pass

            # Parse children (K entry)
            children = []
            k_entry = elem.get("K")
            if k_entry is not None:
                # K can be: MCID (int), single dict, or array
                if isinstance(k_entry, int):
                    mcid = k_entry
                elif isinstance(k_entry, list):
                    for child in k_entry:
                        if isinstance(child, int):
                            mcid = child
                        elif isinstance(child, dict) or hasattr(child, "get"):
                            parsed_child = self._parse_structure_element(
                                child, role_map, page_number
                            )
                            if parsed_child:
                                children.append(parsed_child)
                elif isinstance(k_entry, dict) or hasattr(k_entry, "get"):
                    parsed_child = self._parse_structure_element(
                        k_entry, role_map, page_number
                    )
                    if parsed_child:
                        children.append(parsed_child)

            # Get attributes
            attributes = {}
            if "A" in elem:
                attr_obj = elem["A"]
                if hasattr(attr_obj, "items"):
                    attributes = {k: str(v) for k, v in attr_obj.items()}

            return StructureElement(
                element_type=elem_type_str,
                mcid=mcid,
                alt_text=alt_text,
                actual_text=actual_text,
                attributes=attributes or None,
                children=children if children else None,
                page_number=page_number,
            )

        except Exception as e:
            logger.debug(f"Error parsing structure element: {e}")
            return None

    def get_structure_summary(self) -> dict[str, int]:
        """Get a summary of structure element types in the PDF.

        Returns:
            Dictionary mapping element types to their counts
        """
        structure_tree = self.extract_structure_tree()
        summary: dict[str, int] = {}

        def count_elements(elem: StructureElement) -> None:
            summary[elem.element_type] = summary.get(elem.element_type, 0) + 1
            if elem.children:
                for child in elem.children:
                    count_elements(child)

        for elem in structure_tree:
            count_elements(elem)

        return summary
