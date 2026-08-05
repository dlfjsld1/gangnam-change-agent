from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from app.agent.state import ChangeAgentRuntime, ChangeAgentState
from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.services.document_analysis import analyze_notice_documents
from app.services.field_registry import FieldRegistry
from app.services.policy_builder import build_policy_package
from app.tools.document_extractor import ScraplingAttachmentDownloader
from app.tools.openai_ocr import OpenAIImageOcr
from app.tools.openai_policy_extractor import OpenAIPolicyExtractor
from app.tools.scrapling_adapter import fetch_source_notice


FETCH_NOTICE = "fetch_notice"
ANALYZE_DOCUMENTS = "analyze_documents"
EXTRACT_POLICY = "extract_policy"
BUILD_POLICY = "build_policy"
AWAIT_REVIEW = "await_review"
COMPLETE = "complete"
FAIL = "fail"


def create_default_runtime(field_registry: FieldRegistry) -> ChangeAgentRuntime:
    return ChangeAgentRuntime(
        fetch_notice=fetch_source_notice,
        analyze_documents=analyze_notice_documents,
        extract_policy=OpenAIPolicyExtractor(),
        build_policy=build_policy_package,
        downloader=ScraplingAttachmentDownloader(),
        field_registry=field_registry,
        image_ocr=OpenAIImageOcr(),
    )


def build_change_agent_graph(runtime: ChangeAgentRuntime):
    graph = StateGraph(ChangeAgentState)
    graph.add_node(FETCH_NOTICE, _fetch_notice_node(runtime))
    graph.add_node(ANALYZE_DOCUMENTS, _analyze_documents_node(runtime))
    graph.add_node(EXTRACT_POLICY, _extract_policy_node(runtime))
    graph.add_node(BUILD_POLICY, _build_policy_node(runtime))
    graph.add_node(AWAIT_REVIEW, _await_review_node)
    graph.add_node(COMPLETE, _complete_node)
    graph.add_node(FAIL, _fail_node)

    graph.add_edge(START, FETCH_NOTICE)
    _add_failure_route(graph, FETCH_NOTICE, ANALYZE_DOCUMENTS)
    _add_failure_route(graph, ANALYZE_DOCUMENTS, EXTRACT_POLICY)
    _add_failure_route(graph, EXTRACT_POLICY, BUILD_POLICY)
    graph.add_conditional_edges(
        BUILD_POLICY,
        _route_after_build,
        {FAIL: FAIL, AWAIT_REVIEW: AWAIT_REVIEW, COMPLETE: COMPLETE},
    )
    graph.add_edge(AWAIT_REVIEW, END)
    graph.add_edge(COMPLETE, END)
    graph.add_edge(FAIL, END)
    return graph.compile()


def _add_failure_route(
    graph: StateGraph,
    source: str,
    next_node: str,
) -> None:
    graph.add_conditional_edges(
        source,
        lambda state: FAIL if state.get("error") else next_node,
        {FAIL: FAIL, next_node: next_node},
    )


def _fetch_notice_node(
    runtime: ChangeAgentRuntime,
) -> Callable[[ChangeAgentState], dict[str, object]]:
    def fetch_notice(state: ChangeAgentState) -> dict[str, object]:
        try:
            notice = runtime.fetch_notice(state["notice_url"])
        except Exception as error:
            return _failure(FETCH_NOTICE, error)
        return {
            "notice": notice,
            "node_logs": [
                _started(FETCH_NOTICE, "강남구 공식 공고 수집을 시작했습니다."),
                AgentNodeLog(
                    node=FETCH_NOTICE,
                    status="completed",
                    message="강남구 공식 공고 본문과 첨부 목록을 수집했습니다.",
                ),
            ],
        }

    return fetch_notice


def _analyze_documents_node(
    runtime: ChangeAgentRuntime,
) -> Callable[[ChangeAgentState], dict[str, object]]:
    def analyze_documents(state: ChangeAgentState) -> dict[str, object]:
        try:
            result = runtime.analyze_documents(
                state["run_id"],
                state["notice"],
                runtime.downloader,
                image_ocr=runtime.image_ocr,
                extractors=runtime.document_extractors,
            )
        except Exception as error:
            return _failure(ANALYZE_DOCUMENTS, error)
        return {
            "document_corpus": result.corpus,
            "review_required": result.agent_run.review_required,
            "review_reason": result.agent_run.review_reason,
            "node_logs": [
                _started(ANALYZE_DOCUMENTS, "공고 본문과 첨부 분석을 시작했습니다."),
                *result.agent_run.node_logs,
                AgentNodeLog(
                    node=ANALYZE_DOCUMENTS,
                    status="completed",
                    message="공고 본문과 첨부 분석을 완료했습니다.",
                ),
            ],
        }

    return analyze_documents


