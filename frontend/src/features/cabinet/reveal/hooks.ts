import { create } from "zustand";
import { useCallback, useEffect } from "react";
import {
  AnimationMode,
  buildRevealDataFromCompartment,
  DrawerRevealData,
  DrawerRevealState,
  OpenedBySource,
} from "./types";
import { drawerRevealApi } from "./api";
import {
  CAPSULE_FLYOUT_DURATION_MS,
  CAPSULE_REDUCED_DURATION_MS,
  logRevealEvent,
} from "./animation";
import { DigitalTwinCompartment } from "../../digitalTwin/types";
import { useUiStore } from "../../../store/uiStore";

interface DrawerRevealStore extends DrawerRevealState {
  openReveal: (params: {
    position: number;
    openedBy: OpenedBySource;
    animationMode: AnimationMode;
    initialData?: DrawerRevealData | null;
  }) => void;
  setRevealData: (data: DrawerRevealData) => void;
  setRevealError: (err: string | null) => void;
  finishAnimation: () => void;
  closeReveal: () => void;
  setAnimationMode: (mode: AnimationMode) => void;
}

export const useDrawerRevealStore = create<DrawerRevealStore>((set, get) => ({
  selectedPosition: null,
  isPanelOpen: false,
  isAnimating: false,
  animationMode: "FULL",
  revealData: null,
  openedBy: null,
  isLoading: false,
  error: null,

  openReveal: ({ position, openedBy, animationMode, initialData }) => {
    logRevealEvent("drawer_reveal_opened", {
      position,
      openedBy,
      animationMode,
    });
    if (initialData?.medication && initialData.is_open) {
      logRevealEvent("capsule_animation_played", {
        position,
        animationMode,
        medicationId: initialData.medication.id,
      });
    }
    if (initialData?.warnings && initialData.warnings.length > 0) {
      logRevealEvent("warning_panel_viewed", {
        position,
        warningCount: initialData.warnings.length,
      });
    }
    set({
      selectedPosition: position,
      isPanelOpen: true,
      isAnimating: Boolean(initialData?.medication && initialData?.is_open),
      animationMode,
      revealData: initialData ?? get().revealData,
      openedBy,
      isLoading: !initialData,
      error: null,
    });
  },

  setRevealData: (data) => {
    const prev = get();
    if (data.warnings && data.warnings.length > 0) {
      logRevealEvent("warning_panel_viewed", {
        position: data.position,
        warningCount: data.warnings.length,
      });
    }
    set({
      revealData: data,
      isLoading: false,
      error: null,
      isAnimating: prev.isAnimating || Boolean(data.medication && data.is_open),
    });
  },

  setRevealError: (err) => {
    if (err) {
      logRevealEvent("drawer_reveal_failed", { error: err });
    }
    set({ error: err, isLoading: false });
  },

  finishAnimation: () => set({ isAnimating: false }),

  closeReveal: () => {
    const pos = get().selectedPosition;
    logRevealEvent("drawer_reveal_closed", { position: pos });
    set({
      isPanelOpen: false,
      isAnimating: false,
      openedBy: null,
      error: null,
    });
  },

  setAnimationMode: (mode) => set({ animationMode: mode }),
}));

/**
 * Hook that coordinates Drawer Open -> Capsule Fly-out -> Medication Info Reveal
 * across both 3D Mode and Simple Mode (§7, §19, §25, §26).
 */
export function useDrawerRevealController(params: {
  familyId: number | null;
  cabinetId: number | null;
  cabinetStatus?: string;
  compartments: DigitalTwinCompartment[];
  selectedPosition: number | null;
  nextDosePosition: number | null;
}) {
  const {
    familyId,
    cabinetId,
    cabinetStatus = "ONLINE",
    compartments,
    selectedPosition,
    nextDosePosition,
  } = params;

  const { elderlyMode, reducedMotion } = useUiStore();
  const prefersReduced =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const animationMode: AnimationMode =
    elderlyMode || reducedMotion || prefersReduced ? "REDUCED" : "FULL";

  const store = useDrawerRevealStore();

  useEffect(() => {
    if (store.animationMode !== animationMode) {
      store.setAnimationMode(animationMode);
    }
  }, [animationMode, store]);

  const fetchRevealForPosition = useCallback(
    async (position: number, forceRefresh = false) => {
      if (!familyId || !cabinetId) return;
      try {
        const remote = await drawerRevealApi.getCompartmentReveal(
          familyId,
          cabinetId,
          position,
          { forceRefresh }
        );
        store.setRevealData(remote);
      } catch (err) {
        // Keep cached revealData if cabinet is offline or already populated, only surface error if no data
        if (!useDrawerRevealStore.getState().revealData) {
          store.setRevealError(
            err instanceof Error
              ? err.message
              : "Không thể tải thông tin thuốc lúc này."
          );
        }
      }
    },
    [familyId, cabinetId, store]
  );

  const triggerReveal = useCallback(
    async (
      position: number,
      openedBy: OpenedBySource = "USER",
      forceOpenState?: boolean
    ) => {
      const comp = compartments.find((c) => c.position === position);
      const initialData = comp
        ? buildRevealDataFromCompartment(
            forceOpenState !== undefined
              ? { ...comp, is_open: forceOpenState }
              : comp,
            cabinetId || 0,
            cabinetStatus,
            nextDosePosition
          )
        : null;

      store.openReveal({
        position,
        openedBy,
        animationMode,
        initialData,
      });

      const duration =
        animationMode === "REDUCED"
          ? CAPSULE_REDUCED_DURATION_MS
          : CAPSULE_FLYOUT_DURATION_MS;
      setTimeout(() => {
        useDrawerRevealStore.getState().finishAnimation();
      }, duration);

      await fetchRevealForPosition(position, true);
    },
    [
      compartments,
      cabinetId,
      cabinetStatus,
      nextDosePosition,
      animationMode,
      store,
      fetchRevealForPosition,
    ]
  );

  // Sync reveal state when selected compartment or its open/close state changes in realtime (§25, §26)
  useEffect(() => {
    if (!selectedPosition) return;
    const comp = compartments.find((c) => c.position === selectedPosition);
    if (!comp) return;

    const currentReveal = store.revealData;
    const updatedLocal = buildRevealDataFromCompartment(
      comp,
      cabinetId || 0,
      cabinetStatus,
      nextDosePosition
    );

    // If a drawer transitions from closed -> open (either by USER or SYSTEM COMPARTMENT_OPEN event)
    if (
      comp.is_open &&
      (!store.isPanelOpen ||
        currentReveal?.position !== comp.position ||
        !currentReveal?.is_open)
    ) {
      const source: OpenedBySource =
        store.openedBy ??
        (comp.position === nextDosePosition ? "SYSTEM" : "USER");
      store.openReveal({
        position: comp.position,
        openedBy: source,
        animationMode,
        initialData: updatedLocal,
      });
      void fetchRevealForPosition(comp.position, true);
      return;
    }

    // If drawer is selected by user, keep revealData synchronized with selected compartment
    if (currentReveal?.position !== comp.position || store.isPanelOpen) {
      store.setRevealData(updatedLocal);
    }
  }, [
    selectedPosition,
    compartments,
    cabinetId,
    cabinetStatus,
    nextDosePosition,
    animationMode,
  ]);

  return {
    ...store,
    animationMode,
    triggerReveal,
    retryFetchReveal: () => {
      if (store.selectedPosition) {
        void fetchRevealForPosition(store.selectedPosition, true);
      }
    },
  };
}

