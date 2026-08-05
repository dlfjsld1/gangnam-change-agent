from json import loads
from pathlib import Path
from types import SimpleNamespace

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from app.schemas.document_extraction import (
    AttachmentComparison,
    DocumentExtraction,
    NoticeDocumentCorpus,
)
from app.schemas.field_definition import FieldDefinition
from app.schemas.policy_extraction import (
    PolicyActionDraft,
    PolicyConditionDraft,
    PolicyDraft,
)
from app.schemas.source_notice import SourceAttachment, SourceNotice
from app.services.field_registry import FieldRegistry
from app.services.policy_builder import build_policy_package
from app.tools.openai_policy_extractor import OpenAIPolicyExtractor

CONTRACTS_DIR = Path(__file__).parents[2] / "docs" / "contracts"


class FakeResponses:
    def __init__(self, draft: PolicyDraft) -> None:
        self.draft = draft
        self.request: dict[str, object] | None = None

    def parse(self, **kwargs: object) -> object:
        self.request = kwargs
        return SimpleNamespace(output_parsed=self.draft)


class FakeClient:
    def __init__(self, draft: PolicyDraft) -> None:
        self.responses = FakeResponses(draft)


def _notice(*, image: bool = False) -> SourceNotice:
    attachments = []
    if image:
        attachments.append(
            SourceAttachment(
                filename="고유가 피해 지원금 사용가능 매장.jpg",
                file_type="image",
                url="https://www.gangnam.go.kr/files/support.jpg",
            )
        )
    return SourceNotice(
        source_id="1107105" if image else "61922",
        source_board="gangnam_center_news" if image else "gangnam_public_notice",
        source_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        title=(
            "고유가 피해지원금 사용가능 매장 스티커 이미지 활용안내"
            if image
            else "청년 응시료 지원사업"
        ),
        published_at="2026-01-08",
        department="일자리정책과",
        body_text=(
            "강남구 주민에게 고유가 피해지원금 사용 매장을 안내합니다."
            if image
            else "지원 대상은 강남구 거주 청년입니다. 2월 1일까지 신청하세요."
        ),
        attachments=attachments,
    )


def _corpus(*, image_text: str | None = None) -> NoticeDocumentCorpus:
    groups = []
    if image_text is not None:
        groups.append(
            AttachmentComparison(
                group_key="고유가 피해 지원금 사용가능 매장",
                extractions=[
                    DocumentExtraction(
                        filename="고유가 피해 지원금 사용가능 매장.jpg",
                        source_type="image",
                        status="succeeded",
                        text=image_text,
                    )
                ],
                representative_filename="고유가 피해 지원금 사용가능 매장.jpg",
                review_required=False,
                review_reason=None,
            )
        )
    return NoticeDocumentCorpus(
        html=DocumentExtraction(
            filename="notice.html",
            source_type="html",
            status="succeeded",
            text="지원 대상은 강남구 거주 청년입니다.",
        ),
        attachment_groups=groups,
        review_required=False,
        review_reasons=[],
    )


def _draft(*, quote: str = "지원 대상은 강남구 거주 청년입니다.") -> PolicyDraft:
    return PolicyDraft(
        category="청년 지원",
        effective_at="2026-01-08",
        deadline_at="2026-02-01",
        summary="강남구 거주 청년의 시험 응시료를 지원합니다.",
        conditions=[
            PolicyConditionDraft(
                field="residence",
                label="거주 지역",
                operator="equals",
                scalar_value="강남구",
                values=[],
                minimum=None,
                maximum=None,
                data_type="string",
                question="현재 거주 지역은 어디인가요?",
                sensitivity="medium",
                validity_days=365,
                evidence_quote=quote,
                document_name="61922.html",
            )
        ],
        required_actions=[
            PolicyActionDraft(
                label="2월 1일까지 신청",
                priority=1,
                evidence_quote="2월 1일까지 신청하세요.",
                document_name="61922.html",
            )
        ],
    )


