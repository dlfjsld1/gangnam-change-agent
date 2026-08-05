from collections.abc import Mapping

from pydantic import BaseModel

from app.schemas.agent_run import AgentNodeLog, AgentRun
from app.schemas.document_extraction import NoticeDocumentCorpus
from app.schemas.source_notice import SourceNotice
from app.tools.document_extractor import (
    AttachmentDownloader,
    TextExtractor,
    extract_notice_corpus,
)


class DocumentAnalysisResult(BaseModel):
    corpus: NoticeDocumentCorpus
    agent_run: AgentRun


def analyze_notice_documents(
    run_id: str,
    notice: SourceNotice,
    downloader: AttachmentDownloader,
    *,
    image_ocr: TextExtractor | None = None,
    extractors: Mapping[str, TextExtractor] | None = None,
) -> DocumentAnalysisResult:
    node_logs = [
        AgentNodeLog(
            node="document_extraction",
            status="started",
            message="HTML 본문과 첨부문서 추출을 시작했습니다.",
        )
    ]
    corpus = extract_notice_corpus(
        notice,
        downloader,
        image_ocr=image_ocr,
        extractors=extractors,
    )
    node_logs.append(
        AgentNodeLog(
            node="document_extraction",
            status="completed",
            message="문서 형식별 텍스트 추출을 완료했습니다.",
        )
    )
    node_logs.append(
        AgentNodeLog(
            node="evidence_comparison",
            status="completed",
            message=(
                "형식별 근거 충돌 또는 추출 실패가 있어 관리자 검토가 필요합니다."
                if corpus.review_required
                else "형식별 근거 비교를 완료했습니다."
            ),
        )
    )

    return DocumentAnalysisResult(
        corpus=corpus,
        agent_run=AgentRun(
            run_id=run_id,
            notice_id=notice.source_id,
            status="review_required" if corpus.review_required else "completed",
            node_logs=node_logs,
            review_required=corpus.review_required,
            review_reason=(
                "; ".join(corpus.review_reasons) if corpus.review_reasons else None
            ),
            unresolved_fields=[],
        ),
    )
