import { useEffect, useMemo, useRef, useState } from "react";

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
import type { FieldDefinition, LocalProfile, ProfileFieldCatalogItem } from "./profile/dynamicProfile";
import { loadProfileFieldCatalog } from "./profile/profileFieldApi";
import {
  clearProfile,
  loadProfile,
  saveProfile,
} from "./profile/profileStore";
import policyFixture from "../../../demo-data/approved-policy.json";


const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const basePolicyFixture = policyFixture as PolicyPackage;
type CitizenTab = "home" | "favorites" | "profile";
type CitizenView = {
  activeTab: CitizenTab;
  onboardingMode?: "start" | "edit" | "interests" | "preview";
  selectedPolicyId?: string;
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

async function fetchProfileFields(): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 3_000);
  try {
    return await fetch(`${apiBaseUrl}/api/profile-fields`, { signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}


export function App() {
  const [profile, setProfile] = useState<LocalProfile>({});
  const [policies, setPolicies] = useState<PolicyPackage[]>([]);
  const [profileFieldCatalog, setProfileFieldCatalog] = useState<ProfileFieldCatalogItem[]>([]);
  const [policySource, setPolicySource] = useState<"api" | "unavailable">("unavailable");
  const [ready, setReady] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hiddenPolicyIds, setHiddenPolicyIds] = useState<string[]>([]);
  const [favoritePolicyIds, setFavoritePolicyIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<CitizenTab>("home");
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyPackage>();
  const [onboardingMode, setOnboardingMode] = useState<"start" | "edit" | "interests" | "preview">();
  const [activeFeedIndex, setActiveFeedIndex] = useState(0);
  const [carouselCardHeight, setCarouselCardHeight] = useState(0);
  const [isFeedTransitioning, setIsFeedTransitioning] = useState(false);
  const feedTouchStartY = useRef<number | undefined>(undefined);
  const lastFeedTransitionAt = useRef(0);
  const currentFeedCardRef = useRef<HTMLDivElement | null>(null);
  const historyReady = useRef(false);

  useEffect(() => {
    void Promise.all([
      loadProfile(),
      loadHiddenPolicyIds(),
      loadFavoritePolicyIds(),
      loadApprovedPolicyPackages(fetchPolicyPackages),
      loadProfileFieldCatalog(fetchProfileFields),
    ])
      .then(([savedProfile, savedHiddenPolicyIds, savedFavoritePolicyIds, policyResult, fieldCatalog]) => {
        setProfile(savedProfile);
        setHiddenPolicyIds(savedHiddenPolicyIds);
        setFavoritePolicyIds(savedFavoritePolicyIds);
        setPolicies(policyResult.policies);
        setProfileFieldCatalog(fieldCatalog);
        setPolicySource(policyResult.source);
        if (Object.keys(savedProfile).length === 0) {
          setOnboardingMode("start");
        }
      })
      .finally(() => setReady(true));
  }, []);

  function applyView(view: CitizenView) {
    setActiveTab(view.activeTab);
    setOnboardingMode(view.onboardingMode);
    setSelectedPolicy(view.selectedPolicyId ? policies.find((policy) => policy.policy_id === view.selectedPolicyId) : undefined);
  }

  function navigate(view: CitizenView) {
    applyView(view);
    if (historyReady.current) {
      window.history.pushState({ citizenView: view }, "");
    }
  }

  useEffect(() => {
    if (!ready) {
      return;
    }

    window.history.replaceState({
      citizenView: { activeTab, onboardingMode, selectedPolicyId: selectedPolicy?.policy_id },
    }, "");
    historyReady.current = true;

    const restoreView = (event: PopStateEvent) => {
      const view = event.state?.citizenView as CitizenView | undefined;
      if (view) {
        applyView(view);
      }
    };
    window.addEventListener("popstate", restoreView);
    return () => {
      historyReady.current = false;
      window.removeEventListener("popstate", restoreView);
    };
  }, [ready]);

  const activeProfile = profile;
  const displayPolicies = policies;
  const profileFields = profileFieldCatalog.length > 0
    ? profileFieldCatalog.map((item) => item.field_definition)
    : (displayPolicies[0] ?? basePolicyFixture).required_profile_fields;
  const coreProfileFields = profileFieldCatalog.length > 0
    ? profileFieldCatalog.filter((item) => item.onboarding_group === "core").map((item) => item.field_definition)
    : profileFields;
  const optionalProfileFields = profileFieldCatalog
    .filter((item) => item.onboarding_group === "optional")
    .map((item) => item.field_definition);
  const availablePolicies = useMemo(
    () => displayPolicies.filter((policy) => !hiddenPolicyIds.includes(policy.policy_id)),
    [displayPolicies, hiddenPolicyIds],
  );
  const visiblePolicies = useMemo(
    () => availablePolicies.filter((policy) => evaluateRule(policy.eligibility_rule, activeProfile, today()) !== "NO"),
    [activeProfile, availablePolicies],
  );
  const feedPolicies = activeTab === "favorites"
    ? visiblePolicies.filter((policy) => favoritePolicyIds.includes(policy.policy_id))
    : visiblePolicies;
  const isPagedFeed = activeTab === "home" && feedPolicies.length > 0;
  const isCardPager = isPagedFeed && feedPolicies.length > 1;
  const activeFeedPolicy = feedPolicies[Math.min(activeFeedIndex, Math.max(feedPolicies.length - 1, 0))];
  const nextFeedPolicy = isCardPager ? feedPolicies[(activeFeedIndex + 1) % feedPolicies.length] : undefined;
  const renderedFeedPolicies = isPagedFeed && activeFeedPolicy ? [activeFeedPolicy] : feedPolicies;
  const carouselPreviewHeight = Math.min(260, Math.max(104, Math.round(carouselCardHeight * 0.38)));

  useEffect(() => {
    setActiveFeedIndex(0);
  }, [activeTab, feedPolicies.length]);

  useEffect(() => {
    const card = currentFeedCardRef.current;
    if (!card) {
      return;
    }

    const updateHeight = () => setCarouselCardHeight(card.getBoundingClientRect().height);
    updateHeight();
    const observer = new ResizeObserver(updateHeight);
    observer.observe(card);
    return () => observer.disconnect();
  }, [activeFeedIndex, isCardPager, feedPolicies.length]);

  function moveFeed(direction: -1 | 1) {
    if (!isCardPager || direction < 0 || isFeedTransitioning) {
      return;
    }

    const now = Date.now();
    if (now - lastFeedTransitionAt.current < 360) {
      return;
    }
    lastFeedTransitionAt.current = now;
    setIsFeedTransitioning(true);
  }

  function finishFeedTransition() {
    if (!isFeedTransitioning) {
      return;
    }
    setIsFeedTransitioning(false);
    setActiveFeedIndex((current) => (current + 1) % feedPolicies.length);
  }

  function renderPolicyCard(policy: PolicyPackage) {
    return (
      <PolicyCard
        isFavorite={favoritePolicyIds.includes(policy.policy_id)}
        isInFeedStack={false}
        isSaving={isSaving}
        key={policy.policy_id}
        onAnswer={saveAnswer}
        onFavorite={toggleFavoritePolicy}
        onHide={hideCurrentPolicy}
        onShowDetails={(selected) => navigate({ activeTab, selectedPolicyId: selected.policy_id })}
        policy={policy}
        profile={activeProfile}
      />
    );
  }

  useEffect(() => {
    if (!isCardPager) {
      return;
    }

    const handleWheel = (event: WheelEvent) => {
      if (Math.abs(event.deltaY) < 12) {
        return;
      }
      event.preventDefault();
      moveFeed(event.deltaY > 0 ? 1 : -1);
    };

    window.addEventListener("wheel", handleWheel, { passive: false });
    return () => window.removeEventListener("wheel", handleWheel);
  }, [feedPolicies.length, isCardPager]);

  async function saveAnswer(field: FieldDefinition, value: unknown) {
    setIsSaving(true);
    const nextProfile = recordAnswer(activeProfile, field, value, today());
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
    setActiveTab("home");
    setOnboardingMode("start");
  }

  async function completeProfile(nextProfile: LocalProfile) {
    await saveProfile(nextProfile);
    setProfile(nextProfile);
    navigate({ activeTab: onboardingMode === "edit" || onboardingMode === "interests" ? "profile" : "home" });
  }

  return (
    <>
    <main className="app-shell">
      {onboardingMode ? (
        <Onboarding
          initialProfile={onboardingMode === "edit" || onboardingMode === "interests" ? profile : {}}
          key={onboardingMode}
          mode={onboardingMode}
          optionalFields={optionalProfileFields}
          onComplete={completeProfile}
          onClose={onboardingMode !== "start" ? () => window.history.back() : undefined}
          coreFields={coreProfileFields}
        />
      ) : <>
      {activeTab === "profile" ? (
        <ProfilePage
          key="profile"
          fields={profileFields}
          onEdit={() => navigate({ activeTab: "profile", onboardingMode: "edit" })}
          onEditInterests={() => navigate({ activeTab: "profile", onboardingMode: "interests" })}
          onPreviewIntro={() => navigate({ activeTab: "profile", onboardingMode: "preview" })}
          onReset={resetLocalData}
          profile={profile}
        />
      ) : <>
      <section className="tab-page" key={activeTab}>
      <header className="hero">
        <div className="hero-topline">
          <p>강남 Change Agent</p>
        </div>
        {activeTab === "favorites" ? (
          <h1 className="count-hero-title">
            <span>즐겨찾기</span>
            <span className="hero-count"><strong>{feedPolicies.length}</strong>개</span>
          </h1>
        ) : (
          <h1 className="count-hero-title">
            <span>나에게 관련된 변화</span>
            <span className="hero-count"><strong>{visiblePolicies.length}</strong>개</span>
          </h1>
        )}
        <p>{activeTab === "favorites" ? "별을 눌러 담아둔 공고예요." : "내 정보는 이 기기 안에서만 비교돼요."}</p>
      </header>

      <div
        className={`feed-panel${isPagedFeed ? " feed-panel--paged" : ""}`}
        onTouchEnd={(event) => {
          const startY = feedTouchStartY.current;
          if (!isCardPager || startY === undefined) {
            return;
          }
          const distance = startY - event.changedTouches[0].clientY;
          if (Math.abs(distance) >= 42) {
            moveFeed(distance > 0 ? 1 : -1);
          }
          feedTouchStartY.current = undefined;
        }}
        onTouchStart={(event) => {
          feedTouchStartY.current = event.touches[0].clientY;
        }}
      >
        {!ready && <p className="loading-copy">내 정보를 불러오는 중입니다.</p>}

        {ready && isCardPager && activeFeedPolicy && nextFeedPolicy ? (
          <div
            className={`feed-carousel${isFeedTransitioning ? " is-transitioning" : ""}`}
            style={{ height: carouselCardHeight > 0 ? carouselCardHeight + carouselPreviewHeight : undefined }}
          >
            <div
              className="feed-carousel-track"
              onTransitionEnd={(event) => {
                if (event.propertyName === "transform") {
                  finishFeedTransition();
                }
              }}
              style={{ transform: isFeedTransitioning ? `translateY(-${carouselCardHeight + 16}px)` : undefined }}
            >
              <div className="feed-carousel-card" ref={currentFeedCardRef}>{renderPolicyCard(activeFeedPolicy)}</div>
              <div className="feed-carousel-card">{renderPolicyCard(nextFeedPolicy)}</div>
            </div>
          </div>
        ) : ready && renderedFeedPolicies.map(renderPolicyCard)}

        {ready && activeTab === "home" && displayPolicies.length > 0 && availablePolicies.length === 0 && (
          <EmptyFeed
            actionLabel="숨긴 카드 다시 보기"
            description="숨긴 공고는 언제든 다시 목록에 넣을 수 있어요."
            kind="hidden"
            onAction={restorePolicies}
            title="숨긴 변화가 있어요"
          />
        )}
        {ready && activeTab === "home" && availablePolicies.length > 0 && visiblePolicies.length === 0 && (
          <EmptyFeed
            actionLabel="내 정보 확인"
            description="새로운 공고가 들어오면 여기에서 확인할 수 있어요."
            kind="match"
          onAction={() => navigate({ activeTab: "profile" })}
            title="지금 내 정보와 맞는 공고가 없어요"
          />
        )}
        {ready && activeTab === "favorites" && feedPolicies.length === 0 && (
          <EmptyFeed
            actionLabel="홈에서 공고 둘러보기"
            description="관심 있는 공고의 별을 눌러 이곳에 담아보세요."
            kind="favorite"
            onAction={() => navigate({ activeTab: "home" })}
            title="아직 담아둔 공고가 없어요"
          />
        )}
        {ready && policySource === "unavailable" && (
          <EmptyFeed
            description="잠시 후 다시 시도해 주세요. 내 정보는 이 기기에 안전하게 남아 있어요."
            kind="notice"
            title="공고를 불러오지 못했어요"
          />
        )}
        {ready && policySource === "api" && displayPolicies.length === 0 && (
          <EmptyFeed
            description="확인할 수 있는 새로운 정책 변화가 아직 없어요."
            kind="notice"
            title="지금은 새로 확인할 변화가 없어요"
          />
        )}
      </div>
      </section>
      </>}

      <nav aria-label="주요 메뉴" className="bottom-nav">
        <button aria-current={activeTab === "home" ? "page" : undefined} onClick={() => navigate({ activeTab: "home" })} type="button"><HomeIcon /><span>홈</span></button>
        <button aria-current={activeTab === "favorites" ? "page" : undefined} onClick={() => navigate({ activeTab: "favorites" })} type="button"><StarIcon /><span>즐겨찾기</span></button>
        <button aria-current={activeTab === "profile" ? "page" : undefined} onClick={() => navigate({ activeTab: "profile" })} type="button"><FamilyIcon /><span>내 정보</span></button>
      </nav>
      {selectedPolicy && <PolicyDetail policy={selectedPolicy} onClose={() => window.history.back()} />}
      </>}
    </main>
    </>
  );
}


function EmptyFeed(props: {
  actionLabel?: string;
  description: string;
  kind: "favorite" | "hidden" | "match" | "notice";
  onAction?: () => void | Promise<void>;
  title: string;
}) {
  const icon = props.kind === "favorite" ? <StarIcon />
    : props.kind === "hidden" ? <HiddenIcon />
      : props.kind === "match" ? <SearchIcon />
        : <NoticeIcon />;

  return (
    <section className={`empty-feed empty-feed-${props.kind}`} aria-label={props.title}>
      <span aria-hidden="true" className="empty-feed-icon">{icon}</span>
      <h2>{props.title}</h2>
      <p>{props.description}</p>
      {props.actionLabel && props.onAction && (
        <button onClick={() => void props.onAction?.()} type="button">{props.actionLabel}<span aria-hidden="true">›</span></button>
      )}
    </section>
  );
}


function HomeIcon() {
  return <svg aria-hidden="true" className="line-icon" fill="none" viewBox="0 0 24 24"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V10Z" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /><path d="M9 21v-6h6v6" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>;
}


function StarIcon() {
  return <svg aria-hidden="true" className="line-icon" fill="none" viewBox="0 0 24 24"><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>;
}


function HiddenIcon() {
  return <svg aria-hidden="true" className="line-icon" fill="none" viewBox="0 0 24 24"><path d="M3 3l18 18M10.6 10.7a2 2 0 0 0 2.7 2.7M9.8 5.1A11 11 0 0 1 12 5c5.3 0 8.8 4.4 9.7 6.1a1.8 1.8 0 0 1 0 1.8 14.6 14.6 0 0 1-3.1 3.7M6.1 6.2A14.3 14.3 0 0 0 2.3 11a1.8 1.8 0 0 0 0 1.8C3.2 14.6 6.7 19 12 19c.8 0 1.5-.1 2.2-.3" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>;
}


function SearchIcon() {
  return <svg aria-hidden="true" className="line-icon" fill="none" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.8" /><path d="m16 16 4.5 4.5M8 10.5l1.7 1.7 3.4-3.5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>;
}


function NoticeIcon() {
  return <svg aria-hidden="true" className="line-icon" fill="none" viewBox="0 0 24 24"><path d="M7 3h8l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.8" /><path d="M15 3v5h5M9 13h6M9 17h4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>;
}


function FamilyIcon() {
  return <svg aria-hidden="true" className="line-icon" fill="none" viewBox="0 0 24 24"><circle cx="8" cy="7.5" r="2.5" stroke="currentColor" strokeWidth="1.8" /><circle cx="16.5" cy="8.5" r="2" stroke="currentColor" strokeWidth="1.8" /><circle cx="12" cy="12.5" r="1.7" stroke="currentColor" strokeWidth="1.8" /><path d="M3.5 20c.4-3.1 2.1-4.7 4.5-4.7s4.1 1.6 4.5 4.7M13.3 20c.3-2.3 1.5-3.6 3.3-3.6s3 1.3 3.3 3.6M8.7 20c.2-2 1.4-3 3.3-3s3.1 1 3.3 3" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /></svg>;
}


function ProfilePage(props: {
  fields: FieldDefinition[];
  onEdit: () => void;
  onEditInterests: () => void;
  onPreviewIntro: () => void;
  onReset: () => Promise<void>;
  profile: LocalProfile;
}) {
  const fields = props.fields.filter((field) => field.review_status === "approved");
  const interestField = fields.find((field) => field.key === "interest_categories");
  const savedInterests = interestField ? props.profile[interestField.key]?.value : undefined;
  const hasSavedInterests = Array.isArray(savedInterests) && savedInterests.length > 0;

  return (
    <section className="profile-page tab-page" aria-labelledby="profile-title">
      <h1 id="profile-title">내 정보</h1>
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
      <section className="profile-actions" aria-labelledby="profile-actions-title">
        <h2 id="profile-actions-title">정보 관리</h2>
        <div className="profile-management-list">
          <button className="profile-management-row" onClick={props.onEdit} type="button">
            <span>
              <strong>기본 정보 수정</strong>
              <small>거주 동과 조건 정보</small>
            </span>
            <span aria-hidden="true">›</span>
          </button>
          <button className="profile-management-row" onClick={props.onEditInterests} type="button">
            <span>
              <strong>{hasSavedInterests ? "추가 정보 수정" : "추가 정보 입력"}</strong>
              <small>관심 분야 설정</small>
            </span>
            <span aria-hidden="true">›</span>
          </button>
          <button className="profile-management-row" onClick={props.onPreviewIntro} type="button">
            <span>
              <strong>서비스 소개 다시 보기</strong>
              <small>개인정보 처리 원칙 확인</small>
            </span>
            <span aria-hidden="true">›</span>
          </button>
        </div>
      </section>
      <button className="profile-reset-button" onClick={() => void props.onReset()} type="button">이 기기에서 내 정보 삭제</button>
    </section>
  );
}


interface PolicyCardProps {
  isFavorite: boolean;
  isInFeedStack: boolean;
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
        <PolicyResult actions={props.policy.required_actions} compact={props.isInFeedStack} status={status} />
      )}
      <button className="detail-button" onClick={() => props.onShowDetails(props.policy)} type="button">자세히 보기 <span>›</span></button>
    </article>
  );
}


