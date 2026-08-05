from datetime import date
from typing import Literal

from pydantic import BaseModel


SourceBoard = Literal[
    "gangnam_public_notice",
    "gangnam_job_notice",
    "gangnam_center_news",
]


class SourceAttachment(BaseModel):
    filename: str
    url: str
    file_type: Literal["hwpx", "pdf", "image", "hwp", "other"]
    storage_key: str | None = None
    public_url: str | None = None
    sha256: str | None = None


class SourceNotice(BaseModel):
    source_id: str
    source_board: SourceBoard
    source_url: str
    title: str
    published_at: date
    department: str | None
    body_text: str
    attachments: list[SourceAttachment]
