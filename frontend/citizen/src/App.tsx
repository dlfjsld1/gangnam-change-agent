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


const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const fixturePolicies = [policyFixture as PolicyPackage];

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

  async function saveAnswer(field: FieldDefinition, value: unknown) {
    setIsSaving(true);
    const nextProfile = recordAnswer(profile, field, value, today());
    try {
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
        <p className="privacy-note">⌾ 서버로 전송하지 않아요</p>
        {policySource === "fixture" && ready && <p className="fixture-note">데모 정책을 보여드리고 있어요.</p>}
        {!ready && <p className="loading-copy">내 정보를 불러오는 중입니다.</p>}

        {ready && visiblePolicies.map((policy) => (
          <PolicyCard
            isSaving={isSaving}
            key={policy.policy_id}
            onAnswer={saveAnswer}
            onHide={hideCurrentPolicy}
            policy={policy}
            profile={profile}
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
      </div>

      <nav aria-label="주요 메뉴" className="bottom-nav">
        <button aria-current={activeTab === "home" ? "page" : undefined} onClick={() => setActiveTab("home")} type="button">⌂<span>홈</span></button>
        <button aria-current={activeTab === "changes" ? "page" : undefined} onClick={() => setActiveTab("changes")} type="button">▤<span>전체 변경</span></button>
        <button aria-current={activeTab === "profile" ? "page" : undefined} onClick={() => setActiveTab("profile")} type="button">♙<span>내 정보</span></button>
      </nav>
    </main>
  );
}


interface PolicyCardProps {
  isSaving: boolean;
  onAnswer: (field: FieldDefinition, value: unknown) => Promise<void>;
  onHide: (policyId: string) => Promise<void>;
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
        <p className="result-copy">{status === "YES" ? "조건을 모두 확인했어요." : "현재 확인할 정보가 없어요."}</p>
      )}
      <button className="detail-button" type="button">자세히 보기 <span>›</span></button>
    </article>
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
