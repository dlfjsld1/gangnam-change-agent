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
      policies: payload.filter(isApprovedPolicyPackage),
      source: "api",
    };
  } catch {
    return { policies: fixturePolicies, source: "fixture" };
  }
}


function isApprovedPolicyPackage(value: unknown): value is PolicyPackage {
  return typeof value === "object" && value !== null &&
    "policy_id" in value && typeof value.policy_id === "string" &&
    "review" in value && typeof value.review === "object" && value.review !== null &&
    "status" in value.review && value.review.status === "approved";
}
