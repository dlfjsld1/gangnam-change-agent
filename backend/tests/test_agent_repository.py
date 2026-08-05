from copy import deepcopy
from datetime import date
from json import loads
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from sqlalchemy import func, inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.database import Database
from app.db_models import (
    Base,
    FieldDefinitionProposalRecord,
    FieldDefinitionReviewRecord,
)
from app.repositories.agent_repository import AgentRepository, ReviewConflict
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.field_definition import (
    FieldDefinition,
    FieldDefinitionProposal,
    FieldDefinitionReview,
)
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


def _review(
    proposal: FieldDefinitionProposal,
    run_id: str = "run-1",
) -> FieldDefinitionReview:
    return FieldDefinitionReview(
        review_id=f"{run_id}:{proposal.proposed_field.key}",
        proposal=proposal,
    )


def test_sqlite_repository_persists_agent_result_and_proposal(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    package = deepcopy(APPROVED_POLICY)
    package["review"] = {"status": "pending", "reviewed_at": None}
    proposal = _proposal()

    repository.save_execution(
        _agent_run("run-1", package["policy_id"]),
        notice=_notice(),
        policy_package=package,
        field_proposals=[proposal],
        field_reviews=[_review(proposal)],
    )

    assert repository.get_agent_run("run-1")["review_required"] is True
    assert repository.get_policy_package(package["policy_id"]) == package
    assert repository.get_approved_policy_package(package["policy_id"]) is None
    with database.session_factory() as session:
        proposal_count = session.scalar(
            select(func.count()).select_from(FieldDefinitionProposalRecord)
        )
        review_count = session.scalar(
            select(func.count()).select_from(FieldDefinitionReviewRecord)
        )
    assert proposal_count == 1
    assert review_count == 1
    assert set(inspect(database.engine).get_table_names()) == {
        "agent_runs",
        "field_definition_proposals",
        "field_definition_reviews",
        "policy_packages",
        "source_notices",
    }

    with database.session_factory.begin() as session:
        review_record = session.get(
            FieldDefinitionReviewRecord,
            "run-1:new_condition",
        )
        assert review_record is not None
        review_record.status = "approved"
        review_record.payload = {
            **review_record.payload,
            "status": "approved",
            "approved_field": {
                **proposal.proposed_field.model_dump(mode="json"),
                "review_status": "approved",
            },
        }

    approved_definitions = repository.list_approved_field_definitions()
    assert [definition.key for definition in approved_definitions] == ["new_condition"]
    assert approved_definitions[0].review_status == "approved"


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
    assert repository.get_approved_policy_package("demo-policy-v2") == approved


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


def test_admin_queries_filter_and_join_execution_data(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    package = deepcopy(APPROVED_POLICY)
    package["policy_id"] = "policy-admin"
    package["review"] = {"status": "pending", "reviewed_at": None}
    proposal = _proposal()
    repository.save_execution(
        _agent_run("run-admin", package["policy_id"]),
        policy_package=package,
        field_proposals=[proposal],
        field_reviews=[_review(proposal, "run-admin")],
    )
    repository.save_execution(
        AgentRun(
            run_id="run-completed",
            notice_id="61923",
            status="completed",
            node_logs=[],
            review_required=False,
            review_reason=None,
            unresolved_fields=[],
        )
    )

    runs = repository.list_agent_runs(
        status="review_required",
        review_required=True,
        limit=10,
    )
    reviews = repository.list_field_definition_reviews(
        status="pending",
        run_id="run-admin",
        limit=10,
    )
    packages = repository.list_admin_policy_packages(
        review_status="pending",
        run_id="run-admin",
        limit=10,
    )
    detail = repository.get_agent_run_detail("run-admin")

    assert [run["run_id"] for run in runs] == ["run-admin"]
    assert [review["review_id"] for review in reviews] == ["run-admin:new_condition"]
    assert [item["policy_id"] for item in packages] == ["policy-admin"]
    assert detail is not None
    assert detail["agent_run"]["run_id"] == "run-admin"
    assert detail["policy_package"]["policy_id"] == "policy-admin"
    assert len(detail["field_definition_proposals"]) == 1
    assert len(detail["field_definition_reviews"]) == 1
    assert repository.get_agent_run_detail("missing") is None


def test_field_approval_rewrites_policy_and_enables_publish(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    package = deepcopy(APPROVED_POLICY)
    package["policy_id"] = "policy-review"
    package["review"] = {"status": "pending", "reviewed_at": None}
    proposal = _proposal()
    package["required_profile_fields"].append(
        proposal.proposed_field.model_dump(mode="json")
    )
    package["eligibility_rule"] = {
        "or": [
            package["eligibility_rule"],
            {"field": "new_condition", "operator": "exists", "value": True},
        ]
    }
    repository.save_execution(
        _agent_run("run-1", package["policy_id"]),
        policy_package=package,
        field_proposals=[proposal],
        field_reviews=[_review(proposal)],
    )
    approved_field = proposal.proposed_field.model_copy(
        update={"key": "canonical_condition", "label": "표준 조건"}
    )

    review = repository.approve_field_definition_review(
        "run-1:new_condition",
        approved_field=approved_field,
        review_note="표준 필드로 승인",
    )
    published = repository.approve_policy_package(package["policy_id"])

    assert review["status"] == "approved"
    assert review["approved_field"]["review_status"] == "approved"
    assert published["review"]["status"] == "approved"
    assert published["eligibility_rule"]["or"][1]["field"] == "canonical_condition"
    assert any(
        field["key"] == "canonical_condition"
        for field in published["required_profile_fields"]
    )
    assert repository.get_approved_policy_package(package["policy_id"]) == published
    assert published in repository.list_approved_policy_packages()
    _validate_contract(review, "FieldDefinitionReview")
    _validate_contract(published, "PolicyPackage")


def test_rejected_field_review_blocks_policy_publish(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    package = deepcopy(APPROVED_POLICY)
    package["policy_id"] = "policy-rejected-field"
    package["review"] = {"status": "pending", "reviewed_at": None}
    proposal = _proposal()
    repository.save_execution(
        _agent_run("run-1", package["policy_id"]),
        policy_package=package,
        field_proposals=[proposal],
        field_reviews=[_review(proposal)],
    )

    rejected = repository.reject_field_definition_review(
        "run-1:new_condition",
        review_note="근거 불충분",
    )

    assert rejected["status"] == "rejected"
    with pytest.raises(ReviewConflict):
        repository.approve_policy_package(package["policy_id"])
    assert repository.get_approved_policy_package(package["policy_id"]) is None
    _validate_contract(rejected, "FieldDefinitionReview")


def test_policy_package_can_be_rejected_without_field_reviews(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'agent.db'}")
    database.create_schema()
    repository = AgentRepository(database.session_factory)
    package = deepcopy(APPROVED_POLICY)
    package["policy_id"] = "policy-rejected"
    package["review"] = {"status": "pending", "reviewed_at": None}
    repository.save_execution(
        _agent_run("run-rejected", package["policy_id"]),
        policy_package=package,
    )

    rejected = repository.reject_policy_package(package["policy_id"])

    assert rejected["review"]["status"] == "rejected"
    assert repository.get_approved_policy_package(package["policy_id"]) is None
    _validate_contract(rejected, "PolicyPackage")


def test_models_compile_for_postgresql_dialect() -> None:
    statements = [
        str(CreateTable(table).compile(dialect=postgresql.dialect()))
        for table in Base.metadata.sorted_tables
    ]

    assert len(statements) == 5
    assert all("CREATE TABLE" in statement for statement in statements)


def _validate_contract(payload: dict[str, object], title: str) -> None:
    contracts_dir = PROJECT_ROOT / "docs" / "contracts"
    schemas = [
        loads(path.read_text("utf-8")) for path in contracts_dir.glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(schema for schema in schemas if schema["title"] == title)
    Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(payload)
