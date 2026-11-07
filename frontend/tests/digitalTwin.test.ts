import { describe, expect, it, beforeEach } from "vitest";
import {
  dosageFormToPlaceholderType,
  objectIdToPosition,
  positionToObjectId,
  DigitalTwinSummaryResponse,
} from "../src/features/digitalTwin/types";
import { useDigitalTwinStore } from "../src/features/digitalTwin/store";
import {
  selectCompartmentVisualStatus,
  selectNextDoseCompartment,
  selectSelectedCompartment,
} from "../src/features/digitalTwin/selectors";
import { computeDrawerTargetZ } from "../src/pages/digital-twin/CompartmentMesh";
import { buildPharmaMindCabinetScene } from "../src/pages/digital-twin/CabinetModel";

function buildMockDigitalTwinSummary(): DigitalTwinSummaryResponse {
  return {
    cabinet: {
      id: 10,
      name: "Tủ thuốc Phòng khách",
      device_code: "PM-CAB-001",
      status: "ONLINE",
      hardware_mode: "SIMULATOR",
      last_seen_at: "2026-11-01T08:00:00Z",
    },
    next_dose_position: 1,
    next_dose: {
      schedule_id: 101,
      date: "2026-11-01",
      time: "20:00",
      member: { id: 1, full_name: "Nguyễn Thị Lan" },
      dose_amount: 1,
      dose_unit: "TABLET",
    },
    compartments: Array.from({ length: 6 }, (_, idx) => {
      const pos = idx + 1;
      if (pos === 1) {
        return {
          id: 1,
          position: 1,
          object_id: "drawer_01",
          label: "Ngăn 1",
          status: "AVAILABLE",
          is_open: false,
          medication: {
            id: 501,
            catalog_id: 301,
            name: "Paracetamol",
            strength: "500mg",
            dosage_form: "TABLET",
            quantity: 12,
            unit: "TABLET",
            expiration_date: "2028-06-30",
            status: "ACTIVE",
          },
          members: [
            {
              id: 1,
              full_name: "Nguyễn Thị Lan",
              relationship_label: "Mẹ",
              schedules: [
                {
                  schedule_id: 101,
                  recurrence_type: "DAILY",
                  times: ["08:00", "20:00"],
                  dose_amount: 1,
                  dose_unit: "TABLET",
                },
              ],
              next_schedule: "20:00",
            },
          ],
          next_dose: {
            schedule_id: 101,
            date: "2026-11-01",
            time: "20:00",
            member: { id: 1, full_name: "Nguyễn Thị Lan" },
            dose_amount: 1,
            dose_unit: "TABLET",
          },
          warnings: [],
          allergy_alerts: [],
        };
      }
      if (pos === 6) {
        return {
          id: 6,
          position: 6,
          object_id: "drawer_06",
          label: "Ngăn 6",
          status: "AVAILABLE",
          is_open: false,
          medication: {
            id: 502,
            catalog_id: 302,
            name: "Amoxicillin",
            strength: "500mg",
            dosage_form: "CAPSULE",
            quantity: 18,
            unit: "CAPSULE",
            expiration_date: "2028-10-30",
            status: "ACTIVE",
          },
          members: [
            {
              id: 1,
              full_name: "Nguyễn Thị Lan",
              relationship_label: "Mẹ",
              schedules: [],
              next_schedule: null,
            },
          ],
          next_dose: null,
          warnings: ["ALLERGY_RISK"],
          allergy_alerts: [
            {
              member_id: 1,
              member_name: "Nguyễn Thị Lan",
              alert_type: "ALLERGY",
              substance: "Amoxicillin",
              severity: "SEVERE",
              message: "Thành viên Nguyễn Thị Lan có tiền sử dị ứng với Amoxicillin.",
            },
          ],
        };
      }
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
    }),
  };
}

