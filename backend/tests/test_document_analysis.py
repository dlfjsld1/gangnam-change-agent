from json import loads
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from app.schemas.source_notice import SourceAttachment, SourceNotice
from app.services.document_analysis import analyze_notice_documents


CONTRACTS_DIR = Path(__file__).parents[2] / "docs" / "contracts"


class FakeDownloader:
    def fetch_bytes(self, attachment_url: str) -> bytes:
        if attachment_url.endswith(".pdf"):
            return b"%PDF test payload"
        return b"PK\x03\x04 test payload"


def _notice() -> SourceNotice:
    return SourceNotice(
        source_id="61922",
        source_board="gangnam_public_notice",
        source_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        title="청년 지원 공고",
        published_at="2026-01-08",
        department="일자리정책과",
        body_text="강남구 청년에게 시험 응시료를 지원합니다.",
        attachments=[
            SourceAttachment(
                filename="공고문.pdf",
                file_type="pdf",
                url="https://www.gangnam.go.kr/files/공고문.pdf",
            ),
            SourceAttachment(
                filename="공고문.hwpx",
                file_type="hwpx",
                url="https://www.gangnam.go.kr/files/공고문.hwpx",
            ),
        ],
    )


def _validate_agent_run(payload: dict[str, object]) -> None:
    schema = loads((CONTRACTS_DIR / "agent-run.schema.json").read_text("utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def test_consistent_documents_create_completed_agent_run() -> None:
    shared_text = "지원 대상은 강남구 청년이며 지원 금액은 최대 이십만원입니다."

    result = analyze_notice_documents(
        "run-61922",
        _notice(),
        FakeDownloader(),
        extractors={"pdf": lambda _: shared_text, "hwpx": lambda _: shared_text},
    )

    assert result.agent_run.status == "completed"
    assert result.agent_run.review_required is False
    assert [log.node for log in result.agent_run.node_logs] == [
        "document_extraction",
        "document_extraction",
        "evidence_comparison",
    ]
    _validate_agent_run(result.agent_run.model_dump(mode="json"))


def test_conflict_propagates_review_reason_to_agent_run() -> None:
    result = analyze_notice_documents(
        "run-conflict",
        _notice(),
        FakeDownloader(),
        extractors={
            "pdf": lambda _: "신청 기간은 8월 1일부터 8월 10일까지입니다.",
            "hwpx": lambda _: "신청 기간은 9월 1일부터 9월 30일까지입니다.",
        },
    )

    assert result.agent_run.status == "review_required"
    assert result.agent_run.review_required is True
    assert "일치하지 않음" in result.agent_run.review_reason
    assert result.agent_run.unresolved_fields == []
    _validate_agent_run(result.agent_run.model_dump(mode="json"))
