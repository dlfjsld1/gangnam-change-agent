from copy import deepcopy
from datetime import date
from hashlib import sha256
from typing import Any

import pytest

from app.schemas.source_notice import SourceAttachment, SourceNotice
from app.services.attachment_archive import (
    AttachmentPrivacyRejected,
    S3PublicAttachmentArchive,
)


class FakeDownloader:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads
        self.urls: list[str] = []

    def fetch_bytes(self, attachment_url: str) -> bytes:
        self.urls.append(attachment_url)
        return self.payloads[attachment_url]


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: list[dict[str, Any]] = []

    def put_object(self, **kwargs: Any) -> None:
        self.objects.append(kwargs)


def _notice(filename: str = "지원사업 안내.pdf") -> SourceNotice:
    return SourceNotice(
        source_id="61922",
        source_board="gangnam_public_notice",
        source_url="https://www.gangnam.go.kr/notice/61922",
        title="지원사업",
        published_at=date(2026, 8, 5),
        department="복지과",
        body_text="지원 안내",
        attachments=[
            SourceAttachment(
                filename=filename,
                url="https://www.gangnam.go.kr/files/policy.pdf",
                file_type="pdf",
            ),
            SourceAttachment(
                filename="참고자료.pdf",
                url="https://www.gangnam.go.kr/files/reference.pdf",
                file_type="pdf",
            ),
        ],
    )


def _package(filename: str = "지원사업 안내.pdf") -> dict[str, Any]:
    return {
        "policy_id": "policy-1",
        "evidence": [
            {
                "evidence_id": "evidence-1",
                "document_name": filename,
                "source_url": "https://www.gangnam.go.kr/files/policy.pdf",
            }
        ],
    }


def test_archive_uploads_only_evidence_attachment_and_rewrites_url() -> None:
    content = b"%PDF public policy"
    downloader = FakeDownloader(
        {
            "https://www.gangnam.go.kr/files/policy.pdf": content,
            "https://www.gangnam.go.kr/files/reference.pdf": b"unused",
        }
    )
    client = FakeS3Client()
    archive = S3PublicAttachmentArchive(
        bucket="public-bucket",
        region="ap-northeast-2",
        public_base_url="https://files.example.com",
        client=client,
        downloader=downloader,
    )

    notice, package = archive.archive_policy_evidence(_notice(), _package())

    digest = sha256(content).hexdigest()
    archived = notice.attachments[0]
    assert downloader.urls == ["https://www.gangnam.go.kr/files/policy.pdf"]
    assert archived.storage_key == (
        "public-attachments/gangnam_public_notice/61922/"
        f"{digest[:12]}-지원사업 안내.pdf"
    )
    assert archived.public_url is not None
    assert "%EC%A7%80%EC%9B%90%EC%82%AC%EC%97%85" in archived.public_url
    assert archived.sha256 == digest
    assert notice.attachments[1].public_url is None
    assert package["evidence"][0]["source_url"] == archived.public_url
    assert client.objects[0]["Bucket"] == "public-bucket"
    assert client.objects[0]["ContentType"] == "application/pdf"


def test_archive_rejects_sensitive_filename_before_upload() -> None:
    client = FakeS3Client()
    archive = S3PublicAttachmentArchive(
        bucket="public-bucket",
        region="ap-northeast-2",
        public_base_url="https://files.example.com",
        client=client,
        downloader=FakeDownloader({}),
    )

    with pytest.raises(AttachmentPrivacyRejected):
        archive.archive_policy_evidence(
            _notice("합격자 명단.pdf"),
            deepcopy(_package("합격자 명단.pdf")),
        )

    assert client.objects == []
