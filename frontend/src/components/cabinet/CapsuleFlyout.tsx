import React from "react";
import * as THREE from "three";
import { AnimationMode } from "../../features/cabinet/reveal/types";
import { computeCapsuleFlyoutTransform } from "../../features/cabinet/reveal/animation";
import { CapsulePopout } from "./CapsulePopout";

export interface Reusable3DCapsuleFlyout {
  group: THREE.Group;
  capMat: THREE.MeshStandardMaterial;
  bodyMat: THREE.MeshStandardMaterial;
  ringMat: THREE.MeshStandardMaterial;
  haloMat: THREE.MeshBasicMaterial;
  currentProgress: number;
  activePosition: number | null;
}

/**
 * Creates a single reusable 3D two-tone capsule object (§9, §33, §39)
 * that flies out from whichever compartment is opened.
 */
export function createReusable3DCapsuleFlyout(): Reusable3DCapsuleFlyout {
  const group = new THREE.Group();
  group.name = "capsule_flyout_3d";
  group.visible = false;

  // Left half of capsule (Teal #2E9C95)
  const capGeo = new THREE.CylinderGeometry(0.052, 0.052, 0.095, 24);
  const capMat = new THREE.MeshStandardMaterial({
    color: 0x2e9c95,
    roughness: 0.18,
    metalness: 0.12,
    transparent: true,
    opacity: 1,
  });
  const capCyl = new THREE.Mesh(capGeo, capMat);
  capCyl.position.y = 0.048;

  const capDomeGeo = new THREE.SphereGeometry(
    0.052,
    24,
    16,
    0,
    Math.PI * 2,
    0,
    Math.PI / 2
  );
  const capDome = new THREE.Mesh(capDomeGeo, capMat);
  capDome.position.y = 0.095;

  // Right half of capsule (Warm White #FFFFFF)
  const bodyGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.095, 24);
  const bodyMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.22,
    metalness: 0.06,
    transparent: true,
    opacity: 1,
  });
  const bodyCyl = new THREE.Mesh(bodyGeo, bodyMat);
  bodyCyl.position.y = -0.048;

  const bodyDomeGeo = new THREE.SphereGeometry(
    0.05,
    24,
    16,
    0,
    Math.PI * 2,
    Math.PI / 2,
    Math.PI / 2
  );
  const bodyDome = new THREE.Mesh(bodyDomeGeo, bodyMat);
  bodyDome.position.y = -0.095;

  // Center gold accent band (#E6A83A)
  const ringGeo = new THREE.CylinderGeometry(0.0535, 0.0535, 0.016, 24);
  const ringMat = new THREE.MeshStandardMaterial({
    color: 0xe6a83a,
    roughness: 0.25,
    metalness: 0.35,
    transparent: true,
    opacity: 1,
  });
  const ringMesh = new THREE.Mesh(ringGeo, ringMat);

  // Subtle soft glow ring behind the capsule
  const haloGeo = new THREE.RingGeometry(0.085, 0.125, 32);
  const haloMat = new THREE.MeshBasicMaterial({
    color: 0x6bc5b8,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.32,
  });
  const haloMesh = new THREE.Mesh(haloGeo, haloMat);
  haloMesh.position.z = -0.04;

  const pillInner = new THREE.Group();
  pillInner.add(capCyl, capDome, bodyCyl, bodyDome, ringMesh);
  group.add(pillInner, haloMesh);

  return {
    group,
    capMat,
    bodyMat,
    ringMat,
    haloMat,
    currentProgress: 0,
    activePosition: null,
  };
}

/**
 * Updates the 3D capsule fly-out on every animation frame (§9, §17, §19).
 */
export function update3DCapsuleFlyout(
  flyout: Reusable3DCapsuleFlyout,
  params: {
    shouldShow: boolean;
    drawerX: number;
    drawerY: number;
    drawerZ: number;
    position: number | null;
    elapsedSeconds: number;
    animationMode: AnimationMode;
  }
): void {
  const {
    shouldShow,
    drawerX,
    drawerY,
    drawerZ,
    position,
    elapsedSeconds,
    animationMode,
  } = params;

  if (flyout.activePosition !== position) {
    flyout.activePosition = position;
    flyout.currentProgress = 0;
  }

  const targetProgress = shouldShow ? 1 : 0;
  const stepSpeed = animationMode === "REDUCED" ? 0.35 : 0.09;

  flyout.currentProgress = THREE.MathUtils.lerp(
    flyout.currentProgress,
    targetProgress,
    stepSpeed
  );

  if (flyout.currentProgress < 0.02 && !shouldShow) {
    flyout.group.visible = false;
    return;
  }

  flyout.group.visible = true;
  const tf = computeCapsuleFlyoutTransform({
    drawerX,
    drawerY,
    drawerZ,
    progress: flyout.currentProgress,
    elapsedSeconds,
    animationMode,
  });

  flyout.group.position.set(tf.x, tf.y, tf.z);
  flyout.group.scale.setScalar(tf.scale);
  flyout.group.rotation.set(0, tf.rotationY, tf.rotationZ);

  flyout.capMat.opacity = tf.opacity;
  flyout.bodyMat.opacity = tf.opacity;
  flyout.ringMat.opacity = tf.opacity;
  flyout.haloMat.opacity = tf.opacity * 0.35;
}

interface CapsuleFlyoutOverlayProps {
  visible: boolean;
  position: number | null;
  medicationName?: string | null;
  strength?: string | null;
  memberName?: string | null;
  nextTimeLabel?: string | null;
  animationMode?: AnimationMode;
}

/**
 * Floating HUD banner overlaid on the 3D Cabinet viewport when a drawer opens
 * and the capsule flies out, providing immediate clarity + 2D fallback (§9, §41).
 */
export const CapsuleFlyout: React.FC<CapsuleFlyoutOverlayProps> = ({
  visible,
  position,
  medicationName,
  strength,
  memberName,
  nextTimeLabel,
  animationMode = "FULL",
}) => {
  if (!visible || !position || !medicationName) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: 16,
        bottom: 16,
        right: 16,
        zIndex: 10,
        pointerEvents: "none",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          maxWidth: 480,
          width: "100%",
          pointerEvents: "auto",
        }}
      >
        <CapsulePopout
          visible={true}
          medicationName={`Ngăn ${position}: ${medicationName}`}
          strength={
            [
              strength,
              memberName ? `• ${memberName}` : null,
              nextTimeLabel ? `(${nextTimeLabel})` : null,
            ]
              .filter(Boolean)
              .join(" ")
          }
          animationMode={animationMode}
          size="md"
        />
      </div>
    </div>
  );
};

