from typing import TypedDict

from app.schemas.field_definition import FieldDefinitionProposal


class ChangeAgentState(TypedDict, total=False):
    notice_url: str
    html_content: str
    extracted_conditions: list[dict[str, object]]
    field_proposals: list[FieldDefinitionProposal]
    review_required: bool
    review_reason: str
    policy_package: dict[str, object]
