import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bot,
  Box,
  CheckCircle2,
  Clock,
  DoorOpen,
  FilePlus,
  Pill,
  PlusCircle,
  Users,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";
import { digitalTwinApi } from "../../features/digitalTwin/api";
import { DigitalTwinSummaryResponse } from "../../features/digitalTwin/types";
import { useDigitalTwinStore } from "../../features/digitalTwin/store";

interface DailyDoseItem {
  schedule_id: number;
  time: string;
  member: { id: number; full_name: string };
  medication: {
    id: number;
    name: string;
    strength?: string | null;
    dosage_form?: string | null;
  };
  dose_amount?: number | null;
  dose_unit?: string | null;
  instructions?: string | null;
}

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { families, activeFamilyId, members, createFamily } = useFamilyStore();
  const selectCompartment = useDigitalTwinStore((s) => s.selectCompartment);

  const [dtSummary, setDtSummary] = useState<DigitalTwinSummaryResponse | null>(
    null
  );
  const [dailyDoses, setDailyDoses] = useState<DailyDoseItem[]>([]);
  const [takenKeys, setTakenKeys] = useState<Record<string, boolean>>({});
  const [newFamName, setNewFamName] = useState("");
  const [loading, setLoading] = useState(false);

  const todayIso = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    if (!activeFamilyId) return;
    let cancelled = false;

    const loadDashboard = async () => {
      setLoading(true);
      try {
        const [cabRes, schedRes] = await Promise.all([
          apiRequest<{ items: Array<{ id: number }> }>(
            `/families/${activeFamilyId}/cabinets`
          ),
          apiRequest<{
            items: Array<{
              id: number;
              times: string[];
              member: { id: number; full_name: string };
              medication: {
                id: number;
                name: string;
                strength?: string | null;
                dosage_form?: string | null;
              };
              dose_amount?: number | null;
              dose_unit?: string | null;
              notes?: string | null;
            }>;
          }>(`/families/${activeFamilyId}/schedules?date=${todayIso}`).catch(
            () => ({ items: [] })
          ),
        ]);

        if (cancelled) return;
        const flatDoses: DailyDoseItem[] = [];
        for (const s of schedRes.items || []) {
          for (const t of s.times || []) {
            flatDoses.push({
              schedule_id: s.id,
              time: t,
              member: s.member,
              medication: s.medication,
              dose_amount: s.dose_amount,
              dose_unit: s.dose_unit,
              instructions: s.notes,
            });
          }
        }
        flatDoses.sort((a, b) => a.time.localeCompare(b.time));
        setDailyDoses(flatDoses);

        const firstCab = cabRes.items?.[0];
        if (firstCab) {
          const dt = await digitalTwinApi.getDigitalTwinSummary(
            activeFamilyId,
            firstCab.id
          );
          if (!cancelled) setDtSummary(dt);
        } else {
          setDtSummary(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [activeFamilyId, todayIso]);

  const handleCreateFirstFamily = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFamName.trim()) return;
    await createFamily(newFamName.trim(), "Hộ gia đình PharmaMind AI");
    setNewFamName("");
  };

  const handleOpenNextDoseDrawer = async () => {
    if (!activeFamilyId || !dtSummary || !dtSummary.next_dose_position) return;
    const pos = dtSummary.next_dose_position;
    selectCompartment(pos);
    try {
      await digitalTwinApi.openCompartment(
        activeFamilyId,
        dtSummary.cabinet.id,
        pos
      );
    } catch {
      // ignore if offline
    }
    navigate("/digital-twin");
  };

  if (families.length === 0) {
    return (
      <div className="card" style={{ maxWidth: 560, margin: "24px auto", padding: 32 }}>
        <h2 style={{ marginBottom: 8 }}>
          Chào mừng {user?.full_name || "bạn"} đến với PharmaMind AI 👋
        </h2>
        <p style={{ color: "var(--pm-text-secondary)", marginBottom: 20 }}>
          Hãy khởi tạo Hộ gia đình đầu tiên của bạn để bắt đầu quản lý thành viên,
          kho thuốc, lịch uống thuốc và tủ thuốc thông minh 3D.
        </p>
        <form onSubmit={handleCreateFirstFamily} style={{ display: "flex", gap: 10 }}>
          <input
            type="text"
            className="input"
            placeholder="Ví dụ: Gia đình Nguyễn Văn An"
            value={newFamName}
            onChange={(e) => setNewFamName(e.target.value)}
            required
          />
          <button type="submit" className="btn btn-primary">
            <PlusCircle size={18} />
            Tạo gia đình
          </button>
        </form>
      </div>
    );
  }

  const nextDose = dtSummary?.next_dose;
  const nextPos = dtSummary?.next_dose_position;
  const nextComp = dtSummary?.compartments.find((c) => c.position === nextPos);

  const filledCount =
    dtSummary?.compartments.filter((c) => c.medication !== null).length ?? 0;
  const openCount =
    dtSummary?.compartments.filter((c) => c.is_open).length ?? 0;

  const warningItems: Array<{ label: string; position: number; type: "warn" | "danger" }> =
    [];
  for (const comp of dtSummary?.compartments || []) {
    if (!comp.medication) continue;
    for (const alert of comp.allergy_alerts) {
      warningItems.push({
        label: `Ngăn ${comp.position} (${comp.medication.name}): ${alert.message}`,
        position: comp.position,
        type: "danger",
      });
    }
    if (comp.warnings.includes("LOW_STOCK")) {
      warningItems.push({
        label: `Ngăn ${comp.position}: Thuốc ${comp.medication.name} sắp hết (còn ${comp.medication.quantity} ${comp.medication.unit})`,
        position: comp.position,
        type: "warn",
      });
    }
    if (comp.warnings.includes("EXPIRED")) {
      warningItems.push({
        label: `Ngăn ${comp.position}: Thuốc ${comp.medication.name} đã quá hạn sử dụng`,
        position: comp.position,
        type: "danger",
      });
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      {/* 1. Greeting Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 14,
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 700 }}>
            Xin chào, {user?.full_name || "Gia đình"} 👋
          </h1>
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Tổng quan sức khỏe & lịch dùng thuốc hôm nay ({todayIso}) •{" "}
            {members.length} thành viên
          </p>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Link to="/medications" className="btn btn-outline">
            <PlusCircle size={17} />
            Thêm thuốc
          </Link>
          <Link to="/digital-twin" className="btn btn-primary">
            <Activity size={17} />
            Mở Digital Twin 3D
          </Link>
        </div>
      </div>

      {/* 2. Top Grid: Next Dose Highlight Card + Smart Cabinet Status */}
      <div className="grid-2">
        {/* Next Dose Card */}
        <div className="card card-highlight" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 16 }}>
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
              }}
            >
              <span className="badge badge-primary">
                <Clock size={14} />
                LIỀU UỐNG TIẾP THEO
              </span>
              {nextPos && (
                <span className="badge badge-warning">
                  Ngăn {nextPos} (drawer_0{nextPos})
                </span>
              )}
            </div>

            {nextDose && nextComp?.medication ? (
              <>
                <div style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--pm-text-primary)" }}>
                  {nextDose.time} — {nextComp.medication.name}{" "}
                  {nextComp.medication.strength || ""}
                </div>
                <p style={{ color: "var(--pm-text-secondary)", marginTop: 4 }}>
                  Người dùng: <strong>{nextDose.member.full_name}</strong> • Liều lượng:{" "}
                  <strong>
                    {nextDose.dose_amount || 1} {nextDose.dose_unit || nextComp.medication.unit}
                  </strong>
                </p>
              </>
            ) : dailyDoses.length > 0 ? (
              <>
                <div style={{ fontSize: "1.35rem", fontWeight: 700 }}>
                  {dailyDoses[0].time} — {dailyDoses[0].medication.name}
                </div>
                <p style={{ color: "var(--pm-text-secondary)", marginTop: 4 }}>
                  Người dùng: <strong>{dailyDoses[0].member.full_name}</strong>
                </p>
              </>
            ) : (
              <div>
                <div style={{ fontSize: "1.15rem", fontWeight: 600 }}>
                  Hiện chưa có liều uống sắp tới trong tủ
                </div>
                <p style={{ fontSize: "0.9rem", color: "var(--pm-text-secondary)", marginTop: 4 }}>
                  Bạn có thể thêm đơn thuốc và lịch uống tại mục Lịch uống thuốc.
                </p>
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {nextPos && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleOpenNextDoseDrawer}
              >
                <DoorOpen size={17} />
                Mở Ngăn {nextPos} & Xem trên 3D
              </button>
            )}
            <Link to="/schedules" className="btn btn-secondary">
              Xem toàn bộ lịch uống
            </Link>
          </div>
        </div>

        {/* Smart Cabinet Status Card */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 16 }}>
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
              }}
            >
              <span style={{ fontWeight: 700, fontSize: "1.05rem", display: "flex", alignItems: "center", gap: 8 }}>
                <Box size={19} style={{ color: "var(--pm-primary)" }} />
                Trạng thái Tủ thuốc Thông minh
              </span>
              {dtSummary ? (
                <span
                  className={`badge ${
                    dtSummary.cabinet.status === "ONLINE"
                      ? "badge-success"
                      : "badge-neutral"
                  }`}
                >
                  ● {dtSummary.cabinet.status}
                </span>
              ) : (
                <span className="badge badge-neutral">Chưa kết nối</span>
              )}
            </div>

            {dtSummary ? (
              <div className="grid-3" style={{ gap: 12, marginTop: 10 }}>
                <div
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    background: "var(--pm-bg)",
                  }}
                >
                  <div style={{ fontSize: "0.78rem", color: "var(--pm-text-secondary)" }}>
                    Ngăn có thuốc
                  </div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>
                    {filledCount} / 9
                  </div>
                </div>
                <div
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    background: "var(--pm-bg)",
                  }}
                >
                  <div style={{ fontSize: "0.78rem", color: "var(--pm-text-secondary)" }}>
                    Ngăn đang mở
                  </div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700, color: openCount > 0 ? "var(--pm-success)" : undefined }}>
                    {openCount} ngăn
                  </div>
                </div>
                <div
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    background: "var(--pm-bg)",
                  }}
                >
                  <div style={{ fontSize: "0.78rem", color: "var(--pm-text-secondary)" }}>
                    Cảnh báo
                  </div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700, color: warningItems.length > 0 ? "var(--pm-danger)" : undefined }}>
                    {warningItems.length} mục
                  </div>
                </div>
              </div>
            ) : (
              <p style={{ color: "var(--pm-text-secondary)", fontSize: "0.9rem" }}>
                Gia đình chưa khởi tạo tủ thuốc 6 hộp. Hãy vào mục Digital Twin 3D để tạo tủ thuốc.
              </p>
            )}
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <Link to="/cabinet" className="btn btn-outline" style={{ flex: 1 }}>
              Quản lý ngăn tủ (2D / 3D)
            </Link>
            <Link to="/digital-twin" className="btn btn-primary" style={{ flex: 1 }}>
              Mô hình 3D Tương tác
            </Link>
          </div>
        </div>
      </div>

      {/* 3. Safety & Stock Alerts */}
      {warningItems.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
            <AlertTriangle size={19} style={{ color: "var(--pm-warning)" }} />
            Cảnh báo Thuốc & An toàn Gia đình ({warningItems.length})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {warningItems.map((item, idx) => (
              <div
                key={idx}
                className={`alert-banner ${
                  item.type === "danger" ? "alert-danger" : "alert-warning"
                }`}
                style={{
                  marginBottom: 0,
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>{item.label}</span>
                <button
                  type="button"
                  className="btn btn-sm btn-outline"
                  onClick={() => {
                    selectCompartment(item.position);
                    navigate("/digital-twin");
                  }}
                >
                  Kiểm tra Ngăn {item.position}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Today's Schedule & Quick Actions */}
      <div className="grid-2">
        <div className="card">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 14,
            }}
          >
            <h3 style={{ fontSize: "1.08rem", fontWeight: 700 }}>
              Lịch uống thuốc hôm nay ({dailyDoses.length})
            </h3>
            <Link
              to="/schedules"
              style={{
                fontSize: "0.86rem",
                color: "var(--pm-primary)",
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              Xem chi tiết →
            </Link>
          </div>

          {loading ? (
            <p style={{ color: "var(--pm-text-secondary)" }}>Đang tải lịch uống...</p>
          ) : dailyDoses.length === 0 ? (
            <p style={{ color: "var(--pm-text-secondary)", fontSize: "0.92rem" }}>
              Hôm nay chưa có lịch uống thuốc nào được lên lịch.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {dailyDoses.map((dose, idx) => {
                const key = `${dose.schedule_id}-${dose.time}-${idx}`;
                const isTaken = Boolean(takenKeys[key]);
                return (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px 14px",
                      borderRadius: 12,
                      border: "1px solid var(--pm-border)",
                      background: isTaken ? "var(--pm-success-bg)" : "#fff",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700 }}>
                        {dose.time} — {dose.medication.name}{" "}
                        {dose.medication.strength || ""}
                      </div>
                      <div
                        style={{
                          fontSize: "0.84rem",
                          color: "var(--pm-text-secondary)",
                        }}
                      >
                        {dose.member.full_name} • Liều:{" "}
                        {dose.dose_amount || 1} {dose.dose_unit || "viên"}
                        {dose.instructions ? ` • ${dose.instructions}` : ""}
                      </div>
                    </div>

                    <button
                      type="button"
                      className={`btn btn-sm ${
                        isTaken ? "btn-secondary" : "btn-primary"
                      }`}
                      onClick={() =>
                        setTakenKeys((prev) => ({ ...prev, [key]: !prev[key] }))
                      }
                    >
                      <CheckCircle2 size={15} />
                      {isTaken ? "Đã uống" : "Xác nhận uống"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick Actions Grid */}
        <div className="card">
          <h3 style={{ fontSize: "1.08rem", fontWeight: 700, marginBottom: 14 }}>
            Thao tác nhanh cho Gia đình
          </h3>
          <div className="grid-2" style={{ gap: 12 }}>
            <Link
              to="/family"
              className="card"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: 16,
              }}
            >
              <Users size={24} style={{ color: "var(--pm-primary)" }} />
              <div>
                <div style={{ fontWeight: 700 }}>Hồ sơ Thành viên</div>
                <div style={{ fontSize: "0.8rem", color: "var(--pm-text-secondary)" }}>
                  Bệnh nền, dị ứng & liên hệ
                </div>
              </div>
            </Link>

            <Link
              to="/medications"
              className="card"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: 16,
              }}
            >
              <Pill size={24} style={{ color: "var(--pm-primary)" }} />
              <div>
                <div style={{ fontWeight: 700 }}>Kho thuốc Gia đình</div>
                <div style={{ fontSize: "0.8rem", color: "var(--pm-text-secondary)" }}>
                  Tồn kho, hạn dùng & dạng bào chế
                </div>
              </div>
            </Link>

            <Link
              to="/prescriptions"
              className="card"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: 16,
              }}
            >
              <FilePlus size={24} style={{ color: "var(--pm-primary)" }} />
              <div>
                <div style={{ fontWeight: 700 }}>Đơn thuốc & Lịch</div>
                <div style={{ fontSize: "0.8rem", color: "var(--pm-text-secondary)" }}>
                  Thiết lập giờ nhắc uống thuốc
                </div>
              </div>
            </Link>

            <Link
              to="/ai"
              className="card"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: 16,
              }}
            >
              <Bot size={24} style={{ color: "var(--pm-primary)" }} />
              <div>
                <div style={{ fontWeight: 700 }}>Hỏi AI Dược sĩ</div>
                <div style={{ fontSize: "0.8rem", color: "var(--pm-text-secondary)" }}>
                  Tra cứu cách dùng & lưu ý thuốc
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