def _extract_policy_node(
    runtime: ChangeAgentRuntime,
) -> Callable[[ChangeAgentState], dict[str, object]]:
    def extract_policy(state: ChangeAgentState) -> dict[str, object]:
        try:
            draft = runtime.extract_policy(
                state["notice"],
                state["document_corpus"],
            )
        except Exception as error:
            return _failure(EXTRACT_POLICY, error)
        return {
            "policy_draft": draft,
            "node_logs": [
                _started(EXTRACT_POLICY, "정책 조건과 행동 후보 추출을 시작했습니다."),
                AgentNodeLog(
                    node=EXTRACT_POLICY,
                    status="completed",
                    message="공고에서 정책 조건과 행동 후보를 구조화했습니다.",
                ),
            ],
        }

    return extract_policy


def _build_policy_node(
    runtime: ChangeAgentRuntime,
) -> Callable[[ChangeAgentState], dict[str, object]]:
    def build_policy(state: ChangeAgentState) -> dict[str, object]:
        try:
            result = runtime.build_policy(
                state["run_id"],
                state["notice"],
                state["document_corpus"],
                state["policy_draft"],
                runtime.field_registry,
            )
        except Exception as error:
            return _failure(BUILD_POLICY, error)
        review_reasons = _review_reasons(
            state.get("review_reason"),
            result.agent_run.review_reason,
        )
        return {
            "policy_package": result.policy_package,
            "field_proposals": result.field_proposals,
            "review_required": (
                state.get("review_required", False) or result.agent_run.review_required
            ),
            "review_reason": "; ".join(review_reasons) or None,
            "unresolved_fields": result.agent_run.unresolved_fields,
            "node_logs": [
                _started(BUILD_POLICY, "정책 패키지 후보 조립을 시작했습니다."),
                *result.agent_run.node_logs,
                AgentNodeLog(
                    node=BUILD_POLICY,
                    status="completed",
                    message="정책 패키지 후보 조립을 완료했습니다.",
                ),
            ],
        }

    return build_policy


def _route_after_build(state: ChangeAgentState) -> str:
    if state.get("error"):
        return FAIL
    if state.get("review_required", False):
        return AWAIT_REVIEW
    return COMPLETE


def _await_review_node(state: ChangeAgentState) -> dict[str, object]:
    terminal_log = AgentNodeLog(
        node=AWAIT_REVIEW,
        status="completed",
        message="관리자 검토가 필요한 실행으로 전달했습니다.",
    )
    return _terminal_result(state, terminal_log, "review_required")


def _complete_node(state: ChangeAgentState) -> dict[str, object]:
    terminal_log = AgentNodeLog(
        node=COMPLETE,
        status="completed",
        message="검증된 정책 패키지 후보 생성을 완료했습니다.",
    )
    return _terminal_result(state, terminal_log, "completed")


def _fail_node(state: ChangeAgentState) -> dict[str, object]:
    return {
        "agent_run": AgentRun(
            run_id=state.get("run_id", "unknown"),
            notice_id=_notice_id(state),
            status="failed",
            node_logs=state.get("node_logs", []),
            review_required=True,
            review_reason=state.get("error", "Agent 실행 실패"),
            unresolved_fields=state.get("unresolved_fields", []),
        )
    }


def _terminal_result(
    state: ChangeAgentState,
    terminal_log: AgentNodeLog,
    status: str,
) -> dict[str, object]:
    logs = [*state.get("node_logs", []), terminal_log]
    policy_package = state.get("policy_package")
    policy_id = (
        str(policy_package["policy_id"])
        if policy_package is not None and "policy_id" in policy_package
        else None
    )
    return {
        "node_logs": [terminal_log],
        "agent_run": AgentRun(
            run_id=state["run_id"],
            notice_id=_notice_id(state),
            status=status,
            node_logs=logs,
            review_required=status == "review_required",
            review_reason=state.get("review_reason"),
            unresolved_fields=state.get("unresolved_fields", []),
            policy_id=policy_id,
        ),
    }


def _notice_id(state: ChangeAgentState) -> str:
    notice = state.get("notice")
    return notice.source_id if notice is not None else "unknown"


def _failure(node: str, error: Exception) -> dict[str, object]:
    message = f"{type(error).__name__}: {error}"
    return {
        "error": message,
        "failed_node": node,
        "review_required": True,
        "review_reason": message,
        "node_logs": [
            _started(node, f"{node} 실행을 시작했습니다."),
            AgentNodeLog(node=node, status="failed", message=message),
        ],
    }


def _started(node: str, message: str) -> AgentNodeLog:
    return AgentNodeLog(node=node, status="started", message=message)


def _review_reasons(*values: str | None) -> list[str]:
    reasons: list[str] = []
    for value in values:
        if not value:
            continue
        for reason in value.split("; "):
            if reason not in reasons:
                reasons.append(reason)
    return reasons
