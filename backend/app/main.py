from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAIError

from app.database import Database
from app.repositories.agent_repository import (
    AgentRepository,
    PolicyPackageNotFound,
    ReviewConflict,
    ReviewNotFound,
)
from app.schemas.agent_api import AgentRunRequest, AgentRunResponse
from app.schemas.review_api import ApproveFieldReviewRequest, RejectReviewRequest
from app.services.agent_execution import AgentExecutionService, PreviousPolicyNotFound
from app.services.attachment_archive import (
    AttachmentArchiveUnavailable,
    AttachmentPrivacyRejected,
    configured_public_attachment_archive,
)
from app.services.policy_publish import PolicyPublishService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVED_POLICY_PATH = PROJECT_ROOT / "demo-data" / "approved-policy.json"
database = Database()
agent_repository = AgentRepository(database.session_factory)
public_attachment_archive = configured_public_attachment_archive()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    database.create_schema()
    yield
    database.engine.dispose()


def _load_approved_policy_package() -> dict[str, object]:
    with APPROVED_POLICY_PATH.open(encoding="utf-8") as policy_file:
        policy_package: dict[str, object] = json.load(policy_file)

    review = policy_package.get("review")
    if not isinstance(review, dict) or review.get("status") != "approved":
        raise RuntimeError("Approved policy fixture must have approved review status.")

    return policy_package


def _cors_origins() -> list[str]:
    configured_origins = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174",
    )
    return [
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    ]


app = FastAPI(title="Gangnam Change Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_agent_repository() -> AgentRepository:
    return agent_repository


def get_agent_execution_service(
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> AgentExecutionService:
    return AgentExecutionService(repository)


def get_policy_publish_service(
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> PolicyPublishService:
    return PolicyPublishService(repository, public_attachment_archive)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/policy-packages")
def list_policy_packages(
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> list[dict[str, object]]:
    packages = repository.list_approved_policy_packages()
    return packages or [_load_approved_policy_package()]


@app.get("/api/policy-packages/{policy_id}")
def get_policy_package(
    policy_id: str,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    stored_package = repository.get_approved_policy_package(policy_id)
    if stored_package is not None:
        return stored_package
    if repository.list_approved_policy_packages():
        raise HTTPException(status_code=404, detail="Policy package not found.")
    policy_package = _load_approved_policy_package()
    if policy_package["policy_id"] != policy_id:
        raise HTTPException(status_code=404, detail="Policy package not found.")

    return policy_package


@app.get("/api/field-definition-reviews")
def list_field_definition_reviews(
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
    status: Literal["pending", "approved", "rejected"] | None = None,
    run_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[dict[str, object]]:
    return repository.list_field_definition_reviews(
        status=status,
        run_id=run_id,
        limit=limit,
    )


@app.get("/api/admin/policy-packages")
def list_admin_policy_packages(
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
    review_status: Literal["pending", "approved", "rejected"] | None = None,
    run_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[dict[str, object]]:
    return repository.list_admin_policy_packages(
        review_status=review_status,
        run_id=run_id,
        limit=limit,
    )


@app.get("/api/admin/policy-packages/{policy_id}")
def get_admin_policy_package(
    policy_id: str,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    package = repository.get_policy_package(policy_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Policy package not found.")
    return package


@app.get("/api/admin/agent-runs/{run_id}")
def get_admin_agent_run_detail(
    run_id: str,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    detail = repository.get_agent_run_detail(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    return detail


@app.post("/api/field-definition-reviews/{review_id}/approve")
def approve_field_definition_review(
    review_id: str,
    request: ApproveFieldReviewRequest,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    try:
        return repository.approve_field_definition_review(
            review_id,
            approved_field=request.approved_field,
            review_note=request.review_note,
        )
    except ReviewNotFound as error:
        raise HTTPException(
            status_code=404, detail="Field review not found."
        ) from error
    except ReviewConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/field-definition-reviews/{review_id}/reject")
def reject_field_definition_review(
    review_id: str,
    request: RejectReviewRequest,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    try:
        return repository.reject_field_definition_review(
            review_id,
            review_note=request.review_note,
        )
    except ReviewNotFound as error:
        raise HTTPException(
            status_code=404, detail="Field review not found."
        ) from error
    except ReviewConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/policy-packages/{policy_id}/approve")
def approve_policy_package(
    policy_id: str,
    service: Annotated[PolicyPublishService, Depends(get_policy_publish_service)],
) -> dict[str, object]:
    try:
        return service.approve(policy_id)
    except PolicyPackageNotFound as error:
        raise HTTPException(
            status_code=404, detail="Policy package not found."
        ) from error
    except ReviewConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except AttachmentPrivacyRejected as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except AttachmentArchiveUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/policy-packages/{policy_id}/reject")
def reject_policy_package(
    policy_id: str,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    try:
        return repository.reject_policy_package(policy_id)
    except PolicyPackageNotFound as error:
        raise HTTPException(
            status_code=404, detail="Policy package not found."
        ) from error
    except ReviewConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/agent-runs", response_model=AgentRunResponse, status_code=201)
def create_agent_run(
    request: AgentRunRequest,
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
) -> AgentRunResponse:
    try:
        return service.run(
            request.notice_url,
            previous_policy_id=request.previous_policy_id,
        )
    except PreviousPolicyNotFound as error:
        raise HTTPException(
            status_code=404,
            detail="Approved previous policy package not found.",
        ) from error
    except OpenAIError as error:
        raise HTTPException(
            status_code=503,
            detail="Agent runtime is unavailable.",
        ) from error


@app.get("/api/agent-runs")
def list_agent_runs(
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
    status: Literal[
        "queued",
        "running",
        "completed",
        "failed",
        "review_required",
    ]
    | None = None,
    review_required: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[dict[str, object]]:
    return repository.list_agent_runs(
        status=status,
        review_required=review_required,
        limit=limit,
    )


@app.get("/api/agent-runs/{run_id}")
def get_agent_run(
    run_id: str,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    agent_run = repository.get_agent_run(run_id)
    if agent_run is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    return agent_run
