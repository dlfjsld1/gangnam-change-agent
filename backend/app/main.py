import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas.field_definition import FieldDefinition
from app.services.state_storage import load_state, save_state


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVED_POLICY_PATH = PROJECT_ROOT / "demo-data" / "approved-policy.json"
FIELD_PROPOSAL_PATH = PROJECT_ROOT / "demo-data" / "field-definition-proposal.json"


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def _load_approved_policy_package() -> dict[str, object]:
    policy_package = _load_json(APPROVED_POLICY_PATH)

    review = policy_package.get("review")
    if not isinstance(review, dict) or review.get("status") != "approved":
        raise RuntimeError("Approved policy fixture must have approved review status.")

    return policy_package


_approved_policy = _load_approved_policy_package()
_proposal = _load_json(FIELD_PROPOSAL_PATH)

# Seed data is stored once, then shared through SQLite or PostgreSQL.
_default_reviews: list[dict[str, object]] = [
    {
        "review_id": "review-demo-001",
        "run_id": "run-demo-001",
        "proposal": _proposal,
        "status": "pending",
        "approved_field": None,
        "review_note": None,
        "reviewed_at": None,
        "evidence": _approved_policy["evidence"][0],
        "canonical_candidates": [_approved_policy["required_profile_fields"][2]],
    }
]
_default_agent_runs: dict[str, dict[str, object]] = {
    "run-demo-001": {
        "run_id": "run-demo-001",
        "notice_id": "notice-demo-001",
        "status": "review_required",
        "node_logs": [
            {
                "node": "validate_evidence",
                "status": "completed",
                "message": "새 자격 조건에 관리자 검토가 필요합니다.",
            }
        ],
        "review_required": True,
        "review_reason": _proposal["review_reason"],
        "unresolved_fields": ["military_service_status"],
        "policy_id": "demo-policy-v2",
    }
}


class ReviewEdit(BaseModel):
    approved_field: FieldDefinition


def _cors_origins() -> list[str]:
    configured_origins = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174",
    )
    return [
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    ]


app = FastAPI(title="Gangnam Change Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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


def _get_review(
    review_id: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    reviews = load_state("field_definition_reviews", _default_reviews)
    assert isinstance(reviews, list)
    review = next((item for item in reviews if item["review_id"] == review_id), None)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return reviews, review


def _complete_review(
    reviews: list[dict[str, object]],
    review: dict[str, object],
    status: Literal["approved", "rejected"],
    approved_field: FieldDefinition | None = None,
) -> dict[str, object]:
    if status == "approved":
        field = approved_field or FieldDefinition.model_validate(
            review["proposal"]["proposed_field"]
        )
        review["approved_field"] = field.model_copy(
            update={"review_status": "approved"}
        ).model_dump()
    else:
        review["approved_field"] = None

    review["status"] = status
    review["review_note"] = "관리자 검토 완료"
    review["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    agent_runs = load_state("agent_runs", _default_agent_runs)
    assert isinstance(agent_runs, dict)
    run = agent_runs[review["run_id"]]
    run.update(
        status="completed",
        review_required=False,
        review_reason=None,
        unresolved_fields=[],
    )
    save_state("field_definition_reviews", reviews)
    save_state("agent_runs", agent_runs)
    return review


@app.get("/api/field-definition-reviews")
def list_field_definition_reviews() -> list[dict[str, object]]:
    reviews = load_state("field_definition_reviews", _default_reviews)
    assert isinstance(reviews, list)
    return reviews


@app.post("/api/field-definition-reviews/{review_id}/edit")
def edit_field_definition_review(
    review_id: str,
    request: ReviewEdit,
) -> dict[str, object]:
    reviews, review = _get_review(review_id)
    return _complete_review(reviews, review, "approved", request.approved_field)


@app.post("/api/field-definition-reviews/{review_id}/{decision}")
def decide_field_definition_review(
    review_id: str,
    decision: Literal["approve", "reject"],
) -> dict[str, object]:
    reviews, review = _get_review(review_id)
    return _complete_review(
        reviews,
        review,
        "approved" if decision == "approve" else "rejected",
    )


@app.get("/api/agent-runs/{run_id}")
def get_agent_run(run_id: str) -> dict[str, object]:
    agent_runs = load_state("agent_runs", _default_agent_runs)
    assert isinstance(agent_runs, dict)
    run = agent_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    return run
