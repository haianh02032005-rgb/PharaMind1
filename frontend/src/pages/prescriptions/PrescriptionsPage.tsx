import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, FileUp, PlusCircle } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";

interface PrescriptionRow {
  id: number;
  member_id: number;
  title: string;
  doctor_name?: string | null;
  facility_name?: string | null;
  diagnosis?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  status: string;
  items?: Array<{
    id: number;
    family_medication_id: number;
    dose_amount: number;
    dose_unit: string;
    frequency_per_day: number;
    instructions?: string | null;
  }>;
}

export const PrescriptionsPage: React.FC = () => {
  const { activeFamilyId, members } = useFamilyStore();
  const navigate = useNavigate();
  const [prescriptions, setPrescriptions] = useState<PrescriptionRow[]>([]);
  const [medications, setMedications] = useState<
    Array<{ id: number; catalog?: { name: string } }>
  >([]);

  const [showCreate, setShowCreate] = useState(false);
  const [memberId, setMemberId] = useState("");
  const [title, setTitle] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [medicationId, setMedicationId] = useState("");
  const [doseAmount, setDoseAmount] = useState("1");
  const [instructions, setInstructions] = useState("Uống sau ăn");
  const [busy, setBusy] = useState(false);

  const loadData = useCallback(async () => {
    if (!activeFamilyId) return;
    const [rxRes, medRes] = await Promise.all([
      apiRequest<{ items: PrescriptionRow[] }>(
        `/families/${activeFamilyId}/prescriptions`
      ).catch(() => ({ items: [] })),
      apiRequest<{ items: Array<{ id: number; catalog?: { name: string } }> }>(
        `/families/${activeFamilyId}/medications`
      ).catch(() => ({ items: [] })),
    ]);
    setPrescriptions(rxRes.items || []);
    setMedications(medRes.items || []);
  }, [activeFamilyId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !memberId || !title.trim()) return;
    setBusy(true);
    try {
      const rx = await apiRequest<PrescriptionRow>(
        `/families/${activeFamilyId}/prescriptions`,
        {
          method: "POST",
          body: JSON.stringify({
            member_id: Number(memberId),
            title: title.trim(),
            diagnosis: diagnosis.trim() || null,
            start_date: "2026-01-01",
            end_date: "2028-12-31",
          }),
        }
      );

      if (medicationId) {
        await apiRequest(
          `/families/${activeFamilyId}/prescriptions/${rx.id}/items`,
          {
            method: "POST",
            body: JSON.stringify({
              family_medication_id: Number(medicationId),
              dose_amount: Number(doseAmount) || 1,
              dose_unit: "TABLET",
              frequency_per_day: 2,
              instructions,
            }),
          }
        );
      }

      await loadData();
      setShowCreate(false);
      setTitle("");
      setDiagnosis("");
    } finally {
      setBusy(false);
    }
  };

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
            Quản lý Đơn thuốc Gia đình ({prescriptions.length})
          </h1>
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Lưu trữ đơn thuốc theo từng thành viên và kết nối trực tiếp với Lịch uống thuốc.
          </p>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => navigate("/import-prescription")}
          >
            <FileUp size={18} />
            Nhập từ ảnh / Excel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowCreate(!showCreate)}
          >
            <PlusCircle size={18} />
            Tạo Đơn thuốc mới
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="card">
          <h3 style={{ marginBottom: 14 }}>Tạo Đơn thuốc mới</h3>
          <form onSubmit={handleCreate}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Thành viên *</label>
                <select
                  className="select"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  required
                >
                  <option value="">-- Chọn thành viên --</option>
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.full_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Tiêu đề đơn thuốc *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="VD: Đơn thuốc huyết áp tháng 11"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Chẩn đoán / Ghi chú bác sĩ</label>
                <input
                  type="text"
                  className="input"
                  placeholder="VD: Tăng huyết áp vô căn"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Thuốc kê trong đơn (Tuỳ chọn)</label>
                <select
                  className="select"
                  value={medicationId}
                  onChange={(e) => setMedicationId(e.target.value)}
                >
                  <option value="">-- Chọn thuốc từ kho --</option>
                  {medications.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.catalog?.name || `Thuốc #${m.id}`}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Liều mỗi lần uống</label>
                <input
                  type="number"
                  className="input"
                  value={doseAmount}
                  onChange={(e) => setDoseAmount(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Hướng dẫn dùng</label>
                <input
                  type="text"
                  className="input"
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Đang lưu..." : "Lưu Đơn thuốc"}
            </button>
          </form>
        </div>
      )}

      <div className="grid-2">
        {prescriptions.map((rx) => {
          const memberName =
            members.find((m) => m.id === rx.member_id)?.full_name ||
            `Thành viên #${rx.member_id}`;
          return (
            <div key={rx.id} className="card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 8,
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
                  <FileText size={18} style={{ color: "var(--pm-primary)" }} />
                  <span>{rx.title}</span>
                </div>
                <span className="badge badge-primary">{rx.status}</span>
              </div>
              <p style={{ fontSize: "0.88rem", color: "var(--pm-text-secondary)" }}>
                Người dùng: <strong>{memberName}</strong>
                {rx.diagnosis ? ` • Chẩn đoán: ${rx.diagnosis}` : ""}
              </p>
              <div style={{ marginTop: 10, fontSize: "0.85rem" }}>
                Số thuốc trong đơn: <strong>{rx.items?.length || 0}</strong>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

