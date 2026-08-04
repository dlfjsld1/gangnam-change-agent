from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_policy_packages_returns_only_approved_fixture() -> None:
    response = client.get("/api/policy-packages")

    assert response.status_code == 200
    policy_packages = response.json()
    assert len(policy_packages) == 1
    assert policy_packages[0]["review"]["status"] == "approved"


def test_policy_package_can_be_loaded_by_id() -> None:
    response = client.get("/api/policy-packages/demo-policy-v2")

    assert response.status_code == 200
    assert response.json()["policy_id"] == "demo-policy-v2"
