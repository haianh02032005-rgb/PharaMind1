import { describe, expect, it } from "vitest";
import {
  canCommit,
  countBySeverity,
  getBlockingIssues,
  getConfidenceLevel,
  getFileExtension,
  getScheduleProblems,
  inferSourceType,
  isValidTime,
  normalizeTime,
  sortIssues,
  validateImportFile,
} from "../src/features/importPrescription/validation";
import {
  formatDoseVi,
  summarizeCommit,
  toDraftItemPatch,
  toSchedulePatch,
} from "../src/features/importPrescription/mapping";
import { useImportWizardStore } from "../src/features/importPrescription/store";
import type {
  ImportSession,
  MedicationDraftItem,
  ValidationIssue,
} from "../src/features/importPrescription/types";

describe("FEATURE — Prescription Import Validation & Mapping", () => {
  describe("File validation & Type inference (§6, §27)", () => {
    it("extracts correct lowercase extension", () => {
      expect(getFileExtension("DonThuoc.PDF")).toBe("pdf");
      expect(getFileExtension("scan_prescription.JPEG")).toBe("jpeg");
      expect(getFileExtension("data.xlsx")).toBe("xlsx");
      expect(getFileExtension("no_ext")).toBe("");
    });

    it("infers proper import source type", () => {
      expect(inferSourceType("test.jpg")).toBe("OCR_IMAGE");
      expect(inferSourceType("test.png")).toBe("OCR_IMAGE");
      expect(inferSourceType("test.pdf")).toBe("OCR_PDF");
      expect(inferSourceType("template.xlsx")).toBe("EXCEL_XLSX");
      expect(inferSourceType("export.csv")).toBe("CSV");
      expect(inferSourceType("document.docx")).toBeNull();
    });

    it("validates file extension and size constraints", () => {
      // Valid files
      expect(validateImportFile({ name: "don_thuoc.png", size: 5 * 1024 * 1024 })).toBeNull();
      expect(validateImportFile({ name: "don_thuoc.pdf", size: 18 * 1024 * 1024 })).toBeNull();
      expect(validateImportFile({ name: "don_thuoc.xlsx", size: 2 * 1024 * 1024 })).toBeNull();

      // Empty file
      expect(validateImportFile({ name: "empty.png", size: 0 })).toContain("bị rỗng");

      // Unsupported extension
      expect(validateImportFile({ name: "don.exe", size: 100 })).toContain("không được hỗ trợ");

      // Over size limit (PDF > 20MB, other > 10MB)
      expect(validateImportFile({ name: "huge.pdf", size: 25 * 1024 * 1024 })).toContain(
        "vượt quá 20MB"
      );
      expect(validateImportFile({ name: "huge.png", size: 12 * 1024 * 1024 })).toContain(
        "vượt quá 10MB"
      );
    });
  });

  describe("Time parsing & Schedule validation (No-guessing rule §13)", () => {
    it("validates HH:MM 24-hour time strings", () => {
      expect(isValidTime("08:00")).toBe(true);
      expect(isValidTime("23:59")).toBe(true);
      expect(isValidTime("0:00")).toBe(true);
      expect(isValidTime("24:00")).toBe(false);
      expect(isValidTime("12:60")).toBe(false);
      expect(isValidTime("morning")).toBe(false);
    });

    it("normalizes time strings to zero-padded HH:MM", () => {
      expect(normalizeTime("8:00")).toBe("08:00");
      expect(normalizeTime("20:30")).toBe("20:30");
      expect(normalizeTime("invalid")).toBeNull();
    });

    it("emits error when schedule is enabled but schedule_times is empty (§13.3)", () => {
      const item: MedicationDraftItem = {
        row_index: 0,
        medication_name: "Amoxicillin 500mg",
        schedule: {
          create_schedule: true,
          recurrence_type: "DAILY",
          schedule_times: [], // empty -> must not guess!
          start_date: "2026-11-01",
          reminder_enabled: true,
          reminder_before_minutes: 15,
          grace_period_minutes: 30,
        },
      };

      const problems = getScheduleProblems(item);
      expect(problems).toContain("Vui lòng chọn giờ uống.");
    });

    it("detects duplicate schedule times", () => {
      const item: MedicationDraftItem = {
        row_index: 0,
        medication_name: "Paracetamol 500mg",
        schedule: {
          create_schedule: true,
          recurrence_type: "DAILY",
          schedule_times: ["08:00", "08:00"],
          start_date: "2026-11-01",
          reminder_enabled: true,
          reminder_before_minutes: 15,
          grace_period_minutes: 30,
        },
      };

      const problems = getScheduleProblems(item);
      expect(problems.some((p) => p.includes("bị lặp"))).toBe(true);
    });

    it("passes cleanly when times and start_date are properly specified", () => {
      const item: MedicationDraftItem = {
        row_index: 0,
        medication_name: "Paracetamol 500mg",
        schedule: {
          create_schedule: true,
          recurrence_type: "DAILY",
          schedule_times: ["08:00", "20:00"],
          start_date: "2026-11-01",
          reminder_enabled: true,
          reminder_before_minutes: 15,
          grace_period_minutes: 30,
        },
      };

      expect(getScheduleProblems(item)).toHaveLength(0);
    });
  });

  describe("OCR Confidence Classification (§10.2)", () => {
    it("categorizes high, medium, and low confidence correctly", () => {
      expect(getConfidenceLevel(0.95)).toBe("HIGH");
      expect(getConfidenceLevel(0.85)).toBe("HIGH");
      expect(getConfidenceLevel(0.84)).toBe("MEDIUM");
      expect(getConfidenceLevel(0.70)).toBe("MEDIUM");
      expect(getConfidenceLevel(0.69)).toBe("LOW");
      expect(getConfidenceLevel(0.40)).toBe("LOW");
      expect(getConfidenceLevel(undefined)).toBe("HIGH");
    });
  });

  describe("Validation Issues & Commit Gate (§18, §23)", () => {
    it("sorts issues by severity (BLOCKING > ERROR > WARNING > INFO)", () => {
      const issues: ValidationIssue[] = [
        {
          id: 1,
          import_session_id: 10,
          severity: "WARNING",
          code: "W1",
          field_path: "f",
          message: "Warn",
          is_resolved: false,
        },
        {
          id: 2,
          import_session_id: 10,
          severity: "BLOCKING",
          code: "B1",
          field_path: "f",
          message: "Block",
          is_resolved: false,
        },
        {
          id: 3,
          import_session_id: 10,
          severity: "INFO",
          code: "I1",
          field_path: "f",
          message: "Info",
          is_resolved: false,
        },
        {
          id: 4,
          import_session_id: 10,
          severity: "ERROR",
          code: "E1",
          field_path: "f",
          message: "Err",
          is_resolved: false,
        },
      ];

      const sorted = sortIssues(issues);
      expect(sorted.map((i) => i.severity)).toEqual([
        "BLOCKING",
        "ERROR",
        "WARNING",
        "INFO",
      ]);
    });

    it("filters blocking/error issues and enforces canCommit condition", () => {
      const mockSession = (
        status: string,
        issues: Array<{ severity: ValidationIssue["severity"]; code: string }>
      ): ImportSession =>
        ({
          id: 1,
          family_id: 1,
          member_id: 1,
          source_type: "OCR_IMAGE",
          source_filename: "doc.png",
          source_hash: "abc",
          status,
          import_mode: "CREATE_NEW_PRESCRIPTION",
          parser_version: "1.0",
          is_duplicate: false,
          created_at: "2026-11-01T00:00:00Z",
          items: [],
          validation_issues: issues.map((iss, idx) => ({
            id: idx + 1,
            import_session_id: 1,
            severity: iss.severity,
            code: iss.code,
            field_path: "test",
            message: "msg",
            is_resolved: false,
          })),
          entity_links: [],
        } as unknown as ImportSession);

      // Session with BLOCKING issue cannot commit
      const sessionBlocked = mockSession("REVIEW_REQUIRED", [
        { severity: "BLOCKING", code: "MEMBER_MISMATCH" },
      ]);
      expect(getBlockingIssues(sessionBlocked.validation_issues)).toHaveLength(1);
      expect(canCommit(sessionBlocked)).toBe(false);

      // Session with only WARNING can commit
      const sessionWarnOnly = mockSession("READY_TO_COMMIT", [
        { severity: "WARNING", code: "DUPLICATE_FILE" },
      ]);
      expect(getBlockingIssues(sessionWarnOnly.validation_issues)).toHaveLength(0);
      expect(canCommit(sessionWarnOnly)).toBe(true);

      // Already committed session cannot be re-committed
      const sessionCommitted = mockSession("COMMITTED", []);
      expect(canCommit(sessionCommitted)).toBe(false);
    });

    it("counts issues correctly by severity", () => {
      const issues: ValidationIssue[] = [
        {
          id: 1,
          import_session_id: 1,
          severity: "BLOCKING",
          code: "B",
          field_path: "f",
          message: "m",
          is_resolved: false,
        },
        {
          id: 2,
          import_session_id: 1,
          severity: "WARNING",
          code: "W",
          field_path: "f",
          message: "m",
          is_resolved: false,
        },
        {
          id: 3,
          import_session_id: 1,
          severity: "WARNING",
          code: "W2",
          field_path: "f",
          message: "m",
          is_resolved: false,
        },
      ];
      const counts = countBySeverity(issues);
      expect(counts.BLOCKING).toBe(1);
      expect(counts.WARNING).toBe(2);
      expect(counts.ERROR).toBe(0);
      expect(counts.INFO).toBe(0);
    });
  });

  describe("Payload Mapping & Formatting", () => {
    it("formats Vietnamese dose summary", () => {
      const item: MedicationDraftItem = {
        row_index: 0,
        medication_name: "Panadol",
        dose_amount: 2,
        dose_unit: "tablet",
        frequency_per_day: 3,
      };
      expect(formatDoseVi(item)).toBe("2 viên × 3 lần/ngày");
    });

    it("converts draft item to patch payload", () => {
      const item: MedicationDraftItem = {
        row_index: 2,
        medication_name: "Metformin",
        dose_amount: 1,
        dose_unit: "tablet",
        frequency_per_day: 2,
        action: "LINK_EXISTING",
        family_medication_id: 42,
      };
      const patch = toDraftItemPatch(item);
      expect(patch.row_index).toBe(2);
      expect(patch.action).toBe("LINK_EXISTING");
      expect(patch.family_medication_id).toBe(42);
      expect(patch.medication_name).toBe("Metformin");
    });

    it("converts schedule to patch payload", () => {
      const item: MedicationDraftItem = {
        row_index: 0,
        medication_name: "Test",
        schedule: {
          create_schedule: true,
          recurrence_type: "DAILY",
          schedule_times: ["08:00"],
          start_date: "2026-11-01",
          end_date: "2026-11-07",
          reminder_enabled: true,
          reminder_before_minutes: 15,
          grace_period_minutes: 30,
        },
      };
      const schedPatch = toSchedulePatch(item);
      expect(schedPatch.create_schedule).toBe(true);
      expect(schedPatch.schedule_times).toEqual(["08:00"]);
      expect(schedPatch.start_date).toBe("2026-11-01");
    });

    it("summarizes commit counts cleanly", () => {
      const summary = {
        catalogs_created: 1,
        family_medications_created: 1,
        family_medications_linked: 0,
        member_medications_linked: 1,
        prescriptions_created: 1,
        prescriptions_updated: 0,
        prescription_items_created: 2,
        prescription_items_updated: 0,
        schedules_created: 2,
        conditions_created: 1,
        allergies_created: 1,
        drug_reactions_created: 0,
      };
      const lines = summarizeCommit(summary);
      expect(lines).toContain("1 đơn thuốc mới");
      expect(lines).toContain("2 dòng thuốc mới");
      expect(lines).toContain("2 lịch uống thuốc");
      expect(lines).toContain("1 bệnh lý");
      expect(lines).toContain("1 dị ứng");
    });
  });

  describe("Import Wizard Store", () => {
    it("handles step transitions and resets cleanly", () => {
      const store = useImportWizardStore.getState();
      store.reset();
      expect(useImportWizardStore.getState().step).toBe(0);

      store.setStep(2);
      expect(useImportWizardStore.getState().step).toBe(2);

      store.setMemberId(5);
      expect(useImportWizardStore.getState().memberId).toBe(5);

      store.setImportMode("UPDATE_EXISTING_PRESCRIPTION");
      expect(useImportWizardStore.getState().importMode).toBe(
        "UPDATE_EXISTING_PRESCRIPTION"
      );

      store.reset();
      expect(useImportWizardStore.getState().step).toBe(0);
      expect(useImportWizardStore.getState().memberId).toBeNull();
      expect(useImportWizardStore.getState().importMode).toBe(
        "CREATE_NEW_PRESCRIPTION"
      );
    });
  });
});

