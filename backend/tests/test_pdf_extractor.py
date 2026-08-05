from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.tools.pdf_extractor import extract_pdf_document, render_pdf_page


def _pdf_with_pages(page_texts: list[str | None]) -> bytes:
    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)

    for text in page_texts:
        page = writer.add_blank_page(width=612, height=792)
        if text is None:
            continue
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_reference})}
        )
        content = DecodedStreamObject()
        content.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(content)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_text_pdf_uses_only_local_extraction() -> None:
    content = _pdf_with_pages(
        ["Gangnam youth support eligibility is age 19 through 34 and resident status."]
    )

    def unexpected_ocr(_: bytes) -> str:
        raise AssertionError("Text PDF must not call OCR")

    def unexpected_render(_: bytes, __: int) -> bytes:
        raise AssertionError("Text PDF must not render a page")

    result = extract_pdf_document(
        content,
        image_ocr=unexpected_ocr,
        page_renderer=unexpected_render,
    )

    assert result.document_mode == "text"
    assert result.pages[0].method == "local_text"
    assert "age 19 through 34" in result.text


def test_scanned_pdf_renders_and_ocr_only_the_scanned_page() -> None:
    content = _pdf_with_pages([None])
    rendered_pages: list[int] = []

    def render_page(_: bytes, page_index: int) -> bytes:
        rendered_pages.append(page_index)
        return b"\x89PNG scanned page"

    result = extract_pdf_document(
        content,
        image_ocr=lambda _: "스캔 공고 신청 기간은 8월 1일부터입니다.",
        page_renderer=render_page,
    )

    assert result.document_mode == "scanned"
    assert result.pages[0].method == "openai_ocr"
    assert rendered_pages == [0]


def test_mixed_pdf_preserves_page_order_and_methods() -> None:
    content = _pdf_with_pages(
        [
            "This first page contains enough local text for deterministic extraction.",
            None,
        ]
    )

    result = extract_pdf_document(
        content,
        image_ocr=lambda _: "두 번째 페이지 OCR 결과",
        page_renderer=lambda _content, index: f"page-{index}".encode(),
    )

    assert result.document_mode == "mixed"
    assert [page.page_number for page in result.pages] == [1, 2]
    assert [page.method for page in result.pages] == [
        "local_text",
        "openai_ocr",
    ]
    assert result.text.endswith("두 번째 페이지 OCR 결과")


def test_pdf_page_renderer_produces_png_for_openai_input() -> None:
    content = _pdf_with_pages([None])

    rendered = render_pdf_page(content, 0)

    assert rendered.startswith(b"\x89PNG")
