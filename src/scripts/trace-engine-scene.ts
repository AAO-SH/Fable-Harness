import { PerspectiveCamera } from "three/src/cameras/PerspectiveCamera.js";
import { DoubleSide, PCFShadowMap, SRGBColorSpace } from "three/src/constants.js";
import { CatmullRomCurve3 } from "three/src/extras/curves/CatmullRomCurve3.js";
import { Path } from "three/src/extras/core/Path.js";
import { Shape } from "three/src/extras/core/Shape.js";
import { BoxGeometry } from "three/src/geometries/BoxGeometry.js";
import { CircleGeometry } from "three/src/geometries/CircleGeometry.js";
import { CylinderGeometry } from "three/src/geometries/CylinderGeometry.js";
import { ExtrudeGeometry } from "three/src/geometries/ExtrudeGeometry.js";
import { PlaneGeometry } from "three/src/geometries/PlaneGeometry.js";
import { SphereGeometry } from "three/src/geometries/SphereGeometry.js";
import { TorusGeometry } from "three/src/geometries/TorusGeometry.js";
import { TubeGeometry } from "three/src/geometries/TubeGeometry.js";
import { AmbientLight } from "three/src/lights/AmbientLight.js";
import { DirectionalLight } from "three/src/lights/DirectionalLight.js";
import { PointLight } from "three/src/lights/PointLight.js";
import type { Material } from "three/src/materials/Material.js";
import { MeshBasicMaterial } from "three/src/materials/MeshBasicMaterial.js";
import { MeshPhysicalMaterial } from "three/src/materials/MeshPhysicalMaterial.js";
import { MeshStandardMaterial } from "three/src/materials/MeshStandardMaterial.js";
import { SpriteMaterial } from "three/src/materials/SpriteMaterial.js";
import { Vector3 } from "three/src/math/Vector3.js";
import { Group } from "three/src/objects/Group.js";
import { Mesh } from "three/src/objects/Mesh.js";
import { Sprite } from "three/src/objects/Sprite.js";
import { WebGLRenderer } from "three/src/renderers/WebGLRenderer.js";
import { Scene } from "three/src/scenes/Scene.js";
import { CanvasTexture } from "three/src/textures/CanvasTexture.js";
import type { Texture } from "three/src/textures/Texture.js";

const sceneRoots = [...document.querySelectorAll<HTMLElement>("[data-trace-engine-scene]")];
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

type AnimatedPart = {
  tick: (time: number) => void;
};

const isSceneDisabled = () => {
  try {
    return (
      window.localStorage.getItem("fable-disable-webgl") === "1" ||
      document.documentElement.dataset.traceEngine === "off"
    );
  } catch {
    return false;
  }
};

const setTextureColorSpace = (texture: Texture) => {
  texture.colorSpace = SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
};

const makeTexture = (width: number, height: number, paint: (context: CanvasRenderingContext2D) => void) => {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("CanvasTexture context unavailable");
  }

  paint(context);
  return setTextureColorSpace(new CanvasTexture(canvas));
};

const drawNoise = (context: CanvasRenderingContext2D, width: number, height: number, alpha = 0.08) => {
  const image = context.getImageData(0, 0, width, height);

  for (let index = 0; index < image.data.length; index += 4) {
    const value = 135 + Math.random() * 120;
    image.data[index] = value;
    image.data[index + 1] = value * 0.82;
    image.data[index + 2] = value * 0.52;
    image.data[index + 3] = Math.floor(255 * alpha * Math.random());
  }

  context.putImageData(image, 0, 0);
};

