from datetime import date
from json import loads
from pathlib import Path

from jsonschema import Draft202012Validator

from app.agent.graph import build_change_agent_graph
from app.agent.state import ChangeAgentRuntime
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.document_extraction import DocumentExtraction, NoticeDocumentCorpus
from app.schemas.policy_extraction import PolicyBuildResult, PolicyDraft
from app.schemas.source_notice import SourceNotice
from app.services.document_analysis import DocumentAnalysisResult
from app.services.field_registry import FieldRegistry


AGENT_RUN_SCHEMA = loads(
    (Path(__file__).parents[2] / "docs/contracts/agent-run.schema.json").read_text(
        "utf-8"
    )
)


class FakeDownloader:
    def fetch_bytes(self, attachment_url: str) -> bytes:
        raise AssertionError(f"Unexpected download: {attachment_url}")


def _notice() -> SourceNotice:
    return SourceNotice(
        source_id="61922",
        source_board="gangnam_public_notice",
        source_url="https://www.gangnam.go.kr/notice/view.do?id=61922",
        title="청년 응시료 지원사업",
        published_at=date(2026, 1, 8),
        department="일자리정책과",
        body_text="지원 대상은 강남구 거주 청년입니다.",
        attachments=[],
    )


def _corpus() -> NoticeDocumentCorpus:
    return NoticeDocumentCorpus(
        html=DocumentExtraction(
            filename="61922.html",
            source_type="html",
            status="succeeded",
            text="지원 대상은 강남구 거주 청년입니다.",
        ),
        attachment_groups=[],
        review_required=False,
        review_reasons=[],
    )


def _draft() -> PolicyDraft:
    return PolicyDraft(
        category="청년 지원",
        effective_at=None,
        deadline_at=None,
        summary="청년 응시료 지원",
        conditions=[],
        required_actions=[],
    )


def _policy_package() -> dict[str, object]:
    return {"policy_id": "gangnam_public_notice-61922-v1"}


def _validate_agent_run(agent_run: AgentRun) -> None:
    Draft202012Validator(AGENT_RUN_SCHEMA).validate(agent_run.model_dump(mode="json"))


def _runtime(
    calls: list[str],
    *,
    review_required: bool = False,
    fail_fetch: bool = False,
) -> ChangeAgentRuntime:
    notice = _notice()
    corpus = _corpus()
    draft = _draft()

    def fetch_notice(notice_url: str) -> SourceNotice:
        calls.append("fetch_notice")
        if fail_fetch:
            raise ValueError("수집 실패")
        return notice

    def analyze_documents(*args: object, **kwargs: object) -> DocumentAnalysisResult:
        calls.append("analyze_documents")
        return DocumentAnalysisResult(
            corpus=corpus,
            agent_run=AgentRun(
                run_id="run-graph",
                notice_id=notice.source_id,
                status="completed",
                node_logs=[
                    AgentNodeLog(
                        node="document_extraction",
                        status="completed",
                        message="문서 추출 완료",
                    )
                ],
                review_required=False,
                review_reason=None,
                unresolved_fields=[],
            ),
        )

    def extract_policy(
        source_notice: SourceNotice,
        document_corpus: NoticeDocumentCorpus,
    ) -> PolicyDraft:
        calls.append("extract_policy")
        return draft

    def build_policy(*args: object) -> PolicyBuildResult:
        calls.append("build_policy")
        return PolicyBuildResult(
            policy_package=_policy_package(),
            evidence_issues=[],
            field_proposals=[],
            field_reviews=[],
            agent_run=AgentRun(
                run_id="run-graph",
                notice_id=notice.source_id,
                status="review_required" if review_required else "completed",
                node_logs=[
                    AgentNodeLog(
                        node="evidence_validation",
                        status="completed",
                        message="근거 검증 완료",
                    )
                ],
                review_required=review_required,
                review_reason="새 필드 승인 필요" if review_required else None,
                unresolved_fields=["new_field"] if review_required else [],
                policy_id="gangnam_public_notice-61922-v1",
            ),
        )

    return ChangeAgentRuntime(
        fetch_notice=fetch_notice,
        analyze_documents=analyze_documents,
        extract_policy=extract_policy,
        build_policy=build_policy,
        downloader=FakeDownloader(),
        field_registry=FieldRegistry(),
    )


def test_graph_runs_collection_to_completed_policy_package() -> None:
    calls: list[str] = []
    graph = build_change_agent_graph(_runtime(calls))

    result = graph.invoke(
        {"run_id": "run-graph", "notice_url": "https://example.test/notice"}
    )

    assert calls == [
        "fetch_notice",
        "analyze_documents",
        "extract_policy",
        "build_policy",
    ]
    assert result["policy_package"]["policy_id"] == _policy_package()["policy_id"]
    assert result["policy_package"]["changes"] == []
    assert result["agent_run"].status == "completed"
    assert result["agent_run"].node_logs[-1].node == "complete"
    assert any(log.node == "compare_policy" for log in result["agent_run"].node_logs)
    _validate_agent_run(result["agent_run"])


def test_graph_routes_review_required_result_without_publishing() -> None:
    calls: list[str] = []
    graph = build_change_agent_graph(_runtime(calls, review_required=True))

    result = graph.invoke(
        {"run_id": "run-graph", "notice_url": "https://example.test/notice"}
    )

    assert result["agent_run"].status == "review_required"
    assert result["agent_run"].review_reason == "새 필드 승인 필요"
    assert result["agent_run"].unresolved_fields == ["new_field"]
    assert result["agent_run"].node_logs[-1].node == "await_review"
    _validate_agent_run(result["agent_run"])


def test_graph_applies_explicit_previous_policy_identity() -> None:
    calls: list[str] = []
    graph = build_change_agent_graph(_runtime(calls))

    result = graph.invoke(
        {
            "run_id": "run-graph",
            "notice_url": "https://example.test/notice",
            "previous_policy_package": {
                "policy_family_id": "youth-support",
                "version": 4,
            },
        }
    )

    assert result["policy_package"]["policy_family_id"] == "youth-support"
    assert result["policy_package"]["version"] == 5
    assert result["policy_package"]["policy_id"] == "youth-support-v5"


def test_graph_records_failure_and_stops_following_nodes() -> None:
    calls: list[str] = []
    graph = build_change_agent_graph(_runtime(calls, fail_fetch=True))

    result = graph.invoke(
        {"run_id": "run-graph", "notice_url": "https://example.test/notice"}
    )

    assert calls == ["fetch_notice"]
    assert result["failed_node"] == "fetch_notice"
    assert result["agent_run"].status == "failed"
    assert result["agent_run"].review_required is True
    assert result["agent_run"].node_logs[-1].status == "failed"
    _validate_agent_run(result["agent_run"])
