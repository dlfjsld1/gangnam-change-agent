from datetime import date

import pytest

from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.field_definition import (
    FieldDefinition,
    FieldDefinitionProposal,
    FieldDefinitionReview,
)
from app.schemas.policy_extraction import EvidenceIssue
from app.schemas.source_notice import SourceNotice
from app.services.agent_execution import AgentExecutionService, PreviousPolicyNotFound


class FakeRepository:
    def __init__(self, previous_policy: dict[str, object] | None = None) -> None:
        self.previous_policy = previous_policy
        self.saved: dict[str, object] | None = None

    def get_approved_policy_package(self, policy_id: str) -> dict[str, object] | None:
        if self.previous_policy is None:
            return None
        return self.previous_policy

    def list_approved_field_definitions(self) -> list[FieldDefinition]:
        return []

    def save_execution(self, agent_run: AgentRun, **kwargs: object) -> None:
        self.saved = {"agent_run": agent_run, **kwargs}


class FakeGraph:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.input_state: dict[str, object] | None = None

    def invoke(self, state: dict[str, object]) -> dict[str, object]:
        self.input_state = state
        return self.result


def _notice() -> SourceNotice:
    return SourceNotice(
        source_id="61922",
        source_board="gangnam_public_notice",
        source_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        title="청년 응시료 지원사업",
        published_at=date(2026, 1, 8),
        department="일자리정책과",
        body_text="지원 대상은 강남구 거주 청년입니다.",
        attachments=[],
    )


def _agent_run() -> AgentRun:
    return AgentRun(
        run_id="run-api",
        notice_id="61922",
        status="review_required",
        node_logs=[
            AgentNodeLog(
                node="await_review",
                status="completed",
                message="관리자 검토 대기",
            )
        ],
        review_required=True,
        review_reason="새 필드 승인 필요",
        unresolved_fields=["residence"],
        policy_id="demo-policy-v3",
    )


def _proposal() -> FieldDefinitionProposal:
    return FieldDefinitionProposal(
        proposed_field=FieldDefinition(
            key="residence",
            label="거주 지역",
            data_type="string",
            question="현재 거주 지역은 어디인가요?",
            sensitivity="medium",
            validity_days=365,
            review_status="pending",
        ),
        review_reason="새 필드 승인 필요",
    )


def test_execution_uses_approved_previous_policy_and_persists_result() -> None:
    previous = {
        "policy_id": "demo-policy-v2",
        "policy_family_id": "demo-policy",
        "version": 2,
        "required_profile_fields": [
            {
                "key": "age",
                "label": "나이",
                "data_type": "number",
                "question": "현재 나이는 몇 살인가요?",
                "sensitivity": "low",
                "validity_days": 365,
                "review_status": "approved",
            }
        ],
    }
    proposal = _proposal()
    review = FieldDefinitionReview(
        review_id="run-api:residence",
        proposal=proposal,
    )
    evidence_issue = EvidenceIssue(
        code="evidence.quote_not_found",
        document_name="61922.html",
        message="근거 인용 불일치",
    )
    package = {
        "policy_id": "demo-policy-v3",
        "policy_family_id": "demo-policy",
        "version": 3,
    }
    graph = FakeGraph(
        {
            "notice": _notice(),
            "agent_run": _agent_run(),
            "policy_package": package,
            "field_proposals": [proposal],
            "field_reviews": [review],
            "evidence_issues": [evidence_issue],
        }
    )
    repository = FakeRepository(previous)

    def runtime_factory(registry: object) -> object:
        assert registry.find("age") is not None
        return object()

    service = AgentExecutionService(
        repository,
        runtime_factory=runtime_factory,
        graph_builder=lambda runtime: graph,
    )

    response = service.run(
        _notice().source_url,
        previous_policy_id="demo-policy-v2",
    )

    assert graph.input_state is not None
    assert graph.input_state["previous_policy_package"] == previous
    assert response.agent_run.run_id == "run-api"
    assert response.field_definition_reviews == [review]
    assert response.evidence_issues == [evidence_issue]
    assert repository.saved is not None
    assert repository.saved["policy_package"] == package


def test_execution_rejects_missing_or_unapproved_previous_policy() -> None:
    service = AgentExecutionService(FakeRepository())

    with pytest.raises(PreviousPolicyNotFound):
        service.run(
            _notice().source_url,
            previous_policy_id="missing-policy",
        )
