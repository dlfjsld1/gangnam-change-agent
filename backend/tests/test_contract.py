import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "docs" / "contracts" / "policy-package.schema.json"
APPROVED_POLICY_PATH = PROJECT_ROOT / "demo-data" / "approved-policy.json"
PENDING_POLICY_PATH = PROJECT_ROOT / "demo-data" / "pending-policy.json"


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as source_file:
        return json.load(source_file)


def test_policy_fixtures_include_all_contract_fields() -> None:
    schema = _load_json(SCHEMA_PATH)
    required_fields = set(schema["required"])

    for fixture_path in [APPROVED_POLICY_PATH, PENDING_POLICY_PATH]:
        fixture = _load_json(fixture_path)
        assert required_fields.issubset(fixture)


def test_approved_fixture_evidence_matches_change_reference() -> None:
    fixture = _load_json(APPROVED_POLICY_PATH)
    evidence_ids = {item["evidence_id"] for item in fixture["evidence"]}
    change_evidence_ids = {item["evidence_id"] for item in fixture["changes"]}

    assert change_evidence_ids.issubset(evidence_ids)
    assert fixture["review"]["status"] == "approved"
