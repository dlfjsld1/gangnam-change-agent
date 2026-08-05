import { useEffect, useMemo, useState } from "react";

import { DynamicQuestion } from "./components/DynamicQuestion";
import {
  clearFavoritePolicies,
  loadFavoritePolicyIds,
  removeFavoritePolicy,
  saveFavoritePolicy,
} from "./feed/favoritePolicyStore";
import { hidePolicy, loadHiddenPolicyIds, restoreHiddenPolicies } from "./feed/hiddenPolicyStore";
import { evaluateRule, selectNextQuestion } from "./matcher/evaluateRule";
import type { MatchStatus } from "./matcher/evaluateRule";
import { loadApprovedPolicyPackages } from "./policy/policyApi";
import type { PolicyPackage } from "./policy/policyPackage";
import { recordAnswer } from "./profile/answerProfile";
import type { FieldDefinition, LocalProfile } from "./profile/dynamicProfile";
import { clearProfile, loadProfile, saveProfile } from "./profile/profileStore";
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
  const [favoritePolicyIds, setFavoritePolicyIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState("home");
  const [demoProfileName, setDemoProfileName] = useState<"A" | "B" | undefined>();
  const [demoProfile, setDemoProfile] = useState<LocalProfile>();
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyPackage>();
  const [onboardingMode, setOnboardingMode] = useState<"start" | "edit" | "preview">();

  useEffect(() => {
    void Promise.all([
      loadProfile(),
      loadHiddenPolicyIds(),
      loadFavoritePolicyIds(),
      loadApprovedPolicyPackages(
        fetchPolicyPackages,
        fixturePolicies,
      ),
    ])
      .then(([savedProfile, savedHiddenPolicyIds, savedFavoritePolicyIds, policyResult]) => {
        setProfile(savedProfile);
        setHiddenPolicyIds(savedHiddenPolicyIds);
        setFavoritePolicyIds(savedFavoritePolicyIds);
        setPolicies(policyResult.policies);
        setPolicySource(policyResult.source);
        if (Object.keys(savedProfile).length === 0) {
          setOnboardingMode("start");
        }
      })
      .finally(() => setReady(true));
  }, []);

  const visiblePolicies = useMemo(
    () => policies.filter((policy) => !hiddenPolicyIds.includes(policy.policy_id)),
    [hiddenPolicyIds, policies],
  );
  const feedPolicies = activeTab === "favorites"
    ? visiblePolicies.filter((policy) => favoritePolicyIds.includes(policy.policy_id))
    : visiblePolicies;
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

  async function toggleFavoritePolicy(policyId: string) {
    if (favoritePolicyIds.includes(policyId)) {
      await removeFavoritePolicy(policyId);
      setFavoritePolicyIds((current) => current.filter((id) => id !== policyId));
      return;
    }
    await saveFavoritePolicy(policyId);
    setFavoritePolicyIds((current) => [...new Set([...current, policyId])]);
  }

  async function resetLocalData() {
    if (!window.confirm("이 기기에 저장한 내 정보와 즐겨찾기를 모두 지울까요?")) {
      return;
    }
    await Promise.all([
      clearProfile(),
      clearFavoritePolicies(),
      restoreHiddenPolicies(),
    ]);
    setProfile({});
    setHiddenPolicyIds([]);
    setFavoritePolicyIds([]);
    setDemoProfileName(undefined);
    setDemoProfile(undefined);
    setActiveTab("home");
    setOnboardingMode("start");
  }

  async function completeProfile(nextProfile: LocalProfile) {
    await saveProfile(nextProfile);
    setProfile(nextProfile);
    setActiveTab(onboardingMode === "edit" ? "profile" : "home");
    setOnboardingMode(undefined);
  }

  return (
    <main className="app-shell">
      {onboardingMode ? (
        <Onboarding
          initialProfile={onboardingMode === "edit" ? profile : {}}
          key={onboardingMode}
          mode={onboardingMode}
          onComplete={completeProfile}
          onClose={onboardingMode !== "start" ? () => setOnboardingMode(undefined) : undefined}
          policy={policies[0] ?? fixturePolicies[0]}
        />
      ) : <>
      {activeTab === "profile" ? (
        <ProfilePage
          fields={(policies[0] ?? fixturePolicies[0]).required_profile_fields}
          onEdit={() => setOnboardingMode("edit")}
          onPreviewIntro={() => setOnboardingMode("preview")}
          onReset={resetLocalData}
          profile={profile}
        />
      ) : <>
      <header className="hero">
        <div className="hero-topline">
          <p>강남 Change Agent</p>
          <button aria-label="알림" className="icon-button" type="button">♧</button>
        </div>
        <h1>{activeTab === "favorites" ? `즐겨찾기 ${feedPolicies.length}개` : `나에게 관련된 변화 ${visiblePolicies.length}개`}</h1>
        <p>{activeTab === "favorites" ? "별을 눌러 담아둔 공고예요." : "내 정보는 이 기기 안에서만 비교돼요."}</p>
      </header>

      <div className="feed-panel">
        {policySource === "fixture" && ready && <p className="fixture-note">데모 정책을 보여드리고 있어요.</p>}
        {!ready && <p className="loading-copy">내 정보를 불러오는 중입니다.</p>}

        {ready && feedPolicies.map((policy) => (
          <PolicyCard
            isFavorite={favoritePolicyIds.includes(policy.policy_id)}
            isSaving={isSaving}
            key={policy.policy_id}
            onAnswer={saveAnswer}
            onFavorite={toggleFavoritePolicy}
            onHide={hideCurrentPolicy}
            onShowDetails={setSelectedPolicy}
            policy={policy}
            profile={activeProfile}
          />
        ))}

        {ready && activeTab === "home" && policies.length > 0 && visiblePolicies.length === 0 && (
          <section className="empty-feed">
            <p>숨긴 변화가 있어요.</p>
            <button onClick={restorePolicies} type="button">숨긴 카드 다시 보기</button>
          </section>
        )}
        {ready && activeTab === "favorites" && feedPolicies.length === 0 && (
          <section className="empty-feed"><p>아직 즐겨찾기한 공고가 없어요.</p><p>홈에서 별을 눌러 담아보세요.</p></section>
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
      </>}

      <nav aria-label="주요 메뉴" className="bottom-nav">
        <button aria-current={activeTab === "home" ? "page" : undefined} onClick={() => setActiveTab("home")} type="button">⌂<span>홈</span></button>
        <button aria-current={activeTab === "favorites" ? "page" : undefined} onClick={() => setActiveTab("favorites")} type="button">★<span>즐겨찾기</span></button>
        <button aria-current={activeTab === "profile" ? "page" : undefined} onClick={() => setActiveTab("profile")} type="button">♙<span>내 정보</span></button>
      </nav>
      {selectedPolicy && <PolicyDetail policy={selectedPolicy} onClose={() => setSelectedPolicy(undefined)} />}
      </>}
    </main>
  );
}


function ProfilePage(props: {
  fields: FieldDefinition[];
  onEdit: () => void;
  onPreviewIntro: () => void;
  onReset: () => Promise<void>;
  profile: LocalProfile;
}) {
  const fields = props.fields.filter((field) => field.review_status === "approved");

  return (
    <section className="profile-page" aria-labelledby="profile-title">
      <p className="profile-eyebrow">내 기기에만 저장됨</p>
      <h1 id="profile-title">내 정보</h1>
      <p className="profile-description">공고 조건을 비교하기 위해 저장한 정보예요.</p>
      <div className="profile-privacy">
        중앙 서버에 개인 프로필을 모으지 않아 대규모 유출 위험을 줄입니다.
      </div>
      <section className="profile-values" aria-label="저장한 정보">
        {fields.map((field) => (
          <div className="profile-value" key={field.key}>
            <span>{field.label}</span>
            <strong>{formatProfileValue(field, props.profile[field.key]?.value)}</strong>
          </div>
        ))}
      </section>
      <button className="profile-edit-button" onClick={props.onEdit} type="button">정보 수정하기</button>
      <button className="profile-intro-button" onClick={props.onPreviewIntro} type="button">서비스 소개 다시 보기</button>
      <button className="profile-reset-button" onClick={() => void props.onReset()} type="button">이 기기에서 내 정보 삭제</button>
    </section>
  );
}


interface PolicyCardProps {
  isFavorite: boolean;
  isSaving: boolean;
  onAnswer: (field: FieldDefinition, value: unknown) => Promise<void>;
  onFavorite: (policyId: string) => Promise<void>;
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
        <div className="card-actions">
          <button
            aria-label={`${props.policy.title} ${props.isFavorite ? "즐겨찾기 해제" : "즐겨찾기"}`}
            aria-pressed={props.isFavorite}
            className="favorite-button"
            onClick={() => void props.onFavorite(props.policy.policy_id)}
            type="button"
          >★</button>
          <button className="hide-button" onClick={() => props.onHide(props.policy.policy_id)} type="button">숨기기</button>
        </div>
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


interface OnboardingProps {
  initialProfile: LocalProfile;
  mode: "start" | "edit" | "preview";
  onClose?: () => void;
  onComplete: (profile: LocalProfile) => Promise<void>;
  policy: PolicyPackage;
}

function Onboarding(props: OnboardingProps) {
  const fields = props.policy.required_profile_fields.filter((field) => field.review_status === "approved");
  const [started, setStarted] = useState(props.mode === "edit");
  const [draft, setDraft] = useState(props.initialProfile);
  const [fieldIndex, setFieldIndex] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const field = fields[fieldIndex];

  async function answer(value: unknown) {
    if (!field) {
      return;
    }
    const nextDraft = recordAnswer(draft, field, value, today());
    setDraft(nextDraft);
    if (fieldIndex < fields.length - 1) {
      setFieldIndex((current) => current + 1);
      return;
    }
    setIsSaving(true);
    try {
      await props.onComplete(nextDraft);
    } finally {
      setIsSaving(false);
    }
  }

  if (!started) {
    return (
      <section className="onboarding-screen onboarding-welcome">
        <div className="onboarding-hero">
          <p className="onboarding-brand">강남 Change Agent</p>
          <h1>나에게 맞는 공고를<br />찾아드릴게요</h1>
          <p>입력한 정보는 이 기기에만 저장돼요.</p>
        </div>
        <div className="onboarding-content">
          <div className="onboarding-privacy">중앙 서버에 개인 프로필을 모으지 않아 대규모 유출 위험을 줄입니다.</div>
          <ul className="onboarding-points">
            <li>공고 조건은 이 기기 안에서만 비교해요.</li>
            <li>필요한 정보만 물어봐요.</li>
            <li>언제든 내 정보에서 수정할 수 있어요.</li>
          </ul>
          <button
            className="onboarding-primary"
            onClick={props.mode === "preview" ? props.onClose : () => setStarted(true)}
            type="button"
          >{props.mode === "preview" ? "소개 닫기" : "시작하기"}</button>
          {props.mode !== "preview" && <p className="onboarding-time">1분이면 끝나요</p>}
        </div>
      </section>
    );
  }

  return (
    <section className="onboarding-screen onboarding-form">
      <div className="onboarding-topline">
        <p>{props.mode === "edit" ? "내 정보 수정" : `정보 설정 ${fieldIndex + 1}/${fields.length}`}</p>
        {props.onClose && <button onClick={props.onClose} type="button">닫기</button>}
      </div>
      <h1>{props.mode === "edit" ? "필요한 정보를 다시 확인해요" : "공고 확인에 필요한 정보예요"}</h1>
      <p className="onboarding-description">답변은 이 기기 안에만 저장되고, 언제든 수정할 수 있어요.</p>
      {field && <DynamicQuestion field={field} onAnswer={answer} pending={isSaving} reason="unknown" />}
    </section>
  );
}


function formatProfileValue(field: FieldDefinition, value: unknown): string {
  if (value === undefined || value === null || value === "") {
    return "아직 입력하지 않음";
  }
  if (field.allowed_values) {
    return field.allowed_values.find((option) => option.value === value)?.label ?? String(value);
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니요";
  }
  return String(value);
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
