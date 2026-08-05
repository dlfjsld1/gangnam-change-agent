from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent_run import AgentRun
from app.schemas.field_definition import FieldDataType, Sensitivity


RuleOperator = Literal["equals", "in", "between", "contains", "exists"]


class PolicyConditionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1)
    operator: RuleOperator
    scalar_value: str | None
    values: list[str]
    minimum: float | None
    maximum: float | None
    data_type: FieldDataType
    question: str = Field(min_length=1)
    sensitivity: Sensitivity
    validity_days: int | None
    evidence_quote: str = Field(min_length=1)
    document_name: str = Field(min_length=1)


class PolicyActionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    priority: int = Field(ge=1)
    evidence_quote: str = Field(min_length=1)
    document_name: str = Field(min_length=1)


class PolicyDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1)
    effective_at: date | None
    deadline_at: date | None
    summary: str = Field(min_length=1)
    conditions: list[PolicyConditionDraft]
    required_actions: list[PolicyActionDraft]


class EvidenceIssue(BaseModel):
    code: str
    document_name: str
    message: str


class PolicyBuildResult(BaseModel):
    policy_package: dict[str, object] | None
    agent_run: AgentRun
    evidence_issues: list[EvidenceIssue]
