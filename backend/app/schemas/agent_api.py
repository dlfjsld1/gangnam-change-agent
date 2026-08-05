from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.agent_run import AgentRun
from app.schemas.field_definition import FieldDefinitionProposal, FieldDefinitionReview
from app.schemas.policy_extraction import EvidenceIssue
from app.tools.scrapling_adapter import ALLOWED_SOURCE_HOSTS


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notice_url: str = Field(min_length=1)
    previous_policy_id: str | None = Field(default=None, min_length=1)

    @field_validator("notice_url")
    @classmethod
    def validate_notice_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
            raise ValueError("notice_url must use an approved Gangnam HTTPS host")
        return value


class AgentRunResponse(BaseModel):
    agent_run: AgentRun
    policy_package: dict[str, object] | None
    field_definition_proposals: list[FieldDefinitionProposal]
    field_definition_reviews: list[FieldDefinitionReview]
    evidence_issues: list[EvidenceIssue]
