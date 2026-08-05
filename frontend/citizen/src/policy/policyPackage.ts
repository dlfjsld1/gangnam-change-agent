import type { EligibilityRule } from "../matcher/evaluateRule";
import type { FieldDefinition } from "../profile/dynamicProfile";


export type PolicyPackage = {
  policy_id: string;
  title: string;
  category: string;
  summary: string;
  eligibility_rule: EligibilityRule;
  required_profile_fields: FieldDefinition[];
  changes: Array<{
    change_id: string;
    label: string;
    before: unknown;
    after: unknown;
    impact_hint?: string;
  }>;
  required_actions: Array<{
    action_id: string;
    label: string;
    priority: number;
  }>;
  review: {
    status: "pending" | "approved" | "rejected";
  };
};
