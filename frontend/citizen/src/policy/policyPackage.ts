import type { EligibilityRule } from "../matcher/evaluateRule";
import type { FieldDefinition } from "../profile/dynamicProfile";


export type PolicyPackage = {
  policy_id: string;
  title: string;
  eligibility_rule: EligibilityRule;
  required_profile_fields: FieldDefinition[];
  review: {
    status: "pending" | "approved" | "rejected";
  };
};
