import React from "react";
import {
  DrawerInfoPanel,
  DrawerInfoPanelProps,
} from "./DrawerInfoPanel";

/**
 * MedicationRevealCard wraps the capsule pop-out & structured medication reveal panel
 * for Simple Cabinet Mode and standalone reveal views (§16.2, §18, §32.2).
 */
export const MedicationRevealCard: React.FC<DrawerInfoPanelProps> = (props) => {
  return <DrawerInfoPanel {...props} />;
};

