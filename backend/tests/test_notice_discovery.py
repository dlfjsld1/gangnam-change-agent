import pytest

from app.schemas.agent_api import AgentRunResponse
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.services.notice_discovery import (
    NoticeDiscoveryService,
    NoticeDiscoveryUnavailable,
)


class FakeRepository:
    def __init__(self, existing_urls: set[str]) -> None:
        self.existing_urls = existing_urls

    def has_source_url(self, source_url: str) -> bool:
        return source_url in self.existing_urls


class FakeExecutionService:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def run(self, notice_url: str) -> AgentRunResponse:
        self.urls.append(notice_url)
        return AgentRunResponse(
            agent_run=AgentRun(
                run_id=f"run-{len(self.urls)}",
                notice_id=str(len(self.urls)),
                status="review_required",
                node_logs=[
                    AgentNodeLog(
                        node="await_review",
                        status="completed",
                        message="관리자 검토 대기",
                    )
                ],
                review_required=True,
                review_reason="관리자 검토 필요",
                unresolved_fields=[],
            ),
            policy_package=None,
            field_definition_proposals=[],
            field_definition_reviews=[],
            evidence_issues=[],
        )


def test_discovery_skips_processed_urls_and_runs_first_new_notice() -> None:
    old_url = "https://www.gangnam.go.kr/notice/view.do?id=old"
    first_new_url = "https://www.gangnam.go.kr/notice/view.do?id=new-1"
    second_new_url = "https://www.gangnam.go.kr/notice/view.do?id=new-2"
    execution_service = FakeExecutionService()
    service = NoticeDiscoveryService(
        FakeRepository({old_url}),
        execution_service,
        discover_urls=lambda: [old_url, first_new_url, second_new_url],
    )

    result = service.run(max_new_notices=1)

    assert result.discovered_count == 3
    assert result.already_processed_count == 1
    assert [run.run_id for run in result.processed_runs] == ["run-1"]
    assert execution_service.urls == [first_new_url]


def test_discovery_reports_board_fetch_failure() -> None:
    def fail_discovery() -> list[str]:
        raise TimeoutError("timeout")

    service = NoticeDiscoveryService(
        FakeRepository(set()),
        FakeExecutionService(),
        discover_urls=fail_discovery,
    )

    with pytest.raises(NoticeDiscoveryUnavailable):
        service.run()
