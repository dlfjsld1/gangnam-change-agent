import { useEffect, useMemo, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { ApiError, discoverNewNotices, loadAdminData, loadRunDetail, submitPolicyReview, submitReview } from "./api";
import type { AgentRun, FieldDefinition, FieldDefinitionReview, PolicyPackage, ReviewStatus, SourceNotice } from "./types";

gsap.registerPlugin(useGSAP, ScrollTrigger);

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
  const pageRef = useRef<HTMLElement>(null);
  const [reviews, setReviews] = useState<FieldDefinitionReview[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [run, setRun] = useState(EMPTY_RUN);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [policies, setPolicies] = useState<PolicyPackage[]>([]);
  const [sourceNotice, setSourceNotice] = useState<SourceNotice | null>(null);
  const [source, setSource] = useState<"api" | "fixture">("fixture");
  const [draft, setDraft] = useState<FieldDefinition | null>(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [message, setMessage] = useState("");
  const [workspaceTab, setWorkspaceTab] = useState<"fields" | "policies">("fields");
  const [selectedPolicyId, setSelectedPolicyId] = useState("");
  const [policyAttachments, setPolicyAttachments] = useState<Record<string, SourceNotice["attachments"]>>({});
  const [loadingPolicyId, setLoadingPolicyId] = useState("");

  const pendingReviews = useMemo(() => reviews.filter((item) => item.status === "pending").length, [reviews]);
  const pendingPolicies = useMemo(() => policies.filter((item) => item.review.status === "pending").length, [policies]);
  const selectedPolicy = policies.find((policy) => policy.policy_id === selectedPolicyId) ?? policies[0];

  useGSAP(() => {
    gsap.utils.toArray<HTMLElement>(".workspace-heading, .policy-workspace").forEach((element) => {
      gsap.from(element, {
        y: 54,
        scale: .96,
        opacity: 0,
        duration: .8,
        scrollTrigger: { trigger: element, start: "top 88%", toggleActions: "play none none reverse" },
      });
    });
  }, { scope: pageRef });

  useEffect(() => {
    void loadAdminData().then((data) => {
      setReviews(data.reviews);
      setRun(data.run);
      setRuns(data.runs);
      setPolicies(data.policies);
      setSourceNotice(data.sourceNotice);
      setSource(data.source);
      setSelectedId(data.reviews[0]?.review_id ?? "");
      setWorkspaceTab(data.reviews.length ? "fields" : "policies");
      setMessage(data.source === "api" ? "" : "API 미연결: demo fixture로 동작 중입니다.");
    });
  }, []);

  const selected = reviews.find((review) => review.review_id === selectedId);
  const field = draft ?? selected?.proposal.proposed_field ?? null;
  const selectedRun = runs.find((item) => item.run_id === selected?.run_id) ?? (run.run_id === selected?.run_id ? run : undefined);
  const connectedPolicy = policies.find((policy) => policy.policy_id === selectedRun?.policy_id);

  useEffect(() => {
    setDraft(null);
  }, [selectedId]);

  useEffect(() => {
    if (!policies.some((policy) => policy.policy_id === selectedPolicyId)) {
      setSelectedPolicyId(policies[0]?.policy_id ?? "");
    }
  }, [policies, selectedPolicyId]);

  async function decide(action: ReviewStatus | "edit") {
    if (!selected || !field) {
      return;
    }
    if (
      action !== "rejected"
      && field.data_type === "enum"
      && (
        !field.allowed_values?.length
        || field.allowed_values.some(
          (option) => !String(option.value).trim() || !option.label.trim(),
        )
      )
    ) {
      setMessage("enum 필드는 값과 표시 문구가 있는 선택지를 하나 이상 입력해야 합니다.");
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
    const remainingReviews = reviews.filter((review) => review.review_id !== selected.review_id);
    setReviews(remainingReviews);
    setSelectedId(remainingReviews[0]?.review_id ?? "");
    setDraft(null);
    if (!remainingReviews.length) {
      setWorkspaceTab("policies");
      setMessage("필드 검토를 마쳤습니다. 정책 내용을 확인하고 최종 승인·공개하세요.");
    } else {
      setMessage(action === "rejected" ? "제안을 반려했습니다." : "검토 결과를 저장했습니다. 승인된 필드는 정책 패키지 공개 후보가 됩니다.");
    }
  }

  async function selectRun(runId: string) {
    if (source !== "api") {
      return;
    }
    try {
      const detail = await loadRunDetail(runId);
      setRun(detail.agent_run);
      const pending = detail.field_definition_reviews.filter((review) => review.status === "pending");
      setReviews(pending);
      setSourceNotice(detail.source_notice);
      setSelectedId(pending[0]?.review_id ?? "");
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

  async function selectReview(review: FieldDefinitionReview) {
    setSelectedId(review.review_id);
    if (source !== "api" || !review.run_id || review.run_id === run.run_id) {
      return;
    }
    try {
      const detail = await loadRunDetail(review.run_id);
      setRun(detail.agent_run);
      setSourceNotice(detail.source_notice);
    } catch (error) {
      setMessage(`원본 공고 조회 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
    }
  }

  async function inspectPolicyAttachments(policyId: string) {
    if (policyAttachments[policyId]) {
      setPolicyAttachments((current) => {
        const next = { ...current };
        delete next[policyId];
        return next;
      });
      return;
    }
    const runId = runs.find((item) => item.policy_id === policyId)?.run_id;
    if (!runId) {
      setMessage("이 정책과 연결된 Agent 실행을 찾을 수 없습니다.");
      return;
    }
    setLoadingPolicyId(policyId);
    try {
      const detail = await loadRunDetail(runId);
      setPolicyAttachments((current) => ({
        ...current,
        [policyId]: detail.source_notice?.attachments ?? [],
      }));
    } catch (error) {
      setMessage(`첨부 조회 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
    } finally {
      setLoadingPolicyId("");
    }
  }

  async function checkNewNotices() {
    setIsDiscovering(true);
    setMessage("강남구 공식 게시판에서 새 공고를 확인하고 있습니다.");
    try {
      const discovery = await discoverNewNotices();
      const data = await loadAdminData();
      setReviews(data.reviews);
      setRun(discovery.processed_runs[0] ?? data.run);
      setRuns(data.runs);
      setPolicies(data.policies);
      setSourceNotice(data.sourceNotice);
      setSource(data.source);
      setSelectedId(data.reviews[0]?.review_id ?? "");
      setWorkspaceTab(data.reviews.length ? "fields" : "policies");
      setMessage(
        discovery.processed_runs.length > 0
          ? `새 공고 ${discovery.processed_runs.length}건을 Agent가 처리했습니다.`
          : "새로 처리할 공고가 없습니다.",
      );
    } catch (error) {
      setMessage(`새 공고 확인 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`);
    } finally {
      setIsDiscovering(false);
    }
  }

  return (
    <main className="admin-page" id="top" ref={pageRef}>
      <nav className="topbar" aria-label="관리자 내비게이션">
        <a className="brand" href="#top">GCA <span>CONTROL DESK</span></a>
        {message && <p className="topbar-notice" role="status" aria-live="polite">{message}</p>}
        <span className={`source ${source}`}>{source === "api" ? "API 연결됨" : "데모 데이터"}</span>
      </nav>

      <section className="review-workspace" id="workspace">
        <div className="workspace-bar">
          <div className="workspace-tabs" role="tablist" aria-label="관리자 검토 단계">
            <button aria-selected={workspaceTab === "fields"} onClick={() => setWorkspaceTab("fields")} role="tab" type="button">1. 필드 검토 <span>{pendingReviews}건 남음</span></button>
            <b aria-hidden="true">→</b>
            <button aria-selected={workspaceTab === "policies"} onClick={() => setWorkspaceTab("policies")} role="tab" type="button">2. 정책 승인·공개 <span>{pendingPolicies}건 대기</span></button>
          </div>
          <button className="discover-button" disabled={isDiscovering} onClick={() => void checkNewNotices()}>
            {isDiscovering ? "공고 확인 중…" : "새 공고 확인"}
          </button>
        </div>

        {workspaceTab === "fields" ? <>
          <div className="workspace-heading"><div><p className="eyebrow">Review workspace</p><h2>제안 필드 검토</h2></div><p>근거 원문과 중복 후보를 함께 보고 승인 여부를 결정하세요.</p></div>
          <div className="workspace field-workspace">
            <aside>
              <div className="aside-heading"><h3>검토 큐</h3><span>{reviews.length}</span></div>
              {reviews.map((review) => (
                <button className={review.review_id === selectedId ? "review-item active" : "review-item"} key={review.review_id} onClick={() => void selectReview(review)}>
                  <span><strong>{review.proposal.proposed_field.label}</strong><small>{review.proposal.proposed_field.key}</small></span>
                  <i className={`status-dot ${review.status}`} aria-label={review.status} />
                </button>
              ))}
            </aside>

            {selected && field ? (
              <section className="review-panel">
                <div className="panel-heading">
                  <div><p className="eyebrow">{selected.review_id}</p><h2>{field.label}</h2><code>{field.key}</code></div>
                  <span className={`status ${selected.status}`}>{selected.status}</span>
                </div>
                <p className="next-step">이 필드 검토를 완료하면 <strong>{connectedPolicy?.title ?? "연결된 정책"}</strong> 승인·공개 단계로 이어집니다.</p>
                <div className="reason"><strong>검토 사유</strong><p>{selected.proposal.review_reason}</p></div>
                <div className="detail-grid">
                  <label>필드 키<input value={field.key} onChange={(event) => setDraft({ ...field, key: event.target.value })} /></label>
                  <label>표시 이름<input value={field.label} onChange={(event) => setDraft({ ...field, label: event.target.value })} /></label>
                  <label className="wide">시민 질문<input value={field.question} onChange={(event) => setDraft({ ...field, question: event.target.value })} /></label>
                  <div><span>데이터 형식</span><strong>{field.data_type}</strong></div>
                  <div><span>민감도</span><strong>{field.sensitivity}</strong></div>
                </div>
                {field.data_type === "enum" && <section className="enum-editor">
                  <div className="enum-editor-heading"><div><h3>시민 답변 선택지</h3><p>판정에 사용하는 값과 시민 화면에 보이는 문구를 함께 검토하세요.</p></div><button onClick={() => setDraft({ ...field, allowed_values: [...(field.allowed_values ?? []), { value: "", label: "" }] })} type="button">선택지 추가</button></div>
                  {(field.allowed_values ?? []).map((option, index) => <div className="enum-option" key={`enum-option-${index}`}>
                    <label>판정값<input aria-label={`선택지 ${index + 1} 판정값`} value={String(option.value)} onChange={(event) => setDraft({ ...field, allowed_values: (field.allowed_values ?? []).map((item, itemIndex) => itemIndex === index ? { ...item, value: event.target.value } : item) })} /></label>
                    <label>시민 표시 문구<input aria-label={`선택지 ${index + 1} 표시 문구`} value={option.label} onChange={(event) => setDraft({ ...field, allowed_values: (field.allowed_values ?? []).map((item, itemIndex) => itemIndex === index ? { ...item, label: event.target.value } : item) })} /></label>
                    <button aria-label={`선택지 ${index + 1} 삭제`} className="enum-remove" onClick={() => setDraft({ ...field, allowed_values: (field.allowed_values ?? []).filter((_, itemIndex) => itemIndex !== index) })} type="button">삭제</button>
                  </div>)}
                </section>}
                {selected.evidence && <article className="evidence"><div><h3>원문 근거</h3><a href={selected.evidence.source_url} target="_blank" rel="noreferrer">원문 열기</a></div><p>“{selected.evidence.quote}”</p><small>{selected.evidence.document_name} · {selected.evidence.location}</small></article>}
                {sourceNotice && <article className="evidence"><div><h3>원본 공고·첨부</h3><a href={sourceNotice.source_url} target="_blank" rel="noopener noreferrer">원본 공고 열기</a></div>{sourceNotice.attachments.length ? sourceNotice.attachments.map((attachment) => <p key={attachment.url}><a href={attachment.review_url ?? attachment.public_url ?? attachment.url} target="_blank" rel="noopener noreferrer">{attachment.filename}</a> <small>· {attachment.review_url ? "검토용 S3 · 15분" : attachment.public_url ? "공개 S3" : "공식 원본"}</small></p>) : <p>첨부 파일이 없습니다.</p>}</article>}
                <article className="candidates"><h3>기존 canonical field 후보</h3>{selected.canonical_candidates?.length ? selected.canonical_candidates.map((candidate) => <p key={candidate.key}><code>{candidate.key}</code> · {candidate.label}</p>) : <p>유사 후보가 없습니다.</p>}</article>
                <div className="actions"><button className="reject" onClick={() => void decide("rejected")}>반려</button><button onClick={() => void decide("edit")}>수정 후 승인</button><button className="approve" onClick={() => void decide("approved")}>필드 승인</button></div>
              </section>
            ) : <section className="review-panel empty">검토할 제안이 없습니다.</section>}
          </div>

          <details className="run-details">
            <summary>실행 기록과 원본 공고 <span aria-hidden="true">▾</span></summary>
            <section className="logs">
              <div className="panel-heading"><div><p className="eyebrow">Agent run</p><h2>{run.run_id || "실행 대기"}</h2></div><span className="status pending">{run.status}</span></div>
              {run.review_reason && <p className="run-reason">{run.review_reason} · 미해결: {run.unresolved_fields.join(", ")}</p>}
              <ol>{run.node_logs.map((log) => <li key={`${log.node}-${log.message}`}><span>{log.node}</span><p>{log.message}</p><small>{log.status}</small></li>)}</ol>
            </section>
            <section className="run-picker"><h3>최근 실행</h3><div>{runs.map((item) => <button key={item.run_id} onClick={() => void selectRun(item.run_id)} type="button">{item.run_id} · {item.status}</button>)}</div></section>
            {sourceNotice && <section className="source-card"><h2>원본 공고·첨부</h2><p><a href={sourceNotice.source_url} target="_blank" rel="noopener noreferrer">{sourceNotice.title}</a></p>{sourceNotice.attachments.map((attachment) => <p key={attachment.url}><a href={attachment.public_url ?? attachment.url} target="_blank" rel="noopener noreferrer">{attachment.filename}</a><small> · {attachment.public_url ? "공개 URL" : "원본 URL"}</small></p>)}</section>}
          </details>
        </> : <>
          <div className="workspace-heading"><div><p className="eyebrow">Publish</p><h2>정책 최종 승인·공개</h2></div><p>필드 검토를 마친 정책만 시민 서비스에 공개할 수 있습니다.</p></div>
          {selectedPolicy ? <section className="policy-workspace">
            <nav className="policy-list" aria-label="정책 목록">
              <div className="aside-heading"><h3>정책 큐</h3><span>{policies.length}</span></div>
              {policies.map((policy) => <button className={policy.policy_id === selectedPolicy.policy_id ? "selected" : ""} key={policy.policy_id} onClick={() => setSelectedPolicyId(policy.policy_id)} type="button"><span><strong>{policy.title}</strong><small>{policy.policy_id}</small></span><i className={`status-dot ${policy.review.status}`} aria-label={policy.review.status} /></button>)}
            </nav>
            <article className="policy-detail">
              <header><div><small>{selectedPolicy.policy_id}</small><h3>{selectedPolicy.title}</h3></div><span className={`status ${selectedPolicy.review.status}`}>{selectedPolicy.review.status}</span></header>
              <p>{selectedPolicy.summary}</p>
              <div className="attachment-review"><button disabled={loadingPolicyId === selectedPolicy.policy_id} onClick={() => void inspectPolicyAttachments(selectedPolicy.policy_id)} type="button">{loadingPolicyId === selectedPolicy.policy_id ? "첨부 불러오는 중…" : policyAttachments[selectedPolicy.policy_id] ? "원본 검토 닫기" : "원본 검토"}</button>{policyAttachments[selectedPolicy.policy_id] && <div>{policyAttachments[selectedPolicy.policy_id].length ? policyAttachments[selectedPolicy.policy_id].map((attachment) => <a href={attachment.review_url ?? attachment.public_url ?? attachment.url} key={attachment.url} rel="noopener noreferrer" target="_blank"><span>{attachment.filename}</span><small>{attachment.review_url ? "비공개 S3 · 15분" : attachment.public_url ? "공개 S3" : "공식 원본"}</small></a>) : <p>첨부파일이 없습니다.</p>}</div>}</div>
              {selectedPolicy.review.status === "pending" && <div className="actions"><button className="reject" onClick={() => void decidePolicy(selectedPolicy.policy_id, "reject")} type="button">반려</button><button className="approve" onClick={() => void decidePolicy(selectedPolicy.policy_id, "approve")} type="button">정책 최종 승인·공개</button></div>}
            </article>
          </section> : <p className="empty-state">검토할 정책이 없습니다.</p>}
        </>}
      </section>
      <footer><strong>Gangnam Change Agent</strong><p>시민 프로필과 매칭 결과는 서버에 저장하지 않습니다.</p><a href="#top">맨 위로</a></footer>
    </main>
  );
}
