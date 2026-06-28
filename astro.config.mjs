import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

const site = "https://fable.aao.sh";
const normalizeModuleId = (id) => id.replaceAll("\\", "/");

const manualChunks = (id) => {
  const moduleId = normalizeModuleId(id);

  if (!moduleId.includes("/node_modules/three/src/")) {
    return undefined;
  }

  if (moduleId.includes("/renderers/")) {
    return "three-renderer";
  }

  if (moduleId.includes("/geometries/") || moduleId.includes("/extras/")) {
    return "three-geometry";
  }

  if (moduleId.includes("/materials/") || moduleId.includes("/textures/")) {
    return "three-materials";
  }

  return "three-core";
};

export default defineConfig({
  site,
  integrations: [sitemap()],
  output: "static",
  build: {
    assets: "_assets",
  },
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks,
        },
      },
    },
  },
});
