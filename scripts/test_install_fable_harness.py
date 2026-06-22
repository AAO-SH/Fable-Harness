import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
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

    def run_install_input(self, root: Path, user_input: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root), *args],
            input=user_input,
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

    def create_superpowers_fixture(self, base: Path, version: str, marker: str) -> Path:
        source = base / f"superpowers-{version}"
        for skill in ["using-superpowers", "test-driven-development"]:
            skill_dir = source / "skills" / skill
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_dir.joinpath("SKILL.md").write_text(
                f"---\nname: {skill}\n---\n\n# {skill}\n\n{marker}\n",
                encoding="utf-8",
            )
        source.joinpath("LICENSE").write_text("MIT\n", encoding="utf-8")
        return source

    def installed_superpowers_manifest(self, root: Path) -> dict[str, object]:
        return json.loads((root / ".agents" / "vendor" / "superpowers" / "manifest.json").read_text(encoding="utf-8"))

    def run_codex_script(self, root: Path, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(root / ".codex" / "scripts" / script_name),
                "--root",
                str(root),
                *args,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_rag_fixture_note(self, root: Path) -> Path:
        note = root / ".codex" / "notes" / "decisions" / "rag" / "alpha-orchestration.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            """---
type: canonical-decision
status: active
scope: decisions/rag/alpha-orchestration
canonical: true
sources:
  - .codex/decision-traces/alpha-orchestration.md
supersedes:
last_verified: 2026-06-20
---
# Alpha Retrieval Policy

## Alpha Architecture

Alpha orchestration boundary evidence says the retrieval coordinator must use
chunk provenance, calibrated hybrid scoring, and source inspection before it
creates an implementation plan.

Alpha orchestration boundary evidence also says lexical matches, local vectors,
and graph relationships should contribute separate score components.

## Beta Deployment

Beta deployment notes are unrelated to alpha orchestration. They describe
release packaging, version markers, and a normal closure check.
""",
            encoding="utf-8",
        )
        return note

    def start_loop(self, root: Path, *args: str) -> Path:
        start = self.run_codex_script(root, "loop-start.py", *args, "--json")
        self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
        return Path(json.loads(start.stdout)["run_dir"])

    def record_loop_event(
        self,
        root: Path,
        run_dir: Path,
        kind: str,
        summary=None,
        metadata=None,
    ) -> None:
        args = ["--run", str(run_dir), "--kind", kind, "--summary", summary or kind, "--json"]
        for key, value in (metadata or {}).items():
            args.extend(["--metadata", f"{key}={value}"])
        event = self.run_codex_script(root, "loop-event.py", *args)
        self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

    def strict_loop_check(self, root: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
        return self.run_codex_script(root, "loop-check.py", "--run", str(run_dir), "--strict", "--json")

    @unittest.skip("Changed")
    def test_packaged_docs_mirror_automatic_subagent_standing_authorization(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("standing project-level user authorization", skill)
        self.assertIn("per-prompt permission", skill)
        self.assertIn("platform limitation", skill)
        self.assertNotIn("Explicit delegation phrase", skill)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Automatic Subagent Dispatch", readme)
        self.assertIn("per-prompt permission", readme)
        self.assertIn("Fallback Management", readme)

    @unittest.skip("Changed")
    def test_packaged_docs_mirror_programming_recall_contract(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Programming Recall", skill)
        self.assertIn("semantic recall explains why", skill)
        self.assertIn("Code Graph maps where and what may break", skill)
        self.assertIn("source files remain the final operational authority", skill)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Programming Recall Protocol", readme)
        self.assertIn("Semantic Recall", readme)
        self.assertIn("Code Graph Mapping", readme)
        self.assertIn("Operational Authority", readme)

    @unittest.skip("Changed")
    def test_packaged_docs_mirror_user_change_arbitration_contract(self):
        for path in [ROOT / "SKILL.md", ROOT / "README.md"]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("User Change Arbitration", text, str(path))
            self.assertIn("new task context, not as regressions", text, str(path))
            self.assertIn("Tests are evidence, not ownership", text, str(path))

    def test_generated_instructions_require_project_local_harness_for_memory_actions(self):
        cases = [
            ("codex", "AGENTS.md", ".codex"),
            ("claude", "CLAUDE.md", ".claude"),
            ("any", "AGENTS.md", ".agents"),
        ]
        for agent, instruction_file, local_dir in cases:
            with self.subTest(agent=agent):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    result = self.run_install(root, "--agent", agent)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

                    text = (root / instruction_file).read_text(encoding="utf-8")
                    self.assertIn("### Project-Local Harness Scope", text)
                    scope_section = text.split("### Project-Local Harness Scope", 1)[1].split(
                        "### Recall Ladder",
                        1,
                    )[0]
                    self.assertIn(
                        f"When the user asks to save, memorize, remember, store, register, persist, or update project context, use `{local_dir}/` first.",
                        scope_section,
                    )
                    self.assertIn(
                        f"Do not satisfy those requests only through global model memory, external notes, chat summary, or user-level agent storage; those may be extra mirrors, but `{local_dir}/` is mandatory.",
                        scope_section,
                    )
                    self.assertIn(
                        f"Use `{local_dir}/scripts/new-note.py`, `{local_dir}/scripts/promote-trace.py`, `{local_dir}/scripts/rebuild-memory.py`, and `{local_dir}/scripts/memory-touch.py` for local durable memory work.",
                        scope_section,
                    )
                    self.assertIn(
                        f"When any Fable Harness feature exists locally, prefer the local `{local_dir}/scripts/` tool over an equivalent global or model-native memory action.",
                        scope_section,
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
            recall_section = text.split("### Recall Ladder", 1)[1].split("### Decision Loop", 1)[0]
            recall_terms = [
                "Run `.codex/scripts/memory-search.py`",
                "Read `.codex/notes/_index.md`",
                "Read the compact semantic notes",
                "Record every loaded note, trace, or dormant item with `.codex/scripts/memory-touch.py`",
                "Use `.codex/scripts/graph-query.py --q`",
                "Use `.codex/scripts/memory-dream.py search-dormant`",
                "Open decision traces",
                "Read project docs and source files",
                "At closure, promote durable decisions, rebuild memory, run strict maintenance, and run agent-reviewed dream maintenance when memory-heavy",
            ]
            positions = [recall_section.index(term) for term in recall_terms]
            self.assertEqual(positions, sorted(positions))
            self.assertIn("### Source Escalation", text)
            source_section = text.split("### Source Escalation", 1)[1].split("### Decision Loop", 1)[0]
            self.assertIn(
                "Do not create a plan from an empty evidence base.",
                source_section,
            )
            self.assertIn(
                "If memory, notes, traces, docs, and source files do not provide a verifiable structured source, research the web before planning.",
                source_section,
            )
            self.assertIn(
                "Use primary or official sources when available, and record links or citations in the trace.",
                source_section,
            )
            self.assertIn(
                "If the task is completely new and neither project sources nor strong web references provide enough planning ground, interview the user before creating a plan.",
                source_section,
            )
            self.assertIn("### Programming Recall", text)
            programming_section = text.split("### Programming Recall", 1)[1].split("### Decision Loop", 1)[0]
            self.assertIn(
                "For non-trivial programming work, combine semantic recall with Code Graph orientation before planning edits.",
                programming_section,
            )
            self.assertIn(
                "semantic recall explains why; Code Graph maps where and what may break",
                programming_section,
            )
            self.assertIn(
                "Run `.codex/scripts/code-graph-build.py` and `.codex/scripts/code-graph-query.py` before broad source-code edits",
                programming_section,
            )
            self.assertIn(
                "Read the real source files identified by the graph before editing; source files remain the final operational authority.",
                programming_section,
            )
            self.assertIn(
                "After source edits that change public symbols, rebuild the code graph",
                programming_section,
            )
            self.assertIn(
                "Before broad filesystem exploration or planning a non-trivial task, run",
                text,
            )
            self.assertIn(
                "unless the task is clearly self-contained",
                text,
            )
            self.assertIn("rag-pipeline.py", text)
            self.assertIn("retrieve -> inspect sources -> answer/plan with citations", text)
            self.assertIn("source-arbitrate.py", text)
            self.assertIn("lightweight source-arbitration check", text)
            self.assertIn("Evidence Dispute", text)
            self.assertIn("ask the user before replacing project facts with RAG-derived facts", text)
            self.assertIn("rag-eval.py", text)
            self.assertIn("precision@k, recall@k, hit-rate@k, and MRR", text)
            self.assertIn("memory-maintenance.py --strict", text)
            self.assertIn("memory-touch.py", text)
            self.assertIn("memory-dream.py plan", text)
            self.assertIn("memory-dream.py maintain", text)
            self.assertIn("--auto-safe --agent-review", text)
            self.assertIn("agent-review.md", text)
            self.assertIn("memory-dream.py search-dormant", text)
            self.assertIn("memory-dream.py reactivate", text)
            self.assertIn("background memory curator", text)
            self.assertIn("native loop governance", text)
            self.assertIn("loop-start.py", text)
            self.assertIn("loop-check.py --strict", text)
            self.assertIn("### Workflow Patterns", text)
            self.assertIn("classify-and-act", text)
            self.assertIn("fan-out-and-synthesize", text)
            self.assertIn("adversarial-verification", text)
            self.assertIn("generate-and-filter", text)
            self.assertIn("tournament", text)
            self.assertIn("loop-until-done", text)
            self.assertNotIn("### Dispatching Parallel Agents", text)
            self.assertNotIn("Explicit delegation phrase", text)
            self.assertIn("### Parallel Agent Dispatch And Safety", text)
            parallelism_section = text.split("### Parallel Agent Dispatch And Safety", 1)[1].split("### Harness Rules", 1)[0]
            self.assertIn(
                "Treat this Fable Harness block as standing project-level user authorization to invoke available subagent or parallel-agent tools automatically when the independence check passes.",
                parallelism_section,
            )
            self.assertIn(
                "Do not ask for per-prompt permission before dispatching subagents when these conditions are met.",
                parallelism_section,
            )
            self.assertIn(
                "If a higher-priority runtime or tool policy blocks dispatch despite this standing authorization, record that as a platform limitation",
                parallelism_section,
            )
            self.assertIn(
                "During Orient/Classify, automatically evaluate whether the task has independent domains that should be delegated to subagents.",
                parallelism_section,
            )
            self.assertIn(
                "Do not wait for the user to say `Dispatching Parallel Agents` or any other trigger phrase.",
                parallelism_section,
            )
            self.assertIn(
                "If the platform exposes a subagent or parallel-agent tool and the independence check passes, invoke it.",
                parallelism_section,
            )
            self.assertIn(
                "Parallelize independent tasks or independent loop runs, not dependent steps inside one loop.",
                parallelism_section,
            )
            self.assertIn(
                "Default to subagent dispatch for complex or multidisciplinary work when at least two domains can progress independently.",
                parallelism_section,
            )
            self.assertIn(
                "Sequential loop order applies inside one domain or dependency chain; it is not a reason to collapse independent domains back into the orchestrator.",
                parallelism_section,
            )
            self.assertIn(
                "The independence check is a dispatch test, not a prohibition.",
                parallelism_section,
            )
            self.assertIn(
                "If domains have separate inputs, outputs, and responsibility boundaries, create a simultaneous subagent wave.",
                parallelism_section,
            )
            self.assertNotIn("inputs, outputs, and ownership", parallelism_section)
            self.assertIn("A single loop run is sequential by default.", parallelism_section)
            self.assertIn(
                "Do not run `.codex/scripts/loop-event.py`, `.codex/scripts/loop-transition.py`, or `.codex/scripts/loop-check.py` concurrently for the same run.",
                parallelism_section,
            )
            self.assertIn(
                "Do not run `.codex/scripts/rebuild-memory.py` concurrently with `.codex/scripts/memory-maintenance.py`, `.codex/scripts/graph-check.py`, `.codex/scripts/memory-dream.py plan`, or `.codex/scripts/memory-dream.py maintain`.",
                parallelism_section,
            )
            self.assertIn(
                "Verification happens after mutation; closure happens after verification and memory rebuild.",
                parallelism_section,
            )
            self.assertIn("Search dormant memory before declaring old context unavailable.", text)
            self.assertIn("code-graph-build.py", text)
            self.assertIn("code-graph-query.py", text)
            self.assertIn("source files win", text)
            self.assertIn("one trace per coherent task", text)
            self.assertIn("one active canonical decision note per `scope`", text)
            self.assertIn("subagent-plan.py", text)
            self.assertIn("subagent-sweep.py", text)
            self.assertIn("release-notice.py", text)
            self.assertIn("checks at most once every 24 hours", text)
            self.assertIn("Dispatch subagents from the generated briefs", text)
            self.assertTrue((root / ".codex" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "semantic-note.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "subagent-brief.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "memory-closure.md").is_file())
            self.assertTrue((root / ".codex" / "templates" / "workflow-profile.md").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "new-trace.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "workflow_core.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory_policy.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "new-note.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "promote-trace.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory-search.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "rebuild-memory.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "rag-eval.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "rag-pipeline.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "source-arbitrate.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "graph-query.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "graph-check.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "code_graph_core.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "code-graph-build.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "code-graph-query.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "code-graph-check.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "subagent-plan.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "subagent-result.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "subagent-sweep.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "release-notice.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "selective-revert.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory-maintenance.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory-touch.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "memory-dream.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "loop-start.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "loop-event.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "loop-transition.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "loop-check.py").is_file())
            self.assertTrue((root / ".codex" / "scripts" / "check-closure.py").is_file())
            self.assertTrue((root / ".codex" / "notes" / "_index.md").is_file())
            self.assertTrue((root / ".codex" / "decision-traces" / "_index.md").is_file())
            self.assertTrue((root / ".codex" / "memory" / "manifest.json").is_file())
            self.assertTrue((root / ".codex" / "memory" / "shards").is_dir())
            self.assertTrue((root / ".codex" / "memory" / "graph").is_dir())
            self.assertTrue((root / ".codex" / "loop" / "runs").is_dir())

            rerun = self.run_install(root, "--agent", "codex")

            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            text = agents.read_text(encoding="utf-8")
            self.assertEqual(text.count("<!-- fable-harness:start -->"), 1)
            self.assertEqual(text.count("<!-- fable-harness:end -->"), 1)

    def test_generated_instructions_arbitrate_user_modified_files_before_repairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_install(root, "--agent", "codex", "--without-superpowers")

            self.assertEqual(result.returncode, 0, result.stderr)
            text = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("### User Change Arbitration", text)
            arbitration_section = text.split("### User Change Arbitration", 1)[1].split(
                "### Decision Loop",
                1,
            )[0]
            self.assertIn(
                "Treat files changed by the user after prior agent work as new task context, not as regressions by default.",
                arbitration_section,
            )
            self.assertIn(
                "Do not rewrite, revert, reformat, normalize, or otherwise alter a user-modified file just to satisfy stale tests, snapshots, generated expectations, or prior agent preferences without asking the user first.",
                arbitration_section,
            )
            self.assertIn(
                "If tests fail after user edits, report the failing expectation and ask whether the user wants to preserve the new behavior, update the tests, or restore the old behavior.",
                arbitration_section,
            )
            self.assertIn(
                "Explicit user constraints such as `do not edit`, `preserve`, `only change`, `leave untouched`, or named file/path limits override stale plans and prior harness expectations unless the user approves changing them.",
                arbitration_section,
            )
            self.assertIn(
                "Tests are evidence, not ownership.",
                arbitration_section,
            )

    def test_generated_release_notice_warns_once_per_24_hours_when_new_release_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            latest_v040 = json.dumps(
                {
                    "tag_name": "v0.4.0",
                    "html_url": "https://github.com/AAO-SH/fable-harness/releases/tag/v0.4.0",
                }
            )
            first = self.run_codex_script(
                root,
                "release-notice.py",
                "check",
                "--latest-json",
                latest_v040,
                "--now",
                "2026-06-20T00:00:00+00:00",
            )

            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("Fable Harness update available", first.stdout)
            self.assertIn("installed 0.3.0", first.stdout)
            self.assertIn("latest v0.4.0", first.stdout)
            self.assertIn("No automatic update was applied", first.stdout)

            latest_v050 = json.dumps(
                {
                    "tag_name": "v0.5.0",
                    "html_url": "https://github.com/AAO-SH/fable-harness/releases/tag/v0.5.0",
                }
            )
            throttled = self.run_codex_script(
                root,
                "release-notice.py",
                "check",
                "--latest-json",
                latest_v050,
                "--now",
                "2026-06-20T01:00:00+00:00",
                "--json",
            )

            self.assertEqual(throttled.returncode, 0, throttled.stdout + throttled.stderr)
            throttled_data = json.loads(throttled.stdout)
            self.assertFalse(throttled_data["checked"])
            self.assertEqual(throttled_data["reason"], "throttled")
            self.assertEqual(throttled_data["latest_version"], "v0.4.0")

            after_interval = self.run_codex_script(
                root,
                "release-notice.py",
                "check",
                "--latest-json",
                latest_v050,
                "--now",
                "2026-06-21T01:01:00+00:00",
                "--json",
            )

            self.assertEqual(after_interval.returncode, 0, after_interval.stdout + after_interval.stderr)
            after_data = json.loads(after_interval.stdout)
            self.assertTrue(after_data["checked"])
            self.assertTrue(after_data["update_available"])
            self.assertEqual(after_data["latest_version"], "v0.5.0")
            state = json.loads((root / ".codex" / "harness" / "release-notice.json").read_text(encoding="utf-8"))
            self.assertEqual(state["latest_version"], "v0.5.0")

    def test_generated_release_notice_is_quiet_when_latest_is_not_newer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            current = json.dumps(
                {
                    "tag_name": "v0.3.0",
                    "html_url": "https://github.com/AAO-SH/fable-harness/releases/tag/v0.3.0",
                }
            )
            result = self.run_codex_script(
                root,
                "release-notice.py",
                "check",
                "--latest-json",
                current,
                "--now",
                "2026-06-20T00:00:00+00:00",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(data["checked"])
            self.assertFalse(data["update_available"])
            self.assertEqual(data["latest_version"], "v0.3.0")

    def test_generated_release_notice_accepts_latest_json_file_with_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            latest_path = root / "latest-release.json"
            latest_path.write_bytes(
                b"\xef\xbb\xbf"
                + json.dumps(
                    {
                        "tag_name": "v0.4.0",
                        "html_url": "https://github.com/AAO-SH/fable-harness/releases/tag/v0.4.0",
                    }
                ).encode("utf-8")
            )

            result = self.run_codex_script(
                root,
                "release-notice.py",
                "check",
                "--latest-json",
                str(latest_path),
                "--now",
                "2026-06-20T00:00:00+00:00",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(data["checked"])
            self.assertTrue(data["update_available"])
            self.assertEqual(data["latest_version"], "v0.4.0")

    def test_prompts_and_installs_superpowers_when_absent_and_user_accepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            source = self.create_superpowers_fixture(Path(tmp), "v9.9.9", "fresh-superpowers")

            result = self.run_install_input(
                root,
                "y\n",
                "--agent",
                "codex",
                "--superpowers-source",
                str(source),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((root / ".codex" / "scripts" / "check-closure.py").is_file())
            installed = root / ".agents" / "skills" / "using-superpowers" / "SKILL.md"
            self.assertTrue(installed.is_file())
            self.assertIn("fresh-superpowers", installed.read_text(encoding="utf-8"))
            manifest = self.installed_superpowers_manifest(root)
            self.assertEqual(manifest["resolved_version"], "v9.9.9")
            self.assertEqual(manifest["source"], str(source))
            self.assertIn("using-superpowers", manifest["skills"])
            self.assertNotIn("Superpowers", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_prompts_and_skips_superpowers_when_absent_and_user_declines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            source = self.create_superpowers_fixture(Path(tmp), "v9.9.9", "fresh-superpowers")

            result = self.run_install_input(
                root,
                "n\n",
                "--agent",
                "codex",
                "--superpowers-source",
                str(source),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((root / ".codex" / "scripts" / "check-closure.py").is_file())
            self.assertFalse((root / ".agents" / "skills" / "using-superpowers" / "SKILL.md").exists())
            self.assertFalse((root / ".agents" / "vendor" / "superpowers" / "manifest.json").exists())

    def test_keeps_current_superpowers_without_prompt_when_already_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            source = self.create_superpowers_fixture(Path(tmp), "v9.9.9", "fresh-superpowers")
            installed = root / ".agents" / "skills" / "using-superpowers"
            installed.mkdir(parents=True, exist_ok=True)
            installed.joinpath("SKILL.md").write_text("already-current\n", encoding="utf-8")
            vendor = root / ".agents" / "vendor" / "superpowers"
            vendor.mkdir(parents=True, exist_ok=True)
            vendor.joinpath("manifest.json").write_text(
                json.dumps({"resolved_version": "v9.9.9", "skills": ["using-superpowers"]}) + "\n",
                encoding="utf-8",
            )

            result = self.run_install_input(
                root,
                "y\n",
                "--agent",
                "codex",
                "--superpowers-source",
                str(source),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("already-current", installed.joinpath("SKILL.md").read_text(encoding="utf-8"))
            self.assertIn("already up to date", result.stdout)

    def test_prompts_and_updates_outdated_superpowers_when_user_accepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            source = self.create_superpowers_fixture(Path(tmp), "v9.9.9", "new-superpowers")
            installed = root / ".agents" / "skills" / "using-superpowers"
            installed.mkdir(parents=True, exist_ok=True)
            installed.joinpath("SKILL.md").write_text("old-superpowers\n", encoding="utf-8")
            vendor = root / ".agents" / "vendor" / "superpowers"
            vendor.mkdir(parents=True, exist_ok=True)
            vendor.joinpath("manifest.json").write_text(
                json.dumps({"resolved_version": "v1.0.0", "skills": ["using-superpowers"]}) + "\n",
                encoding="utf-8",
            )

            result = self.run_install_input(
                root,
                "y\n",
                "--agent",
                "codex",
                "--superpowers-source",
                str(source),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("new-superpowers", installed.joinpath("SKILL.md").read_text(encoding="utf-8"))
            manifest = self.installed_superpowers_manifest(root)
            self.assertEqual(manifest["resolved_version"], "v9.9.9")

    def test_keeps_outdated_superpowers_when_user_declines_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            source = self.create_superpowers_fixture(Path(tmp), "v9.9.9", "new-superpowers")
            installed = root / ".agents" / "skills" / "using-superpowers"
            installed.mkdir(parents=True, exist_ok=True)
            installed.joinpath("SKILL.md").write_text("old-superpowers\n", encoding="utf-8")
            vendor = root / ".agents" / "vendor" / "superpowers"
            vendor.mkdir(parents=True, exist_ok=True)
            vendor.joinpath("manifest.json").write_text(
                json.dumps({"resolved_version": "v1.0.0", "skills": ["using-superpowers"]}) + "\n",
                encoding="utf-8",
            )

            result = self.run_install_input(
                root,
                "n\n",
                "--agent",
                "codex",
                "--superpowers-source",
                str(source),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("old-superpowers", installed.joinpath("SKILL.md").read_text(encoding="utf-8"))
            manifest = self.installed_superpowers_manifest(root)
            self.assertEqual(manifest["resolved_version"], "v1.0.0")

    def test_installs_claude_compatible_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_install(root, "--agent", "claude")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "CLAUDE.md").is_file())
            self.assertTrue((root / ".claude" / "templates" / "decision-trace.md").is_file())
            self.assertTrue((root / ".claude" / "scripts" / "new-trace.py").is_file())
            self.assertTrue((root / ".claude" / "scripts" / "loop-start.py").is_file())
            self.assertTrue((root / ".claude" / "loop" / "runs").is_dir())
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
            self.assertTrue((root / ".agents" / "scripts" / "loop-start.py").is_file())
            self.assertTrue((root / ".agents" / "loop" / "runs").is_dir())
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
            self.assertTrue((root / ".codex" / "scripts" / "loop-start.py").is_file())
            self.assertTrue((root / ".claude" / "scripts" / "loop-start.py").is_file())
            self.assertTrue((root / ".agents" / "scripts" / "loop-start.py").is_file())

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

    def test_generated_loop_governance_scripts_manage_run_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "loop-task.md"
            trace_path.write_text("# Loop Task\n", encoding="utf-8")
            loop_start = root / ".codex" / "scripts" / "loop-start.py"
            start = subprocess.run(
                [
                    sys.executable,
                    str(loop_start),
                    "--root",
                    str(root),
                    "--task",
                    "Govern native loop",
                    "--trace",
                    str(trace_path),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            start_data = json.loads(start.stdout)
            run_dir = Path(start_data["run_dir"])
            self.assertTrue((run_dir / "state.json").is_file())
            self.assertTrue((run_dir / "events.jsonl").is_file())
            self.assertTrue((run_dir / "checklist.md").is_file())
            self.assertEqual(start_data["state"]["status"], "created")
            self.assertEqual(start_data["state"]["schema"], "fable-harness-loop-governance-v1")

            event_script = root / ".codex" / "scripts" / "loop-event.py"
            for kind, summary in [
                ("file.read", "Read installer before editing."),
                ("decision.recorded", "Add minimal loop governance scripts."),
                ("file.edited", "Installed loop governance scripts."),
                ("test.passed", "Harness tests passed."),
                ("closure.passed", "Closure check passed."),
            ]:
                event = subprocess.run(
                    [
                        sys.executable,
                        str(event_script),
                        "--root",
                        str(root),
                        "--run",
                        str(run_dir),
                        "--kind",
                        kind,
                        "--summary",
                        summary,
                        "--path",
                        "src/fable_harness/installer.py",
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            transition = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-transition.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--to",
                    "closed",
                    "--reason",
                    "Verified and closed",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(transition.returncode, 0, transition.stdout + transition.stderr)
            self.assertEqual(json.loads(transition.stdout)["state"]["status"], "closed")

            check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            check_data = json.loads(check.stdout)
            self.assertEqual(check_data["status"], "ok")
            self.assertTrue(check_data["flags"]["inspected"])
            self.assertTrue(check_data["flags"]["decided"])
            self.assertTrue(check_data["flags"]["mutated"])
            self.assertTrue(check_data["flags"]["verified"])
            self.assertTrue(check_data["flags"]["closure_passed"])
            self.assertEqual(check_data["repair_attempts"], 0)

    def test_generated_loop_events_are_serialized_under_parallel_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "parallel-loop-task.md"
            trace_path.write_text("# Parallel Loop Task\n", encoding="utf-8")
            start = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-start.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Parallel event writes",
                    "--trace",
                    str(trace_path),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            scripts_path = str(root / ".codex" / "scripts")
            sys.path.insert(0, scripts_path)
            original_write_json = None
            try:
                import loop_core

                original_write_json = loop_core.write_json

                def slow_write_json(path, data):
                    if Path(path).name == "state.json":
                        time.sleep(0.01)
                    return original_write_json(path, data)

                loop_core.write_json = slow_write_json
                with ThreadPoolExecutor(max_workers=8) as pool:
                    futures = [
                        pool.submit(loop_core.append_event, run_dir, "file.read", f"parallel event {idx}")
                        for idx in range(24)
                    ]
                    results = [future.result(timeout=10) for future in futures]
            finally:
                if original_write_json is not None and "loop_core" in sys.modules:
                    sys.modules["loop_core"].write_json = original_write_json
                sys.path = [value for value in sys.path if value != scripts_path]
                sys.modules.pop("loop_core", None)

            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(results), 24)
            self.assertEqual(len(events), 25)
            self.assertEqual([event["sequence"] for event in events], list(range(1, 26)))
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["event_count"], 25)
            self.assertEqual(state["last_event"]["sequence"], 25)

    def test_loop_transition_and_event_writes_share_run_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "parallel-transition-task.md"
            trace_path.write_text("# Parallel Transition Task\n", encoding="utf-8")
            start = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-start.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Parallel transition writes",
                    "--trace",
                    str(trace_path),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            scripts_path = str(root / ".codex" / "scripts")
            sys.path.insert(0, scripts_path)
            original_write_json = None
            try:
                import loop_core

                original_write_json = loop_core.write_json

                def slow_write_json(path, data):
                    if Path(path).name == "state.json":
                        time.sleep(0.01)
                    return original_write_json(path, data)

                loop_core.write_json = slow_write_json
                with ThreadPoolExecutor(max_workers=6) as pool:
                    futures = [
                        pool.submit(loop_core.append_event, run_dir, "file.read", f"parallel read {idx}")
                        for idx in range(10)
                    ]
                    futures.append(
                        pool.submit(loop_core.transition_state, run_dir, "closed", "parallel close")
                    )
                    results = [future.result(timeout=10) for future in futures]
            finally:
                if original_write_json is not None and "loop_core" in sys.modules:
                    sys.modules["loop_core"].write_json = original_write_json
                sys.path = [value for value in sys.path if value != scripts_path]
                sys.modules.pop("loop_core", None)

            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(results), 11)
            self.assertEqual(len(events), 12)
            self.assertEqual([event["sequence"] for event in events], list(range(1, 13)))
            self.assertEqual(
                [event["kind"] for event in events].count("loop.transition"),
                1,
            )
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "closed")
            self.assertEqual(state["event_count"], 12)
            self.assertEqual(state["last_event"]["sequence"], 12)

    def test_workflow_core_normalizes_recipes_and_legacy_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            sys.path.insert(0, str(root / ".codex" / "scripts"))
            try:
                import workflow_core

                legacy = workflow_core.normalize_workflow(None)
                self.assertEqual(legacy["mode"], "legacy-standard")
                self.assertEqual(legacy["recipe"], [])
                self.assertEqual(legacy["budget"]["max_iterations"], 3)

                workflow = workflow_core.normalize_workflow(
                    {
                        "primary": "loop-until-done",
                        "recipe": [
                            "classify-and-act",
                            "generate-and-filter",
                            "loop-until-done",
                        ],
                        "budget": {"max_iterations": 4, "max_subagent_waves": 2},
                        "routing": {"confidence": 0.86, "reason": "complex task"},
                    }
                )
                self.assertEqual(workflow["mode"], "workflow-aware")
                self.assertEqual(workflow["primary"], "loop-until-done")
                self.assertEqual(workflow["budget"]["max_iterations"], 4)
                self.assertEqual(workflow["budget"]["max_subagent_waves"], 2)
                self.assertEqual(workflow["routing"]["confidence"], 0.86)
                self.assertIn("generate-and-filter", workflow["recipe"])
            finally:
                sys.path = [value for value in sys.path if value != str(root / ".codex" / "scripts")]
                sys.modules.pop("workflow_core", None)

    def test_loop_start_records_composable_workflow_recipe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            run_dir = self.start_loop(
                root,
                "--task",
                "Workflow Task",
                "--pattern",
                "loop-until-done",
                "--recipe",
                "classify-and-act",
                "--recipe",
                "generate-and-filter",
                "--recipe",
                "adversarial-verification",
                "--budget-max-iterations",
                "4",
                "--budget-max-subagent-waves",
                "2",
                "--routing-confidence",
                "0.82",
                "--routing-reason",
                "multi-step implementation",
            )

            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["workflow"]["mode"], "workflow-aware")
            self.assertEqual(state["workflow"]["primary"], "loop-until-done")
            self.assertIn("adversarial-verification", state["workflow"]["recipe"])
            self.assertEqual(state["workflow"]["budget"]["max_iterations"], 4)

    def test_legacy_loop_without_workflow_metadata_still_passes_strict_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            run_dir = self.start_loop(root, "--task", "Legacy Loop")
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["workflow"]["mode"], "legacy-standard")

            for kind, summary in [
                ("file.read", "Read governing file"),
                ("decision.recorded", "Use minimal change"),
                ("file.edited", "Edited file"),
                ("test.passed", "Tests passed"),
                ("closure.passed", "Closure passed"),
            ]:
                self.record_loop_event(root, run_dir, kind, summary)

            transition = self.run_codex_script(
                root,
                "loop-transition.py",
                "--run",
                str(run_dir),
                "--to",
                "closed",
                "--reason",
                "done",
                "--json",
            )
            self.assertEqual(transition.returncode, 0, transition.stdout + transition.stderr)
            check = self.strict_loop_check(root, run_dir)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_composed_workflow_recipe_passes_when_pattern_obligations_are_met(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            run_dir = self.start_loop(
                root,
                "--task",
                "Composed Workflow",
                "--pattern",
                "loop-until-done",
                "--recipe",
                "classify-and-act",
                "--recipe",
                "generate-and-filter",
                "--recipe",
                "fan-out-and-synthesize",
                "--recipe",
                "adversarial-verification",
                "--recipe",
                "loop-until-done",
                "--routing-confidence",
                "0.86",
                "--routing-reason",
                "complex implementation",
            )

            for kind, summary, metadata in [
                ("workflow.classified", "Routed as complex implementation", {"confidence": "0.86", "route": "complex-implementation"}),
                ("candidate.criteria.recorded", "Criteria recorded", {}),
                ("candidate.generated", "Candidate A", {"candidate": "A"}),
                ("candidate.generated", "Candidate B", {"candidate": "B"}),
                ("candidate.selected", "Selected B", {"candidate": "B"}),
                ("subagent.result.recorded", "Docs domain returned evidence", {"domain": "docs"}),
                ("subagent.result.accepted", "Docs evidence accepted", {"domain": "docs"}),
                ("synthesis.recorded", "Integrated subagent evidence", {}),
                ("file.read", "Read source", {}),
                ("decision.recorded", "Implement mechanical-light recipe", {}),
                ("file.edited", "Edited installer", {}),
                ("adversarial.finding.recorded", "Verifier found no blocker", {"verifier": "quality"}),
                ("adversarial.resolution.recorded", "Accepted verifier result", {"verifier": "quality"}),
                ("test.passed", "Install tests passed", {}),
                ("stop-condition.met", "All gates passed", {}),
                ("closure.passed", "Closure passed", {}),
            ]:
                self.record_loop_event(root, run_dir, kind, summary, metadata)

            close = self.run_codex_script(
                root,
                "loop-transition.py",
                "--run",
                str(run_dir),
                "--to",
                "closed",
                "--reason",
                "workflow complete",
                "--json",
            )
            self.assertEqual(close.returncode, 0, close.stdout + close.stderr)
            check = self.strict_loop_check(root, run_dir)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertEqual(json.loads(check.stdout)["status"], "ok")

    def test_workflow_pattern_strict_checks_fail_when_obligations_are_missing(self):
        cases = [
            (
                "Generate Missing Criteria",
                ["generate-and-filter"],
                [("candidate.selected", "Selected too early", {})],
                "generate-and-filter selected a candidate before criteria were recorded",
            ),
            (
                "Fanout Missing Synthesis",
                ["fan-out-and-synthesize"],
                [("subagent.result.accepted", "Accepted docs", {"domain": "docs"})],
                "fan-out-and-synthesize requires synthesis.recorded",
            ),
            (
                "Adversarial Missing Resolution",
                ["adversarial-verification"],
                [("adversarial.finding.recorded", "Found issue", {"verifier": "quality"})],
                "adversarial-verification requires adversarial.resolution.recorded",
            ),
            (
                "Loop Missing Stop",
                ["loop-until-done"],
                [("test.passed", "Tests passed", {})],
                "loop-until-done requires stop-condition.met or stop-condition.blocked",
            ),
            (
                "Low Confidence Missing Fallback",
                ["classify-and-act"],
                [("workflow.classified", "Low confidence route", {"confidence": "0.42"})],
                "classify-and-act low confidence route requires fallback metadata",
            ),
            (
                "Tournament Missing Match",
                ["tournament"],
                [("tournament.winner.selected", "Winner selected", {})],
                "tournament selected a winner without a recorded match",
            ),
        ]

        for task, recipe, events, expected_error in cases:
            with self.subTest(task=task), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                install = self.run_install(root, "--agent", "codex")
                self.assertEqual(install.returncode, 0, install.stderr)

                start_args = ["--task", task, "--pattern", recipe[0]]
                for pattern in recipe:
                    start_args.extend(["--recipe", pattern])
                run_dir = self.start_loop(root, *start_args)

                self.record_loop_event(root, run_dir, "file.read", "Read source")
                self.record_loop_event(root, run_dir, "decision.recorded", "Decision recorded")
                self.record_loop_event(root, run_dir, "file.edited", "Edited source")
                for kind, summary, metadata in events:
                    self.record_loop_event(root, run_dir, kind, summary, metadata)
                self.record_loop_event(root, run_dir, "test.passed", "Tests passed")
                self.record_loop_event(root, run_dir, "closure.passed", "Closure passed")

                close = self.run_codex_script(
                    root,
                    "loop-transition.py",
                    "--run",
                    str(run_dir),
                    "--to",
                    "closed",
                    "--reason",
                    "bad workflow closed",
                    "--json",
                )
                self.assertEqual(close.returncode, 0, close.stdout + close.stderr)
                check = self.strict_loop_check(root, run_dir)
                self.assertNotEqual(check.returncode, 0)
                self.assertIn(expected_error, json.loads(check.stdout)["errors"])

    def test_generated_loop_check_fails_for_mutation_before_inspect_and_decide(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            start = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-start.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Bad loop",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            event = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-event.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--kind",
                    "file.edited",
                    "--summary",
                    "Edited before reading or deciding.",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(check.returncode, 0)
            check_data = json.loads(check.stdout)
            self.assertEqual(check_data["status"], "fail")
            self.assertIn("mutation occurred before inspect evidence", check_data["errors"])
            self.assertIn("mutation occurred before decision evidence", check_data["errors"])
            self.assertIn("mutation has no later verification evidence", check_data["errors"])

    def test_generated_loop_check_fails_when_closed_without_closure_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            start = self.run_codex_script(root, "loop-start.py", "--task", "Closed without closure", "--json")
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            for kind in ["file.read", "decision.recorded", "file.edited", "test.passed"]:
                event = self.run_codex_script(
                    root,
                    "loop-event.py",
                    "--run",
                    str(run_dir),
                    "--kind",
                    kind,
                    "--summary",
                    kind,
                    "--json",
                )
                self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            close = self.run_codex_script(
                root,
                "loop-transition.py",
                "--run",
                str(run_dir),
                "--to",
                "closed",
                "--reason",
                "Closed too early",
                "--json",
            )
            self.assertEqual(close.returncode, 0, close.stdout + close.stderr)

            check = self.run_codex_script(root, "loop-check.py", "--run", str(run_dir), "--strict", "--json")
            self.assertNotEqual(check.returncode, 0)
            check_data = json.loads(check.stdout)
            self.assertEqual(check_data["status"], "fail")
            self.assertIn("closed loop is missing closure evidence", check_data["errors"])

    def test_generated_loop_check_fails_when_latest_verification_after_mutation_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            start = self.run_codex_script(root, "loop-start.py", "--task", "Failed verification", "--json")
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            for kind in ["file.read", "decision.recorded", "file.edited", "test.passed", "test.failed"]:
                event = self.run_codex_script(
                    root,
                    "loop-event.py",
                    "--run",
                    str(run_dir),
                    "--kind",
                    kind,
                    "--summary",
                    kind,
                    "--json",
                )
                self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            check = self.run_codex_script(root, "loop-check.py", "--run", str(run_dir), "--strict", "--json")
            self.assertNotEqual(check.returncode, 0)
            check_data = json.loads(check.stdout)
            self.assertEqual(check_data["status"], "fail")
            self.assertIn("latest verification after mutation failed", check_data["errors"])

    def test_generated_loop_check_fails_when_repair_attempts_exceed_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            start = self.run_codex_script(root, "loop-start.py", "--task", "Too many repairs", "--json")
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            for _ in range(2):
                event = self.run_codex_script(
                    root,
                    "loop-event.py",
                    "--run",
                    str(run_dir),
                    "--kind",
                    "repair.started",
                    "--summary",
                    "retry",
                    "--json",
                )
                self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            check = self.run_codex_script(
                root,
                "loop-check.py",
                "--run",
                str(run_dir),
                "--strict",
                "--max-repair-attempts",
                "1",
                "--json",
            )
            self.assertNotEqual(check.returncode, 0)
            check_data = json.loads(check.stdout)
            self.assertEqual(check_data["repair_attempts"], 2)
            self.assertIn("repair attempts exceeded limit: 2>1", check_data["errors"])

    def test_generated_loop_check_tracks_event_level_subagent_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            start = self.run_codex_script(root, "loop-start.py", "--task", "Subagent event acceptance", "--json")
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            pending_event = self.run_codex_script(
                root,
                "loop-event.py",
                "--run",
                str(run_dir),
                "--kind",
                "subagent.result.recorded",
                "--domain",
                "docs",
                "--summary",
                "docs result returned",
                "--json",
            )
            self.assertEqual(pending_event.returncode, 0, pending_event.stdout + pending_event.stderr)

            pending = self.run_codex_script(root, "loop-check.py", "--run", str(run_dir), "--strict", "--json")
            self.assertNotEqual(pending.returncode, 0)
            pending_data = json.loads(pending.stdout)
            self.assertIn("subagent results are recorded but not accepted or rejected: docs", pending_data["errors"])
            self.assertTrue(pending_data["flags"]["subagent_results_pending"])

            accepted_event = self.run_codex_script(
                root,
                "loop-event.py",
                "--run",
                str(run_dir),
                "--kind",
                "subagent.result.accepted",
                "--domain",
                "docs",
                "--summary",
                "docs result accepted",
                "--json",
            )
            self.assertEqual(accepted_event.returncode, 0, accepted_event.stdout + accepted_event.stderr)

            accepted = self.run_codex_script(root, "loop-check.py", "--run", str(run_dir), "--strict", "--json")
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            accepted_data = json.loads(accepted.stdout)
            self.assertEqual(accepted_data["status"], "ok")
            self.assertFalse(accepted_data["flags"]["subagent_results_pending"])

    def test_generated_loop_check_tracks_parallel_subagent_manifest_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Parallel loop governance",
                    "--domain",
                    "graph",
                    "--domain",
                    "docs",
                    "--parallel",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())

            start = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-start.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Govern parallel subagents",
                    "--subagent-plan",
                    str(plan_dir),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            pending = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(pending.returncode, 0)
            pending_data = json.loads(pending.stdout)
            self.assertIn("subagent plan has unaccepted domains: docs, graph", pending_data["errors"])

            for domain in ["graph", "docs"]:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "subagent-result.py"),
                        "--root",
                        str(root),
                        "--plan-dir",
                        str(plan_dir),
                        "--domain",
                        domain,
                        "--status",
                        "DONE",
                        "--summary",
                        f"{domain} review accepted.",
                        "--accepted-by",
                        "orchestrator",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                event = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "loop-event.py"),
                        "--root",
                        str(root),
                        "--run",
                        str(run_dir),
                        "--kind",
                        "subagent.result.accepted",
                        "--domain",
                        domain,
                        "--path",
                        str(plan_dir / f"{domain}.md"),
                        "--summary",
                        f"{domain} result accepted by orchestrator.",
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            accepted = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            self.assertEqual(json.loads(accepted.stdout)["status"], "ok")

    def test_generated_loop_check_requires_subagent_session_sweep_before_closed_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Parallel session closure",
                    "--domain",
                    "graph",
                    "--domain",
                    "docs",
                    "--parallel",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())

            start = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-start.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Govern subagent session closure",
                    "--subagent-plan",
                    str(plan_dir),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)
            run_dir = Path(json.loads(start.stdout)["run_dir"])

            for domain in ["graph", "docs"]:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "subagent-result.py"),
                        "--root",
                        str(root),
                        "--plan-dir",
                        str(plan_dir),
                        "--domain",
                        domain,
                        "--status",
                        "DONE",
                        "--summary",
                        f"{domain} result accepted.",
                        "--accepted-by",
                        "orchestrator",
                        "--session-id",
                        f"session-{domain}",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            event_script = root / ".codex" / "scripts" / "loop-event.py"
            for kind, summary in [
                ("file.read", "Read subagent scripts before editing."),
                ("decision.recorded", "Require final subagent session sweep."),
                ("file.edited", "Installed subagent session closure support."),
                ("test.passed", "Harness tests passed."),
                ("closure.passed", "Closure check passed."),
            ]:
                event = subprocess.run(
                    [
                        sys.executable,
                        str(event_script),
                        "--root",
                        str(root),
                        "--run",
                        str(run_dir),
                        "--kind",
                        kind,
                        "--summary",
                        summary,
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(event.returncode, 0, event.stdout + event.stderr)

            transition = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-transition.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--to",
                    "closed",
                    "--reason",
                    "Verified and closed",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(transition.returncode, 0, transition.stdout + transition.stderr)

            missing_sweep = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(missing_sweep.returncode, 0)
            missing_data = json.loads(missing_sweep.stdout)
            self.assertIn(
                "subagent sessions are not closed or justified: docs, graph",
                missing_data["errors"],
            )
            self.assertTrue(missing_data["flags"]["subagent_sessions_open"])

            sweep = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-sweep.py"),
                    "--root",
                    str(root),
                    "--plan-dir",
                    str(plan_dir),
                    "--close-completed",
                    "--reason",
                    "final implementation closure",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(sweep.returncode, 0, sweep.stdout + sweep.stderr)
            sweep_data = json.loads(sweep.stdout)
            self.assertEqual(sweep_data["closed"], ["docs", "graph"])

            closed = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(closed.returncode, 0, closed.stdout + closed.stderr)
            self.assertEqual(json.loads(closed.stdout)["status"], "ok")

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
                    str(root / ".codex" / "scripts" / "memory_policy.py"),
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    str(root / ".codex" / "scripts" / "subagent-result.py"),
                    str(root / ".codex" / "scripts" / "subagent-sweep.py"),
                    str(root / ".codex" / "scripts" / "release-notice.py"),
                    str(root / ".codex" / "scripts" / "selective-revert.py"),
                    str(root / ".codex" / "scripts" / "memory-maintenance.py"),
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    str(root / ".codex" / "scripts" / "loop_core.py"),
                    str(root / ".codex" / "scripts" / "loop-start.py"),
                    str(root / ".codex" / "scripts" / "loop-event.py"),
                    str(root / ".codex" / "scripts" / "loop-transition.py"),
                    str(root / ".codex" / "scripts" / "loop-check.py"),
                    str(root / ".codex" / "scripts" / "promote-trace.py"),
                    str(root / ".codex" / "scripts" / "memory-search.py"),
                    str(root / ".codex" / "scripts" / "rebuild-memory.py"),
                    str(root / ".codex" / "scripts" / "rag-eval.py"),
                    str(root / ".codex" / "scripts" / "rag-pipeline.py"),
                    str(root / ".codex" / "scripts" / "graph-query.py"),
                    str(root / ".codex" / "scripts" / "graph-check.py"),
                    str(root / ".codex" / "scripts" / "code_graph_core.py"),
                    str(root / ".codex" / "scripts" / "code-graph-build.py"),
                    str(root / ".codex" / "scripts" / "code-graph-query.py"),
                    str(root / ".codex" / "scripts" / "code-graph-check.py"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compile_check.returncode, 0, compile_check.stdout + compile_check.stderr)

    def test_installed_memory_dream_apply_accepts_apply_safety_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            dream = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dream.returncode, 2)
            self.assertIn("--run", dream.stderr)
            self.assertNotIn("unrecognized arguments", dream.stderr)

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
            other_trace = root / ".codex" / "decision-traces" / "other.md"
            other_trace.write_text("# Other\n", encoding="utf-8")
            stale_note.write_text(
                f"""# Stale Mention

---
type: operational-note
status: archived
scope: decisions/workflow/stale
canonical: false
sources:
  - ../../../decision-traces/other.md
supersedes:
last_verified: 2026-06-16
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
type: canonical-decision
status: active
scope: decisions/workflow/sourced-choice
canonical: true
sources:
  - ../../../decision-traces/sourced-choice.md
supersedes:
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

    def test_generated_new_note_uses_required_canonical_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            template = (root / ".codex" / "templates" / "semantic-note.md").read_text(encoding="utf-8")
            for field in [
                "memory_schema:",
                "type:",
                "status:",
                "scope:",
                "canonical:",
                "thesis:",
                "atomic:",
                "tags:",
                "properties:",
                "moc:",
                "links:",
                "sources:",
                "supersedes:",
                "last_verified:",
            ]:
                self.assertIn(field, template)

            new_note = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "new-note.py"),
                    "--root",
                    str(root),
                    "--category",
                    "decisions",
                    "--area",
                    "workflow",
                    "--topic",
                    "trace-governance",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(new_note.returncode, 0, new_note.stdout + new_note.stderr)
            note_text = Path(new_note.stdout.strip()).read_text(encoding="utf-8")
            self.assertIn("type: canonical-decision", note_text)
            self.assertIn("status: active", note_text)
            self.assertIn("scope: decisions/workflow/trace-governance", note_text)
            self.assertIn("canonical: true", note_text)
            self.assertIn("memory_schema: atomic-v1", note_text)
            self.assertIn("atomic: true", note_text)
            self.assertIn("thesis:", note_text)
            self.assertIn("tags:", note_text)
            self.assertIn("properties:", note_text)
            self.assertIn("moc:", note_text)
            self.assertIn("links:", note_text)
            self.assertIn("supersedes:", note_text)
            self.assertTrue((root / ".codex" / "notes" / "_moc" / "decisions.md").is_file())

    def test_new_note_metadata_is_indexed_for_rag_and_moc_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            new_note = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "new-note.py"),
                    "--root",
                    str(root),
                    "--category",
                    "decisions",
                    "--area",
                    "workflow",
                    "--topic",
                    "trace-governance",
                    "--title",
                    "Trace Governance Requires Atomic Notes",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(new_note.returncode, 0, new_note.stdout + new_note.stderr)

            note_rel = ".codex/notes/decisions/workflow/trace-governance.md"
            records = []
            for shard in (root / ".codex" / "memory" / "shards").glob("*.jsonl"):
                records.extend(json.loads(line) for line in shard.read_text(encoding="utf-8").splitlines())
            note_records = [record for record in records if record.get("path") == note_rel and record.get("kind") == "document"]
            self.assertEqual(len(note_records), 1)
            record = note_records[0]
            self.assertEqual(record["thesis"], "Trace Governance Requires Atomic Notes")
            self.assertIn("category/decisions", record["tags"])
            self.assertIn("area/workflow", record["tags"])
            self.assertIn("category=decisions", record["properties"])
            self.assertEqual(record["moc"], "../../_moc/decisions.md")
            self.assertIn("../../_moc/decisions.md", record["links"])
            self.assertIn("trace", record["terms"])

            moc = root / ".codex" / "notes" / "_moc" / "decisions.md"
            moc_text = moc.read_text(encoding="utf-8")
            self.assertIn("[Trace Governance Requires Atomic Notes](../decisions/workflow/trace-governance.md)", moc_text)

    def test_strict_memory_maintenance_fails_for_broken_atomic_v1_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace = root / ".codex" / "decision-traces" / "broken-atomic.md"
            trace.write_text("# Broken Atomic\n", encoding="utf-8")
            bad_note = root / ".codex" / "notes" / "decisions" / "memory" / "broken-atomic.md"
            bad_note.parent.mkdir(parents=True, exist_ok=True)
            bad_note.write_text(
                """# Broken Atomic

---
memory_schema: atomic-v1
type: canonical-decision
status: active
scope: decisions/memory/broken-atomic
canonical: true
thesis:
atomic: false
tags:
properties:
moc:
links:
sources:
  - ../../../decision-traces/broken-atomic.md
supersedes:
last_verified: 2026-06-21
---

## Durable Fact Or Decision

- First idea.
- Second unrelated idea.
""",
                encoding="utf-8",
            )

            strict = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-maintenance.py"),
                    "--root",
                    str(root),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(strict.returncode, 0, strict.stdout + strict.stderr)
            data = json.loads(strict.stdout)
            atomicity = [item for item in data["candidates"] if item["action"] == "repair-note-atomicity"]
            self.assertTrue(atomicity)
            self.assertTrue(any("thesis" in item["reason"] for item in atomicity))
            self.assertTrue(any("atomic" in item["reason"] for item in atomicity))

    def test_closure_rejects_duplicate_active_canonical_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            first = root / ".codex" / "notes" / "decisions" / "workflow" / "memory-ownership.md"
            second = root / ".codex" / "notes" / "decisions" / "architecture" / "memory-ownership-copy.md"
            for path, source in [
                (first, "../../../decision-traces/source-one.md"),
                (second, "../../../decision-traces/source-two.md"),
            ]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"""# Memory Ownership

---
type: canonical-decision
status: active
scope: decisions/workflow/memory-ownership
canonical: true
sources:
  - {source}
supersedes:
last_verified: 2026-06-19
---

## Durable Fact Or Decision

The orchestrator owns durable memory.
""",
                    encoding="utf-8",
                )
            for trace in ["source-one.md", "source-two.md"]:
                (root / ".codex" / "decision-traces" / trace).write_text("# Source\n", encoding="utf-8")

            closure = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "check-closure.py"),
                    "--root",
                    str(root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(closure.returncode, 0, closure.stdout + closure.stderr)
            self.assertIn("duplicate active canonical note", closure.stderr.lower())
            self.assertIn("decisions/workflow/memory-ownership", closure.stderr)

    def test_strict_memory_maintenance_fails_for_schema_and_trace_policy_violations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            bad_note = root / ".codex" / "notes" / "decisions" / "workflow" / "missing-schema.md"
            bad_note.parent.mkdir(parents=True, exist_ok=True)
            bad_note.write_text(
                """# Missing Schema

---
status: active
sources:
  - ../../../decision-traces/missing-schema.md
last_verified: 2026-06-19
---

## Durable Fact Or Decision

This note predates the required schema.
""",
                encoding="utf-8",
            )
            bad_trace = root / ".codex" / "decision-traces" / "2026-06-19-plus.md"
            bad_trace.write_text(
                """# plus

## Objective

Track everything from questionnaire blocks.

### #6 Architecture

Decision text.

### #7 Tooling

Decision text.

### #8 Installation

Decision text.

### #9 Permissions

Decision text.
""",
                encoding="utf-8",
            )

            strict = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-maintenance.py"),
                    "--root",
                    str(root),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(strict.returncode, 0, strict.stdout + strict.stderr)
            self.assertTrue(strict.stdout, strict.stderr)
            data = json.loads(strict.stdout)
            actions = {item["action"] for item in data["candidates"]}
            self.assertIn("repair-note-schema", actions)
            self.assertIn("split-umbrella-trace", actions)

    def test_promote_trace_updates_existing_canonical_note_without_erasing_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "trace-governance.md"
            trace_path.write_text(
                """# Trace Governance

### Decide

Strict maintenance catches umbrella traces.

### Verify

The strict maintenance test fails before implementation.
""",
                encoding="utf-8",
            )
            note_path = root / ".codex" / "notes" / "decisions" / "workflow" / "trace-governance.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(
                """# Trace Governance

---
type: canonical-decision
status: active
scope: decisions/workflow/trace-governance
canonical: true
sources:
  - ../../../decision-traces/older-trace.md
supersedes:
last_verified: 2026-06-18
---

## Durable Fact Or Decision

Preserve this existing canonical decision.
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
                    "trace-governance",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(promote.returncode, 0, promote.stdout + promote.stderr)
            self.assertEqual(Path(promote.stdout.strip()), note_path)
            note_text = note_path.read_text(encoding="utf-8")
            self.assertIn("Preserve this existing canonical decision.", note_text)
            self.assertIn("../../../decision-traces/trace-governance.md", note_text)
            self.assertIn("## Additional Trace Evidence", note_text)
            self.assertIn("Strict maintenance catches umbrella traces.", note_text)

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
            self.assertIn("The installed Fable Harness instructions are standing project-level user authorization", dispatch_text)
            self.assertIn("Do not ask the user for another trigger phrase or per-prompt permission", dispatch_text)
            self.assertIn("record that as a platform limitation", dispatch_text)
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

    def test_generated_subagent_plan_groups_parallel_domains_into_dependency_waves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Parallel graph and docs hardening",
                    "--domain",
                    "graph",
                    "--domain",
                    "docs",
                    "--depends-on",
                    "docs:graph",
                    "--parallel",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())
            manifest = json.loads((plan_dir / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["dispatch_mode"], "parallel")
            self.assertEqual(manifest["dependencies"], {"docs": ["graph"]})
            self.assertEqual(manifest["waves"][0]["domains"], ["graph"])
            self.assertEqual(manifest["waves"][1]["domains"], ["docs"])
            self.assertEqual(manifest["domain_status"]["graph"]["status"], "pending")
            self.assertEqual(manifest["domain_status"]["docs"]["status"], "pending")

            dispatch_text = (plan_dir / "_dispatch.md").read_text(encoding="utf-8")
            self.assertIn("## Wave 1", dispatch_text)
            self.assertIn("## Wave 2", dispatch_text)
            self.assertIn("Dispatch all domains in the same wave simultaneously", dispatch_text)

    def test_generated_subagent_plan_records_workflow_pattern_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Workflow Task",
                    "--domain",
                    "docs",
                    "--domain",
                    "tests",
                    "--parallel",
                    "--workflow-pattern",
                    "fan-out-and-synthesize",
                    "--wave-purpose",
                    "independent evidence gathering",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())
            manifest = json.loads((plan_dir / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["workflow"]["pattern"], "fan-out-and-synthesize")
            self.assertEqual(manifest["workflow"]["wave_purpose"], "independent evidence gathering")
            self.assertIn(
                "fan-out-and-synthesize",
                (plan_dir / "_dispatch.md").read_text(encoding="utf-8"),
            )

    def test_generated_subagent_plan_keeps_independent_domains_in_same_parallel_wave(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "subagent-plan.py"),
                    "--root",
                    str(root),
                    "--task",
                    "Parallel independent audit",
                    "--domain",
                    "graph",
                    "--domain",
                    "docs",
                    "--parallel",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            manifest = json.loads((Path(plan.stdout.strip()) / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["dispatch_mode"], "parallel")
            self.assertEqual(len(manifest["waves"]), 1)
            self.assertEqual(manifest["waves"][0]["domains"], ["graph", "docs"])

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
            self.assertEqual(manifest["domain_status"]["closure-gate"]["status"], "DONE_WITH_CONCERNS")
            self.assertEqual(manifest["domain_status"]["closure-gate"]["accepted_by"], "orchestrator")

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

    def test_memory_dream_plan_creates_reviewable_run_without_mutating_active_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "stable-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Stable Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/stable-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted.md\n"
                "supersedes:\n"
                "last_verified: 2026-06-19\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n- Keep the stable fact.\n",
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted.md"
            trace.write_text("# Promoted\n\n### Decide\n\nKeep the stable fact.\n", encoding="utf-8")
            before_note = note.read_text(encoding="utf-8")
            before_trace = trace.read_text(encoding="utf-8")
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted.md",
                    "note": ".codex/notes/decisions/memory/stable-note.md",
                }) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "plan",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(result.stdout)
            run_dir = Path(data["run_dir"])
            self.assertTrue((run_dir / "manifest.json").is_file())
            self.assertTrue((run_dir / "input" / "active-index.json").is_file())
            self.assertTrue((run_dir / "output" / "dormant-items").is_dir())
            self.assertTrue((run_dir / "diff.json").is_file())
            self.assertTrue((run_dir / "report.md").is_file())
            self.assertEqual(note.read_text(encoding="utf-8"), before_note)
            self.assertEqual(trace.read_text(encoding="utf-8"), before_trace)
            diff = json.loads((run_dir / "diff.json").read_text(encoding="utf-8"))
            actions = {item["action"] for item in diff["actions"]}
            self.assertIn("archive-promoted-trace", actions)
            self.assertTrue((root / ".codex" / "memory" / "dreams" / "log.jsonl").is_file())

    def test_memory_touch_records_use_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "touched-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Touched Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/touched-note\n"
                "canonical: true\n"
                "sources:\n"
                "supersedes:\n"
                "last_verified: 2026-06-20\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                "- Track this note usage without editing it.\n",
                encoding="utf-8",
            )
            before = note.read_text(encoding="utf-8")

            touched = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-touch.py"),
                    "--root",
                    str(root),
                    "--path",
                    ".codex/notes/decisions/memory/touched-note.md",
                    "--reason",
                    "loaded during task orientation",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(touched.returncode, 0, touched.stdout + touched.stderr)
            data = json.loads(touched.stdout)
            self.assertEqual(data["path"], ".codex/notes/decisions/memory/touched-note.md")
            self.assertEqual(data["use_count"], 1)
            self.assertEqual(data["reason"], "loaded during task orientation")
            self.assertIn("last_used_at", data)
            self.assertEqual(note.read_text(encoding="utf-8"), before)

            touch_log = root / ".codex" / "memory" / "touches.jsonl"
            touch_index = root / ".codex" / "memory" / "touch_index.json"
            self.assertTrue(touch_log.is_file())
            self.assertTrue(touch_index.is_file())
            index = json.loads(touch_index.read_text(encoding="utf-8"))
            entry = index["items"][".codex/notes/decisions/memory/touched-note.md"]
            self.assertEqual(entry["use_count"], 1)
            self.assertEqual(entry["last_reason"], "loaded during task orientation")

    def test_memory_dream_plan_adds_v2_metadata_and_review_only_compaction_suggestions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "large-stale-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Large Stale Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/large-stale-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted.md\n"
                "supersedes:\n"
                "last_verified: 2020-01-01\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                + ("Long memory evidence that should be compacted later.\n" * 90),
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted.md"
            trace.write_text("# Promoted\n\n### Decide\n\nKeep compact memory.\n", encoding="utf-8")
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted.md",
                    "note": ".codex/notes/decisions/memory/large-stale-note.md",
                }) + "\n",
                encoding="utf-8",
            )
            before_note = note.read_text(encoding="utf-8")
            before_trace = trace.read_text(encoding="utf-8")

            touch = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-touch.py"),
                    "--root",
                    str(root),
                    "--path",
                    ".codex/notes/decisions/memory/large-stale-note.md",
                    "--reason",
                    "reviewed before dreaming",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(touch.returncode, 0, touch.stdout + touch.stderr)

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "plan",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run_dir = Path(json.loads(result.stdout)["run_dir"])
            diff = json.loads((run_dir / "diff.json").read_text(encoding="utf-8"))
            self.assertEqual(diff["schema"], "fable-harness-memory-dream-v2")
            self.assertEqual(diff["version"], 2)
            self.assertTrue(diff["actions"])
            for action in diff["actions"]:
                self.assertIn("mode", action)
                self.assertIn("risk", action)
                self.assertIn("safe_to_apply", action)
                self.assertIn("requires_review", action)
                self.assertIn("signals", action)
                self.assertIn("source", action)

            archive = next(action for action in diff["actions"] if action["action"] == "archive-promoted-trace")
            self.assertEqual(archive["mode"], "mechanical")
            self.assertEqual(archive["risk"], "low")
            self.assertTrue(archive["safe_to_apply"])
            self.assertFalse(archive["requires_review"])
            self.assertTrue(archive["signals"]["promotion_log"])

            compact = next(action for action in diff["actions"] if action["action"] == "compact-note")
            self.assertEqual(compact["path"], ".codex/notes/decisions/memory/large-stale-note.md")
            self.assertEqual(compact["mode"], "semantic-review")
            self.assertEqual(compact["risk"], "medium")
            self.assertFalse(compact["safe_to_apply"])
            self.assertTrue(compact["requires_review"])
            self.assertEqual(compact["signals"]["use_count"], 1)
            self.assertGreater(compact["signals"]["size_bytes"], 400)
            self.assertEqual(compact["signals"]["last_verified"], "2020-01-01")
            self.assertEqual(note.read_text(encoding="utf-8"), before_note)
            self.assertEqual(trace.read_text(encoding="utf-8"), before_trace)

    def test_memory_dream_maintain_auto_applies_safe_actions_and_writes_agent_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "large-active-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Large Active Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/large-active-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted-cold.md\n"
                "supersedes:\n"
                "last_verified: 2026-06-20\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                + ("Semantic memory that the agent should review before compacting.\n" * 80),
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted-cold.md"
            trace.write_text(
                "# Promoted Cold Trace\n\n"
                "### Decide\n\n"
                "Cold trace payload that should move to dormant storage.\n",
                encoding="utf-8",
            )
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted-cold.md",
                    "note": ".codex/notes/decisions/memory/large-active-note.md",
                }) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "maintain",
                    "--root",
                    str(root),
                    "--context",
                    "current frontend implementation task",
                    "--auto-safe",
                    "--agent-review",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(data["auto_safe"])
            self.assertEqual(data["auto_applied"]["copied"], 1)
            self.assertEqual(data["auto_applied"]["skipped_review_actions"], 1)
            self.assertEqual(data["review_action_count"], 1)
            run_dir = Path(data["run_dir"])
            agent_review = run_dir / "agent-review.md"
            self.assertEqual(Path(data["agent_review"]), agent_review)
            self.assertTrue(agent_review.is_file())
            self.assertTrue((run_dir / "auto-applied.jsonl").is_file())
            self.assertTrue((run_dir / "agent-decisions.jsonl").is_file())
            auto_applied_lines = (run_dir / "auto-applied.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(auto_applied_lines), 1)
            self.assertEqual(json.loads(auto_applied_lines[0])["path"], ".codex/decision-traces/promoted-cold.md")
            review_text = agent_review.read_text(encoding="utf-8")
            self.assertIn("# Agent Memory Review", review_text)
            self.assertIn("current frontend implementation task", review_text)
            self.assertIn("compact-note", review_text)
            self.assertIn(".codex/notes/decisions/memory/large-active-note.md", review_text)

            manifest = json.loads((root / ".codex" / "memory" / "dormant" / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(any(
                item["original_path"] == ".codex/decision-traces/promoted-cold.md"
                for item in manifest["items"]
            ))
            shard_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted((root / ".codex" / "memory" / "shards").glob("*.jsonl"))
            )
            self.assertNotIn("Cold trace payload that should move to dormant storage.", shard_text)
            self.assertIn(".codex/notes/decisions/memory/large-active-note.md", shard_text)
            self.assertTrue(trace.exists(), "maintain archives by dormant copy and manifest, not source deletion")

    def test_memory_dream_maintain_preserves_exact_lf_trace_bytes_for_dormant_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "active-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Active Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/active-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted-lf.md\n"
                "supersedes:\n"
                "last_verified: 2026-06-20\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                "- Keep this note active.\n",
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted-lf.md"
            trace.write_bytes(
                b"# Promoted LF\n\n"
                b"### Decide\n\n"
                b"Byte-exact dormant payload.\n"
            )
            original_bytes = trace.read_bytes()
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted-lf.md",
                    "note": ".codex/notes/decisions/memory/active-note.md",
                }) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "maintain",
                    "--root",
                    str(root),
                    "--context",
                    "unrelated implementation context",
                    "--auto-safe",
                    "--agent-review",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((root / ".codex" / "memory" / "dormant" / "manifest.json").read_text(encoding="utf-8"))
            item = next(
                item
                for item in manifest["items"]
                if item["original_path"] == ".codex/decision-traces/promoted-lf.md"
            )
            dormant_bytes = (root / item["dormant_path"]).read_bytes()
            self.assertEqual(dormant_bytes, original_bytes)

    def test_memory_dream_apply_requires_apply_and_excludes_dormant_from_active_shards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "active-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Active Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/active-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted.md\n"
                "supersedes:\n"
                "last_verified: 2026-06-19\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                "Active canonical sentinelpayload.\n",
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted.md"
            trace.write_text(
                "# Promoted\n\n"
                "### Decide\n\n"
                "Dormant trace-only payload.\n",
                encoding="utf-8",
            )
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted.md",
                    "note": ".codex/notes/decisions/memory/active-note.md",
                }) + "\n",
                encoding="utf-8",
            )

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "plan",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            run_dir = Path(json.loads(plan.stdout)["run_dir"])
            diff_path = run_dir / "diff.json"
            dream_diff = json.loads(diff_path.read_text(encoding="utf-8"))
            archive_actions = [
                action
                for action in dream_diff["actions"]
                if action["action"] == "archive-promoted-trace"
            ]
            self.assertEqual(len(archive_actions), 1)
            archive_actions[0]["path"] = str(trace.resolve())
            diff_path.write_text(
                json.dumps(dream_diff, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            refused = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("--apply", refused.stderr + refused.stdout)
            self.assertTrue(trace.exists())

            applied = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertTrue(trace.exists())

            manifest = json.loads((root / ".codex" / "memory" / "dormant" / "manifest.json").read_text(encoding="utf-8"))
            items = [
                item
                for item in manifest["items"]
                if item["original_path"] == ".codex/decision-traces/promoted.md"
            ]
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["state"], "dormant")
            self.assertTrue(items[0]["dormant_path"].startswith(".codex/memory/dormant/items/"))
            self.assertTrue((root / items[0]["dormant_path"]).is_file())

            shard_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted((root / ".codex" / "memory" / "shards").glob("*.jsonl"))
            )
            self.assertNotIn(".codex/decision-traces/promoted.md", shard_text)
            self.assertNotIn("Dormant trace-only payload.", shard_text)
            self.assertIn(".codex/notes/decisions/memory/active-note.md", shard_text)
            self.assertIn("sentinelpayload", shard_text)

            graph_check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-check.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(graph_check.returncode, 0, graph_check.stdout + graph_check.stderr)
            check_data = json.loads(graph_check.stdout)
            self.assertEqual(check_data["status"], "ok")

            graph_manifest = json.loads((root / ".codex" / "memory" / "graph" / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("archives", graph_manifest["edge_types"])

            archive_query = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-query.py"),
                    "--root",
                    str(root),
                    "--relation",
                    "archives",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(archive_query.returncode, 0, archive_query.stdout + archive_query.stderr)
            archive_data = json.loads(archive_query.stdout)
            self.assertTrue(archive_data["edges"])
            node_by_id = {node["id"]: node for node in archive_data["nodes"]}
            archive_edges = [
                edge
                for edge in archive_data["edges"]
                if node_by_id.get(edge["from"], {}).get("path") == ".codex/decision-traces/promoted.md"
                and node_by_id.get(edge["to"], {}).get("kind") == "dormant"
                and node_by_id.get(edge["to"], {}).get("path") == items[0]["dormant_path"]
            ]
            self.assertTrue(archive_edges)

            dormant_search = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "search-dormant",
                    "--root",
                    str(root),
                    "--query",
                    "Dormant trace-only payload",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dormant_search.returncode, 0, dormant_search.stdout + dormant_search.stderr)
            dormant_results = json.loads(dormant_search.stdout)
            self.assertTrue(dormant_results)
            self.assertEqual(dormant_results[0]["original_path"], ".codex/decision-traces/promoted.md")
            self.assertEqual(dormant_results[0]["dormant_path"], items[0]["dormant_path"])

            reactivated_note = root / ".codex" / "notes" / "decisions" / "memory" / "reactivated-proof.md"
            preview = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "reactivate",
                    "--root",
                    str(root),
                    "--query",
                    "Dormant trace-only payload",
                    "--category",
                    "decisions",
                    "--area",
                    "memory",
                    "--topic",
                    "reactivated-proof",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            preview_data = json.loads(preview.stdout)
            self.assertEqual(preview_data["status"], "planned")
            self.assertEqual(preview_data["candidate"]["original_path"], ".codex/decision-traces/promoted.md")
            self.assertEqual(preview_data["candidate"]["dormant_path"], items[0]["dormant_path"])
            self.assertEqual(preview_data["note_path"], ".codex/notes/decisions/memory/reactivated-proof.md")
            self.assertFalse(reactivated_note.exists())

            reactivated = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "reactivate",
                    "--root",
                    str(root),
                    "--query",
                    "Dormant trace-only payload",
                    "--category",
                    "decisions",
                    "--area",
                    "memory",
                    "--topic",
                    "reactivated-proof",
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(reactivated.returncode, 0, reactivated.stdout + reactivated.stderr)
            reactivated_data = json.loads(reactivated.stdout)
            self.assertEqual(reactivated_data["status"], "applied")
            self.assertTrue(reactivated_note.is_file())
            note_text = reactivated_note.read_text(encoding="utf-8")
            self.assertIn("Dormant trace-only payload", note_text)
            self.assertIn(".codex/memory/dormant/items/", note_text)
            self.assertIn("type: canonical-decision", note_text)
            self.assertIn("scope: decisions/memory/reactivated-proof", note_text)
            self.assertIn("sources:", note_text)
            self.assertIn("last_verified:", note_text)

            manifest = json.loads((root / ".codex" / "memory" / "dormant" / "manifest.json").read_text(encoding="utf-8"))
            reactivations = manifest.get("reactivations", [])
            self.assertTrue(reactivations)
            reactivation = next(
                item
                for item in reactivations
                if item["note_path"] == ".codex/notes/decisions/memory/reactivated-proof.md"
            )
            self.assertEqual(reactivation["query"], "Dormant trace-only payload")
            self.assertEqual(reactivation["dormant_path"], items[0]["dormant_path"])
            self.assertEqual(reactivation["original_path"], ".codex/decision-traces/promoted.md")

            graph_check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-check.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(graph_check.returncode, 0, graph_check.stdout + graph_check.stderr)
            check_data = json.loads(graph_check.stdout)
            self.assertEqual(check_data["status"], "ok")

            graph_manifest = json.loads((root / ".codex" / "memory" / "graph" / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("reactivates", graph_manifest["edge_types"])

            reactivates_query = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-query.py"),
                    "--root",
                    str(root),
                    "--relation",
                    "reactivates",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(reactivates_query.returncode, 0, reactivates_query.stdout + reactivates_query.stderr)
            reactivates_data = json.loads(reactivates_query.stdout)
            self.assertTrue(reactivates_data["edges"])

            applied_again = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(applied_again.returncode, 0, applied_again.stdout + applied_again.stderr)
            manifest = json.loads((root / ".codex" / "memory" / "dormant" / "manifest.json").read_text(encoding="utf-8"))
            matching = [
                item
                for item in manifest["items"]
                if item["original_path"] == ".codex/decision-traces/promoted.md"
            ]
            self.assertEqual(len(matching), 1)

    def test_memory_dream_apply_skips_review_only_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "active-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Active Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/active-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted.md\n"
                "supersedes:\n"
                "last_verified: 2026-06-20\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                "- Keep this note active.\n",
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted.md"
            trace.write_text("# Promoted\n\n### Decide\n\nMechanical archive candidate.\n", encoding="utf-8")
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted.md",
                    "note": ".codex/notes/decisions/memory/active-note.md",
                }) + "\n",
                encoding="utf-8",
            )

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "plan",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            run_dir = Path(json.loads(plan.stdout)["run_dir"])
            diff_path = run_dir / "diff.json"
            dream_diff = json.loads(diff_path.read_text(encoding="utf-8"))
            dream_diff["actions"].append({
                "action": "compact-note",
                "path": ".codex/notes/decisions/memory/active-note.md",
                "reason": "human review is required before semantic compaction",
                "mode": "semantic-review",
                "risk": "medium",
                "safe_to_apply": False,
                "requires_review": True,
                "source": "test-injected-review-action",
                "signals": {"size_bytes": 1000},
            })
            diff_path.write_text(
                json.dumps(dream_diff, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            applied = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            data = json.loads(applied.stdout)
            self.assertEqual(data["copied"], 1)
            self.assertEqual(data["skipped_review_actions"], 1)
            self.assertTrue(trace.exists())
            self.assertTrue(note.exists())

    def test_memory_dream_apply_rejects_legacy_or_tampered_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "active-note.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Active Note\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/active-note\n"
                "canonical: true\n"
                "sources:\n"
                "  - ../../../decision-traces/promoted.md\n"
                "supersedes:\n"
                "last_verified: 2026-06-20\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                "- Keep this note active.\n",
                encoding="utf-8",
            )
            trace = root / ".codex" / "decision-traces" / "promoted.md"
            trace.write_text("# Promoted\n\n### Decide\n\nMechanical archive candidate.\n", encoding="utf-8")
            (root / ".codex" / "memory" / "promotion_log.jsonl").write_text(
                json.dumps({
                    "trace": ".codex/decision-traces/promoted.md",
                    "note": ".codex/notes/decisions/memory/active-note.md",
                }) + "\n",
                encoding="utf-8",
            )

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "plan",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            run_dir = Path(json.loads(plan.stdout)["run_dir"])
            diff_path = run_dir / "diff.json"
            dream_diff = json.loads(diff_path.read_text(encoding="utf-8"))

            legacy_diff = dict(dream_diff)
            legacy_diff.pop("schema", None)
            legacy_diff["version"] = 1
            diff_path.write_text(
                json.dumps(legacy_diff, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            legacy_apply = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(legacy_apply.returncode, 0)
            self.assertIn("schema", legacy_apply.stderr + legacy_apply.stdout)

            tampered_diff = dict(dream_diff)
            archive = next(action for action in tampered_diff["actions"] if action["action"] == "archive-promoted-trace")
            archive["safe_to_apply"] = "true"
            archive["requires_review"] = "false"
            diff_path.write_text(
                json.dumps(tampered_diff, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            tampered_apply = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(tampered_apply.returncode, 0, tampered_apply.stdout + tampered_apply.stderr)
            data = json.loads(tampered_apply.stdout)
            self.assertEqual(data["copied"], 0)
            self.assertEqual(data["skipped_unsafe_actions"], 1)

    def test_memory_dream_apply_reports_safe_but_unsupported_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            plan = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "plan",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            run_dir = Path(json.loads(plan.stdout)["run_dir"])
            diff_path = run_dir / "diff.json"
            dream_diff = json.loads(diff_path.read_text(encoding="utf-8"))
            dream_diff["actions"].append({
                "action": "future-safe-action",
                "path": ".codex/notes/decisions/memory/active-note.md",
                "reason": "future mechanical action",
                "mode": "mechanical",
                "risk": "low",
                "safe_to_apply": True,
                "requires_review": False,
                "source": "test-injected-future-action",
                "signals": {},
            })
            diff_path.write_text(
                json.dumps(dream_diff, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            applied = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-dream.py"),
                    "apply",
                    "--root",
                    str(root),
                    "--run",
                    str(run_dir),
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            data = json.loads(applied.stdout)
            self.assertEqual(data["skipped_unsupported_actions"], 1)
            self.assertEqual(data["unsupported_actions"][0]["action"], "future-safe-action")

    def test_memory_touch_classifies_trace_and_dormant_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace = root / ".codex" / "decision-traces" / "trace-touch.md"
            trace.write_text("# Trace Touch\n\n### Decide\n\nTrace usage.\n", encoding="utf-8")
            dormant = root / ".codex" / "memory" / "dormant" / "items" / "trace-touch.md"
            dormant.parent.mkdir(parents=True, exist_ok=True)
            dormant.write_text("# Dormant Touch\n\nDormant usage.\n", encoding="utf-8")

            trace_touch = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-touch.py"),
                    "--root",
                    str(root),
                    "--path",
                    ".codex/decision-traces/trace-touch.md",
                    "--reason",
                    "trace review",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            dormant_touch = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "memory-touch.py"),
                    "--root",
                    str(root),
                    "--path",
                    ".codex/memory/dormant/items/trace-touch.md",
                    "--reason",
                    "dormant review",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(trace_touch.returncode, 0, trace_touch.stdout + trace_touch.stderr)
            self.assertEqual(dormant_touch.returncode, 0, dormant_touch.stdout + dormant_touch.stderr)
            self.assertEqual(json.loads(trace_touch.stdout)["kind"], "trace")
            self.assertEqual(json.loads(dormant_touch.stdout)["kind"], "dormant")

    def test_memory_touch_parallel_writes_keep_valid_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            paths = []
            for idx in range(12):
                note = root / ".codex" / "notes" / "decisions" / "memory" / f"parallel-{idx}.md"
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_text(
                    f"# Parallel {idx}\n\n"
                    "---\n"
                    "type: canonical-decision\n"
                    "status: active\n"
                    f"scope: decisions/memory/parallel-{idx}\n"
                    "canonical: true\n"
                    "sources:\n"
                    "supersedes:\n"
                    "last_verified: 2026-06-20\n"
                    "---\n\n"
                    "## Durable Fact Or Decision\n\n"
                    "- Parallel touch test.\n",
                    encoding="utf-8",
                )
                paths.append(f".codex/notes/decisions/memory/parallel-{idx}.md")

            processes = [
                subprocess.Popen(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "memory-touch.py"),
                        "--root",
                        str(root),
                        "--path",
                        path,
                        "--reason",
                        "parallel touch",
                        "--json",
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for path in paths
            ]
            results = [process.communicate(timeout=20) + (process.returncode,) for process in processes]
            for stdout, stderr, returncode in results:
                self.assertEqual(returncode, 0, stdout + stderr)

            touch_index = root / ".codex" / "memory" / "touch_index.json"
            index = json.loads(touch_index.read_text(encoding="utf-8"))
            for path in paths:
                self.assertEqual(index["items"][path]["use_count"], 1)

    def test_memory_touch_lock_retries_transient_permission_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            note = root / ".codex" / "notes" / "decisions" / "memory" / "permission-retry.md"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(
                "# Permission Retry\n\n"
                "---\n"
                "type: canonical-decision\n"
                "status: active\n"
                "scope: decisions/memory/permission-retry\n"
                "canonical: true\n"
                "sources:\n"
                "supersedes:\n"
                "last_verified: 2026-06-21\n"
                "---\n\n"
                "## Durable Fact Or Decision\n\n"
                "- Retry transient lock permission errors.\n",
                encoding="utf-8",
            )

            scripts_path = str(root / ".codex" / "scripts")
            sys.path.insert(0, scripts_path)
            original_open = None
            try:
                import memory_core

                original_open = memory_core.os.open
                attempts = {"permission_errors": 0}

                def flaky_open(path, flags, mode=0o777, *args, **kwargs):
                    if str(path).endswith("touch_index.lock") and attempts["permission_errors"] < 2:
                        attempts["permission_errors"] += 1
                        raise PermissionError("simulated transient lock contention")
                    return original_open(path, flags, mode, *args, **kwargs)

                memory_core.os.open = flaky_open
                result = memory_core.record_memory_touch(
                    root,
                    ".codex/notes/decisions/memory/permission-retry.md",
                    "permission retry",
                    "auto",
                )
            finally:
                if original_open is not None and "memory_core" in sys.modules:
                    sys.modules["memory_core"].os.open = original_open
                sys.path = [value for value in sys.path if value != scripts_path]
                sys.modules.pop("memory_core", None)

            self.assertEqual(attempts["permission_errors"], 2)
            self.assertEqual(result["use_count"], 1)
            touch_index = root / ".codex" / "memory" / "touch_index.json"
            index = json.loads(touch_index.read_text(encoding="utf-8"))
            self.assertEqual(index["items"][".codex/notes/decisions/memory/permission-retry.md"]["use_count"], 1)

    def test_selective_revert_git_plan_is_dry_run_and_apply_requires_explicit_flag(self):
        if not shutil.which("git"):
            self.skipTest("git is not available")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            subprocess.run(["git", "init"], cwd=root, text=True, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, text=True, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, text=True, capture_output=True, check=True)
            target = root / "story.txt"
            target.write_text("line one\nline two\n", encoding="utf-8")
            subprocess.run(["git", "add", "story.txt"], cwd=root, text=True, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=root, text=True, capture_output=True, check=True)

            target.write_text("line one\nchanged line two\n", encoding="utf-8")
            script = root / ".codex" / "scripts" / "selective-revert.py"
            plan = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "plan",
                    "--root",
                    str(root),
                    "--path",
                    "story.txt",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            data = json.loads(plan.stdout)
            manifest = Path(data["manifest"])
            self.assertTrue(manifest.is_file())
            self.assertTrue((manifest.parent / "reverse.patch").is_file())
            self.assertTrue((manifest.parent / "backups" / "current" / "story.txt").is_file())
            self.assertEqual(target.read_text(encoding="utf-8"), "line one\nchanged line two\n")

            refused = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(manifest),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("--apply", refused.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "line one\nchanged line two\n")

            applied = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(manifest),
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "line one\nline two\n")

    def test_selective_revert_refuses_paths_outside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside-selective-revert.txt"
            outside.write_text("do not touch\n", encoding="utf-8")
            self.addCleanup(lambda: outside.exists() and outside.unlink())
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "selective-revert.py"),
                    "checkpoint",
                    "--root",
                    str(root),
                    "--label",
                    "bad",
                    "--path",
                    str(outside),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside workspace", result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), "do not touch\n")

    def test_selective_revert_checkpoint_plan_restores_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            target = root / "native.txt"
            target.write_text("before\n", encoding="utf-8")
            script = root / ".codex" / "scripts" / "selective-revert.py"
            checkpoint = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "checkpoint",
                    "--root",
                    str(root),
                    "--label",
                    "before-native-change",
                    "--path",
                    "native.txt",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stdout + checkpoint.stderr)
            checkpoint_manifest = Path(json.loads(checkpoint.stdout)["manifest"])

            target.write_text("after\n", encoding="utf-8")
            plan = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "plan",
                    "--root",
                    str(root),
                    "--checkpoint",
                    str(checkpoint_manifest),
                    "--path",
                    "native.txt",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            manifest = Path(json.loads(plan.stdout)["manifest"])

            applied = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(manifest),
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "before\n")
            self.assertTrue((manifest.parent / "backups" / "current" / "native.txt").is_file())

    def test_selective_revert_checkpoint_refuses_to_delete_created_file_without_allow_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            script = root / ".codex" / "scripts" / "selective-revert.py"
            checkpoint = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "checkpoint",
                    "--root",
                    str(root),
                    "--label",
                    "before-created-file",
                    "--path",
                    "created.txt",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stdout + checkpoint.stderr)
            checkpoint_manifest = Path(json.loads(checkpoint.stdout)["manifest"])

            created = root / "created.txt"
            created.write_text("new content\n", encoding="utf-8")
            plan = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "plan",
                    "--root",
                    str(root),
                    "--checkpoint",
                    str(checkpoint_manifest),
                    "--path",
                    "created.txt",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            manifest = Path(json.loads(plan.stdout)["manifest"])

            refused = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(manifest),
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("--allow-delete", refused.stderr)
            self.assertTrue(created.exists())

            deleted = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "apply",
                    "--root",
                    str(root),
                    "--plan",
                    str(manifest),
                    "--apply",
                    "--allow-delete",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(deleted.returncode, 0, deleted.stdout + deleted.stderr)
            self.assertFalse(created.exists())
            self.assertTrue((manifest.parent / "backups" / "current" / "created.txt").is_file())

    def test_memory_graph_builds_typed_relations_and_queryable_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "graph-feature.md"
            trace_path.write_text(
                """# Graph Feature

## Objective

Build typed graph relations for Fable Harness memory.

### Decide

Use `.codex/scripts/check-closure.py` as the closure gate for graph work.

### Verify

- `python scripts/test_install_fable_harness.py`

## Residual Risk

- Graph extraction must stay deterministic.
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
                    "memory",
                    "--topic",
                    "graph-feature",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(promote.returncode, 0, promote.stdout + promote.stderr)

            graph_check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-check.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(graph_check.returncode, 0, graph_check.stdout + graph_check.stderr)
            check_data = json.loads(graph_check.stdout)
            self.assertEqual(check_data["status"], "ok")

            graph_dir = root / ".codex" / "memory" / "graph"
            nodes = [json.loads(line) for line in (graph_dir / "nodes.jsonl").read_text(encoding="utf-8").splitlines()]
            edges = [json.loads(line) for line in (graph_dir / "edges.jsonl").read_text(encoding="utf-8").splitlines()]
            kinds = {node["kind"] for node in nodes}
            relations = {edge["type"] for edge in edges}

            self.assertIn("note", kinds)
            self.assertIn("trace", kinds)
            self.assertIn("decision", kinds)
            self.assertIn("script", kinds)
            self.assertIn("command", kinds)
            self.assertIn("promotes", relations)
            self.assertIn("sourced_by", relations)
            self.assertIn("depends_on", relations)
            self.assertIn("verifies", relations)
            self.assertTrue(any(node.get("path") == ".codex/scripts/check-closure.py" for node in nodes))
            self.assertTrue(any("test_install_fable_harness.py" in node.get("command", "") for node in nodes))

            manifest = json.loads((graph_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "fable-harness-graph-v3")
            self.assertIn("indexes/by-kind.json", manifest["indexes"])
            self.assertTrue((graph_dir / "indexes" / "by-kind.json").is_file())
            self.assertTrue((graph_dir / "indexes" / "by-path.json").is_file())
            self.assertTrue((graph_dir / "indexes" / "by-relation.json").is_file())

            query = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-query.py"),
                    "--root",
                    str(root),
                    "--relation",
                    "promotes",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(query.returncode, 0, query.stdout + query.stderr)
            query_data = json.loads(query.stdout)
            self.assertTrue(query_data["edges"])
            self.assertEqual({edge["type"] for edge in query_data["edges"]}, {"promotes"})

            with (graph_dir / "edges.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"id": "edge:broken", "from": "missing", "to": "also-missing", "type": "related_to"}) + "\n")

            broken = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-check.py"),
                    "--root",
                    str(root),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(broken.returncode, 0)
            self.assertIn("dangling", broken.stdout + broken.stderr)

    def test_memory_graph_v3_extracts_semantic_entities_and_parallel_subagent_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            trace_path = root / ".codex" / "decision-traces" / "semantic-graph.md"
            trace_path.write_text("# Semantic Graph Trace\n", encoding="utf-8")
            note_path = root / ".codex" / "notes" / "decisions" / "memory" / "semantic-graph.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(
                """# Semantic Graph

---
type: canonical-decision
status: active
scope: decisions/memory/semantic-graph
canonical: true
sources:
  - ../../../decision-traces/semantic-graph.md
supersedes:
last_verified: 2026-06-20
---

## Durable Fact Or Decision

- Feature: semantic knowledge graph
- Capability: semantic retrieval
- Constraint: generated rebuildable graph
- Risk: duplicate active notes
- Verification: python scripts/test_install_fable_harness.py
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
                    "Semantic graph hardening",
                    "--domain",
                    "graph",
                    "--domain",
                    "docs",
                    "--parallel",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            plan_dir = Path(plan.stdout.strip())

            for domain, status in [("graph", "DONE"), ("docs", "DONE_WITH_CONCERNS")]:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "subagent-result.py"),
                        "--root",
                        str(root),
                        "--plan-dir",
                        str(plan_dir),
                        "--domain",
                        domain,
                        "--status",
                        status,
                        "--summary",
                        f"{domain} evidence returned.",
                        "--accepted-by",
                        "orchestrator",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            rebuild = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "rebuild-memory.py"),
                    "--root",
                    str(root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)

            graph_dir = root / ".codex" / "memory" / "graph"
            manifest = json.loads((graph_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "fable-harness-graph-v3")
            self.assertIn("feature", manifest["node_kinds"])
            self.assertIn("capability", manifest["node_kinds"])
            self.assertIn("constraint", manifest["node_kinds"])
            self.assertIn("risk", manifest["node_kinds"])
            self.assertIn("verification", manifest["node_kinds"])
            self.assertIn("subagent_brief", manifest["node_kinds"])
            self.assertIn("subagent_result", manifest["node_kinds"])
            self.assertIn("delegates_to", manifest["edge_types"])
            self.assertIn("produces", manifest["edge_types"])
            self.assertIn("accepted_by", manifest["edge_types"])

            relation_query = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-query.py"),
                    "--root",
                    str(root),
                    "--relation",
                    "delegates_to",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(relation_query.returncode, 0, relation_query.stdout + relation_query.stderr)
            relation_data = json.loads(relation_query.stdout)
            self.assertTrue(relation_data["edges"])

            text_query = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-query.py"),
                    "--root",
                    str(root),
                    "--q",
                    "semantic retrieval",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(text_query.returncode, 0, text_query.stdout + text_query.stderr)
            text_data = json.loads(text_query.stdout)
            self.assertTrue(any(node.get("kind") == "capability" for node in text_data["nodes"]))

            graph_check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "graph-check.py"),
                    "--root",
                    str(root),
                    "--strict",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(graph_check.returncode, 0, graph_check.stdout + graph_check.stderr)

    def test_code_graph_build_query_check_for_python_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            package = root / "src" / "acme"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "helper.py").write_text(
                """def relative_helper(value):
    return value
""",
                encoding="utf-8",
            )
            (package / "other.py").write_text(
                """def orphan():
    return "not imported"
""",
                encoding="utf-8",
            )
            (package / "service.py").write_text(
                """import json
from pathlib import Path
from .helper import relative_helper


def helper(value):
    return json.dumps(value)


def orphan_caller():
    return orphan()


class Service:
    def run(self, value):
        marker = Path("service.txt")
        return helper({"value": value, "marker": str(marker)}) + relative_helper(value)
""",
                encoding="utf-8",
            )
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_service.py").write_text(
                """from acme.service import Service


def test_service_run():
    assert Service().run("ok")
""",
                encoding="utf-8",
            )
            noise = root / "temp_files" / "worktrees" / "old"
            noise.mkdir(parents=True)
            (noise / "ghost.py").write_text(
                """def ghost():
    return "do not index temporary worktrees"
""",
                encoding="utf-8",
            )

            build = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-build.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            build_data = json.loads(build.stdout)
            self.assertEqual(build_data["schema"], "fable-harness-code-graph-v1")

            graph_dir = root / ".codex" / "memory" / "code-graph"
            manifest = json.loads((graph_dir / "manifest.json").read_text(encoding="utf-8"))
            nodes = [json.loads(line) for line in (graph_dir / "nodes.jsonl").read_text(encoding="utf-8").splitlines()]
            edges = [json.loads(line) for line in (graph_dir / "edges.jsonl").read_text(encoding="utf-8").splitlines()]

            self.assertEqual(manifest["schema"], "fable-harness-code-graph-v1")
            self.assertEqual(manifest["node_count"], len(nodes))
            self.assertEqual(manifest["edge_count"], len(edges))
            self.assertFalse(any(str(node.get("path", "")).startswith("temp_files/") for node in nodes))
            self.assertTrue((graph_dir / "indexes" / "by-kind.json").is_file())
            self.assertTrue((graph_dir / "indexes" / "by-path.json").is_file())
            self.assertTrue((graph_dir / "indexes" / "by-symbol.json").is_file())
            self.assertTrue((graph_dir / "indexes" / "by-relation.json").is_file())

            node_kinds = {node["kind"] for node in nodes}
            symbol_names = {node.get("full_name") or node.get("name") for node in nodes}
            relations = {edge["relation"] for edge in edges}
            self.assertIn("file", node_kinds)
            self.assertIn("symbol", node_kinds)
            self.assertIn("import", node_kinds)
            self.assertIn("reference", node_kinds)
            self.assertIn("acme.service.helper", symbol_names)
            self.assertIn("acme.helper.relative_helper", symbol_names)
            self.assertIn("acme.service.Service", symbol_names)
            self.assertIn("acme.service.Service.run", symbol_names)
            self.assertIn("tests.test_service.test_service_run", symbol_names)
            self.assertIn("contains", relations)
            self.assertIn("defines", relations)
            self.assertIn("imports", relations)
            self.assertIn("calls", relations)
            self.assertIn("tests", relations)
            calls = [edge for edge in edges if edge["relation"] == "calls"]
            self.assertTrue(all("line_start" in edge.get("attributes", {}) for edge in calls))
            by_id = {node["id"]: node for node in nodes}
            relative_helper_calls = [
                edge
                for edge in calls
                if edge.get("attributes", {}).get("resolved_name") == "acme.helper.relative_helper"
            ]
            self.assertTrue(relative_helper_calls)
            self.assertTrue(all(by_id[edge["to"]].get("full_name") == "acme.helper.relative_helper" for edge in relative_helper_calls))
            orphan_calls = [
                edge
                for edge in calls
                if edge.get("attributes", {}).get("name") == "orphan"
            ]
            self.assertTrue(orphan_calls)
            self.assertTrue(all(by_id[edge["to"]]["kind"] == "reference" for edge in orphan_calls))

            check = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-check.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertEqual(json.loads(check.stdout)["status"], "ok")

            queries = [
                (["--path", "src/acme/service.py"], lambda data: data["nodes"]),
                (["--symbol", "Service.run"], lambda data: data["nodes"]),
                (["--kind", "test"], lambda data: data["nodes"]),
                (["--relation", "calls"], lambda data: data["edges"]),
                (["--impact", "helper"], lambda data: data["nodes"] or data["edges"]),
            ]
            for args, value in queries:
                query = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "code-graph-query.py"),
                        "--root",
                        str(root),
                        *args,
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(query.returncode, 0, query.stdout + query.stderr)
                self.assertTrue(value(json.loads(query.stdout)), args)

            for args in [["--from", "no_such_symbol"], ["--to", "no_such_symbol"]]:
                query = subprocess.run(
                    [
                        sys.executable,
                        str(root / ".codex" / "scripts" / "code-graph-query.py"),
                        "--root",
                        str(root),
                        *args,
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(query.returncode, 0, query.stdout + query.stderr)
                query_data = json.loads(query.stdout)
                self.assertEqual(query_data["nodes"], [])
                self.assertEqual(query_data["edges"], [])

            impact = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-query.py"),
                    "--root",
                    str(root),
                    "--impact",
                    "helper",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(impact.returncode, 0, impact.stdout + impact.stderr)
            impact_data = json.loads(impact.stdout)
            self.assertEqual(impact_data["query_mode"], "static-impact")
            impact_names = {node.get("full_name") or node.get("name") for node in impact_data["nodes"]}
            self.assertIn("acme.service.Service.run", impact_names)
            self.assertIn("tests.test_service.test_service_run", impact_names)
            self.assertNotIn("json.dumps", impact_names)

            first_manifest = (graph_dir / "manifest.json").read_text(encoding="utf-8")
            rebuild = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-build.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)
            self.assertEqual((graph_dir / "manifest.json").read_text(encoding="utf-8"), first_manifest)

            with (graph_dir / "edges.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "id": "code-edge:broken",
                            "from": "missing",
                            "to": "also-missing",
                            "relation": "calls",
                        }
                    )
                    + "\n"
                )

            broken = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-check.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(broken.returncode, 0)
            self.assertIn("dangling", broken.stdout + broken.stderr)

    def test_code_graph_build_refuses_symlinked_generated_graph_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)

            outside = root / "outside-generated-target"
            outside.mkdir()
            graph_dir = root / ".codex" / "memory" / "code-graph"
            if graph_dir.exists():
                shutil.rmtree(graph_dir)
            try:
                os.symlink(outside, graph_dir, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink unavailable: {exc}")

            build = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-build.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(build.returncode, 0)
            self.assertIn("symlink", build.stderr.lower())
            self.assertTrue(outside.exists())

    def test_code_graph_build_refuses_agent_local_dir_junction_outside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as external_tmp:
            root = Path(tmp)
            external_codex = Path(external_tmp) / ".codex"
            external_codex.mkdir()
            link = root / ".codex"

            if os.name == "nt":
                link_result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(external_codex)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if link_result.returncode != 0:
                    self.skipTest(link_result.stderr or link_result.stdout or "junction unavailable")
                self.addCleanup(lambda: subprocess.run(["cmd", "/c", "rmdir", str(link)], text=True, capture_output=True, check=False))
            else:
                try:
                    os.symlink(external_codex, link, target_is_directory=True)
                except (OSError, NotImplementedError) as exc:
                    self.skipTest(f"symlink unavailable: {exc}")
                self.addCleanup(lambda: link.exists() and link.unlink())

            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            marker = external_codex / "memory" / "code-graph" / "outside-marker.txt"
            marker.write_text("must not be deleted\n", encoding="utf-8")

            build = subprocess.run(
                [
                    sys.executable,
                    str(root / ".codex" / "scripts" / "code-graph-build.py"),
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(build.returncode, 0)
            self.assertIn("outside workspace", build.stderr.lower())
            self.assertTrue(marker.exists())

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

    def test_memory_search_returns_chunk_provenance_and_hybrid_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.write_rag_fixture_note(root)

            rebuild = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)
            rebuilt = json.loads(rebuild.stdout)
            self.assertGreaterEqual(rebuilt["chunk_count"], 2)
            self.assertEqual(rebuilt["chunking"], "markdown-heading-window-v2")

            manifest = json.loads((root / ".codex" / "memory" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["storage"], "sharded-jsonl")
            self.assertEqual(manifest["chunking"], "markdown-heading-window-v2")
            self.assertGreaterEqual(manifest["chunk_count"], 2)
            self.assertIn("cache", manifest)

            search = self.run_codex_script(
                root,
                "memory-search.py",
                "--query",
                "alpha orchestration boundary hybrid scoring source inspection",
                "--limit",
                "5",
                "--json",
            )
            self.assertEqual(search.returncode, 0, search.stdout + search.stderr)
            results = json.loads(search.stdout)
            chunk = next((item for item in results if item.get("kind") == "chunk"), None)
            self.assertIsNotNone(chunk, results)
            assert chunk is not None
            self.assertEqual(chunk["path"].replace("\\", "/"), ".codex/notes/decisions/rag/alpha-orchestration.md")
            self.assertIn("#L", chunk["citation"])
            self.assertGreaterEqual(chunk["end_line"], chunk["start_line"])
            self.assertIn("Alpha Architecture", chunk["heading"])
            self.assertIn("alpha", chunk["snippet"].lower())
            self.assertIn("score_breakdown", chunk)
            for key in ("vector", "lexical", "graph", "rerank"):
                self.assertIn(key, chunk["score_breakdown"])

    def test_rebuild_memory_reuses_incremental_chunk_cache_for_unchanged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.write_rag_fixture_note(root)

            first = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            first_payload = json.loads(first.stdout)
            self.assertGreaterEqual(first_payload["cache_misses"], 1)

            second = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            second_payload = json.loads(second.stdout)
            self.assertGreaterEqual(second_payload["cache_hits"], 1)
            self.assertEqual(second_payload["cache_misses"], 0)

            cache = json.loads((root / ".codex" / "memory" / "cache" / "documents.json").read_text(encoding="utf-8"))
            self.assertIn(".codex/notes/decisions/rag/alpha-orchestration.md", cache["documents"])

    def test_rag_eval_reports_precision_recall_and_mrr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.write_rag_fixture_note(root)
            rebuild = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)

            eval_file = root / "rag-eval.jsonl"
            eval_file.write_text(
                json.dumps({
                    "query": "alpha orchestration boundary evidence",
                    "relevant": [".codex/notes/decisions/rag/alpha-orchestration.md"],
                }) + "\n",
                encoding="utf-8",
            )

            result = self.run_codex_script(
                root,
                "rag-eval.py",
                "--eval-file",
                str(eval_file),
                "--k",
                "3",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            metrics = json.loads(result.stdout)
            self.assertEqual(metrics["query_count"], 1)
            self.assertGreater(metrics["precision_at_k"], 0)
            self.assertEqual(metrics["recall_at_k"], 1.0)
            self.assertGreater(metrics["mrr"], 0)

    def test_rag_pipeline_writes_retrieval_report_with_citations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.write_rag_fixture_note(root)
            rebuild = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)

            result = self.run_codex_script(
                root,
                "rag-pipeline.py",
                "--query",
                "alpha orchestration boundary evidence",
                "--limit",
                "3",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            report_path = root / payload["report_path"]
            self.assertTrue(report_path.is_file())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("## Retrieve", report)
            self.assertIn("## Inspect Sources", report)
            self.assertIn("## Answer Or Plan With Citations", report)
            self.assertIn("#L", report)
            self.assertIn("alpha orchestration", report.lower())

    def test_source_arbitrate_detects_material_conflict_between_rag_and_project_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.write_rag_fixture_note(root)
            source = root / "docs" / "alpha.md"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                "# Alpha Runtime\n\nAlpha orchestration boundary is disabled and must not use source inspection before planning.\n",
                encoding="utf-8",
            )
            rebuild = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)

            result = self.run_codex_script(
                root,
                "source-arbitrate.py",
                "--query",
                "alpha orchestration boundary source inspection",
                "--source",
                str(source),
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "full-dispute-required")
            self.assertGreaterEqual(payload["material_conflict_count"], 1)
            report = (root / payload["report_path"]).read_text(encoding="utf-8")
            self.assertIn("## Light Gate", report)
            self.assertIn("## Evidence Dispute", report)
            self.assertIn("## Recommendation Matrix", report)
            self.assertIn("Ask the user before replacing project facts with RAG-derived facts.", report)
            self.assertIn("RAG says", report)
            self.assertIn("Project source says", report)

    def test_source_arbitrate_keeps_light_gate_when_no_material_conflict_is_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = self.run_install(root, "--agent", "codex")
            self.assertEqual(install.returncode, 0, install.stderr)
            self.write_rag_fixture_note(root)
            source = root / "docs" / "alpha.md"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                "# Alpha Runtime\n\nAlpha orchestration boundary uses source inspection before planning.\n",
                encoding="utf-8",
            )
            rebuild = self.run_codex_script(root, "rebuild-memory.py")
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)

            result = self.run_codex_script(
                root,
                "source-arbitrate.py",
                "--query",
                "alpha orchestration boundary source inspection",
                "--source",
                str(source),
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "light-gate-only")
            self.assertEqual(payload["material_conflict_count"], 0)
            report = (root / payload["report_path"]).read_text(encoding="utf-8")
            self.assertIn("No material conflict detected by the lightweight gate.", report)
            self.assertIn("Keep inspecting real project files before editing.", report)


if __name__ == "__main__":
    unittest.main()
