import { readdir, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { basename, join, relative } from "node:path";
import { test } from "node:test";
import assert from "node:assert/strict";

const publicAssets = fileURLToPath(new URL("../public/assets", import.meta.url));
const maxAssetBytes = 2_000_000;

async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(
    entries.map(async (entry) => {
      const path = join(directory, entry.name);
      return entry.isDirectory() ? listFiles(path) : [path];
    })
  );

  return files.flat();
}

test("public deploy assets stay inside the page weight budget", async () => {
  const files = await listFiles(publicAssets);
  const oversized = [];

  for (const file of files) {
    const info = await stat(file);
    if (info.size > maxAssetBytes) {
      oversized.push(`${relative(publicAssets, file)}:${info.size}`);
    }
  }

  assert.deepEqual(oversized, []);
});

test("legacy exploratory assets are not kept in public deploy assets", async () => {
  const files = await listFiles(publicAssets);
  const legacyNames = new Set([
    "trace-engine-hero.png",
    "trace-engine-hero.webp",
    "trace-engine-realistic.svg",
    "trace-engine-realistic.webp",
    "trace-engine-cinematic-sprite.webp",
    "fable-butterfly.svg",
    "fable-harness-icon-512.gif",
    "fable-harness-logo.svg",
  ]);

  const legacyFiles = files
    .map((file) => relative(publicAssets, file))
    .filter((file) => file.startsWith("workflows\\") || file.startsWith("workflows/") || legacyNames.has(basename(file)));

  assert.deepEqual(legacyFiles, []);
});
