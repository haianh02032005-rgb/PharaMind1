import React from "react";
import { Eye, Sparkles, User } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { useUiStore } from "../../store/uiStore";

export const SettingsPage: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const {
    elderlyMode,
    reducedMotion,
    cabinetViewMode,
    toggleElderlyMode,
    toggleReducedMotion,
    setCabinetViewMode,
  } = useUiStore();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div>
        <h1 style={{ fontSize: "1.55rem", fontWeight: 700 }}>
          Cài đặt Hệ thống & Trợ năng
        </h1>
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Tuỳ chỉnh giao diện thân thiện cho người cao tuổi (Chế độ dễ đọc) và hiệu
          ứng 3D.
        </p>
      </div>

      <div className="grid-2">
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <h3 style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Eye size={19} style={{ color: "var(--pm-primary)" }} />
            Trợ năng & Chế độ Người lớn tuổi (Elderly Mode)
          </h3>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: 14,
              borderBottom: "1px solid var(--pm-border)",
            }}
          >
            <div>
              <div style={{ fontWeight: 700 }}>Chế độ dễ đọc (Elderly Mode)</div>
              <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
                Tăng kích thước chữ (+20%), nút bấm lớn (≥ 50px) và viền tương phản cao.
              </div>
            </div>
            <button
              type="button"
              className={`btn btn-sm ${
                elderlyMode ? "btn-primary" : "btn-outline"
              }`}
              onClick={toggleElderlyMode}
            >
              {elderlyMode ? "Đang BẬT" : "Đang TẮT"}
            </button>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: 14,
              borderBottom: "1px solid var(--pm-border)",
            }}
          >
            <div>
              <div style={{ fontWeight: 700 }}>
                Giảm chuyển động (Reduced Motion)
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
                Tắt hiệu ứng trượt ngăn kéo 3D để tránh gây mỏi mắt cho người nhạy cảm.
              </div>
            </div>
            <button
              type="button"
              className={`btn btn-sm ${
                reducedMotion ? "btn-primary" : "btn-outline"
              }`}
              onClick={toggleReducedMotion}
            >
              {reducedMotion ? "Đang BẬT" : "Đang TẮT"}
            </button>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 700 }}>
                Chế độ hiển thị mặc định cho Tủ thuốc
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--pm-text-secondary)" }}>
                Chọn giữa Mô hình 3D tương tác hoặc Lưới 2D 3×3 đơn giản.
              </div>
            </div>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() =>
                setCabinetViewMode(cabinetViewMode === "3D" ? "SIMPLE" : "3D")
              }
            >
              <Sparkles size={14} />
              {cabinetViewMode === "3D" ? "3D Digital Twin" : "Lưới 2D 3×3"}
            </button>
          </div>
        </div>

        <div className="card">
          <h3 style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <User size={19} style={{ color: "var(--pm-primary)" }} />
            Thông tin Tài khoản
          </h3>
          <p style={{ marginBottom: 8 }}>
            <strong>Họ và tên:</strong> {user?.full_name || "Người dùng"}
          </p>
          <p style={{ marginBottom: 8 }}>
            <strong>Email:</strong> {user?.email}
          </p>
          <p>
            <strong>Trạng thái:</strong>{" "}
            <span className="badge badge-success">{user?.status || "ACTIVE"}</span>
          </p>
        </div>
      </div>
    </div>
  );
};

