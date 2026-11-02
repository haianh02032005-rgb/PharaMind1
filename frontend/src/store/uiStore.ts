import { create } from "zustand";

interface UiState {
  elderlyMode: boolean;
  reducedMotion: boolean;
  cabinetViewMode: "3D" | "SIMPLE";
  toggleElderlyMode: () => void;
  setElderlyMode: (enabled: boolean) => void;
  toggleReducedMotion: () => void;
  setCabinetViewMode: (mode: "3D" | "SIMPLE") => void;
}

const ELDERLY_KEY = "pm_elderly_mode";
const REDUCED_MOTION_KEY = "pm_reduced_motion";

function readBool(key: string): boolean {
  try {
    return localStorage.getItem(key) === "true";
  } catch {
    return false;
  }
}

function syncBodyClasses(elderly: boolean, reduced: boolean): void {
  if (typeof document === "undefined") return;
  document.body.classList.toggle("elderly-mode", elderly);
  document.body.classList.toggle("reduced-motion", reduced);
}

const initialElderly = readBool(ELDERLY_KEY);
const initialReduced = readBool(REDUCED_MOTION_KEY);
syncBodyClasses(initialElderly, initialReduced);

export const useUiStore = create<UiState>((set, get) => ({
  elderlyMode: initialElderly,
  reducedMotion: initialReduced,
  cabinetViewMode: initialElderly ? "SIMPLE" : "3D",

  toggleElderlyMode: () => {
    const next = !get().elderlyMode;
    try {
      localStorage.setItem(ELDERLY_KEY, String(next));
    } catch {
      // ignore
    }
    syncBodyClasses(next, get().reducedMotion);
    set({
      elderlyMode: next,
      cabinetViewMode: next ? "SIMPLE" : get().cabinetViewMode,
    });
  },

  setElderlyMode: (enabled: boolean) => {
    try {
      localStorage.setItem(ELDERLY_KEY, String(enabled));
    } catch {
      // ignore
    }
    syncBodyClasses(enabled, get().reducedMotion);
    set({ elderlyMode: enabled });
  },

  toggleReducedMotion: () => {
    const next = !get().reducedMotion;
    try {
      localStorage.setItem(REDUCED_MOTION_KEY, String(next));
    } catch {
      // ignore
    }
    syncBodyClasses(get().elderlyMode, next);
    set({ reducedMotion: next });
  },

  setCabinetViewMode: (mode) => set({ cabinetViewMode: mode }),
}));

