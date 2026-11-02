import React, { useCallback, useEffect, useState } from "react";
import { Calendar, Package, Pill, PlusCircle } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";
import { dosageFormToPlaceholderType } from "../../features/digitalTwin/types";

interface MedicationItem {
  id: number;
  family_id: number;
  quantity: number;
  unit: string;
  low_stock_threshold?: number | null;
  expiration_date?: string | null;
  status: string;
  notes?: string | null;
  catalog: {
    id: number;
    name: string;
    brand_name?: string | null;
    active_ingredient?: string | null;
    strength?: string | null;
    dosage_form?: string | null;
  };
}

export const MedicationsPage: React.FC = () => {
  const { activeFamilyId, members } = useFamilyStore();
  const [medications, setMedications] = useState<MedicationItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // 3-step Add Medication modal (§28)
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [name, setName] = useState("");
  const [activeIngredient, setActiveIngredient] = useState("");
  const [strength, setStrength] = useState("");
  const [dosageForm, setDosageForm] = useState("TABLET");
  const [quantity, setQuantity] = useState("20");
  const [unit, setUnit] = useState("TABLET");
  const [lowStockThreshold, setLowStockThreshold] = useState("5");
  const [expirationDate, setExpirationDate] = useState("2028-12-31");
  const [selectedMemberId, setSelectedMemberId] = useState<string>("");
  const [selectedCompartmentPos, setSelectedCompartmentPos] =
    useState<string>("");
  const [busy, setBusy] = useState(false);

  const loadMedications = useCallback(async () => {
    if (!activeFamilyId) return;
    try {
      const res = await apiRequest<{ items: MedicationItem[] }>(
        `/families/${activeFamilyId}/medications?include_archived=true`
      );
      setMedications(res.items || []);
    } catch {
      setMedications([]);
    }
  }, [activeFamilyId]);

  useEffect(() => {
    void loadMedications();
  }, [loadMedications]);

  const handleCreateMedication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !name.trim()) return;
    setBusy(true);
    try {
      const created = await apiRequest<MedicationItem>(
        `/families/${activeFamilyId}/medications`,
        {
          method: "POST",
          body: JSON.stringify({
            name: name.trim(),
            active_ingredient: activeIngredient.trim() || null,
            strength: strength.trim() || null,
            dosage_form: dosageForm,
            quantity: Number(quantity) || 10,
            unit,
            low_stock_threshold: Number(lowStockThreshold) || 5,
            expiration_date: expirationDate || null,
          }),
        }
      );

      if (selectedMemberId) {
        await apiRequest(
          `/families/${activeFamilyId}/medications/${created.id}/members`,
          {
            method: "POST",
            body: JSON.stringify({ member_id: Number(selectedMemberId) }),
          }
        ).catch(() => {});
      }

      if (selectedCompartmentPos) {
        const cabRes = await apiRequest<{ items: Array<{ id: number }> }>(
          `/families/${activeFamilyId}/cabinets`
        ).catch(() => ({ items: [] }));
        const cabId = cabRes.items?.[0]?.id;
        if (cabId) {
          await apiRequest(
            `/families/${activeFamilyId}/cabinets/${cabId}/compartments/${Number(
              selectedCompartmentPos
            )}/medication`,
            {
              method: "PUT",
              body: JSON.stringify({ family_medication_id: created.id }),
            }
          ).catch(() => {});
        }
      }

      await loadMedications();
      setShowModal(false);
      setStep(1);
      setName("");
      setActiveIngredient("");
      setStrength("");
    } finally {
      setBusy(false);
    }
  };

  const filtered = medications.filter((m) => {
    if (statusFilter === "ALL") return true;
    if (statusFilter === "LOW_STOCK") {
      return (
        m.low_stock_threshold !== null &&
        m.low_stock_threshold !== undefined &&
        m.quantity <= m.low_stock_threshold
      );
    }
    return m.status === statusFilter;
  });

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
            Kho thuốc Gia đình ({medications.length})
          </h1>
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Quản lý tồn kho, hạn sử dụng, dạng bào chế 3D và gán thành viên sử dụng.
          </p>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={() => {
            setStep(1);
            setShowModal(true);
          }}
        >
          <PlusCircle size={18} />
          Thêm thuốc mới (3 Bước)
        </button>
      </div>

      {/* Filter Bar */}
      <div className="tabs-bar" style={{ marginBottom: 4 }}>
        {[
          { key: "ALL", label: "Tất cả" },
          { key: "ACTIVE", label: "Đang dùng" },
          { key: "LOW_STOCK", label: "Sắp hết" },
          { key: "EXPIRED", label: "Quá hạn" },
          { key: "ARCHIVED", label: "Đã lưu trữ" },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`tab-btn ${statusFilter === tab.key ? "active" : ""}`}
            onClick={() => setStatusFilter(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Medications Grid */}
      {filtered.length === 0 ? (
        <div className="card">
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Không có thuốc nào trong danh mục lọc hiện tại.
          </p>
        </div>
      ) : (
        <div className="grid-3">
          {filtered.map((med) => {
            const isLow =
              med.low_stock_threshold != null &&
              med.quantity <= med.low_stock_threshold;
            return (
              <div
                key={med.id}
                className="card"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: 14,
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      gap: 8,
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
                      <Pill size={18} style={{ color: "var(--pm-primary)" }} />
                      <span>
                        {med.catalog.name}{" "}
                        {med.catalog.strength ? `(${med.catalog.strength})` : ""}
                      </span>
                    </div>

                    <span
                      className={`badge ${
                        isLow ? "badge-warning" : "badge-success"
                      }`}
                    >
                      {isLow ? "Sắp hết" : med.status}
                    </span>
                  </div>

                  {med.catalog.active_ingredient && (
                    <div
                      style={{
                        fontSize: "0.84rem",
                        color: "var(--pm-text-secondary)",
                        marginTop: 4,
                      }}
                    >
                      Hoạt chất: {med.catalog.active_ingredient}
                    </div>
                  )}
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingTop: 12,
                    borderTop: "1px solid var(--pm-border)",
                    fontSize: "0.88rem",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Package size={15} style={{ color: "var(--pm-primary)" }} />
                    <strong>
                      {med.quantity} {med.unit}
                    </strong>
                  </span>

                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Calendar size={15} style={{ color: "var(--pm-primary)" }} />
                    {med.expiration_date || "KGH"}
                  </span>

                  <span className="badge badge-primary">
                    3D: {dosageFormToPlaceholderType(med.catalog.dosage_form)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 3-Step Add Medication Modal */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 16,
              }}
            >
              <h3>Thêm Thuốc vào Kho Gia đình (Bước {step}/3)</h3>
              <span className="badge badge-primary">Bước {step} / 3</span>
            </div>

            <form onSubmit={handleCreateMedication}>
              {step === 1 && (
                <>
                  <div className="form-group">
                    <label className="form-label">Tên thuốc *</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="Ví dụ: Paracetamol, Amlodipine..."
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="grid-2">
                    <div className="form-group">
                      <label className="form-label">Hoạt chất</label>
                      <input
                        type="text"
                        className="input"
                        placeholder="Ví dụ: Paracetamol"
                        value={activeIngredient}
                        onChange={(e) => setActiveIngredient(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Hàm lượng</label>
                      <input
                        type="text"
                        className="input"
                        placeholder="Ví dụ: 500mg"
                        value={strength}
                        onChange={(e) => setStrength(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      Dạng bào chế (Quyết định mô hình 3D trong ngăn tủ)
                    </label>
                    <select
                      className="select"
                      value={dosageForm}
                      onChange={(e) => {
                        setDosageForm(e.target.value);
                        setUnit(e.target.value);
                      }}
                    >
                      <option value="TABLET">Viên nén (TABLET)</option>
                      <option value="CAPSULE">Viên nang (CAPSULE)</option>
                      <option value="SYRUP">Chai siro / Dung dịch (SYRUP)</option>
                      <option value="SACHET">Gói bột / Vỉ (SACHET)</option>
                      <option value="OTHER">Hộp thuốc khác (OTHER)</option>
                    </select>
                  </div>
                </>
              )}

              {step === 2 && (
                <>
                  <div className="grid-2">
                    <div className="form-group">
                      <label className="form-label">Số lượng hiện có *</label>
                      <input
                        type="number"
                        className="input"
                        min={1}
                        value={quantity}
                        onChange={(e) => setQuantity(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Ngưỡng cảnh báo sắp hết</label>
                      <input
                        type="number"
                        className="input"
                        min={0}
                        value={lowStockThreshold}
                        onChange={(e) => setLowStockThreshold(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Hạn sử dụng</label>
                    <input
                      type="date"
                      className="input"
                      value={expirationDate}
                      onChange={(e) => setExpirationDate(e.target.value)}
                    />
                  </div>
                </>
              )}

              {step === 3 && (
                <>
                  <div className="form-group">
                    <label className="form-label">
                      Gán cho thành viên sử dụng (Tuỳ chọn)
                    </label>
                    <select
                      className="select"
                      value={selectedMemberId}
                      onChange={(e) => setSelectedMemberId(e.target.value)}
                    >
                      <option value="">-- Chưa chọn thành viên --</option>
                      {members.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.full_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Đặt vào Ngăn Tủ thuốc 3D (Ngăn 1 – 9, Tuỳ chọn)
                    </label>
                    <select
                      className="select"
                      value={selectedCompartmentPos}
                      onChange={(e) => setSelectedCompartmentPos(e.target.value)}
                    >
                      <option value="">-- Chưa đặt vào ngăn tủ --</option>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((pos) => (
                        <option key={pos} value={pos}>
                          Ngăn {pos} (drawer_0{pos})
                        </option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: 18,
                }}
              >
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => {
                    if (step === 1) setShowModal(false);
                    else setStep((step - 1) as 1 | 2);
                  }}
                >
                  {step === 1 ? "Huỷ" : "← Quay lại"}
                </button>

                {step < 3 ? (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      if (step === 1 && !name.trim()) return;
                      setStep((step + 1) as 2 | 3);
                    }}
                  >
                    Tiếp theo →
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={busy}
                  >
                    {busy ? "Đang lưu thuốc..." : "Hoàn tất & Lưu thuốc"}
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

