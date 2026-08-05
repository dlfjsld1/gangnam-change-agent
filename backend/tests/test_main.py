from fastapi.testclient import TestClient

from app.main import (
    app,
    get_agent_execution_service,
    get_agent_repository,
    get_notice_discovery_service,
    get_policy_publish_service,
)
from app.repositories.agent_repository import ReviewConflict, ReviewNotFound
from app.schemas.agent_api import AgentRunResponse
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.discovery_api import NoticeDiscoveryResponse
from app.services.agent_execution import PreviousPolicyNotFound
from app.services.notice_discovery import NoticeDiscoveryUnavailable


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_policy_packages_returns_only_approved_fixture() -> None:
    response = client.get("/api/policy-packages")

    assert response.status_code == 200
    policy_packages = response.json()
    assert len(policy_packages) == 1
    assert policy_packages[0]["review"]["status"] == "approved"


def test_policy_package_can_be_loaded_by_id() -> None:
    response = client.get("/api/policy-packages/demo-policy-v2")

    assert response.status_code == 200
    assert response.json()["policy_id"] == "demo-policy-v2"


class FakeExecutionService:
    def __init__(self, *, missing_previous: bool = False) -> None:
        self.missing_previous = missing_previous
        self.request: tuple[str, str | None] | None = None

    def run(
        self,
        notice_url: str,
        *,
        previous_policy_id: str | None = None,
    ) -> AgentRunResponse:
        self.request = (notice_url, previous_policy_id)
        if self.missing_previous:
            raise PreviousPolicyNotFound(previous_policy_id)
        return AgentRunResponse(
            agent_run=AgentRun(
                run_id="run-api",
                notice_id="61922",
                status="completed",
                node_logs=[
                    AgentNodeLog(
                        node="complete",
                        status="completed",
                        message="완료",
                    )
                ],
                review_required=False,
                review_reason=None,
                unresolved_fields=[],
                policy_id="demo-policy-v1",
            ),
            policy_package={"policy_id": "demo-policy-v1"},
            field_definition_proposals=[],
            field_definition_reviews=[],
            evidence_issues=[],
        )


class FakeNoticeDiscoveryService:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.unavailable = unavailable
        self.max_new_notices: int | None = None

    def run(self, *, max_new_notices: int = 1) -> NoticeDiscoveryResponse:
        self.max_new_notices = max_new_notices
        if self.unavailable:
            raise NoticeDiscoveryUnavailable("board unavailable")
        return NoticeDiscoveryResponse(
            discovered_count=4,
            already_processed_count=3,
            processed_runs=[
                AgentRun(
                    run_id="run-discovery",
                    notice_id="61923",
                    status="review_required",
                    node_logs=[],
                    review_required=True,
                    review_reason="관리자 검토 필요",
                    unresolved_fields=[],
                )
            ],
        )


class FakeAgentRepository:
    def __init__(self, agent_run: dict[str, object] | None) -> None:
        self.agent_run = agent_run

    def get_agent_run(self, run_id: str) -> dict[str, object] | None:
        return self.agent_run


