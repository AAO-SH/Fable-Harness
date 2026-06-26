import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";

const html = await readFile(new URL("../dist/index.html", import.meta.url), "utf8");
const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]));
const hrefs = [...html.matchAll(/\shref="([^"]+)"/g)].map((match) => match[1]);

const missingAnchors = hrefs
  .filter((href) => href.startsWith("#"))
  .map((href) => href.slice(1))
  .filter((anchor) => !ids.has(anchor));

assert.deepEqual(missingAnchors, [], `Missing internal anchors: ${missingAnchors.join(", ")}`);

const brokenAssetRefs = [...html.matchAll(/\s(?:src|href)="([^"]+)"/g)]
  .map((match) => match[1])
  .filter((ref) => ref.startsWith("/assets/") || ref.startsWith("/_assets/"))
  .filter((ref) => ref.includes("undefined") || ref.includes("null"));

assert.deepEqual(brokenAssetRefs, [], `Suspicious asset refs: ${brokenAssetRefs.join(", ")}`);

console.log(`Checked ${hrefs.length} links and ${ids.size} ids.`);
