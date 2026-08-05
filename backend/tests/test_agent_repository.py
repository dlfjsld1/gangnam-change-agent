from copy import deepcopy
from datetime import date
from json import loads
from pathlib import Path

from sqlalchemy import func, inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.database import Database
from app.db_models import Base, FieldDefinitionProposalRecord
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.field_definition import FieldDefinition, FieldDefinitionProposal
from app.schemas.source_notice import SourceNotice


PROJECT_ROOT = Path(__file__).parents[2]
APPROVED_POLICY = loads(
    (PROJECT_ROOT / "demo-data" / "approved-policy.json").read_text("utf-8")
)


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


def _agent_run(run_id: str, policy_id: str | None) -> AgentRun:
    return AgentRun(
        run_id=run_id,
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
        unresolved_fields=["new_condition"],
        policy_id=policy_id,
    )


def _proposal() -> FieldDefinitionProposal:
    return FieldDefinitionProposal(
        proposed_field=FieldDefinition(
            key="new_condition",
            label="새 조건",
            data_type="string",
            question="새 조건에 해당하나요?",
            sensitivity="low",
            validity_days=30,
            review_status="pending",
        ),
        review_reason="공고에서 새 조건을 발견했습니다.",
    )


def test_sqlite_repository_persists_agent_result_and_proposal(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    package = deepcopy(APPROVED_POLICY)
    package["review"] = {"status": "pending", "reviewed_at": None}

    repository.save_execution(
        _agent_run("run-1", package["policy_id"]),
        notice=_notice(),
        policy_package=package,
        field_proposals=[_proposal()],
    )

    assert repository.get_agent_run("run-1")["review_required"] is True
    assert repository.get_policy_package(package["policy_id"]) == package
    with database.session_factory() as session:
        proposal_count = session.scalar(
            select(func.count()).select_from(FieldDefinitionProposalRecord)
        )
    assert proposal_count == 1
    assert set(inspect(database.engine).get_table_names()) == {
        "agent_runs",
        "field_definition_proposals",
        "field_definition_reviews",
        "policy_packages",
        "source_notices",
    }


def test_latest_policy_query_returns_only_approved_version(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    approved = deepcopy(APPROVED_POLICY)
    pending = deepcopy(APPROVED_POLICY)
    pending["policy_id"] = "demo-policy-v3"
    pending["version"] = 3
    pending["review"] = {"status": "pending", "reviewed_at": None}

    repository.save_execution(
        _agent_run("run-approved", approved["policy_id"]),
        policy_package=approved,
    )
    repository.save_execution(
        _agent_run("run-pending", pending["policy_id"]),
        policy_package=pending,
    )

    latest = repository.get_latest_approved_policy("demo-policy")

    assert latest is not None
    assert latest["policy_id"] == "demo-policy-v2"


def test_failed_run_can_be_saved_without_notice_or_policy(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    failed_run = AgentRun(
        run_id="run-failed",
        notice_id="unknown",
        status="failed",
        node_logs=[
            AgentNodeLog(node="fetch_notice", status="failed", message="수집 실패")
        ],
        review_required=True,
        review_reason="수집 실패",
        unresolved_fields=[],
    )

    repository.save_execution(failed_run)

    assert repository.get_agent_run("run-failed")["status"] == "failed"


def test_models_compile_for_postgresql_dialect() -> None:
    statements = [
        str(CreateTable(table).compile(dialect=postgresql.dialect()))
        for table in Base.metadata.sorted_tables
    ]

    assert len(statements) == 5
    assert all("CREATE TABLE" in statement for statement in statements)