class FakeReviewRepository:
    def __init__(self, *, conflict: bool = False, missing: bool = False) -> None:
        self.conflict = conflict
        self.missing = missing

    def list_field_definition_reviews(
        self,
        *,
        status: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return [{"review_id": "review-1", "status": "pending"}]

    def approve_field_definition_review(
        self,
        review_id: str,
        *,
        approved_field: object = None,
        review_note: str | None = None,
    ) -> dict[str, object]:
        if self.missing:
            raise ReviewNotFound(review_id)
        if self.conflict:
            raise ReviewConflict("already completed")
        return {
            "review_id": review_id,
            "status": "approved",
            "review_note": review_note,
        }


class FakePublishedRepository:
    def __init__(self, packages: list[dict[str, object]]) -> None:
        self.packages = packages

    def list_approved_policy_packages(self) -> list[dict[str, object]]:
        return self.packages

    def get_approved_policy_package(self, policy_id: str) -> dict[str, object] | None:
        return next(
            (item for item in self.packages if item["policy_id"] == policy_id),
            None,
        )


class FakeAdminQueryRepository:
    def __init__(self, *, missing: bool = False) -> None:
        self.missing = missing
        self.filters: dict[str, object] = {}

    def list_agent_runs(
        self,
        *,
        status: str | None = None,
        review_required: bool | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        self.filters["runs"] = (status, review_required, limit)
        return [{"run_id": "run-admin", "status": "review_required"}]

    def list_field_definition_reviews(
        self,
        *,
        status: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        self.filters["reviews"] = (status, run_id, limit)
        return [{"review_id": "run-admin:new-condition", "status": "pending"}]

    def list_admin_policy_packages(
        self,
        *,
        review_status: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        self.filters["packages"] = (review_status, run_id, limit)
        return [{"policy_id": "policy-admin", "review": {"status": "pending"}}]

    def get_policy_package(self, policy_id: str) -> dict[str, object] | None:
        if self.missing:
            return None
        return {"policy_id": policy_id, "review": {"status": "pending"}}

    def get_agent_run_detail(self, run_id: str) -> dict[str, object] | None:
        if self.missing:
            return None
        return {
            "agent_run": {"run_id": run_id},
            "policy_package": {"policy_id": "policy-admin"},
            "field_definition_proposals": [],
            "field_definition_reviews": [],
        }


class FakePolicyPublishService:
    def approve(self, policy_id: str) -> dict[str, object]:
        return {
            "policy_id": policy_id,
            "review": {"status": "approved"},
        }


def test_agent_run_endpoint_executes_service() -> None:
    service = FakeExecutionService()
    app.dependency_overrides[get_agent_execution_service] = lambda: service
    try:
        response = client.post(
            "/api/agent-runs",
            json={
                "notice_url": "https://www.gangnam.go.kr/notice/view.do?id=61922",
                "previous_policy_id": "demo-policy-v2",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["agent_run"]["run_id"] == "run-api"
    assert service.request == (
        "https://www.gangnam.go.kr/notice/view.do?id=61922",
        "demo-policy-v2",
    )


def test_notice_discovery_endpoint_runs_crawler_with_default_limit() -> None:
    service = FakeNoticeDiscoveryService()
    app.dependency_overrides[get_notice_discovery_service] = lambda: service
    try:
        response = client.post("/api/notice-discovery-runs", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["processed_runs"][0]["run_id"] == "run-discovery"
    assert service.max_new_notices == 1


def test_notice_discovery_endpoint_rejects_invalid_limit() -> None:
    response = client.post(
        "/api/notice-discovery-runs",
        json={"max_new_notices": 6},
    )

    assert response.status_code == 422


def test_notice_discovery_endpoint_reports_board_failure() -> None:
    service = FakeNoticeDiscoveryService(unavailable=True)
    app.dependency_overrides[get_notice_discovery_service] = lambda: service
    try:
        response = client.post("/api/notice-discovery-runs", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_agent_run_endpoint_rejects_unapproved_host() -> None:
    response = client.post(
        "/api/agent-runs",
        json={"notice_url": "https://example.com/notices/1"},
    )

    assert response.status_code == 422


def test_agent_run_endpoint_returns_404_for_missing_previous_policy() -> None:
    service = FakeExecutionService(missing_previous=True)
    app.dependency_overrides[get_agent_execution_service] = lambda: service
    try:
        response = client.post(
            "/api/agent-runs",
            json={
                "notice_url": "https://www.gangnam.go.kr/notice/view.do?id=61922",
                "previous_policy_id": "missing-policy",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_agent_run_can_be_loaded_by_id() -> None:
    repository = FakeAgentRepository({"run_id": "run-api", "status": "completed"})
    app.dependency_overrides[get_agent_repository] = lambda: repository
    try:
        response = client.get("/api/agent-runs/run-api")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["run_id"] == "run-api"


def test_missing_agent_run_returns_404() -> None:
    app.dependency_overrides[get_agent_repository] = lambda: FakeAgentRepository(None)
    try:
        response = client.get("/api/agent-runs/missing")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_field_review_can_be_approved() -> None:
    repository = FakeReviewRepository()
    app.dependency_overrides[get_agent_repository] = lambda: repository
    try:
        response = client.post(
            "/api/field-definition-reviews/review-1/approve",
            json={"review_note": "근거 확인"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "review_id": "review-1",
        "status": "approved",
        "review_note": "근거 확인",
    }


def test_completed_field_review_returns_conflict() -> None:
    app.dependency_overrides[get_agent_repository] = lambda: FakeReviewRepository(
        conflict=True
    )
    try:
        response = client.post(
            "/api/field-definition-reviews/review-1/approve",
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


def test_missing_field_review_returns_not_found() -> None:
    app.dependency_overrides[get_agent_repository] = lambda: FakeReviewRepository(
        missing=True
    )
    try:
        response = client.post(
            "/api/field-definition-reviews/missing/approve",
            json={},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_public_policy_api_prefers_approved_database_packages() -> None:
    package = {
        "policy_id": "stored-policy",
        "review": {"status": "approved", "reviewed_at": "2026-08-05T00:00:00Z"},
    }
    repository = FakePublishedRepository([package])
    app.dependency_overrides[get_agent_repository] = lambda: repository
    try:
        list_response = client.get("/api/policy-packages")
        fixture_response = client.get("/api/policy-packages/demo-policy-v2")
    finally:
        app.dependency_overrides.clear()

    assert list_response.json() == [package]
    assert fixture_response.status_code == 404


def test_admin_query_endpoints_forward_filters_and_return_details() -> None:
    repository = FakeAdminQueryRepository()
    app.dependency_overrides[get_agent_repository] = lambda: repository
    try:
        runs = client.get(
            "/api/agent-runs?status=review_required&review_required=true&limit=10"
        )
        reviews = client.get(
            "/api/field-definition-reviews?status=pending&run_id=run-admin&limit=20"
        )
        packages = client.get(
            "/api/admin/policy-packages?review_status=pending&run_id=run-admin&limit=30"
        )
        package = client.get("/api/admin/policy-packages/policy-admin")
        detail = client.get("/api/admin/agent-runs/run-admin")
    finally:
        app.dependency_overrides.clear()

    assert runs.status_code == 200
    assert reviews.status_code == 200
    assert packages.status_code == 200
    assert package.json()["review"]["status"] == "pending"
    assert detail.json()["agent_run"]["run_id"] == "run-admin"
    assert repository.filters == {
        "runs": ("review_required", True, 10),
        "reviews": ("pending", "run-admin", 20),
        "packages": ("pending", "run-admin", 30),
    }


def test_admin_query_details_return_not_found() -> None:
    app.dependency_overrides[get_agent_repository] = lambda: FakeAdminQueryRepository(
        missing=True
    )
    try:
        package = client.get("/api/admin/policy-packages/missing")
        detail = client.get("/api/admin/agent-runs/missing")
    finally:
        app.dependency_overrides.clear()

    assert package.status_code == 404
    assert detail.status_code == 404


def test_admin_query_rejects_invalid_filter_or_limit() -> None:
    invalid_status = client.get("/api/agent-runs?status=unknown")
    invalid_limit = client.get("/api/admin/policy-packages?limit=101")

    assert invalid_status.status_code == 422
    assert invalid_limit.status_code == 422


def test_policy_approval_uses_publish_service() -> None:
    app.dependency_overrides[get_policy_publish_service] = (
        lambda: FakePolicyPublishService()
    )
    try:
        response = client.post("/api/policy-packages/policy-1/approve")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["review"]["status"] == "approved"
