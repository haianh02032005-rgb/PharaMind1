export type ImportSourceType = "OCR_IMAGE" | "OCR_PDF" | "EXCEL_XLSX" | "CSV";

export type ImportStatus =
  | "UPLOADED"
  | "PARSING"
  | "REVIEW_REQUIRED"
  | "READY_TO_COMMIT"
  | "COMMITTED"
  | "REJECTED"
  | "FAILED";

export type ImportMode =
  | "CREATE_NEW_PRESCRIPTION"
  | "UPDATE_EXISTING_PRESCRIPTION"
  | "CREATE_MEDICATION_ONLY";

export type ValidationSeverity = "INFO" | "WARNING" | "ERROR" | "BLOCKING";

export type MedicationAction = "LINK_EXISTING" | "CREATE_NEW" | "UPDATE_ITEM" | "SKIP";

export interface ValidationIssue {
  id: number;
  import_session_id: number;
  import_item_id?: number | null;
  severity: ValidationSeverity;
  code: string;
  field_path: string;
  message: string;
  suggested_fix?: string | null;
  is_resolved: boolean;
}

export interface ScheduleDraft {
  create_schedule: boolean;
  recurrence_type: string;
  schedule_times: string[];
  start_date?: string | null;
  end_date?: string | null;
  reminder_enabled: boolean;
  reminder_before_minutes: number;
  grace_period_minutes: number;
}

export interface MedicationCandidate {
  type: "FAMILY_MEDICATION" | "MEDICATION_CATALOG";
  family_medication_id?: number | null;
  catalog_id?: number | null;
  name: string;
  active_ingredient?: string | null;
  strength?: string | null;
  dosage_form?: string | null;
  quantity?: number;
  unit?: string;
  linked_to_member?: boolean;
  match_type: string;
}

export interface MedicationDraftItem {
  row_index: number;
  medication_name: string;
  active_ingredient?: string | null;
  strength?: string | null;
  dosage_form?: string | null;
  dose_amount?: number | null;
  dose_unit?: string | null;
  frequency_per_day?: number | null;
  frequency_text?: string | null;
  route?: string | null;
  instructions?: string | null;
  quantity?: number | null;
  unit?: string | null;
  expiration_date?: string | null;
  confidence?: number;
  field_confidences?: Record<string, number>;
  action?: MedicationAction;
  resolution_status?: string;
  family_medication_id?: number | null;
  catalog_id?: number | null;
  candidates?: MedicationCandidate[];
  allergy_warnings?: string[];
  reaction_warnings?: string[];
  schedule?: ScheduleDraft;
  user_edited?: boolean;
}

export interface PrescriptionDraft {
  member_name?: string | null;
  member_identifier?: string | null;
  title?: string | null;
  doctor_name?: string | null;
  facility_name?: string | null;
  issued_at?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  notes?: string | null;
  field_confidences?: Record<string, number>;
}

export interface HealthConditionCandidate {
  name: string;
  diagnosed_at?: string | null;
  status: string;
  notes?: string | null;
  confirmed: boolean;
}

export interface AllergyCandidate {
  allergen: string;
  allergy_type: string;
  severity: string;
  reaction_description?: string | null;
  notes?: string | null;
  confirmed: boolean;
}

export interface DrugReactionCandidate {
  drug_name: string;
  active_ingredient?: string | null;
  reaction: string;
  severity: string;
  occurred_at?: string | null;
  notes?: string | null;
  confirmed: boolean;
}

export interface HealthUpdatesDraft {
  confirm_conditions: boolean;
  conditions: HealthConditionCandidate[];
  confirm_allergies: boolean;
  allergies: AllergyCandidate[];
  confirm_drug_reactions: boolean;
  drug_reactions: DrugReactionCandidate[];
  has_no_known_allergy_note?: boolean;
  general_notes_append?: string | null;
}

export interface MemberResolution {
  selected_member_id: number;
  selected_member_name: string;
  extracted_member_name?: string | null;
  name_matched: boolean;
  match_score: number;
  is_resolved: boolean;
  user_confirmed_override?: boolean;
}

