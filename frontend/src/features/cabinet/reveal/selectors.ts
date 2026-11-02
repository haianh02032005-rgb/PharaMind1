import {
  DrawerRevealData,
  DrawerRevealState,
  RevealMemberItem,
  RevealWarningItem,
} from "./types";

const UNIT_LABELS_VI: Record<string, string> = {
  TABLET: "viên",
  OVAL_TABLET: "viên",
  CAPSULE: "viên nang",
  SOFTGEL: "viên nang mềm",
  BOTTLE: "chai",
  SYRUP: "ml",
  SACHET: "gói",
  BLISTER: "vỉ",
  BOX: "hộp",
};

export function formatMedicationUnitVi(unit?: string | null): string {
  if (!unit) return "đơn vị";
  const upper = unit.toUpperCase();
  return UNIT_LABELS_VI[upper] || unit.toLowerCase();
}

export function formatExpirationMonthYear(dateStr?: string | null): string {
  if (!dateStr) return "Chưa cập nhật";
  const parts = dateStr.split("-");
  if (parts.length >= 2) {
    return `${parts[1]}/${parts[0]}`;
  }
  return dateStr;
}

/**
 * Formats a member's next schedule into friendly Vietnamese (`20:00 hôm nay` or `08:00 (2026-11-02)`).
 */
export function formatMemberScheduleLabelVi(
  member: RevealMemberItem,
  todayIso?: string
): string {
  const refToday = todayIso || new Date().toISOString().slice(0, 10);
  const timeStr = member.next_time || member.times?.[0] || null;
  if (!timeStr) {
    return "Chưa có lịch uống cụ thể.";
  }
  if (!member.next_date || member.next_date === refToday) {
    return `${timeStr} hôm nay`;
  }
  return `${timeStr} (${member.next_date})`;
}

/**
 * Returns true when the capsule fly-out / pop-out illustration should be shown (§9, §22, §24):
 * - Only when the compartment has a medication (`medication !== null`)
 * - And the drawer is open (`is_open === true`) or panel is actively triggered on a non-empty compartment.
 */
export function selectShouldShowCapsule(
  revealData: DrawerRevealData | null,
  isPanelOpen: boolean
): boolean {
  if (!revealData || !isPanelOpen) return false;
  if (!revealData.medication) return false;
  if (revealData.cabinet_status === "OFFLINE" && !revealData.is_open) {
    return false;
  }
  return revealData.is_open;
}

/**
 * Returns members sorted so that the member with the earliest upcoming schedule is first (§13).
 */
export function selectPrioritizedMembers(
  revealData: DrawerRevealData | null
): RevealMemberItem[] {
  if (!revealData || !revealData.members) return [];
  return [...revealData.members].sort((a, b) => {
    const hasA = a.next_time || a.times.length > 0 ? 0 : 1;
    const hasB = b.next_time || b.times.length > 0 ? 0 : 1;
    if (hasA !== hasB) return hasA - hasB;
    const timeA = a.next_time || a.times[0] || "99:99";
    const timeB = b.next_time || b.times[0] || "99:99";
    return timeA.localeCompare(timeB);
  });
}

/**
 * Extracts safety warnings (allergy / drug reaction / stock / expiry) with soft wording (§15, §37).
 */
export function selectSafetyWarnings(
  revealData: DrawerRevealData | null
): RevealWarningItem[] {
  if (!revealData || !revealData.warnings) return [];
  return revealData.warnings;
}

/**
 * Determines the contextual header badge for the reveal panel (§14, §24, §27).
 */
export function selectRevealContextEmphasis(state: DrawerRevealState): {
  title: string;
  variant: "warning" | "primary" | "neutral" | "success";
} {
  const data = state.revealData;
  if (data?.cabinet_status === "OFFLINE") {
    return {
      title: "Chế độ xem ngoại tuyến",
      variant: "neutral",
    };
  }
  if (state.openedBy === "SYSTEM" && data?.is_next_dose) {
    return {
      title: "⏰ Đến giờ uống thuốc",
      variant: "warning",
    };
  }
  if (data?.is_next_dose) {
    return {
      title: "⏰ Lần uống tiếp theo",
      variant: "warning",
    };
  }
  return {
    title: data?.is_open ? "Ngăn đang mở" : "Thông tin ngăn thuốc",
    variant: data?.is_open ? "success" : "primary",
  };
}