const makeParchmentTexture = () =>
  makeTexture(1024, 1024, (context) => {
    const gradient = context.createLinearGradient(0, 0, 1024, 1024);
    gradient.addColorStop(0, "#d6c09a");
    gradient.addColorStop(0.48, "#a88a5b");
    gradient.addColorStop(1, "#4b2f1a");
    context.fillStyle = gradient;
    context.fillRect(0, 0, 1024, 1024);
    drawNoise(context, 1024, 1024, 0.18);

    context.strokeStyle = "rgba(60, 42, 24, 0.2)";
    context.lineWidth = 1;
    for (let offset = 48; offset < 1024; offset += 72) {
      context.beginPath();
      context.moveTo(offset, 0);
      context.lineTo(offset + 44, 1024);
      context.stroke();
      context.beginPath();
      context.moveTo(0, offset);
      context.lineTo(1024, offset - 36);
      context.stroke();
    }

    context.strokeStyle = "rgba(42, 30, 20, 0.18)";
    for (let radius = 120; radius <= 460; radius += 88) {
      context.beginPath();
      context.arc(780, 210, radius, 0, Math.PI * 2);
      context.stroke();
    }
  });

const makeMetalTexture = (base: string, highlight: string) =>
  makeTexture(512, 512, (context) => {
    const gradient = context.createLinearGradient(0, 0, 512, 512);
    gradient.addColorStop(0, highlight);
    gradient.addColorStop(0.34, base);
    gradient.addColorStop(0.7, "#24130a");
    gradient.addColorStop(1, highlight);
    context.fillStyle = gradient;
    context.fillRect(0, 0, 512, 512);
    drawNoise(context, 512, 512, 0.11);

    context.strokeStyle = "rgba(255, 244, 198, 0.16)";
    context.lineWidth = 1;
    for (let y = 10; y < 512; y += 14) {
      context.beginPath();
      context.moveTo(0, y + Math.sin(y) * 6);
      context.lineTo(512, y + Math.cos(y * 0.4) * 8);
      context.stroke();
    }
  });

const makePaperTexture = (label: string, body: string) =>
  makeTexture(512, 288, (context) => {
    const gradient = context.createLinearGradient(0, 0, 512, 288);
    gradient.addColorStop(0, "#f4dc9f");
    gradient.addColorStop(0.65, "#d0ae6a");
    gradient.addColorStop(1, "#8c612e");
    context.fillStyle = gradient;
    context.fillRect(0, 0, 512, 288);
    drawNoise(context, 512, 288, 0.14);

    context.strokeStyle = "rgba(70, 40, 18, 0.22)";
    context.lineWidth = 2;
    for (let y = 84; y < 250; y += 34) {
      context.beginPath();
      context.moveTo(36, y);
      context.lineTo(476, y + Math.sin(y) * 2);
      context.stroke();
    }

    context.fillStyle = "#6c421c";
    context.font = "700 32px JetBrains Mono, monospace";
    context.fillText(label, 36, 52);
    context.fillStyle = "#1f1309";
    context.font = "800 28px JetBrains Mono, monospace";
    const lines = body.split("\n");
    lines.forEach((line, index) => context.fillText(line, 36, 112 + index * 36));

    context.strokeStyle = "rgba(65, 36, 14, 0.5)";
    context.lineWidth = 4;
    context.strokeRect(18, 18, 476, 252);
  });

const makeClockTexture = () =>
  makeTexture(512, 512, (context) => {
    context.clearRect(0, 0, 512, 512);
    const gradient = context.createRadialGradient(208, 160, 20, 256, 256, 240);
    gradient.addColorStop(0, "#f7deb0");
    gradient.addColorStop(0.42, "#b9823c");
    gradient.addColorStop(0.76, "#3c2212");
    gradient.addColorStop(1, "#110805");
    context.fillStyle = gradient;
    context.beginPath();
    context.arc(256, 256, 238, 0, Math.PI * 2);
    context.fill();
    drawNoise(context, 512, 512, 0.08);

    context.strokeStyle = "rgba(255, 239, 181, 0.72)";
    context.lineWidth = 9;
    context.beginPath();
    context.arc(256, 256, 212, 0, Math.PI * 2);
    context.stroke();

    context.strokeStyle = "rgba(30, 18, 10, 0.78)";
    context.lineWidth = 5;
    for (let tick = 0; tick < 60; tick++) {
      const angle = (tick / 60) * Math.PI * 2;
      const inner = tick % 5 === 0 ? 174 : 194;
      context.beginPath();
      context.moveTo(256 + Math.cos(angle) * inner, 256 + Math.sin(angle) * inner);
      context.lineTo(256 + Math.cos(angle) * 206, 256 + Math.sin(angle) * 206);
      context.stroke();
    }
  });