export interface PrescriptionDiff {
  target_prescription_id: number;
  target_prescription_title?: string | null;
  target_prescription_status: string;
  metadata_changes: Record<string, { previous: unknown; proposed: unknown }>;
  added_items: Array<Record<string, unknown>>;
  updated_items: Array<{
    row_index: number;
    existing_item_id: number;
    medication_name: string;
    changes: Record<string, { previous: unknown; proposed: unknown }>;
  }>;
  unchanged_items: Array<Record<string, unknown>>;
  retained_existing_items: Array<{ existing_item_id: number; medication_name: string; note: string }>;
}

export interface ReviewPayload {
  member_resolution?: MemberResolution;
  prescription?: PrescriptionDraft;
  items?: MedicationDraftItem[];
  health_updates?: HealthUpdatesDraft;
  prescription_diff?: PrescriptionDiff | null;
  duplicate_acknowledged?: boolean;
}

export interface ImportEntityLink {
  id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  previous_snapshot?: Record<string, unknown> | null;
  new_snapshot?: Record<string, unknown> | null;
  created_at: string;
}

export interface CommitSummaryData {
  catalogs_created: number;
  family_medications_created: number;
  family_medications_linked: number;
  member_medications_linked: number;
  prescriptions_created: number;
  prescriptions_updated: number;
  prescription_items_created: number;
  prescription_items_updated: number;
  schedules_created: number;
  conditions_created: number;
  allergies_created: number;
  drug_reactions_created: number;
  prescription_id?: number | null;
  committed_at?: string;
}

export interface ImportSession {
  id: number;
  family_id: number;
  member_id: number;
  source_type: ImportSourceType;
  source_filename: string;
  source_hash: string;
  status: ImportStatus;
  import_mode: ImportMode;
  overall_confidence?: number | null;
  parser_version: string;
  review_payload?: ReviewPayload | null;
  commit_summary?: CommitSummaryData | null;
  target_prescription_id?: number | null;
  is_duplicate: boolean;
  duplicate_of_import_id?: number | null;
  created_at: string;
  committed_at?: string | null;
  items: Array<{ id: number; row_index: number; confidence?: number | null; resolution_status: string }>;
  validation_issues: ValidationIssue[];
  entity_links: ImportEntityLink[];
}

export interface DraftItemPatch {
  row_index: number;
  action?: MedicationAction;
  family_medication_id?: number | null;
  catalog_id?: number | null;
  medication_name?: string;
  strength?: string | null;
  dose_amount?: number | null;
  dose_unit?: string | null;
  frequency_per_day?: number | null;
  frequency_text?: string | null;
  route?: string | null;
  instructions?: string | null;
  quantity?: number | null;
  create_schedule?: boolean;
  schedule_times?: string[];
  start_date?: string | null;
  end_date?: string | null;
  reminder_enabled?: boolean;
}

export interface DraftUpdateRequest {
  import_mode?: ImportMode;
  target_prescription_id?: number | null;
  confirm_member_match?: boolean;
  confirm_duplicate_override?: boolean;
  prescription?: Partial<PrescriptionDraft>;
  items?: DraftItemPatch[];
  health_updates?: Partial<HealthUpdatesDraft>;
}

export interface CommitRequest {
  confirm_member_id: number;
  confirm_import_mode: ImportMode;
  confirm_schedule_creation: boolean;
  confirm_health_updates: boolean;
  confirm_ocr_review: boolean;
}

export type WizardStep = 0 | 1 | 2 | 3 | 4 | 5;

export const WIZARD_STEPS: Array<{ key: WizardStep; label: string }> = [
  { key: 0, label: "Thành viên" },
  { key: 1, label: "Tải tài liệu" },
  { key: 2, label: "Rà soát" },
  { key: 3, label: "Lịch uống" },
  { key: 4, label: "Hồ sơ sức khỏe" },
  { key: 5, label: "Xác nhận" },
];

