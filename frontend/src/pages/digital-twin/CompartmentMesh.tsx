import * as THREE from "three";
import {
  DigitalTwinCompartment,
  dosageFormToPlaceholderType,
  positionToObjectId,
} from "../../features/digitalTwin/types";
import { selectCompartmentVisualStatus } from "../../features/digitalTwin/selectors";

export interface CompartmentMeshNode {
  position: number;
  objectId: string;
  group: THREE.Group;
  frontPanel: THREE.Mesh;
  frontMaterial: THREE.MeshStandardMaterial;
  ledBarMaterial: THREE.MeshStandardMaterial;
  medicationGroup: THREE.Group;
  baseZ: number;
}

/**
 * Computes the target Z offset for a drawer (`isOpen === true` translates forward by +0.26).
 */
export function computeDrawerTargetZ(
  baseZ: number,
  isOpen: boolean
): number {
  return isOpen ? baseZ + 0.26 : baseZ;
}

/**
 * Builds the 3D medication placeholder mesh inside a compartment drawer
 * according to the assigned medication's `dosage_form`.
 */
export function buildMedicationPlaceholderGroup(
  dosageForm?: string | null
): THREE.Group {
  const medGroup = new THREE.Group();
  medGroup.name = "medication_placeholder";
  const kind = dosageFormToPlaceholderType(dosageForm);

  if (kind === "TABLET") {
    // Blister pack + round white/mint tablets
    const trayGeo = new THREE.BoxGeometry(0.18, 0.014, 0.12);
    const trayMat = new THREE.MeshStandardMaterial({
      color: 0xdcecec,
      metalness: 0.35,
      roughness: 0.25,
    });
    const tray = new THREE.Mesh(trayGeo, trayMat);
    tray.position.set(0, -0.04, 0);
    medGroup.add(tray);

    const pillGeo = new THREE.CylinderGeometry(0.022, 0.022, 0.014, 20);
    const pillMat = new THREE.MeshStandardMaterial({
      color: 0x2e9c95,
      roughness: 0.25,
    });
    const offsets = [
      [-0.045, -0.028],
      [0, -0.028],
      [0.045, -0.028],
      [-0.045, 0.028],
      [0, 0.028],
      [0.045, 0.028],
    ];
    for (const [ox, oz] of offsets) {
      const pill = new THREE.Mesh(pillGeo, pillMat);
      pill.position.set(ox, -0.028, oz);
      medGroup.add(pill);
    }
  } else if (kind === "CAPSULE") {
    const capGeo = new THREE.CapsuleGeometry(0.022, 0.05, 8, 16);
    const capMat1 = new THREE.MeshStandardMaterial({
      color: 0x2e9c95,
      roughness: 0.2,
    });
    const capMat2 = new THREE.MeshStandardMaterial({
      color: 0xe6a83a,
      roughness: 0.25,
    });
    for (let i = -1; i <= 1; i++) {
      const mesh = new THREE.Mesh(capGeo, i % 2 === 0 ? capMat1 : capMat2);
      mesh.rotation.z = Math.PI / 2;
      mesh.rotation.y = i * 0.25;
      mesh.position.set(i * 0.055, -0.03, i * 0.02);
      medGroup.add(mesh);
    }
  } else if (kind === "BOTTLE") {
    const bodyGeo = new THREE.CylinderGeometry(0.048, 0.048, 0.13, 24);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: 0xd9822b,
      roughness: 0.2,
      metalness: 0.1,
    });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.set(0, -0.01, 0);
    medGroup.add(body);

    const capGeo = new THREE.CylinderGeometry(0.034, 0.034, 0.032, 20);
    const capMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.3,
    });
    const cap = new THREE.Mesh(capGeo, capMat);
    cap.position.set(0, 0.068, 0);
    medGroup.add(cap);
  } else {
    // BLISTER or BOX
    const boxGeo = new THREE.BoxGeometry(0.18, 0.09, 0.11);
    const boxMat = new THREE.MeshStandardMaterial({
      color: 0x2e9c95,
      roughness: 0.3,
    });
    const box = new THREE.Mesh(boxGeo, boxMat);
    box.position.set(0, -0.02, 0);
    medGroup.add(box);
  }

  return medGroup;
}

/**
 * Creates a single interactive 3D compartment drawer (`drawer_01`..`drawer_06`).
 */
