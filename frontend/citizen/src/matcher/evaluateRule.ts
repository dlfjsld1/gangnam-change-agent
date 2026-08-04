import type { LocalProfile } from "../profile/dynamicProfile";


export type MatchStatus = "YES" | "NO" | "UNKNOWN" | "STALE";

type Rule = {
  field: string;
  operator: "equals" | "between";
  value?: unknown;
  min?: number;
  max?: number;
};

export function evaluateAndRule(
  rules: Rule[],
  profile: LocalProfile,
  today: string,
): MatchStatus {
  let hasUnknown = false;
  let hasStale = false;

  for (const rule of rules) {
    const profileValue = profile[rule.field];
    if (!profileValue) {
      hasUnknown = true;
      continue;
    }
    if (profileValue.validUntil && profileValue.validUntil < today) {
      hasStale = true;
      continue;
    }
    if (rule.operator === "equals" && profileValue.value !== rule.value) {
      return "NO";
    }
    if (
      rule.operator === "between" &&
      (typeof profileValue.value !== "number" ||
        profileValue.value < (rule.min ?? -Infinity) ||
        profileValue.value > (rule.max ?? Infinity))
    ) {
      return "NO";
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
