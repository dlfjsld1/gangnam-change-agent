from collections.abc import Iterable

from app.schemas.field_definition import FieldDefinition, FieldDefinitionProposal


class FieldRegistry:
    def __init__(self, definitions: Iterable[FieldDefinition] = ()) -> None:
        self._definitions = {definition.key: definition for definition in definitions}

    def find(self, key: str) -> FieldDefinition | None:
        return self._definitions.get(key)

    def propose(
        self,
        definition: FieldDefinition,
        review_reason: str,
    ) -> FieldDefinitionProposal | None:
        if self.find(definition.key) is not None:
            return None

        return FieldDefinitionProposal(
            proposed_field=definition.model_copy(update={"review_status": "pending"}),
            review_reason=review_reason,
        )
