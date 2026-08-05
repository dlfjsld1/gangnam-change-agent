export type ReviewStatus = "pending" | "approved" | "rejected";

export interface FieldDefinition {
  key: string;
  label: string;
  data_type: "boolean" | "enum" | "number" | "date" | "string" | "list";
  allowed_values?: Array<{ value: unknown; label: string }>;
  question: string;
  sensitivity: "low" | "medium" | "high";
  validity_days?: number;
  review_status: ReviewStatus;
}

export interface FieldDefinitionReview {
  review_id: string;
  proposal: {
    proposed_field: FieldDefinition;
    review_required: true;
    review_reason: string;
  };
  status: ReviewStatus;
  approved_field: FieldDefinition | null;
  review_note: string | null;
  reviewed_at: string | null;
  run_id?: string;
  evidence?: {
    document_name: string;
    location: string;
    quote: string;
    source_url: string;
  };
  canonical_candidates?: FieldDefinition[];
}

export interface AgentRun {
  run_id: string;
  notice_id: string;
  status: "queued" | "running" | "completed" | "failed" | "review_required";
  node_logs: Array<{
    node: string;
    status: "started" | "completed" | "failed";
    message: string;
  }>;
  review_required: boolean;
  review_reason: string | null;
  unresolved_fields: string[];
  policy_id?: string | null;
}


export interface PolicyPackage {
  policy_id: string;
  title: string;
  summary: string;
  review: {
    status: ReviewStatus;
    reviewed_at: string | null;
  };
}

export interface AdminRunDetail {
  agent_run: AgentRun;
  policy_package: PolicyPackage | null;
  field_definition_reviews: FieldDefinitionReview[];
}
