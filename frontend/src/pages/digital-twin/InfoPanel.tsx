import React from "react";
import { DigitalTwinCompartment } from "../../features/digitalTwin/types";
import { buildRevealDataFromCompartment } from "../../features/cabinet/reveal/types";
import { useDrawerRevealStore } from "../../features/cabinet/reveal/hooks";
import { DrawerInfoPanel } from "../../components/cabinet/DrawerInfoPanel";
import { useUiStore } from "../../store/uiStore";

export interface AvailableMedicationOption {
  id: number;
  name: string;
  strength?: string | null;
  quantity: number;
  unit: string;
}

interface InfoPanelProps {
  compartment: DigitalTwinCompartment | null;
  cabinetStatus?: string;
  nextDosePosition: number | null;
  availableMedications?: AvailableMedicationOption[];
  onOpenCompartment: (position: number) => Promise<void>;
  onCloseCompartment: (position: number) => Promise<void>;
  onAssignMedication?: (position: number, medicationId: number) => Promise<void>;
  onUnassignMedication?: (position: number) => Promise<void>;
}

export const InfoPanel: React.FC<InfoPanelProps> = ({
  compartment,
  cabinetStatus = "ONLINE",
  nextDosePosition,
  availableMedications = [],
  onOpenCompartment,
  onCloseCompartment,
  onAssignMedication,
  onUnassignMedication,
}) => {
  const { elderlyMode, reducedMotion } = useUiStore();
  const revealStore = useDrawerRevealStore();
  const animationMode = elderlyMode || reducedMotion ? "REDUCED" : "FULL";

  const revealData =
    compartment &&
    revealStore.revealData &&
    revealStore.revealData.position === compartment.position
      ? {
          ...revealStore.revealData,
          is_open: compartment.is_open,
          cabinet_status: cabinetStatus,
        }
      : compartment
      ? buildRevealDataFromCompartment(
          compartment,
          0,
          cabinetStatus,
          nextDosePosition
        )
      : null;

  return (
    <DrawerInfoPanel
      revealData={revealData}
      isPanelOpen={Boolean(compartment)}
      isAnimating={revealStore.isAnimating}
      animationMode={animationMode}
      openedBy={revealStore.openedBy ?? "USER"}
      error={revealStore.error}
      availableMedications={availableMedications}
      onOpenCompartment={onOpenCompartment}
      onCloseCompartment={onCloseCompartment}
      onAssignMedication={onAssignMedication}
      onUnassignMedication={onUnassignMedication}
    />
  );
};
