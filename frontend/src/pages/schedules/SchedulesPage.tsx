import React, { useCallback, useEffect, useState } from "react";
import { CalendarClock, Clock, PlusCircle } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";

interface ScheduleRow {
  id: number;
  member_id: number;
  family_medication_id: number;
  recurrence_type: string;
  start_date: string;
  end_date?: string | null;
  status: string;
  times: string[];
  member?: { id: number; full_name: string };
  medication?: { id: number; name: string; strength?: string | null };
}

export const SchedulesPage: React.FC = () => {
  const { activeFamilyId, members } = useFamilyStore();
  const [schedules, setSchedules] = useState<ScheduleRow[]>([]);
  const [prescriptions, setPrescriptions] = useState<
    Array<{
      id: number;
      title: string;
      items?: Array<{ id: number; family_medication_id: number }>;
    }>
  >([]);

  const [showCreate, setShowCreate] = useState(false);
  const [rxItemId, setRxItemId] = useState("");
  const [timesStr, setTimesStr] = useState("08:00, 20:00");
  const [busy, setBusy] = useState(false);

  const loadSchedules = useCallback(async () => {
    if (!activeFamilyId) return;
    const [schedRes, rxRes] = await Promise.all([
      apiRequest<{ items: ScheduleRow[] }>(
        `/families/${activeFamilyId}/schedules`
      ).catch(() => ({ items: [] })),
      apiRequest<{ items: typeof prescriptions }>(
        `/families/${activeFamilyId}/prescriptions`
      ).catch(() => ({ items: [] })),
    ]);
    setSchedules(schedRes.items || []);
    setPrescriptions(rxRes.items || []);
  }, [activeFamilyId]);

  useEffect(() => {
    void loadSchedules();
  }, [loadSchedules]);

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !rxItemId) return;
    setBusy(true);
    try {
      const times = timesStr
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      await apiRequest(`/families/${activeFamilyId}/schedules`, {
        method: "POST",
        body: JSON.stringify({
          prescription_item_id: Number(rxItemId),
          start_date: "2026-01-01",
          end_date: "2028-12-31",
          recurrence_type: "DAILY",
          times,
        }),
      });
      await loadSchedules();
      setShowCreate(false);
    } finally {
      setBusy(false);
    }
  };

  const rxItemsFlat = prescriptions.flatMap((rx) =>
    (rx.items || []).map((it) => ({
      id: it.id,
      label: `${rx.title} — Mục thuốc #${it.id}`,
    }))
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.55rem", fontWeight: 700 }}>
            Lịch uống thuốc Gia đình ({schedules.length})
          </h1>
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Theo dõi lịch uống thuốc theo khung giờ Sáng / Trưa / Chiều / Tối và đồng bộ
            highlight ngăn tủ 3D.
          </p>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setShowCreate(!showCreate)}
        >
          <PlusCircle size={18} />
          Tạo Lịch uống thuốc
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Tạo Lịch uống từ Đơn thuốc</h3>
          <form onSubmit={handleCreateSchedule}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Mục thuốc trong đơn *</label>
                <select
                  className="select"
                  value={rxItemId}
                  onChange={(e) => setRxItemId(e.target.value)}
                  required
                >
                  <option value="">-- Chọn mục thuốc từ đơn thuốc --</option>
                  {rxItemsFlat.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">
                  Các khung giờ uống (HH:MM, cách nhau dấu phẩy)
                </label>
                <input
                  type="text"
                  className="input"
                  value={timesStr}
                  onChange={(e) => setTimesStr(e.target.value)}
                  required
                />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Lưu Lịch uống
            </button>
          </form>
        </div>
      )}

      {schedules.length === 0 ? (
        <div className="card">
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Chưa có lịch uống thuốc nào. Hãy tạo đơn thuốc trước hoặc dùng dữ liệu mẫu.
          </p>
        </div>
      ) : (
        <div className="grid-2">
          {schedules.map((sched) => {
            const memberName =
              sched.member?.full_name ||
              members.find((m) => m.id === sched.member_id)?.full_name ||
              `Thành viên #${sched.member_id}`;
            return (
              <div key={sched.id} className="card">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 10,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontWeight: 700,
                      fontSize: "1.08rem",
                    }}
                  >
                    <CalendarClock
                      size={19}
                      style={{ color: "var(--pm-primary)" }}
                    />
                    <span>
                      {sched.medication?.name ||
                        `Thuốc #${sched.family_medication_id}`}
                    </span>
                  </div>
                  <span className="badge badge-success">{sched.status}</span>
                </div>

                <p style={{ fontSize: "0.9rem", color: "var(--pm-text-secondary)" }}>
                  Thành viên: <strong>{memberName}</strong> • Tần suất:{" "}
                  <strong>{sched.recurrence_type}</strong>
                </p>

                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    flexWrap: "wrap",
                    marginTop: 12,
                  }}
                >
                  {sched.times.map((t) => (
                    <span key={t} className="badge badge-warning">
                      <Clock size={13} />
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

