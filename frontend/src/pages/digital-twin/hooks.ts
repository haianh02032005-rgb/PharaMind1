import { useCallback, useEffect, useState } from "react";
import { digitalTwinApi } from "../../features/digitalTwin/api";
import { useDigitalTwinStore } from "../../features/digitalTwin/store";
import { createDigitalTwinWebSocket } from "../../features/digitalTwin/websocket";
import { isPiHardwareApp, sendHardwareCommand } from "../../features/digitalTwin/hardware";

export function useDigitalTwinController(
  familyId: number | null,
  cabinetId: number | null
) {
  const [unlockDisabled, setUnlockDisabled] = useState(false);
  const {
    cabinet,
    compartments,
    selectedPosition,
    hoveredPosition,
    nextDosePosition,
    nextDose,
    filterMemberId,
    wsConnected,
    hardwareConnected,
    isLoading,
    error,
    setDigitalTwinData,
    selectCompartment,
    hoverCompartment,
    setFilterMemberId,
    setLoading,
    setError,
  } = useDigitalTwinStore();

  useEffect(() => {
    const bridge = window.pharmamindHardware;
    if (!bridge) return;
    const unsubscribe = bridge.subscribe((state) => {
      useDigitalTwinStore.getState().applyHardwareState(state);
    });
    void bridge.getState().then((state) => {
      useDigitalTwinStore.getState().applyHardwareState(state);
    }).catch(() => {
      useDigitalTwinStore.getState().applyHardwareState({ connected: false, boxes: null });
    });
    return unsubscribe;
  }, []);

  const refreshSummary = useCallback(async () => {
    if (!familyId || !cabinetId) return;
    setLoading(true);
    try {
      const summary = await digitalTwinApi.getDigitalTwinSummary(
        familyId,
        cabinetId,
        filterMemberId
      );
      setDigitalTwinData(summary);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Không thể tải dữ liệu Digital Twin 3D"
      );
    }
  }, [familyId, cabinetId, filterMemberId, setDigitalTwinData, setLoading, setError]);

  useEffect(() => {
    if (!familyId || !cabinetId) return;
    void refreshSummary();
  }, [familyId, cabinetId, filterMemberId, refreshSummary]);

  // Connect WebSocket for realtime updates + fallback polling every 12s if disconnected
  useEffect(() => {
    if (!familyId || !cabinetId) return;
    const wsClient = createDigitalTwinWebSocket(familyId, cabinetId);
    wsClient.connect();

    const pollInterval = setInterval(() => {
      if (!useDigitalTwinStore.getState().wsConnected) {
        void refreshSummary();
      }
    }, 12000);

    return () => {
      clearInterval(pollInterval);
      wsClient.disconnect();
    };
  }, [familyId, cabinetId, refreshSummary]);

  const handleOpenCompartment = useCallback(
    async (position: number) => {
      if (!familyId || !cabinetId) return;
      if (isPiHardwareApp()) {
        if (unlockDisabled) throw new Error("Vui lòng đợi chốt ngăn trước nhả hoàn toàn");
        setUnlockDisabled(true);
        try {
          await sendHardwareCommand({ action: "UNLOCK_BOX", box_id: position });
        } finally {
          window.setTimeout(() => setUnlockDisabled(false), 2500);
        }
        return;
      }
      await digitalTwinApi.openCompartment(familyId, cabinetId, position);
      await refreshSummary();
    },
    [familyId, cabinetId, refreshSummary, unlockDisabled]
  );

  const handleSetLed = useCallback(async (position: number, state: "ON" | "OFF") => {
    await sendHardwareCommand({ action: "SET_LED", box_id: position, state });
    useDigitalTwinStore.getState().setHardwareLed(position, state);
  }, []);

  const handleCloseCompartment = useCallback(
    async (position: number) => {
      if (!familyId || !cabinetId) return;
      if (isPiHardwareApp()) {
        throw new Error("Hãy đóng ngăn bằng tay; cảm biến sẽ cập nhật trạng thái tự động");
      }
      await digitalTwinApi.closeCompartment(familyId, cabinetId, position);
      await refreshSummary();
    },
    [familyId, cabinetId, refreshSummary]
  );

  const handleToggleOnline = useCallback(async () => {
    if (!familyId || !cabinetId || !cabinet) return;
    if (cabinet.status === "ONLINE") {
      await digitalTwinApi.setSimulatorOffline(familyId, cabinetId);
    } else {
      await digitalTwinApi.setSimulatorOnline(familyId, cabinetId);
    }
    await refreshSummary();
  }, [familyId, cabinetId, cabinet, refreshSummary]);

  const handleSyncState = useCallback(async () => {
    if (!familyId || !cabinetId) return;
    await digitalTwinApi.syncCabinetState(familyId, cabinetId);
    await refreshSummary();
  }, [familyId, cabinetId, refreshSummary]);

  return {
    cabinet,
    compartments,
    selectedPosition,
    hoveredPosition,
    nextDosePosition,
    nextDose,
    filterMemberId,
    wsConnected,
    hardwareConnected,
    isPiHardwareApp: isPiHardwareApp(),
    unlockDisabled,
    handleSetLed,
    effectiveCabinetStatus: isPiHardwareApp() ? (hardwareConnected ? "ONLINE" : "OFFLINE") : cabinet?.status,
    isLoading,
    error,
    selectCompartment,
    hoverCompartment,
    setFilterMemberId,
    refreshSummary,
    handleOpenCompartment,
    handleCloseCompartment,
    handleToggleOnline,
    handleSyncState,
  };
}

