from fastapi.testclient import TestClient

from app.main import (
    app,
    get_agent_execution_service,
    get_agent_repository,
)
from app.schemas.agent_api import AgentRunResponse
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.services.agent_execution import PreviousPolicyNotFound


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


class FakeAgentRepository:
    def __init__(self, agent_run: dict[str, object] | None) -> None:
        self.agent_run = agent_run

    def get_agent_run(self, run_id: str) -> dict[str, object] | None:
        return self.agent_run


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
