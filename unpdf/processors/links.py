"""Process hyperlinks in PDF documents."""

import re

import pdfplumber


class LinkInfo:
    """Information about a hyperlink."""

    def __init__(  # noqa: D107
        self, text: str, url: str, page_num: int, x0: float, y0: float
    ):
        self.text = text
        self.url = url
        self.page_num = page_num
        self.x0 = x0
        self.y0 = y0


def extract_links(pdf_path: str) -> list[LinkInfo]:
    """Extract hyperlinks from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of LinkInfo objects containing link metadata
    """
    links = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract annotations (URI links)
            if hasattr(page, "annots") and page.annots:
                for annot in page.annots:
                    if annot.get("uri"):
                        url = annot["uri"]
                        # Get the bounding box
                        rect = annot.get("rect", [0, 0, 0, 0])
                        x0, y0 = rect[0], rect[1]

                        # Try to find the text at this location
                        text = _extract_text_at_position(page, rect)

                        if not text:
                            text = url

                        links.append(
                            LinkInfo(
                                text=text,
                                url=url,
                                page_num=page_num,
                                x0=x0,
                                y0=y0,
                            )
                        )

            # Also look for plain text URLs in the content
            text = page.extract_text()
            if text:
                plain_urls = _extract_plain_urls(text)
                for url in plain_urls:
                    links.append(
                        LinkInfo(
                            text=url,
                            url=url,
                            page_num=page_num,
                            x0=0,
                            y0=0,
                        )
                    )

    return links


def _extract_text_at_position(page, rect: list[float]) -> str | None:  # type: ignore[no-untyped-def]
    """Extract text at a specific position on the page.

    Args:
        page: pdfplumber page object
        rect: Bounding box [x0, y0, x1, y1]

    Returns:
        Text at the position, or None if not found
    """
    try:
        x0, y0, x1, y1 = rect
        # Crop to the annotation area
        crop = page.crop((x0, y0, x1, y1))
        text = crop.extract_text()
        return text.strip() if text else None
    except Exception:
        return None


def _extract_plain_urls(text: str) -> list[str]:
    """Extract plain URLs from text using regex.

    Args:
        text: Text to search for URLs

    Returns:
        List of URLs found in the text
    """
    # Regex pattern for URLs
    url_pattern = re.compile(
        r"http[s]?://"
        r"(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )

    urls = url_pattern.findall(text)
    return list(set(urls))  # Remove duplicates


def convert_link_to_markdown(link_info: LinkInfo) -> str:
    """Convert a LinkInfo object to Markdown format.

    Args:
        link_info: LinkInfo object

    Returns:
        Markdown link string
    """
    # Escape special characters in link text
    text = link_info.text.replace("[", "\\[").replace("]", "\\]")

    # If the text is the same as the URL, just use the URL
    if text == link_info.url:
        return f"<{link_info.url}>"

    return f"[{text}]({link_info.url})"
