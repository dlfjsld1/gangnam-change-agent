import { fixtureReviews, fixtureRun } from "./fixture";
import type { AdminRunDetail, AgentRun, FieldDefinition, FieldDefinitionReview, PolicyPackage, ReviewStatus } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function loadAdminData(): Promise<{
  reviews: FieldDefinitionReview[];
  run: AgentRun;
  runs: AgentRun[];
  policies: PolicyPackage[];
  source: "api" | "fixture";
}> {
  try {
    const [reviews, runs, policies] = await Promise.all([
      request<FieldDefinitionReview[]>("/api/field-definition-reviews"),
      request<AgentRun[]>("/api/agent-runs"),
      request<PolicyPackage[]>("/api/admin/policy-packages"),
    ]);
    const runId = reviews[0]?.run_id ?? runs[0]?.run_id;
    if (!runId) {
      return { reviews, run: fixtureRun, runs, policies, source: "api" };
    }
    const detail = await loadRunDetail(runId);
    return { reviews, run: detail.agent_run, runs, policies, source: "api" };
  } catch {
    return { reviews: fixtureReviews, run: fixtureRun, runs: [fixtureRun], policies: [], source: "fixture" };
  }
}

export function loadRunDetail(runId: string): Promise<AdminRunDetail> {
  return request(`/api/admin/agent-runs/${encodeURIComponent(runId)}`);
}

export async function submitReview(
  reviewId: string,
  action: ReviewStatus | "edit",
  field: FieldDefinition,
): Promise<void> {
  const body = JSON.stringify(action === "edit" ? { approved_field: field } : {});
  const endpointAction = action === "rejected" ? "reject" : "approve";
  await request(`/api/field-definition-reviews/${encodeURIComponent(reviewId)}/${endpointAction}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
}

export function submitPolicyReview(policyId: string, action: "approve" | "reject"): Promise<PolicyPackage> {
  return request(`/api/policy-packages/${encodeURIComponent(policyId)}/${action}`, { method: "POST" });
}
