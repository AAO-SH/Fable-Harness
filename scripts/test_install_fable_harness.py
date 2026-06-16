import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_fable_harness.py")
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class InstallFableHarnessTest(unittest.TestCase):
    def run_install(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_module_install(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC)
        return subprocess.run(
            [sys.executable, "-m", "fable_harness", str(root), *args],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def test_installs_codex_harness_and_preserves_existing_agents_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            agents.write_text("# Existing Instructions\n\nKeep this line.\n", encoding="utf-8")

            result = self.run_install(root, "--agent", "codex")

            self.assertEqual(result.returncode, 0, result.stderr)
            text = agents.read_text(encoding="utf-8")
            self.assertIn("Keep this line.", text)
            self.assertIn("<!-- fable-harness:start -->", text)
            self.assertIn("The main orchestrating agent owns memory coherence.", text)
            self.assertIn(
                "Before broad filesystem exploration or planning a non-trivial task, run",
                text,
            )
            self.assertIn(
                "unless the task is clearly self-contained",
                text,
            )
            self.assertIn("subagent-plan.py", text)
            self.assertIn("Dispatch subagents from the generated briefs", text)
            self.assertTrue((root / ".codex" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "semantic-note.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "subagent-brief.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "memory-closure.md").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "new-trace.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "new-note.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "promote-trace.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory-search.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "rebuild-memory.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "subagent-plan.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "subagent-result.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory-maintenance.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "check-closure.py").is_file())
            self.assertTrue((root / ".codex" / "notes" / "_index.md").is_file())
            self.assertTrue((root / ".codex" / "decision-traces" / "_index.md").is_file())
            self.assertTrue((root / ".codex" / "memory" / "manifest.json").is_file())
            self.assertTrue((root / ".codex" / "memory" / "shards").is_dir())
            self.assertTrue((root / ".codex" / "memory" / "graph").is_dir())

            rerun = self.run_install(root, "--agent", "codex")

            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            text = agents.read_text(encoding="utf-8")
            self.assertEqual(text.count("<!-- fable-harness:start -->"), 1)
            self.assertEqual(text.count("<!-- fable-harness:end -->"), 1)

    def test_installs_claude_compatible_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_install(root, "--agent", "claude")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "CLAUDE.md").is_file())
            self.assertTrue((root / ".claude" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".claude" / "scripts" / "new-trace.py").is_file())
            self.assertIn(
                ".claude/notes/_index.md",
                (root / "CLAUDE.md").read_text(encoding="utf-8"),
            )

    def test_installs_any_compatible_harness_with_agents_md_and_agents_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_install(root, "--agent", "any")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertFalse((root / "CLAUDE.md").exists())
            self.assertTrue((root / ".agents" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".agents" / "scripts" / "check-closure.py").is_file())
            self.assertIn(
                ".agents/notes/_index.md",
                (root / "AGENTS.md").read_text(encoding="utf-8"),
            )

            closure = subprocess.run(
                [
                    sys.executable,
                    str(root / ".agents" / "scripts" / "check-closure.py"),
                    "--root",
                    str(root),
                    "--agent",
                    "any",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(closure.returncode, 0, closure.stdout + closure.stderr)

    def test_both_installs_codex_claude_and_any_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_install(root, "--agent", "both")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertTrue((root / "CLAUDE.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".claude" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".agents" / "templates" / "decision-trace.md").is_file())

    def test_auto_uses_any_for_neutral_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_install(root, "--agent", "auto")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertTrue((root / ".agents" / "templates" / "decision-trace.md").is_file())
            self.assertFalse((root / ".codex").exists())
            self.assertFalse((root / ".claude").exists())

    def test_python_module_entrypoint_installs_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_module_install(root, "--agent", "codex")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "check-closure.py").is_file())

    def test_generated_scripts_create_trace_and_validate_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_script = root / ".codex" / "scripts" / "new-trace.py"
            trace = subprocess.run(
                [sys.executable, str(trace_script), "--root", str(root), "--title", "Demo Harness"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(trace.returncode, 0, trace.stderr)
            trace_path = Path(trace.stdout.strip())
            self.assertTrue(trace_path.is_file())
            self.assertIn("Demo Harness", trace_path.read_text(encoding="utf-8"))
            self.assertIn(trace_path.name, (root / ".codex" / "decision-traces" / "_index.md").read_text(encoding="utf-8"))

            closure_script = root / ".codex" / "scripts" / "check-closure.py"
            closure = subprocess.run(
                [sys.executable, str(closure_script), "--root", str(root), "--trace", str(trace_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(closure.returncode, 0, closure.stdout + closure.stderr)
            self.assertIn("closure check passed", closure.stdout.lower())

    def test_generated_scripts_compile_on_python_311_when_launcher_exists(self):
        if not shutil.which("py"):
            self.skipTest("Windows py launcher is not available")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            compile_check = subprocess.run(
                [
                    "py",
                    "-3",
                    "-m",
                    "py_compile",
                    str(root / ".codex" / "scripts" / "memory_core.py"),
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    str(root / ".codex" / "scripts" / "subagent-result.py"),
                    str(root / ".codex" / "scripts" / "memory-maintenance.py"),
                    str(root / ".codex" / "scripts" / "promote-trace.py"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compile_check.returncode, 0, compile_check.stdout + compile_check.stderr)

    def test_closure_requires_durable_trace_promotion_before_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "durable-memory-choice.md"
            trace_path.write_text(
                """# Durable Memory Choice

## Objective

Decide how subagent findings become durable memory.

### Decide

The orchestrator must review subagent findings before promoting them into semantic notes.

### Verify

The closure check should fail until this decision is promoted.
""",
                encoding="utf-8",
            )
            stale_note = root / ".codex" / "notes" / "decisions" / "workflow" / "stale.md"
            stale_note.parent.mkdir(parents=True, exist_ok=True)
            stale_note.write_text(
                f"""# Stale Mention

---
status: stale
sources:
  -
last_verified:
---

This note mentions {trace_path.name} but does not source it.
""",
                encoding="utf-8",
            )

            closure_script = root / ".codex" / "scripts" / "check-closure.py"
            first = subprocess.run(
                [sys.executable, str(closure_script), "--root", str(root), "--trace", str(trace_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("durable trace evidence was not promoted", first.stderr.lower())
            self.assertIn("promote-trace.py", first.stderr)

            promote = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "promote-trace.py"),
                    "--root",
                    str(root),
                    "--trace",
                    str(trace_path),
                    "--category",
                    "decisions",
                    "--area",
                    "workflow",
                    "--topic",
                    "subagent-memory-ownership",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(promote.returncode, 0, promote.stdout + promote.stderr)

            second = subprocess.run(
                [sys.executable, str(closure_script), "--root", str(root), "--trace", str(trace_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)

    def test_closure_allows_trace_when_note_sources_it_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "sourced-choice.md"
            trace_path.write_text(
                """# Sourced Choice

### Decide

Use parsed note sources as promotion proof.
""",
                encoding="utf-8",
            )
            note_path = root / ".codex" / "notes" / "decisions" / "workflow" / "sourced-choice.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(
                """# Sourced Choice

---
status: active
sources:
  - ../../../decision-traces/sourced-choice.md
last_verified: 2026-06-16
---

## Durable Fact Or Decision

Use parsed note sources as promotion proof.
""",
                encoding="utf-8",
            )

            closure = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "check-closure.py"),
                    "--root",
                    str(root),
                    "--trace",
                    str(trace_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(closure.returncode, 0, closure.stdout + closure.stderr)

    def test_generated_subagent_plan_creates_dispatch_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "active-task.md"
            trace_path.write_text("# Active Task\n", encoding="utf-8")

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Harden the Fable Harness",
                    "--domain",
                    "closure gate",
                    "--domain",
                    "subagent invocation",
                    "--trace",
                    str(trace_path),
                    "--file",
                    str(root / "AGENTS.md"),
                    "--protected-test",
                    str(root / ".codex" / "scripts" / "check-closure.py"),
                    "--verification",
                    "python scripts/test_install_fable_harness.py",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())
            self.assertTrue(plan_dir.is_dir())

            dispatch = plan_dir / "_dispatch.md"
            self.assertTrue(dispatch.is_file())
            dispatch_text = dispatch.read_text(encoding="utf-8")
            self.assertIn("Dispatch using the available subagent tool", dispatch_text)
            self.assertIn("spawn_agent", dispatch_text)
            self.assertIn("closure-gate.md", dispatch_text)
            self.assertIn("subagent-invocation.md", dispatch_text)

            brief = (plan_dir / "closure-gate.md").read_text(encoding="utf-8")
            self.assertIn("Harden the Fable Harness", brief)
            self.assertIn("Current Trace", brief)
            self.assertIn(trace_path.name, brief)
            self.assertIn(str(root / "AGENTS.md"), brief)
            self.assertIn(str(root / ".codex" / "scripts" / "check-closure.py"), brief)
            self.assertIn("python scripts/test_install_fable_harness.py", brief)

    def test_generated_subagent_plan_resolves_relative_trace_from_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "relative-trace.md"
            trace_path.write_text("# Relative Trace\n", encoding="utf-8")

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Check relative trace handling",
                    "--domain",
                    "trace paths",
                    "--trace",
                    ".codex/decision-traces/relative-trace.md",
                ],
                cwd=Path(tmp).parent,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            brief = Path(plan.stdout.strip()) / "trace-paths.md"
            self.assertIn(
                ".codex/decision-traces/relative-trace.md",
                brief.read_text(encoding="utf-8"),
            )

    def test_generated_subagent_result_records_outcome_in_dispatch_and_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "active-task.md"
            trace_path.write_text(
                """# Active Task

## Subagents

| Stage | Subtask | Evidence Returned | Accepted By Orchestrator |
|---|---|---|---|
| pending | closure gate | pending | pending |

## Memory Updates

- Durable decisions promoted: none
""",
                encoding="utf-8",
            )

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Check closure gate",
                    "--domain",
                    "closure gate",
                    "--trace",
                    str(trace_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-result.py"),
                    "--root",
                    str(root),
                    "--plan-dir",
                    str(plan_dir),
                    "--domain",
                    "closure gate",
                    "--status",
                    "DONE_WITH_CONCERNS",
                    "--summary",
                    "Closure needs exact source evidence.",
                    "--finding",
                    "Loose trace-name matching can pass stale notes.",
                    "--accepted-by",
                    "orchestrator",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result_path = Path(result.stdout.strip())
            self.assertTrue(result_path.is_file())
            self.assertIn("DONE_WITH_CONCERNS", result_path.read_text(encoding="utf-8"))

            dispatch_text = (plan_dir / "_dispatch.md").read_text(encoding="utf-8")
            self.assertIn("| closure-gate |", dispatch_text)
            self.assertIn("DONE_WITH_CONCERNS", dispatch_text)
            self.assertIn("orchestrator", dispatch_text)

            trace_text = trace_path.read_text(encoding="utf-8")
            self.assertIn("Closure needs exact source evidence.", trace_text)
            self.assertIn(result_path.name, trace_text)

            manifest = json.loads((plan_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["results"][0]["status"], "DONE_WITH_CONCERNS")

    def test_memory_maintenance_reports_growth_and_retrieval_risks_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            large_note = root / ".codex" / "notes" / "project" / "large-note.md"
            large_note.parent.mkdir(parents=True, exist_ok=True)
            large_note.write_text(
                "# Large Note\n\n---\nstatus: active\nsources:\n  - ../../decision-traces/missing.md\nlast_verified: 2020-01-01\n---\n\n"
                + ("dense memory line\n" * 80),
                encoding="utf-8",
            )

            promoted_trace = root / ".codex" / "decision-traces" / "promoted.md"
            promoted_trace.write_text("# Promoted\n\n### Decide\n\nKeep notes compact.\n", encoding="utf-8")
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({"trace": ".codex/decision-traces/promoted.md", "note": ".codex/notes/project/large-note.md"}) + "\n",
                encoding="utf-8",
            )

            report = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-maintenance.py"),
                    "--root",
                    str(root),
                    "--max-note-bytes",
                    "400",
                    "--stale-days",
                    "30",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
            data = json.loads(report.stdout)
            actions = {item["action"] for item in data["candidates"]}
            self.assertIn("compact-note", actions)
            self.assertIn("repair-source", actions)
            self.assertIn("revalidate-note", actions)
            self.assertIn("archive-promoted-trace", actions)
            self.assertTrue((root / ".codex" / "memory" / "maintenance" / "latest-report.json").is_file())
            self.assertTrue((root / ".codex" / "memory" / "maintenance" / "latest-report.md").is_file())
            self.assertTrue(large_note.exists(), "maintenance report must not delete source notes")

    def test_memory_scripts_create_promote_index_search_and_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_script = root / ".codex" / "scripts" / "new-trace.py"
            trace = subprocess.run(
                [sys.executable, str(trace_script), "--root", str(root), "--title", "Memory Ownership"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(trace.returncode, 0, trace.stderr)
            trace_path = Path(trace.stdout.strip())
            trace_path.write_text(
                """# Memory Ownership

## Objective

Decide who owns project memory.

### Decide

The main orchestrating agent owns memory coherence. Subagents may suggest memory updates but cannot silently promote durable notes.

### Verify

The closure check passed for the memory ownership workflow.
""",
                encoding="utf-8",
            )

            promote = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "promote-trace.py"),
                    "--root",
                    str(root),
                    "--trace",
                    str(trace_path),
                    "--category",
                    "decisions",
                    "--area",
                    "workflow",
                    "--topic",
                    "memory-ownership",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(promote.returncode, 0, promote.stdout + promote.stderr)
            note_path = root / ".codex" / "notes" / "decisions" / "workflow" / "memory-ownership.md"
            self.assertTrue(note_path.is_file())
            note_text = note_path.read_text(encoding="utf-8")
            self.assertIn("main orchestrating agent owns memory coherence", note_text)
            self.assertIn(trace_path.name, note_text)
            self.assertIn(
                "memory-ownership.md",
                (root / ".codex" / "notes" / "_index.md").read_text(encoding="utf-8"),
            )

            manifest = json.loads((root / ".codex" / "memory" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["storage"], "sharded-jsonl")
            self.assertGreaterEqual(manifest["document_count"], 1)
            self.assertTrue(manifest["shards"])
            self.assertTrue((root / ".codex" / "memory" / "graph" / "nodes.jsonl").is_file())
            self.assertTrue((root / ".codex" / "memory" / "graph" / "edges.jsonl").is_file())
            self.assertTrue((root / ".codex" / "memory" / "promotion_log.jsonl").is_file())

            search = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-search.py"),
                    "--root",
                    str(root),
                    "--query",
                    "who owns memory coherence",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(search.returncode, 0, search.stdout + search.stderr)
            results = json.loads(search.stdout)
            self.assertTrue(results)
            self.assertEqual(results[0]["path"].replace("\\", "/"), ".codex/notes/decisions/workflow/memory-ownership.md")


if __name__ == "__main__":
    unittest.main()
