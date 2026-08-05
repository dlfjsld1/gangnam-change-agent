from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAIError

from app.database import Database
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent_api import AgentRunRequest, AgentRunResponse
from app.services.agent_execution import AgentExecutionService, PreviousPolicyNotFound


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVED_POLICY_PATH = PROJECT_ROOT / "demo-data" / "approved-policy.json"
database = Database()
agent_repository = AgentRepository(database.session_factory)


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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/policy-packages")
def list_policy_packages() -> list[dict[str, object]]:
    return [_load_approved_policy_package()]


@app.get("/api/policy-packages/{policy_id}")
def get_policy_package(policy_id: str) -> dict[str, object]:
    policy_package = _load_approved_policy_package()
    if policy_package["policy_id"] != policy_id:
        raise HTTPException(status_code=404, detail="Policy package not found.")

    return policy_package


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


@app.get("/api/agent-runs/{run_id}")
def get_agent_run(
    run_id: str,
    repository: Annotated[AgentRepository, Depends(get_agent_repository)],
) -> dict[str, object]:
    agent_run = repository.get_agent_run(run_id)
    if agent_run is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    return agent_run
