import { describe, expect, it, beforeEach } from "vitest";
import {
  buildRevealDataFromCompartment,
  DrawerRevealData,
} from "../src/features/cabinet/reveal/types";
import {
  clearRevealEventLog,
  computeCapsuleFlyoutTransform,
  getRevealEventLog,
} from "../src/features/cabinet/reveal/animation";
import {
  formatExpirationMonthYear,
  formatMedicationUnitVi,
  formatMemberScheduleLabelVi,
  selectPrioritizedMembers,
  selectRevealContextEmphasis,
  selectSafetyWarnings,
  selectShouldShowCapsule,
} from "../src/features/cabinet/reveal/selectors";
import { useDrawerRevealStore } from "../src/features/cabinet/reveal/hooks";
import {
  createReusable3DCapsuleFlyout,
  update3DCapsuleFlyout,
} from "../src/components/cabinet/CapsuleFlyout";

function makeSampleRevealData(
  overrides: Partial<DrawerRevealData> = {}
): DrawerRevealData {
  return {
    cabinet_id: 1,
    cabinet_status: "ONLINE",
    position: 8,
    object_id: "drawer_08",
    label: "Ngăn 8",
    status: "OPEN",
    is_open: true,
    is_next_dose: true,
    medication: {
      id: 10,
      catalog_id: 100,
      name: "Amlodipine",
      active_ingredient: "Amlodipine",
      strength: "5 mg",
      dosage_form: "TABLET",
      quantity: 20,
      unit: "TABLET",
      expiration_date: "2027-05-31",
      status: "ACTIVE",
    },
    members: [
      {
        id: 3,
        full_name: "Bà Lan",
        relationship_label: "Bà",
        dose_amount: 1,
        dose_unit: "TABLET",
        next_schedule: "2026-11-01T20:00:00+07:00",
        next_date: "2026-11-01",
        next_time: "20:00",
        times: ["08:00", "20:00"],
        instructions: "Uống sau ăn",
      },
    ],
    next_dose: {
      schedule_id: 55,
      date: "2026-11-01",
      time: "20:00",
      member: { id: 3, full_name: "Bà Lan" },
      dose_amount: 1,
      dose_unit: "TABLET",
    },
    warnings: [],
    ...overrides,
  };
}

