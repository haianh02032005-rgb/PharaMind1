import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Box,
  Calendar,
  CalendarClock,
  ChevronDown,
  ChevronUp,
  Clock,
  DoorClosed,
  DoorOpen,
  Package,
  Pill,
  PlusCircle,
  RefreshCw,
  Trash2,
  UserCheck,
  WifiOff,
  X,
} from "lucide-react";
import {
  AnimationMode,
  DrawerRevealData,
  OpenedBySource,
} from "../../features/cabinet/reveal/types";
import {
  formatExpirationMonthYear,
  formatMedicationUnitVi,
  formatMemberScheduleLabelVi,
  selectPrioritizedMembers,
  selectRevealContextEmphasis,
  selectSafetyWarnings,
  selectShouldShowCapsule,
} from "../../features/cabinet/reveal/selectors";
import { CapsulePopout } from "./CapsulePopout";
import { DrawerWarningBadge } from "./DrawerWarningBadge";
import { AvailableMedicationOption } from "../../pages/digital-twin/InfoPanel";

export interface DrawerInfoPanelProps {
  revealData: DrawerRevealData | null;
  isPanelOpen: boolean;
  isAnimating?: boolean;
  animationMode?: AnimationMode;
  openedBy?: OpenedBySource;
  error?: string | null;
  availableMedications?: AvailableMedicationOption[];
  onOpenCompartment: (position: number) => Promise<void>;
  onCloseCompartment: (position: number) => Promise<void>;
  onAssignMedication?: (position: number, medicationId: number) => Promise<void>;
  onUnassignMedication?: (position: number) => Promise<void>;
  onRetry?: () => void;
  onClosePanel?: () => void;
  hardwareMode?: boolean;
  hardwareConnected?: boolean;
  unlockDisabled?: boolean;
  ledState?: "ON" | "OFF";
  onSetLed?: (position: number, state: "ON" | "OFF") => Promise<void>;
}

