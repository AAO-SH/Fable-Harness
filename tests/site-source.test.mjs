import { readFile } from "node:fs/promises";
import { test } from "node:test";
import assert from "node:assert/strict";

const requiredAnchors = ["why", "install", "workflows", "evidence", "community", "faq"];

test("site data defines the institutional landing page contract", async () => {
  const source = await readFile(new URL("../src/data/site.ts", import.meta.url), "utf8");

  assert.match(source, /Fable Harness/);
  assert.match(source, /project-local operating layer/);
  assert.match(source, /Install the Fable-Harness skill/);
  assert.match(source, /npx @aao-sh\/fable-harness "\.\/path\/to\/project" --agent auto/);
  assert.match(source, /Product Design/);
  assert.match(source, /Creative Production/);
  assert.match(source, /Figma/);
  assert.match(source, /Canva/);

  for (const anchor of requiredAnchors) {
    assert.match(source, new RegExp(`id: "${anchor}"`));
  }
});

test("page source exposes all stable section anchors", async () => {
  const source = await readFile(new URL("../src/pages/index.astro", import.meta.url), "utf8");

  for (const anchor of requiredAnchors) {
    assert.match(source, new RegExp(`id=\\{site\\.sections\\.${anchor}\\.id\\}|id="${anchor}"`));
  }
});
