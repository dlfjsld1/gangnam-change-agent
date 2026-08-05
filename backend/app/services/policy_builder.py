import re
from difflib import SequenceMatcher

from app.schemas.agent_run import AgentNodeLog
from app.schemas.document_extraction import DocumentExtraction, NoticeDocumentCorpus
from app.schemas.field_definition import FieldDefinition, FieldDefinitionProposal
from app.schemas.policy_extraction import (
    EvidenceIssue,
    PolicyBuildResult,
    PolicyConditionDraft,
    PolicyDraft,
)
from app.schemas.source_notice import SourceNotice
from app.services.field_registry import FieldRegistry
from app.services.human_review import build_human_review

MINIMUM_TITLE_OCR_SIMILARITY = 0.55


def build_policy_package(
    run_id: str,
    notice: SourceNotice,
    corpus: NoticeDocumentCorpus,
    draft: PolicyDraft,
    field_registry: FieldRegistry,
) -> PolicyBuildResult:
    documents = _source_documents(notice, corpus)
    issues = _validate_evidence(notice, corpus, draft, documents)
    unresolved_fields: list[str] = []
    definitions: dict[str, FieldDefinition] = {}
    field_proposals: list[FieldDefinitionProposal] = []
    rules: list[dict[str, object]] = []

    for condition in draft.conditions:
        if condition.field not in definitions:
            definition, proposal = _resolve_field_definition(
                notice,
                condition,
                field_registry,
            )
            definitions[condition.field] = definition
            if proposal is not None:
                field_proposals.append(proposal)
            if definition.review_status != "approved":
                unresolved_fields.append(condition.field)
        try:
            rules.append(_eligibility_rule(condition))
        except ValueError as error:
            issues.append(
                EvidenceIssue(
                    code="eligibility.invalid_condition",
                    document_name=condition.document_name,
                    message=str(error),
                )
            )

    policy_id = f"{notice.source_board}-{notice.source_id}-v1"
    package = None
    if rules:
        package = {
            "policy_id": policy_id,
            "policy_family_id": f"{notice.source_board}-{notice.source_id}",
            "version": 1,
            "title": notice.title,
            "category": draft.category,
            "published_at": notice.published_at.isoformat(),
            "effective_at": (
                draft.effective_at.isoformat() if draft.effective_at else None
            ),
            "deadline_at": (
                draft.deadline_at.isoformat() if draft.deadline_at else None
            ),
            "summary": draft.summary,
            "changes": [],
            "eligibility_rule": {"and": rules},
            "required_profile_fields": [
                definition.model_dump(exclude_none=True)
                for definition in definitions.values()
            ],
            "required_actions": [
                {
                    "action_id": f"action-{index}",
                    "label": action.label,
                    "priority": action.priority,
                }
                for index, action in enumerate(draft.required_actions, start=1)
            ],
            "evidence": _evidence_items(notice, draft),
            "review": {"status": "pending", "reviewed_at": None},
        }

    reasons = [issue.message for issue in issues]
    if unresolved_fields:
        reasons.append(f"승인되지 않은 프로필 필드: {', '.join(unresolved_fields)}")
    review_required = bool(reasons)
    node_logs = [
        AgentNodeLog(
            node="policy_extraction",
            status="completed",
            message="공고에서 정책 조건과 행동 후보를 구조화했습니다.",
        ),
        AgentNodeLog(
            node="evidence_validation",
            status="completed",
            message=(
                "근거 불일치 또는 미승인 필드가 있어 관리자 검토가 필요합니다."
                if review_required
                else "모든 정책 후보의 원문 근거를 확인했습니다."
            ),
        ),
        AgentNodeLog(
            node="field_resolution",
            status="completed",
            message=(
                "새 프로필 필드를 관리자 검토 대상으로 제안했습니다."
                if field_proposals
                else "기존 프로필 필드의 승인 상태를 확인했습니다."
            ),
        ),
    ]
    agent_run, field_reviews = build_human_review(
        run_id=run_id,
        notice_id=notice.source_id,
        policy_id=policy_id if package is not None else None,
        node_logs=node_logs,
        reasons=reasons,
        unresolved_fields=unresolved_fields,
        field_proposals=field_proposals,
    )
    return PolicyBuildResult(
        policy_package=package,
        evidence_issues=issues,
        field_proposals=field_proposals,
        field_reviews=field_reviews,
        agent_run=agent_run,
    )


