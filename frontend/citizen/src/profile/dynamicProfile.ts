export type ProfileValue = {
  value: unknown;
  updatedAt: string;
  validUntil?: string;
  source: "user_input";
  sensitivity: "low" | "medium" | "high";
};

export type LocalProfile = Record<string, ProfileValue>;

export type FieldDefinition = {
  key: string;
  label: string;
  data_type: "boolean" | "enum" | "number" | "date" | "string" | "list";
  allowed_values?: Array<{ value: unknown; label: string }>;
  question: string;
  sensitivity: ProfileValue["sensitivity"];
  validity_days?: number;
  review_status: "pending" | "approved" | "rejected";
};
