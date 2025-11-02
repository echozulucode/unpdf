"""Processors for unpdf.

This package contains modules for processing and classifying PDF content:
    - headings: Heading detection based on font size
    - lists: List detection (bullets and numbered)
    - code: Code block detection (monospace fonts)
    - blockquotes: Quote detection
    - links: Hyperlink processing

Example:
    from unpdf.processors.headings import HeadingProcessor

    processor = HeadingProcessor(avg_font_size=12.0)
    element = processor.process(text_span)
"""
