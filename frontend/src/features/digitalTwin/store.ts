import { create } from "zustand";
import { CabinetRealtimeMessage } from "../../services/websocketClient";
import {
  DigitalTwinCabinetHeader,
  DigitalTwinCompartment,
  DigitalTwinNextDose,
  DigitalTwinSummaryResponse,
  positionToObjectId,
} from "./types";

export interface DigitalTwinState {
  cabinet: DigitalTwinCabinetHeader | null;
  compartments: DigitalTwinCompartment[];
  selectedPosition: number | null;
  hoveredPosition: number | null;
  nextDosePosition: number | null;
  nextDose: DigitalTwinNextDose | null;
  filterMemberId: number | null;
  wsConnected: boolean;
  isLoading: boolean;
  error: string | null;

  setDigitalTwinData: (data: DigitalTwinSummaryResponse) => void;
  selectCompartment: (position: number | null) => void;
  hoverCompartment: (position: number | null) => void;
  setFilterMemberId: (memberId: number | null) => void;
  setWsConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  applyRealtimeEvent: (evt: CabinetRealtimeMessage) => void;
  reset: () => void;
}

function buildDefaultCompartments(): DigitalTwinCompartment[] {
  return Array.from({ length: 9 }, (_, i) => {
    const pos = i + 1;
    return {
      id: pos,
      position: pos,
      object_id: positionToObjectId(pos),
      label: `Ngăn ${pos}`,
      status: "EMPTY",
      is_open: false,
      medication: null,
      members: [],
      next_dose: null,
      warnings: [],
      allergy_alerts: [],
    };
  });
}

export const useDigitalTwinStore = create<DigitalTwinState>((set, get) => ({
  cabinet: null,
  compartments: buildDefaultCompartments(),
  selectedPosition: 1,
  hoveredPosition: null,
  nextDosePosition: null,
  nextDose: null,
  filterMemberId: null,
  wsConnected: false,
  isLoading: false,
  error: null,

  setDigitalTwinData: (data: DigitalTwinSummaryResponse) => {
    const currentSelected = get().selectedPosition;
    const defaultSelect =
      currentSelected ??
      data.next_dose_position ??
      data.compartments.find((c) => c.medication !== null)?.position ??
      1;
    set({
      cabinet: data.cabinet,
      compartments: data.compartments,
      nextDosePosition: data.next_dose_position,
      nextDose: data.next_dose,
      selectedPosition: defaultSelect,
      isLoading: false,
      error: null,
    });
  },

  selectCompartment: (position) => set({ selectedPosition: position }),
  hoverCompartment: (position) => set({ hoveredPosition: position }),
  setFilterMemberId: (memberId) => set({ filterMemberId: memberId }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),

  applyRealtimeEvent: (evt: CabinetRealtimeMessage) => {
    const state = get();
    const { event_type, occurred_at, payload } = evt;

    if (event_type === "CABINET_ONLINE") {
      if (state.cabinet) {
        set({
          cabinet: {
            ...state.cabinet,
            status: "ONLINE",
            last_seen_at: occurred_at || state.cabinet.last_seen_at,
          },
        });
      }
      return;
    }

    if (event_type === "CABINET_OFFLINE") {
      if (state.cabinet) {
        set({
          cabinet: {
            ...state.cabinet,
            status: "OFFLINE",
            last_seen_at: occurred_at || state.cabinet.last_seen_at,
          },
        });
      }
      return;
    }

    if (
      event_type === "COMPARTMENT_OPEN" ||
      event_type === "COMPARTMENT_CLOSE"
    ) {
      const targetPos = Number(payload?.position);
      const isOpen =
        event_type === "COMPARTMENT_OPEN"
          ? true
          : event_type === "COMPARTMENT_CLOSE"
          ? false
          : Boolean(payload?.is_open);

      set({
        cabinet: state.cabinet
          ? {
              ...state.cabinet,
              last_seen_at: occurred_at || state.cabinet.last_seen_at,
            }
          : null,
        compartments: state.compartments.map((comp) => {
          if (comp.position !== targetPos) return comp;
          return {
            ...comp,
            is_open: isOpen,
            status: isOpen
              ? "OPEN"
              : comp.medication
              ? "AVAILABLE"
              : "EMPTY",
          };
        }),
      });
      return;
    }

    if (event_type === "CABINET_STATE_SYNC") {
      const compMap = (payload?.compartments || {}) as Record<string, boolean>;
      set({
        cabinet: state.cabinet
          ? {
              ...state.cabinet,
              status: (payload?.status as string) || state.cabinet.status,
              last_seen_at: occurred_at || state.cabinet.last_seen_at,
            }
          : null,
        compartments: state.compartments.map((comp) => {
          const openVal = compMap[String(comp.position)];
          if (typeof openVal !== "boolean") return comp;
          return {
            ...comp,
            is_open: openVal,
            status: openVal
              ? "OPEN"
              : comp.medication
              ? "AVAILABLE"
              : "EMPTY",
          };
        }),
      });
    }
  },

  reset: () =>
    set({
      cabinet: null,
      compartments: buildDefaultCompartments(),
      selectedPosition: 1,
      hoveredPosition: null,
      nextDosePosition: null,
      nextDose: null,
      filterMemberId: null,
      wsConnected: false,
      isLoading: false,
      error: null,
    }),
}));

