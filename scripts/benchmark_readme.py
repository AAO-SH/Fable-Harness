#!/usr/bin/env python3
"""Generate the README benchmark table for Fable Harness."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_fable_harness.py"

CAPABILITIES = [
    ("Root agent instructions", ["AGENTS.md"]),
    ("Decision trace template", [".codex/templates/decision-trace.md"]),
    ("Closure gate", [".codex/scripts/check-closure.py"]),
    ("Memory search", [".codex/scripts/memory-search.py"]),
    ("RAG pipeline", [".codex/scripts/rag-pipeline.py"]),
    ("Loop governance", [".codex/scripts/loop-start.py", ".codex/scripts/loop-check.py"]),
    ("Subagent planning", [".codex/scripts/subagent-plan.py"]),
    ("Selective rollback", [".codex/scripts/selective-revert.py"]),
    ("Code graph", [".codex/scripts/code-graph-build.py"]),
    ("Memory dreaming", [".codex/scripts/memory-dream.py"]),
]


def exists_all(root: Path, paths: list[str]) -> bool:
    return all((root / path).is_file() for path in paths)


def count_files(root: Path, pattern: str) -> int:
    return len(list(root.glob(pattern)))


def measure_workspace(root: Path) -> dict[str, object]:
    capabilities = {
        name: exists_all(root, paths)
        for name, paths in CAPABILITIES
    }
    return {
        "capabilities": capabilities,
        "capability_count": sum(1 for value in capabilities.values() if value),
        "capability_total": len(CAPABILITIES),
        "installed_scripts": count_files(root, ".codex/scripts/*.py"),
        "installed_templates": count_files(root, ".codex/templates/*.md"),
        "has_agent_instructions": (root / "AGENTS.md").is_file(),
    }


def run_benchmark() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as before_name, tempfile.TemporaryDirectory() as after_name:
        before_root = Path(before_name)
        after_root = Path(after_name)
        before = measure_workspace(before_root)

        started = time.perf_counter()
        install = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                str(after_root),
                "--agent",
                "codex",
                "--without-superpowers",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        if install.returncode != 0:
            raise RuntimeError(install.stdout + install.stderr)

        after = measure_workspace(after_root)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scope": "empty temporary workspace vs same workspace after Fable Harness install",
            "command": "python scripts/benchmark_readme.py --markdown",
            "install_elapsed_ms": elapsed_ms,
            "before": before,
            "after": after,
        }


def markdown(report: dict[str, object]) -> str:
    before = report["before"]
    after = report["after"]
    assert isinstance(before, dict)
    assert isinstance(after, dict)
    lines = [
        f"Measured on: {report['generated_at']}",
        "",
        f"Scope: {report['scope']}. This measures deterministic harness control surfaces, not model quality.",
        "",
        "| Capability | Without Fable Harness | With Fable Harness |",
        "|---|---:|---:|",
        (
            f"| Capability checks passed | "
            f"{before['capability_count']}/{before['capability_total']} | "
            f"{after['capability_count']}/{after['capability_total']} |"
        ),
        f"| Installed scripts | {before['installed_scripts']} | {after['installed_scripts']} |",
        f"| Installed templates | {before['installed_templates']} | {after['installed_templates']} |",
        f"| Root agent instructions | {'yes' if before['has_agent_instructions'] else 'no'} | {'yes' if after['has_agent_instructions'] else 'no'} |",
        f"| Install elapsed | n/a | {report['install_elapsed_ms']} ms |",
        "",
        "<details>",
        "<summary>Capability checks</summary>",
        "",
        "| Check | Without | With |",
        "|---|---:|---:|",
    ]
    before_caps = before["capabilities"]
    after_caps = after["capabilities"]
    assert isinstance(before_caps, dict)
    assert isinstance(after_caps, dict)
    for name, _paths in CAPABILITIES:
        lines.append(
            f"| {name} | {'yes' if before_caps[name] else 'no'} | {'yes' if after_caps[name] else 'no'} |"
        )
    lines.extend(["", "</details>"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Fable Harness README claims.")
    parser.add_argument("--markdown", action="store_true", help="Print a Markdown table.")
    parser.add_argument("--json", action="store_true", help="Print the raw benchmark JSON.")
    args = parser.parse_args()

    report = run_benchmark()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
