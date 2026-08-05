from copy import deepcopy
from hashlib import sha256
import mimetypes
import os
from pathlib import PurePath
import re
from typing import Any, Protocol
from urllib.parse import quote

from app.schemas.source_notice import SourceAttachment, SourceNotice
from app.tools.document_extractor import (
    AttachmentDownloader,
    ScraplingAttachmentDownloader,
)


SENSITIVE_FILENAME_TERMS = (
    "개인정보",
    "합격자",
    "응시자",
    "지원자명단",
    "연락처",
)


class PublicAttachmentArchive(Protocol):
    def archive_policy_evidence(
        self,
        notice: SourceNotice,
        policy_package: dict[str, Any],
    ) -> tuple[SourceNotice, dict[str, Any]]: ...


class DisabledPublicAttachmentArchive:
    def archive_policy_evidence(
        self,
        notice: SourceNotice,
        policy_package: dict[str, Any],
    ) -> tuple[SourceNotice, dict[str, Any]]:
        return notice, policy_package


class S3PublicAttachmentArchive:
    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        public_base_url: str,
        prefix: str = "public-attachments",
        client: Any,
        downloader: AttachmentDownloader | None = None,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._public_base_url = public_base_url.rstrip("/")
        self._prefix = prefix.strip("/")
        self._client = client
        self._downloader = downloader or ScraplingAttachmentDownloader()

    def archive_policy_evidence(
        self,
        notice: SourceNotice,
        policy_package: dict[str, Any],
    ) -> tuple[SourceNotice, dict[str, Any]]:
        evidence_names = {
            str(evidence.get("document_name"))
            for evidence in policy_package.get("evidence", [])
            if isinstance(evidence, dict) and evidence.get("document_name")
        }
        archived_by_name: dict[str, SourceAttachment] = {}
        attachments: list[SourceAttachment] = []
        for attachment in notice.attachments:
            if attachment.filename not in evidence_names:
                attachments.append(attachment)
                continue
            _ensure_public_filename(attachment.filename)
            try:
                content = self._downloader.fetch_bytes(attachment.url)
                digest = sha256(content).hexdigest()
                key = _object_key(
                    self._prefix,
                    notice,
                    attachment.filename,
                    digest,
                )
                content_type = (
                    mimetypes.guess_type(attachment.filename)[0]
                    or "application/octet-stream"
                )
                self._client.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                    CacheControl="public, max-age=31536000, immutable",
                )
            except Exception as error:
                raise AttachmentArchiveUnavailable(
                    f"Public attachment archive failed: {attachment.filename}"
                ) from error
            archived = attachment.model_copy(
                update={
                    "storage_key": key,
                    "public_url": f"{self._public_base_url}/{quote(key, safe='/')}",
                    "sha256": digest,
                }
            )
            attachments.append(archived)
            archived_by_name[attachment.filename] = archived

        package = deepcopy(policy_package)
        for evidence in package.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            archived = archived_by_name.get(str(evidence.get("document_name")))
            if archived is not None:
                evidence["source_url"] = archived.public_url
        return notice.model_copy(update={"attachments": attachments}), package


def configured_public_attachment_archive() -> PublicAttachmentArchive:
    bucket = os.getenv("S3_ATTACHMENT_BUCKET")
    if not bucket:
        return DisabledPublicAttachmentArchive()
    region = os.getenv("S3_ATTACHMENT_REGION", "ap-northeast-2")
    base_url = os.getenv(
        "PUBLIC_ATTACHMENT_BASE_URL",
        f"https://{bucket}.s3.{region}.amazonaws.com",
    )
    import boto3

    return S3PublicAttachmentArchive(
        bucket=bucket,
        region=region,
        public_base_url=base_url,
        prefix=os.getenv("S3_ATTACHMENT_PREFIX", "public-attachments"),
        client=boto3.client("s3", region_name=region),
    )


def _ensure_public_filename(filename: str) -> None:
    compact = re.sub(r"\s+", "", filename)
    if any(term in compact for term in SENSITIVE_FILENAME_TERMS):
        raise AttachmentPrivacyRejected(
            f"Attachment requires privacy review before public archive: {filename}"
        )


def _object_key(
    prefix: str,
    notice: SourceNotice,
    filename: str,
    digest: str,
) -> str:
    safe_name = PurePath(filename.replace("\\", "/")).name.replace("/", "_")
    return (
        f"{prefix}/{notice.source_board}/{notice.source_id}/{digest[:12]}-{safe_name}"
    )


class AttachmentPrivacyRejected(RuntimeError):
    pass


class AttachmentArchiveUnavailable(RuntimeError):
    pass
