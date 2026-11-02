import React from "react";
import { DigitalTwinCompartment } from "../../features/digitalTwin/types";
import { CabinetCanvas } from "./CabinetCanvas";
import { AvailableMedicationOption, InfoPanel } from "./InfoPanel";

interface DigitalTwinLayoutProps {
  compartments: DigitalTwinCompartment[];
  selectedCompartment: DigitalTwinCompartment | null;
  selectedPosition: number | null;
  hoveredPosition: number | null;
  nextDosePosition: number | null;
  cabinetStatus?: string;
  availableMedications?: AvailableMedicationOption[];
  onSelectCompartment: (position: number) => void;
  onHoverCompartment: (position: number | null) => void;
  onOpenCompartment: (position: number) => Promise<void>;
  onCloseCompartment: (position: number) => Promise<void>;
  onAssignMedication?: (position: number, medicationId: number) => Promise<void>;
  onUnassignMedication?: (position: number) => Promise<void>;
}

export const DigitalTwinLayout: React.FC<DigitalTwinLayoutProps> = ({
  compartments,
  selectedCompartment,
  selectedPosition,
  hoveredPosition,
  nextDosePosition,
  cabinetStatus,
  availableMedications,
  onSelectCompartment,
  onHoverCompartment,
  onOpenCompartment,
  onCloseCompartment,
  onAssignMedication,
  onUnassignMedication,
}) => {
  return (
    <div className="dt-layout">
      <CabinetCanvas
        compartments={compartments}
        selectedPosition={selectedPosition}
        hoveredPosition={hoveredPosition}
        nextDosePosition={nextDosePosition}
        cabinetStatus={cabinetStatus}
        onSelectCompartment={onSelectCompartment}
        onHoverCompartment={onHoverCompartment}
      />

      <InfoPanel
        compartment={selectedCompartment}
        cabinetStatus={cabinetStatus}
        nextDosePosition={nextDosePosition}
        availableMedications={availableMedications}
        onOpenCompartment={onOpenCompartment}
        onCloseCompartment={onCloseCompartment}
        onAssignMedication={onAssignMedication}
        onUnassignMedication={onUnassignMedication}
      />
    </div>
  );
};

