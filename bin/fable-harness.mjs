#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const installerPath = resolve(packageRoot, "scripts", "install_fable_harness.py");
const args = process.argv.slice(2);

if (args.includes("--help") || args.includes("-h")) {
  printUsage();
  process.exit(0);
}

if (args.length === 0) {
  printUsage();
  process.exit(1);
}

const python = findPython();
const result = spawnSync(python, [installerPath, ...args], {
  stdio: "inherit"
});

if (result.error !== undefined) {
  console.error(`Failed to run Python installer: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 1);

function findPython() {
  for (const candidate of process.platform === "win32"
    ? ["python", "py"]
    : ["python3", "python"]) {
    const result = spawnSync(candidate, ["--version"], {
      encoding: "utf8",
      stdio: "pipe"
    });

    if (result.status === 0) {
      return candidate;
    }
  }

  console.error("Python is required to install Fable Harness.");
  process.exit(1);
}

function printUsage() {
  console.log(`Fable Harness installer

Usage:
  fable-harness <project-root> --agent <codex|claude|any|both|auto>

Examples:
  fable-harness . --agent codex
  fable-harness C:\\path\\to\\project --agent both
`);
}
