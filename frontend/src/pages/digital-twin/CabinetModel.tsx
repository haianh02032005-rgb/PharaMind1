import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import {
  CompartmentMeshNode,
  createCompartmentMeshNode,
} from "./CompartmentMesh";

export interface CabinetSceneGraph {
  root: THREE.Group;
  drawers: Map<number, CompartmentMeshNode>;
  interactiveMeshes: THREE.Object3D[];
}

/**
 * Builds the complete PharmaMind 3D Smart Medicine Cabinet scene graph
 * (`cabinet_body`, `top_screen`, `handle`, and `drawer_01`..`drawer_09`),
 * and asynchronously validates `/models/pharmamind_cabinet.glb`.
 */
export function buildPharmaMindCabinetScene(
  onGlbStatus?: (loaded: boolean) => void
): CabinetSceneGraph {
  const root = new THREE.Group();
  root.name = "PharmaMindSmartCabinet";

  // 1. Outer white cabinet body (`cabinet_body`)
  const bodyGroup = new THREE.Group();
  bodyGroup.name = "cabinet_body";

  const outerShellGeo = new THREE.BoxGeometry(1.36, 1.58, 0.52);
  const outerShellMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.22,
    metalness: 0.05,
  });
  const outerShell = new THREE.Mesh(outerShellGeo, outerShellMat);
  outerShell.position.set(0, 0, -0.06);
  outerShell.castShadow = true;
  outerShell.receiveShadow = true;
  bodyGroup.add(outerShell);

  // Soft mint inner frame accent around the 3x3 grid
  const bezelGeo = new THREE.BoxGeometry(1.26, 1.22, 0.46);
  const bezelMat = new THREE.MeshStandardMaterial({
    color: 0xc8eee8,
    roughness: 0.28,
    metalness: 0.04,
  });
  const bezel = new THREE.Mesh(bezelGeo, bezelMat);
  bezel.position.set(0, -0.1, -0.02);
  bodyGroup.add(bezel);

  root.add(bodyGroup);

  // 2. Top horizontal smart screen (`top_screen`)
  const screenGroup = new THREE.Group();
  screenGroup.name = "top_screen";
  const screenGeo = new THREE.BoxGeometry(0.56, 0.15, 0.03);
  const screenMat = new THREE.MeshStandardMaterial({
    color: 0x132b30,
    emissive: 0x1d5c58,
    emissiveIntensity: 0.35,
    roughness: 0.15,
    metalness: 0.2,
  });
  const screenMesh = new THREE.Mesh(screenGeo, screenMat);
  screenMesh.position.set(0, 0.62, 0.21);
  screenGroup.add(screenMesh);
  root.add(screenGroup);

  // 3. Top ergonomic carrying handle (`handle`)
  const handleGroup = new THREE.Group();
  handleGroup.name = "handle";

  const topBarGeo = new THREE.BoxGeometry(0.42, 0.045, 0.08);
  const handleMat = new THREE.MeshStandardMaterial({
    color: 0xeaf6f5,
    roughness: 0.25,
    metalness: 0.15,
  });
  const topBar = new THREE.Mesh(topBarGeo, handleMat);
  topBar.position.set(0, 0.86, -0.04);
  handleGroup.add(topBar);

  const postGeo = new THREE.CylinderGeometry(0.024, 0.024, 0.09, 16);
  const leftPost = new THREE.Mesh(postGeo, handleMat);
  leftPost.position.set(-0.16, 0.81, -0.04);
  const rightPost = new THREE.Mesh(postGeo, handleMat);
  rightPost.position.set(0.16, 0.81, -0.04);
  handleGroup.add(leftPost, rightPost);

  root.add(handleGroup);

  // 4. Nine interactive compartments (`drawer_01`..`drawer_09`)
  const drawers = new Map<number, CompartmentMeshNode>();
  const interactiveMeshes: THREE.Object3D[] = [];

  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const position = row * 3 + col + 1;
      const node = createCompartmentMeshNode(position, col, row);
      drawers.set(position, node);
      root.add(node.group);
      node.group.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          child.userData = { position, objectId: node.objectId };
          interactiveMeshes.push(child);
        }
      });
    }
  }

  // Attempt to load `/models/pharmamind_cabinet.glb` to verify GLB asset integrity
  if (typeof window !== "undefined") {
    try {
      const loader = new GLTFLoader();
      loader.load(
        "/models/pharmamind_cabinet.glb",
        (gltf) => {
          const hasDrawers =
            gltf.scene.getObjectByName("drawer_01") !== undefined &&
            gltf.scene.getObjectByName("drawer_09") !== undefined;
          onGlbStatus?.(hasDrawers);
        },
        undefined,
        () => {
          onGlbStatus?.(false);
        }
      );
    } catch {
      onGlbStatus?.(false);
    }
  }

  return { root, drawers, interactiveMeshes };
}