function PolicyResult(props: { actions: PolicyPackage["required_actions"]; compact: boolean; status: MatchStatus }) {
  if (props.status === "YES") {
    if (props.compact) {
      return null;
    }
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
  const sourceLinks = props.policy.evidence.filter(
    (evidence, index, evidenceItems) => evidence.source_url &&
      evidenceItems.findIndex((item) => item.source_url === evidence.source_url) === index,
  );

  return (
    <div className="detail-backdrop" role="presentation">
      <section aria-labelledby="policy-detail-title" aria-modal="true" className="detail-sheet" role="dialog">
        <header className="detail-header">
          <button aria-label="공고 목록으로 돌아가기" className="detail-back-button" onClick={props.onClose} type="button">
            <span aria-hidden="true">←</span> 돌아가기
          </button>
          <span aria-hidden="true">공고 상세</span>
        </header>
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
        {sourceLinks.length > 0 && (
          <section aria-label="원문 및 첨부파일" className="source-links">
            <h3>원문 및 첨부파일</h3>
            {sourceLinks.map((evidence) => {
              const isOriginalNotice = evidence.source_type.toLowerCase() === "html";
              return (
                <a className="source-link-button" href={evidence.source_url} key={evidence.evidence_id} rel="noopener noreferrer" target="_blank">
                  <span className="source-link-icon" aria-hidden="true">{isOriginalNotice ? "↗" : "↓"}</span>
                  <span>
                    <strong>{isOriginalNotice ? "원문 공고 보기" : evidence.document_name}</strong>
                    <small>{isOriginalNotice ? "강남구 공식 공고 페이지" : `${evidence.source_type.toUpperCase()} 첨부파일 · 새 탭에서 열기`}</small>
                  </span>
                  <span aria-hidden="true" className="source-link-arrow">›</span>
                </a>
              );
            })}
          </section>
        )}
      </section>
    </div>
  );
}


interface OnboardingProps {
  coreFields: FieldDefinition[];
  initialProfile: LocalProfile;
  mode: "start" | "edit" | "interests" | "preview";
  onClose?: () => void;
  onComplete: (profile: LocalProfile) => Promise<void>;
  optionalFields: FieldDefinition[];
}

function Onboarding(props: OnboardingProps) {
  const fields = props.coreFields.filter((field) => field.review_status === "approved");
  const interestField = props.optionalFields.find((field) => field.key === "interest_categories");
  const [started, setStarted] = useState(props.mode === "edit" || props.mode === "interests");
  const [draft, setDraft] = useState(props.initialProfile);
  const [fieldIndex, setFieldIndex] = useState(0);
  const [step, setStep] = useState<"questions" | "summary" | "interests">(
    props.mode === "interests" ? "interests" : "questions",
  );
  const [selectedInterests, setSelectedInterests] = useState<string[]>(() => {
    const savedValue = interestField ? props.initialProfile[interestField.key]?.value : undefined;
    return Array.isArray(savedValue) ? savedValue.filter((value): value is string => typeof value === "string") : [];
  });
  const [isSaving, setIsSaving] = useState(false);
  const field = fields[fieldIndex];

  useEffect(() => {
    if (props.mode !== "start") {
      return;
    }

    const returnToIntro = (event: PopStateEvent) => {
      if (event.state?.citizenView?.onboardingMode === "start") {
        setStarted(false);
      }
    };
    window.addEventListener("popstate", returnToIntro);
    return () => window.removeEventListener("popstate", returnToIntro);
  }, [props.mode]);

  function startOnboarding() {
    window.history.pushState({ citizenView: { activeTab: "home", onboardingMode: "start" } }, "");
    setStarted(true);
  }

  async function complete(profile: LocalProfile) {
    setIsSaving(true);
    try {
      await props.onComplete(profile);
    } finally {
      setIsSaving(false);
    }
  }

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
    if (props.mode === "start") {
      setStep("summary");
      return;
    }
    await complete(nextDraft);
  }

  async function saveInterests() {
    if (!interestField) {
      await complete(draft);
      return;
    }
    const nextDraft = { ...draft };
    if (selectedInterests.length > 0) {
      Object.assign(nextDraft, recordAnswer(draft, interestField, selectedInterests, today()));
    } else {
      delete nextDraft[interestField.key];
    }
    setDraft(nextDraft);
    await complete(nextDraft);
  }

  function toggleInterest(value: string) {
    setSelectedInterests((current) => current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value]);
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
            onClick={props.mode === "preview" ? props.onClose : startOnboarding}
            type="button"
          >{props.mode === "preview" ? "소개 닫기" : "시작하기"}</button>
          {props.mode !== "preview" && <p className="onboarding-time">1분이면 끝나요</p>}
        </div>
      </section>
    );
  }

  if (step === "summary") {
    return (
      <section className="onboarding-screen onboarding-form onboarding-summary">
        <p className="onboarding-step">정보 설정 완료</p>
        <h1>입력한 정보를<br />확인해 주세요</h1>
        <p className="onboarding-description">입력한 정보는 이 기기 안에서만 저장돼요.</p>
        <dl className="onboarding-summary-list">
          {fields.map((summaryField) => (
            <div key={summaryField.key}>
              <dt>{summaryField.label}</dt>
              <dd>{formatProfileValue(summaryField, draft[summaryField.key]?.value)}</dd>
            </div>
          ))}
        </dl>
        {interestField && <button className="onboarding-more-info" onClick={() => setStep("interests")} type="button">
          <span className="onboarding-optional-label">선택</span>
          <div>
            <h2>관심 분야를 추가할까요?</h2>
            <p>관심 있는 공고를 더 쉽게 찾아볼 수 있어요.</p>
          </div>
          <span aria-hidden="true" className="onboarding-more-info-arrow">›</span>
        </button>}
        <div className="onboarding-summary-actions">
          <button className="onboarding-secondary" disabled={isSaving} onClick={() => void complete(draft)} type="button">지금 공고 보러가기</button>
        </div>
      </section>
    );
  }

  if (step === "interests") {
    return (
      <section className="onboarding-screen onboarding-form onboarding-interests">
        {props.onClose && <div className="onboarding-topline">
          <button aria-label="내 정보로 돌아가기" className="onboarding-back-button" onClick={props.onClose} type="button"><span aria-hidden="true">←</span> 내 정보</button>
        </div>}
        <p className="onboarding-step">선택 입력</p>
        <h1>관심 있는 분야를<br />골라 주세요</h1>
        <p className="onboarding-description">여러 개를 골라도 되고, 선택하지 않아도 괜찮아요.</p>
        <div className="interest-options" role="group" aria-label="관심 분야">
          {interestField?.allowed_values?.map((option) => {
            const value = String(option.value);
            const selected = selectedInterests.includes(value);
            return <button aria-pressed={selected} className="interest-option" key={value} onClick={() => toggleInterest(value)} type="button">{option.label}</button>;
          })}
        </div>
        <div className="onboarding-action-group">
          <button className="onboarding-primary" disabled={isSaving} onClick={() => void saveInterests()} type="button">선택 완료</button>
          <button className="onboarding-secondary" disabled={isSaving} onClick={() => void complete(draft)} type="button">나중에 설정할게요</button>
        </div>
      </section>
    );
  }

  return (
    <section className="onboarding-screen onboarding-form">
      <div className="onboarding-topline">
        {props.onClose ? <button aria-label="내 정보로 돌아가기" className="onboarding-back-button" onClick={props.onClose} type="button"><span aria-hidden="true">←</span> 내 정보</button> : <p>{`정보 설정 ${fieldIndex + 1}/${fields.length}`}</p>}
      </div>
      <h1>{props.mode === "edit" ? "필요한 정보를 다시 확인해요" : "공고 확인에 필요한 정보예요"}</h1>
      <p className="onboarding-description">답변은 이 기기 안에만 저장되고, 언제든 수정할 수 있어요.</p>
      {field && <DynamicQuestion field={field} key={field.key} onAnswer={answer} pending={isSaving} reason="unknown" />}
    </section>
  );
}


function formatProfileValue(field: FieldDefinition, value: unknown): string {
  if (value === undefined || value === null || value === "") {
    return "아직 입력하지 않음";
  }
  if (field.allowed_values) {
    if (field.data_type === "list" && Array.isArray(value)) {
      return value.map((item) => field.allowed_values?.find((option) => option.value === item)?.label ?? String(item)).join(" · ");
    }
    return field.allowed_values.find((option) => option.value === value)?.label ?? String(value);
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니요";
  }
  return String(value);
}


function statusLabel(status: MatchStatus): string {
  if (status === "YES") {
    return "대상 가능성 높음";
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