export const DrawerInfoPanel: React.FC<DrawerInfoPanelProps> = ({
  revealData,
  isPanelOpen,
  isAnimating = false,
  animationMode = "FULL",
  openedBy = "USER",
  error = null,
  availableMedications = [],
  onOpenCompartment,
  onCloseCompartment,
  onAssignMedication,
  onUnassignMedication,
  onRetry,
  onClosePanel,
  hardwareMode = false,
  hardwareConnected = false,
  unlockDisabled = false,
  ledState = "OFF",
  onSetLed,
}) => {
  const [showMore, setShowMore] = useState(false);
  const [selectedMedId, setSelectedMedId] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (error && !revealData) {
    return (
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div className="alert-banner alert-danger" style={{ marginBottom: 0 }}>
          <AlertTriangle size={18} />
          <span>Không thể tải thông tin thuốc lúc này.</span>
        </div>
        {onRetry && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onRetry}
          >
            <RefreshCw size={15} />
            Thử lại
          </button>
        )}
      </div>
    );
  }

  if (!revealData) {
    return (
      <div className="card">
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Hãy chọn hoặc mở một ngăn thuốc để xem viên thuốc minh họa và thông tin người
          dùng.
        </p>
      </div>
    );
  }

  const isOffline = revealData.cabinet_status === "OFFLINE";
  const med = revealData.medication;
  const prioritizedMembers = selectPrioritizedMembers(revealData);
  const primaryMember = prioritizedMembers[0] || null;
  const warnings = selectSafetyWarnings(revealData);
  const showCapsule = selectShouldShowCapsule(revealData, isPanelOpen || revealData.is_open);
  const emphasis = selectRevealContextEmphasis({
    selectedPosition: revealData.position,
    isPanelOpen,
    isAnimating,
    animationMode,
    revealData,
    openedBy,
    isLoading: false,
    error,
  });

  const unitVi = formatMedicationUnitVi(med?.unit);
  const primaryDoseAmount =
    primaryMember?.dose_amount ?? revealData.next_dose?.dose_amount ?? 1;
  const primaryDoseUnitVi = formatMedicationUnitVi(
    primaryMember?.dose_unit ?? revealData.next_dose?.dose_unit ?? med?.unit
  );

  const handleToggleDrawer = async () => {
    setActionError(null);
    setBusy(true);
    try {
      if (revealData.is_open) {
        await onCloseCompartment(revealData.position);
      } else {
        await onOpenCompartment(revealData.position);
      }
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Không thể điều khiển ngăn tủ"
      );
    } finally {
      setBusy(false);
    }
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onAssignMedication || !selectedMedId) return;
    setActionError(null);
    setBusy(true);
    try {
      await onAssignMedication(revealData.position, Number(selectedMedId));
      setSelectedMedId("");
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Không thể gán thuốc cho ngăn"
      );
    } finally {
      setBusy(false);
    }
  };

  const handleUnassign = async () => {
    if (!onUnassignMedication) return;
    setActionError(null);
    setBusy(true);
    try {
      await onUnassignMedication(revealData.position);
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Không thể gỡ thuốc khỏi ngăn"
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        transition:
          animationMode === "REDUCED"
            ? "none"
            : "all 260ms cubic-bezier(0.22, 1, 0.36, 1)",
      }}
    >
      {/* Top Bar: Compartment Header & Context Emphasis Badge */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid var(--pm-border)",
          paddingBottom: 12,
          gap: 10,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: "1.22rem", fontWeight: 700 }}>
              {revealData.label || `Ngăn ${revealData.position}`}
            </span>
            <code
              style={{
                fontSize: "0.76rem",
                padding: "2px 8px",
                borderRadius: 6,
                background: "var(--pm-bg)",
                color: "var(--pm-text-secondary)",
              }}
            >
              {revealData.object_id}
            </code>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className={`badge badge-${emphasis.variant}`}>
            {emphasis.title}
          </span>
          {onClosePanel && (
            <button
              type="button"
              className="btn btn-sm btn-outline"
              onClick={onClosePanel}
              title="Đóng bảng thông tin"
              style={{ padding: "4px 8px" }}
            >
              <X size={15} />
            </button>
          )}
        </div>
      </div>

      {/* Offline State Banner (§24) */}
      {isOffline && (
        <div className="alert-banner alert-warning" style={{ marginBottom: 0 }}>
          <WifiOff size={18} style={{ flexShrink: 0, marginTop: 2 }} />
          <span>
            Thiết bị hiện không kết nối. Dữ liệu có thể chưa được cập nhật mới nhất.
          </span>
        </div>
      )}

      {actionError && (
        <div className="alert-banner alert-danger" style={{ marginBottom: 0 }}>
          <AlertTriangle size={18} />
          <span>{actionError}</span>
        </div>
      )}

      {/* Open / Close Drawer Primary Button */}
      <div style={{ display: "flex", gap: 10 }}>
        <button
          type="button"
          disabled={busy || isOffline || (hardwareMode && (!hardwareConnected || unlockDisabled || revealData.is_open))}
          onClick={handleToggleDrawer}
          className={`btn ${
            revealData.is_open ? "btn-outline" : "btn-primary"
          }`}
          style={{ flex: 1 }}
        >
          {hardwareMode && revealData.is_open ? (
            <>Ngăn đang mở · đóng bằng tay</>
          ) : revealData.is_open ? (
            <>
              <DoorClosed size={18} />
              Đóng ngăn {revealData.position}
            </>
          ) : (
            <>
              <DoorOpen size={18} />
              {hardwareMode ? `Mở chốt hộp ${revealData.position}` : `Mở ngăn ${revealData.position} (Xem thuốc bay ra)`}
            </>
          )}
        </button>
        {hardwareMode && onSetLed && (
          <button
            type="button"
            className="btn btn-outline"
            disabled={!hardwareConnected || busy}
            onClick={async () => {
              setActionError(null);
              setBusy(true);
              try {
                await onSetLed(revealData.position, ledState === "ON" ? "OFF" : "ON");
              } catch (err) {
                setActionError(err instanceof Error ? err.message : "Không thể điều khiển LED");
              } finally {
                setBusy(false);
              }
            }}
          >
            Đèn LED: {ledState === "ON" ? "Bật" : "Tắt"}
          </button>
        )}
      </div>

      {/* Empty State (§22): No capsule fly-out; show empty message & assign CTA */}
      {!med ? (
        <div
          style={{
            padding: 22,
            borderRadius: 16,
            background: "var(--pm-bg)",
            border: "1px dashed var(--pm-border)",
            textAlign: "center",
          }}
        >
          <Box
            size={34}
            style={{ color: "var(--pm-offline)", margin: "0 auto 8px" }}
          />
          <div style={{ fontWeight: 700, fontSize: "1.05rem", marginBottom: 4 }}>
            Ngăn này hiện chưa có thuốc.
          </div>
          <p
            style={{
              fontSize: "0.88rem",
              color: "var(--pm-text-secondary)",
              marginBottom: 14,
            }}
          >
            Khi ngăn trống, hiệu ứng viên thuốc bay ra sẽ không kích hoạt.
          </p>

          {onAssignMedication && availableMedications.length > 0 && (
            <form onSubmit={handleAssign} style={{ display: "flex", gap: 8 }}>
              <select
                className="select"
                value={selectedMedId}
                onChange={(e) => setSelectedMedId(e.target.value)}
                required
              >
                <option value="">-- Chọn thuốc để gán cho ngăn --</option>
                {availableMedications.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} {m.strength ? `(${m.strength})` : ""} — Còn {m.quantity}{" "}
                    {m.unit}
                  </option>
                ))}
              </select>
              <button
                type="submit"
                className="btn btn-primary btn-sm"
                disabled={busy || !selectedMedId}
              >
                <PlusCircle size={16} />
                Gán thuốc cho ngăn
              </button>
            </form>
          )}
        </div>
      ) : (
        <>
          {/* 1. Capsule Illustration & Medication Name (§12, §34, §35) */}
          {showCapsule ? (
            <CapsulePopout
              visible={true}
              medicationName={med.name}
              strength={med.strength}
              animationMode={animationMode}
              size="lg"
            />
          ) : (
            <div
              style={{
                padding: "14px 16px",
                borderRadius: 14,
                background: "var(--pm-bg)",
                border: "1px solid var(--pm-border)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  fontWeight: 700,
                  fontSize: "1.18rem",
                }}
              >
                <Pill size={20} style={{ color: "var(--pm-primary)" }} />
                <span>
                  {med.name} {med.strength ? `${med.strength}` : ""}
                </span>
              </div>
              <span className="badge badge-neutral">Ngăn đang đóng</span>
            </div>
          )}

          {/* Next Dose Priority Highlight (§14) */}
          {revealData.is_next_dose && revealData.next_dose && (
            <div
              style={{
                padding: "12px 16px",
                borderRadius: 14,
                background: "var(--pm-warning-bg)",
                border: "1.5px solid var(--pm-warning)",
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <Clock size={20} style={{ color: "#b7791f", flexShrink: 0 }} />
              <div>
                <div style={{ fontWeight: 700, color: "#8a5a0d" }}>
                  {openedBy === "SYSTEM"
                    ? "Đến giờ uống thuốc"
                    : `Tiếp theo: ${revealData.next_dose.time} hôm nay`}
                </div>
                <div style={{ fontSize: "0.88rem", color: "#8a5a0d" }}>
                  Người uống: <strong>{revealData.next_dose.member.full_name}</strong> •
                  Liều:{" "}
                  <strong>
                    {revealData.next_dose.dose_amount || 1} {primaryDoseUnitVi}
                  </strong>
                </div>
              </div>
            </div>
          )}

          {/* 2 & 3. Structured Key Facts Block (§12, §34, §35) */}
          <div
            style={{
              padding: 16,
              borderRadius: 16,
              background: "#ffffff",
              border: "1.5px solid var(--pm-border)",
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            {/* Người cần uống & Lịch uống (§11.2, §11.3, §13, §23) */}
            <div>
              <div
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  color: "var(--pm-text-secondary)",
                  marginBottom: 4,
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <UserCheck size={15} style={{ color: "var(--pm-primary)" }} />
                Người cần uống & Lịch uống:
              </div>

              {prioritizedMembers.length === 0 ? (
                <div style={{ fontWeight: 600, color: "var(--pm-text-secondary)" }}>
                  Chưa gán thành viên sử dụng • Chưa có lịch uống cụ thể.
                </div>
              ) : prioritizedMembers.length === 1 ? (
                <div>
                  <div style={{ fontSize: "1.08rem", fontWeight: 700 }}>
                    {primaryMember.full_name}{" "}
                    {primaryMember.relationship_label
                      ? `(${primaryMember.relationship_label})`
                      : ""}
                  </div>
                  <div
                    style={{
                      fontSize: "0.95rem",
                      color: "var(--pm-primary)",
                      fontWeight: 600,
                      marginTop: 2,
                    }}
                  >
                    Lịch uống: {formatMemberScheduleLabelVi(primaryMember)}
                  </div>
                </div>
              ) : (
                /* Multiple members using the same medication (§13) */
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {prioritizedMembers.map((m) => (
                    <div
                      key={m.id}
                      style={{
                        padding: "8px 10px",
                        borderRadius: 10,
                        background: "var(--pm-bg)",
                        fontSize: "0.94rem",
                        fontWeight: 600,
                      }}
                    >
                      • {m.full_name} — {formatMemberScheduleLabelVi(m)} —{" "}
                      {m.dose_amount || 1}{" "}
                      {formatMedicationUnitVi(m.dose_unit || med.unit)}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Liều dùng, Còn lại & Hạn dùng Grid (§12, §34) */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                gap: 10,
                paddingTop: 10,
                borderTop: "1px solid var(--pm-border)",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "0.78rem",
                    color: "var(--pm-text-secondary)",
                  }}
                >
                  Liều dùng
                </div>
                <div style={{ fontWeight: 700, fontSize: "1.02rem" }}>
                  {primaryDoseAmount} {primaryDoseUnitVi}
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontSize: "0.78rem",
                    color: "var(--pm-text-secondary)",
                  }}
                >
                  Còn lại
                </div>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "1.02rem",
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <Package size={15} style={{ color: "var(--pm-primary)" }} />
                  {med.quantity} {unitVi}
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontSize: "0.78rem",
                    color: "var(--pm-text-secondary)",
                  }}
                >
                  Hạn dùng
                </div>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "0.98rem",
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <Calendar size={15} style={{ color: "var(--pm-primary)" }} />
                  {formatExpirationMonthYear(med.expiration_date)}
                </div>
              </div>
            </div>
          </div>

          {/* 6. Safety Warning Section (§11.4, §12, §15, §37) */}
          <div>
            <div
              style={{
                fontSize: "0.82rem",
                fontWeight: 600,
                color: "var(--pm-text-secondary)",
                marginBottom: 6,
              }}
            >
              Cảnh báo an toàn:
            </div>
            <DrawerWarningBadge warnings={warnings} />
          </div>

          {/* Expandable "Xem thêm" section for secondary details (§35) */}
          <div>
            <button
              type="button"
              className="btn btn-sm btn-outline"
              onClick={() => setShowMore(!showMore)}
              style={{ width: "100%", justifyContent: "space-between" }}
            >
              <span>
                {showMore
                  ? "Thu gọn thông tin chi tiết"
                  : "Xem thêm (Hoạt chất, dạng bào chế & quản lý ngăn)"}
              </span>
              {showMore ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {showMore && (
              <div
                style={{
                  marginTop: 10,
                  padding: 14,
                  borderRadius: 12,
                  background: "var(--pm-bg)",
                  fontSize: "0.88rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                }}
              >
                <div>
                  <strong>Hoạt chất:</strong>{" "}
                  {med.active_ingredient || "Chưa cập nhật"}
                </div>
                <div>
                  <strong>Dạng bào chế:</strong> {med.dosage_form || "TABLET"}
                </div>
                <div>
                  <strong>Hạn sử dụng đầy đủ:</strong>{" "}
                  {med.expiration_date || "Chưa cập nhật"}
                </div>
                {primaryMember?.instructions && (
                  <div>
                    <strong>Hướng dẫn dùng:</strong> {primaryMember.instructions}
                  </div>
                )}

                {onUnassignMedication && (
                  <div style={{ marginTop: 8, textAlign: "right" }}>
                    <button
                      type="button"
                      className="btn btn-sm btn-danger"
                      disabled={busy}
                      onClick={handleUnassign}
                    >
                      <Trash2 size={14} />
                      Gỡ thuốc khỏi ngăn {revealData.position}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action CTAs (§36) */}
          <div
            style={{
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
              paddingTop: 6,
              borderTop: "1px solid var(--pm-border)",
            }}
          >
            <Link
              to="/medications"
              className="btn btn-sm btn-secondary"
              style={{ flex: 1 }}
            >
              <Pill size={15} />
              Xem chi tiết thuốc
            </Link>
            <Link
              to="/schedules"
              className="btn btn-sm btn-secondary"
              style={{ flex: 1 }}
            >
              <CalendarClock size={15} />
              Xem lịch hôm nay
            </Link>
          </div>
        </>
      )}
    </div>
  );
};

