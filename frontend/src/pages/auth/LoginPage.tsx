import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, LogIn, ShieldCheck } from "lucide-react";
import { authService } from "../../services/authService";
import { apiRequest } from "../../services/apiClient";
import { useAuthStore } from "../../store/authStore";
import { useFamilyStore } from "../../store/familyStore";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const hydrate = useAuthStore((s) => s.hydrate);
  const fetchFamilies = useFamilyStore((s) => s.fetchFamilies);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authService.login({ email, password });
      await hydrate();
      await fetchFamilies();
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Đăng nhập không thành công. Vui lòng kiểm tra lại email/mật khẩu."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSeedAndLogin = async () => {
    setError(null);
    setDemoLoading(true);
    const demoEmail = "demo@pharmamind.vn";
    const demoPass = "DemoPass123!";
    try {
      try {
        await authService.login({ email: demoEmail, password: demoPass });
      } catch {
        try {
          await authService.register({
            email: demoEmail,
            password: demoPass,
            full_name: "Nguyễn Minh An (Demo)",
          });
          await authService.login({ email: demoEmail, password: demoPass });
        } catch {
          // If already exists or register fails, try logging in again
          await authService.login({ email: demoEmail, password: demoPass });
        }
      }
      await hydrate();
      await fetchFamilies();
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Không thể đăng nhập tài khoản demo"
      );
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
        background: "linear-gradient(135deg, #e7f6f4 0%, #f7fafa 100%)",
      }}
    >
      <div className="card" style={{ maxWidth: 460, width: "100%", padding: 32 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 20,
          }}
        >
          <div className="app-brand-logo">PM</div>
          <div>
            <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
              PharmaMind AI
            </h1>
            <p style={{ fontSize: "0.86rem", color: "var(--pm-text-secondary)" }}>
              Hệ thống Quản lý Thuốc & Tủ Thuốc Thông Minh 3D
            </p>
          </div>
        </div>

        {error && (
          <div className="alert-banner alert-danger" style={{ marginBottom: 16 }}>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email đăng nhập</label>
            <input
              type="email"
              className="input"
              placeholder="nhap.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mật khẩu</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || demoLoading}
            style={{ width: "100%", marginTop: 6 }}
          >
            <LogIn size={18} />
            {loading ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>
        </form>

        <div
          style={{
            margin: "18px 0",
            borderTop: "1px solid var(--pm-border)",
            paddingTop: 16,
          }}
        >
          <button
            type="button"
            className="btn btn-secondary"
            disabled={loading || demoLoading}
            onClick={handleDemoSeedAndLogin}
            style={{ width: "100%", justifyContent: "center" }}
          >
            <Sparkles size={18} />
            {demoLoading
              ? "Đang vào không gian demo..."
              : "Dùng thử ngay (Tài khoản & Dữ liệu 3D mẫu)"}
          </button>
          <div
            style={{
              fontSize: "0.78rem",
              color: "var(--pm-text-secondary)",
              textAlign: "center",
              marginTop: 6,
            }}
          >
            Tài khoản mẫu: <strong>demo@pharmamind.vn</strong> / <strong>DemoPass123!</strong>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "0.88rem",
            color: "var(--pm-text-secondary)",
          }}
        >
          <span>Chưa có tài khoản?</span>
          <Link
            to="/register"
            style={{ color: "var(--pm-primary)", fontWeight: 600 }}
          >
            Đăng ký tài khoản mới →
          </Link>
        </div>

        <div
          style={{
            marginTop: 20,
            padding: 12,
            borderRadius: 10,
            background: "var(--pm-bg)",
            fontSize: "0.78rem",
            color: "var(--pm-text-secondary)",
            display: "flex",
            gap: 8,
          }}
        >
          <ShieldCheck
            size={16}
            style={{ color: "var(--pm-primary)", flexShrink: 0, marginTop: 2 }}
          />
          <span>
            PharmaMind AI hỗ trợ theo dõi lịch dùng thuốc và cảnh báo an toàn hộ gia
            đình; không thay thế chẩn đoán hoặc chỉ định của bác sĩ.
          </span>
        </div>
      </div>
    </div>
  );
};

