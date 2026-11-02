import type {
  CommitSummaryData,
  DraftItemPatch,
  ImportMode,
  MedicationAction,
  MedicationDraftItem,
} from "./types";

export const IMPORT_MODE_LABELS: Record<ImportMode, string> = {
  CREATE_NEW_PRESCRIPTION: "Tạo đơn thuốc mới",
  UPDATE_EXISTING_PRESCRIPTION: "Cập nhật đơn thuốc hiện có",
  CREATE_MEDICATION_ONLY: "Chỉ thêm thuốc vào tủ (không tạo đơn)",
};

export const ACTION_LABELS: Record<MedicationAction, string> = {
  LINK_EXISTING: "Dùng thuốc có sẵn",
  CREATE_NEW: "Tạo thuốc mới",
  UPDATE_ITEM: "Cập nhật dòng thuốc",
  SKIP: "Bỏ qua",
};

export const SEVERITY_LABELS: Record<string, string> = {
  BLOCKING: "Chặn",
  ERROR: "Lỗi",
  WARNING: "Cảnh báo",
  INFO: "Thông tin",
};

export const STATUS_LABELS: Record<string, string> = {
  UPLOADED: "Đã tải lên",
  PARSING: "Đang phân tích",
  REVIEW_REQUIRED: "Cần rà soát",
  READY_TO_COMMIT: "Sẵn sàng lưu",
  COMMITTED: "Đã lưu",
  REJECTED: "Đã hủy",
  FAILED: "Thất bại",
};

export const ENTITY_LABELS: Record<string, string> = {
  Prescription: "Đơn thuốc",
  PrescriptionItem: "Dòng thuốc",
  MedicationCatalog: "Danh mục thuốc",
  FamilyMedication: "Thuốc gia đình",
  MemberMedication: "Liên kết thành viên",
  MedicationSchedule: "Lịch uống",
  MedicalCondition: "Bệnh lý",
  AllergyProfile: "Dị ứng",
  DrugReactionHistory: "Phản ứng thuốc",
  HealthProfile: "Hồ sơ sức khỏe",
};

/** Build a minimal PATCH item payload from an edited draft row. */
export function toDraftItemPatch(item: MedicationDraftItem): DraftItemPatch {
  return {
    row_index: item.row_index,
    action: item.action,
    family_medication_id: item.family_medication_id ?? null,
    catalog_id: item.catalog_id ?? null,
    medication_name: item.medication_name,
    strength: item.strength ?? null,
    dose_amount: item.dose_amount ?? null,
    dose_unit: item.dose_unit ?? null,
    frequency_per_day: item.frequency_per_day ?? null,
    frequency_text: item.frequency_text ?? null,
    route: item.route ?? null,
    instructions: item.instructions ?? null,
    quantity: item.quantity ?? null,
  };
}

export function toSchedulePatch(item: MedicationDraftItem): DraftItemPatch {
  return {
    row_index: item.row_index,
    create_schedule: item.schedule?.create_schedule ?? false,
    schedule_times: item.schedule?.schedule_times ?? [],
    start_date: item.schedule?.start_date ?? null,
    end_date: item.schedule?.end_date ?? null,
    reminder_enabled: item.schedule?.reminder_enabled ?? true,
  };
}

export function formatDoseVi(item: MedicationDraftItem): string {
  const amount = item.dose_amount ?? "?";
  const unitMap: Record<string, string> = {
    tablet: "viên",
    capsule: "viên nang",
    ml: "ml",
    mg: "mg",
    drop: "giọt",
    puff: "nhát xịt",
    unit: "đơn vị",
  };
  const unit = unitMap[(item.dose_unit || "").toLowerCase()] || item.dose_unit || "";
  const freq = item.frequency_per_day ? ` × ${item.frequency_per_day} lần/ngày` : "";
  return `${amount} ${unit}${freq}`.trim();
}

export function summarizeCommit(summary: CommitSummaryData | null | undefined): string[] {
  if (!summary) return [];
  const lines: string[] = [];
  const add = (n: number | undefined, label: string) => {
    if (n && n > 0) lines.push(`${n} ${label}`);
  };
  add(summary.prescriptions_created, "đơn thuốc mới");
  add(summary.prescriptions_updated, "đơn thuốc được cập nhật");
  add(summary.prescription_items_created, "dòng thuốc mới");
  add(summary.prescription_items_updated, "dòng thuốc được cập nhật");
  add(summary.family_medications_created, "thuốc mới trong tủ gia đình");
  add(summary.family_medications_linked, "thuốc có sẵn được liên kết");
  add(summary.schedules_created, "lịch uống thuốc");
  add(summary.conditions_created, "bệnh lý");
  add(summary.allergies_created, "dị ứng");
  add(summary.drug_reactions_created, "phản ứng thuốc");
  return lines;
}

