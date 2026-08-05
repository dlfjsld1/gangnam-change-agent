from copy import deepcopy
from typing import Any


PolicyPackage = dict[str, Any]


def apply_policy_diff(
    previous: PolicyPackage | None,
    current: PolicyPackage,
) -> PolicyPackage:
    result = deepcopy(current)
    if previous is None:
        result["changes"] = []
        return result

    family_id = str(previous["policy_family_id"])
    version = int(previous["version"]) + 1
    result["policy_family_id"] = family_id
    result["version"] = version
    result["policy_id"] = f"{family_id}-v{version}"
    result["changes"] = _condition_changes(previous, result)
    result["changes"].extend(_metadata_changes(previous, result))
    return result


def _condition_changes(
    previous: PolicyPackage,
    current: PolicyPackage,
) -> list[dict[str, object]]:
    before_by_field = _rules_by_field(previous.get("eligibility_rule", {}))
    after_by_field = _rules_by_field(current.get("eligibility_rule", {}))
    labels = _field_labels(previous, current)
    evidence_by_field = _evidence_by_field(current)
    changes: list[dict[str, object]] = []

    for field in sorted(before_by_field.keys() | after_by_field.keys()):
        before_rules = before_by_field.get(field, [])
        after_rules = after_by_field.get(field, [])
        if before_rules == after_rules:
            continue
        before = _compact_rules(before_rules)
        after = _compact_rules(after_rules)
        change_type = _change_type(before_rules, after_rules)
        changes.append(
            {
                "change_id": f"change-{field}",
                "field": field,
                "label": labels.get(field, field),
                "before": before,
                "after": after,
                "change_type": change_type,
                "impact_hint": _impact_hint(change_type),
                "evidence_id": evidence_by_field.get(field)
                or _first_evidence_id(current),
            }
        )
    return changes


def _metadata_changes(
    previous: PolicyPackage,
    current: PolicyPackage,
) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []
    for field, label in (
        ("effective_at", "시행일"),
        ("deadline_at", "신청 마감일"),
    ):
        before = previous.get(field)
        after = current.get(field)
        if before == after:
            continue
        changes.append(
            {
                "change_id": f"change-{field}",
                "field": field,
                "label": label,
                "before": before,
                "after": after,
                "change_type": "changed",
                "impact_hint": f"{label}이 변경되었습니다.",
                "evidence_id": _first_evidence_id(current),
            }
        )

    before_actions = _action_labels(previous)
    after_actions = _action_labels(current)
    if before_actions != after_actions:
        changes.append(
            {
                "change_id": "change-required_actions",
                "field": "required_actions",
                "label": "필요한 행동",
                "before": before_actions,
                "after": after_actions,
                "change_type": "changed",
                "impact_hint": "신청 또는 확인 절차가 변경되었습니다.",
                "evidence_id": _first_evidence_id(current),
            }
        )
    return changes


def _rules_by_field(rule: object) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for leaf in _leaf_rules(rule):
        field = str(leaf["field"])
        grouped.setdefault(field, []).append(leaf)
    return grouped


def _leaf_rules(rule: object) -> list[dict[str, object]]:
    if not isinstance(rule, dict):
        return []
    for branch in ("and", "or"):
        children = rule.get(branch)
        if isinstance(children, list):
            return [leaf for child in children for leaf in _leaf_rules(child)]
    if "field" in rule and "operator" in rule:
        return [deepcopy(rule)]
    return []


def _field_labels(
    previous: PolicyPackage,
    current: PolicyPackage,
) -> dict[str, str]:
    labels: dict[str, str] = {}
    for package in (previous, current):
        for definition in package.get("required_profile_fields", []):
            if isinstance(definition, dict):
                labels[str(definition.get("key", ""))] = str(
                    definition.get("label", definition.get("key", ""))
                )
    return labels


def _evidence_by_field(package: PolicyPackage) -> dict[str, str]:
    leaves = _leaf_rules(package.get("eligibility_rule", {}))
    evidence = package.get("evidence", [])
    mapped: dict[str, str] = {}
    for index, leaf in enumerate(leaves):
        if index >= len(evidence) or not isinstance(evidence[index], dict):
            break
        mapped.setdefault(str(leaf["field"]), str(evidence[index]["evidence_id"]))
    return mapped


def _first_evidence_id(package: PolicyPackage) -> str:
    evidence = package.get("evidence", [])
    if not evidence or not isinstance(evidence[0], dict):
        raise ValueError("Policy diff requires current evidence")
    return str(evidence[0]["evidence_id"])


def _compact_rules(rules: list[dict[str, object]]) -> object:
    if not rules:
        return None
    return rules[0] if len(rules) == 1 else rules


def _change_type(
    before: list[dict[str, object]],
    after: list[dict[str, object]],
) -> str:
    if not before:
        return "added"
    if not after:
        return "removed"
    if len(before) == len(after) == 1:
        return _single_rule_change_type(before[0], after[0])
    return "changed"


def _single_rule_change_type(
    before: dict[str, object],
    after: dict[str, object],
) -> str:
    if before.get("operator") != after.get("operator"):
        return "changed"
    if before.get("operator") == "between":
        before_min, before_max = before.get("min"), before.get("max")
        after_min, after_max = after.get("min"), after.get("max")
        if all(
            isinstance(value, (int, float))
            for value in (before_min, before_max, after_min, after_max)
        ):
            if after_min <= before_min and after_max >= before_max:
                return "expanded"
            if after_min >= before_min and after_max <= before_max:
                return "narrowed"
    if before.get("operator") == "in":
        before_values = set(before.get("value", []))
        after_values = set(after.get("value", []))
        if after_values > before_values:
            return "expanded"
        if after_values < before_values:
            return "narrowed"
    return "changed"


def _impact_hint(change_type: str) -> str:
    return {
        "added": "새로운 판정 조건이 추가되었습니다.",
        "removed": "기존 판정 조건이 제거되었습니다.",
        "expanded": "이 조건을 충족하는 시민 범위가 넓어질 수 있습니다.",
        "narrowed": "이 조건을 충족하는 시민 범위가 좁아질 수 있습니다.",
    }.get(change_type, "판정 조건이 변경되었습니다.")


def _action_labels(package: PolicyPackage) -> list[str]:
    return [
        str(action["label"])
        for action in package.get("required_actions", [])
        if isinstance(action, dict) and "label" in action
    ]
