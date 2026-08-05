from app.schemas.field_definition import FieldDefinition
from app.services.field_registry import FieldRegistry


def _field(
    key: str,
    label: str = "거주 지역",
    data_type: str = "string",
    review_status: str = "approved",
) -> FieldDefinition:
    return FieldDefinition(
        key=key,
        label=label,
        data_type=data_type,
        question="현재 거주 지역은 어디인가요?",
        sensitivity="medium",
        review_status=review_status,
    )


def test_exact_key_match_wins_over_label_match() -> None:
    exact = _field("residence", label="거주지")
    result = FieldRegistry([exact]).resolve_fields(
        [_field("residence", label="거주 지역")]
    )

    assert result.resolved_fields == [exact]
    assert result.field_proposals == []
    assert result.review_required is False


def test_normalized_label_and_data_type_reuses_canonical_field() -> None:
    residence = _field("residence", label="거주-지역")
    result = FieldRegistry([residence]).resolve_fields([_field("residence_alias")])

    assert result.resolved_fields == [residence]
    assert result.field_proposals == []
    assert result.unresolved_fields == []


def test_ambiguous_label_creates_proposal_instead_of_reusing_field() -> None:
    result = FieldRegistry(
        [_field("residence_a"), _field("residence_b")]
    ).resolve_fields([_field("residence_candidate")])

    assert result.resolved_fields[0].key == "residence_candidate"
    assert len(result.field_proposals) == 1
    assert result.unresolved_fields == ["residence_candidate"]
    assert result.review_required is True


def test_pending_or_rejected_match_is_unresolved_without_duplicate_proposal() -> None:
    pending = _field("residence", review_status="pending")
    result = FieldRegistry([pending]).resolve_fields([_field("residence_alias")])

    assert result.resolved_fields == [pending]
    assert result.field_proposals == []
    assert result.unresolved_fields == ["residence"]


def test_same_unknown_field_creates_one_proposal_per_run() -> None:
    result = FieldRegistry().resolve_fields(
        [_field("residence_one"), _field("residence_two", label="거주-지역")]
    )

    assert len(result.field_proposals) == 1
    assert [field.key for field in result.resolved_fields] == [
        "residence_one",
        "residence_one",
    ]
    assert result.unresolved_fields == ["residence_one"]
