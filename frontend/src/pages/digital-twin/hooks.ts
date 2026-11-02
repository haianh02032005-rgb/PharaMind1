import { useCallback, useEffect } from "react";
import { digitalTwinApi } from "../../features/digitalTwin/api";
import { useDigitalTwinStore } from "../../features/digitalTwin/store";
import { createDigitalTwinWebSocket } from "../../features/digitalTwin/websocket";

export function useDigitalTwinController(
  familyId: number | null,
  cabinetId: number | null
) {
  const {
    cabinet,
    compartments,
    selectedPosition,
    hoveredPosition,
    nextDosePosition,
    nextDose,
    filterMemberId,
    wsConnected,
    isLoading,
    error,
    setDigitalTwinData,
    selectCompartment,
    hoverCompartment,
    setFilterMemberId,
    setLoading,
    setError,
  } = useDigitalTwinStore();

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
      await digitalTwinApi.openCompartment(familyId, cabinetId, position);
      await refreshSummary();
    },
    [familyId, cabinetId, refreshSummary]
  );

  const handleCloseCompartment = useCallback(
    async (position: number) => {
      if (!familyId || !cabinetId) return;
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

