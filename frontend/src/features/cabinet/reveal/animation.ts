import { AnimationMode } from "./types";

/**
 * Recommended capsule fly-out duration: 300–700 ms (§9.3).
 */
export const CAPSULE_FLYOUT_DURATION_MS = 520;
export const CAPSULE_REDUCED_DURATION_MS = 180;

export type RevealAnalyticsEventName =
  | "drawer_reveal_opened"
  | "drawer_reveal_closed"
  | "capsule_animation_played"
  | "drawer_reveal_failed"
  | "warning_panel_viewed";

export interface RevealAnalyticsEvent {
  event: RevealAnalyticsEventName;
  timestamp: string;
  payload?: Record<string, unknown>;
}

const revealEventLog: RevealAnalyticsEvent[] = [];

/**
 * Logs UI events for analytics & observability (§42).
 */
export function logRevealEvent(
  event: RevealAnalyticsEventName,
  payload?: Record<string, unknown>
): void {
  const entry: RevealAnalyticsEvent = {
    event,
    timestamp: new Date().toISOString(),
    payload,
  };
  revealEventLog.push(entry);
  if (revealEventLog.length > 100) {
    revealEventLog.shift();
  }
}

export function getRevealEventLog(): RevealAnalyticsEvent[] {
  return [...revealEventLog];
}

export function clearRevealEventLog(): void {
  revealEventLog.length = 0;
}

/**
 * Smooth cubic-out easing for natural, gentle capsule fly-out (§6.4, §9.2).
 */
export function easeOutCubic(t: number): number {
  const clamped = Math.max(0, Math.min(1, t));
  return 1 - Math.pow(1 - clamped, 3);
}

export interface Capsule3DTransform {
  x: number;
  y: number;
  z: number;
  scale: number;
  opacity: number;
  rotationY: number;
  rotationZ: number;
}

/**
 * Computes the 3D transform of the illustrative capsule flying out of a drawer (§9, §17, §19).
 *
 * - In `FULL` mode: spawns inside the open drawer, rises above the cabinet face (`+0.42m` on Y),
 *   and flies forward (`+0.46m` on Z) over ~520ms before hovering.
 *   over ~520ms, then hovers gently in front of the open drawer.
 * - In `REDUCED` mode: appears smoothly in front of the drawer without flying far or continuous bobbing (§19).
 */
export function computeCapsuleFlyoutTransform(params: {
  drawerX: number;
  drawerY: number;
  drawerZ: number;
  progress: number; // 0 (closed) .. 1 (open & revealed)
  elapsedSeconds: number;
  animationMode: AnimationMode;
}): Capsule3DTransform {
  const {
    drawerX,
    drawerY,
    drawerZ,
    progress,
    elapsedSeconds,
    animationMode,
  } = params;
  const eased = easeOutCubic(progress);

  if (animationMode === "REDUCED") {
    return {
      x: drawerX,
      y: drawerY + 0.4,
      z: drawerZ + 0.34,
      scale: eased > 0.05 ? 1 : 0.001,
      opacity: eased,
      rotationY: 0.25,
      rotationZ: Math.PI / 5,
    };
  }

  // Parabolic arc peaking halfway through fly-out + gentle floating once settled
  const arcLift = Math.sin(eased * Math.PI) * 0.08;
  const floatOffset =
    eased > 0.92 ? Math.sin(elapsedSeconds * 2.4) * 0.018 : 0;
  const gentleSpin =
    eased * 0.45 + (eased > 0.92 ? Math.sin(elapsedSeconds * 1.5) * 0.12 : 0);

  return {
    x: drawerX,
    y: drawerY + 0.42 * eased + arcLift + floatOffset,
    z: drawerZ + 0.1 + 0.36 * eased,
    scale: Math.max(0.001, 0.35 + 0.65 * eased),
    opacity: eased,
    rotationY: gentleSpin,
    rotationZ: Math.PI / 5,
  };
}

