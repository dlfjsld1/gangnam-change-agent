from app.agent.state import ChangeAgentState
from app.schemas.field_definition import FieldDefinition
from app.services.field_registry import FieldRegistry


def detect_unknown_field_definitions(
    state: ChangeAgentState,
    registry: FieldRegistry,
    candidate_fields: list[FieldDefinition],
) -> ChangeAgentState:
    proposals = [
        proposal
        for field_definition in candidate_fields
        if (
            proposal := registry.propose(
                field_definition,
                "새 조건의 원문 의미를 관리자 확인이 필요합니다.",
            )
        )
        is not None
    ]
    if not proposals:
        return state

    return {
        **state,
        "field_proposals": proposals,
        "review_required": True,
        "review_reason": "새 동적 필드 정의 검토 필요",
    }
