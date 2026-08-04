import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVED_POLICY_PATH = PROJECT_ROOT / "demo-data" / "approved-policy.json"


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


app = FastAPI(title="Gangnam Change Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=[],
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
