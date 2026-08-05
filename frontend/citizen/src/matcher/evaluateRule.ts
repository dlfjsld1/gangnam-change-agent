import type { FieldDefinition, LocalProfile } from "../profile/dynamicProfile";


export type MatchStatus = "YES" | "NO" | "UNKNOWN" | "STALE";

type Condition = {
  field: string;
  operator: "equals" | "contains" | "in" | "exists";
  value?: unknown;
} | {
  field: string;
  operator: "between";
  min?: number;
  max?: number;
};

export type EligibilityRule = Condition | {
  and: EligibilityRule[];
} | {
  or: EligibilityRule[];
};

export type QuestionSelection = {
  field: FieldDefinition;
  reason: "unknown" | "stale";
};


export function evaluateRule(
  rule: EligibilityRule,
  profile: LocalProfile,
  today: string,
): MatchStatus {
  if ("and" in rule) {
    return evaluateAndRule(rule.and, profile, today);
  }
  if ("or" in rule) {
    return evaluateOrRule(rule.or, profile, today);
  }

  return evaluateCondition(rule, profile, today);
}


export function evaluateAndRule(
  rules: EligibilityRule[],
  profile: LocalProfile,
  today: string,
): MatchStatus {
  let hasUnknown = false;
  let hasStale = false;

  for (const rule of rules) {
    const status = evaluateRule(rule, profile, today);
    if (status === "NO") {
      return "NO";
    }
    if (status === "STALE") {
      hasStale = true;
    }
    if (status === "UNKNOWN") {
      hasUnknown = true;
    }
  }

  if (hasStale) {
    return "STALE";
  }
  if (hasUnknown) {
    return "UNKNOWN";
  }
  return "YES";
}


export function selectNextQuestion(
  rule: EligibilityRule,
  fields: FieldDefinition[],
  profile: LocalProfile,
  today: string,
): QuestionSelection | undefined {
  const status = evaluateRule(rule, profile, today);
  if (status !== "UNKNOWN" && status !== "STALE") {
    return undefined;
  }

  const eligibleFields = new Map(
    fields
      .filter((field) => field.review_status === "approved")
      .map((field) => [field.key, field]),
  );
  const reason = status === "STALE" ? "stale" : "unknown";

  for (const fieldKey of collectConditionFields(rule)) {
    const field = eligibleFields.get(fieldKey);
    const profileValue = profile[fieldKey];
    if (!field) {
      continue;
    }
    if (reason === "stale" && isStale(profileValue, today)) {
      return { field, reason };
    }
    if (reason === "unknown" && !profileValue) {
      return { field, reason };
    }
  }

  return undefined;
}


function evaluateOrRule(
  rules: EligibilityRule[],
  profile: LocalProfile,
  today: string,
): MatchStatus {
  let hasUnknown = false;
  let hasStale = false;

  for (const rule of rules) {
    const status = evaluateRule(rule, profile, today);
    if (status === "YES") {
      return "YES";
    }
    if (status === "STALE") {
      hasStale = true;
    }
    if (status === "UNKNOWN") {
      hasUnknown = true;
    }
  }

  if (hasStale) {
    return "STALE";
  }
  if (hasUnknown) {
    return "UNKNOWN";
  }
  return "NO";
}


function collectConditionFields(rule: EligibilityRule): string[] {
  if ("and" in rule) {
    return rule.and.flatMap(collectConditionFields);
  }
  if ("or" in rule) {
    return rule.or.flatMap(collectConditionFields);
  }
  return [rule.field];
}


function evaluateCondition(
  condition: Condition,
  profile: LocalProfile,
  today: string,
): MatchStatus {
  const profileValue = profile[condition.field];
  if (!profileValue) {
    return "UNKNOWN";
  }
  if (isStale(profileValue, today)) {
    return "STALE";
  }

  if (condition.operator === "equals") {
    return Object.is(profileValue.value, condition.value) ? "YES" : "NO";
  }
  if (condition.operator === "between") {
    return typeof profileValue.value === "number" &&
      profileValue.value >= (condition.min ?? -Infinity) &&
      profileValue.value <= (condition.max ?? Infinity)
      ? "YES"
      : "NO";
  }
  if (condition.operator === "in") {
    return Array.isArray(condition.value) && valueIsIn(profileValue.value, condition.value)
      ? "YES"
      : "NO";
  }
  if (condition.operator === "contains") {
    return valueContains(profileValue.value, condition.value) ? "YES" : "NO";
  }
  return condition.value ? "YES" : "NO";
}


function isStale(
  profileValue: LocalProfile[string] | undefined,
  today: string,
): boolean {
  return Boolean(profileValue?.validUntil && profileValue.validUntil < today);
}


function valueIsIn(value: unknown, allowedValues: unknown[]): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => allowedValues.some((allowed) => Object.is(item, allowed)));
  }
  return allowedValues.some((allowed) => Object.is(value, allowed));
}


function valueContains(value: unknown, expectedValue: unknown): boolean {
  if (typeof value === "string" && typeof expectedValue === "string") {
    return value.includes(expectedValue);
  }
  return Array.isArray(value) && value.some((item) => Object.is(item, expectedValue));
}
