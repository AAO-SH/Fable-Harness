import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

const site = "https://fable.aao.sh";

export default defineConfig({
  site,
  integrations: [sitemap()],
  output: "static",
  build: {
    assets: "_assets",
  },
});
