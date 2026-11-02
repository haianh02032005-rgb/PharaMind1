import React, { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import { useImportWizard } from "../../features/importPrescription/hooks";
import { toSchedulePatch } from "../../features/importPrescription/mapping";
import { getScheduleProblems, normalizeTime } from "../../features/importPrescription/validation";
import type { MedicationDraftItem, ScheduleDraft } from "../../features/importPrescription/types";
import { SchedulePreview } from "../../components/importPrescription/ImportComponents";

const defaultSchedule = (start?: string | null, end?: string | null): ScheduleDraft => ({
  create_schedule: false,
  recurrence_type: "DAILY",
  schedule_times: [],
  start_date: start ?? null,
  end_date: end ?? null,
  reminder_enabled: true,
  reminder_before_minutes: 15,
  grace_period_minutes: 30,
});

export const ScheduleStep: React.FC = () => {
  const w = useImportWizard();
  const review = w.session?.review_payload;
  const [items, setItems] = useState<MedicationDraftItem[]>([]);
  const [newTime, setNewTime] = useState<Record<number, string>>({});

  useEffect(() => {
    const rx = review?.prescription;
    setItems(
      (review?.items || []).map((i) => ({
        ...i,
        schedule: { ...defaultSchedule(rx?.start_date || rx?.issued_at, rx?.end_date), ...(i.schedule || {}) },
      }))
    );
  }, [review]);

  if (!w.session) return null;
  const active = items.filter((i) => i.action !== "SKIP");

  const updateSchedule = (row: number, patch: Partial<ScheduleDraft>) =>
    setItems((prev) =>
      prev.map((i) => (i.row_index === row ? { ...i, schedule: { ...(i.schedule as ScheduleDraft), ...patch } } : i))
    );

  const addTime = (item: MedicationDraftItem) => {
    const t = normalizeTime(newTime[item.row_index] || "");
    if (!t) return;
    const times = Array.from(new Set([...(item.schedule?.schedule_times || []), t])).sort();
    updateSchedule(item.row_index, { schedule_times: times, create_schedule: true });
    setNewTime((p) => ({ ...p, [item.row_index]: "" }));
  };

  const problemsCount = active.reduce((n, i) => n + getScheduleProblems(i).length, 0);

  const next = async () => {
    const s = await w.patch({ items: active.map(toSchedulePatch) });
    if (s) w.setStep(4);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="card">
        <h3 style={{ marginBottom: 6 }}>Bước 4 · Thiết lập giờ uống thuốc</h3>
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Hệ thống <strong>không tự đoán giờ uống</strong>. Nếu đơn chỉ ghi “2 lần/ngày”, hãy chọn giờ cụ thể hoặc tắt tạo lịch cho thuốc đó.
        </p>
      </div>

      {active.map((item) => {
        const sched = item.schedule as ScheduleDraft;
        const problems = getScheduleProblems(item);
        return (
          <div key={item.row_index} className="card">
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
              <div>
                <strong>{item.medication_name}</strong>
                <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
                  {item.frequency_text || (item.frequency_per_day ? `${item.frequency_per_day} lần/ngày` : "Chưa rõ tần suất")}
                </div>
              </div>
              <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={sched.create_schedule}
                  onChange={(e) => updateSchedule(item.row_index, { create_schedule: e.target.checked })}
                />
                Tạo lịch nhắc uống
              </label>
            </div>

            {sched.create_schedule && (
              <>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
                  {sched.schedule_times.map((t) => (
                    <span key={t} className="badge badge-primary" style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                      {t}
                      <X
                        size={12}
                        style={{ cursor: "pointer" }}
                        onClick={() => updateSchedule(item.row_index, { schedule_times: sched.schedule_times.filter((x) => x !== t) })}
                      />
                    </span>
                  ))}
                  <input
                    type="time"
                    className="input"
                    style={{ width: 130 }}
                    value={newTime[item.row_index] || ""}
                    onChange={(e) => setNewTime((p) => ({ ...p, [item.row_index]: e.target.value }))}
                  />
                  <button type="button" className="btn btn-sm btn-outline" onClick={() => addTime(item)}>
                    <Plus size={14} /> Thêm giờ
                  </button>
                </div>
                <div className="grid-3">
                  <div className="form-group">
                    <label className="form-label">Ngày bắt đầu</label>
                    <input type="date" className="input" value={sched.start_date || ""} onChange={(e) => updateSchedule(item.row_index, { start_date: e.target.value || null })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Ngày kết thúc</label>
                    <input type="date" className="input" value={sched.end_date || ""} onChange={(e) => updateSchedule(item.row_index, { end_date: e.target.value || null })} />
                  </div>
                  <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    <input type="checkbox" checked={sched.reminder_enabled} onChange={(e) => updateSchedule(item.row_index, { reminder_enabled: e.target.checked })} />
                    Bật nhắc nhở
                  </label>
                </div>
                {problems.map((p) => (
                  <div key={p} className="alert-banner alert-danger" style={{ marginTop: 6 }}>{p}</div>
                ))}
              </>
            )}
          </div>
        );
      })}

      <SchedulePreview items={active} />

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" className="btn btn-secondary" onClick={() => w.setStep(2)}>Quay lại</button>
        <button type="button" className="btn btn-primary" disabled={w.busy || problemsCount > 0} onClick={next}>
          Tiếp tục: Hồ sơ sức khỏe
        </button>
      </div>
    </div>
  );
};

