from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent_run import AgentRun


class NoticeDiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_new_notices: int = Field(default=1, ge=1, le=5)


class NoticeDiscoveryResponse(BaseModel):
    discovered_count: int
    already_processed_count: int
    processed_runs: list[AgentRun]
