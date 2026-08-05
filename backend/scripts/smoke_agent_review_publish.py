import json
import os
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class SmokeApi(Protocol):
    def get(self, path: str) -> Any: ...

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any: ...


class JsonApiClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, payload or {})

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self._base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=300) as response:  # noqa: S310
                return json.load(response)
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"{method} {path} failed with HTTP {error.code}: {body}"
            ) from error


def run_smoke(
    client: SmokeApi,
    *,
    notice_url: str,
    previous_policy_id: str | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {"notice_url": notice_url}
    if previous_policy_id:
        request["previous_policy_id"] = previous_policy_id
    execution = client.post("/api/agent-runs", request)
    agent_run = execution["agent_run"]
    package = execution.get("policy_package")
    if not isinstance(package, dict):
        raise RuntimeError("Agent execution did not produce a PolicyPackage.")

    approved_reviews: list[str] = []
    for review in execution.get("field_definition_reviews", []):
        review_id = str(review["review_id"])
        client.post(
            f"/api/field-definition-reviews/{quote(review_id, safe='')}/approve",
            {"review_note": "deployment smoke approval"},
        )
        approved_reviews.append(review_id)

    policy_id = str(package["policy_id"])
    published = client.post(f"/api/policy-packages/{quote(policy_id, safe='')}/approve")
    public_package = client.get(f"/api/policy-packages/{quote(policy_id, safe='')}")
    if published.get("review", {}).get("status") != "approved":
        raise RuntimeError("Policy approval did not return approved status.")
    if public_package.get("review", {}).get("status") != "approved":
        raise RuntimeError("Citizen API did not publish the approved policy.")

    return {
        "run_id": agent_run["run_id"],
        "policy_id": policy_id,
        "approved_field_reviews": approved_reviews,
        "published_status": public_package["review"]["status"],
    }


def main() -> None:
    if os.getenv("SMOKE_ALLOW_MUTATIONS", "").lower() != "true":
        raise SystemExit(
            "Set SMOKE_ALLOW_MUTATIONS=true only for an isolated deployment smoke DB."
        )
    notice_url = os.getenv("SMOKE_NOTICE_URL")
    if not notice_url:
        raise SystemExit("SMOKE_NOTICE_URL is required.")

    result = run_smoke(
        JsonApiClient(os.getenv("BACKEND_BASE_URL", "http://localhost:8000")),
        notice_url=notice_url,
        previous_policy_id=os.getenv("SMOKE_PREVIOUS_POLICY_ID"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