def _resolve_field_definition(
    notice: SourceNotice,
    condition: PolicyConditionDraft,
    field_registry: FieldRegistry,
) -> tuple[FieldDefinition, FieldDefinitionProposal | None]:
    existing = field_registry.find(condition.field)
    if existing is not None:
        return existing, None

    proposed = FieldDefinition(
        key=condition.field,
        label=condition.label,
        data_type=condition.data_type,
        question=condition.question,
        sensitivity=condition.sensitivity,
        validity_days=condition.validity_days,
        review_status="pending",
    )
    proposal = field_registry.propose(
        proposed,
        f"공고 {notice.source_id}에서 새 조건 필드를 발견했습니다: {condition.label}",
    )
    if proposal is None:
        raise RuntimeError(f"Unable to create field proposal: {condition.field}")
    return proposal.proposed_field, proposal


def _validate_evidence(
    notice: SourceNotice,
    corpus: NoticeDocumentCorpus,
    draft: PolicyDraft,
    documents: dict[str, str],
) -> list[EvidenceIssue]:
    issues = [
        EvidenceIssue(
            code="evidence.document_conflict",
            document_name="attachment_group",
            message=reason,
        )
        for reason in corpus.review_reasons
    ]
    candidates = [*draft.conditions, *draft.required_actions]
    for candidate in candidates:
        source_text = documents.get(candidate.document_name)
        if source_text is None:
            issues.append(
                EvidenceIssue(
                    code="evidence.document_missing",
                    document_name=candidate.document_name,
                    message=f"근거 문서를 찾을 수 없음: {candidate.document_name}",
                )
            )
        elif _normalize(candidate.evidence_quote) not in _normalize(source_text):
            issues.append(
                EvidenceIssue(
                    code="evidence.quote_not_found",
                    document_name=candidate.document_name,
                    message=f"원문에 없는 인용문: {candidate.evidence_quote}",
                )
            )

    for extraction in _successful_images(corpus):
        similarity = SequenceMatcher(
            None,
            _normalize(notice.title),
            _normalize(extraction.text),
        ).ratio()
        if similarity < MINIMUM_TITLE_OCR_SIMILARITY:
            issues.append(
                EvidenceIssue(
                    code="evidence.image_title_conflict",
                    document_name=extraction.filename,
                    message=(
                        "HTML 제목과 이미지 OCR 핵심 문구가 일치하지 않음: "
                        f"{extraction.filename}"
                    ),
                )
            )
    return issues


def _eligibility_rule(condition: PolicyConditionDraft) -> dict[str, object]:
    base: dict[str, object] = {
        "field": condition.field,
        "operator": condition.operator,
    }
    if condition.operator == "between":
        if condition.minimum is None or condition.maximum is None:
            raise ValueError(f"between 범위 누락: {condition.field}")
        return {**base, "min": condition.minimum, "max": condition.maximum}
    if condition.operator == "in":
        if not condition.values:
            raise ValueError(f"in 값 목록 누락: {condition.field}")
        return {**base, "value": condition.values}
    if condition.operator == "exists":
        value = (condition.scalar_value or "").casefold()
        if value not in {"true", "false"}:
            raise ValueError(f"exists boolean 값 누락: {condition.field}")
        return {**base, "value": value == "true"}
    if condition.scalar_value is None:
        raise ValueError(f"조건 값 누락: {condition.field}")
    return {**base, "value": condition.scalar_value}


def _source_documents(
    notice: SourceNotice,
    corpus: NoticeDocumentCorpus,
) -> dict[str, str]:
    documents = {f"{notice.source_id}.html": f"{notice.title} {notice.body_text}"}
    for group in corpus.attachment_groups:
        for extraction in group.extractions:
            if extraction.status == "succeeded":
                documents[extraction.filename] = extraction.text
    return documents


def _successful_images(corpus: NoticeDocumentCorpus) -> list[DocumentExtraction]:
    return [
        extraction
        for group in corpus.attachment_groups
        for extraction in group.extractions
        if extraction.status == "succeeded" and extraction.source_type == "image"
    ]


def _evidence_items(
    notice: SourceNotice,
    draft: PolicyDraft,
) -> list[dict[str, str]]:
    attachment_urls = {
        attachment.filename: attachment.url for attachment in notice.attachments
    }
    candidates = [*draft.conditions, *draft.required_actions]
    return [
        {
            "evidence_id": f"evidence-{index}",
            "source_type": (
                "HTML" if candidate.document_name.endswith(".html") else "ATTACHMENT"
            ),
            "document_name": candidate.document_name,
            "location": "원문 인용",
            "quote": candidate.evidence_quote,
            "source_url": attachment_urls.get(
                candidate.document_name,
                notice.source_url,
            ),
        }
        for index, candidate in enumerate(candidates, start=1)
    ]


def _normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", value.casefold())
