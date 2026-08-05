from collections.abc import Callable, Mapping
from dataclasses import dataclass
from operator import add
from typing import Annotated, TypedDict

from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.document_extraction import NoticeDocumentCorpus
from app.schemas.field_definition import FieldDefinitionProposal
from app.schemas.policy_extraction import PolicyBuildResult, PolicyDraft
from app.schemas.source_notice import SourceNotice
from app.services.document_analysis import DocumentAnalysisResult
from app.services.field_registry import FieldRegistry
from app.tools.document_extractor import AttachmentDownloader, TextExtractor


NoticeLoader = Callable[[str], SourceNotice]
DocumentAnalyzer = Callable[..., DocumentAnalysisResult]
PolicyExtractor = Callable[[SourceNotice, NoticeDocumentCorpus], PolicyDraft]
PolicyBuilder = Callable[
    [str, SourceNotice, NoticeDocumentCorpus, PolicyDraft, FieldRegistry],
    PolicyBuildResult,
]


@dataclass(frozen=True)
class ChangeAgentRuntime:
    fetch_notice: NoticeLoader
    analyze_documents: DocumentAnalyzer
    extract_policy: PolicyExtractor
    build_policy: PolicyBuilder
    downloader: AttachmentDownloader
    field_registry: FieldRegistry
    image_ocr: TextExtractor | None = None
    document_extractors: Mapping[str, TextExtractor] | None = None


class ChangeAgentState(TypedDict, total=False):
    run_id: str
    notice_url: str
    html_content: str
    extracted_conditions: list[dict[str, object]]
    notice: SourceNotice
    document_corpus: NoticeDocumentCorpus
    policy_draft: PolicyDraft
    field_proposals: list[FieldDefinitionProposal]
    review_required: bool
    review_reason: str | None
    unresolved_fields: list[str]
    policy_package: dict[str, object] | None
    agent_run: AgentRun
    node_logs: Annotated[list[AgentNodeLog], add]
    error: str
    failed_node: str
