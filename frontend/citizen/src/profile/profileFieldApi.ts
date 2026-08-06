import type { ProfileFieldCatalogItem } from "./dynamicProfile";


type ProfileFieldResponse = {
  ok: boolean;
  json: () => Promise<unknown>;
};

type ProfileFieldRequest = () => Promise<ProfileFieldResponse>;


export async function loadProfileFieldCatalog(
  request: ProfileFieldRequest,
): Promise<ProfileFieldCatalogItem[]> {
  try {
    const response = await request();
    if (!response.ok) {
      throw new Error("Profile field API request failed.");
    }

    const payload = await response.json();
    if (!Array.isArray(payload)) {
      throw new Error("Profile field API response must be an array.");
    }

    return payload.filter(isProfileFieldCatalogItem)
      .sort((left, right) => left.display_order - right.display_order);
  } catch {
    return [];
  }
}


function isProfileFieldCatalogItem(value: unknown): value is ProfileFieldCatalogItem {
  return typeof value === "object" && value !== null &&
    "field_definition" in value && typeof value.field_definition === "object" && value.field_definition !== null &&
    "key" in value.field_definition && typeof value.field_definition.key === "string" &&
    "onboarding_group" in value && (value.onboarding_group === "core" || value.onboarding_group === "optional") &&
    "eligibility_usable" in value && typeof value.eligibility_usable === "boolean" &&
    "display_order" in value && typeof value.display_order === "number";
}
