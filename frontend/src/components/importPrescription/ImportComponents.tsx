import React from "react";
import { AlertOctagon, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type {
  CommitSummaryData,
  HealthUpdatesDraft,
  ImportEntityLink,
  ImportSession,
  MedicationDraftItem,
  PrescriptionDiff,
  ValidationIssue,
} from "../../features/importPrescription/types";
import {
  countBySeverity,
  getConfidenceLevel,
  sortIssues,
} from "../../features/importPrescription/validation";
import {
  ACTION_LABELS,
  ENTITY_LABELS,
  IMPORT_MODE_LABELS,
  SEVERITY_LABELS,
  STATUS_LABELS,
  formatDoseVi,
  summarizeCommit,
} from "../../features/importPrescription/mapping";

/* ------------------------------------------------------------------ */
/* OCRConfidenceBadge                                                  */
/* ------------------------------------------------------------------ */
export const OCRConfidenceBadge: React.FC<{ confidence?: number | null }> = ({ confidence }) => {
  if (confidence === null || confidence === undefined) return null;
  const level = getConfidenceLevel(confidence);
  const cls =
    level === "HIGH" ? "badge-success" : level === "MEDIUM" ? "badge-warning" : "badge-danger";
  const label = level === "HIGH" ? "Tin cậy cao" : level === "MEDIUM" ? "Trung bình" : "Thấp";
  return (
    <span className={`badge ${cls}`} title="Độ tin cậy OCR">
      {label} · {Math.round(confidence * 100)}%
    </span>
  );
};

/* ------------------------------------------------------------------ */
/* ConflictAlert                                                       */
/* ------------------------------------------------------------------ */
const severityIcon = (sev: string) => {
  if (sev === "BLOCKING") return <AlertOctagon size={16} />;
  if (sev === "ERROR") return <AlertTriangle size={16} />;
  if (sev === "WARNING") return <AlertTriangle size={16} />;
  return <Info size={16} />;
};

export const ConflictAlert: React.FC<{ issues: ValidationIssue[]; compact?: boolean }> = ({
  issues,
  compact,
}) => {
  if (!issues.length) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {sortIssues(issues).map((iss) => {
        const danger = iss.severity === "BLOCKING" || iss.severity === "ERROR";
        const info = iss.severity === "INFO";
        return (
          <div
            key={iss.id}
            className={`alert-banner ${danger ? "alert-danger" : info ? "" : "alert-warning"}`}
            style={{
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
              ...(info
                ? { background: "var(--pm-primary-light)", color: "var(--pm-text-primary)" }
                : {}),
            }}
            role={danger ? "alert" : "status"}
          >
            <span style={{ marginTop: 2 }}>{severityIcon(iss.severity)}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                [{SEVERITY_LABELS[iss.severity] || iss.severity}] {iss.message}
              </div>
              {!compact && iss.suggested_fix && (
                <div style={{ fontSize: "0.82rem", opacity: 0.85, marginTop: 2 }}>
                  Gợi ý: {iss.suggested_fix}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* ImportSummaryCard                                                   */
/* ------------------------------------------------------------------ */
export const ImportSummaryCard: React.FC<{ session: ImportSession }> = ({ session }) => {
  const counts = countBySeverity(session.validation_issues);
  const active = (session.review_payload?.items || []).filter((i) => i.action !== "SKIP").length;
  return (
    <div className="card" style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "center" }}>
      <div style={{ flex: "1 1 220px" }}>
        <div style={{ fontWeight: 700 }}>{session.source_filename}</div>
        <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
          Phiên #{session.id} · {session.source_type} · {IMPORT_MODE_LABELS[session.import_mode]}
        </div>
      </div>
      <span className={`badge ${session.status === "READY_TO_COMMIT" || session.status === "COMMITTED" ? "badge-success" : session.status === "REJECTED" ? "badge-neutral" : "badge-warning"}`}>
        {STATUS_LABELS[session.status] || session.status}
      </span>
      <OCRConfidenceBadge confidence={session.overall_confidence} />
      <span className="badge badge-primary">{active} thuốc</span>
      {counts.BLOCKING + counts.ERROR > 0 && (
        <span className="badge badge-danger">{counts.BLOCKING + counts.ERROR} lỗi cần xử lý</span>
      )}
      {counts.WARNING > 0 && <span className="badge badge-warning">{counts.WARNING} cảnh báo</span>}
      {session.is_duplicate && <span className="badge badge-warning">Tài liệu trùng</span>}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* FieldReviewRow                                                      */
/* ------------------------------------------------------------------ */
export const FieldReviewRow: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  confidence?: number;
  type?: string;
  disabled?: boolean;
}> = ({ label, value, onChange, confidence, type = "text", disabled }) => {
  const low = confidence !== undefined && getConfidenceLevel(confidence) === "LOW";
  return (
    <div className="form-group">
      <label className="form-label" style={{ display: "flex", gap: 8, alignItems: "center" }}>
        {label}
        {confidence !== undefined && <OCRConfidenceBadge confidence={confidence} />}
      </label>
      <input
        className="input"
        type={type}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        style={low ? { borderColor: "var(--pm-danger)", background: "var(--pm-danger-bg)" } : undefined}
      />
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* MedicationMatchCard                                                 */
/* ------------------------------------------------------------------ */
export const MedicationMatchCard: React.FC<{
  item: MedicationDraftItem;
  issues: ValidationIssue[];
  disabled?: boolean;
  onChange: (next: MedicationDraftItem) => void;
}> = ({ item, issues, disabled, onChange }) => {
  const set = <K extends keyof MedicationDraftItem>(k: K, v: MedicationDraftItem[K]) =>
    onChange({ ...item, [k]: v, user_edited: true });
  const skipped = item.action === "SKIP";
  const familyCandidates = (item.candidates || []).filter((c) => c.family_medication_id);

  return (
    <div className="card" style={{ opacity: skipped ? 0.6 : 1 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
        <div style={{ fontWeight: 700 }}>
          #{item.row_index + 1} · {item.medication_name || "(chưa có tên)"}
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <OCRConfidenceBadge confidence={item.confidence} />
          <span className="badge badge-neutral">{ACTION_LABELS[item.action || "CREATE_NEW"]}</span>
        </div>
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">Xử lý thuốc</label>
          <select
            className="select"
            value={item.action === "LINK_EXISTING" && item.family_medication_id ? `fm:${item.family_medication_id}` : item.action || "CREATE_NEW"}
            disabled={disabled}
            onChange={(e) => {
              const v = e.target.value;
              if (v.startsWith("fm:")) {
                onChange({ ...item, action: "LINK_EXISTING", family_medication_id: Number(v.slice(3)), user_edited: true });
              } else {
                onChange({
                  ...item,
                  action: v as MedicationDraftItem["action"],
                  family_medication_id: v === "CREATE_NEW" ? null : item.family_medication_id,
                  user_edited: true,
                });
              }
            }}
          >
            {familyCandidates.map((c) => (
              <option key={c.family_medication_id ?? c.name} value={`fm:${c.family_medication_id}`}>
                Dùng thuốc có sẵn: {c.name} {c.strength || ""} (còn {c.quantity ?? 0} {c.unit || ""})
              </option>
            ))}
            <option value="CREATE_NEW">Tạo thuốc mới trong tủ gia đình</option>
            <option value="SKIP">Bỏ qua dòng này</option>
          </select>
        </div>
        <FieldReviewRow
          label="Tên thuốc"
          value={item.medication_name || ""}
          disabled={disabled || skipped}
          confidence={item.field_confidences?.medication_name}
          onChange={(v) => set("medication_name", v)}
        />
      </div>

      {!skipped && (
        <>
          <div className="grid-4">
            <FieldReviewRow label="Hàm lượng" value={item.strength || ""} disabled={disabled} onChange={(v) => set("strength", v)} />
            <FieldReviewRow
              label="Liều/lần"
              type="number"
              value={item.dose_amount?.toString() ?? ""}
              disabled={disabled}
              confidence={item.field_confidences?.dose_amount}
              onChange={(v) => set("dose_amount", v === "" ? null : Number(v))}
            />
            <div className="form-group">
              <label className="form-label">Đơn vị</label>
              <select className="select" value={item.dose_unit || "tablet"} disabled={disabled} onChange={(e) => set("dose_unit", e.target.value)}>
                {["tablet", "capsule", "ml", "mg", "drop", "puff", "unit"].map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>
            <FieldReviewRow
              label="Số lần/ngày"
              type="number"
              value={item.frequency_per_day?.toString() ?? ""}
              disabled={disabled}
              confidence={item.field_confidences?.frequency_per_day}
              onChange={(v) => set("frequency_per_day", v === "" ? null : Number(v))}
            />
          </div>
          <div className="grid-2">
            <FieldReviewRow label="Hướng dẫn dùng" value={item.instructions || ""} disabled={disabled} onChange={(v) => set("instructions", v)} />
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Đường dùng</label>
                <select className="select" value={item.route || ""} disabled={disabled} onChange={(e) => set("route", e.target.value)}>
                  <option value="">Chọn đường dùng</option>
                  <option value="ORAL">Uống</option>
                  <option value="TOPICAL">Bôi ngoài da</option>
                  <option value="INHALATION">Hít / xịt</option>
                  <option value="INJECTION">Tiêm</option>
                  <option value="EYE">Mắt</option>
                  <option value="EAR">Tai</option>
                  <option value="NASAL">Mũi</option>
                  <option value="OTHER">Khác</option>
                </select>
              </div>
              <FieldReviewRow
                label="Số lượng nhập tủ"
                type="number"
                value={item.quantity?.toString() ?? ""}
                disabled={disabled || item.action === "LINK_EXISTING"}
                onChange={(v) => set("quantity", v === "" ? null : Number(v))}
              />
            </div>
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)", marginBottom: 8 }}>
            Tóm tắt liều: <strong>{formatDoseVi(item)}</strong>
          </div>
        </>
      )}
      <ConflictAlert issues={issues} compact />
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* PrescriptionDiffCard                                                */
/* ------------------------------------------------------------------ */
export const PrescriptionDiffCard: React.FC<{ diff: PrescriptionDiff }> = ({ diff }) => (
  <div className="card">
    <h3 style={{ marginBottom: 8 }}>
      So sánh với đơn #{diff.target_prescription_id} – {diff.target_prescription_title || "(không tiêu đề)"}
    </h3>
    {Object.keys(diff.metadata_changes).length > 0 && (
      <div style={{ marginBottom: 8 }}>
        <strong>Thông tin đơn thay đổi:</strong>
        <ul>
          {Object.entries(diff.metadata_changes).map(([k, v]) => (
            <li key={k}>
              {k}: <s>{String(v.previous ?? "—")}</s> → <strong>{String(v.proposed ?? "—")}</strong>
            </li>
          ))}
        </ul>
      </div>
    )}
    <div className="grid-2">
      <div>
        <div style={{ color: "var(--pm-success)", fontWeight: 600 }}>+ Thêm mới ({diff.added_items.length})</div>
        <ul>{diff.added_items.map((a, i) => <li key={i}>{String(a.medication_name)}</li>)}</ul>
        <div style={{ color: "var(--pm-warning)", fontWeight: 600 }}>~ Cập nhật ({diff.updated_items.length})</div>
        <ul>
          {diff.updated_items.map((u) => (
            <li key={u.existing_item_id}>
              {u.medication_name}:{" "}
              {Object.entries(u.changes).map(([k, c]) => `${k} ${String(c.previous)}→${String(c.proposed)}`).join(", ")}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <div style={{ color: "var(--pm-text-secondary)", fontWeight: 600 }}>
          = Giữ nguyên ({diff.unchanged_items.length + diff.retained_existing_items.length})
        </div>
        <ul>
          {diff.unchanged_items.map((u, i) => <li key={`u${i}`}>{String(u.medication_name)}</li>)}
          {diff.retained_existing_items.map((r) => (
            <li key={r.existing_item_id}>{r.medication_name} <em style={{ fontSize: "0.8rem" }}>(không tự động xóa)</em></li>
          ))}
        </ul>
      </div>
    </div>
  </div>
);

/* ------------------------------------------------------------------ */
/* SchedulePreview                                                     */
/* ------------------------------------------------------------------ */
export const SchedulePreview: React.FC<{ items: MedicationDraftItem[] }> = ({ items }) => {
  const rows = items
    .filter((i) => i.action !== "SKIP" && i.schedule?.create_schedule)
    .flatMap((i) => (i.schedule?.schedule_times || []).map((t) => ({ t, name: i.medication_name, dose: formatDoseVi(i) })))
    .sort((a, b) => a.t.localeCompare(b.t));
  if (!rows.length) {
    return <div style={{ color: "var(--pm-text-secondary)" }}>Chưa có lịch uống nào được thiết lập.</div>;
  }
  return (
    <div className="card">
      <h3 style={{ marginBottom: 8 }}>Xem trước lịch uống mỗi ngày</h3>
      {rows.map((r, idx) => (
        <div key={idx} style={{ display: "flex", gap: 12, padding: "6px 0", borderBottom: "1px solid var(--pm-border)" }}>
          <strong style={{ width: 60 }}>{r.t}</strong>
          <span>{r.name}</span>
          <span style={{ color: "var(--pm-text-secondary)", marginLeft: "auto" }}>{r.dose}</span>
        </div>
      ))}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* HealthUpdatePreview                                                 */
/* ------------------------------------------------------------------ */
export const HealthUpdatePreview: React.FC<{ health?: HealthUpdatesDraft | null }> = ({ health }) => {
  if (!health) return null;
  const conds = (health.conditions || []).filter((c) => c.confirmed && health.confirm_conditions);
  const alls = (health.allergies || []).filter((a) => a.confirmed && health.confirm_allergies);
  const rxs = (health.drug_reactions || []).filter((r) => r.confirmed && health.confirm_drug_reactions);
  if (!conds.length && !alls.length && !rxs.length) {
    return <div style={{ color: "var(--pm-text-secondary)" }}>Không cập nhật Hồ sơ sức khỏe.</div>;
  }
  return (
    <ul>
      {conds.map((c, i) => <li key={`c${i}`}>Bệnh lý: {c.name}</li>)}
      {alls.map((a, i) => <li key={`a${i}`}>Dị ứng: {a.allergen} ({a.severity})</li>)}
      {rxs.map((r, i) => <li key={`r${i}`}>Phản ứng thuốc: {r.drug_name} – {r.reaction}</li>)}
    </ul>
  );
};

/* ------------------------------------------------------------------ */
/* CommitSummary                                                       */
/* ------------------------------------------------------------------ */
export const CommitSummary: React.FC<{
  summary?: CommitSummaryData | null;
  links: ImportEntityLink[];
}> = ({ summary, links }) => {
  const lines = summarizeCommit(summary);
  return (
    <div className="card card-highlight">
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10, color: "var(--pm-success)" }}>
        <CheckCircle2 size={22} />
        <h3>Đã lưu đơn thuốc thành công</h3>
      </div>
      <ul>{lines.map((l) => <li key={l}>{l}</li>)}</ul>
      {links.length > 0 && (
        <details style={{ marginTop: 10 }}>
          <summary style={{ cursor: "pointer" }}>Nhật ký nguồn gốc dữ liệu ({links.length})</summary>
          <ul style={{ fontSize: "0.85rem" }}>
            {links.map((l) => (
              <li key={l.id}>
                {l.action} · {ENTITY_LABELS[l.entity_type] || l.entity_type} #{l.entity_id}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
};

