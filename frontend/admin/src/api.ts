import { fixtureReviews, fixtureRun } from "./fixture";
import type { AgentRun, FieldDefinition, FieldDefinitionReview, ReviewStatus } from "./types";

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
  source: "api" | "fixture";
}> {
  try {
    const reviews = await request<FieldDefinitionReview[]>("/api/field-definition-reviews");
    const runId = reviews[0]?.run_id;
    if (!runId) {
      return { reviews, run: fixtureRun, source: "api" };
    }
    const run = await request<AgentRun>(`/api/agent-runs/${encodeURIComponent(runId)}`);
    return { reviews, run, source: "api" };
  } catch {
    return { reviews: fixtureReviews, run: fixtureRun, source: "fixture" };
  }
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
  const body = action === "edit" ? JSON.stringify({ approved_field: field }) : undefined;
  await request(`/api/field-definition-reviews/${encodeURIComponent(reviewId)}/${action}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body,
  });
}

