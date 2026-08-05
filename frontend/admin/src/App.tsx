import { useEffect, useState } from "react";

import { ApiError, loadAdminData, loadRunDetail, submitPolicyReview, submitReview } from "./api";
import type { AgentRun, FieldDefinition, FieldDefinitionReview, PolicyPackage, ReviewStatus, SourceNotice } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const EMPTY_RUN: AgentRun = {
  run_id: "",
  notice_id: "",
  status: "queued",
  node_logs: [],
  review_required: false,
  review_reason: null,
  unresolved_fields: [],
};

export function App() {
  const [reviews, setReviews] = useState<FieldDefinitionReview[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [run, setRun] = useState(EMPTY_RUN);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [policies, setPolicies] = useState<PolicyPackage[]>([]);
  const [sourceNotice, setSourceNotice] = useState<SourceNotice | null>(null);
  const [source, setSource] = useState<"api" | "fixture">("fixture");
  const [draft, setDraft] = useState<FieldDefinition | null>(null);
  const [message, setMessage] = useState("검토 데이터를 불러오는 중입니다.");

  useEffect(() => {
    void loadAdminData().then((data) => {
      setReviews(data.reviews);
      setRun(data.run);
      setRuns(data.runs);
      setPolicies(data.policies);
      setSourceNotice(data.sourceNotice);
      setSource(data.source);
      setSelectedId(data.reviews[0]?.review_id ?? "");
      setMessage(data.source === "api" ? "Backend API에 연결되었습니다." : "API 미연결: demo fixture로 동작 중입니다.");
    });
  }, []);

  const selected = reviews.find((review) => review.review_id === selectedId);
  const field = draft ?? selected?.proposal.proposed_field ?? null;

  useEffect(() => {
    setDraft(null);
  }, [selectedId]);

  async function decide(action: ReviewStatus | "edit") {
    if (!selected || !field) {
      return;
    }
    if (source === "api") {
      try {
        await submitReview(selected.review_id, action, field);
      } catch (error) {
        setMessage(`처리 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
        return;
      }
    }
    const status = action === "edit" ? "approved" : action;
    const reviewedAt = new Date().toISOString();
    setReviews((current) => current.map((review) => review.review_id === selected.review_id ? {
      ...review,
      status,
      approved_field: status === "approved" ? { ...field, review_status: "approved" } : null,
      reviewed_at: reviewedAt,
    } : review));
    setDraft(null);
    setMessage(action === "rejected" ? "제안을 반려했습니다." : "검토 결과를 저장했습니다. 승인된 필드는 정책 패키지 공개 후보가 됩니다.");
  }

  async function selectRun(runId: string) {
    if (source !== "api") {
      return;
    }
    try {
      const detail = await loadRunDetail(runId);
      setRun(detail.agent_run);
      setReviews(detail.field_definition_reviews);
      setSourceNotice(detail.source_notice);
      setSelectedId(detail.field_definition_reviews[0]?.review_id ?? "");
    } catch (error) {
      setMessage(`실행 상세 조회 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
    }
  }

  async function decidePolicy(policyId: string, action: "approve" | "reject") {
    try {
      const updated = await submitPolicyReview(policyId, action);
      setPolicies((current) => current.map((policy) => policy.policy_id === policyId ? updated : policy));
      const runId = runs.find((item) => item.policy_id === policyId)?.run_id;
      if (action === "approve" && runId) {
        const detail = await loadRunDetail(runId);
        setRun(detail.agent_run);
        setSourceNotice(detail.source_notice);
      }
      setMessage(action === "approve" ? "정책을 승인하고 시민 API에 공개했습니다." : "정책을 반려했습니다.");
    } catch (error) {
      const prefix = error instanceof ApiError && error.status === 409
        ? "승인 불가"
        : error instanceof ApiError && error.status === 503
          ? "첨부 저장 실패·재시도 필요"
          : "정책 처리 실패";
      setMessage(`${prefix}: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
    }
  }
  return (
    <main className="admin-page">
      <header className="hero">
        <div>
          <p className="eyebrow">Gangnam Change Agent</p>
          <h1>관리자 통합 화면 준비 완료</h1>
          <p>
            이 앱은 Agent가 만든 검토 대기 정책 패키지를 보여주고 승인 흐름을 연결합니다.
          </p>
          <p className="environment">API: {apiBaseUrl}</p>
        </div>
        <span className={`source ${source}`}>{source === "api" ? "LIVE API" : "DEMO FIXTURE"}</span>
      </header>

      <p className="notice" role="status">{message}</p>

      <section className="summary-grid" aria-label="검토 현황">
        <article><strong>{reviews.filter((item) => item.status === "pending").length}</strong><span>검토 대기</span></article>
        <article><strong>{reviews.filter((item) => item.status === "approved").length}</strong><span>승인</span></article>
        <article><strong>{run.unresolved_fields.length}</strong><span>미해결 필드</span></article>
        <article><strong>0건</strong><span>서버 저장 개인 프로필</span></article>
      </section>

      <div className="workspace">
        <aside>
          <h2>검토 목록</h2>
          {reviews.map((review) => (
            <button className={review.review_id === selectedId ? "review-item active" : "review-item"} key={review.review_id} onClick={() => setSelectedId(review.review_id)}>
              <span>{review.proposal.proposed_field.label}</span>
              <small>{review.status}</small>
            </button>
          ))}
        </aside>

        {selected && field ? (
          <section className="review-panel">
            <div className="panel-heading">
              <div><p className="eyebrow">{selected.review_id}</p><h2>{field.label}</h2></div>
              <span className={`status ${selected.status}`}>{selected.status}</span>
            </div>

            <div className="reason"><strong>검토 사유</strong><p>{selected.proposal.review_reason}</p></div>

            <div className="detail-grid">
              <label>필드 키<input value={field.key} onChange={(event) => setDraft({ ...field, key: event.target.value })} /></label>
              <label>표시 이름<input value={field.label} onChange={(event) => setDraft({ ...field, label: event.target.value })} /></label>
              <label className="wide">시민 질문<input value={field.question} onChange={(event) => setDraft({ ...field, question: event.target.value })} /></label>
              <div><span>데이터 형식</span><strong>{field.data_type}</strong></div>
              <div><span>민감도</span><strong>{field.sensitivity}</strong></div>
            </div>

            {selected.evidence && (
              <article className="evidence">
                <div><h3>원문 근거</h3><a href={selected.evidence.source_url} target="_blank" rel="noreferrer">원문 열기</a></div>
                <p>“{selected.evidence.quote}”</p>
                <small>{selected.evidence.document_name} · {selected.evidence.location}</small>
              </article>
            )}

            <article className="candidates">
              <h3>기존 canonical field 후보</h3>
              {selected.canonical_candidates?.length ? selected.canonical_candidates.map((candidate) => <p key={candidate.key}><code>{candidate.key}</code> · {candidate.label}</p>) : <p>유사 후보가 없습니다.</p>}
            </article>

            <div className="actions">
              <button className="reject" onClick={() => void decide("rejected")}>반려</button>
              <button onClick={() => void decide("edit")}>수정 후 승인</button>
              <button className="approve" onClick={() => void decide("approved")}>승인</button>
            </div>
          </section>
        ) : <section className="review-panel empty">검토할 제안이 없습니다.</section>}
      </div>

      <section className="logs">
        <div className="panel-heading"><div><p className="eyebrow">Agent run</p><h2>{run.run_id || "실행 대기"}</h2></div><span className="status pending">{run.status}</span></div>
        {run.review_reason && <p className="run-reason">{run.review_reason} · 미해결: {run.unresolved_fields.join(", ")}</p>}
        <ol>{run.node_logs.map((log) => <li key={`${log.node}-${log.message}`}><span>{log.node}</span><p>{log.message}</p><small>{log.status}</small></li>)}</ol>
      </section>

      <section className="privacy">
        <h2>Agent 실행 목록</h2>
        <div className="actions">
          {runs.map((item) => <button key={item.run_id} onClick={() => void selectRun(item.run_id)} type="button">{item.run_id} · {item.status}</button>)}
        </div>
      </section>

      {sourceNotice && <section className="privacy">
        <h2>원본 공고·첨부</h2>
        <p><a href={sourceNotice.source_url} target="_blank" rel="noopener noreferrer">{sourceNotice.title}</a></p>
        {sourceNotice.attachments.map((attachment) => <p key={attachment.url}>
          <a href={attachment.public_url ?? attachment.url} target="_blank" rel="noopener noreferrer">{attachment.filename}</a>
          <small> · {attachment.public_url ? "공개 URL" : "원본 URL"}</small>
        </p>)}
      </section>}

      <section className="privacy">
        <h2>정책 검토</h2>
        {policies.map((policy) => (
          <article className="reason" key={policy.policy_id}>
            <strong>{policy.title}</strong>
            <p>{policy.summary}</p>
            <small>{policy.policy_id} · {policy.review.status}</small>
            {policy.review.status === "pending" && <div className="actions">
              <button className="reject" onClick={() => void decidePolicy(policy.policy_id, "reject")} type="button">반려</button>
              <button className="approve" onClick={() => void decidePolicy(policy.policy_id, "approve")} type="button">승인·공개</button>
            </div>}
          </article>
        ))}
      </section>
      <section className="privacy">
        <h2>개인정보 보호 현황</h2>
        <p>서버 저장 사용자 나이 0건 · 거주지역 0건 · 고용 상태 0건 · 개인 프로필 0건</p>
        <small>중앙 서버에 개인 프로필을 모으지 않아 대규모 유출 위험을 줄입니다.</small>
      </section>
    </main>
  );
}
