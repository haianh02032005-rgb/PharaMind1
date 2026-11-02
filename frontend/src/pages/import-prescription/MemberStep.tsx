import React, { useEffect, useState } from "react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";
import { useImportWizard } from "../../features/importPrescription/hooks";
import { IMPORT_MODE_LABELS } from "../../features/importPrescription/mapping";
import type { ImportMode } from "../../features/importPrescription/types";

interface RxOption {
  id: number;
  title?: string | null;
  status: string;
}

export const MemberStep: React.FC = () => {
  const members = useFamilyStore((s) => s.members);
  const w = useImportWizard();
  const [prescriptions, setPrescriptions] = useState<RxOption[]>([]);

  useEffect(() => {
    if (!w.familyId || !w.memberId) {
      setPrescriptions([]);
      return;
    }
    apiRequest<{ items: RxOption[] }>(
      `/families/${w.familyId}/prescriptions?member_id=${w.memberId}`
    )
      .then((r) => setPrescriptions((r.items || []).filter((p) => p.status === "ACTIVE")))
      .catch(() => setPrescriptions([]));
  }, [w.familyId, w.memberId]);

  const activeMembers = members.filter((m) => m.status !== "INACTIVE" && m.status !== "ARCHIVED");
  const needsTarget = w.importMode === "UPDATE_EXISTING_PRESCRIPTION";
  const canContinue = !!w.memberId && (!needsTarget || !!w.targetPrescriptionId);

  return (
    <div className="card">
      <h3 style={{ marginBottom: 6 }}>Bước 1 · Chọn thành viên nhận đơn thuốc</h3>
      <p style={{ color: "var(--pm-text-secondary)", marginBottom: 14 }}>
        Dữ liệu chỉ được lưu vào hồ sơ của thành viên bạn chọn sau khi bạn xác nhận ở bước cuối.
      </p>

      <div className="grid-3" style={{ marginBottom: 16 }}>
        {activeMembers.map((m) => (
          <button
            key={m.id}
            type="button"
            className={`card ${w.memberId === m.id ? "card-highlight" : ""}`}
            style={{ textAlign: "left", cursor: "pointer", borderWidth: w.memberId === m.id ? 2 : 1 }}
            onClick={() => {
              w.setMemberId(m.id);
              w.setTargetPrescriptionId(null);
            }}
          >
            <div style={{ fontWeight: 700 }}>{m.full_name}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
              {m.relationship_label || "Thành viên"}
            </div>
          </button>
        ))}
        {activeMembers.length === 0 && <div>Chưa có thành viên nào. Hãy thêm thành viên ở mục Gia đình.</div>}
      </div>

      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">Chế độ nhập</label>
          <select
            className="select"
            value={w.importMode}
            onChange={(e) => w.setImportMode(e.target.value as ImportMode)}
          >
            {(Object.keys(IMPORT_MODE_LABELS) as ImportMode[]).map((k) => (
              <option key={k} value={k}>{IMPORT_MODE_LABELS[k]}</option>
            ))}
          </select>
        </div>
        {needsTarget && (
          <div className="form-group">
            <label className="form-label">Đơn thuốc cần cập nhật *</label>
            <select
              className="select"
              value={w.targetPrescriptionId ?? ""}
              onChange={(e) => w.setTargetPrescriptionId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">-- Chọn đơn thuốc đang ACTIVE --</option>
              {prescriptions.map((p) => (
                <option key={p.id} value={p.id}>#{p.id} · {p.title || "(không tiêu đề)"}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <button type="button" className="btn btn-primary" disabled={!canContinue} onClick={() => w.setStep(1)}>
        Tiếp tục
      </button>
    </div>
  );
};

