import { create } from "zustand";
import { CabinetRealtimeMessage } from "../../services/websocketClient";
import { HardwareState, PhysicalBoxState } from "./hardware";
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
  hardwareConnected: boolean;
  hardwareBoxes: Record<string, PhysicalBoxState> | null;
  legacyCompartmentCount: number;
  isLoading: boolean;
  error: string | null;

  setDigitalTwinData: (data: DigitalTwinSummaryResponse) => void;
  selectCompartment: (position: number | null) => void;
  hoverCompartment: (position: number | null) => void;
  setFilterMemberId: (memberId: number | null) => void;
  setWsConnected: (connected: boolean) => void;
  applyHardwareState: (state: HardwareState) => void;
  setHardwareLed: (position: number, ledState: "ON" | "OFF") => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  applyRealtimeEvent: (evt: CabinetRealtimeMessage) => void;
  reset: () => void;
}

function buildDefaultCompartments(): DigitalTwinCompartment[] {
  return Array.from({ length: 6 }, (_, i) => {
    const pos = i + 1;
    return {
      id: pos,
      position: pos,
      object_id: positionToObjectId(pos),
      label: `Ngăn ${pos}`,
      status: "EMPTY",
      is_open: false,
      led_state: "OFF",
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
  hardwareConnected: false,
  hardwareBoxes: null,
  legacyCompartmentCount: 0,
  isLoading: false,
  error: null,

  setDigitalTwinData: (data: DigitalTwinSummaryResponse) => {
    const currentSelected = get().selectedPosition;
    const defaultSelect =
      (currentSelected && currentSelected <= 6 ? currentSelected : null) ??
      (data.next_dose_position && data.next_dose_position <= 6 ? data.next_dose_position : null) ??
      data.compartments.find((c) => c.position <= 6 && c.medication !== null)?.position ??
      1;
    set({
      cabinet: data.cabinet,
      legacyCompartmentCount: data.compartments.filter((comp) => comp.position > 6).length,
      compartments: data.compartments
        .filter((comp) => comp.position >= 1 && comp.position <= 6)
        .map((comp) => {
          const physical = get().hardwareBoxes?.[String(comp.position)];
          return physical ? {
            ...comp,
            is_open: physical.status === "OPEN",
            led_state: physical.led_state,
            status: physical.status === "OPEN" ? "OPEN" : comp.medication ? "AVAILABLE" : "EMPTY",
          } : comp;
        }),
      nextDosePosition: data.next_dose_position && data.next_dose_position <= 6 ? data.next_dose_position : null,
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
  applyHardwareState: ({ connected, boxes }) => set((state) => ({
    hardwareConnected: connected,
    hardwareBoxes: connected ? boxes : null,
    compartments: state.compartments.map((comp) => {
      const physical = connected ? boxes?.[String(comp.position)] : null;
      return physical ? {
        ...comp,
        is_open: physical.status === "OPEN",
        led_state: physical.led_state,
        status: physical.status === "OPEN" ? "OPEN" : comp.medication ? "AVAILABLE" : "EMPTY",
      } : comp;
    }),
  })),
  setHardwareLed: (position, ledState) => set((state) => ({
    hardwareBoxes: state.hardwareBoxes ? {
      ...state.hardwareBoxes,
      [String(position)]: { ...state.hardwareBoxes[String(position)], led_state: ledState },
    } : null,
    compartments: state.compartments.map((comp) => comp.position === position
      ? { ...comp, led_state: ledState }
      : comp),
  })),
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

    if (state.hardwareBoxes && (
      event_type === "COMPARTMENT_OPEN" ||
      event_type === "COMPARTMENT_CLOSE" ||
      event_type === "CABINET_STATE_SYNC"
    )) return;

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
      hardwareConnected: false,
      hardwareBoxes: null,
      legacyCompartmentCount: 0,
      isLoading: false,
      error: null,
    }),
}));

