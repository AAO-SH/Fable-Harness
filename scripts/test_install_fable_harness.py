import os
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
            self.assertTrue((root / ".codex" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "semantic-note.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "subagent-brief.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "memory-closure.md").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "new-trace.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "check-closure.py").is_file())
            self.assertTrue((root / ".codex" / "notes" / "_index.md").is_file())
            self.assertTrue((root / ".codex" / "decision-traces" / "_index.md").is_file())

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


if __name__ == "__main__":
    unittest.main()
