import React, { useEffect, useState } from "react";
import { useImportWizard } from "../../features/importPrescription/hooks";
import type { HealthUpdatesDraft } from "../../features/importPrescription/types";
import { ConflictAlert } from "../../components/importPrescription/ImportComponents";

const empty: HealthUpdatesDraft = {
  confirm_conditions: false,
  conditions: [],
  confirm_allergies: false,
  allergies: [],
  confirm_drug_reactions: false,
  drug_reactions: [],
};

export const HealthUpdateStep: React.FC = () => {
  const w = useImportWizard();
  const session = w.session;
  const [h, setH] = useState<HealthUpdatesDraft>(empty);

  useEffect(() => {
    setH({ ...empty, ...(session?.review_payload?.health_updates || {}) });
  }, [session?.review_payload]);

  if (!session) return null;
  const healthIssues = session.validation_issues.filter((i) => i.field_path.startsWith("health_updates"));
  const total = h.conditions.length + h.allergies.length + h.drug_reactions.length;

  const next = async () => {
    const s = await w.patch({ health_updates: h });
    if (s) {
      w.setConfirmHealth(h.confirm_conditions || h.confirm_allergies || h.confirm_drug_reactions);
      w.setStep(5);
    }
  };

  const Section: React.FC<{
    title: string;
    enabled: boolean;
    onToggle: (v: boolean) => void;
    children: React.ReactNode;
    count: number;
  }> = ({ title, enabled, onToggle, children, count }) => (
    <div className="card">
      <label style={{ display: "flex", gap: 8, alignItems: "center", fontWeight: 700, marginBottom: 8 }}>
        <input type="checkbox" checked={enabled} disabled={count === 0} onChange={(e) => onToggle(e.target.checked)} />
        {title} ({count})
      </label>
      {count === 0 ? <div style={{ color: "var(--pm-text-secondary)" }}>Không phát hiện.</div> : children}
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="card">
        <h3 style={{ marginBottom: 6 }}>Bước 5 · Cập nhật Hồ sơ sức khỏe (tuỳ chọn)</h3>
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Chỉ những mục bạn tích chọn mới được lưu. Dị ứng đã có trong hồ sơ sẽ <strong>không bao giờ bị xóa tự động</strong>,
          và phản ứng thuốc không tự chuyển thành dị ứng.
        </p>
      </div>
      <ConflictAlert issues={healthIssues} />

      {total === 0 && <div className="card">Tài liệu không chứa thông tin chẩn đoán, dị ứng hay phản ứng thuốc.</div>}

      <Section title="Chẩn đoán / Bệnh lý" count={h.conditions.length} enabled={h.confirm_conditions} onToggle={(v) => setH({ ...h, confirm_conditions: v })}>
        {h.conditions.map((c, i) => (
          <label key={i} style={{ display: "flex", gap: 8, alignItems: "center", padding: "4px 0" }}>
            <input
              type="checkbox"
              checked={c.confirmed}
              disabled={!h.confirm_conditions}
              onChange={(e) => setH({ ...h, conditions: h.conditions.map((x, j) => (j === i ? { ...x, confirmed: e.target.checked } : x)) })}
            />
            {c.name}
          </label>
        ))}
      </Section>

      <Section title="Dị ứng" count={h.allergies.length} enabled={h.confirm_allergies} onToggle={(v) => setH({ ...h, confirm_allergies: v })}>
        {h.allergies.map((a, i) => (
          <label key={i} style={{ display: "flex", gap: 8, alignItems: "center", padding: "4px 0" }}>
            <input
              type="checkbox"
              checked={a.confirmed}
              disabled={!h.confirm_allergies}
              onChange={(e) => setH({ ...h, allergies: h.allergies.map((x, j) => (j === i ? { ...x, confirmed: e.target.checked } : x)) })}
            />
            {a.allergen} <span className="badge badge-warning">{a.severity}</span>
          </label>
        ))}
      </Section>

      <Section title="Phản ứng thuốc" count={h.drug_reactions.length} enabled={h.confirm_drug_reactions} onToggle={(v) => setH({ ...h, confirm_drug_reactions: v })}>
        {h.drug_reactions.map((r, i) => (
          <label key={i} style={{ display: "flex", gap: 8, alignItems: "center", padding: "4px 0" }}>
            <input
              type="checkbox"
              checked={r.confirmed}
              disabled={!h.confirm_drug_reactions}
              onChange={(e) => setH({ ...h, drug_reactions: h.drug_reactions.map((x, j) => (j === i ? { ...x, confirmed: e.target.checked } : x)) })}
            />
            {r.drug_name}: {r.reaction}
          </label>
        ))}
      </Section>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" className="btn btn-secondary" onClick={() => w.setStep(3)}>Quay lại</button>
        <button type="button" className="btn btn-primary" disabled={w.busy} onClick={next}>
          Tiếp tục: Xác nhận
        </button>
      </div>
    </div>
  );
};