describe("FEATURE — Drawer Open Capsule Fly-out & Medication Info Reveal (§43)", () => {
  beforeEach(() => {
    clearRevealEventLog();
    useDrawerRevealStore.getState().closeReveal();
  });

  it("43.1 Happy path: opens drawer with medication, member & schedule, plays capsule fly-out and logs events", () => {
    const data = makeSampleRevealData();
    useDrawerRevealStore.getState().openReveal({
      position: 8,
      openedBy: "USER",
      animationMode: "FULL",
      initialData: data,
    });

    const state = useDrawerRevealStore.getState();
    expect(state.isPanelOpen).toBe(true);
    expect(state.isAnimating).toBe(true);
    expect(selectShouldShowCapsule(state.revealData, state.isPanelOpen)).toBe(
      true
    );

    // Verify 3D capsule fly-out trajectory moves forward on Z
    const startTf = computeCapsuleFlyoutTransform({
      drawerX: 0,
      drawerY: -0.47,
      drawerZ: 0.33,
      progress: 0,
      elapsedSeconds: 0,
      animationMode: "FULL",
    });
    const endTf = computeCapsuleFlyoutTransform({
      drawerX: 0,
      drawerY: -0.47,
      drawerZ: 0.33,
      progress: 1,
      elapsedSeconds: 1.0,
      animationMode: "FULL",
    });
    expect(endTf.z).toBeGreaterThan(startTf.z + 0.3);
    expect(endTf.y).toBeGreaterThan(startTf.y + 0.35);
    expect(endTf.z).toBeGreaterThan(0.33 + 0.195); // capsule clears the open drawer face
    expect(endTf.opacity).toBeCloseTo(1);

    // Formatting checks (§12)
    expect(formatMedicationUnitVi("TABLET")).toBe("viên");
    expect(formatExpirationMonthYear("2027-05-31")).toBe("05/2027");
    expect(
      formatMemberScheduleLabelVi(data.members[0], "2026-11-01")
    ).toBe("20:00 hôm nay");

    const events = getRevealEventLog().map((e) => e.event);
    expect(events).toContain("drawer_reveal_opened");
    expect(events).toContain("capsule_animation_played");
  });

  it("43.2 Empty compartment: does NOT show capsule fly-out when medication is null", () => {
    const emptyData = makeSampleRevealData({
      medication: null,
      members: [],
      status: "EMPTY",
    });
    useDrawerRevealStore.getState().openReveal({
      position: 2,
      openedBy: "USER",
      animationMode: "FULL",
      initialData: emptyData,
    });

    const state = useDrawerRevealStore.getState();
    expect(selectShouldShowCapsule(state.revealData, state.isPanelOpen)).toBe(
      false
    );
    expect(state.isAnimating).toBe(false);
  });

  it("43.3 Multiple members: prioritizes the member with the earliest upcoming schedule first (§13)", () => {
    const multiMemberData = makeSampleRevealData({
      members: [
        {
          id: 2,
          full_name: "Ông Minh",
          relationship_label: "Ông",
          dose_amount: 1,
          dose_unit: "TABLET",
          next_time: "20:00",
          times: ["20:00"],
        },
        {
          id: 1,
          full_name: "Bà Lan",
          relationship_label: "Bà",
          dose_amount: 1,
          dose_unit: "TABLET",
          next_time: "08:00",
          times: ["08:00"],
        },
      ],
    });

    const prioritized = selectPrioritizedMembers(multiMemberData);
    expect(prioritized).toHaveLength(2);
    expect(prioritized[0].full_name).toBe("Bà Lan");
    expect(prioritized[0].next_time).toBe("08:00");
    expect(prioritized[1].full_name).toBe("Ông Minh");
  });

  it("43.4 Warning present: extracts allergy/drug reaction warnings with supportive wording and logs warning_panel_viewed", () => {
    const warnData = makeSampleRevealData({
      warnings: [
        {
          type: "ALLERGY_WARNING",
          severity: "SEVERE",
          member_id: 3,
          member_name: "Bà Lan",
          substance: "Amoxicillin",
          message:
            "⚠ Thành viên Bà Lan có tiền sử dị ứng với Amoxicillin. Vui lòng kiểm tra trước khi dùng thuốc.",
        },
      ],
    });

    useDrawerRevealStore.getState().openReveal({
      position: 8,
      openedBy: "USER",
      animationMode: "FULL",
      initialData: warnData,
    });

    const warnings = selectSafetyWarnings(
      useDrawerRevealStore.getState().revealData
    );
    expect(warnings).toHaveLength(1);
    expect(warnings[0].type).toBe("ALLERGY_WARNING");
    expect(warnings[0].message).toContain("Bà Lan");

    const events = getRevealEventLog().map((e) => e.event);
    expect(events).toContain("warning_panel_viewed");
  });

  it("43.5 Reduced motion: disables continuous bobbing and arc lift while preserving reveal clarity (§19)", () => {
    const tf1 = computeCapsuleFlyoutTransform({
      drawerX: 0.39,
      drawerY: 0.27,
      drawerZ: 0.07,
      progress: 1,
      elapsedSeconds: 1.0,
      animationMode: "REDUCED",
    });
    const tf2 = computeCapsuleFlyoutTransform({
      drawerX: 0.39,
      drawerY: 0.27,
      drawerZ: 0.07,
      progress: 1,
      elapsedSeconds: 3.5,
      animationMode: "REDUCED",
    });

    // Position and rotation stay steady in REDUCED motion mode
    expect(tf1.y).toBeCloseTo(tf2.y);
    expect(tf1.rotationY).toBeCloseTo(tf2.rotationY);
    expect(tf1.opacity).toBeCloseTo(1);
  });

  it("43.6 Offline cabinet: shows offline context emphasis and prevents false open animation when drawer is closed (§24)", () => {
    const offlineData = makeSampleRevealData({
      cabinet_status: "OFFLINE",
      is_open: false,
    });

    useDrawerRevealStore.getState().openReveal({
      position: 8,
      openedBy: "USER",
      animationMode: "FULL",
      initialData: offlineData,
    });

    const state = useDrawerRevealStore.getState();
    expect(selectShouldShowCapsule(state.revealData, state.isPanelOpen)).toBe(
      false
    );
    const emphasis = selectRevealContextEmphasis(state);
    expect(emphasis.title).toBe("Chế độ xem ngoại tuyến");
  });

  it("43.7 Realtime open event: highlights 'Đến giờ uống thuốc' when opened by SYSTEM for next dose and updates reusable 3D capsule mesh", () => {
    const sysData = makeSampleRevealData({
      is_open: true,
      is_next_dose: true,
    });

    useDrawerRevealStore.getState().openReveal({
      position: 8,
      openedBy: "SYSTEM",
      animationMode: "FULL",
      initialData: sysData,
    });

    const state = useDrawerRevealStore.getState();
    const emphasis = selectRevealContextEmphasis(state);
    expect(emphasis.title).toContain("Đến giờ uống thuốc");

    // Verify reusable 3D capsule mesh updates visibility and position
    const flyout3D = createReusable3DCapsuleFlyout();
    expect(flyout3D.group.visible).toBe(false);

    update3DCapsuleFlyout(flyout3D, {
      shouldShow: true,
      drawerX: 0,
      drawerY: -0.47,
      drawerZ: 0.07,
      position: 8,
      elapsedSeconds: 0.5,
      animationMode: "FULL",
    });
    expect(flyout3D.group.visible).toBe(true);
    expect(flyout3D.activePosition).toBe(8);

    // Also verify buildRevealDataFromCompartment helper
    const built = buildRevealDataFromCompartment(
      {
        id: 8,
        position: 8,
        object_id: "drawer_08",
        label: "Ngăn 8",
        status: "OPEN",
        is_open: true,
        medication: sysData.medication,
        members: [],
        next_dose: sysData.next_dose,
        warnings: ["LOW_STOCK"],
        allergy_alerts: [],
      },
      1,
      "ONLINE",
      8
    );
    expect(built.is_next_dose).toBe(true);
    expect(built.warnings.some((w) => w.type === "LOW_STOCK_WARNING")).toBe(
      true
    );
  });
});

