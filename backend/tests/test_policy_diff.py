from copy import deepcopy
from json import loads
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from app.services.policy_diff import apply_policy_diff


PROJECT_ROOT = Path(__file__).parents[2]
CONTRACTS_DIR = PROJECT_ROOT / "docs" / "contracts"
APPROVED_POLICY = loads(
    (PROJECT_ROOT / "demo-data" / "approved-policy.json").read_text("utf-8")
)


def _validate_policy_package(package: dict[str, object]) -> None:
    schemas = [
        loads(path.read_text("utf-8")) for path in CONTRACTS_DIR.glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(item for item in schemas if item["title"] == "PolicyPackage")
    Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(package)


def test_diff_inherits_family_and_detects_expanded_condition_and_metadata() -> None:
    previous = deepcopy(APPROVED_POLICY)
    current = deepcopy(APPROVED_POLICY)
    current["policy_id"] = "new-notice-v1"
    current["policy_family_id"] = "new-notice"
    current["version"] = 1
    current["eligibility_rule"]["and"][1]["max"] = 42
    current["deadline_at"] = "2026-10-01"
    current["required_actions"].append(
        {"action_id": "visit", "label": "주민센터 방문", "priority": 3}
    )

    result = apply_policy_diff(previous, current)

    assert result["policy_family_id"] == "demo-policy"
    assert result["version"] == 3
    assert result["policy_id"] == "demo-policy-v3"
    changes = {change["field"]: change for change in result["changes"]}
    assert changes["age"]["change_type"] == "expanded"
    assert changes["deadline_at"]["after"] == "2026-10-01"
    assert changes["required_actions"]["after"][-1] == "주민센터 방문"
    evidence_ids = {item["evidence_id"] for item in result["evidence"]}
    assert {item["evidence_id"] for item in result["changes"]} <= evidence_ids
    _validate_policy_package(result)


def test_diff_handles_recursive_rules_and_added_or_removed_fields() -> None:
    previous = deepcopy(APPROVED_POLICY)
    current = deepcopy(APPROVED_POLICY)
    previous["eligibility_rule"] = {
        "or": [
            {"field": "age", "operator": "between", "min": 19, "max": 34},
            {
                "and": [
                    {
                        "field": "residence",
                        "operator": "equals",
                        "value": "강남구",
                    },
                    {
                        "field": "employment_status",
                        "operator": "equals",
                        "value": "unemployed",
                    },
                ]
            },
        ]
    }
    current["eligibility_rule"] = {
        "or": [
            {"field": "age", "operator": "between", "min": 19, "max": 39},
            {
                "field": "military_service_status",
                "operator": "equals",
                "value": "completed",
            },
        ]
    }

    result = apply_policy_diff(previous, current)
    changes = {change["field"]: change for change in result["changes"]}

    assert changes["age"]["change_type"] == "expanded"
    assert changes["residence"]["change_type"] == "removed"
    assert changes["employment_status"]["change_type"] == "removed"
    assert changes["military_service_status"]["change_type"] == "added"


def test_first_policy_keeps_version_and_has_no_changes() -> None:
    current = deepcopy(APPROVED_POLICY)

    result = apply_policy_diff(None, current)

    assert result["policy_id"] == current["policy_id"]
    assert result["version"] == current["version"]
    assert result["changes"] == []