export function createCompartmentMeshNode(
  position: number,
  colIndex: number,
  rowIndex: number
): CompartmentMeshNode {
  const objectId = positionToObjectId(position);
  const group = new THREE.Group();
  group.name = objectId;
  group.userData = { position, objectId };

  const xs = [-0.39, 0.0, 0.39];
  const ys = [0.17, -0.27];
  const baseZ = 0.07;

  group.position.set(xs[colIndex], ys[rowIndex], baseZ);

  // Drawer tray bin (translucent mint-white acrylic)
  const trayGeo = new THREE.BoxGeometry(0.33, 0.28, 0.38);
  const trayMat = new THREE.MeshStandardMaterial({
    color: 0xf4fbfa,
    roughness: 0.25,
    metalness: 0.05,
    transparent: true,
    opacity: 0.88,
  });
  const trayMesh = new THREE.Mesh(trayGeo, trayMat);
  trayMesh.userData = { position, objectId };
  group.add(trayMesh);

  // Front face panel with rounded aesthetic & status tint
  const frontGeo = new THREE.BoxGeometry(0.34, 0.3, 0.032);
  const frontMaterial = new THREE.MeshStandardMaterial({
    color: 0xddf4f1,
    roughness: 0.18,
    metalness: 0.08,
    transparent: true,
    opacity: 0.92,
  });
  const frontPanel = new THREE.Mesh(frontGeo, frontMaterial);
  frontPanel.position.set(0, 0, 0.195);
  frontPanel.userData = { position, objectId };
  group.add(frontPanel);

  // Top LED indicator bar on each drawer
  const ledGeo = new THREE.BoxGeometry(0.24, 0.022, 0.038);
  const ledBarMaterial = new THREE.MeshStandardMaterial({
    color: 0x2e9c95,
    emissive: 0x2e9c95,
    emissiveIntensity: 0.35,
    roughness: 0.2,
  });
  const ledBar = new THREE.Mesh(ledGeo, ledBarMaterial);
  ledBar.position.set(0, 0.11, 0.2);
  ledBar.userData = { position, objectId };
  group.add(ledBar);

  // Subtle drawer handle grip
  const gripGeo = new THREE.BoxGeometry(0.11, 0.026, 0.044);
  const gripMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.25,
    metalness: 0.1,
  });
  const grip = new THREE.Mesh(gripGeo, gripMat);
  grip.position.set(0, -0.02, 0.205);
  grip.userData = { position, objectId };
  group.add(grip);

  // Medication placeholder group inside the drawer
  const medicationGroup = new THREE.Group();
  medicationGroup.position.set(0, 0.01, 0.04);
  group.add(medicationGroup);

  return {
    position,
    objectId,
    group,
    frontPanel,
    frontMaterial,
    ledBarMaterial,
    medicationGroup,
    baseZ,
  };
}

/**
 * Updates visual material, LED glow, and 3D medication content of a CompartmentMeshNode.
 */
export function syncCompartmentMeshVisuals(
  node: CompartmentMeshNode,
  comp: DigitalTwinCompartment,
  selectedPosition: number | null,
  hoveredPosition: number | null,
  nextDosePosition: number | null,
  cabinetStatus?: string,
  elapsedTime = 0
): void {
  const visual = selectCompartmentVisualStatus(
    comp,
    selectedPosition,
    nextDosePosition,
    cabinetStatus
  );

  const isHovered = comp.position === hoveredPosition;
  const baseColor = new THREE.Color(visual.colorHex);

  // Front panel tint
  if (visual.isSelected) {
    node.frontMaterial.color.setHex(0xbbeae3);
    node.frontMaterial.emissive.setHex(0x2e9c95);
    node.frontMaterial.emissiveIntensity = 0.22;
  } else if (isHovered) {
    node.frontMaterial.color.setHex(0xd2f2ed);
    node.frontMaterial.emissive.setHex(0x2e9c95);
    node.frontMaterial.emissiveIntensity = 0.12;
  } else if (comp.medication) {
    node.frontMaterial.color.setHex(0xddf4f1);
    node.frontMaterial.emissive.setHex(0x000000);
    node.frontMaterial.emissiveIntensity = 0;
  } else {
    node.frontMaterial.color.setHex(0xf1f6f6);
    node.frontMaterial.emissive.setHex(0x000000);
    node.frontMaterial.emissiveIntensity = 0;
  }

  // LED indicator bar (pulse on next dose)
  const ledColor = comp.led_state === "ON"
    ? new THREE.Color(0x2fa66a)
    : comp.led_state === "OFF" ? new THREE.Color(0x456462) : baseColor;
  node.ledBarMaterial.color.copy(ledColor);
  node.ledBarMaterial.emissive.copy(ledColor);
  if (comp.led_state === "ON") {
    node.ledBarMaterial.emissiveIntensity = 0.9;
  } else if (comp.led_state === "OFF") {
    node.ledBarMaterial.emissiveIntensity = 0.02;
  } else if (visual.isHighlightedNextDose) {
    const pulse = 0.45 + 0.4 * Math.sin(elapsedTime * 5.0);
    node.ledBarMaterial.emissiveIntensity = pulse;
  } else if (comp.is_open || visual.isSelected) {
    node.ledBarMaterial.emissiveIntensity = 0.65;
  } else {
    node.ledBarMaterial.emissiveIntensity = 0.25;
  }

  // Rebuild medication 3D placeholder if dosage form changed
  const desiredKey = comp.medication
    ? `${comp.medication.id}:${comp.medication.dosage_form || "BOX"}`
    : "NONE";
  if (node.medicationGroup.userData.medKey !== desiredKey) {
    node.medicationGroup.clear();
    node.medicationGroup.userData.medKey = desiredKey;
    if (comp.medication) {
      const placeholder = buildMedicationPlaceholderGroup(
        comp.medication.dosage_form
      );
      node.medicationGroup.add(placeholder);
    }
  }
}

