import type { FieldDefinition, LocalProfile } from "./dynamicProfile";


export function recordAnswer(
  profile: LocalProfile,
  field: FieldDefinition,
  value: unknown,
  today: string,
): LocalProfile {
  return {
    ...profile,
    [field.key]: {
      value,
      updatedAt: today,
      validUntil: field.validity_days
        ? addDays(today, field.validity_days)
        : undefined,
      source: "user_input",
      sensitivity: field.sensitivity,
    },
  };
}


function addDays(date: string, days: number): string {
  const result = new Date(`${date}T00:00:00Z`);
  result.setUTCDate(result.getUTCDate() + days);
  return result.toISOString().slice(0, 10);
}