const makeLabelSprite = (text: string) => {
  const texture = makePaperTexture(text, "");
  const material = new SpriteMaterial({
    map: texture,
    transparent: true,
    opacity: 0.9,
    depthWrite: false,
  });
  const sprite = new Sprite(material);
  sprite.scale.set(0.72, 0.2, 1);
  return sprite;
};

const createGearGeometry = (rootRadius: number, tipRadius: number, holeRadius: number, teeth: number, depth: number) => {
  const shape = new Shape();
  const steps = teeth * 2;

  for (let index = 0; index <= steps; index++) {
    const radius = index % 2 === 0 ? tipRadius : rootRadius;
    const angle = (index / steps) * Math.PI * 2;
    const x = Math.cos(angle) * radius;
    const y = Math.sin(angle) * radius;

    if (index === 0) {
      shape.moveTo(x, y);
    } else {
      shape.lineTo(x, y);
    }
  }

  const hole = new Path();
  hole.absarc(0, 0, holeRadius, 0, Math.PI * 2, true);
  shape.holes.push(hole);

  const geometry = new ExtrudeGeometry(shape, {
    depth,
    bevelEnabled: true,
    bevelSegments: 2,
    bevelSize: depth * 0.18,
    bevelThickness: depth * 0.12,
  });
  geometry.center();
  return geometry;
};

const addSpokes = (group: Group, count: number, radius: number, material: Material) => {
  for (let index = 0; index < count; index++) {
    const spoke = new Mesh(new BoxGeometry(radius * 1.5, radius * 0.055, 0.045), material);
    spoke.rotation.z = (index / count) * Math.PI * 2;
    spoke.position.z = 0.05;
    group.add(spoke);
  }
};

