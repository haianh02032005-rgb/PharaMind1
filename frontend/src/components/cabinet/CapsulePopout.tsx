import React from "react";
import { AnimationMode } from "../../features/cabinet/reveal/types";

interface CapsulePopoutProps {
  visible: boolean;
  medicationName?: string | null;
  strength?: string | null;
  animationMode?: AnimationMode;
  size?: "md" | "lg";
}

/**
 * 2D / SVG illustrative two-tone capsule pop-out component for Simple Mode
 * and the Medication Reveal Header (§9, §16.2, §18, §19, §41).
 */
export const CapsulePopout: React.FC<CapsulePopoutProps> = ({
  visible,
  medicationName,
  strength,
  animationMode = "FULL",
  size = "lg",
}) => {
  if (!visible || !medicationName) return null;

  const isReduced = animationMode === "REDUCED";
  const pillWidth = size === "lg" ? 92 : 68;
  const pillHeight = size === "lg" ? 40 : 30;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "12px 16px",
        borderRadius: 16,
        background: "linear-gradient(135deg, #e3f7f4 0%, #ffffff 100%)",
        border: "1.5px solid var(--pm-secondary)",
        boxShadow: "0 8px 22px rgba(46, 156, 149, 0.16)",
        animation: isReduced
          ? "fadeIn 180ms ease-out forwards"
          : "capsulePopoutAnim 520ms cubic-bezier(0.22, 1, 0.36, 1) forwards",
      }}
    >
      <style>
        {`
          @keyframes capsulePopoutAnim {
            0% {
              opacity: 0;
              transform: translateY(14px) scale(0.68);
            }
            70% {
              opacity: 1;
              transform: translateY(-3px) scale(1.04);
            }
            100% {
              opacity: 1;
              transform: translateY(0) scale(1);
            }
          }
          @keyframes capsuleFloatGentle {
            0%, 100% { transform: rotate(-16deg) translateY(0px); }
            50% { transform: rotate(-12deg) translateY(-4px); }
          }
        `}
      </style>

      {/* Two-tone 3D-shaded SVG Capsule */}
      <div
        aria-hidden="true"
        style={{
          width: pillWidth,
          height: pillHeight,
          borderRadius: 9999,
          display: "flex",
          overflow: "hidden",
          boxShadow:
            "0 6px 14px rgba(46, 156, 149, 0.28), inset 0 3px 6px rgba(255,255,255,0.65)",
          border: "1.5px solid rgba(23, 52, 58, 0.12)",
          flexShrink: 0,
          transform: "rotate(-14deg)",
          animation: isReduced
            ? "none"
            : "capsuleFloatGentle 2.8s ease-in-out infinite",
        }}
      >
        {/* Left Cap: PharmaMind Teal */}
        <div
          style={{
            width: "50%",
            height: "100%",
            background:
              "linear-gradient(180deg, #43b5ad 0%, #2e9c95 60%, #20756f 100%)",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 5,
              left: 8,
              right: 4,
              height: 6,
              borderRadius: 99,
              background: "rgba(255,255,255,0.45)",
            }}
          />
        </div>

        {/* Center Gold Ring */}
        <div
          style={{
            width: 4,
            height: "100%",
            background: "linear-gradient(180deg, #f8d486 0%, #e6a83a 100%)",
          }}
        />

        {/* Right Body: Warm Pearl White */}
        <div
          style={{
            flex: 1,
            height: "100%",
            background:
              "linear-gradient(180deg, #ffffff 0%, #f2f8f8 65%, #dcecec 100%)",
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 5,
              left: 4,
              right: 8,
              height: 6,
              borderRadius: 99,
              background: "rgba(255,255,255,0.8)",
            }}
          />
        </div>
      </div>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: "0.76rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.04em",
            color: "var(--pm-primary)",
          }}
        >
          Thuốc trong ngăn vừa mở
        </div>
        <div
          style={{
            fontSize: size === "lg" ? "1.18rem" : "1rem",
            fontWeight: 700,
            color: "var(--pm-text-primary)",
          }}
        >
          {medicationName} {strength ? `${strength}` : ""}
        </div>
      </div>
    </div>
  );
};

