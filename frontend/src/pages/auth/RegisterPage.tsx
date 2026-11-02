import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { authService } from "../../services/authService";
import { useAuthStore } from "../../store/authStore";
import { useFamilyStore } from "../../store/familyStore";

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const hydrate = useAuthStore((s) => s.hydrate);
  const createFamily = useFamilyStore((s) => s.createFamily);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [familyName, setFamilyName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authService.register({
        full_name: fullName,
        email,
        password,
      });
      await authService.login({ email, password });
      await hydrate();
      if (familyName.trim()) {
        await createFamily(familyName.trim(), "Hộ gia đình PharmaMind AI");
      }
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Đăng ký không thành công"
      );
    } finally {
      setLoading(false);
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
            <h1 style={{ fontSize: "1.35rem", fontWeight: 700 }}>
              Tạo tài khoản PharmaMind AI
            </h1>
            <p style={{ fontSize: "0.86rem", color: "var(--pm-text-secondary)" }}>
              Quản lý tủ thuốc thông minh cho cả gia đình
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
            <label className="form-label">Họ và tên của bạn</label>
            <input
              type="text"
              className="input"
              placeholder="Nguyễn Văn An"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="input"
              placeholder="an.nguyen@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mật khẩu (tối thiểu 8 ký tự, chữ & số)</label>
            <input
              type="password"
              className="input"
              placeholder="StrongPass123"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              Tên hộ gia đình (tuỳ chọn — khởi tạo ngay)
            </label>
            <input
              type="text"
              className="input"
              placeholder="Gia đình Nguyễn Văn An"
              value={familyName}
              onChange={(e) => setFamilyName(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: "100%", marginTop: 8 }}
          >
            <UserPlus size={18} />
            {loading ? "Đang tạo tài khoản..." : "Đăng ký & Bắt đầu"}
          </button>
        </form>

        <div
          style={{
            marginTop: 18,
            textAlign: "center",
            fontSize: "0.88rem",
            color: "var(--pm-text-secondary)",
          }}
        >
          Đã có tài khoản?{" "}
          <Link
            to="/login"
            style={{ color: "var(--pm-primary)", fontWeight: 600 }}
          >
            Đăng nhập ngay
          </Link>
        </div>
      </div>
    </div>
  );
};