const createPaperPlane = (label: string, body: string, width = 1.0) => {
  const texture = makePaperTexture(label, body);
  const material = new MeshStandardMaterial({
    map: texture,
    color: "#ffe2a0",
    roughness: 0.72,
    metalness: 0.02,
    transparent: true,
    side: DoubleSide,
  });
  const mesh = new Mesh(new PlaneGeometry(width, width * 0.56), material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
};

const initTraceEngineScene = (root: HTMLElement) => {
  const canvas = root.querySelector<HTMLCanvasElement>("[data-trace-engine-canvas]");

  if (!canvas) {
    return;
  }

  if (isSceneDisabled()) {
    root.setAttribute("data-render-state", "fallback");
    canvas.setAttribute("data-render-state", "fallback");
    return;
  }

  let frameId = 0;
  const animatedParts: AnimatedPart[] = [];
  const scene = new Scene();
  const camera = new PerspectiveCamera(34, 1, 0.1, 100);
  camera.position.set(0, 0.26, 6.1);
  camera.lookAt(0, 0.08, 0);

  const renderer = new WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setClearColor(0x140d08, 0);
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;

  const parchment = makeParchmentTexture();
  const brassTexture = makeMetalTexture("#9b5b22", "#f4d16e");
  const copperTexture = makeMetalTexture("#823f22", "#e79a55");
  const steelTexture = makeMetalTexture("#6e6a60", "#d5d2c4");
  const clockTexture = makeClockTexture();

  const brass = new MeshStandardMaterial({
    map: brassTexture,
    color: "#d69b3c",
    metalness: 0.76,
    roughness: 0.38,
    transparent: true,
    opacity: 0.58,
  });
  const copper = new MeshStandardMaterial({
    map: copperTexture,
    color: "#b86b35",
    metalness: 0.68,
    roughness: 0.42,
    transparent: true,
    opacity: 0.55,
  });
  const steel = new MeshStandardMaterial({
    map: steelTexture,
    color: "#a49c8e",
    metalness: 0.82,
    roughness: 0.32,
    transparent: true,
    opacity: 0.5,
  });
  const darkMetal = new MeshStandardMaterial({
    color: "#332014",
    metalness: 0.7,
    roughness: 0.5,
    transparent: true,
    opacity: 0.36,
  });
  const glass = new MeshPhysicalMaterial({
    color: "#c9f4e8",
    metalness: 0,
    roughness: 0.12,
    transmission: 0.2,
    transparent: true,
    opacity: 0.08,
    side: DoubleSide,
  });

  const ambient = new AmbientLight(0xffd79c, 1.6);
  const key = new DirectionalLight(0xffd28a, 3.2);
  key.position.set(-2.5, 3.2, 3.5);
  key.castShadow = true;
  key.shadow.mapSize.width = 1024;
  key.shadow.mapSize.height = 1024;
  const rim = new PointLight(0x76c8bb, 2.2, 8);
  rim.position.set(2.4, 0.7, 2.2);
  const warmGlow = new PointLight(0xf0b75b, 1.8, 5);
  warmGlow.position.set(-0.4, -1.2, 2.1);
  scene.add(ambient, key, rim, warmGlow);

  const background = new Mesh(
    new PlaneGeometry(5.4, 6.4),
    new MeshStandardMaterial({
      map: parchment,
      color: "#c6a674",
      roughness: 0.94,
      metalness: 0.02,
      transparent: true,
      opacity: 0.18,
      depthWrite: false,
    })
  );
  background.position.set(0, 0.06, -1.55);
  background.receiveShadow = true;
  scene.add(background);

  const machine = new Group();
  machine.position.set(-0.06, 0.0, 0.18);
  machine.scale.setScalar(0.44);
  scene.add(machine);

  const coreBack = new Mesh(new CylinderGeometry(1.32, 1.32, 0.26, 96), darkMetal);
  coreBack.rotation.x = Math.PI / 2;
  coreBack.position.z = -0.12;
  coreBack.receiveShadow = true;
  machine.add(coreBack);

  const halo = new Mesh(new TorusGeometry(1.22, 0.055, 18, 112), brass);
  halo.castShadow = true;
  machine.add(halo);
  animatedParts.push({ tick: (time) => (halo.rotation.z = time * 0.08) });

  const flywheel = new Group();
  flywheel.add(new Mesh(createGearGeometry(0.98, 1.1, 0.32, 28, 0.09), steel));
  flywheel.add(new Mesh(new TorusGeometry(0.7, 0.035, 14, 88), brass));
  addSpokes(flywheel, 8, 0.96, brass);
  flywheel.position.z = 0.08;
  machine.add(flywheel);
  animatedParts.push({ tick: (time) => (flywheel.rotation.z = time * 0.18) });

  const mainGear = new Group();
  mainGear.add(new Mesh(createGearGeometry(0.4, 0.52, 0.14, 18, 0.14), brass));
  addSpokes(mainGear, 6, 0.48, steel);
  mainGear.position.set(0, 0, 0.28);
  machine.add(mainGear);
  animatedParts.push({ tick: (time) => (mainGear.rotation.z = -time * 0.68) });

  const leftGear = new Group();
  leftGear.add(new Mesh(createGearGeometry(0.26, 0.34, 0.09, 14, 0.12), copper));
  addSpokes(leftGear, 5, 0.31, brass);
  leftGear.position.set(-0.62, -0.28, 0.38);
  machine.add(leftGear);
  animatedParts.push({ tick: (time) => (leftGear.rotation.z = time * 0.96) });

  const rightGear = new Group();
  rightGear.add(new Mesh(createGearGeometry(0.28, 0.37, 0.11, 15, 0.12), brass));
  addSpokes(rightGear, 5, 0.34, steel);
  rightGear.position.set(0.72, -0.22, 0.32);
  machine.add(rightGear);
  animatedParts.push({ tick: (time) => (rightGear.rotation.z = time * 0.82) });

  const glassDome = new Mesh(new SphereGeometry(1.0, 48, 24, 0, Math.PI * 2, 0, Math.PI * 0.52), glass);
  glassDome.rotation.x = Math.PI;
  glassDome.position.set(0, 0.04, 0.5);
  machine.add(glassDome);

  const cabinet = new Group();
  cabinet.position.set(1.55, -0.42, -0.08);
  cabinet.rotation.y = -0.2;
  cabinet.scale.setScalar(0.82);
  scene.add(cabinet);

  const cabinetBox = new Mesh(new BoxGeometry(0.92, 1.42, 0.28), steel);
  cabinetBox.castShadow = true;
  cabinetBox.receiveShadow = true;
  cabinet.add(cabinetBox);

  for (let index = 0; index < 4; index++) {
    const drawer = new Mesh(new BoxGeometry(0.78, 0.22, 0.08), darkMetal);
    drawer.position.set(0, 0.48 - index * 0.31, 0.17);
    drawer.castShadow = true;
    cabinet.add(drawer);
  }
  const cabinetLabel = makeLabelSprite("Archive");
  cabinetLabel.position.set(0, -0.68, 0.2);
  cabinet.add(cabinetLabel);

  const clock = new Group();
  clock.position.set(1.42, 1.22, 0.2);
  clock.rotation.y = -0.22;
  scene.add(clock);
  const clockFace = new Mesh(
    new CircleGeometry(0.42, 72),
    new MeshStandardMaterial({
      map: clockTexture,
      color: "#e9c276",
      metalness: 0.34,
      roughness: 0.44,
      side: DoubleSide,
    })
  );
  clockFace.castShadow = true;
  clock.add(clockFace);
  const hourHand = new Mesh(new BoxGeometry(0.035, 0.28, 0.03), copper);
  hourHand.position.y = 0.11;
  hourHand.position.z = 0.04;
  const minuteHand = new Mesh(new BoxGeometry(0.024, 0.38, 0.03), brass);
  minuteHand.position.y = 0.16;
  minuteHand.position.z = 0.06;
  clock.add(hourHand, minuteHand);
  animatedParts.push({
    tick: (time) => {
      clock.rotation.z = -time * 0.18;
      hourHand.rotation.z = -time * 0.52;
      minuteHand.rotation.z = -time * 1.4;
    },
  });

  const promptSlip = createPaperPlane("Prompt", "# Make a 2D\nplatformer game...", 1.08);
  promptSlip.position.set(-1.34, -1.63, 1.08);
  promptSlip.rotation.set(-0.64, 0.2, -0.08);
  scene.add(promptSlip);

  const documents = [
    createPaperPlane("agents.md", "workspace memory", 0.82),
    createPaperPlane("notes.md", "manageable notes", 0.82),
    createPaperPlane("trace.md", "decision trace", 0.82),
  ];
  documents.forEach((documentMesh, index) => {
    documentMesh.position.set(0.88 + index * 0.08, 0.3 - index * 0.23, 0.96 + index * 0.04);
    documentMesh.rotation.set(-0.3, -0.36, 0.08 - index * 0.04);
    documentMesh.scale.setScalar(0.8);
    scene.add(documentMesh);
  });

  const tubeMaterial = new MeshStandardMaterial({
    map: copperTexture,
    color: "#9a542d",
    metalness: 0.78,
    roughness: 0.36,
  });
  const tubeCurve = new CatmullRomCurve3([
    new Vector3(-1.42, -0.1, -0.08),
    new Vector3(-1.58, 0.78, 0.08),
    new Vector3(-0.88, 1.16, 0.02),
    new Vector3(-0.3, 1.36, -0.02),
  ]);
  const tube = new Mesh(new TubeGeometry(tubeCurve, 64, 0.035, 12, false), tubeMaterial);
  tube.castShadow = true;
  scene.add(tube);

  const foregroundShadow = new Mesh(
    new PlaneGeometry(4.5, 0.78),
    new MeshBasicMaterial({
      color: "#080503",
      transparent: true,
      opacity: 0.12,
      depthWrite: false,
    })
  );
  foregroundShadow.position.set(0.04, -2.08, 1.25);
  foregroundShadow.rotation.x = -0.7;
  scene.add(foregroundShadow);

  const resize = () => {
    const bounds = root.getBoundingClientRect();
    const width = Math.max(1, Math.floor(bounds.width));
    const height = Math.max(1, Math.floor(bounds.height));
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.65));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };

  const observer = new ResizeObserver(resize);
  observer.observe(root);
  resize();

  const renderFrame = (timeMs = 0) => {
    const time = timeMs / 1000;
    machine.rotation.y = Math.sin(time * 0.22) * 0.035;
    machine.rotation.x = Math.sin(time * 0.18) * 0.012;
    camera.position.x = Math.sin(time * 0.12) * 0.08;
    camera.position.y = 0.26 + Math.cos(time * 0.1) * 0.035;
    camera.lookAt(0, 0.08, 0);

    if (!prefersReducedMotion.matches) {
      const cycle = (time % 7.4) / 7.4;
      const travel = Math.sin(Math.min(1, cycle * 1.7) * Math.PI * 0.5);
      promptSlip.position.x = -1.34 + travel * 1.32;
      promptSlip.position.y = -1.63 + travel * 0.58 + Math.sin(time * 1.6) * 0.018;
      promptSlip.position.z = 1.08 + Math.sin(time * 1.2) * 0.035;
      promptSlip.rotation.z = -0.08 + travel * 0.12;

      documents.forEach((documentMesh, index) => {
        const offset = index * 0.34;
        documentMesh.position.y = 0.3 - index * 0.23 + Math.sin(time * 1.15 + offset) * 0.03;
        documentMesh.position.z = 0.96 + index * 0.04 + Math.cos(time * 0.95 + offset) * 0.024;
        documentMesh.rotation.z = 0.08 - index * 0.04 + Math.sin(time * 0.8 + offset) * 0.025;
      });

      animatedParts.forEach((part) => part.tick(time));
    }

    renderer.render(scene, camera);
    const renderState = prefersReducedMotion.matches ? "static" : "active";
    root.setAttribute("data-render-state", renderState);
    canvas.setAttribute("data-render-state", renderState);

    if (!prefersReducedMotion.matches) {
      frameId = window.requestAnimationFrame(renderFrame);
    }
  };

  const dispose = () => {
    window.cancelAnimationFrame(frameId);
    observer.disconnect();
    scene.traverse((object) => {
      if (object instanceof Mesh) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach((material) => material.dispose());
      }
      if (object instanceof Sprite) {
        object.material.dispose();
      }
    });
    [parchment, brassTexture, copperTexture, steelTexture, clockTexture].forEach((texture) => texture.dispose());
    renderer.dispose();
  };

  try {
    renderFrame();
    if (!prefersReducedMotion.matches) {
      frameId = window.requestAnimationFrame(renderFrame);
    }
    window.addEventListener("pagehide", dispose, { once: true });
  } catch {
    root.setAttribute("data-render-state", "fallback");
    canvas.setAttribute("data-render-state", "fallback");
    dispose();
  }
};

sceneRoots.forEach(initTraceEngineScene);

