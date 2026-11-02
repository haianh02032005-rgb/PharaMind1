import React, { useState } from "react";
import { Link } from "react-router-dom";
import { HeartPulse, PlusCircle, UserPlus, Users } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";

export const FamilyPage: React.FC = () => {
  const {
    families,
    activeFamilyId,
    members,
    createFamily,
    fetchMembers,
    setActiveFamilyId,
  } = useFamilyStore();

  const [showAddMember, setShowAddMember] = useState(false);
  const [fullName, setFullName] = useState("");
  const [relationship, setRelationship] = useState("");
  const [gender, setGender] = useState("UNSPECIFIED");
  const [dob, setDob] = useState("");
  const [notes, setNotes] = useState("");

  const [newFamName, setNewFamName] = useState("");
  const [showAddFamily, setShowAddFamily] = useState(false);
  const [busy, setBusy] = useState(false);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFamilyId || !fullName.trim()) return;
    setBusy(true);
    try {
      await apiRequest(`/families/${activeFamilyId}/members`, {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName.trim(),
          relationship_label: relationship.trim() || null,
          gender,
          date_of_birth: dob || null,
          notes: notes.trim() || null,
        }),
      });
      await fetchMembers(activeFamilyId);
      setFullName("");
      setRelationship("");
      setDob("");
      setNotes("");
      setShowAddMember(false);
    } finally {
      setBusy(false);
    }
  };

  const handleCreateFamily = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFamName.trim()) return;
    setBusy(true);
    try {
      await createFamily(newFamName.trim(), "Hộ gia đình PharmaMind AI");
      setNewFamName("");
      setShowAddFamily(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
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
            Gia đình & Hồ sơ Sức khỏe Thành viên
          </h1>
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Quản lý thành viên hộ gia đình, bệnh nền, tiền sử dị ứng, phản ứng thuốc và
            liên hệ khẩn cấp.
          </p>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => setShowAddFamily(!showAddFamily)}
          >
            <PlusCircle size={17} />
            Tạo Gia đình mới
          </button>
          {activeFamilyId && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowAddMember(true)}
            >
              <UserPlus size={17} />
              Thêm Thành viên
            </button>
          )}
        </div>
      </div>

      {showAddFamily && (
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Tạo Hộ gia đình mới</h3>
          <form onSubmit={handleCreateFamily} style={{ display: "flex", gap: 10 }}>
            <input
              type="text"
              className="input"
              placeholder="Tên gia đình (VD: Gia đình Nội Ngoại)"
              value={newFamName}
              onChange={(e) => setNewFamName(e.target.value)}
              required
            />
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Lưu gia đình
            </button>
          </form>
        </div>
      )}

      {/* Family Workspace Selector Cards */}
      {families.length > 1 && (
        <div className="grid-3">
          {families.map((fam) => (
            <div
              key={fam.id}
              onClick={() => void setActiveFamilyId(fam.id)}
              className={`card ${
                fam.id === activeFamilyId ? "card-highlight" : ""
              }`}
              style={{ cursor: "pointer" }}
            >
              <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>
                🏠 {fam.name}
              </div>
              <div
                style={{
                  fontSize: "0.82rem",
                  color: "var(--pm-text-secondary)",
                  marginTop: 4,
                }}
              >
                Trạng thái: {fam.status}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Family Members Grid */}
      <div className="card">
        <h3
          style={{
            fontSize: "1.1rem",
            fontWeight: 700,
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Users size={20} style={{ color: "var(--pm-primary)" }} />
          Danh sách Thành viên ({members.length})
        </h3>

        {members.length === 0 ? (
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Gia đình chưa có thành viên nào. Nhấn &ldquo;Thêm Thành viên&rdquo; để tạo hồ
            sơ sức khỏe.
          </p>
        ) : (
          <div className="grid-3">
            {members.map((member) => (
              <div
                key={member.id}
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
                      alignItems: "center",
                    }}
                  >
                    <span style={{ fontWeight: 700, fontSize: "1.1rem" }}>
                      {member.full_name}
                    </span>
                    {member.relationship_label && (
                      <span className="badge badge-primary">
                        {member.relationship_label}
                      </span>
                    )}
                  </div>
                  <div
                    style={{
                      fontSize: "0.85rem",
                      color: "var(--pm-text-secondary)",
                      marginTop: 6,
                    }}
                  >
                    Ngày sinh: {member.date_of_birth || "Chưa cập nhật"} • Giới tính:{" "}
                    {member.gender || "UNSPECIFIED"}
                  </div>
                </div>

                <Link
                  to={`/members/${member.id}`}
                  className="btn btn-secondary btn-sm"
                  style={{ width: "100%" }}
                >
                  <HeartPulse size={16} />
                  Mở Hồ sơ Sức khỏe & Lịch thuốc
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Member Modal */}
      {showAddMember && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3 style={{ marginBottom: 14 }}>Thêm Thành viên Gia đình</h3>
            <form onSubmit={handleAddMember}>
              <div className="form-group">
                <label className="form-label">Họ và tên thành viên *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Ví dụ: Bà Nguyễn Thị Lan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Mối quan hệ trong gia đình</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Mẹ, Bố, Ông, Bà, Con..."
                    value={relationship}
                    onChange={(e) => setRelationship(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Giới tính</label>
                  <select
                    className="select"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                  >
                    <option value="UNSPECIFIED">Chưa xác định</option>
                    <option value="FEMALE">Nữ</option>
                    <option value="MALE">Nam</option>
                    <option value="OTHER">Khác</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Ngày sinh</label>
                <input
                  type="date"
                  className="input"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Ghi chú chăm sóc</label>
                <textarea
                  className="textarea"
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: 10,
                  marginTop: 16,
                }}
              >
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowAddMember(false)}
                >
                  Huỷ
                </button>
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  {busy ? "Đang lưu..." : "Thêm thành viên"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

