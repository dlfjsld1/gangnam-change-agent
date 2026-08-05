from collections.abc import Callable
from io import BytesIO
import re

from pypdf import PdfReader
import pypdfium2 as pdfium

from app.schemas.pdf_extraction import PdfDocumentExtraction, PdfPageExtraction


MINIMUM_MEANINGFUL_PAGE_CHARACTERS = 40
PDF_RENDER_SCALE = 2

ImageOcr = Callable[[bytes], str]
PageRenderer = Callable[[bytes, int], bytes]


class PdfOcrRequiredError(ValueError):
    pass


def extract_pdf_document(
    content: bytes,
    *,
    image_ocr: ImageOcr | None = None,
    page_renderer: PageRenderer | None = None,
) -> PdfDocumentExtraction:
    reader = PdfReader(BytesIO(content))
    if not reader.pages:
        raise ValueError("PDF document has no pages")

    render_page = page_renderer or render_pdf_page
    pages: list[PdfPageExtraction] = []
    for page_index, page in enumerate(reader.pages):
        local_text = _clean_text(page.extract_text() or "")
        if (
            _meaningful_character_count(local_text)
            >= MINIMUM_MEANINGFUL_PAGE_CHARACTERS
        ):
            pages.append(
                PdfPageExtraction(
                    page_number=page_index + 1,
                    method="local_text",
                    text=local_text,
                )
            )
            continue

        if image_ocr is None:
            raise PdfOcrRequiredError(f"PDF page {page_index + 1} requires image OCR")
        ocr_text = _clean_text(image_ocr(render_page(content, page_index)))
        if not ocr_text:
            raise ValueError(f"OCR returned no text for PDF page {page_index + 1}")
        pages.append(
            PdfPageExtraction(
                page_number=page_index + 1,
                method="openai_ocr",
                text=ocr_text,
            )
        )

    methods = {page.method for page in pages}
    document_mode = (
        "text"
        if methods == {"local_text"}
        else "scanned"
        if methods == {"openai_ocr"}
        else "mixed"
    )
    return PdfDocumentExtraction(
        document_mode=document_mode,
        pages=pages,
        text="\n".join(page.text for page in pages),
    )


def render_pdf_page(content: bytes, page_index: int) -> bytes:
    document = pdfium.PdfDocument(content)
    page = document[page_index]
    bitmap = page.render(scale=PDF_RENDER_SCALE)
    image = bitmap.to_pil()
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _meaningful_character_count(value: str) -> int:
    return len(re.findall(r"[0-9A-Za-z가-힣]", value))


def _clean_text(value: str) -> str:
    return " ".join(value.split())
