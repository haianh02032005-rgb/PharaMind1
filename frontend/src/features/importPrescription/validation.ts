import type {
  ImportSession,
  ImportSourceType,
  MedicationDraftItem,
  ValidationIssue,
  ValidationSeverity,
} from "./types";

export const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "pdf", "xlsx", "csv"] as const;
export const MAX_PDF_BYTES = 20 * 1024 * 1024;
export const MAX_OTHER_BYTES = 10 * 1024 * 1024;

const TIME_RE = /^([01]?\d|2[0-3]):([0-5]\d)$/;

export function getFileExtension(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx + 1).toLowerCase() : "";
}

export function inferSourceType(name: string): ImportSourceType | null {
  const ext = getFileExtension(name);
  if (ext === "jpg" || ext === "jpeg" || ext === "png") return "OCR_IMAGE";
  if (ext === "pdf") return "OCR_PDF";
  if (ext === "xlsx") return "EXCEL_XLSX";
  if (ext === "csv") return "CSV";
  return null;
}

/** Client-side file validation (§6). Returns error message or null. */
export function validateImportFile(file: { name: string; size: number }): string | null {
  const ext = getFileExtension(file.name);
  if (!(ACCEPTED_EXTENSIONS as readonly string[]).includes(ext)) {
    return `Định dạng ".${ext || "?"}" không được hỗ trợ. Chỉ chấp nhận JPG, JPEG, PNG, PDF, XLSX, CSV.`;
  }
  if (file.size <= 0) return "Tệp tải lên bị rỗng.";
  const max = ext === "pdf" ? MAX_PDF_BYTES : MAX_OTHER_BYTES;
  if (file.size > max) {
    return `Kích thước tệp vượt quá ${Math.round(max / (1024 * 1024))}MB.`;
  }
  return null;
}

export function isValidTime(value: string): boolean {
  return TIME_RE.test(value.trim());
}

export function normalizeTime(value: string): string | null {
  const m = value.trim().match(TIME_RE);
  if (!m) return null;
  return `${m[1].padStart(2, "0")}:${m[2]}`;
}

/** Local schedule check mirroring backend §13 — never guesses times. */
export function getScheduleProblems(item: MedicationDraftItem): string[] {
  const problems: string[] = [];
  if (item.action === "SKIP" || !item.schedule?.create_schedule) return problems;
  const times = item.schedule.schedule_times || [];
  if (times.length === 0) problems.push("Vui lòng chọn giờ uống.");
  const seen = new Set<string>();
  for (const t of times) {
    const n = normalizeTime(t);
    if (!n) problems.push(`Giờ "${t}" không đúng định dạng HH:MM.`);
    else if (seen.has(n)) problems.push(`Giờ ${n} bị lặp.`);
    else seen.add(n);
  }
  if (!item.schedule.start_date) problems.push("Thiếu ngày bắt đầu.");
  return problems;
}

const SEVERITY_ORDER: Record<ValidationSeverity, number> = {
  BLOCKING: 0,
  ERROR: 1,
  WARNING: 2,
  INFO: 3,
};

export function sortIssues(issues: ValidationIssue[]): ValidationIssue[] {
  return [...issues].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
}

export function getBlockingIssues(issues: ValidationIssue[]): ValidationIssue[] {
  return issues.filter(
    (i) => !i.is_resolved && (i.severity === "BLOCKING" || i.severity === "ERROR")
  );
}

export function countBySeverity(issues: ValidationIssue[]): Record<ValidationSeverity, number> {
  const out: Record<ValidationSeverity, number> = { BLOCKING: 0, ERROR: 0, WARNING: 0, INFO: 0 };
  for (const i of issues) if (!i.is_resolved) out[i.severity] += 1;
  return out;
}

export function canCommit(session: ImportSession | null): boolean {
  if (!session) return false;
  if (session.status === "COMMITTED" || session.status === "REJECTED") return false;
  return getBlockingIssues(session.validation_issues).length === 0;
}

export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

/** §10.2: >=0.85 high, 0.70–0.85 medium, <0.70 low. */
export function getConfidenceLevel(confidence: number | null | undefined): ConfidenceLevel {
  const c = confidence ?? 1;
  if (c >= 0.85) return "HIGH";
  if (c >= 0.7) return "MEDIUM";
  return "LOW";
}

export function issuesForRow(issues: ValidationIssue[], rowIndex: number): ValidationIssue[] {
  const prefix = `items[${rowIndex}]`;
  return issues.filter((i) => i.field_path.startsWith(prefix));
}

