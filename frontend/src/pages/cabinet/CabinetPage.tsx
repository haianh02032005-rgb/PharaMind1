import React, { useEffect, useState } from "react";
import { Box, Grid, Sparkles } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { useUiStore } from "../../store/uiStore";
import { apiRequest } from "../../services/apiClient";
import { digitalTwinApi } from "../../features/digitalTwin/api";
import {
  selectCompartmentVisualStatus,
  selectSelectedCompartment,
} from "../../features/digitalTwin/selectors";
import { useDigitalTwinStore } from "../../features/digitalTwin/store";
import { useDigitalTwinController } from "../digital-twin/hooks";
import { StatusBar } from "../digital-twin/StatusBar";
import { DigitalTwinLayout } from "../digital-twin/DigitalTwinLayout";
import { AvailableMedicationOption } from "../digital-twin/InfoPanel";
import { useDrawerRevealController } from "../../features/cabinet/reveal/hooks";
import { CapsulePopout } from "../../components/cabinet/CapsulePopout";
import { MedicationRevealCard } from "../../components/cabinet/MedicationRevealCard";

export const CabinetPage: React.FC = () => {
  const { activeFamilyId } = useFamilyStore();
  const { cabinetViewMode, setCabinetViewMode } = useUiStore();
  const [cabinetId, setCabinetId] = useState<number | null>(null);
  const [availableMeds, setAvailableMeds] = useState<AvailableMedicationOption[]>([]);

  useEffect(() => {
    if (!activeFamilyId) return;
    Promise.all([
      apiRequest<{ items: Array<{ id: number }> }>(
        `/families/${activeFamilyId}/cabinets`
      ),
      apiRequest<{
        items: Array<{
          id: number;
          catalog?: { name: string; strength?: string | null };
          quantity: number;
          unit: string;
          status: string;
        }>;
      }>(`/families/${activeFamilyId}/medications`),
    ])
      .then(([cabRes, medRes]) => {
        setCabinetId(cabRes.items?.[0]?.id ?? null);
        setAvailableMeds(
          (medRes.items || [])
            .filter((m) => m.status === "ACTIVE")
            .map((m) => ({
              id: m.id,
              name: m.catalog?.name || `Thuốc #${m.id}`,
              strength: m.catalog?.strength,
              quantity: m.quantity,
              unit: m.unit,
            }))
        );
      })
      .catch(() => setCabinetId(null));
  }, [activeFamilyId]);

  const dt = useDigitalTwinController(activeFamilyId, cabinetId);
  const selectedCompartment = useDigitalTwinStore(selectSelectedCompartment);
  const reveal = useDrawerRevealController({
    familyId: activeFamilyId,
    cabinetId,
    cabinetStatus: dt.cabinet?.status,
    compartments: dt.compartments,
    selectedPosition: dt.selectedPosition,
    nextDosePosition: dt.nextDosePosition,
  });

  const handleAssignMed = async (position: number, medicationId: number) => {
    if (!activeFamilyId || !cabinetId) return;
    await digitalTwinApi.assignMedication(
      activeFamilyId,
      cabinetId,
      position,
      medicationId
    );
    await dt.refreshSummary();
  };

  const handleUnassignMed = async (position: number) => {
    if (!activeFamilyId || !cabinetId) return;
    await digitalTwinApi.unassignMedication(activeFamilyId, cabinetId, position);
    await dt.refreshSummary();
  };

  if (!cabinetId) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 36 }}>
        <Box
          size={42}
          style={{ color: "var(--pm-primary)", margin: "0 auto 12px" }}
        />
        <h3>Chưa kết nối Tủ thuốc Thông minh</h3>
        <p style={{ color: "var(--pm-text-secondary)", marginTop: 6 }}>
          Hãy mở mục Digital Twin 3D để khởi tạo tủ thuốc 9 ngăn cho gia đình.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Header & Mode Switcher (Simple Mode 2D vs 3D Digital Twin) */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 14,
          marginBottom: 16,
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.55rem", fontWeight: 700 }}>
            Tủ thuốc Thông minh 9 Ngăn
          </h1>
          <p style={{ color: "var(--pm-text-secondary)" }}>
            Chuyển đổi linh hoạt giữa Chế độ Đơn giản (Lưới 3×3 dễ đọc cho người lớn
            tuổi) và Chế độ 3D (Digital Twin).
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            className={`btn ${
              cabinetViewMode === "SIMPLE" ? "btn-primary" : "btn-outline"
            }`}
            onClick={() => setCabinetViewMode("SIMPLE")}
          >
            <Grid size={17} />
            Chế độ Đơn giản (2D 3×3)
          </button>
          <button
            type="button"
            className={`btn ${
              cabinetViewMode === "3D" ? "btn-primary" : "btn-outline"
            }`}
            onClick={() => setCabinetViewMode("3D")}
          >
            <Sparkles size={17} />
            Chế độ 3D (Digital Twin)
          </button>
        </div>
      </div>

      <StatusBar
        cabinet={dt.cabinet}
        wsConnected={dt.wsConnected}
        onToggleOnline={dt.handleToggleOnline}
        onSyncState={dt.handleSyncState}
      />

      {cabinetViewMode === "3D" ? (
        <DigitalTwinLayout
          compartments={dt.compartments}
          selectedCompartment={selectedCompartment}
          selectedPosition={dt.selectedPosition}
          hoveredPosition={dt.hoveredPosition}
          nextDosePosition={dt.nextDosePosition}
          cabinetStatus={dt.cabinet?.status}
          availableMedications={availableMeds}
          onSelectCompartment={dt.selectCompartment}
          onHoverCompartment={dt.hoverCompartment}
          onOpenCompartment={dt.handleOpenCompartment}
          onCloseCompartment={dt.handleCloseCompartment}
          onAssignMedication={handleAssignMed}
          onUnassignMedication={handleUnassignMed}
        />
      ) : (
        /* Simple Mode 2D 3x3 Grid for Elderly Accessibility */
        <div className="dt-layout">
          <div className="card">
            <h3 style={{ marginBottom: 14 }}>
              Sơ đồ 9 Ngăn Tủ Thuốc (Chế độ Đơn giản Dễ đọc)
            </h3>
            <div className="cabinet-grid-3x3">
              {dt.compartments.map((comp) => {
                const vis = selectCompartmentVisualStatus(
                  comp,
                  dt.selectedPosition,
                  dt.nextDosePosition,
                  dt.cabinet?.status
                );
                return (
                  <div
                    key={comp.position}
                    onClick={() => dt.selectCompartment(comp.position)}
                    className={`compartment-tile ${
                      vis.isSelected ? "selected" : ""
                    } ${vis.isHighlightedNextDose ? "next-dose" : ""} ${
                      comp.is_open ? "is-open" : ""
                    }`}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <span style={{ fontWeight: 700, fontSize: "1.08rem" }}>
                        Ngăn {comp.position}
                      </span>
                      <span className={`badge badge-${vis.badgeVariant}`}>
                        {vis.badgeLabel}
                      </span>
                    </div>

                    <div style={{ margin: "10px 0" }}>
                      {comp.medication ? (
                        comp.is_open && dt.cabinet?.status !== "OFFLINE" ? (
                          <CapsulePopout
                            visible={true}
                            medicationName={comp.medication.name}
                            strength={comp.medication.strength}
                            animationMode={reveal.animationMode}
                            size="md"
                          />
                        ) : (
                          <>
                            <div style={{ fontWeight: 700, fontSize: "1rem" }}>
                              💊 {comp.medication.name}
                            </div>
                            <div
                              style={{
                                fontSize: "0.85rem",
                                color: "var(--pm-text-secondary)",
                              }}
                            >
                              Còn {comp.medication.quantity} {comp.medication.unit}
                            </div>
                          </>
                        )
                      ) : (
                        <div style={{ color: "var(--pm-text-secondary)" }}>
                          Chưa đặt thuốc
                        </div>
                      )}
                    </div>

                    <div
                      style={{
                        fontSize: "0.78rem",
                        color: "var(--pm-text-secondary)",
                      }}
                    >
                      {comp.next_dose
                        ? `⏰ Liều kế: ${comp.next_dose.time} (${comp.next_dose.member.full_name})`
                        : comp.object_id}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <MedicationRevealCard
            revealData={reveal.revealData}
            isPanelOpen={Boolean(selectedCompartment)}
            isAnimating={reveal.isAnimating}
            animationMode={reveal.animationMode}
            openedBy={reveal.openedBy ?? "USER"}
            error={reveal.error}
            availableMedications={availableMeds}
            onOpenCompartment={async (pos) => {
              await dt.handleOpenCompartment(pos);
              await reveal.triggerReveal(pos, "USER", true);
            }}
            onCloseCompartment={async (pos) => {
              await dt.handleCloseCompartment(pos);
              await reveal.triggerReveal(pos, "USER", false);
            }}
            onAssignMedication={handleAssignMed}
            onUnassignMedication={handleUnassignMed}
            onRetry={reveal.retryFetchReveal}
          />
        </div>
      )}
    </div>
  );
};

