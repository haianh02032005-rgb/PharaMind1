import React, { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  Bot,
  Box,
  CalendarClock,
  Eye,
  FileText,
  FileUp,
  Home,
  LogOut,
  Pill,
  Settings,
  Users,
} from "lucide-react";
import { PwaInstallButton } from "../pwa/PwaInstallButton";
import { useAuthStore } from "../../store/authStore";
import { useFamilyStore } from "../../store/familyStore";
import { useUiStore } from "../../store/uiStore";

const NAV_ITEMS = [
  { to: "/", label: "Trang chủ", icon: Home, end: true },
  { to: "/family", label: "Gia đình & Hồ sơ", icon: Users },
  { to: "/medications", label: "Thuốc gia đình", icon: Pill },
  { to: "/prescriptions", label: "Đơn thuốc", icon: FileText },
  { to: "/import-prescription", label: "Nhập đơn (OCR/Excel)", icon: FileUp },
  { to: "/schedules", label: "Lịch uống thuốc", icon: CalendarClock },
  { to: "/cabinet", label: "Tủ thuốc thông minh", icon: Box },
  { to: "/digital-twin", label: "Digital Twin 3D", icon: Activity },
  { to: "/ai", label: "Trợ lý AI Dược sĩ", icon: Bot },
  { to: "/settings", label: "Cài đặt", icon: Settings },
];

const MOBILE_TABS = [
  { to: "/", label: "Trang chủ", icon: Home, end: true },
  { to: "/medications", label: "Thuốc", icon: Pill },
  { to: "/schedules", label: "Lịch uống", icon: CalendarClock },
  { to: "/cabinet", label: "Tủ thuốc", icon: Box },
  { to: "/family", label: "Gia đình", icon: Users },
];

export const AppShell: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { families, activeFamilyId, fetchFamilies, setActiveFamilyId } =
    useFamilyStore();
  const { elderlyMode, toggleElderlyMode } = useUiStore();

  useEffect(() => {
    void fetchFamilies();
  }, [fetchFamilies]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      {/* Desktop Left Sidebar */}
      <aside className="app-sidebar">
        <div className="app-brand">
          <div className="app-brand-logo">PM</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1.08rem" }}>
              PharmaMind AI
            </div>
            <div
              style={{
                fontSize: "0.76rem",
                color: "var(--pm-text-secondary)",
              }}
            >
              Chăm sóc thuốc gia đình
            </div>
          </div>
        </div>

        <nav className="app-nav-list">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `app-nav-item ${isActive ? "active" : ""}`
                }
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div
          style={{
            borderTop: "1px solid var(--pm-border)",
            paddingTop: 14,
            marginTop: 12,
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <PwaInstallButton />
          <div style={{ fontSize: "0.84rem" }}>
            <div style={{ fontWeight: 600 }}>{user?.full_name || "Người dùng"}</div>
            <div style={{ color: "var(--pm-text-secondary)", fontSize: "0.78rem" }}>
              {user?.email}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-sm btn-outline"
            onClick={handleLogout}
            style={{ width: "100%" }}
          >
            <LogOut size={15} />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="app-main-area">
        <header className="app-topbar">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span
              style={{
                fontSize: "0.86rem",
                fontWeight: 600,
                color: "var(--pm-text-secondary)",
              }}
            >
              Gia đình:
            </span>
            {families.length > 0 ? (
              <select
                className="select"
                style={{ width: "auto", minWidth: 210, padding: "7px 12px" }}
                value={activeFamilyId ?? ""}
                onChange={(e) =>
                  void setActiveFamilyId(Number(e.target.value))
                }
              >
                {families.map((f) => (
                  <option key={f.id} value={f.id}>
                    🏠 {f.name}
                  </option>
                ))}
              </select>
            ) : (
              <span className="badge badge-warning">Chưa có gia đình</span>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button
              type="button"
              onClick={toggleElderlyMode}
              className={`btn btn-sm ${
                elderlyMode ? "btn-primary" : "btn-secondary"
              }`}
              title="Tăng cỡ chữ, nút lớn và chế độ hiển thị dễ đọc cho người lớn tuổi"
            >
              <Eye size={16} />
              {elderlyMode ? "Chế độ dễ đọc: BẬT" : "Chế độ dễ đọc"}
            </button>
          </div>
        </header>

        <main className="app-content">
          <Outlet />
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-bottom-nav">
        {MOBILE_TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                `mobile-nav-link ${isActive ? "active" : ""}`
              }
            >
              <Icon size={20} />
              <span>{tab.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};

