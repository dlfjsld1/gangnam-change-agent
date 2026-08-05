import { useEffect, useMemo, useState } from "react";

import { DynamicQuestion } from "./components/DynamicQuestion";
import { hidePolicy, loadHiddenPolicyIds, restoreHiddenPolicies } from "./feed/hiddenPolicyStore";
import { evaluateRule, selectNextQuestion } from "./matcher/evaluateRule";
import type { MatchStatus } from "./matcher/evaluateRule";
import { loadApprovedPolicyPackages } from "./policy/policyApi";
import type { PolicyPackage } from "./policy/policyPackage";
import { recordAnswer } from "./profile/answerProfile";
import type { FieldDefinition, LocalProfile } from "./profile/dynamicProfile";
import { loadProfile, saveProfile } from "./profile/profileStore";
import policyFixture from "../../../demo-data/approved-policy.json";
import userA from "../../../demo-data/user-a.json";
import userB from "../../../demo-data/user-b.json";


const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const fixturePolicies = [policyFixture as PolicyPackage];
const demoProfiles = {
  A: toLocalProfile(userA.profile),
  B: toLocalProfile(userB.profile),
};

function today(): string {
  return new Date().toISOString().slice(0, 10);
}


async function fetchPolicyPackages(): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 3_000);
  try {
    return await fetch(`${apiBaseUrl}/api/policy-packages`, { signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}


export function App() {
  const [profile, setProfile] = useState<LocalProfile>({});
  const [policies, setPolicies] = useState<PolicyPackage[]>(fixturePolicies);
  const [policySource, setPolicySource] = useState<"api" | "fixture">("fixture");
  const [ready, setReady] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hiddenPolicyIds, setHiddenPolicyIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState("home");
  const [demoProfileName, setDemoProfileName] = useState<"A" | "B" | undefined>();
  const [demoProfile, setDemoProfile] = useState<LocalProfile>();
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyPackage>();

  useEffect(() => {
    void Promise.all([
      loadProfile(),
      loadHiddenPolicyIds(),
      loadApprovedPolicyPackages(
        fetchPolicyPackages,
        fixturePolicies,
      ),
    ])
      .then(([savedProfile, savedHiddenPolicyIds, policyResult]) => {
        setProfile(savedProfile);
        setHiddenPolicyIds(savedHiddenPolicyIds);
        setPolicies(policyResult.policies);
        setPolicySource(policyResult.source);
      })
      .finally(() => setReady(true));
  }, []);

  const visiblePolicies = useMemo(
    () => policies.filter((policy) => !hiddenPolicyIds.includes(policy.policy_id)),
    [hiddenPolicyIds, policies],
  );
  const activeProfile = demoProfile ?? profile;

  async function saveAnswer(field: FieldDefinition, value: unknown) {
    setIsSaving(true);
    const nextProfile = recordAnswer(activeProfile, field, value, today());
    try {
      if (demoProfileName) {
        setDemoProfile(nextProfile);
        return;
      }
      await saveProfile(nextProfile);
      setProfile(nextProfile);
    } finally {
      setIsSaving(false);
    }
  }

  async function hideCurrentPolicy(policyId: string) {
    await hidePolicy(policyId);
    setHiddenPolicyIds((current) => [...new Set([...current, policyId])]);
  }

  async function restorePolicies() {
    await restoreHiddenPolicies();
    setHiddenPolicyIds([]);
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-topline">
          <p>강남 Change Agent</p>
          <button aria-label="알림" className="icon-button" type="button">♧</button>
        </div>
        <h1>나에게 관련된 변화 {visiblePolicies.length}개</h1>
        <p>내 정보는 이 기기 안에서만 비교돼요.</p>
      </header>

      <div className="feed-panel">
        {policySource === "fixture" && ready && <p className="fixture-note">데모 정책을 보여드리고 있어요.</p>}
        {!ready && <p className="loading-copy">내 정보를 불러오는 중입니다.</p>}

        {ready && visiblePolicies.map((policy) => (
          <PolicyCard
            isSaving={isSaving}
            key={policy.policy_id}
            onAnswer={saveAnswer}
            onHide={hideCurrentPolicy}
            onShowDetails={setSelectedPolicy}
            policy={policy}
            profile={activeProfile}
          />
        ))}

        {ready && policies.length > 0 && visiblePolicies.length === 0 && (
          <section className="empty-feed">
            <p>숨긴 변화가 있어요.</p>
            <button onClick={restorePolicies} type="button">숨긴 카드 다시 보기</button>
          </section>
        )}
        {ready && policies.length === 0 && (
          <section className="empty-feed"><p>지금은 새로 확인할 변화가 없어요.</p></section>
        )}

        {ready && (
          <section className="demo-switcher" aria-label="데모 프로필 전환">
            <p>발표용 데모 프로필</p>
            <button aria-pressed={demoProfileName === "A"} onClick={() => { setDemoProfileName("A"); setDemoProfile(demoProfiles.A); }} type="button">사용자 A</button>
            <button aria-pressed={demoProfileName === "B"} onClick={() => { setDemoProfileName("B"); setDemoProfile(demoProfiles.B); }} type="button">사용자 B</button>
            <button aria-pressed={!demoProfileName} onClick={() => { setDemoProfileName(undefined); setDemoProfile(undefined); }} type="button">내 프로필</button>
          </section>
        )}
      </div>

      <nav aria-label="주요 메뉴" className="bottom-nav">
        <button aria-current={activeTab === "home" ? "page" : undefined} onClick={() => setActiveTab("home")} type="button">⌂<span>홈</span></button>
        <button aria-current={activeTab === "changes" ? "page" : undefined} onClick={() => setActiveTab("changes")} type="button">▤<span>전체 변경</span></button>
        <button aria-current={activeTab === "profile" ? "page" : undefined} onClick={() => setActiveTab("profile")} type="button">♙<span>내 정보</span></button>
      </nav>
      {selectedPolicy && <PolicyDetail policy={selectedPolicy} onClose={() => setSelectedPolicy(undefined)} />}
    </main>
  );
}


interface PolicyCardProps {
  isSaving: boolean;
  onAnswer: (field: FieldDefinition, value: unknown) => Promise<void>;
  onHide: (policyId: string) => Promise<void>;
  onShowDetails: (policy: PolicyPackage) => void;
  policy: PolicyPackage;
  profile: LocalProfile;
}

function PolicyCard(props: PolicyCardProps) {
  const currentDate = today();
  const status = evaluateRule(props.policy.eligibility_rule, props.profile, currentDate);
  const question = selectNextQuestion(
    props.policy.eligibility_rule,
    props.policy.required_profile_fields,
    props.profile,
    currentDate,
  );
  const change = props.policy.changes[0];

  return (
    <article className="policy-card">
      <div className="card-topline">
        <span className={`status-chip status-${status.toLowerCase()}`}>{statusLabel(status)}</span>
        <button className="hide-button" onClick={() => props.onHide(props.policy.policy_id)} type="button">숨기기</button>
      </div>
      <p className="policy-category">✦ {props.policy.category}</p>
      <h2>{props.policy.title}</h2>
      {change && (
        <p className="change-copy">
          {change.label} <strong>{formatChange(change.before)}</strong> <span>→</span> <strong className="accent-value">{formatChange(change.after)}</strong>
        </p>
      )}
      <p className="impact-copy">{props.policy.summary}</p>
      {question ? (
        <DynamicQuestion
          field={question.field}
          reason={question.reason}
          onAnswer={(value) => props.onAnswer(question.field, value)}
          pending={props.isSaving}
        />
      ) : (
        <PolicyResult actions={props.policy.required_actions} status={status} />
      )}
      <button className="detail-button" onClick={() => props.onShowDetails(props.policy)} type="button">자세히 보기 <span>›</span></button>
    </article>
  );
}


function PolicyResult(props: { actions: PolicyPackage["required_actions"]; status: MatchStatus }) {
  if (props.status === "YES") {
    return (
      <section className="action-list">
        <h3>해야 할 일</h3>
        {props.actions.map((action) => <p key={action.action_id}>{action.priority}. {action.label}</p>)}
      </section>
    );
  }
  return <p className="result-copy">{props.status === "NO" ? "현재 조건으로는 관련 대상이 아니에요." : "현재 확인할 정보가 없어요."}</p>;
}


function PolicyDetail(props: { onClose: () => void; policy: PolicyPackage }) {
  return (
    <div className="detail-backdrop" role="presentation">
      <section aria-labelledby="policy-detail-title" aria-modal="true" className="detail-sheet" role="dialog">
        <div className="sheet-handle" />
        <button aria-label="상세 화면 닫기" className="sheet-close" onClick={props.onClose} type="button">×</button>
        <p className="policy-category">✦ {props.policy.category}</p>
        <h2 id="policy-detail-title">{props.policy.title}</h2>
        <p className="detail-summary">{props.policy.summary}</p>
        <section className="detail-section">
          <h3>무엇이 바뀌었나요?</h3>
          {props.policy.changes.map((change) => (
            <p key={change.change_id}><strong>{change.label}</strong> {formatChange(change.before)} → {formatChange(change.after)}</p>
          ))}
        </section>
        <section className="detail-section">
          <h3>신청 마감일</h3>
          <p>{props.policy.deadline_at ?? "별도 마감일 없음"}</p>
        </section>
        <section className="detail-section">
          <h3>해야 할 일</h3>
          {props.policy.required_actions.map((action) => <p key={action.action_id}>{action.priority}. {action.label}</p>)}
        </section>
        <section className="detail-section evidence-section">
          <h3>변경 근거</h3>
          {props.policy.evidence.map((evidence) => (
            <blockquote key={evidence.evidence_id}>
              <p>“{evidence.quote}”</p>
              <footer>{evidence.document_name} · {evidence.location}</footer>
            </blockquote>
          ))}
        </section>
      </section>
    </div>
  );
}


function statusLabel(status: MatchStatus): string {
  if (status === "YES") {
    return "✓ 대상 가능성 높음";
  }
  if (status === "NO") {
    return "확인 결과 대상 아님";
  }
  return "확인 필요";
}


function formatChange(value: unknown): string {
  if (typeof value === "object" && value && "max" in value) {
    return `${String(value.max)}세`;
  }
  return String(value ?? "");
}


function toLocalProfile(profile: Record<string, { value: unknown; updated_at: string; valid_until?: string; sensitivity: string }>): LocalProfile {
  return Object.fromEntries(Object.entries(profile).map(([key, value]) => [key, {
    value: value.value,
    updatedAt: value.updated_at,
    validUntil: value.valid_until,
    source: "user_input",
    sensitivity: value.sensitivity as LocalProfile[string]["sensitivity"],
  }]));
}
