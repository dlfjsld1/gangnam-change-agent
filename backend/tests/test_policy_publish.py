from datetime import date
from typing import Any

from app.schemas.source_notice import SourceNotice
from app.services.policy_publish import PolicyPublishService


class FakeRepository:
    def __init__(self) -> None:
        self.notice = SourceNotice(
            source_id="61922",
            source_board="gangnam_public_notice",
            source_url="https://www.gangnam.go.kr/notice/61922",
            title="지원사업",
            published_at=date(2026, 8, 5),
            department="복지과",
            body_text="지원 안내",
            attachments=[],
        )
        self.saved_notice: SourceNotice | None = None
        self.approved_package: dict[str, Any] | None = None

    def get_policy_publish_context(
        self, policy_id: str
    ) -> tuple[dict[str, Any], SourceNotice]:
        return {"policy_id": policy_id, "evidence": []}, self.notice

    def save_source_notice(self, notice: SourceNotice) -> None:
        self.saved_notice = notice

    def approve_policy_package(
        self,
        policy_id: str,
        *,
        policy_package: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert policy_package is not None
        self.approved_package = policy_package
        return {**policy_package, "review": {"status": "approved"}}


class FakeArchive:
    def archive_policy_evidence(
        self,
        notice: SourceNotice,
        policy_package: dict[str, Any],
    ) -> tuple[SourceNotice, dict[str, Any]]:
        return notice, {**policy_package, "archived": True}


def test_publish_archives_evidence_before_policy_approval() -> None:
    repository = FakeRepository()
    service = PolicyPublishService(repository, FakeArchive())

    published = service.approve("policy-1")

    assert repository.saved_notice == repository.notice
    assert repository.approved_package == {
        "policy_id": "policy-1",
        "evidence": [],
        "archived": True,
    }
    assert published["review"]["status"] == "approved"
