"""Extractors for unpdf.

This package contains modules for extracting content from PDF files:
    - text: Text extraction with font metadata
    - tables: Table detection and extraction
    - images: Image extraction and saving

Example:
    from unpdf.extractors.text import extract_text_with_metadata

    spans = extract_text_with_metadata(Path("document.pdf"))
    for span in spans:
        print(f"{span['text']}: {span['font_size']}pt")
"""
