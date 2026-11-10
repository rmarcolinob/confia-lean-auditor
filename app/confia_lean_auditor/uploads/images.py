"""Uploaded file -> normalized PNG pages. Pillow and pypdfium2 are optional (extra `ocr`)."""
from __future__ import annotations

import io
from dataclasses import dataclass

MAX_SIDE = 1600
MAX_SOURCE_PIXELS = 50_000_000
MAX_PAGES = 3

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
PDF_SIGNATURE = b"%PDF-"


class UnsupportedUpload(ValueError):
    pass


class InvalidUpload(ValueError):
    pass


class UploadDependencyMissing(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedPage:
    source_index: int
    source_media_type: str
    page_in_source: int
    png: bytes
    width: int
    height: int


def media_type(data: bytes) -> str:
    # Trust the bytes, never the declared filename or type.
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    if data.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    if data.startswith(PDF_SIGNATURE):
        return "application/pdf"
    raise UnsupportedUpload("unsupported_media_type")


def _pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        raise UploadDependencyMissing("pillow_missing") from None
    Image.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS
    return Image, ImageOps


def _to_png(image) -> tuple[bytes, int, int]:
    Image, _ = _pillow()
    image = image.convert("RGB")
    if max(image.size) > MAX_SIDE:
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue(), image.width, image.height


def _image_pages(data: bytes, kind: str, source_index: int) -> list[PreparedPage]:
    Image, ImageOps = _pillow()
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        # verify() invalidates the image object, so decode from a fresh handle.
        with Image.open(io.BytesIO(data)) as image:
            png, width, height = _to_png(ImageOps.exif_transpose(image))
    except Image.DecompressionBombError:
        raise InvalidUpload("image_too_large") from None
    except (OSError, ValueError, SyntaxError):
        raise InvalidUpload("invalid_image") from None
    return [PreparedPage(source_index, kind, 0, png, width, height)]


def _pdf_pages(data: bytes, source_index: int, budget: int) -> list[PreparedPage]:
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise UploadDependencyMissing("pypdfium2_missing") from None
    _pillow()
    try:
        document = pdfium.PdfDocument(data)
    except Exception:
        raise InvalidUpload("invalid_pdf") from None
    try:
        if len(document) == 0:
            raise InvalidUpload("empty_pdf")
        if len(document) > budget:
            raise InvalidUpload("too_many_pages")
        pages = []
        for index in range(len(document)):
            page = document[index]
            scale = MAX_SIDE / max(page.get_size())
            png, width, height = _to_png(page.render(scale=scale).to_pil())
            pages.append(PreparedPage(source_index, "application/pdf", index, png, width, height))
        return pages
    finally:
        document.close()


def prepare_pages(files: list[bytes]) -> list[PreparedPage]:
    pages: list[PreparedPage] = []
    for index, data in enumerate(files):
        if not data:
            raise InvalidUpload("empty_file")
        kind = media_type(data)
        budget = MAX_PAGES - len(pages)
        if budget <= 0:
            raise InvalidUpload("too_many_pages")
        if kind == "application/pdf":
            pages += _pdf_pages(data, index, budget)
        else:
            pages += _image_pages(data, kind, index)
    if len(pages) > MAX_PAGES:
        raise InvalidUpload("too_many_pages")
    return pages
