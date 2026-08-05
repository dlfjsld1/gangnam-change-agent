from typing import Literal

from pydantic import BaseModel


DocumentType = Literal["html", "pdf", "hwpx", "image", "hwp", "other"]
ExtractionStatus = Literal["succeeded", "failed"]


class DocumentExtraction(BaseModel):
    filename: str
    source_type: DocumentType
    status: ExtractionStatus
    text: str = ""
    error: str | None = None


class AttachmentComparison(BaseModel):
    group_key: str
    extractions: list[DocumentExtraction]
    representative_filename: str | None
    review_required: bool
    review_reason: str | None


class NoticeDocumentCorpus(BaseModel):
    html: DocumentExtraction
    attachment_groups: list[AttachmentComparison]
    review_required: bool
    review_reasons: list[str]
