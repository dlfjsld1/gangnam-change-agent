from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FieldDataType = Literal["boolean", "enum", "number", "date", "string", "list"]
Sensitivity = Literal["low", "medium", "high"]
FieldReviewStatus = Literal["pending", "approved", "rejected"]


class FieldOption(BaseModel):
    value: str | int | float | bool
    label: str


class FieldDefinition(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    data_type: FieldDataType
    allowed_values: list[FieldOption] = []
    question: str
    sensitivity: Sensitivity
    validity_days: int | None = Field(default=None, ge=1)
    review_status: FieldReviewStatus


class FieldDefinitionProposal(BaseModel):
    proposed_field: FieldDefinition
    review_required: Literal[True] = True
    review_reason: str


class FieldDefinitionReview(BaseModel):
    review_id: str
    proposal: FieldDefinitionProposal
    status: Literal["pending", "approved", "rejected"] = "pending"
    approved_field: FieldDefinition | None = None
    review_note: str | None = None
    reviewed_at: datetime | None = None


class ProfileFieldCatalogItem(BaseModel):
    field_definition: FieldDefinition
    onboarding_group: Literal["core", "optional"]
    eligibility_usable: bool
    display_order: int = Field(ge=0)
