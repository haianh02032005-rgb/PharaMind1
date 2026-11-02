import React, { useEffect, useState } from "react";
import { Box, Filter, PlusCircle } from "lucide-react";
import { useFamilyStore } from "../../store/familyStore";
import { apiRequest } from "../../services/apiClient";
import { digitalTwinApi } from "../../features/digitalTwin/api";
import { selectSelectedCompartment } from "../../features/digitalTwin/selectors";
import { useDigitalTwinStore } from "../../features/digitalTwin/store";
import { useDigitalTwinController } from "./hooks";
import { StatusBar } from "./StatusBar";
import { DigitalTwinLayout } from "./DigitalTwinLayout";
import { AvailableMedicationOption } from "./InfoPanel";
import { useDrawerRevealController } from "../../features/cabinet/reveal/hooks";

interface CabinetBrief {
  id: number;
  name: string;
  device_code: string;
  status: string;
}

export const DigitalTwinPage: React.FC = () => {
  const { activeFamilyId, members } = useFamilyStore();
  const [cabinetId, setCabinetId] = useState<number | null>(null);
  const [availableMeds, setAvailableMeds] = useState<AvailableMedicationOption[]>([]);
  const [creatingCabinet, setCreatingCabinet] = useState(false);

  const loadFamilyCabinetAndMeds = async (famId: number) => {
    try {
      const [cabRes, medRes] = await Promise.all([
        apiRequest<{ items: CabinetBrief[] }>(`/families/${famId}/cabinets`),
        apiRequest<{
          items: Array<{
            id: number;
            catalog?: { name: string; strength?: string | null };
            quantity: number;
            unit: string;
            status: string;
          }>;
        }>(`/families/${famId}/medications`),
      ]);
      const activeCab = (cabRes.items || [])[0] || null;
      setCabinetId(activeCab ? activeCab.id : null);
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
    } catch {
      setCabinetId(null);
    }
  };

  useEffect(() => {
    if (activeFamilyId) {
      void loadFamilyCabinetAndMeds(activeFamilyId);
    }
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

  const handleQuickCreateCabinet = async () => {
    if (!activeFamilyId) return;
    setCreatingCabinet(true);
    try {
      const code = `PM-CAB-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
      const created = await apiRequest<CabinetBrief>(
        `/families/${activeFamilyId}/cabinets`,
        {
          method: "POST",
          body: JSON.stringify({
            name: "Tủ thuốc thông minh Gia đình",
            device_code: code,
            notes: "Tủ thuốc 9 ngăn đồng bộ Digital Twin 3D",
          }),
        }
      );
      await digitalTwinApi.setSimulatorOnline(activeFamilyId, created.id);
      setCabinetId(created.id);
    } finally {
      setCreatingCabinet(false);
    }
  };

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

  if (!activeFamilyId) {
    return (
      <div className="card">
        <h3>Chưa chọn hộ gia đình</h3>
        <p style={{ color: "var(--pm-text-secondary)", marginTop: 6 }}>
          Vui lòng tạo hoặc chọn một gia đình tại mục Gia đình để sử dụng Digital Twin 3D.
        </p>
      </div>
    );
  }

  if (!cabinetId) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 36 }}>
        <Box
          size={44}
          style={{ color: "var(--pm-primary)", margin: "0 auto 12px" }}
        />
        <h2 style={{ marginBottom: 8 }}>
          Khởi tạo Tủ thuốc Thông minh 9 Ngăn (Digital Twin 3D)
        </h2>
        <p
          style={{
            color: "var(--pm-text-secondary)",
            maxWidth: 520,
            margin: "0 auto 20px",
          }}
        >
          Gia đình bạn chưa có tủ thuốc thông minh được kết nối. Nhấn nút bên dưới để
          khởi tạo tủ thuốc 9 ngăn và đồng bộ trực tiếp với mô hình Digital Twin 3D.
        </p>
        <button
          type="button"
          className="btn btn-primary"
          disabled={creatingCabinet}
          onClick={handleQuickCreateCabinet}
        >
          <PlusCircle size={18} />
          {creatingCabinet
            ? "Đang khởi tạo tủ thuốc 9 ngăn..."
            : "Tạo Tủ thuốc Thông minh 9 Ngăn ngay"}
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header & Member Filter */}
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
            Digital Twin 3D — {dt.cabinet?.name || "Tủ thuốc Thông minh"}
          </h1>
          <p style={{ color: "var(--pm-text-secondary)", fontSize: "0.92rem" }}>
            Mô hình song sinh số 3D thời gian thực đồng bộ trực tiếp với trạng thái 9 ngăn tủ thuốc.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Filter size={16} style={{ color: "var(--pm-text-secondary)" }} />
          <select
            className="select"
            style={{ width: 230 }}
            value={dt.filterMemberId ?? ""}
            onChange={(e) =>
              dt.setFilterMemberId(
                e.target.value ? Number(e.target.value) : null
              )
            }
          >
            <option value="">Tất cả thành viên gia đình</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.full_name} {m.relationship_label ? `(${m.relationship_label})` : ""}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar
        cabinet={dt.cabinet}
        wsConnected={dt.wsConnected}
        onToggleOnline={dt.handleToggleOnline}
        onSyncState={dt.handleSyncState}
      />

      {/* 2-Column 3D Digital Twin Layout */}
      <DigitalTwinLayout
        compartments={dt.compartments}
        selectedCompartment={selectedCompartment}
        selectedPosition={dt.selectedPosition}
        hoveredPosition={dt.hoveredPosition}
        nextDosePosition={dt.nextDosePosition}
        cabinetStatus={dt.cabinet?.status}
        availableMedications={availableMeds}
        onSelectCompartment={(pos) => {
          dt.selectCompartment(pos);
          void reveal.triggerReveal(pos, "USER");
        }}
        onHoverCompartment={(pos) => dt.hoverCompartment(pos)}
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
      />
    </div>
  );
};

