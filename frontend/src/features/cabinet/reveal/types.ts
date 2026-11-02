import {
  DigitalTwinCompartment,
  DigitalTwinMedicationSummary,
  DigitalTwinNextDose,
} from "../../digitalTwin/types";

export type AnimationMode = "FULL" | "REDUCED";
export type OpenedBySource = "USER" | "SYSTEM" | null;

export interface RevealMemberItem {
  id: number;
  full_name: string;
  relationship_label?: string | null;
  dose_amount?: number | null;
  dose_unit?: string | null;
  next_schedule?: string | null;
  next_date?: string | null;
  next_time?: string | null;
  times: string[];
  instructions?: string | null;
}

export interface RevealWarningItem {
  type:
    | "ALLERGY_WARNING"
    | "DRUG_REACTION_WARNING"
    | "LOW_STOCK_WARNING"
    | "DEPLETED_WARNING"
    | "EXPIRING_WARNING"
    | "EXPIRED_WARNING"
    | string;
  severity?: string | null;
  member_id?: number | null;
  member_name?: string | null;
  substance?: string | null;
  message: string;
}

export interface DrawerRevealData {
  cabinet_id: number;
  cabinet_status: string;
  position: number;
  object_id: string;
  label?: string | null;
  status: string;
  is_open: boolean;
  is_next_dose: boolean;
  medication: DigitalTwinMedicationSummary | null;
  members: RevealMemberItem[];
  next_dose: DigitalTwinNextDose | null;
  warnings: RevealWarningItem[];
}

export type DrawerRevealState = {
  selectedPosition: number | null;
  isPanelOpen: boolean;
  isAnimating: boolean;
  animationMode: AnimationMode;
  revealData: DrawerRevealData | null;
  openedBy: OpenedBySource;
  isLoading: boolean;
  error: string | null;
};

/**
 * Converts a cached `DigitalTwinCompartment` into `DrawerRevealData`
 * so the reveal panel & capsule fly-out can render immediately (including when cabinet is OFFLINE §24).
 */
export function buildRevealDataFromCompartment(
  comp: DigitalTwinCompartment,
  cabinetId = 0,
  cabinetStatus = "ONLINE",
  nextDosePosition: number | null = null
): DrawerRevealData {
  const members: RevealMemberItem[] = comp.members.map((m) => {
    const firstSched = m.schedules?.[0];
    const allTimes = Array.from(
      new Set((m.schedules || []).flatMap((s) => s.times || []))
    ).sort();
    return {
      id: m.id,
      full_name: m.full_name,
      relationship_label: m.relationship_label,
      dose_amount: m.next_dose_amount ?? firstSched?.dose_amount ?? 1,
      dose_unit:
        m.next_dose_unit ??
        firstSched?.dose_unit ??
        comp.medication?.unit ??
        "TABLET",
      next_schedule:
        m.next_dose_date && m.next_dose_time
          ? `${m.next_dose_date}T${m.next_dose_time}:00`
          : m.next_schedule || null,
      next_date: m.next_dose_date || null,
      next_time: m.next_dose_time || m.next_schedule || null,
      times: allTimes,
      instructions: firstSched?.instructions ?? null,
    };
  });

  // Sort members: earliest schedule first (§13)
  members.sort((a, b) => {
    const hasA = a.next_time ? 0 : 1;
    const hasB = b.next_time ? 0 : 1;
    if (hasA !== hasB) return hasA - hasB;
    return (a.next_time || "99:99").localeCompare(b.next_time || "99:99");
  });

  const warnings: RevealWarningItem[] = [];
  for (const alert of comp.allergy_alerts || []) {
    warnings.push({
      type:
        alert.alert_type === "ALLERGY"
          ? "ALLERGY_WARNING"
          : "DRUG_REACTION_WARNING",
      severity: alert.severity,
      member_id: alert.member_id,
      member_name: alert.member_name,
      substance: alert.substance,
      message: `⚠ Thành viên ${alert.member_name} có tiền sử ${
        alert.alert_type === "ALLERGY" ? "dị ứng" : "phản ứng thuốc"
      } với ${alert.substance}. Vui lòng kiểm tra trước khi dùng thuốc.`,
    });
  }

  if (comp.warnings.includes("LOW_STOCK") && comp.medication) {
    warnings.push({
      type: "LOW_STOCK_WARNING",
      severity: "MODERATE",
      message: `⚠ Thuốc ${comp.medication.name} sắp hết (còn ${comp.medication.quantity} ${comp.medication.unit}).`,
    });
  }
  if (comp.warnings.includes("DEPLETED") && comp.medication) {
    warnings.push({
      type: "DEPLETED_WARNING",
      severity: "SEVERE",
      message: `⚠ Thuốc ${comp.medication.name} trong ngăn đã hết.`,
    });
  }
  if (comp.warnings.includes("EXPIRED") && comp.medication) {
    warnings.push({
      type: "EXPIRED_WARNING",
      severity: "SEVERE",
      message: `⚠ Thuốc ${comp.medication.name} đã quá hạn sử dụng (${comp.medication.expiration_date}). Vui lòng kiểm tra trước khi dùng.`,
    });
  } else if (comp.warnings.includes("EXPIRING") && comp.medication) {
    warnings.push({
      type: "EXPIRING_WARNING",
      severity: "MODERATE",
      message: `⚠ Thuốc ${comp.medication.name} sắp đến hạn sử dụng (${comp.medication.expiration_date}).`,
    });
  }

  return {
    cabinet_id: cabinetId,
    cabinet_status: cabinetStatus,
    position: comp.position,
    object_id: comp.object_id,
    label: comp.label,
    status: comp.status,
    is_open: comp.is_open,
    is_next_dose: nextDosePosition === comp.position,
    medication: comp.medication,
    members,
    next_dose: comp.next_dose,
    warnings,
  };
}

