"""Bounded document decoding, without OCR or mathematical dependencies."""
import base64
from contextlib import closing
from io import BytesIO
import math
import threading

from PIL import Image, ImageOps
import pypdfium2 as pdfium

from .exam_models import MAX_DOCUMENT_BYTES, MAX_TOTAL_BYTES, MAX_EXAM_PAGES

# PDFium is not thread-safe, even for different documents.
_pdf_lock = threading.Lock()


class CaptureError(ValueError):
    pass


def png_preview(image):
    image.thumbnail((2048, 2048))
    output = BytesIO()
    image.convert("RGB").save(output, format="PNG")
    return output.getvalue(), image.width, image.height


def prepare(package):
    """Returns original bytes and ordered previews; never replaces an original."""
    originals, pages = [], []
    for doc in package.original_documents:
        try:
            data = base64.b64decode(doc.content_base64, validate=True)
        except ValueError:
            raise CaptureError("Arquivo codificado inválido.") from None
        if not data or len(data) > MAX_DOCUMENT_BYTES:
            raise CaptureError("Cada arquivo deve ter no máximo 20 MiB.")
        originals.append(data)
    if sum(map(len, originals)) > MAX_TOTAL_BYTES:
        raise CaptureError("A prova deve ter no máximo 40 MiB de originais.")
    if package.original_documents[0].media_type == "application/pdf":
        if not originals[0].startswith(b"%PDF-"):
            raise CaptureError("O arquivo não é um PDF válido.")
        with _pdf_lock:
            try:
                with closing(pdfium.PdfDocument(originals[0])) as document:
                    if not 1 <= len(document) <= MAX_EXAM_PAGES:
                        raise CaptureError("O PDF deve conter entre 1 e 50 páginas.")
                    rotation = package.original_documents[0].rotation_degrees
                    for index in range(len(document)):
                        with closing(document[index]) as page:
                            width, height = page.get_size()
                            if not all(math.isfinite(x) and 0 < x <= 20000 for x in (width, height)):
                                raise CaptureError("Dimensões de página inválidas.")
                            with closing(page.render(scale=min(2, 2048 / max(width, height)), rotation=rotation)) as bitmap:
                                with bitmap.to_pil() as image:
                                    preview, w, h = png_preview(image)
                            pages.append((0, index + 1, preview, w, h, rotation,
                                          "pdfium-4-render-png-v1"))
            except CaptureError:
                raise
            except Exception:
                raise CaptureError("Não foi possível abrir o PDF. Confira se está íntegro e sem senha.") from None
    else:
        for index, (doc, data) in enumerate(zip(package.original_documents, originals)):
            try:
                with Image.open(BytesIO(data)) as source:
                    if source.format != {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[doc.media_type]:
                        raise CaptureError("O formato informado não corresponde à imagem.")
                    if source.width * source.height > 24_000_000 or getattr(source, "n_frames", 1) != 1:
                        raise CaptureError("Use imagens estáticas de até 24 megapixels.")
                    with ImageOps.exif_transpose(source) as oriented:
                        with oriented.rotate(-doc.rotation_degrees, expand=True) as image:
                            preview, w, h = png_preview(image)
                    pages.append((index, 1, preview, w, h, doc.rotation_degrees,
                                  "pillow-exif-rotate-png-v1"))
            except CaptureError:
                raise
            except Exception:
                raise CaptureError("Imagem inválida. Use JPEG, PNG ou WebP.") from None
    if any(p.page_number > len(pages) for p in package.pages):
        raise CaptureError("Metadados referem-se a uma página inexistente.")
    return originals, pages
