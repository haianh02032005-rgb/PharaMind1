import { DigitalTwinCompartment } from "./types";
import { DigitalTwinState } from "./store";

export function selectSelectedCompartment(
  state: DigitalTwinState
): DigitalTwinCompartment | null {
  if (state.selectedPosition === null) return null;
  return (
    state.compartments.find((c) => c.position === state.selectedPosition) ??
    null
  );
}

export function selectNextDoseCompartment(
  state: DigitalTwinState
): DigitalTwinCompartment | null {
  if (state.nextDosePosition === null) return null;
  return (
    state.compartments.find((c) => c.position === state.nextDosePosition) ??
    null
  );
}

export function selectCompartmentVisualStatus(
  comp: DigitalTwinCompartment,
  selectedPosition: number | null,
  nextDosePosition: number | null,
  cabinetStatus?: string
): {
  colorHex: string;
  badgeLabel: string;
  badgeVariant: "success" | "warning" | "danger" | "primary" | "neutral";
  isHighlightedNextDose: boolean;
  isSelected: boolean;
} {
  const isSelected = comp.position === selectedPosition;
  const isHighlightedNextDose = comp.position === nextDosePosition;

  if (cabinetStatus === "OFFLINE") {
    return {
      colorHex: "#8FA3A8",
      badgeLabel: "Tủ mất kết nối",
      badgeVariant: "neutral",
      isHighlightedNextDose,
      isSelected,
    };
  }

  if (comp.is_open) {
    return {
      colorHex: "#2FA66A",
      badgeLabel: "Đang mở",
      badgeVariant: "success",
      isHighlightedNextDose,
      isSelected,
    };
  }

  if (
    comp.warnings.includes("EXPIRED") ||
    comp.warnings.includes("DEPLETED")
  ) {
    return {
      colorHex: "#D9534F",
      badgeLabel: comp.warnings.includes("EXPIRED") ? "Quá hạn" : "Hết thuốc",
      badgeVariant: "danger",
      isHighlightedNextDose,
      isSelected,
    };
  }

  if (
    comp.warnings.includes("ALLERGY_RISK") ||
    comp.warnings.includes("DRUG_REACTION_RISK")
  ) {
    return {
      colorHex: "#D9534F",
      badgeLabel: "Cảnh báo dị ứng",
      badgeVariant: "danger",
      isHighlightedNextDose,
      isSelected,
    };
  }

  if (
    isHighlightedNextDose ||
    comp.warnings.includes("LOW_STOCK") ||
    comp.warnings.includes("EXPIRING")
  ) {
    return {
      colorHex: "#E6A83A",
      badgeLabel: isHighlightedNextDose
        ? "Liều tiếp theo"
        : comp.warnings.includes("LOW_STOCK")
        ? "Sắp hết"
        : "Sắp hết hạn",
      badgeVariant: "warning",
      isHighlightedNextDose,
      isSelected,
    };
  }

  if (comp.medication) {
    return {
      colorHex: isSelected ? "#2E9C95" : "#6BC5B8",
      badgeLabel: "Có thuốc",
      badgeVariant: "primary",
      isHighlightedNextDose,
      isSelected,
    };
  }

  return {
    colorHex: isSelected ? "#2E9C95" : "#DCECEC",
    badgeLabel: "Ngăn trống",
    badgeVariant: "neutral",
    isHighlightedNextDose,
    isSelected,
  };
}

