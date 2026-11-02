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
    let demoEmail = "giadinh.pharmamind@example.com";
    const demoPass = "PharmaMind123";
    try {
      try {
        await authService.login({ email: demoEmail, password: demoPass });
      } catch {
        try {
          await authService.register({
            email: demoEmail,
            password: demoPass,
            full_name: "Nguyễn Văn An",
          });
        } catch {
          demoEmail = `giadinh.${Date.now().toString().slice(-5)}@example.com`;
          await authService.register({
            email: demoEmail,
            password: demoPass,
            full_name: "Nguyễn Văn An",
          });
        }
        await authService.login({ email: demoEmail, password: demoPass });
      }
      await hydrate();
      const families = await fetchFamilies();

      if (families.length === 0) {
        // Seed a realistic Vietnamese family with members, medications, schedules & 9-drawer cabinet
        const fam = await useFamilyStore
          .getState()
          .createFamily(
            "Gia đình Nguyễn Văn An",
            "Tủ thuốc thông minh phòng khách"
          );

        const memMom = await apiRequest<{ id: number }>(
          `/families/${fam.id}/members`,
          {
            method: "POST",
            body: JSON.stringify({
              full_name: "Bà Nguyễn Thị Lan",
              relationship_label: "Mẹ",
              gender: "FEMALE",
              date_of_birth: "1960-05-14",
            }),
          }
        );

        const memDad = await apiRequest<{ id: number }>(
          `/families/${fam.id}/members`,
          {
            method: "POST",
            body: JSON.stringify({
              full_name: "Ông Nguyễn Văn Minh",
              relationship_label: "Bố",
              gender: "MALE",
              date_of_birth: "1958-09-20",
            }),
          }
        );

        // Add allergy to Amoxicillin for Bà Lan
        await apiRequest(
          `/families/${fam.id}/members/${memMom.id}/allergies`,
          {
            method: "POST",
            body: JSON.stringify({
              allergen: "Amoxicillin",
              allergy_type: "DRUG",
              severity: "SEVERE",
              reaction_description: "Nổi mề đay, khó thở nhẹ",
            }),
          }
        );

        // Create 3 medications
        const med1 = await apiRequest<{ id: number }>(
          `/families/${fam.id}/medications`,
          {
            method: "POST",
            body: JSON.stringify({
              name: "Amlodipine",
              active_ingredient: "Amlodipine",
              strength: "5mg",
              dosage_form: "TABLET",
              quantity: 28,
              unit: "TABLET",
              low_stock_threshold: 7,
              expiration_date: "2028-10-30",
            }),
          }
        );

        const med2 = await apiRequest<{ id: number }>(
          `/families/${fam.id}/medications`,
          {
            method: "POST",
            body: JSON.stringify({
              name: "Paracetamol",
              active_ingredient: "Paracetamol",
              strength: "500mg",
              dosage_form: "TABLET",
              quantity: 4,
              unit: "TABLET",
              low_stock_threshold: 6,
              expiration_date: "2028-06-15",
            }),
          }
        );

        const med3 = await apiRequest<{ id: number }>(
          `/families/${fam.id}/medications`,
          {
            method: "POST",
            body: JSON.stringify({
              name: "Amoxicillin",
              active_ingredient: "Amoxicillin",
              strength: "500mg",
              dosage_form: "CAPSULE",
              quantity: 16,
              unit: "CAPSULE",
              low_stock_threshold: 4,
              expiration_date: "2028-12-31",
            }),
          }
        );

        // Link members
        await apiRequest(
          `/families/${fam.id}/medications/${med1.id}/members`,
          {
            method: "POST",
            body: JSON.stringify({ member_id: memMom.id }),
          }
        );
        await apiRequest(
          `/families/${fam.id}/medications/${med2.id}/members`,
          {
            method: "POST",
            body: JSON.stringify({ member_id: memDad.id }),
          }
        );
        await apiRequest(
          `/families/${fam.id}/medications/${med3.id}/members`,
          {
            method: "POST",
            body: JSON.stringify({ member_id: memMom.id }),
          }
        );

        // Create prescription & schedule
        const rx = await apiRequest<{ id: number }>(
          `/families/${fam.id}/prescriptions`,
          {
            method: "POST",
            body: JSON.stringify({
              member_id: memMom.id,
              title: "Đơn thuốc huyết áp định kỳ",
              start_date: "2026-01-01",
              end_date: "2028-12-31",
            }),
          }
        );

        const rxItem = await apiRequest<{ id: number }>(
          `/families/${fam.id}/prescriptions/${rx.id}/items`,
          {
            method: "POST",
            body: JSON.stringify({
              family_medication_id: med1.id,
              dose_amount: 1,
              dose_unit: "TABLET",
              frequency_per_day: 2,
              instructions: "Uống sau bữa sáng và bữa tối",
            }),
          }
        );

        await apiRequest(`/families/${fam.id}/schedules`, {
          method: "POST",
          body: JSON.stringify({
            prescription_item_id: rxItem.id,
            start_date: "2026-01-01",
            end_date: "2028-12-31",
            recurrence_type: "DAILY",
            times: ["08:00", "20:00"],
          }),
        });

        // Create Smart Cabinet & assign compartments 1, 5, 8
        const cab = await apiRequest<{ id: number }>(
          `/families/${fam.id}/cabinets`,
          {
            method: "POST",
            body: JSON.stringify({
              name: "Tủ thuốc Thông minh Phòng khách",
              device_code: `PM-DEMO-${Math.random()
                .toString(36)
                .substring(2, 7)
                .toUpperCase()}`,
            }),
          }
        );

        await apiRequest(
          `/families/${fam.id}/cabinets/${cab.id}/simulator/online`,
          { method: "POST" }
        );
        await apiRequest(
          `/families/${fam.id}/cabinets/${cab.id}/compartments/1/medication`,
          {
            method: "PUT",
            body: JSON.stringify({ family_medication_id: med1.id }),
          }
        );
        await apiRequest(
          `/families/${fam.id}/cabinets/${cab.id}/compartments/5/medication`,
          {
            method: "PUT",
            body: JSON.stringify({ family_medication_id: med2.id }),
          }
        );
        await apiRequest(
          `/families/${fam.id}/cabinets/${cab.id}/compartments/8/medication`,
          {
            method: "PUT",
            body: JSON.stringify({ family_medication_id: med3.id }),
          }
        );

        await fetchFamilies();
      }
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Không thể khởi tạo dữ liệu demo"
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
            style={{ width: "100%" }}
          >
            <Sparkles size={18} />
            {demoLoading
              ? "Đang khởi tạo Gia đình & Tủ thuốc 3D mẫu..."
              : "Trải nghiệm nhanh (Tự động nạp Gia đình & Tủ 3D mẫu)"}
          </button>
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

