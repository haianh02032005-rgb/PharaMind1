export type CabinetConnectionStatus = "ONLINE" | "OFFLINE" | "ARCHIVED";

export type CompartmentStatusType =
  | "EMPTY"
  | "AVAILABLE"
  | "LOW_STOCK"
  | "OPEN"
  | "ALERT"
  | "ERROR";

export type WarningCode =
  | "LOW_STOCK"
  | "DEPLETED"
  | "EXPIRING"
  | "EXPIRED"
  | "ALLERGY_RISK"
  | "DRUG_REACTION_RISK"
  | string;

export interface DigitalTwinCabinetHeader {
  id: number;
  name: string;
  device_code: string;
  status: CabinetConnectionStatus | string;
  hardware_mode: string;
  last_seen_at: string | null;
}

export interface DigitalTwinMedicationSummary {
  id: number;
  catalog_id: number;
  name: string;
  brand_name?: string | null;
  active_ingredient?: string | null;
  strength?: string | null;
  dosage_form?: string | null;
  quantity: number;
  unit: string;
  expiration_date?: string | null;
  status: string;
}

export interface DigitalTwinScheduleBrief {
  schedule_id: number;
  recurrence_type: string;
  times: string[];
  dose_amount?: number | null;
  dose_unit?: string | null;
  instructions?: string | null;
}

export interface DigitalTwinMemberSummary {
  id: number;
  full_name: string;
  relationship_label?: string | null;
  schedules: DigitalTwinScheduleBrief[];
  next_schedule?: string | null;
  next_dose_date?: string | null;
  next_dose_time?: string | null;
  next_dose_amount?: number | null;
  next_dose_unit?: string | null;
}

export interface DigitalTwinNextDose {
  schedule_id: number;
  date: string;
  time: string;
  member: {
    id: number;
    full_name: string;
  };
  dose_amount?: number | null;
  dose_unit?: string | null;
}

export interface DigitalTwinAllergyAlert {
  member_id: number;
  member_name: string;
  alert_type: "ALLERGY" | "DRUG_REACTION" | string;
  substance: string;
  severity?: string | null;
  reaction?: string | null;
  message: string;
}

export interface DigitalTwinCompartment {
  id: number;
  position: number;
  object_id: string;
  label?: string | null;
  status: CompartmentStatusType | string;
  is_open: boolean;
  led_state?: "ON" | "OFF";
  medication: DigitalTwinMedicationSummary | null;
  members: DigitalTwinMemberSummary[];
  next_dose: DigitalTwinNextDose | null;
  warnings: WarningCode[];
  allergy_alerts: DigitalTwinAllergyAlert[];
}

export interface DigitalTwinSummaryResponse {
  cabinet: DigitalTwinCabinetHeader;
  next_dose_position: number | null;
  next_dose: DigitalTwinNextDose | null;
  compartments: DigitalTwinCompartment[];
}

/**
 * Maps physical box position (1..6) to the 3D node name.
 */
export function positionToObjectId(position: number): string {
  const clamped = Math.max(1, Math.min(6, Math.floor(position)));
  return `drawer_${String(clamped).padStart(2, "0")}`;
}

/**
 * Maps a 3D drawer node name back to physical box position (1..6).
 */
export function objectIdToPosition(objectId: string): number | null {
  const match = /^drawer_0([1-6])$/.exec(objectId.trim());
  if (!match) return null;
  return Number(match[1]);
}

/**
 * Maps dosage form to 3D placeholder type inside a compartment.
 */
export function dosageFormToPlaceholderType(
  dosageForm?: string | null
): "TABLET" | "CAPSULE" | "BOTTLE" | "BLISTER" | "BOX" {
  const norm = (dosageForm || "").toUpperCase();
  if (norm === "CAPSULE" || norm === "SOFTGEL") return "CAPSULE";
  if (norm === "SYRUP" || norm === "DROPS" || norm === "BOTTLE")
    return "BOTTLE";
  if (norm === "SACHET" || norm === "BLISTER") return "BLISTER";
  if (norm === "TABLET" || norm === "OVAL_TABLET") return "TABLET";
  return "BOX";
}

