from io import BytesIO
from zipfile import ZipFile

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.schemas.source_notice import SourceAttachment, SourceNotice
from app.tools.document_extractor import (
    ScraplingAttachmentDownloader,
    extract_hwpx_text,
    extract_notice_corpus,
    extract_pdf_text,
)


class FakeDownloader:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []

    def fetch_bytes(self, attachment_url: str) -> bytes:
        self.requested_urls.append(attachment_url)
        if attachment_url.endswith(".pdf"):
            return b"%PDF fake test payload"
        if attachment_url.endswith(".hwpx"):
            return b"PK\x03\x04 fake test payload"
        if attachment_url.endswith(".png"):
            return b"\x89PNG fake test payload"
        return attachment_url.encode()


def _notice(attachments: list[SourceAttachment]) -> SourceNotice:
    return SourceNotice(
        source_id="61922",
        source_board="gangnam_public_notice",
        source_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        title="청년 지원 공고",
        published_at="2026-01-08",
        department="일자리정책과",
        body_text="강남구 청년에게 시험 응시료를 지원합니다.",
        attachments=attachments,
    )


def _attachment(filename: str, file_type: str) -> SourceAttachment:
    return SourceAttachment(
        filename=filename,
        file_type=file_type,
        url=f"https://www.gangnam.go.kr/files/{filename}",
    )


def test_local_variants_run_before_required_image_ocr() -> None:
    downloader = FakeDownloader()
    notice = _notice(
        [
            _attachment("공고문.pdf", "pdf"),
            _attachment("공고문.hwpx", "hwpx"),
            _attachment("공고문.png", "image"),
        ]
    )
    shared_text = "지원 대상은 강남구 거주 청년이며 최대 이십만원을 지원합니다."

    ocr_calls: list[bytes] = []
    corpus = extract_notice_corpus(
        notice,
        downloader,
        image_ocr=lambda content: ocr_calls.append(content) or shared_text,
        extractors={"pdf": lambda _: shared_text, "hwpx": lambda _: shared_text},
    )

    group = corpus.attachment_groups[0]
    assert downloader.requested_urls == [
        "https://www.gangnam.go.kr/files/공고문.pdf",
        "https://www.gangnam.go.kr/files/공고문.hwpx",
        "https://www.gangnam.go.kr/files/공고문.png",
    ]
    assert len(ocr_calls) == 1
    assert [result.status for result in group.extractions] == [
        "succeeded",
        "succeeded",
        "succeeded",
    ]
    assert group.representative_filename == "공고문.pdf"
    assert group.review_required is False


def test_image_ocr_runs_when_no_local_evidence_exists() -> None:
    notice = _notice([_attachment("안내.png", "image")])

    corpus = extract_notice_corpus(
        notice,
        FakeDownloader(),
        image_ocr=lambda _: "신청 대상은 강남구 거주 청년입니다.",
    )

    result = corpus.attachment_groups[0].extractions[0]
    assert result.status == "succeeded"
    assert result.text == "신청 대상은 강남구 거주 청년입니다."
    assert corpus.review_required is False


def test_image_ocr_runs_before_local_conflict_requests_review() -> None:
    notice = _notice(
        [
            _attachment("모집.pdf", "pdf"),
            _attachment("모집.hwpx", "hwpx"),
            _attachment("모집.png", "image"),
        ]
    )
    ocr_calls: list[bytes] = []

    corpus = extract_notice_corpus(
        notice,
        FakeDownloader(),
        image_ocr=lambda content: ocr_calls.append(content)
        or "신청 기간은 8월 1일부터 8월 10일까지입니다.",
        extractors={
            "pdf": lambda _: "신청 기간은 8월 1일부터 8월 10일까지입니다.",
            "hwpx": lambda _: "접수 기간은 9월 1일부터 9월 30일까지입니다.",
        },
    )

    assert len(ocr_calls) == 1
    assert corpus.attachment_groups[0].review_required is True


def test_variant_conflict_requires_review_without_discarding_results() -> None:
    notice = _notice(
        [
            _attachment("모집.pdf", "pdf"),
            _attachment("모집.hwpx", "hwpx"),
        ]
    )

    corpus = extract_notice_corpus(
        notice,
        FakeDownloader(),
        extractors={
            "pdf": lambda _: "신청 기간은 8월 1일부터 8월 10일까지입니다.",
            "hwpx": lambda _: "접수 기간은 9월 1일부터 9월 30일까지입니다.",
        },
    )

    group = corpus.attachment_groups[0]
    assert group.review_required is True
    assert "일치하지 않음" in group.review_reason
    assert all(result.text for result in group.extractions)


def test_missing_image_ocr_is_recorded_as_review_reason() -> None:
    notice = _notice([_attachment("안내.png", "image")])

    corpus = extract_notice_corpus(notice, FakeDownloader())

    result = corpus.attachment_groups[0].extractions[0]
    assert result.status == "failed"
    assert result.error == "No extractor configured for image"
    assert corpus.review_required is True


def test_hwpx_extractor_reads_text_from_all_sections() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "Contents/section0.xml",
            '<hp:section xmlns:hp="urn:hancom"><hp:t>지원 대상</hp:t></hp:section>',
        )
        archive.writestr(
            "Contents/section1.xml",
            '<hp:section xmlns:hp="urn:hancom"><hp:t>강남구 청년</hp:t></hp:section>',
        )

    assert extract_hwpx_text(buffer.getvalue()) == "지원 대상 강남구 청년"


def test_pdf_extractor_reads_page_text() -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    content = DecodedStreamObject()
    content.set_data(
        b"BT /F1 12 Tf 72 720 Td "
        b"(Eligibility applies to Gangnam residents age 19 to 34 with support.) "
        b"Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(content)
    buffer = BytesIO()
    writer.write(buffer)

    assert extract_pdf_text(buffer.getvalue()) == (
        "Eligibility applies to Gangnam residents age 19 to 34 with support."
    )


def test_attachment_downloader_rejects_unapproved_hosts_before_fetch() -> None:
    with pytest.raises(ValueError, match="Unapproved attachment URL"):
        ScraplingAttachmentDownloader().fetch_bytes(
            "https://example.com/untrusted/document.pdf"
        )
