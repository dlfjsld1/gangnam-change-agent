from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SourceNoticeRecord(Base):
    __tablename__ = "source_notices"

    notice_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    source_board: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    published_at: Mapped[date] = mapped_column(Date)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )


class AgentRunRecord(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    notice_key: Mapped[str | None] = mapped_column(
        ForeignKey("source_notices.notice_key"), nullable=True, index=True
    )
    notice_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    review_required: Mapped[bool] = mapped_column(Boolean, index=True)
    policy_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )


class PolicyPackageRecord(Base):
    __tablename__ = "policy_packages"
    __table_args__ = (
        UniqueConstraint("policy_family_id", "version", name="uq_policy_version"),
    )

    policy_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    policy_family_id: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[int] = mapped_column(Integer)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), index=True)
    review_status: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )


class CanonicalFieldDefinitionRecord(Base):
    __tablename__ = "canonical_field_definitions"

    field_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    onboarding_group: Mapped[str] = mapped_column(String(32), index=True)
    eligibility_usable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    display_order: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )


class FieldDefinitionProposalRecord(Base):
    __tablename__ = "field_definition_proposals"

    proposal_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), index=True)
    field_key: Mapped[str] = mapped_column(String(128), index=True)
    review_status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )


class FieldDefinitionReviewRecord(Base):
    __tablename__ = "field_definition_reviews"

    review_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("field_definition_proposals.proposal_id"), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now
    )
