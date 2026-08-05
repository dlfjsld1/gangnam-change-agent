from pydantic import BaseModel, ConfigDict, Field

from app.schemas.field_definition import FieldDefinition


class ApproveFieldReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_field: FieldDefinition | None = None
    review_note: str | None = Field(default=None, min_length=1)


class RejectReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_note: str | None = Field(default=None, min_length=1)
