import { useEffect, useMemo, useState } from "react";

import { DynamicQuestion } from "./components/DynamicQuestion";
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

  useEffect(() => {
    void loadProfile()
      .then(setProfile)
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

  return (
    <main>
      <p className="eyebrow">Gangnam Change Agent</p>
      <h1>{policyPackage.title}</h1>
      <p>내 정보는 이 기기 안에서만 판정합니다.</p>
      {!profileReady && <p>내 정보를 불러오는 중입니다.</p>}
      {profileReady && <p>현재 결과: {status}</p>}
      {profileReady && question && (
        <DynamicQuestion
          field={question.field}
          reason={question.reason}
          onAnswer={saveAnswer}
          pending={isSaving}
        />
      )}
      {profileReady && !question && (
        <p>{status === "YES" ? "모든 조건을 확인했습니다." : "추가 질문이 없습니다."}</p>
      )}
    </main>
  );
}
