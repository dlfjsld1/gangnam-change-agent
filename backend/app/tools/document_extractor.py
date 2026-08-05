from collections.abc import Callable, Mapping
from difflib import SequenceMatcher
from io import BytesIO
from pathlib import PurePath
import re
from typing import Protocol
from urllib.parse import urlparse
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from scrapling.fetchers import Fetcher

from app.schemas.document_extraction import (
    AttachmentComparison,
    DocumentExtraction,
    NoticeDocumentCorpus,
)
from app.schemas.source_notice import SourceAttachment, SourceNotice
from app.tools.pdf_extractor import extract_pdf_document


MINIMUM_TEXT_LENGTH = 20
MINIMUM_VARIANT_SIMILARITY = 0.55
SOURCE_PRIORITY = {"pdf": 0, "hwpx": 1, "image": 2, "hwp": 3, "other": 4}
ALLOWED_ATTACHMENT_HOSTS = {
    "gangnam.go.kr",
    "www.gangnam.go.kr",
    "gangnam.eminwon.seoul.kr",
}
BROKEN_CERTIFICATE_CHAIN_HOSTS = {"gangnam.eminwon.seoul.kr"}

TextExtractor = Callable[[bytes], str]


class AttachmentDownloader(Protocol):
    def fetch_bytes(self, attachment_url: str) -> bytes:
        """Download one public attachment."""


class ScraplingAttachmentDownloader:
    def fetch_bytes(self, attachment_url: str) -> bytes:
        parsed_url = urlparse(attachment_url)
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname not in ALLOWED_ATTACHMENT_HOSTS
        ):
            raise ValueError(f"Unapproved attachment URL: {attachment_url}")
        response = Fetcher.get(
            attachment_url,
            timeout=30,
            verify=parsed_url.hostname not in BROKEN_CERTIFICATE_CHAIN_HOSTS,
            headers={
                "User-Agent": (
                    "GangnamChangeAgentMVP/0.1 (+hackathon; public-notice-research)"
                )
            },
        )
        if response.status >= 400:
            raise ValueError(f"Attachment download failed: HTTP {response.status}")
        return response.body


def extract_notice_corpus(
    notice: SourceNotice,
    downloader: AttachmentDownloader,
    *,
    image_ocr: TextExtractor | None = None,
    extractors: Mapping[str, TextExtractor] | None = None,
) -> NoticeDocumentCorpus:
    active_extractors: dict[str, TextExtractor] = {
        "pdf": lambda content: extract_pdf_text(content, image_ocr=image_ocr),
        "hwpx": extract_hwpx_text,
    }
    if image_ocr is not None:
        active_extractors["image"] = image_ocr
    if extractors is not None:
        active_extractors.update(extractors)

    groups = _group_attachments(notice.attachments)
    comparisons = [
        _extract_and_compare(group_key, attachments, downloader, active_extractors)
        for group_key, attachments in groups.items()
    ]
    review_reasons = [
        comparison.review_reason
        for comparison in comparisons
        if comparison.review_required and comparison.review_reason
    ]

    return NoticeDocumentCorpus(
        html=DocumentExtraction(
            filename=f"{notice.source_id}.html",
            source_type="html",
            status="succeeded",
            text=notice.body_text,
        ),
        attachment_groups=comparisons,
        review_required=bool(review_reasons),
        review_reasons=review_reasons,
    )


def extract_pdf_text(
    content: bytes,
    *,
    image_ocr: TextExtractor | None = None,
) -> str:
    return extract_pdf_document(content, image_ocr=image_ocr).text


def extract_hwpx_text(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            section_names = sorted(
                name
                for name in archive.namelist()
                if re.fullmatch(r"Contents/section\d+\.xml", name)
            )
            texts: list[str] = []
            for section_name in section_names:
                root = ElementTree.fromstring(archive.read(section_name))
                texts.extend(
                    element.text or ""
                    for element in root.iter()
                    if element.tag.rsplit("}", 1)[-1] == "t"
                )
    except (BadZipFile, ElementTree.ParseError) as error:
        raise ValueError("Invalid HWPX document") from error
    return _clean_text(" ".join(texts))


def _extract_and_compare(
    group_key: str,
    attachments: list[SourceAttachment],
    downloader: AttachmentDownloader,
    extractors: Mapping[str, TextExtractor],
) -> AttachmentComparison:
    results = [
        _extract_attachment(attachment, downloader, extractors)
        for attachment in attachments
    ]
    succeeded = [result for result in results if result.status == "succeeded"]
    representative = min(
        succeeded,
        key=lambda result: SOURCE_PRIORITY[result.source_type],
        default=None,
    )

    failed_names = [result.filename for result in results if result.status == "failed"]
    conflict = _has_text_conflict(succeeded)
    reasons: list[str] = []
    if failed_names:
        reasons.append(f"추출 실패: {', '.join(failed_names)}")
    if conflict:
        reasons.append("동일 문서의 형식별 추출 내용이 일치하지 않음")

    return AttachmentComparison(
        group_key=group_key,
        extractions=results,
        representative_filename=(
            representative.filename if representative is not None else None
        ),
        review_required=bool(reasons),
        review_reason="; ".join(reasons) or None,
    )


def _extract_attachment(
    attachment: SourceAttachment,
    downloader: AttachmentDownloader,
    extractors: Mapping[str, TextExtractor],
) -> DocumentExtraction:
    extractor = extractors.get(attachment.file_type)
    if extractor is None:
        return DocumentExtraction(
            filename=attachment.filename,
            source_type=attachment.file_type,
            status="failed",
            error=f"No extractor configured for {attachment.file_type}",
        )

    try:
        content = downloader.fetch_bytes(attachment.url)
        _validate_payload(attachment.file_type, content)
        text = _clean_text(extractor(content))
        if len(text) < MINIMUM_TEXT_LENGTH:
            raise ValueError("Extracted text is too short")
    except Exception as error:
        return DocumentExtraction(
            filename=attachment.filename,
            source_type=attachment.file_type,
            status="failed",
            error=str(error),
        )

    return DocumentExtraction(
        filename=attachment.filename,
        source_type=attachment.file_type,
        status="succeeded",
        text=text,
    )


def _group_attachments(
    attachments: list[SourceAttachment],
) -> dict[str, list[SourceAttachment]]:
    groups: dict[str, list[SourceAttachment]] = {}
    for attachment in attachments:
        group_key = _clean_text(PurePath(attachment.filename).stem).casefold()
        groups.setdefault(group_key, []).append(attachment)
    return groups


def _has_text_conflict(extractions: list[DocumentExtraction]) -> bool:
    for index, left in enumerate(extractions):
        for right in extractions[index + 1 :]:
            if _number_tokens(left.text) != _number_tokens(right.text):
                return True
            ratio = SequenceMatcher(
                None,
                _comparison_text(left.text),
                _comparison_text(right.text),
            ).ratio()
            if ratio < MINIMUM_VARIANT_SIMILARITY:
                return True
    return False


def _number_tokens(value: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)*", value)


def _validate_payload(file_type: str, content: bytes) -> None:
    expected_magic = {
        "pdf": (b"%PDF",),
        "hwpx": (b"PK\x03\x04",),
        "image": (
            b"\x89PNG",
            b"\xff\xd8\xff",
            b"GIF8",
            b"BM",
            b"II*\x00",
            b"MM\x00*",
            b"RIFF",
        ),
    }.get(file_type)
    if expected_magic and not content.startswith(expected_magic):
        raise ValueError(f"Downloaded content is not a valid {file_type} payload")


def _comparison_text(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", value.casefold())


def _clean_text(value: str) -> str:
    return " ".join(value.split())
