from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.field_definition import FieldDefinitionProposal, FieldDefinitionReview


def build_human_review(
    *,
    run_id: str,
    notice_id: str,
    policy_id: str | None,
    node_logs: list[AgentNodeLog],
    reasons: list[str],
    unresolved_fields: list[str],
    field_proposals: list[FieldDefinitionProposal],
) -> tuple[AgentRun, list[FieldDefinitionReview]]:
    unique_reasons = list(dict.fromkeys(reasons))
    unique_fields = list(dict.fromkeys(unresolved_fields))
    review_required = bool(unique_reasons or unique_fields)
    agent_run = AgentRun(
        run_id=run_id,
        notice_id=notice_id,
        status="review_required" if review_required else "completed",
        node_logs=node_logs,
        review_required=review_required,
        review_reason="; ".join(unique_reasons) or None,
        unresolved_fields=unique_fields,
        policy_id=policy_id,
    )
    field_reviews = [
        FieldDefinitionReview(
            review_id=f"{run_id}:{proposal.proposed_field.key}",
            proposal=proposal,
        )
        for proposal in field_proposals
    ]
    return agent_run, field_reviews
