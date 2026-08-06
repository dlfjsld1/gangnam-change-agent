import type { PolicyPackage } from "./policyPackage";


export type PolicySource = "api" | "fixture";

type PolicyResponse = {
  ok: boolean;
  json: () => Promise<unknown>;
};

type PolicyRequest = () => Promise<PolicyResponse>;

export async function loadApprovedPolicyPackages(
  request: PolicyRequest,
  fixturePolicies: PolicyPackage[],
): Promise<{ policies: PolicyPackage[]; source: PolicySource }> {
  try {
    const response = await request();
    if (!response.ok) {
      throw new Error("Policy API request failed.");
    }

    const payload = await response.json();
    if (!Array.isArray(payload)) {
      throw new Error("Policy API response must be an array.");
    }

    return {
      policies: payload.filter(isApprovedPolicyPackage).map(fillEmptyEnumOptions),
      source: "api",
    };
  } catch {
    return { policies: fixturePolicies, source: "fixture" };
  }
}


function fillEmptyEnumOptions(policy: PolicyPackage): PolicyPackage {
  const required_profile_fields = policy.required_profile_fields.map((field) => {
    if (field.data_type !== "enum" || field.allowed_values?.length) {
      return field;
    }
    const value = findConditionValue(policy.eligibility_rule, field.key);
    if (value === undefined) {
      return field;
    }
    const values = Array.isArray(value) ? value : [value];
    return {
      ...field,
      allowed_values: [
        ...values.map((item) => ({ value: item, label: String(item) })),
        { value: "__not_applicable__", label: "해당하지 않음" },
      ],
    };
  });
  return { ...policy, required_profile_fields };
}


function findConditionValue(rule: PolicyPackage["eligibility_rule"], field: string): unknown {
  if ("and" in rule) {
    return rule.and.map((item) => findConditionValue(item, field)).find((value) => value !== undefined);
  }
  if ("or" in rule) {
    return rule.or.map((item) => findConditionValue(item, field)).find((value) => value !== undefined);
  }
  return rule.field === field && "value" in rule ? rule.value : undefined;
}


function isApprovedPolicyPackage(value: unknown): value is PolicyPackage {
  return typeof value === "object" && value !== null &&
    "policy_id" in value && typeof value.policy_id === "string" &&
    "review" in value && typeof value.review === "object" && value.review !== null &&
    "status" in value.review && value.review.status === "approved";
}
