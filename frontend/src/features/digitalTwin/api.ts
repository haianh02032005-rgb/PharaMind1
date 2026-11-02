import { apiRequest } from "../../services/apiClient";
import { DigitalTwinSummaryResponse } from "./types";

export const digitalTwinApi = {
  async getDigitalTwinSummary(
    familyId: number,
    cabinetId: number,
    memberId?: number | null
  ): Promise<DigitalTwinSummaryResponse> {
    const query = memberId ? `?member_id=${memberId}` : "";
    return apiRequest<DigitalTwinSummaryResponse>(
      `/families/${familyId}/cabinets/${cabinetId}/digital-twin${query}`
    );
  },

  async openCompartment(
    familyId: number,
    cabinetId: number,
    position: number
  ): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/compartments/${position}/open`,
      { method: "POST" }
    );
  },

  async closeCompartment(
    familyId: number,
    cabinetId: number,
    position: number
  ): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/compartments/${position}/close`,
      { method: "POST" }
    );
  },

  async setSimulatorOnline(familyId: number, cabinetId: number): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/simulator/online`,
      { method: "POST" }
    );
  },

  async setSimulatorOffline(
    familyId: number,
    cabinetId: number
  ): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/simulator/offline`,
      { method: "POST" }
    );
  },

  async syncCabinetState(familyId: number, cabinetId: number): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/simulator/sync`,
      { method: "POST" }
    );
  },

  async assignMedication(
    familyId: number,
    cabinetId: number,
    position: number,
    familyMedicationId: number
  ): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/compartments/${position}/medication`,
      {
        method: "PUT",
        body: JSON.stringify({ family_medication_id: familyMedicationId }),
      }
    );
  },

  async unassignMedication(
    familyId: number,
    cabinetId: number,
    position: number
  ): Promise<void> {
    await apiRequest(
      `/families/${familyId}/cabinets/${cabinetId}/compartments/${position}/medication`,
      { method: "DELETE" }
    );
  },
};

