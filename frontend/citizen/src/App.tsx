import { useEffect, useMemo, useState } from "react";

import { DynamicQuestion } from "./components/DynamicQuestion";
import { hidePolicy, loadHiddenPolicyIds, restoreHiddenPolicies } from "./feed/hiddenPolicyStore";
import { evaluateRule, selectNextQuestion } from "./matcher/evaluateRule";
import type { MatchStatus } from "./matcher/evaluateRule";
import type { PolicyPackage } from "./policy/policyPackage";
import { recordAnswer } from "./profile/answerProfile";
import type { LocalProfile } from "./profile/dynamicProfile";
import { loadProfile, saveProfile } from "./profile/profileStore";
import policyFixture from "../../../demo-data/approved-policy.json";


const policyPackage = policyFixture as PolicyPackage;

function today(): string {
  return new Date().toISOString().slice(0, 10);
}


export function App() {
  const [profile, setProfile] = useState<LocalProfile>({});
  const [profileReady, setProfileReady] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hiddenPolicyIds, setHiddenPolicyIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState("home");

  useEffect(() => {
    void Promise.all([loadProfile(), loadHiddenPolicyIds()])
      .then(([savedProfile, savedHiddenPolicyIds]) => {
        setProfile(savedProfile);
        setHiddenPolicyIds(savedHiddenPolicyIds);
      })
      .finally(() => setProfileReady(true));
  }, []);

  const currentDate = today();
  const status = useMemo<MatchStatus>(
    () => evaluateRule(policyPackage.eligibility_rule, profile, currentDate),
    [currentDate, profile],
  );
  const question = useMemo(
    () => selectNextQuestion(
      policyPackage.eligibility_rule,
      policyPackage.required_profile_fields,
      profile,
      currentDate,
    ),
    [currentDate, profile],
  );
  const isHidden = hiddenPolicyIds.includes(policyPackage.policy_id);
  const change = policyPackage.changes[0];

  async function saveAnswer(value: unknown) {
    if (!question) {
      return;
    }

    setIsSaving(true);
    const nextProfile = recordAnswer(profile, question.field, value, currentDate);
    try {
      await saveProfile(nextProfile);
      setProfile(nextProfile);
    } finally {
      setIsSaving(false);
    }
  }

  async function hideCurrentPolicy() {
    await hidePolicy(policyPackage.policy_id);
    setHiddenPolicyIds((current) => [...new Set([...current, policyPackage.policy_id])]);
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
        <h1>나에게 관련된 변화 {isHidden ? 0 : 1}개</h1>
        <p>내 정보는 이 기기 안에서만 비교돼요.</p>
      </header>

      <div className="feed-panel">
        <p className="privacy-note">⌾ 서버로 전송하지 않아요</p>
        {!profileReady && <p className="loading-copy">내 정보를 불러오는 중입니다.</p>}

        {profileReady && !isHidden && (
          <article className="policy-card">
            <div className="card-topline">
              <span className={`status-chip status-${status.toLowerCase()}`}>
                {status === "YES" ? "✓ 대상 가능성 높음" : status === "NO" ? "확인 결과 대상 아님" : "확인 필요"}
              </span>
              <button className="hide-button" onClick={hideCurrentPolicy} type="button">숨기기</button>
            </div>
            <p className="policy-category">✦ {policyPackage.category}</p>
            <h2>{policyPackage.title}</h2>
            {change && (
              <p className="change-copy">
                {change.label} <strong>{formatChange(change.before)}</strong> <span>→</span> <strong className="accent-value">{formatChange(change.after)}</strong>
              </p>
            )}
            <p className="impact-copy">{policyPackage.summary}</p>
            {question ? (
              <DynamicQuestion
                field={question.field}
                reason={question.reason}
                onAnswer={saveAnswer}
                pending={isSaving}
              />
            ) : (
              <p className="result-copy">{status === "YES" ? "조건을 모두 확인했어요." : "현재 확인할 정보가 없어요."}</p>
            )}
            <button className="detail-button" type="button">자세히 보기 <span>›</span></button>
          </article>
        )}

        {profileReady && isHidden && (
          <section className="empty-feed">
            <p>숨긴 변화가 있어요.</p>
            <button onClick={restorePolicies} type="button">숨긴 카드 다시 보기</button>
          </section>
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


function formatChange(value: unknown): string {
  if (typeof value === "object" && value && "max" in value) {
    return `${String(value.max)}세`;
  }
  return String(value ?? "");
}
