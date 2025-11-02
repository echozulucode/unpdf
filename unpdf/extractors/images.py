"""Extract images from PDF documents."""

import hashlib
from pathlib import Path

import pdfplumber


class ImageInfo:
    """Information about an extracted image."""

    def __init__(  # noqa: D107
        self,
        image_id: str,
        page_num: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        width: int,
        height: int,
        image_data: bytes,
        ext: str = "png",
    ):
        self.image_id = image_id
        self.page_num = page_num
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.width = width
        self.height = height
        self.image_data = image_data
        self.ext = ext
        self.filename = f"{image_id}.{ext}"


def extract_images(pdf_path: str, output_dir: str | None = None) -> list[ImageInfo]:
    """Extract all images from a PDF file.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images (if None, images are not saved)

    Returns:
        List of ImageInfo objects containing image metadata and data
    """
    images = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_images = page.images
            for img_idx, img in enumerate(page_images):
                # Extract image bounds
                x0 = img.get("x0", 0)
                y0 = img.get("y0", 0)
                x1 = img.get("x1", 0)
                y1 = img.get("y1", 0)

                # Get image dimensions
                width = int(img.get("width", 0))
                height = int(img.get("height", 0))

                # Generate unique image ID based on page and position
                image_hash = hashlib.md5(
                    f"{page_num}_{img_idx}_{x0}_{y0}".encode()
                ).hexdigest()[:8]
                image_id = f"image_p{page_num}_{image_hash}"

                # Try to extract the actual image data
                try:
                    # Get the image object from the page
                    img_obj = page.crop((x0, y0, x1, y1)).to_image()
                    image_data = img_obj.original.tobytes()
                    ext = "png"
                except Exception:
                    # If extraction fails, create a placeholder
                    image_data = b""
                    ext = "png"

                image_info = ImageInfo(
                    image_id=image_id,
                    page_num=page_num,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    width=width,
                    height=height,
                    image_data=image_data,
                    ext=ext,
                )

                images.append(image_info)

                # Save image if output directory is provided
                if output_dir and image_data:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    image_file = output_path / image_info.filename
                    image_file.write_bytes(image_data)

    return images


def detect_image_caption(page, image_info: ImageInfo) -> str | None:  # type: ignore[no-untyped-def]
    """Detect caption text near an image.

    Args:
        page: pdfplumber page object
        image_info: ImageInfo object for the image

    Returns:
        Caption text if found, None otherwise
    """
    # Look for text below the image within a reasonable distance
    caption_region_height = 50
    caption_bbox = (
        image_info.x0,
        image_info.y1,
        image_info.x1,
        image_info.y1 + caption_region_height,
    )

    try:
        caption_crop = page.crop(caption_bbox)
        caption_text: str | None = caption_crop.extract_text()

        if caption_text:
            # Clean up the caption
            caption_text = caption_text.strip()
            # Only return if it looks like a caption (reasonable length)
            if len(caption_text) > 0 and len(caption_text) < 200:
                return caption_text
    except Exception:
        pass

    return None
