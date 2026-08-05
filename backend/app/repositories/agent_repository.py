from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, sessionmaker

from app.db_models import (
    AgentRunRecord,
    FieldDefinitionProposalRecord,
    FieldDefinitionReviewRecord,
    PolicyPackageRecord,
    SourceNoticeRecord,
)
from app.schemas.agent_run import AgentRun
from app.schemas.field_definition import (
    FieldDefinition,
    FieldDefinitionProposal,
    FieldDefinitionReview,
)
from app.schemas.source_notice import SourceNotice


class AgentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_execution(
        self,
        agent_run: AgentRun,
        *,
        notice: SourceNotice | None = None,
        policy_package: dict[str, Any] | None = None,
        field_proposals: list[FieldDefinitionProposal] | None = None,
        field_reviews: list[FieldDefinitionReview] | None = None,
    ) -> None:
        with self._session_factory.begin() as session:
            notice_key = None
            if notice is not None:
                notice_key = _notice_key(notice)
                session.merge(_notice_record(notice, notice_key))
            session.merge(_agent_run_record(agent_run, notice_key))
            if policy_package is not None:
                session.merge(_policy_package_record(agent_run.run_id, policy_package))
            for proposal in field_proposals or []:
                session.merge(_proposal_record(agent_run.run_id, proposal))
            for review in field_reviews or []:
                session.merge(_review_record(review))

    def get_agent_run(self, run_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            record = session.get(AgentRunRecord, run_id)
            return record.payload if record is not None else None

    def get_policy_package(self, policy_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            record = session.get(PolicyPackageRecord, policy_id)
            return record.payload if record is not None else None

    def get_approved_policy_package(self, policy_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            record = session.get(PolicyPackageRecord, policy_id)
            if record is None or record.review_status != "approved":
                return None
            return record.payload

    def list_approved_policy_packages(self) -> list[dict[str, Any]]:
        statement: Select[tuple[PolicyPackageRecord]] = (
            select(PolicyPackageRecord)
            .where(PolicyPackageRecord.review_status == "approved")
            .order_by(
                PolicyPackageRecord.policy_family_id,
                PolicyPackageRecord.version.desc(),
            )
        )
        with self._session_factory() as session:
            return [record.payload for record in session.scalars(statement)]

    def list_field_definition_reviews(self) -> list[dict[str, Any]]:
        statement: Select[tuple[FieldDefinitionReviewRecord]] = select(
            FieldDefinitionReviewRecord
        ).order_by(FieldDefinitionReviewRecord.created_at)
        with self._session_factory() as session:
            return [record.payload for record in session.scalars(statement)]

    def approve_field_definition_review(
        self,
        review_id: str,
        *,
        approved_field: FieldDefinition | None = None,
        review_note: str | None = None,
    ) -> dict[str, Any]:
        with self._session_factory.begin() as session:
            review = session.get(FieldDefinitionReviewRecord, review_id)
            if review is None:
                raise ReviewNotFound(review_id)
            if review.status != "pending":
                raise ReviewConflict("Field definition review is already completed.")

            proposal = session.get(
                FieldDefinitionProposalRecord,
                review.proposal_id,
            )
            if proposal is None:
                raise ReviewNotFound(review.proposal_id)

            original_field = FieldDefinition.model_validate(
                proposal.payload["proposed_field"]
            )
            selected_field = approved_field or original_field
            selected_field = selected_field.model_copy(
                update={"review_status": "approved"}
            )
            reviewed_at = datetime.now(timezone.utc)
            review_payload = {
                **review.payload,
                "status": "approved",
                "approved_field": selected_field.model_dump(mode="json"),
                "review_note": review_note,
                "reviewed_at": reviewed_at.isoformat(),
            }
            review.status = "approved"
            review.payload = review_payload
            review.reviewed_at = reviewed_at
            proposal.review_status = "approved"

            package = session.scalar(
                select(PolicyPackageRecord).where(
                    PolicyPackageRecord.run_id == proposal.run_id
                )
            )
            if package is not None:
                package.payload = _replace_policy_field(
                    package.payload,
                    old_key=original_field.key,
                    approved_field=selected_field,
                )
            return review_payload

    def reject_field_definition_review(
        self,
        review_id: str,
        *,
        review_note: str | None = None,
    ) -> dict[str, Any]:
        with self._session_factory.begin() as session:
            review = session.get(FieldDefinitionReviewRecord, review_id)
            if review is None:
                raise ReviewNotFound(review_id)
            if review.status != "pending":
                raise ReviewConflict("Field definition review is already completed.")

            proposal = session.get(
                FieldDefinitionProposalRecord,
                review.proposal_id,
            )
            if proposal is None:
                raise ReviewNotFound(review.proposal_id)

            reviewed_at = datetime.now(timezone.utc)
            review_payload = {
                **review.payload,
                "status": "rejected",
                "approved_field": None,
                "review_note": review_note,
                "reviewed_at": reviewed_at.isoformat(),
            }
            review.status = "rejected"
            review.payload = review_payload
            review.reviewed_at = reviewed_at
            proposal.review_status = "rejected"
            return review_payload

    def approve_policy_package(self, policy_id: str) -> dict[str, Any]:
        return self._set_policy_review_status(policy_id, "approved")

    def reject_policy_package(self, policy_id: str) -> dict[str, Any]:
        return self._set_policy_review_status(policy_id, "rejected")

    def _set_policy_review_status(
        self,
        policy_id: str,
        status: str,
    ) -> dict[str, Any]:
        with self._session_factory.begin() as session:
            package = session.get(PolicyPackageRecord, policy_id)
            if package is None:
                raise PolicyPackageNotFound(policy_id)
            if package.review_status != "pending":
                raise ReviewConflict("Policy package review is already completed.")

            if status == "approved":
                proposals = session.scalars(
                    select(FieldDefinitionProposalRecord).where(
                        FieldDefinitionProposalRecord.run_id == package.run_id
                    )
                ).all()
                if any(proposal.review_status != "approved" for proposal in proposals):
                    raise ReviewConflict(
                        "All field definition reviews must be approved before publish."
                    )

            reviewed_at = datetime.now(timezone.utc).isoformat()
            payload = deepcopy(package.payload)
            payload["review"] = {
                "status": status,
                "reviewed_at": reviewed_at,
            }
            package.review_status = status
            package.payload = payload
            return payload

    def list_approved_field_definitions(self) -> list[FieldDefinition]:
        statement: Select[tuple[FieldDefinitionReviewRecord]] = select(
            FieldDefinitionReviewRecord
        ).where(FieldDefinitionReviewRecord.status == "approved")
        definitions: dict[str, FieldDefinition] = {}
        with self._session_factory() as session:
            for record in session.scalars(statement):
                approved_field = record.payload.get("approved_field")
                if isinstance(approved_field, dict):
                    definition = FieldDefinition.model_validate(approved_field)
                    definitions[definition.key] = definition
        return list(definitions.values())

    def get_latest_approved_policy(
        self,
        policy_family_id: str,
    ) -> dict[str, Any] | None:
        statement: Select[tuple[PolicyPackageRecord]] = (
            select(PolicyPackageRecord)
            .where(
                PolicyPackageRecord.policy_family_id == policy_family_id,
                PolicyPackageRecord.review_status == "approved",
            )
            .order_by(PolicyPackageRecord.version.desc())
            .limit(1)
        )
        with self._session_factory() as session:
            record = session.scalar(statement)
            return record.payload if record is not None else None


def _notice_key(notice: SourceNotice) -> str:
    return f"{notice.source_board}:{notice.source_id}"


def _notice_record(notice: SourceNotice, notice_key: str) -> SourceNoticeRecord:
    return SourceNoticeRecord(
        notice_key=notice_key,
        source_id=notice.source_id,
        source_board=notice.source_board,
        source_url=notice.source_url,
        title=notice.title,
        published_at=notice.published_at,
        department=notice.department,
        payload=notice.model_dump(mode="json"),
    )


def _agent_run_record(agent_run: AgentRun, notice_key: str | None) -> AgentRunRecord:
    return AgentRunRecord(
        run_id=agent_run.run_id,
        notice_key=notice_key,
        notice_id=agent_run.notice_id,
        status=agent_run.status,
        review_required=agent_run.review_required,
        policy_id=agent_run.policy_id,
        payload=agent_run.model_dump(mode="json"),
    )


def _policy_package_record(
    run_id: str,
    package: dict[str, Any],
) -> PolicyPackageRecord:
    review = package.get("review")
    review_status = review.get("status") if isinstance(review, dict) else "pending"
    return PolicyPackageRecord(
        policy_id=str(package["policy_id"]),
        policy_family_id=str(package["policy_family_id"]),
        version=int(package["version"]),
        run_id=run_id,
        review_status=str(review_status),
        payload=package,
    )


def _proposal_record(
    run_id: str,
    proposal: FieldDefinitionProposal,
) -> FieldDefinitionProposalRecord:
    field_key = proposal.proposed_field.key
    return FieldDefinitionProposalRecord(
        proposal_id=f"{run_id}:{field_key}",
        run_id=run_id,
        field_key=field_key,
        review_status="pending",
        payload=proposal.model_dump(mode="json"),
    )


def _review_record(review: FieldDefinitionReview) -> FieldDefinitionReviewRecord:
    return FieldDefinitionReviewRecord(
        review_id=review.review_id,
        proposal_id=review.review_id,
        status=review.status,
        payload=review.model_dump(mode="json"),
        reviewed_at=review.reviewed_at,
    )


class ReviewNotFound(LookupError):
    pass


class PolicyPackageNotFound(LookupError):
    pass


class ReviewConflict(RuntimeError):
    pass


def _replace_policy_field(
    package: dict[str, Any],
    *,
    old_key: str,
    approved_field: FieldDefinition,
) -> dict[str, Any]:
    updated = deepcopy(package)
    fields = updated.get("required_profile_fields", [])
    replacement = approved_field.model_dump(mode="json")
    replaced_fields: list[dict[str, Any]] = []
    for field in fields:
        candidate = replacement if field.get("key") == old_key else field
        if not any(item.get("key") == candidate.get("key") for item in replaced_fields):
            replaced_fields.append(candidate)
    updated["required_profile_fields"] = replaced_fields
    updated["eligibility_rule"] = _replace_rule_field(
        updated.get("eligibility_rule"),
        old_key,
        approved_field.key,
    )
    for change in updated.get("changes", []):
        if change.get("field") == old_key:
            change["field"] = approved_field.key
            change["label"] = approved_field.label
    return updated


def _replace_rule_field(rule: Any, old_key: str, new_key: str) -> Any:
    if not isinstance(rule, dict):
        return rule
    updated = deepcopy(rule)
    if updated.get("field") == old_key:
        updated["field"] = new_key
    for operator in ("and", "or"):
        if isinstance(updated.get(operator), list):
            updated[operator] = [
                _replace_rule_field(child, old_key, new_key)
                for child in updated[operator]
            ]
    return updated
