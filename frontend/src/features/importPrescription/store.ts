import { create } from "zustand";
import type { ImportMode, ImportSession, WizardStep } from "./types";

interface ImportWizardState {
  step: WizardStep;
  memberId: number | null;
  importMode: ImportMode;
  targetPrescriptionId: number | null;
  session: ImportSession | null;
  busy: boolean;
  error: string | null;
  confirmSchedules: boolean;
  confirmHealth: boolean;
  setStep: (step: WizardStep) => void;
  setMemberId: (id: number | null) => void;
  setImportMode: (mode: ImportMode) => void;
  setTargetPrescriptionId: (id: number | null) => void;
  setSession: (s: ImportSession | null) => void;
  setBusy: (b: boolean) => void;
  setError: (e: string | null) => void;
  setConfirmSchedules: (v: boolean) => void;
  setConfirmHealth: (v: boolean) => void;
  reset: () => void;
}

const initial = {
  step: 0 as WizardStep,
  memberId: null,
  importMode: "CREATE_NEW_PRESCRIPTION" as ImportMode,
  targetPrescriptionId: null,
  session: null,
  busy: false,
  error: null,
  confirmSchedules: true,
  confirmHealth: false,
};

export const useImportWizardStore = create<ImportWizardState>((set) => ({
  ...initial,
  setStep: (step) => set({ step, error: null }),
  setMemberId: (memberId) => set({ memberId }),
  setImportMode: (importMode) => set({ importMode }),
  setTargetPrescriptionId: (targetPrescriptionId) => set({ targetPrescriptionId }),
  setSession: (session) => set({ session }),
  setBusy: (busy) => set({ busy }),
  setError: (error) => set({ error }),
  setConfirmSchedules: (confirmSchedules) => set({ confirmSchedules }),
  setConfirmHealth: (confirmHealth) => set({ confirmHealth }),
  reset: () => set({ ...initial }),
}));

