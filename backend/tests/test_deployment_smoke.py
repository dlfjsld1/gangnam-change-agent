from typing import Any

import pytest

from scripts.smoke_agent_review_publish import run_smoke


class FakeSmokeApi:
    def __init__(self, *, include_package: bool = True) -> None:
        self.include_package = include_package
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append(("POST", path, payload))
        if path == "/api/agent-runs":
            return {
                "agent_run": {"run_id": "run-1"},
                "policy_package": (
                    {"policy_id": "policy-1"} if self.include_package else None
                ),
                "field_definition_reviews": [{"review_id": "run-1:new_condition"}],
            }
        if path.endswith("/approve") and path.startswith(
            "/api/field-definition-reviews/"
        ):
            return {"status": "approved"}
        if path == "/api/policy-packages/policy-1/approve":
            return {"review": {"status": "approved"}}
        raise AssertionError(f"Unexpected POST {path}")

    def get(self, path: str) -> Any:
        self.calls.append(("GET", path, None))
        if path == "/api/policy-packages/policy-1":
            return {"review": {"status": "approved"}}
        raise AssertionError(f"Unexpected GET {path}")


def test_smoke_runs_agent_review_publish_and_public_read() -> None:
    client = FakeSmokeApi()

    result = run_smoke(
        client,
        notice_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        previous_policy_id="previous-policy",
    )

    assert result == {
        "run_id": "run-1",
        "policy_id": "policy-1",
        "approved_field_reviews": ["run-1:new_condition"],
        "published_status": "approved",
    }
    assert client.calls == [
        (
            "POST",
            "/api/agent-runs",
            {
                "notice_url": "https://www.gangnam.go.kr/notice/view.do?id=61922",
                "previous_policy_id": "previous-policy",
            },
        ),
        (
            "POST",
            "/api/field-definition-reviews/run-1%3Anew_condition/approve",
            {"review_note": "deployment smoke approval"},
        ),
        ("POST", "/api/policy-packages/policy-1/approve", None),
        ("GET", "/api/policy-packages/policy-1", None),
    ]


def test_smoke_stops_when_agent_has_no_policy_package() -> None:
    with pytest.raises(RuntimeError, match="did not produce"):
        run_smoke(
            FakeSmokeApi(include_package=False),
            notice_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        )
