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

export type ProfileFieldCatalogItem = {
  field_definition: FieldDefinition;
  onboarding_group: "core" | "optional";
  eligibility_usable: boolean;
  display_order: number;
};
