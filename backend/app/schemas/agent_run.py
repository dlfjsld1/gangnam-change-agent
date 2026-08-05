from typing import Literal

from pydantic import BaseModel


AgentRunStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "review_required",
]
NodeLogStatus = Literal["started", "completed", "failed"]


class AgentNodeLog(BaseModel):
    node: str
    status: NodeLogStatus
    message: str


class AgentRun(BaseModel):
    run_id: str
    notice_id: str
    status: AgentRunStatus
    node_logs: list[AgentNodeLog]
    review_required: bool
    review_reason: str | None
    unresolved_fields: list[str]
    policy_id: str | None = None
