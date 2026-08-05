import { fixtureReviews, fixtureRun } from "./fixture";
import type { AdminRunDetail, AgentRun, FieldDefinition, FieldDefinitionReview, PolicyPackage, ReviewStatus, SourceNotice } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    const detail = await response.json().then((body) => body.detail as string).catch(() => response.statusText);
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function loadAdminData(): Promise<{
  reviews: FieldDefinitionReview[];
  run: AgentRun;
  runs: AgentRun[];
  policies: PolicyPackage[];
  sourceNotice: SourceNotice | null;
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
      return { reviews, run: fixtureRun, runs, policies, sourceNotice: null, source: "api" };
    }
    const detail = await loadRunDetail(runId);
    return { reviews, run: detail.agent_run, runs, policies, sourceNotice: detail.source_notice, source: "api" };
  } catch {
    return { reviews: fixtureReviews, run: fixtureRun, runs: [fixtureRun], policies: [], sourceNotice: null, source: "fixture" };
  }
}

export function loadRunDetail(runId: string): Promise<AdminRunDetail> {
  return request(`/api/admin/agent-runs/${encodeURIComponent(runId)}`);
}

export async function discoverNewNotices(): Promise<{
  discovered_count: number;
  already_processed_count: number;
  processed_runs: AgentRun[];
}> {
  return request("/api/notice-discovery-runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ max_new_notices: 1 }),
  });
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