describe("Task 10 — Digital Twin 3D Unit & Integration Tests", () => {
  beforeEach(() => {
    useDigitalTwinStore.getState().reset();
  });

  it("Test Case 1 (§68): maps physical boxes 1..6 accurately", () => {
    for (let pos = 1; pos <= 6; pos++) {
      const objId = positionToObjectId(pos);
      expect(objId).toBe(`drawer_0${pos}`);
      expect(objectIdToPosition(objId)).toBe(pos);
    }
    expect(objectIdToPosition("invalid_node")).toBeNull();
    expect(dosageFormToPlaceholderType("TABLET")).toBe("TABLET");
    expect(dosageFormToPlaceholderType("CAPSULE")).toBe("CAPSULE");
    expect(dosageFormToPlaceholderType("SYRUP")).toBe("BOTTLE");
    expect(dosageFormToPlaceholderType("SACHET")).toBe("BLISTER");
  });

  it("Test Case 2 (§69): selects compartment 6 and returns its medication, member, and allergy alert details", () => {
    const store = useDigitalTwinStore.getState();
    store.setDigitalTwinData(buildMockDigitalTwinSummary());
    store.selectCompartment(6);

    const updated = useDigitalTwinStore.getState();
    const selected = selectSelectedCompartment(updated);
    expect(selected).not.toBeNull();
    expect(selected?.position).toBe(6);
    expect(selected?.object_id).toBe("drawer_06");
    expect(selected?.medication?.name).toBe("Amoxicillin");
    expect(selected?.allergy_alerts).toHaveLength(1);
    expect(selected?.allergy_alerts[0].substance).toBe("Amoxicillin");
  });

  it("Test Case 3 (§70): handles realtime COMPARTMENT_OPEN and COMPARTMENT_CLOSE events and translates drawer along Z-axis", () => {
    const store = useDigitalTwinStore.getState();
    store.setDigitalTwinData(buildMockDigitalTwinSummary());

    const baseZ = 0.07;
    expect(computeDrawerTargetZ(baseZ, false)).toBeCloseTo(0.07);

    store.applyRealtimeEvent({
      event_type: "COMPARTMENT_OPEN",
      family_id: 1,
      cabinet_id: 10,
      occurred_at: "2026-11-01T09:00:00Z",
      payload: { position: 6, is_open: true },
    });

    let comp8 = useDigitalTwinStore
      .getState()
      .compartments.find((c) => c.position === 6);
    expect(comp8?.is_open).toBe(true);
    expect(comp8?.status).toBe("OPEN");
    expect(computeDrawerTargetZ(baseZ, true)).toBeGreaterThan(baseZ);

    store.applyRealtimeEvent({
      event_type: "COMPARTMENT_CLOSE",
      family_id: 1,
      cabinet_id: 10,
      occurred_at: "2026-11-01T09:01:00Z",
      payload: { position: 6, is_open: false },
    });

    comp8 = useDigitalTwinStore
      .getState()
      .compartments.find((c) => c.position === 6);
    expect(comp8?.is_open).toBe(false);
    expect(comp8?.status).toBe("AVAILABLE");
  });

  it("Test Case 4 (§71): highlights the compartment with the next dose", () => {
    const store = useDigitalTwinStore.getState();
    store.setDigitalTwinData(buildMockDigitalTwinSummary());

    const state = useDigitalTwinStore.getState();
    const nextComp = selectNextDoseCompartment(state);
    expect(nextComp?.position).toBe(1);

    const vis = selectCompartmentVisualStatus(
      nextComp!,
      state.selectedPosition,
      state.nextDosePosition,
      state.cabinet?.status
    );
    expect(vis.isHighlightedNextDose).toBe(true);
    expect(vis.badgeLabel).toBe("Liều tiếp theo");
    expect(vis.colorHex).toBe("#E6A83A");
  });

  it("Test Case 5 (§72): transitions cabinet to OFFLINE on CABINET_OFFLINE event", () => {
    const store = useDigitalTwinStore.getState();
    store.setDigitalTwinData(buildMockDigitalTwinSummary());

    store.applyRealtimeEvent({
      event_type: "CABINET_OFFLINE",
      family_id: 1,
      cabinet_id: 10,
      occurred_at: "2026-11-01T09:05:00Z",
      payload: { status: "OFFLINE" },
    });

    const state = useDigitalTwinStore.getState();
    expect(state.cabinet?.status).toBe("OFFLINE");

    const vis = selectCompartmentVisualStatus(
      state.compartments[0],
      1,
      1,
      state.cabinet?.status
    );
    expect(vis.badgeLabel).toBe("Tủ mất kết nối");
    expect(vis.colorHex).toBe("#8FA3A8");
  });

  it("Test Case 6 (§73): renders empty compartment state cleanly when medication is null", () => {
    const store = useDigitalTwinStore.getState();
    store.setDigitalTwinData(buildMockDigitalTwinSummary());
    store.selectCompartment(3);

    const state = useDigitalTwinStore.getState();
    const comp3 = selectSelectedCompartment(state);
    expect(comp3?.medication).toBeNull();

    const vis = selectCompartmentVisualStatus(
      comp3!,
      3,
      state.nextDosePosition,
      state.cabinet?.status
    );
    expect(vis.badgeLabel).toBe("Ngăn trống");
  });

  it("Test Case 7: builds 3D scene graph with six drawers", () => {
    const graph = buildPharmaMindCabinetScene();
    expect(graph.root.getObjectByName("cabinet_body")).toBeDefined();
    expect(graph.root.getObjectByName("top_screen")).toBeDefined();
    expect(graph.root.getObjectByName("handle")).toBeDefined();
    for (let pos = 1; pos <= 6; pos++) {
      const nodeName = positionToObjectId(pos);
      expect(graph.root.getObjectByName(nodeName)).toBeDefined();
      expect(graph.drawers.get(pos)?.objectId).toBe(nodeName);
    }
    expect(graph.drawers.size).toBe(6);
    expect(graph.root.getObjectByName("drawer_07")).toBeUndefined();
  });

  it("applies Pi sensor data over cached backend state and resynchronizes after reconnect", () => {
    const store = useDigitalTwinStore.getState();
    store.setDigitalTwinData(buildMockDigitalTwinSummary());
    const closed = Object.fromEntries(Array.from({ length: 6 }, (_, i) => [
      String(i + 1), { status: "CLOSED" as const, led_state: "OFF" as const },
    ]));
    store.applyHardwareState({ connected: true, boxes: closed });
    store.applyHardwareState({ connected: true, boxes: {
      ...closed, "2": { status: "OPEN", led_state: "ON" },
    } });
    expect(useDigitalTwinStore.getState().compartments[1].is_open).toBe(true);
    expect(useDigitalTwinStore.getState().compartments[1].led_state).toBe("ON");
    store.setDigitalTwinData(buildMockDigitalTwinSummary());
    expect(useDigitalTwinStore.getState().compartments[1].is_open).toBe(true);
    store.applyHardwareState({ connected: false, boxes: null });
    store.applyHardwareState({ connected: true, boxes: closed });
    expect(useDigitalTwinStore.getState().compartments[1].is_open).toBe(false);
  });
});

