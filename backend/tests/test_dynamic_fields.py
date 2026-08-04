from app.agent.mock_graph import detect_unknown_field_definitions
from app.schemas.field_definition import FieldDefinition
from app.services.field_registry import FieldRegistry


def test_new_field_creates_review_required_proposal() -> None:
    military_status = FieldDefinition(
        key="military_service_status",
        label="병역 이행 상태",
        data_type="enum",
        question="병역 의무를 이행하셨나요?",
        sensitivity="medium",
        review_status="approved",
    )

    state = detect_unknown_field_definitions({}, FieldRegistry(), [military_status])

    assert state["review_required"] is True
    assert state["field_proposals"][0].proposed_field.review_status == "pending"


def test_existing_field_does_not_create_proposal() -> None:
    residence = FieldDefinition(
        key="residence",
        label="거주 지역",
        data_type="string",
        question="현재 거주 지역은 어디인가요?",
        sensitivity="medium",
        review_status="approved",
    )

    state = detect_unknown_field_definitions(
        {},
        FieldRegistry([residence]),
        [residence],
    )

    assert "field_proposals" not in state
