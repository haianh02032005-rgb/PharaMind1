import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RotateCcw, ZoomIn, ZoomOut, Sparkles } from "lucide-react";
import { DigitalTwinCompartment } from "../../features/digitalTwin/types";
import { selectCompartmentVisualStatus } from "../../features/digitalTwin/selectors";
import { buildPharmaMindCabinetScene, CabinetSceneGraph } from "./CabinetModel";
import {
  computeDrawerTargetZ,
  syncCompartmentMeshVisuals,
} from "./CompartmentMesh";
import {
  CapsuleFlyout,
  createReusable3DCapsuleFlyout,
  update3DCapsuleFlyout,
} from "../../components/cabinet/CapsuleFlyout";
import { useUiStore } from "../../store/uiStore";

interface CabinetCanvasProps {
  compartments: DigitalTwinCompartment[];
  selectedPosition: number | null;
  hoveredPosition: number | null;
  nextDosePosition: number | null;
  cabinetStatus?: string;
  onSelectCompartment: (position: number) => void;
  onHoverCompartment: (position: number | null) => void;
}

const DEFAULT_CAM_POS = new THREE.Vector3(0, 0.18, 2.55);

export const CabinetCanvas: React.FC<CabinetCanvasProps> = ({
  compartments,
  selectedPosition,
  hoveredPosition,
  nextDosePosition,
  cabinetStatus,
  onSelectCompartment,
  onHoverCompartment,
}) => {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const sceneGraphRef = useRef<CabinetSceneGraph | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const [webglReady, setWebglReady] = useState(true);
  const [glbVerified, setGlbVerified] = useState(true);
  const { reducedMotion, elderlyMode } = useUiStore();
  const animationMode = reducedMotion || elderlyMode ? "REDUCED" : "FULL";

  // Keep latest props in a ref for the animation loop & raycaster
  const latestPropsRef = useRef({
    compartments,
    selectedPosition,
    hoveredPosition,
    nextDosePosition,
    cabinetStatus,
    reducedMotion,
    onSelectCompartment,
    onHoverCompartment,
  });
  latestPropsRef.current = {
    compartments,
    selectedPosition,
    hoveredPosition,
    nextDosePosition,
    cabinetStatus,
    reducedMotion,
    onSelectCompartment,
    onHoverCompartment,
  };

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(
        container.clientWidth || 640,
        container.clientHeight || 500
      );
      renderer.shadowMap.enabled = true;
    } catch {
      setWebglReady(false);
      return;
    }

    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf1f8f7);

    const camera = new THREE.PerspectiveCamera(
      40,
      (container.clientWidth || 640) / (container.clientHeight || 500),
      0.1,
      25
    );
    camera.position.copy(DEFAULT_CAM_POS);
    cameraRef.current = camera;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 1.65;
    controls.maxDistance = 4.2;
    controls.minPolarAngle = Math.PI * 0.22;
    controls.maxPolarAngle = Math.PI * 0.68;
    controls.minAzimuthAngle = -Math.PI * 0.38;
    controls.maxAzimuthAngle = Math.PI * 0.38;
    controlsRef.current = controls;

    // Studio Healthcare Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.15);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.35);
    dirLight.position.set(2.4, 3.6, 3.2);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const fillLight = new THREE.DirectionalLight(0xddf4f1, 0.75);
    fillLight.position.set(-2.5, 1.2, 2.0);
    scene.add(fillLight);

    // Subtle circular pedestal under cabinet
    const floorGeo = new THREE.CylinderGeometry(1.05, 1.15, 0.04, 48);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0xe1f0ee,
      roughness: 0.6,
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.position.set(0, -0.84, -0.04);
    scene.add(floor);

    // Build PharmaMind 3D Cabinet
    const cabinetGraph = buildPharmaMindCabinetScene((loaded) => {
      setGlbVerified(loaded);
    });
    sceneGraphRef.current = cabinetGraph;
    scene.add(cabinetGraph.root);

    // Reusable 3D Capsule Fly-out object (§9, §17, §39)
    const capsuleFlyout3D = createReusable3DCapsuleFlyout();
    scene.add(capsuleFlyout3D.group);

    // Raycasting for hover & click
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let pointerDownPos = { x: 0, y: 0 };

    const getHitPosition = (clientX: number, clientY: number): number | null => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(
        cabinetGraph.interactiveMeshes,
        true
      );
      if (hits.length > 0) {
        const pos = hits[0].object.userData?.position;
        if (typeof pos === "number") return pos;
      }
      return null;
    };

    const handlePointerMove = (e: PointerEvent) => {
      const hitPos = getHitPosition(e.clientX, e.clientY);
      renderer.domElement.style.cursor = hitPos ? "pointer" : "grab";
      if (hitPos !== latestPropsRef.current.hoveredPosition) {
        latestPropsRef.current.onHoverCompartment(hitPos);
      }
    };

    const handlePointerDown = (e: PointerEvent) => {
      pointerDownPos = { x: e.clientX, y: e.clientY };
    };

    const handlePointerUp = (e: PointerEvent) => {
      const dx = Math.abs(e.clientX - pointerDownPos.x);
      const dy = Math.abs(e.clientY - pointerDownPos.y);
      if (dx < 6 && dy < 6) {
        const hitPos = getHitPosition(e.clientX, e.clientY);
        if (hitPos) {
          latestPropsRef.current.onSelectCompartment(hitPos);
        }
      }
    };

    renderer.domElement.addEventListener("pointermove", handlePointerMove);
    renderer.domElement.addEventListener("pointerdown", handlePointerDown);
    renderer.domElement.addEventListener("pointerup", handlePointerUp);

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 640;
      const h = container.clientHeight || 500;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Animation loop
    const clock = new THREE.Clock();
    let frameId = 0;

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      const {
        compartments: comps,
        selectedPosition: selPos,
        hoveredPosition: hovPos,
        nextDosePosition: nextPos,
        cabinetStatus: cabStat,
        reducedMotion: noMotion,
      } = latestPropsRef.current;

      for (const comp of comps) {
        const node = cabinetGraph.drawers.get(comp.position);
        if (!node) continue;
        const targetZ = computeDrawerTargetZ(node.baseZ, comp.is_open);
        if (noMotion) {
          node.group.position.z = targetZ;
        } else {
          node.group.position.z = THREE.MathUtils.lerp(
            node.group.position.z,
            targetZ,
            0.14
          );
        }
        syncCompartmentMeshVisuals(
          node,
          comp,
          selPos,
          hovPos,
          nextPos,
          cabStat,
          elapsed
        );
      }

      // Update 3D Capsule Fly-out for the active open compartment with medication
      const activeOpenComp =
        comps.find(
          (c) => c.position === selPos && c.is_open && c.medication !== null
        ) ||
        comps.find((c) => c.is_open && c.medication !== null) ||
        null;

      if (activeOpenComp && cabStat !== "OFFLINE") {
        const openNode = cabinetGraph.drawers.get(activeOpenComp.position);
        if (openNode) {
          update3DCapsuleFlyout(capsuleFlyout3D, {
            shouldShow: true,
            drawerX: openNode.group.position.x,
            drawerY: openNode.group.position.y,
            // Use the current open drawer depth, not the closed base depth. This
            // keeps the capsule in front of the moving drawer face as it rises.
            drawerZ: openNode.group.position.z,
            position: activeOpenComp.position,
            elapsedSeconds: elapsed,
            animationMode: noMotion ? "REDUCED" : "FULL",
          });
        }
      } else {
        update3DCapsuleFlyout(capsuleFlyout3D, {
          shouldShow: false,
          drawerX: 0,
          drawerY: 0,
          drawerZ: 0.07,
          position: null,
          elapsedSeconds: elapsed,
          animationMode: noMotion ? "REDUCED" : "FULL",
        });
      }

      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("pointermove", handlePointerMove);
      renderer.domElement.removeEventListener("pointerdown", handlePointerDown);
      renderer.domElement.removeEventListener("pointerup", handlePointerUp);
      controls.dispose();
      renderer.dispose();
    };
  }, []);

  const handleResetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.copy(DEFAULT_CAM_POS);
      controlsRef.current.target.set(0, 0, 0);
      controlsRef.current.update();
    }
  };

  const handleZoom = (factor: number) => {
    if (cameraRef.current) {
      cameraRef.current.position.multiplyScalar(factor);
      cameraRef.current.position.clampLength(1.65, 4.1);
    }
  };

  return (
    <div
      className="card"
      style={{
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 14,
      }}
    >
      {/* Top Camera & Legend Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Sparkles size={18} style={{ color: "var(--pm-primary)" }} />
          <span style={{ fontWeight: 700 }}>
            Mô hình 3D Tủ thuốc Thông minh (9 Ngăn)
          </span>
          <span className="badge badge-primary" style={{ fontSize: "0.74rem" }}>
            {glbVerified ? "GLB 3D Verified" : "3D Procedural Mesh"}
          </span>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            className="btn btn-sm btn-outline"
            onClick={() => handleZoom(0.88)}
            title="Phóng to"
          >
            <ZoomIn size={15} />
          </button>
          <button
            type="button"
            className="btn btn-sm btn-outline"
            onClick={() => handleZoom(1.12)}
            title="Thu nhỏ"
          >
            <ZoomOut size={15} />
          </button>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={handleResetCamera}
          >
            <RotateCcw size={15} />
            Đặt lại góc nhìn
          </button>
        </div>
      </div>

      {/* 3D Canvas Viewport + Floating Capsule Flyout HUD */}
      <div style={{ position: "relative" }}>
        {webglReady ? (
          <div
            ref={mountRef}
            style={{
              width: "100%",
              height: 450,
              borderRadius: 16,
              overflow: "hidden",
              border: "1px solid var(--pm-border)",
              position: "relative",
              background: "linear-gradient(180deg, #eef8f6 0%, #ffffff 100%)",
            }}
          />
        ) : null}

        {(() => {
          const openRevealedComp =
            compartments.find(
              (c) =>
                c.position === selectedPosition &&
                c.is_open &&
                c.medication !== null
            ) ||
            compartments.find((c) => c.is_open && c.medication !== null) ||
            null;
          if (!openRevealedComp || cabinetStatus === "OFFLINE") return null;
          const firstMember = openRevealedComp.members?.[0];
          return (
            <CapsuleFlyout
              visible={true}
              position={openRevealedComp.position}
              medicationName={openRevealedComp.medication?.name}
              strength={openRevealedComp.medication?.strength}
              memberName={
                openRevealedComp.next_dose?.member.full_name ||
                firstMember?.full_name
              }
              nextTimeLabel={
                openRevealedComp.next_dose?.time || firstMember?.next_schedule
              }
              animationMode={animationMode}
            />
          );
        })()}
      </div>

      {/* Quick Interactive 3x3 Compartment Selector Strip beneath 3D Canvas */}
      <div>
        <div
          style={{
            fontSize: "0.82rem",
            color: "var(--pm-text-secondary)",
            marginBottom: 8,
            display: "flex",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <span>
            Nhấp trực tiếp vào ngăn trên tủ 3D hoặc chọn nhanh ngăn bên dưới:
          </span>
          <span style={{ display: "flex", gap: 12 }}>
            <span>🟢 Đang mở</span>
            <span>🟠 Liều tiếp theo / Sắp hết</span>
            <span>🔴 Cảnh báo</span>
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 8,
          }}
        >
          {compartments.map((comp) => {
            const vis = selectCompartmentVisualStatus(
              comp,
              selectedPosition,
              nextDosePosition,
              cabinetStatus
            );
            return (
              <button
                key={comp.position}
                type="button"
                onClick={() => onSelectCompartment(comp.position)}
                style={{
                  textAlign: "left",
                  padding: "8px 12px",
                  borderRadius: 10,
                  border: vis.isSelected
                    ? "2px solid var(--pm-primary)"
                    : vis.isHighlightedNextDose
                    ? "2px solid var(--pm-warning)"
                    : "1px solid var(--pm-border)",
                  background: vis.isSelected
                    ? "var(--pm-primary-light)"
                    : "#ffffff",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 6,
                  fontFamily: "inherit",
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: "0.84rem",
                      color: "var(--pm-text-primary)",
                    }}
                  >
                    Ngăn {comp.position}{" "}
                    {comp.is_open ? "• ĐANG MỞ" : ""}
                  </div>
                  <div
                    style={{
                      fontSize: "0.78rem",
                      color: "var(--pm-text-secondary)",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {comp.medication ? comp.medication.name : "Ngăn trống"}
                  </div>
                </div>
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: vis.colorHex,
                    flexShrink: 0,
                  }}
                />
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