def _registry() -> FieldRegistry:
    return FieldRegistry(
        [
            FieldDefinition(
                key="residence",
                label="거주 지역",
                data_type="string",
                question="현재 거주 지역은 어디인가요?",
                sensitivity="medium",
                validity_days=365,
                review_status="approved",
            )
        ]
    )


def _validate_policy_package(payload: dict[str, object]) -> None:
    schemas = [
        loads(path.read_text("utf-8")) for path in CONTRACTS_DIR.glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    policy_schema = next(
        schema for schema in schemas if schema["title"] == "PolicyPackage"
    )
    Draft202012Validator(
        policy_schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(payload)


def _validate_field_proposal(payload: dict[str, object]) -> None:
    schemas = [
        loads(path.read_text("utf-8")) for path in CONTRACTS_DIR.glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    proposal_schema = next(
        schema for schema in schemas if schema["title"] == "FieldDefinitionProposal"
    )
    Draft202012Validator(
        proposal_schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(payload)


def _validate_contract(payload: dict[str, object], title: str) -> None:
    schemas = [
        loads(path.read_text("utf-8")) for path in CONTRACTS_DIR.glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(schema for schema in schemas if schema["title"] == title)
    Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(payload)


def test_openai_extractor_uses_structured_policy_draft() -> None:
    draft = _draft()
    client = FakeClient(draft)

    result = OpenAIPolicyExtractor(client=client, model="gpt-test-policy")(
        _notice(),
        _corpus(),
    )

    assert result == draft
    assert client.responses.request is not None
    assert client.responses.request["model"] == "gpt-test-policy"
    assert client.responses.request["text_format"] is PolicyDraft
    assert "61922.html" in str(client.responses.request["input"])


def test_verified_draft_builds_schema_valid_policy_package() -> None:
    result = build_policy_package(
        "run-policy",
        _notice(),
        _corpus(),
        _draft(),
        _registry(),
    )

    assert result.policy_package is not None
    assert result.agent_run.status == "completed"
    assert result.agent_run.review_required is False
    assert result.policy_package["eligibility_rule"] == {
        "and": [{"field": "residence", "operator": "equals", "value": "강남구"}]
    }
    _validate_policy_package(result.policy_package)
    _validate_contract(result.agent_run.model_dump(mode="json"), "AgentRun")


def test_ocr_title_mismatch_requires_review() -> None:
    notice = _notice(image=True)
    draft = _draft().model_copy(
        update={
            "conditions": [
                _draft()
                .conditions[0]
                .model_copy(
                    update={
                        "evidence_quote": "강남구 주민에게 고유가 피해지원금 사용 매장을 안내합니다.",
                        "document_name": "1107105.html",
                    }
                )
            ],
            "required_actions": [],
        }
    )

    result = build_policy_package(
        "run-ocr-conflict",
        notice,
        _corpus(image_text="민생에 플러스 교육가 피해지원금 사용가능매장 행정안전부"),
        draft,
        _registry(),
    )

    assert result.agent_run.status == "review_required"
    assert result.agent_run.review_required is True
    assert any(
        issue.code == "evidence.image_title_conflict"
        for issue in result.evidence_issues
    )


def test_hallucinated_quote_requires_review() -> None:
    result = build_policy_package(
        "run-bad-quote",
        _notice(),
        _corpus(),
        _draft(quote="지원금은 최대 100만원입니다."),
        _registry(),
    )

    assert result.agent_run.review_required is True
    assert result.evidence_issues[0].code == "evidence.quote_not_found"


def test_unknown_field_remains_pending_and_unresolved() -> None:
    result = build_policy_package(
        "run-new-field",
        _notice(),
        _corpus(),
        _draft(),
        FieldRegistry(),
    )

    assert result.policy_package is not None
    assert result.agent_run.review_required is True
    assert result.agent_run.unresolved_fields == ["residence"]
    assert len(result.field_proposals) == 1
    assert len(result.field_reviews) == 1
    assert result.field_reviews[0].review_id == "run-new-field:residence"
    assert result.field_reviews[0].status == "pending"
    assert result.field_reviews[0].approved_field is None
    assert result.field_reviews[0].review_note is None
    assert result.field_reviews[0].reviewed_at is None
    _validate_field_proposal(result.field_proposals[0].model_dump(mode="json"))
    _validate_contract(
        result.field_reviews[0].model_dump(mode="json"),
        "FieldDefinitionReview",
    )
    assert result.policy_package["required_profile_fields"][0]["review_status"] == (
        "pending"
    )


def test_document_extraction_conflict_is_preserved() -> None:
    corpus = _corpus().model_copy(
        update={
            "review_required": True,
            "review_reasons": ["동일 문서의 형식별 추출 내용이 일치하지 않음"],
        }
    )

    result = build_policy_package(
        "run-document-conflict",
        _notice(),
        corpus,
        _draft(),
        _registry(),
    )

    assert result.agent_run.review_required is True
    assert result.evidence_issues[0].code == "evidence.document_conflict"


def test_approved_field_is_reused_without_proposal() -> None:
    result = build_policy_package(
        "run-existing-field",
        _notice(),
        _corpus(),
        _draft(),
        _registry(),
    )

    assert result.field_proposals == []
    assert result.agent_run.unresolved_fields == []
    assert result.policy_package is not None
    assert result.policy_package["required_profile_fields"][0]["review_status"] == (
        "approved"
    )


def test_label_and_data_type_match_uses_canonical_field_key() -> None:
    draft = _draft().model_copy(
        update={
            "conditions": [
                _draft()
                .conditions[0]
                .model_copy(update={"field": "residence_alias", "label": "거주-지역"})
            ]
        }
    )
    result = build_policy_package(
        "run-canonical-field",
        _notice(),
        _corpus(),
        draft,
        _registry(),
    )

    assert result.field_proposals == []
    assert result.agent_run.unresolved_fields == []
    assert result.policy_package is not None
    assert result.policy_package["eligibility_rule"] == {
        "and": [{"field": "residence", "operator": "equals", "value": "강남구"}]
    }
    _validate_policy_package(result.policy_package)


def test_pending_field_is_not_proposed_twice() -> None:
    pending_residence = FieldDefinition(
        key="residence",
        label="거주 지역",
        data_type="string",
        question="현재 거주 지역은 어디인가요?",
        sensitivity="medium",
        validity_days=365,
        review_status="pending",
    )

    result = build_policy_package(
        "run-pending-field",
        _notice(),
        _corpus(),
        _draft(),
        FieldRegistry([pending_residence]),
    )

    assert result.field_proposals == []
    assert result.agent_run.review_required is True
    assert result.agent_run.unresolved_fields == ["residence"]
    assert result.field_reviews == []


def test_review_reasons_and_fields_are_deduplicated_in_input_order() -> None:
    corpus = _corpus().model_copy(
        update={
            "review_required": True,
            "review_reasons": ["추출 실패", "추출 실패"],
        }
    )
    duplicate_condition = (
        _draft()
        .conditions[0]
        .model_copy(update={"field": "household_type", "label": "가구 유형"})
    )
    draft = _draft().model_copy(
        update={"conditions": [duplicate_condition, duplicate_condition]}
    )

    result = build_policy_package(
        "run-stable-review",
        _notice(),
        corpus,
        draft,
        FieldRegistry(),
    )

    assert result.agent_run.review_reason == (
        "추출 실패; 새 정책 조건 필드를 발견했습니다: 가구 유형"
    )
    assert result.agent_run.unresolved_fields == ["household_type"]
    assert [review.review_id for review in result.field_reviews] == [
        "run-stable-review:household_type"
    ]
