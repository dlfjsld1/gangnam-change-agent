import assert from "node:assert/strict";
import test from "node:test";

import { evaluateRule, selectNextQuestion } from "./evaluateRule.ts";
import { recordAnswer } from "../profile/answerProfile.ts";
import { loadApprovedPolicyPackages } from "../policy/policyApi.ts";
import policyPackage from "../../../../demo-data/approved-policy.json" with { type: "json" };
import staleRefreshSmoke from "../../../../demo-data/stale-refresh-smoke.json" with { type: "json" };
import unknownQuestionSmoke from "../../../../demo-data/unknown-question-smoke.json" with { type: "json" };


const TODAY = "2026-08-05";

function profile(values) {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => [
      key,
      {
        value,
        updatedAt: TODAY,
        source: "user_input",
        sensitivity: "low",
      },
    ]),
  );
}


test("evaluates every MVP condition operator", () => {
  const localProfile = profile({
    residence: "강남구",
    age: 35,
    categories: ["청년", "구직자"],
  });

  assert.equal(
    evaluateRule(
      { field: "residence", operator: "equals", value: "강남구" },
      localProfile,
      TODAY,
    ),
    "YES",
  );
  assert.equal(
    evaluateRule(
      { field: "residence", operator: "in", value: ["강남구", "서초구"] },
      localProfile,
      TODAY,
    ),
    "YES",
  );
  assert.equal(
    evaluateRule(
      { field: "age", operator: "between", min: 19, max: 39 },
      localProfile,
      TODAY,
    ),
    "YES",
  );
  assert.equal(
    evaluateRule(
      { field: "categories", operator: "contains", value: "청년" },
      localProfile,
      TODAY,
    ),
    "YES",
  );
  assert.equal(
    evaluateRule(
      { field: "residence", operator: "exists", value: true },
      localProfile,
      TODAY,
    ),
    "YES",
  );
});


test("AND returns NO before STALE or UNKNOWN", () => {
  const localProfile = profile({ residence: "서초구" });
  localProfile.employment = {
    value: "unemployed",
    updatedAt: "2026-01-01",
    validUntil: "2026-08-04",
    source: "user_input",
    sensitivity: "medium",
  };

  assert.equal(
    evaluateRule(
      {
        and: [
          { field: "employment", operator: "equals", value: "unemployed" },
          { field: "residence", operator: "equals", value: "강남구" },
          { field: "military", operator: "exists", value: true },
        ],
      },
      localProfile,
      TODAY,
    ),
    "NO",
  );
});


test("OR returns YES before STALE or UNKNOWN", () => {
  const localProfile = profile({ residence: "강남구" });
  localProfile.employment = {
    value: "unemployed",
    updatedAt: "2026-01-01",
    validUntil: "2026-08-04",
    source: "user_input",
    sensitivity: "medium",
  };

  assert.equal(
    evaluateRule(
      {
        or: [
          { field: "employment", operator: "equals", value: "unemployed" },
          { field: "residence", operator: "equals", value: "강남구" },
          { field: "military", operator: "exists", value: true },
        ],
      },
      localProfile,
      TODAY,
    ),
    "YES",
  );
});


test("evaluates nested AND and OR rules", () => {
  const localProfile = profile({ residence: "강남구", age: 35 });

  assert.equal(
    evaluateRule(
      {
        and: [
          { field: "residence", operator: "equals", value: "강남구" },
          {
            or: [
              { field: "age", operator: "between", min: 19, max: 39 },
              { field: "age", operator: "between", min: 65, max: 99 },
            ],
          },
        ],
      },
      localProfile,
      TODAY,
    ),
    "YES",
  );
});


test("selects the approved missing field from the UNKNOWN smoke fixture", () => {
  assert.equal(
    evaluateRule(
      policyPackage.eligibility_rule,
      unknownQuestionSmoke.profile,
      unknownQuestionSmoke.today,
    ),
    unknownQuestionSmoke.expected_before,
  );

  const selection = selectNextQuestion(
    policyPackage.eligibility_rule,
    policyPackage.required_profile_fields,
    unknownQuestionSmoke.profile,
    unknownQuestionSmoke.today,
  );

  assert.deepEqual(selection, {
    field: policyPackage.required_profile_fields.find(
      (field) => field.key === unknownQuestionSmoke.missing_field,
    ),
    reason: "unknown",
  });
});


test("records an answer locally and changes the UNKNOWN smoke fixture to YES", () => {
  const field = policyPackage.required_profile_fields.find(
    (candidate) => candidate.key === unknownQuestionSmoke.missing_field,
  );
  const nextProfile = recordAnswer(
    unknownQuestionSmoke.profile,
    field,
    unknownQuestionSmoke.answer,
    unknownQuestionSmoke.today,
  );

  assert.equal(
    evaluateRule(
      policyPackage.eligibility_rule,
      nextProfile,
      unknownQuestionSmoke.today,
    ),
    unknownQuestionSmoke.expected_after,
  );
});


test("selects a STALE field before a missing field and changes it to YES after refresh", () => {
  const profileWithMissingField = { ...staleRefreshSmoke.profile };
  delete profileWithMissingField.military_service_status;

  assert.equal(
    evaluateRule(
      policyPackage.eligibility_rule,
      profileWithMissingField,
      staleRefreshSmoke.today,
    ),
    staleRefreshSmoke.expected_before,
  );

  const selection = selectNextQuestion(
    policyPackage.eligibility_rule,
    policyPackage.required_profile_fields,
    profileWithMissingField,
    staleRefreshSmoke.today,
  );
  const staleField = policyPackage.required_profile_fields.find(
    (field) => field.key === staleRefreshSmoke.stale_field,
  );

  assert.deepEqual(selection, { field: staleField, reason: "stale" });

  const refreshedProfile = recordAnswer(
    staleRefreshSmoke.profile,
    staleField,
    staleRefreshSmoke.answer,
    staleRefreshSmoke.today,
  );
  assert.equal(
    evaluateRule(
      policyPackage.eligibility_rule,
      refreshedProfile,
      staleRefreshSmoke.today,
    ),
    staleRefreshSmoke.expected_after,
  );
});


test("uses only approved API policies and falls back to the fixture on failure", async () => {
  const approvedResult = await loadApprovedPolicyPackages(
    async () => ({
      ok: true,
      json: async () => [policyPackage, { ...policyPackage, policy_id: "pending", review: { status: "pending" } }],
    }),
    [policyPackage],
  );
  assert.deepEqual(approvedResult, { policies: [policyPackage], source: "api" });

  const fallbackResult = await loadApprovedPolicyPackages(
    async () => { throw new Error("offline"); },
    [policyPackage],
  );
  assert.deepEqual(fallbackResult, { policies: [policyPackage], source: "fixture" });
});
