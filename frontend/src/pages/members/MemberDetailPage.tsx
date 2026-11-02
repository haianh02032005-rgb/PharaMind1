import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
  FileText,
  FileUp,
  HeartPulse,
  PhoneCall,
  Pill,
  PlusCircle,
} from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";

type TabType = "OVERVIEW" | "HEALTH" | "MEDICATIONS" | "PRESCRIPTIONS" | "SCHEDULES";

export const MemberDetailPage: React.FC = () => {
  const { memberId } = useParams<{ memberId: string }>();
  const numericMemberId = Number(memberId);
  const { activeFamilyId, members } = useFamilyStore();

  const [activeTab, setActiveTab] = useState<TabType>("HEALTH");
  const [conditions, setConditions] = useState<
    Array<{ id: number; condition_name: string; status: string; notes?: string }>
  >([]);
  const [allergies, setAllergies] = useState<
    Array<{
      id: number;
      allergen: string;
      allergy_type: string;
      severity: string;
      reaction_description?: string;
    }>
  >([]);
  const [reactions, setReactions] = useState<
    Array<{
      id: number;
      drug_name: string;
      active_ingredient?: string;
      reaction: string;
      severity: string;
    }>
  >([]);
  const [contacts, setContacts] = useState<
    Array<{
      id: number;
      contact_name: string;
      relationship_label?: string;
      phone: string;
      is_primary: boolean;
    }>
  >([]);
  const [memberSchedules, setMemberSchedules] = useState<
    Array<{
      id: number;
      recurrence_type: string;
      times: string[];
      medication?: { name: string; strength?: string };
    }>
  >([]);

  // Form states for adding Health Profile records
  const [condName, setCondName] = useState("");
  const [allergen, setAllergen] = useState("");
  const [allergySeverity, setAllergySeverity] = useState("SEVERE");
  const [allergyDesc, setAllergyDesc] = useState("");
  const [rxDrugName, setRxDrugName] = useState("");
  const [rxReaction, setRxReaction] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactPhone, setContactPhone] = useState("");

  const member = members.find((m) => m.id === numericMemberId);

  const loadMemberHealthData = useCallback(async () => {
    if (!activeFamilyId || !numericMemberId) return;
    try {
      const [condRes, algRes, rxRes, cntRes, schedRes] = await Promise.all([
        apiRequest<{ items: typeof conditions }>(
          `/families/${activeFamilyId}/members/${numericMemberId}/conditions`
        ).catch(() => ({ items: [] })),
        apiRequest<{ items: typeof allergies }>(
          `/families/${activeFamilyId}/members/${numericMemberId}/allergies`
        ).catch(() => ({ items: [] })),
        apiRequest<{ items: typeof reactions }>(
          `/families/${activeFamilyId}/members/${numericMemberId}/drug-reactions`
        ).catch(() => ({ items: [] })),
        apiRequest<{ items: typeof contacts }>(
          `/families/${activeFamilyId}/members/${numericMemberId}/emergency-contacts`
        ).catch(() => ({ items: [] })),
        apiRequest<{ items: typeof memberSchedules }>(
          `/families/${activeFamilyId}/members/${numericMemberId}/schedules`
        ).catch(() => ({ items: [] })),
      ]);
      setConditions(condRes.items || []);
      setAllergies(algRes.items || []);
      setReactions(rxRes.items || []);
      setContacts(cntRes.items || []);
      setMemberSchedules(schedRes.items || []);
    } catch {
      // ignore
    }
  }, [activeFamilyId, numericMemberId]);

  useEffect(() => {
    void loadMemberHealthData();
  }, [loadMemberHealthData]);

  const handleAddCondition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !condName.trim()) return;
    await apiRequest(
      `/families/${activeFamilyId}/members/${numericMemberId}/conditions`,
      {
        method: "POST",
        body: JSON.stringify({
          condition_name: condName.trim(),
          status: "ACTIVE",
        }),
      }
    );
    setCondName("");
    await loadMemberHealthData();
  };

  const handleAddAllergy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !allergen.trim()) return;
    await apiRequest(
      `/families/${activeFamilyId}/members/${numericMemberId}/allergies`,
      {
        method: "POST",
        body: JSON.stringify({
          allergen: allergen.trim(),
          allergy_type: "DRUG",
          severity: allergySeverity,
          reaction_description: allergyDesc.trim() || null,
        }),
      }
    );
    setAllergen("");
    setAllergyDesc("");
    await loadMemberHealthData();
  };

  const handleAddReaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !rxDrugName.trim() || !rxReaction.trim()) return;
    await apiRequest(
      `/families/${activeFamilyId}/members/${numericMemberId}/drug-reactions`,
      {
        method: "POST",
        body: JSON.stringify({
          drug_name: rxDrugName.trim(),
          reaction: rxReaction.trim(),
          severity: "MODERATE",
        }),
      }
    );
    setRxDrugName("");
    setRxReaction("");
    await loadMemberHealthData();
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !contactName.trim() || !contactPhone.trim()) return;
    await apiRequest(
      `/families/${activeFamilyId}/members/${numericMemberId}/emergency-contacts`,
      {
        method: "POST",
        body: JSON.stringify({
          contact_name: contactName.trim(),
          phone: contactPhone.trim(),
          is_primary: true,
        }),
      }
    );
    setContactName("");
    setContactPhone("");
    await loadMemberHealthData();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div>
        <Link
          to="/family"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            color: "var(--pm-primary)",
            textDecoration: "none",
            fontWeight: 600,
            marginBottom: 10,
          }}
        >
          <ArrowLeft size={16} />
          Quay lại danh sách thành viên
        </Link>
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
              {member?.full_name || `Thành viên #${numericMemberId}`}{" "}
              {member?.relationship_label ? `(${member.relationship_label})` : ""}
            </h1>
            <p style={{ color: "var(--pm-text-secondary)" }}>
              Hồ sơ sức khỏe cá nhân hóa — Tự động đối chiếu cảnh báo dị ứng trên Digital Twin 3D.
            </p>
          </div>
          <Link
            to={`/import-prescription?memberId=${numericMemberId}`}
            className="btn btn-outline"
            style={{ textDecoration: "none" }}
          >
            <FileUp size={18} />
            Nhập đơn thuốc cho thành viên này
          </Link>
        </div>
      </div>

      {/* 5 Tabs as specified in FRONTEND_SPECIFICATION §24 */}
      <div className="tabs-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === "OVERVIEW" ? "active" : ""}`}
          onClick={() => setActiveTab("OVERVIEW")}
        >
          Tổng quan
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "HEALTH" ? "active" : ""}`}
          onClick={() => setActiveTab("HEALTH")}
        >
          Sức khỏe (Bệnh nền & Dị ứng)
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "MEDICATIONS" ? "active" : ""}`}
          onClick={() => setActiveTab("MEDICATIONS")}
        >
          Thuốc
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "PRESCRIPTIONS" ? "active" : ""}`}
          onClick={() => setActiveTab("PRESCRIPTIONS")}
        >
          Đơn thuốc
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "SCHEDULES" ? "active" : ""}`}
          onClick={() => setActiveTab("SCHEDULES")}
        >
          Lịch dùng ({memberSchedules.length})
        </button>
      </div>

      {activeTab === "OVERVIEW" && (
        <div className="grid-2">
          <div className="card">
            <h3 style={{ marginBottom: 10 }}>Thông tin cá nhân</h3>
            <p>
              <strong>Họ tên:</strong> {member?.full_name}
            </p>
            <p>
              <strong>Vai trò trong nhà:</strong>{" "}
              {member?.relationship_label || "Thành viên"}
            </p>
            <p>
              <strong>Ngày sinh:</strong> {member?.date_of_birth || "Chưa cập nhật"}
            </p>
            <p>
              <strong>Số dị ứng đã ghi nhận:</strong> {allergies.length}
            </p>
            <p>
              <strong>Số bệnh nền đang theo dõi:</strong> {conditions.length}
            </p>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 10 }}>Tóm tắt Lịch uống thuốc</h3>
            {memberSchedules.length === 0 ? (
              <p style={{ color: "var(--pm-text-secondary)" }}>
                Chưa có lịch uống thuốc đang hoạt động.
              </p>
            ) : (
              memberSchedules.map((s) => (
                <div
                  key={s.id}
                  style={{
                    padding: 10,
                    borderBottom: "1px solid var(--pm-border)",
                  }}
                >
                  <strong>{s.medication?.name || `Lịch #${s.id}`}</strong> — Giờ:{" "}
                  {s.times.join(", ")}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "HEALTH" && (
        <div className="grid-2">
          {/* 1. Allergies */}
          <div className="card">
            <h3
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 12,
              }}
            >
              <AlertTriangle size={19} style={{ color: "var(--pm-danger)" }} />
              Tiền sử Dị ứng ({allergies.length})
            </h3>
            <form onSubmit={handleAddAllergy} style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <input
                  type="text"
                  className="input"
                  placeholder="Tên dị nguyên / thuốc (VD: Amoxicillin)"
                  value={allergen}
                  onChange={(e) => setAllergen(e.target.value)}
                  required
                />
                <select
                  className="select"
                  style={{ width: 140 }}
                  value={allergySeverity}
                  onChange={(e) => setAllergySeverity(e.target.value)}
                >
                  <option value="MILD">Nhẹ (MILD)</option>
                  <option value="MODERATE">Vừa (MODERATE)</option>
                  <option value="SEVERE">Nặng (SEVERE)</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  className="input"
                  placeholder="Biểu hiện (VD: Nổi mẩn đỏ, khó thở)"
                  value={allergyDesc}
                  onChange={(e) => setAllergyDesc(e.target.value)}
                />
                <button type="submit" className="btn btn-primary btn-sm">
                  <PlusCircle size={15} />
                  Thêm
                </button>
              </div>
            </form>

            {allergies.map((a) => (
              <div
                key={a.id}
                className="alert-banner alert-danger"
                style={{ justifyContent: "space-between" }}
              >
                <div>
                  <strong>{a.allergen}</strong> ({a.severity})
                  {a.reaction_description ? ` — ${a.reaction_description}` : ""}
                </div>
              </div>
            ))}
          </div>

          {/* 2. Medical Conditions */}
          <div className="card">
            <h3
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 12,
              }}
            >
              <HeartPulse size={19} style={{ color: "var(--pm-primary)" }} />
              Bệnh nền đang theo dõi ({conditions.length})
            </h3>
            <form
              onSubmit={handleAddCondition}
              style={{ display: "flex", gap: 8, marginBottom: 14 }}
            >
              <input
                type="text"
                className="input"
                placeholder="Tên bệnh lý (VD: Tăng huyết áp, Đái tháo đường)"
                value={condName}
                onChange={(e) => setCondName(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-primary btn-sm">
                <PlusCircle size={15} />
                Thêm
              </button>
            </form>

            {conditions.map((c) => (
              <div
                key={c.id}
                style={{
                  padding: "10px 12px",
                  borderRadius: 10,
                  border: "1px solid var(--pm-border)",
                  marginBottom: 8,
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <strong>{c.condition_name}</strong>
                <span className="badge badge-primary">{c.status}</span>
              </div>
            ))}
          </div>

          {/* 3. Drug Reactions */}
          <div className="card">
            <h3
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 12,
              }}
            >
              <Pill size={19} style={{ color: "var(--pm-warning)" }} />
              Tiền sử Phản ứng thuốc ({reactions.length})
            </h3>
            <form onSubmit={handleAddReaction} style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <input
                  type="text"
                  className="input"
                  placeholder="Tên thuốc gây phản ứng (VD: Ibuprofen)"
                  value={rxDrugName}
                  onChange={(e) => setRxDrugName(e.target.value)}
                  required
                />
                <input
                  type="text"
                  className="input"
                  placeholder="Triệu chứng phản ứng (VD: Đau dạ dày)"
                  value={rxReaction}
                  onChange={(e) => setRxReaction(e.target.value)}
                  required
                />
                <button type="submit" className="btn btn-primary btn-sm">
                  Thêm
                </button>
              </div>
            </form>
            {reactions.map((r) => (
              <div key={r.id} className="alert-banner alert-warning">
                <div>
                  <strong>{r.drug_name}:</strong> {r.reaction} ({r.severity})
                </div>
              </div>
            ))}
          </div>

          {/* 4. Emergency Contacts */}
          <div className="card">
            <h3
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 12,
              }}
            >
              <PhoneCall size={19} style={{ color: "var(--pm-success)" }} />
              Liên hệ Khẩn cấp ({contacts.length})
            </h3>
            <form
              onSubmit={handleAddContact}
              style={{ display: "flex", gap: 8, marginBottom: 14 }}
            >
              <input
                type="text"
                className="input"
                placeholder="Tên người liên hệ"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                required
              />
              <input
                type="text"
                className="input"
                placeholder="Số điện thoại"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-primary btn-sm">
                Thêm
              </button>
            </form>
            {contacts.map((c) => (
              <div
                key={c.id}
                style={{
                  padding: "10px 12px",
                  borderRadius: 10,
                  border: "1px solid var(--pm-border)",
                  marginBottom: 8,
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span>
                  <strong>{c.contact_name}</strong> — 📞 {c.phone}
                </span>
                {c.is_primary && (
                  <span className="badge badge-success">Liên hệ chính</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {(activeTab === "MEDICATIONS" ||
        activeTab === "PRESCRIPTIONS" ||
        activeTab === "SCHEDULES") && (
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>
            Lịch uống thuốc & Đơn thuốc của {member?.full_name}
          </h3>
          {memberSchedules.length === 0 ? (
            <p style={{ color: "var(--pm-text-secondary)" }}>
              Chưa có lịch uống thuốc nào cho thành viên này.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {memberSchedules.map((s) => (
                <div
                  key={s.id}
                  style={{
                    padding: 14,
                    borderRadius: 12,
                    border: "1px solid var(--pm-border)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700 }}>
                      {s.medication?.name || `Lịch #${s.id}`}{" "}
                      {s.medication?.strength || ""}
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
                      Tần suất: {s.recurrence_type} • Khung giờ:{" "}
                      <strong>{s.times.join(", ")}</strong>
                    </div>
                  </div>
                  <Link to="/digital-twin" className="btn btn-sm btn-secondary">
                    Xem trên Tủ 3D
                  </Link>
                </div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 16, display: "flex", gap: 10 }}>
            <Link to="/prescriptions" className="btn btn-outline btn-sm">
              <FileText size={15} />
              Quản lý Đơn thuốc
            </Link>
            <Link to="/schedules" className="btn btn-primary btn-sm">
              <CalendarClock size={15} />
              Quản lý Lịch uống thuốc
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

