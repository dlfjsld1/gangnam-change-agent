from collections.abc import Iterable
from dataclasses import dataclass

from app.schemas.field_definition import FieldDefinition, FieldDefinitionProposal


@dataclass(frozen=True)
class FieldResolutionResult:
    resolved_fields: list[FieldDefinition]
    field_proposals: list[FieldDefinitionProposal]
    unresolved_fields: list[str]
    review_required: bool
    review_reason: str | None


class FieldRegistry:
    def __init__(self, definitions: Iterable[FieldDefinition] = ()) -> None:
        self._definitions = {definition.key: definition for definition in definitions}

    def find(self, key: str) -> FieldDefinition | None:
        return self._definitions.get(key)

    def resolve_fields(
        self,
        candidates: Iterable[FieldDefinition],
    ) -> FieldResolutionResult:
        resolved_fields: list[FieldDefinition] = []
        proposals: list[FieldDefinitionProposal] = []
        unresolved_fields: list[str] = []
        review_reasons: list[str] = []
        proposed_by_fingerprint: dict[tuple[str, str], FieldDefinition] = {}

        for candidate in candidates:
            resolved, proposal, reason = self._resolve_candidate(
                candidate,
                proposed_by_fingerprint,
            )
            resolved_fields.append(resolved)
            if proposal is not None:
                proposals.append(proposal)
            if resolved.review_status != "approved":
                unresolved_fields.append(resolved.key)
            if reason is not None:
                review_reasons.append(reason)

        unique_unresolved = sorted(set(unresolved_fields))
        if unique_unresolved and not review_reasons:
            review_reasons.append(
                f"승인되지 않은 프로필 필드: {', '.join(unique_unresolved)}"
            )
        return FieldResolutionResult(
            resolved_fields=resolved_fields,
            field_proposals=proposals,
            unresolved_fields=unique_unresolved,
            review_required=bool(unique_unresolved),
            review_reason="; ".join(dict.fromkeys(review_reasons)) or None,
        )

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

    def _resolve_candidate(
        self,
        candidate: FieldDefinition,
        proposed_by_fingerprint: dict[tuple[str, str], FieldDefinition],
    ) -> tuple[FieldDefinition, FieldDefinitionProposal | None, str | None]:
        exact = self.find(candidate.key)
        if exact is not None:
            return exact, None, None

        fingerprint = _fingerprint(candidate)
        if fingerprint in proposed_by_fingerprint:
            return proposed_by_fingerprint[fingerprint], None, None

        matches = [
            definition
            for definition in self._definitions.values()
            if _fingerprint(definition) == fingerprint
        ]
        if len(matches) == 1:
            return matches[0], None, None

        if len(matches) > 1:
            reason = f"'{candidate.label}' 필드와 같은 이름·자료형의 canonical field가 여러 개입니다."
        else:
            reason = f"새 정책 조건 필드를 발견했습니다: {candidate.label}"

        proposal = FieldDefinitionProposal(
            proposed_field=candidate.model_copy(update={"review_status": "pending"}),
            review_reason=reason,
        )
        proposed_by_fingerprint[fingerprint] = proposal.proposed_field
        return proposal.proposed_field, proposal, reason


def _fingerprint(definition: FieldDefinition) -> tuple[str, str]:
    normalized_label = "".join(
        character for character in definition.label.casefold() if character.isalnum()
    )
    return normalized_label, definition.data_type
