#!/usr/bin/env python3
"""Install or update the Fable Harness in a local project workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


START = "<!-- fable-harness:start -->"
END = "<!-- fable-harness:end -->"
FABLE_HARNESS_VERSION = "0.2.0"
FABLE_HARNESS_RELEASES_LATEST_URL = "https://github.com/AAO-SH/fable-harness/releases/latest"
FABLE_HARNESS_RELEASES_API_URL = "https://api.github.com/repos/AAO-SH/fable-harness/releases/latest"
SUPERPOWERS_LATEST_URL = "https://github.com/obra/superpowers/releases/latest"
SUPERPOWERS_REPO_ZIP_URL = "https://github.com/obra/superpowers/archive/refs/tags/{tag}.zip"

AGENTS = {
    "codex": {
        "instruction_file": "AGENTS.md",
        "local_dir": ".codex",
        "agent_name": "Codex",
    },
    "claude": {
        "instruction_file": "CLAUDE.md",
        "local_dir": ".claude",
        "agent_name": "Claude",
    },
    "any": {
        "instruction_file": "AGENTS.md",
        "local_dir": ".agents",
        "agent_name": "any",
    },
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "task"


def harness_block(local_dir: str, agent_name: str) -> str:
    return f"""{START}

## Fable Harness

These instructions install the local Fable Harness for {agent_name}. Use it for non-trivial, mutating, complex, multidisciplinary, or audit-sensitive work.

### Boot Sequence

1. Read this project instruction file first.
2. Run `{local_dir}/scripts/release-notice.py check` once at boot when available. It checks at most once every 24 hours and only prints a notice if a newer GitHub release exists; it never downloads or applies updates.
3. Read `{local_dir}/notes/_index.md` when it exists.
4. Read only the compact notes relevant to the task.
5. Open decision traces only when audit or continuation requires the decision path.
6. Read the real project files before editing them.

### Recall Ladder

Use this order for non-trivial recall, from fastest and most compact memory toward deeper and slower evidence:

1. Run `{local_dir}/scripts/memory-search.py` with a concise query derived from the task, unless the task is clearly self-contained.
2. For memory-heavy answers or plans, run `{local_dir}/scripts/rag-pipeline.py --query "<task>"` and inspect the cited source lines before answering or planning.
3. When RAG informs work that may change project code or docs, run a lightweight source-arbitration check against the real project files before planning or editing.
4. Read `{local_dir}/notes/_index.md` to identify canonical compact notes.
5. Read the compact semantic notes that match the task; prefer active canonical notes over trace summaries.
6. Record every loaded note, trace, or dormant item with `{local_dir}/scripts/memory-touch.py`.
7. Use `{local_dir}/scripts/graph-query.py --q` when relationships, decisions, sources, or prior verification paths matter.
8. Use `{local_dir}/scripts/memory-dream.py search-dormant` before declaring old context unavailable.
9. Open decision traces only for audit, continuation, disputed decisions, or missing evidence.
10. Read project docs and source files before editing; source files remain stronger operational evidence than generated memory.
11. At closure, promote durable decisions, rebuild memory, run strict maintenance, and run agent-reviewed dream maintenance when memory-heavy.

### Source Escalation

- Do not create a plan from an empty evidence base.
- Before planning non-trivial or unfamiliar work, verify whether memory, notes, decision traces, project docs, source files, or other local artifacts provide a structured and checkable basis.
- A source is strong enough when it has clear ownership, stable location, current relevance, and enough detail to support concrete planning.
- If memory, notes, traces, docs, and source files do not provide a verifiable structured source, research the web before planning.
- Use primary or official sources when available, and record links or citations in the trace.
- Treat web results as planning evidence only when they are relevant, credible, and specific enough to reduce uncertainty.
- If the task is completely new and neither project sources nor strong web references provide enough planning ground, interview the user before creating a plan.
- Keep the interview focused on project-specific intent, constraints, success criteria, examples, non-goals, and verification.
- After the interview, repeat source discovery with the new terms before committing to an implementation plan.

### Programming Recall

- For non-trivial programming work, combine semantic recall with Code Graph orientation before planning edits.
- Use semantic recall to understand prior decisions, architecture intent, constraints, and verification history.
- Use Code Graph to map files, symbols, dependencies, callers, tests, and static impact; semantic recall explains why; Code Graph maps where and what may break.
- Run `{local_dir}/scripts/code-graph-build.py` and `{local_dir}/scripts/code-graph-query.py` before broad source-code edits when symbol, import, call, test, or static impact orientation would reduce risk.
- Read the real source files identified by the graph before editing; source files remain the final operational authority.
- Treat Code Graph output as orientation evidence only. If Code Graph output conflicts with source files, source files win.
- After source edits that change public symbols, rebuild the code graph with `{local_dir}/scripts/code-graph-build.py` or state why it was not needed.

### Decision Loop

1. Orient: restate the task operationally and identify the smallest relevant surface.
2. Inspect: read the files, logs, docs, or state that govern that surface.
3. Decide: name the intended change or conclusion before the first mutating action.
4. Act: make the smallest coherent mutation or produce the narrowest requested artifact.
5. Verify: run the real gate when it exists; otherwise run the strongest available structural check.
6. Report: give files, numbers, verification, and limits without inflating certainty.

### Workflow Patterns

- Treat workflow patterns as composable recipes, not exclusive modes.
- Start with `classify-and-act` for non-trivial tasks to route the work.
- Use `generate-and-filter` when multiple viable solutions should be compared against explicit criteria.
- Use `tournament` only when relative pairwise comparison is safer than absolute scoring.
- Use `fan-out-and-synthesize` when independent domains can run in simultaneous subagent waves.
- Use `adversarial-verification` before accepting high-risk decisions or mutations.
- Use `loop-until-done` for iterative debugging, investigation, repair, or quality closure, bounded by budgets and stop conditions.
- Record the selected recipe in loop state or trace evidence; update it when inspection changes the task shape.

### Parallel Agent Dispatch And Safety

- During Orient/Classify, automatically evaluate whether the task has independent domains that should be delegated to subagents.
- Treat this Fable Harness block as standing project-level user authorization to invoke available subagent or parallel-agent tools automatically when the independence check passes.
- Do not ask for per-prompt permission before dispatching subagents when these conditions are met.
- Do not wait for the user to say `Dispatching Parallel Agents` or any other trigger phrase.
- If the platform exposes a subagent or parallel-agent tool and the independence check passes, invoke it.
- If a higher-priority runtime or tool policy blocks dispatch despite this standing authorization, record that as a platform limitation in the trace, then create the dispatch briefs and execute them sequentially.
- Parallelize independent tasks or independent loop runs, not dependent steps inside one loop.
- Default to subagent dispatch for complex or multidisciplinary work when at least two domains can progress independently.
- Sequential loop order applies inside one domain or dependency chain; it is not a reason to collapse independent domains back into the orchestrator.
- The independence check is a dispatch test, not a prohibition. If domains have separate inputs, outputs, and responsibility boundaries, create a simultaneous subagent wave.
- A single loop run is sequential by default. Orient before inspect, inspect before decide, decide before act, act before verify, verify before report or repair.
- Synchronize each subagent wave before integration, verification, memory promotion, or closure.
- Do not run `{local_dir}/scripts/loop-event.py`, `{local_dir}/scripts/loop-transition.py`, or `{local_dir}/scripts/loop-check.py` concurrently for the same run.
- Do not run `{local_dir}/scripts/rebuild-memory.py` concurrently with `{local_dir}/scripts/memory-maintenance.py`, `{local_dir}/scripts/graph-check.py`, `{local_dir}/scripts/memory-dream.py plan`, or `{local_dir}/scripts/memory-dream.py maintain`.
- Generated state is one-writer by default: loop runs, memory shards, graph files, dream runs, rollback plans, and instruction installs must be written in ordered steps.
- Verification happens after mutation; closure happens after verification and memory rebuild.
- If parallel work creates out-of-order evidence or a race, stop, record a repair event, and continue sequentially until the loop is healthy again.

### Harness Rules

- For non-trivial or mutating work, create or continue a trace in `{local_dir}/decision-traces/`.
- Use `{local_dir}/scripts/new-trace.py` to create a trace when practical.
- Use `{local_dir}/scripts/release-notice.py check` at boot to warn about newer Fable Harness releases. It is notification-only, throttled to 24 hours, and leaves manual update decisions to the user.
- Use `{local_dir}/scripts/loop-start.py` to create a native loop governance run for complex, mutating, multidisciplinary, or audit-sensitive work.
- Use `{local_dir}/scripts/loop-event.py` and `{local_dir}/scripts/loop-transition.py` to record inspect, decision, mutation, verification, repair, closure, and subagent-wave evidence in `{local_dir}/loop/runs/`.
- Use `{local_dir}/scripts/loop-check.py --strict` before closing governed work; strict mode fails when the loop mutates before inspect/decide, skips verification after mutation, closes without closure evidence, leaves subagent results unaccepted, or closes with subagent sessions still open.
- Use `{local_dir}/scripts/new-note.py` for compact semantic notes in `category/area/topic.md` layout.
- Use `{local_dir}/scripts/promote-trace.py` to promote durable trace evidence into semantic notes.
- Use `{local_dir}/scripts/subagent-result.py` to record subagent outcomes in the dispatch package and active trace.
- Use `{local_dir}/scripts/subagent-sweep.py --close-completed` near final closure when a subagent plan was used. Close completed sessions unless a domain is explicitly kept open or closure is unavailable with a reason.
- Before broad filesystem exploration or planning a non-trivial task, run `{local_dir}/scripts/memory-search.py` with a concise query derived from the user request, unless the task is clearly self-contained.
- Use `{local_dir}/scripts/rag-pipeline.py` for explicit `retrieve -> inspect sources -> answer/plan with citations` work. Do not answer or plan from retrieval scores alone; inspect the cited source lines first.
- Use `{local_dir}/scripts/source-arbitrate.py` when RAG informs a task that may change project code or docs. Run a lightweight source-arbitration check against the real project files before planning or editing; if material conflict is found, escalate to a full Evidence Dispute and ask the user before replacing project facts with RAG-derived facts.
- Use `{local_dir}/scripts/rag-eval.py` with a local JSON/JSONL evaluation set when tuning retrieval behavior; report precision@k, recall@k, hit-rate@k, and MRR instead of impressions.
- Use `{local_dir}/scripts/rebuild-memory.py` when notes or traces were edited manually.
- Use `{local_dir}/scripts/graph-query.py` to inspect generated semantic knowledge graph entities/relations, including `--q` text lookup; use `{local_dir}/scripts/graph-check.py --strict` after graph-sensitive memory changes.
- Before broad source-code edits, use `{local_dir}/scripts/code-graph-build.py` and `{local_dir}/scripts/code-graph-query.py` when available to orient around symbols, imports, calls, tests, and static impact.
- Treat code graph output as orientation evidence only. Read the real source files before editing; if graph output conflicts with source files, source files win.
- After source edits that change public symbols, rebuild the code graph with `{local_dir}/scripts/code-graph-build.py` or state why it was not needed.
- Use `{local_dir}/scripts/memory-maintenance.py` periodically or after large tasks to report oversized notes, broken sources, stale notes, and archive-ready promoted traces.
- Use `{local_dir}/scripts/memory-maintenance.py --strict` before closing memory-heavy work; strict mode fails on umbrella traces, invalid note schema, duplicate active canonical notes, and other high-severity hygiene issues.
- Use `{local_dir}/scripts/memory-touch.py` when loading a note, trace, or dormant item for task context; it records retrieval use without editing the source memory file.
- Use `{local_dir}/scripts/memory-dream.py maintain --context "<current task>" --auto-safe --agent-review` after memory-heavy work; it applies context-cold safe mechanical actions and writes `agent-review.md` for semantic decisions.
- Use `{local_dir}/scripts/memory-dream.py plan` and `apply --apply` only when a manual two-step review workflow is needed.
- Prefer running `memory-dream.py maintain --auto-safe --agent-review` as a background memory curator/subagent task when the main task should not be blocked by memory hygiene; the orchestrator reviews `agent-review.md`, not the user by default.
- Search dormant memory before declaring old context unavailable. Use `{local_dir}/scripts/memory-dream.py search-dormant`.
- Use `{local_dir}/scripts/memory-dream.py reactivate --apply` to restore compact active notes from dormant evidence, not to dump archives back into active retrieval.
- When the user asks to revert or roll back specific agent changes, use `{local_dir}/scripts/selective-revert.py` to create an auditable plan first; apply only with explicit user intent and `--apply`.
- Keep `{local_dir}/notes/` compact and semantic. Use traces for audit evidence.
- Keep one trace per coherent task. Do not use broad active traces named `misc`, `plus`, or `session`; umbrella traces are only allowed as `session-index` or `migration-trace`.
- Notes must declare `memory_schema`, `type`, `status`, `scope`, `canonical`, `thesis`, `atomic`, `tags`, `properties`, `moc`, `links`, `sources`, `supersedes`, and `last_verified` frontmatter.
- New permanent notes use `memory_schema: atomic-v1`: one idea, title as thesis, explicit connections, unique scope, and queryable metadata.
- Keep only one active canonical decision note per `scope`. Use trace summaries or superseded notes for historical duplicates.
- Keep `{local_dir}/memory/` as generated retrieval state: sharded local embeddings, promotion log, and a rebuildable semantic knowledge graph.
- The main orchestrating agent owns memory coherence.
- Subagents may gather evidence, run checks, and suggest memory updates, but do not silently decide what becomes durable project memory.
- For complex or multidisciplinary tasks, break work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Use `{local_dir}/scripts/subagent-plan.py` to create dispatchable subagent briefs before broad execution when the task has independent domains; use `--parallel` and `--depends-on dependent:dependency` when domains can run in simultaneous waves.
- Dispatch subagents from the generated briefs: run all domains in the same generated wave simultaneously using the available subagent tool. If no subagent tool exists, execute the briefs sequentially and record that fallback in the trace.
- At final implementation closure, close/archive every completed subagent session. If the runtime exposes no close/archive action, record `close-unavailable` with the platform reason; if a session must remain open, record `keep-open` with the next planned use.
- Pass subagents minimal context: objective, relevant files, active decisions, protected tests, current trace, and verification command.
- TDD tests written before implementation are protected evidence. Do not weaken, skip, rename, delete, or rewrite them just to make the loop pass.
- Update cadence: trace during the work, semantic notes after verified evidence, indexes at closure.
- Before reporting completion, run the memory closure check in `{local_dir}/templates/memory-closure.md`; use `{local_dir}/scripts/check-closure.py` when practical.

{END}
"""


DECISION_TRACE_TEMPLATE = """# {title}

## Objective

{objective}

## Trace Scope

- One coherent task or task block:
- Not mixed with:

## Workflow Recipe

- Primary pattern:
- Supporting patterns:
- Routing confidence:
- Routing reason:
- Budget:
- Stop conditions:
- Recipe changes:

## Continuation Justification

- Required only when this trace is intentionally continued on a later day.

## Constraints

- User instructions:
- Protected tests:
- Scope boundaries:

## Loop

### Orient

-

### Inspect

-

### Decide

-

### Act

-

### Verify

-

## Subagents

| Stage | Subtask | Evidence Returned | Accepted By Orchestrator |
|---|---|---|---|
|  |  |  |  |

## Memory Updates

- Semantic notes changed:
- Indexes changed:
- Durable decisions promoted:

## Residual Risk

-
"""

SEMANTIC_NOTE_TEMPLATE = """# {title}

---
memory_schema: atomic-v1
type: canonical-decision
status: active
scope:
canonical: true
thesis: {title}
atomic: true
tags:
  - category/<category>
properties:
  - scope=
moc:
links:
  - <related-note-or-moc>
sources:
  - ../decision-traces/<trace>.md
supersedes:
last_verified:
validation:
  - atomic
  - thesis-title
  - connects
  - unique
  - metadata
---

## Durable Fact Or Decision

-

## Connections

- MOC:
- Related:

## Validation

- Atomic: one idea only.
- Thesis title: the title states the claim.
- Connects: at least one link, MOC, or source anchors the note.
- Unique: scope does not duplicate another active canonical note.
- Metadata: tags and properties are queryable.

## Evidence

-

## Operational Use

-

## Revalidation

-
"""

SUBAGENT_BRIEF_TEMPLATE = """# Subagent Brief

## Objective

-

## Scope

- Read:
- Edit:
- Do not touch:

## Active Decisions

-

## Protected Tests

-

## Current Trace

-

## Operating Rules

- Stay inside the assigned scope.
- Prefer read/check/report unless the brief explicitly permits edits.
- Do not promote semantic notes or memory directly.
- Return evidence to the orchestrator for acceptance.

## Expected Evidence

- Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- Files read:
- Commands run:
- Findings:
- Risks:
- Suggested memory updates:

## Verification Command

```text

```
"""

MEMORY_CLOSURE_TEMPLATE = """# Memory Closure Check

Before reporting completion, the orchestrator checks:

- [ ] Did this task create or change a durable decision?
- [ ] Did it verify a command, test, build, lint, typecheck, or runtime behavior worth remembering?
- [ ] Did it create a protected TDD test or change the status of one?
- [ ] Did any existing note become stale, contradicted, or too broad?
- [ ] Are all notes using required frontmatter: memory_schema, type, status, scope, canonical, thesis, atomic, tags, properties, moc, links, sources, supersedes, last_verified?
- [ ] Do new permanent notes pass the five-question gate: atomic, thesis title, connects, unique, metadata?
- [ ] Is there only one active canonical decision note for each scope?
- [ ] Is the current trace scoped to one coherent task rather than an umbrella work log?
- [ ] Is the current decision trace linked from the relevant index or note?
- [ ] Do compact notes point back to the trace that proves them?
- [ ] Did `memory-maintenance.py --strict` pass when this task touched traces, notes, or memory?
- [ ] Are residual risks named in the trace and final answer?
"""

WORKFLOW_PROFILE_TEMPLATE = """# Workflow Profile

## Recipe

- Primary pattern:
- Supporting patterns:
- Routing confidence:
- Routing reason:

## Pattern Obligations

- classify-and-act: record route, confidence, and fallback when confidence is low.
- fan-out-and-synthesize: record parallel domains, accepted results, and synthesis.
- adversarial-verification: record verifier focus, findings, and resolution.
- generate-and-filter: record criteria before candidates and selected result after filtering.
- tournament: record pairwise comparisons and winner.
- loop-until-done: record budget, progress, stop condition, and escalation trigger.
"""

NEW_TRACE_SCRIPT = r'''#!/usr/bin/env python3
"""Create a Fable Harness decision trace and update the trace index."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "task"


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def instruction_file_for(local_dir: Path) -> str:
    if local_dir.name == ".claude":
        return "CLAUDE.md"
    return "AGENTS.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a decision trace.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    traces = local_dir / "decision-traces"
    traces.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(args.slug or args.title)
    path = traces / f"{stamp}-{slug}.md"

    template_path = local_dir / "templates" / "decision-trace.md"
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else "# {title}\n\n## Objective\n\n{objective}\n"
    content = template.replace("{title}", args.title).replace("{objective}", "Describe the task objective.")
    path.write_text(content, encoding="utf-8")

    index = traces / "_index.md"
    if not index.exists():
        index.write_text("# Decision Trace Index\n\n## Traces\n\n", encoding="utf-8")
    rel = path.name
    line = f"- {stamp[:10]}: [{args.title}]({rel})\n"
    index_text = index.read_text(encoding="utf-8")
    if rel not in index_text:
        index.write_text(index_text.rstrip() + "\n" + line, encoding="utf-8")

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

MEMORY_POLICY_SCRIPT = r'''#!/usr/bin/env python3
"""Policy checks for Fable Harness traces and semantic notes."""

from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path


NOTE_TYPES = {"canonical-decision", "trace-summary", "operational-note", "migration-note"}
NOTE_STATUSES = {"active", "superseded", "archived"}
ATOMIC_NOTE_FIELDS = ["thesis", "atomic", "tags", "properties", "moc", "links", "validation"]
ATOMIC_VALIDATION_ITEMS = {"atomic", "thesis-title", "connects", "unique", "metadata"}
GENERIC_TRACE_TITLES = {"misc", "plus", "session", "work", "task", "update", "notes"}
DOMAIN_TERMS = {
    "architecture": {"architecture", "domain", "boundary", "service", "module"},
    "tooling": {"tooling", "workflow", "script", "command", "package", "install"},
    "policy": {"policy", "permission", "security", "compliance", "capability"},
    "questionnaire": {"questionnaire", "question", "answer", "block"},
    "release": {"release", "publish", "version", "npm", "pypi"},
    "testing": {"test", "tdd", "verify", "validation", "coverage"},
}


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def file_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def parse_frontmatter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    try:
        start = next(idx for idx, line in enumerate(lines) if line.strip() == "---")
    except StopIteration:
        return {}
    meta: dict[str, object] = {}
    current: str | None = None
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("- ") and current:
            if not isinstance(meta.get(current), list):
                meta[current] = []
            value = stripped[2:].strip()
            if value:
                meta[current].append(value)
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current = key.strip()
            value = value.strip()
            meta[current] = value
    return meta


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def add_candidate(
    candidates: list[dict[str, object]],
    action: str,
    path: Path,
    root: Path,
    reason: str,
    severity: str = "warn",
    size: int | None = None,
) -> None:
    item: dict[str, object] = {
        "action": action,
        "path": relpath(path, root),
        "reason": reason,
        "severity": severity,
    }
    if size is not None:
        item["bytes"] = size
    candidates.append(item)


def expected_scope(note: Path, local_dir: Path) -> str:
    return relpath(note.with_suffix(""), local_dir / "notes")


def note_title_matches_thesis(title: str, thesis: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    return bool(thesis.strip()) and normalize(title) == normalize(thesis)


def is_active_canonical(meta: dict[str, object]) -> bool:
    return (
        str(meta.get("type", "")).strip() == "canonical-decision"
        and str(meta.get("status", "")).strip() == "active"
        and as_bool(meta.get("canonical"))
    )


def is_atomic_v1(meta: dict[str, object]) -> bool:
    return str(meta.get("memory_schema", "")).strip() == "atomic-v1"


def skip_policy_note(note: Path, local_dir: Path) -> bool:
    if note.name == "_index.md":
        return True
    try:
        parts = note.relative_to(local_dir / "notes").parts
    except ValueError:
        return False
    return bool(parts and parts[0] in {"_moc", "_inbox"})


def resolve_source(note: Path, source: str) -> Path:
    path = Path(source.strip().strip("`"))
    if not path.is_absolute():
        path = note.parent / path
    return path.resolve()


def note_policy_candidates(note: Path, root: Path, local_dir: Path, validate_sources: bool = False) -> list[dict[str, object]]:
    text = note.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    candidates: list[dict[str, object]] = []
    required = ["type", "status", "scope", "canonical", "sources", "supersedes", "last_verified"]
    missing = [key for key in required if key not in meta]
    if missing:
        add_candidate(candidates, "repair-note-schema", note, root, f"missing required frontmatter: {', '.join(missing)}", "high")
        return candidates
    note_type = str(meta.get("type", "")).strip()
    status = str(meta.get("status", "")).strip()
    if note_type not in NOTE_TYPES:
        add_candidate(candidates, "repair-note-schema", note, root, f"invalid note type: {note_type}", "high")
    if status not in NOTE_STATUSES:
        add_candidate(candidates, "repair-note-schema", note, root, f"invalid note status: {status}", "high")
    if as_bool(meta.get("canonical")) and note_type != "canonical-decision":
        add_candidate(candidates, "repair-note-schema", note, root, "canonical notes must use type canonical-decision", "high")
    if not str(meta.get("scope", "")).strip():
        add_candidate(candidates, "repair-note-schema", note, root, "scope must not be empty", "high")
    if is_active_canonical(meta) and not is_atomic_v1(meta):
        missing_atomic = [key for key in ["memory_schema", *ATOMIC_NOTE_FIELDS] if key not in meta]
        if missing_atomic:
            add_candidate(
                candidates,
                "upgrade-note-atomicity",
                note,
                root,
                f"legacy active canonical note is missing permanent-note metadata: {', '.join(missing_atomic)}",
                "warn",
            )
    if is_atomic_v1(meta):
        missing = [key for key in ATOMIC_NOTE_FIELDS if key not in meta]
        if missing:
            add_candidate(candidates, "repair-note-atomicity", note, root, f"missing atomic frontmatter: {', '.join(missing)}", "high")
        title = file_title(text, note.stem)
        thesis = str(meta.get("thesis", "")).strip()
        if not thesis:
            add_candidate(candidates, "repair-note-atomicity", note, root, "thesis must not be empty", "high")
        elif not note_title_matches_thesis(title, thesis):
            add_candidate(candidates, "repair-note-atomicity", note, root, "title must state the same thesis as thesis frontmatter", "high")
        if not as_bool(meta.get("atomic")):
            add_candidate(candidates, "repair-note-atomicity", note, root, "atomic must be true for permanent notes", "high")
        if not as_list(meta.get("tags", [])):
            add_candidate(candidates, "repair-note-atomicity", note, root, "tags must include at least one queryable tag", "high")
        if not as_list(meta.get("properties", [])):
            add_candidate(candidates, "repair-note-atomicity", note, root, "properties must include at least one queryable property", "high")
        moc = str(meta.get("moc", "")).strip()
        links = as_list(meta.get("links", []))
        if not moc:
            add_candidate(candidates, "repair-note-atomicity", note, root, "moc must point to a map of content", "high")
        if not links:
            add_candidate(candidates, "repair-note-atomicity", note, root, "links must connect the note to a MOC or related note", "high")
        validation = set(as_list(meta.get("validation", [])))
        missing_validation = sorted(ATOMIC_VALIDATION_ITEMS - validation)
        if missing_validation:
            add_candidate(candidates, "repair-note-atomicity", note, root, f"validation gate is missing: {', '.join(missing_validation)}", "high")
    if validate_sources:
        sources = as_list(meta.get("sources", []))
        if not sources:
            add_candidate(candidates, "repair-source", note, root, "note has no source evidence", "high")
        for source in sources:
            if not resolve_source(note, source).exists():
                add_candidate(candidates, "repair-source", note, root, f"missing source: {source}", "high")
    return candidates


def duplicate_canonical_candidates(root: Path, local_dir: Path) -> list[dict[str, object]]:
    notes = local_dir / "notes"
    by_scope: dict[str, list[Path]] = {}
    if not notes.exists():
        return []
    for note in notes.rglob("*.md"):
        if skip_policy_note(note, local_dir):
            continue
        meta = parse_frontmatter(note.read_text(encoding="utf-8"))
        if (
            str(meta.get("type", "")).strip() == "canonical-decision"
            and str(meta.get("status", "")).strip() == "active"
            and as_bool(meta.get("canonical"))
        ):
            scope = str(meta.get("scope", "")).strip() or expected_scope(note, local_dir)
            by_scope.setdefault(scope, []).append(note)
    candidates: list[dict[str, object]] = []
    for scope, paths in sorted(by_scope.items()):
        if len(paths) > 1:
            joined = ", ".join(relpath(path, root) for path in paths)
            add_candidate(
                candidates,
                "deduplicate-canonical-note",
                paths[0],
                root,
                f"duplicate active canonical note for scope {scope}: {joined}",
                "high",
            )
    return candidates


def allowed_umbrella_trace(title: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return normalized.startswith("session-index") or normalized.startswith("migration-trace")


def trace_policy_candidates(trace: Path, root: Path, max_trace_bytes: int = 24576) -> list[dict[str, object]]:
    text = trace.read_text(encoding="utf-8")
    title = file_title(text, trace.stem)
    normalized_title = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    candidates: list[dict[str, object]] = []
    if normalized_title in GENERIC_TRACE_TITLES:
        add_candidate(candidates, "rename-generic-trace", trace, root, f"generic trace title: {title}", "high")
    block_markers = re.findall(r"(?im)(?:^|\s)(?:#\d+|block[-_ ]?\d+)\b", text)
    if len(block_markers) >= 3 and not allowed_umbrella_trace(title):
        add_candidate(candidates, "split-umbrella-trace", trace, root, "trace contains multiple questionnaire/block markers", "high")
    lower = text.lower()
    domains = [
        domain
        for domain, terms in DOMAIN_TERMS.items()
        if any(re.search(rf"\b{re.escape(term)}\b", lower) for term in terms)
    ]
    if len(domains) >= 4 and not allowed_umbrella_trace(title):
        add_candidate(candidates, "review-mixed-domain-trace", trace, root, f"trace mixes domains: {', '.join(domains)}", "warn")
    size = trace.stat().st_size
    if size > max_trace_bytes and not allowed_umbrella_trace(title):
        add_candidate(candidates, "summarize-trace", trace, root, f"trace exceeds {max_trace_bytes} bytes", "high", size)
    date_match = re.match(r"(\d{4}-\d{2}-\d{2})", trace.name)
    if date_match:
        created = dt.date.fromisoformat(date_match.group(1))
        modified = dt.datetime.fromtimestamp(trace.stat().st_mtime).date()
        if modified > created and "Continuation Justification" not in text:
            add_candidate(candidates, "justify-trace-continuation", trace, root, "trace was updated on a later day without continuation justification", "high")
    return candidates


def policy_candidates(
    root: Path,
    local_dir: Path,
    max_trace_bytes: int = 24576,
    validate_sources: bool = False,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    notes = local_dir / "notes"
    if notes.exists():
        for note in sorted(notes.rglob("*.md")):
            if skip_policy_note(note, local_dir):
                continue
            candidates.extend(note_policy_candidates(note, root, local_dir, validate_sources))
    candidates.extend(duplicate_canonical_candidates(root, local_dir))
    traces = local_dir / "decision-traces"
    if traces.exists():
        for trace in sorted(traces.rglob("*.md")):
            if trace.name == "_index.md":
                continue
            candidates.extend(trace_policy_candidates(trace, root, max_trace_bytes))
    return candidates


def critical_closure_failures(root: Path, local_dir: Path, trace: Path | None = None) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    notes = local_dir / "notes"
    if notes.exists():
        for note in sorted(notes.rglob("*.md")):
            if skip_policy_note(note, local_dir):
                continue
            candidates.extend(note_policy_candidates(note, root, local_dir, validate_sources=True))
    candidates.extend(duplicate_canonical_candidates(root, local_dir))
    if trace and trace.exists():
        candidates.extend(trace_policy_candidates(trace, root))
    return [item for item in candidates if item.get("severity") == "high"]


def has_high_severity(candidates: list[dict[str, object]]) -> bool:
    return any(item.get("severity") == "high" for item in candidates)
'''

CHECK_CLOSURE_SCRIPT = r'''#!/usr/bin/env python3
"""Check whether a project has the expected Fable Harness closure surface."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from memory_policy import critical_closure_failures


REQUIRED_TEMPLATES = [
    "decision-trace.md",
    "semantic-note.md",
    "subagent-brief.md",
    "memory-closure.md",
    "workflow-profile.md",
]

REQUIRED_MEMORY_SCRIPTS = [
    "memory_policy.py",
    "memory_core.py",
    "new-note.py",
    "promote-trace.py",
    "memory-search.py",
    "rebuild-memory.py",
    "rag-eval.py",
    "rag-pipeline.py",
    "source-arbitrate.py",
    "graph-query.py",
    "graph-check.py",
    "code_graph_core.py",
    "code-graph-build.py",
    "code-graph-query.py",
    "code-graph-check.py",
    "release-notice.py",
    "workflow_core.py",
    "subagent-plan.py",
    "subagent-result.py",
    "subagent-sweep.py",
    "selective-revert.py",
    "memory-maintenance.py",
    "memory-touch.py",
    "memory-dream.py",
    "loop_core.py",
    "loop-start.py",
    "loop-event.py",
    "loop-transition.py",
    "loop-check.py",
]


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def instruction_file_for(local_dir: Path) -> str:
    if local_dir.name == ".claude":
        return "CLAUDE.md"
    return "AGENTS.md"


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def section(text: str, names: tuple[str, ...]) -> str:
    wanted = {name.lower() for name in names}
    current: str | None = None
    chunks: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            continue
        if current in wanted:
            chunks.append(line)
    return "\n".join(chunks).strip()


def meaningful(text: str) -> str:
    ignored = {
        "",
        "-",
        "- none",
        "none",
        "n/a",
        "na",
        "not applicable",
        "not recorded",
        "todo",
        "tbd",
    }
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower() in ignored:
            continue
        if stripped.startswith("|") or stripped.startswith("```"):
            continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def trace_needs_promotion(text: str) -> bool:
    decision = section(text, ("Decide", "Decision", "Decisions", "Durable Decision", "Chosen Approach"))
    return bool(meaningful(decision))


def source_lines(text: str) -> list[str]:
    sources: list[str] = []
    in_sources = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("sources:"):
            in_sources = True
            continue
        if in_sources:
            if stripped.startswith("- "):
                value = stripped[2:].strip().strip("`").strip()
                if value:
                    sources.append(value)
                continue
            if stripped and not line.startswith(" "):
                break
    return sources


def source_points_to_trace(source: str, note: Path, root: Path, local_dir: Path, trace: Path) -> bool:
    normalized = source.replace("\\", "/").strip()
    exact = {
        trace.name,
        relpath(trace, root),
        relpath(trace, local_dir),
    }
    if normalized in exact:
        return True
    candidate = Path(source)
    if not candidate.is_absolute():
        candidate = (note.parent / candidate).resolve()
    return candidate == trace


def trace_is_promoted(root: Path, local_dir: Path, trace_path: Path) -> bool:
    trace = trace_path.resolve()
    candidates = {
        trace.name,
        relpath(trace, root),
        relpath(trace, local_dir),
    }

    log_path = local_dir / "memory" / "promotion_log.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(item.get("trace", "")).replace("\\", "/") in candidates:
                return True

    notes = local_dir / "notes"
    if notes.exists():
        for note in notes.rglob("*.md"):
            if note.name == "_index.md":
                continue
            text = note.read_text(encoding="utf-8")
            if any(source_points_to_trace(source, note, root, local_dir, trace) for source in source_lines(text)):
                return True

    return False


def append_trace_promotion_failures(root: Path, local_dir: Path, trace_arg: str, missing: list[str]) -> None:
    trace_path = Path(trace_arg)
    if not trace_path.is_absolute():
        trace_path = root / trace_path
    trace_path = trace_path.resolve()
    if not trace_path.exists():
        return
    text = trace_path.read_text(encoding="utf-8")
    if trace_needs_promotion(text) and not trace_is_promoted(root, local_dir, trace_path):
        command = (
            f"{local_dir / 'scripts' / 'promote-trace.py'} --root {root} "
            f"--trace {trace_path} --category decisions --area workflow --topic <topic>"
        )
        missing.append(
            f"{trace_path}: durable trace evidence was not promoted. Run: {command}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fable Harness closure files.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--trace", help="Decision trace file expected to exist.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    missing = []

    instruction = instruction_file_for(local_dir)
    instruction_path = root / instruction
    if not instruction_path.exists():
        missing.append(str(instruction_path))
    elif "fable-harness:start" not in instruction_path.read_text(encoding="utf-8"):
        missing.append(f"{instruction_path} missing fable-harness block")

    for name in REQUIRED_TEMPLATES:
        path = local_dir / "templates" / name
        if not path.exists():
            missing.append(str(path))

    for path in [
        local_dir / "scripts" / "new-trace.py",
        local_dir / "scripts" / "check-closure.py",
        *[local_dir / "scripts" / name for name in REQUIRED_MEMORY_SCRIPTS],
        local_dir / "notes" / "_index.md",
        local_dir / "decision-traces" / "_index.md",
        local_dir / "memory" / "manifest.json",
    ]:
        if not path.exists():
            missing.append(str(path))

    if args.trace:
        trace_path = Path(args.trace)
        if not trace_path.is_absolute():
            trace_path = root / trace_path
        if not trace_path.exists():
            missing.append(args.trace)
        else:
            append_trace_promotion_failures(root, local_dir, str(trace_path), missing)
            for item in critical_closure_failures(root, local_dir, trace_path.resolve()):
                missing.append(f"{item['path']}: {item['reason']}")
    else:
        for item in critical_closure_failures(root, local_dir):
            missing.append(f"{item['path']}: {item['reason']}")

    if missing:
        print("Fable Harness closure check failed:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("Fable Harness closure check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

WORKFLOW_CORE_SCRIPT = r'''#!/usr/bin/env python3
"""Workflow pattern helpers for Fable Harness loop governance."""

from __future__ import annotations


PATTERNS = {
    "classify-and-act": {"phase": "orient", "required": ["workflow.classified"]},
    "fan-out-and-synthesize": {
        "phase": "execution",
        "required": ["subagent.result.accepted", "synthesis.recorded"],
    },
    "adversarial-verification": {
        "phase": "verification",
        "required": ["adversarial.finding.recorded", "adversarial.resolution.recorded"],
    },
    "generate-and-filter": {
        "phase": "planning",
        "required": ["candidate.criteria.recorded", "candidate.selected"],
    },
    "tournament": {
        "phase": "planning",
        "required": ["tournament.match.recorded", "tournament.winner.selected"],
    },
    "loop-until-done": {"phase": "governance", "required": ["stop-condition.met"]},
}

DEFAULT_BUDGET = {
    "max_iterations": 3,
    "max_repairs": 2,
    "max_subagent_waves": 2,
    "low_confidence_threshold": 0.70,
}


def _clean_pattern(value: object) -> str:
    pattern = str(value or "").strip()
    if not pattern:
        return ""
    if pattern not in PATTERNS:
        raise ValueError(f"unknown workflow pattern: {pattern}")
    return pattern


def _merge_budget(raw_budget: object) -> dict[str, object]:
    budget: dict[str, object] = dict(DEFAULT_BUDGET)
    if isinstance(raw_budget, dict):
        for key, value in raw_budget.items():
            if value is not None:
                budget[str(key)] = value
    return budget


def normalize_workflow(raw: object) -> dict[str, object]:
    if not raw:
        return {
            "mode": "legacy-standard",
            "primary": None,
            "recipe": [],
            "routing": {"confidence": None, "reason": "", "fallback": ""},
            "budget": dict(DEFAULT_BUDGET),
        }
    if not isinstance(raw, dict):
        raise ValueError("workflow metadata must be an object")

    recipe: list[str] = []
    primary = _clean_pattern(raw.get("primary"))
    for item in raw.get("recipe") or []:
        pattern = _clean_pattern(item)
        if pattern and pattern not in recipe:
            recipe.append(pattern)
    if primary and primary not in recipe:
        recipe.append(primary)
    if not primary and recipe:
        primary = recipe[0]
    if not recipe:
        return normalize_workflow(None)

    routing_raw = raw.get("routing")
    routing = routing_raw if isinstance(routing_raw, dict) else {}
    return {
        "mode": "workflow-aware",
        "primary": primary,
        "recipe": recipe,
        "routing": {
            "confidence": routing.get("confidence"),
            "reason": str(routing.get("reason") or ""),
            "fallback": str(routing.get("fallback") or ""),
        },
        "budget": _merge_budget(raw.get("budget")),
    }


def pattern_set(workflow: dict[str, object]) -> set[str]:
    return {str(pattern) for pattern in workflow.get("recipe", []) if str(pattern) in PATTERNS}


def _event_indices(events: list[dict[str, object]], kind: str) -> list[int]:
    return [index for index, event in enumerate(events) if str(event.get("kind")) == kind]


def _has_event(events: list[dict[str, object]], kind: str) -> bool:
    return bool(_event_indices(events, kind))


def _first_index(events: list[dict[str, object]], kind: str) -> int | None:
    indices = _event_indices(events, kind)
    return indices[0] if indices else None


def _require_event(events: list[dict[str, object]], kind: str, errors: list[str], message: str) -> None:
    if not _has_event(events, kind):
        errors.append(message)


def _require_any(events: list[dict[str, object]], kinds: list[str], errors: list[str], message: str) -> None:
    if not any(_has_event(events, kind) for kind in kinds):
        errors.append(message)


def _metadata(event: dict[str, object]) -> dict[str, object]:
    metadata = event.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def workflow_errors(
    workflow: dict[str, object],
    events: list[dict[str, object]],
    state: dict[str, object],
    strict: bool,
) -> tuple[list[str], list[str]]:
    workflow = normalize_workflow(workflow)
    if workflow.get("mode") == "legacy-standard":
        return [], []

    errors: list[str] = []
    warnings: list[str] = []
    if not strict:
        warnings.append("workflow-aware run has pattern gates disabled outside strict mode")
        return errors, warnings

    recipe = pattern_set(workflow)

    if "classify-and-act" in recipe:
        classified = [event for event in events if str(event.get("kind")) == "workflow.classified"]
        _require_event(events, "workflow.classified", errors, "classify-and-act requires workflow.classified")
        budget = workflow.get("budget")
        budget_map = budget if isinstance(budget, dict) else {}
        threshold = _float_or_none(budget_map.get("low_confidence_threshold"))
        threshold = 0.70 if threshold is None else threshold
        routing = workflow.get("routing")
        routing_map = routing if isinstance(routing, dict) else {}
        for event in classified:
            metadata = _metadata(event)
            confidence = _float_or_none(metadata.get("confidence"))
            fallback = str(metadata.get("fallback") or routing_map.get("fallback") or "")
            if confidence is not None and confidence < threshold and not fallback:
                errors.append("classify-and-act low confidence route requires fallback metadata")

    if "generate-and-filter" in recipe:
        criteria_index = _first_index(events, "candidate.criteria.recorded")
        selected_index = _first_index(events, "candidate.selected")
        if selected_index is not None and (criteria_index is None or criteria_index > selected_index):
            errors.append("generate-and-filter selected a candidate before criteria were recorded")
        _require_event(events, "candidate.selected", errors, "generate-and-filter requires candidate.selected")

    if "fan-out-and-synthesize" in recipe:
        _require_event(
            events,
            "subagent.result.accepted",
            errors,
            "fan-out-and-synthesize requires accepted subagent result evidence",
        )
        _require_event(events, "synthesis.recorded", errors, "fan-out-and-synthesize requires synthesis.recorded")

    if "adversarial-verification" in recipe:
        _require_event(
            events,
            "adversarial.finding.recorded",
            errors,
            "adversarial-verification requires adversarial.finding.recorded",
        )
        _require_event(
            events,
            "adversarial.resolution.recorded",
            errors,
            "adversarial-verification requires adversarial.resolution.recorded",
        )

    if "tournament" in recipe:
        _require_event(events, "tournament.match.recorded", errors, "tournament selected a winner without a recorded match")
        _require_event(events, "tournament.winner.selected", errors, "tournament requires tournament.winner.selected")

    if "loop-until-done" in recipe:
        _require_any(
            events,
            ["stop-condition.met", "stop-condition.blocked"],
            errors,
            "loop-until-done requires stop-condition.met or stop-condition.blocked",
        )

    return errors, warnings
'''


MEMORY_CORE_SCRIPT = r'''#!/usr/bin/env python3
"""Local-first memory core for Fable Harness scripts.

Storage is deliberately sharded JSONL. Manifests stay small; retrieval reads
candidate shards instead of one large vector file.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import time
from pathlib import Path


VECTOR_DIMS = 64
MEMORY_SCHEMA = "fable-harness-memory-v2"
GRAPH_SCHEMA = "fable-harness-graph-v3"
CHUNKING_STRATEGY = "markdown-heading-window-v2"
MAX_CHUNK_CHARS = 1800
CHUNK_OVERLAP_LINES = 2
HYBRID_SCORE_WEIGHTS = {
    "vector": 0.40,
    "lexical": 0.35,
    "graph": 0.15,
    "rerank": 0.10,
}
STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "because", "before",
    "between", "but", "can", "codex", "did", "does", "done", "for", "from",
    "had", "has", "have", "into", "its", "not", "now", "the", "then",
    "this", "that", "they", "trace", "when", "where", "with", "work",
}
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "topic"


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def top_terms(text: str, limit: int = 16) -> list[str]:
    counts: dict[str, int] = {}
    for token in tokens(text):
        if token in STOPWORDS or len(token) < 3:
            continue
        counts[token] = counts.get(token, 0) + 1
    return [
        term
        for term, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def vector(text: str) -> list[list[float]]:
    values = [0.0] * VECTOR_DIMS
    for token in tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = digest[0] % VECTOR_DIMS
        sign = 1.0 if digest[1] % 2 == 0 else -1.0
        values[idx] += sign
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [[idx, round(value / norm, 6)] for idx, value in enumerate(values) if value]


def vector_dict(items: list[list[float]]) -> dict[int, float]:
    return {int(idx): float(value) for idx, value in items}


def cosine(left: list[list[float]], right: list[list[float]]) -> float:
    a = vector_dict(left)
    b = vector_dict(right)
    if not a or not b:
        return 0.0
    return sum(value * b.get(idx, 0.0) for idx, value in a.items())


def file_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def compact_summary(text: str, limit: int = 420) -> str:
    lines = []
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not lines:
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
        if sum(len(item) for item in lines) > limit:
            break
    summary = " ".join(lines)
    return summary[:limit].rstrip()


def section(text: str, names: tuple[str, ...]) -> str:
    wanted = {name.lower() for name in names}
    current: str | None = None
    chunks: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            continue
        if current in wanted:
            chunks.append(line)
    return "\n".join(chunks).strip()


def source_lines(text: str) -> list[str]:
    sources: list[str] = []
    in_sources = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("sources:"):
            in_sources = True
            continue
        if in_sources:
            if stripped.startswith("- "):
                sources.append(stripped[2:].strip())
                continue
            if stripped and not line.startswith(" "):
                break
    return sources


def parse_frontmatter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    try:
        start = next(idx for idx, line in enumerate(lines) if line.strip() == "---")
    except StopIteration:
        return {}
    meta: dict[str, object] = {}
    current: str | None = None
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("- ") and current:
            if not isinstance(meta.get(current), list):
                meta[current] = []
            value = stripped[2:].strip()
            if value:
                meta[current].append(value)
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current = key.strip()
            meta[current] = value.strip()
    return meta


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def note_moc_path(local_dir: Path, category: str) -> Path:
    return local_dir / "notes" / "_moc" / f"{slugify(category)}.md"


def note_metadata(text: str, path: Path, local_dir: Path, doc_type: str) -> dict[str, object]:
    if doc_type != "note":
        return {}
    meta = parse_frontmatter(text)
    return {
        "memory_schema": str(meta.get("memory_schema", "")).strip(),
        "thesis": str(meta.get("thesis", "")).strip(),
        "atomic": str(meta.get("atomic", "")).strip(),
        "tags": as_list(meta.get("tags", [])),
        "properties": as_list(meta.get("properties", [])),
        "moc": str(meta.get("moc", "")).strip(),
        "links": as_list(meta.get("links", [])),
        "validation": as_list(meta.get("validation", [])),
    }


def metadata_terms(metadata: dict[str, object]) -> list[str]:
    values = [
        str(metadata.get("thesis", "")),
        " ".join(str(tag) for tag in metadata.get("tags", [])),
        " ".join(str(prop) for prop in metadata.get("properties", [])),
        str(metadata.get("moc", "")),
        " ".join(str(link) for link in metadata.get("links", [])),
    ]
    seen: set[str] = set()
    terms: list[str] = []
    for token in tokens(" ".join(values)):
        lowered = token.lower()
        if lowered not in seen:
            seen.add(lowered)
            terms.append(lowered)
    return terms[:24]


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def citation_for(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    if not start_line:
        return path
    if not end_line or end_line == start_line:
        return f"{path}#L{start_line}"
    return f"{path}#L{start_line}-L{end_line}"


def markdown_sections(text: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    if not lines:
        return []
    sections: list[dict[str, object]] = []
    heading_stack: list[str] = []
    current_heading = "Document"
    current_start = 1

    for line_number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        if current_start < line_number:
            sections.append({
                "heading": current_heading,
                "start_line": current_start,
                "end_line": line_number - 1,
                "text": "\n".join(lines[current_start - 1:line_number - 1]),
            })
        level = len(match.group(1))
        title = match.group(2).strip()
        heading_stack = heading_stack[: max(level - 1, 0)]
        heading_stack.append(title)
        current_heading = " > ".join(heading_stack)
        current_start = line_number

    sections.append({
        "heading": current_heading,
        "start_line": current_start,
        "end_line": len(lines),
        "text": "\n".join(lines[current_start - 1:]),
    })
    return sections


def split_large_section(section: dict[str, object]) -> list[dict[str, object]]:
    text = str(section.get("text", ""))
    if len(text) <= MAX_CHUNK_CHARS:
        return [section]
    lines = text.splitlines()
    chunks: list[dict[str, object]] = []
    start = 0
    base_line = int(section.get("start_line", 1))
    while start < len(lines):
        chars = 0
        end = start
        while end < len(lines) and (chars + len(lines[end]) + 1 <= MAX_CHUNK_CHARS or end == start):
            chars += len(lines[end]) + 1
            end += 1
        chunks.append({
            "heading": section.get("heading", "Document"),
            "start_line": base_line + start,
            "end_line": base_line + end - 1,
            "text": "\n".join(lines[start:end]),
        })
        if end >= len(lines):
            break
        start = max(start + 1, end - CHUNK_OVERLAP_LINES)
    return chunks


def markdown_chunks(text: str) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    for section_item in markdown_sections(text):
        for chunk in split_large_section(section_item):
            chunk_text = str(chunk.get("text", "")).strip()
            if not chunk_text:
                continue
            if not has_substantive_chunk_content(chunk_text):
                continue
            chunks.append(chunk)
    return chunks


def has_substantive_chunk_content(text: str) -> bool:
    in_frontmatter = False
    seen_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            if not seen_frontmatter:
                seen_frontmatter = True
                in_frontmatter = True
                continue
            if in_frontmatter:
                in_frontmatter = False
                continue
        if in_frontmatter:
            continue
        if not stripped or stripped.startswith("#"):
            continue
        return True
    return False


def graph_terms_for_doc(doc: dict[str, object]) -> list[str]:
    text = str(doc.get("text", ""))
    semantic_labels = [label for _kind, label in semantic_items(text)]
    parts = [
        str(doc.get("title", "")),
        str(doc.get("summary", "")),
        str(doc.get("thesis", "")),
        " ".join(str(term) for term in doc.get("terms", [])),
        " ".join(str(tag) for tag in doc.get("tags", [])),
        " ".join(str(prop) for prop in doc.get("properties", [])),
        str(doc.get("moc", "")),
        " ".join(str(link) for link in doc.get("links", [])),
        " ".join(str(source) for source in doc.get("sources", [])),
        " ".join(referenced_paths(text)),
        " ".join(command_lines(text)),
        " ".join(decision_snippets(text)),
        " ".join(semantic_labels),
    ]
    return top_terms(" ".join(parts), limit=32)


def chunk_record(doc: dict[str, object], chunk: dict[str, object], index: int) -> dict[str, object]:
    chunk_text = str(chunk.get("text", ""))
    heading = str(chunk.get("heading") or doc.get("title") or "Document")
    start_line = int(chunk.get("start_line", 1))
    end_line = int(chunk.get("end_line", start_line))
    path = str(doc["path"])
    chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
    identity = f"{path}:{start_line}:{end_line}:{chunk_hash}"
    summary = compact_summary(chunk_text, limit=360) or heading
    graph_terms = top_terms(" ".join([
        heading,
        " ".join(str(term) for term in doc.get("graph_terms", [])),
        " ".join(str(source) for source in doc.get("sources", [])),
    ]), limit=32)
    record = {
        "id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        "type": doc["type"],
        "kind": "chunk",
        "path": path,
        "parent_id": doc["id"],
        "parent_path": path,
        "chunk_index": index,
        "title": doc["title"],
        "heading": heading,
        "summary": summary,
        "snippet": summary,
        "terms": top_terms(" ".join([heading, chunk_text]), limit=24),
        "graph_terms": graph_terms,
        "text_hash": doc["text_hash"],
        "chunk_hash": chunk_hash,
        "vector": vector(chunk_text),
        "sources": doc.get("sources", []),
        "start_line": start_line,
        "end_line": end_line,
        "citation": citation_for(path, start_line, end_line),
    }
    for key in ["memory_schema", "thesis", "atomic", "tags", "properties", "moc", "links", "validation"]:
        if key in doc:
            record[key] = doc[key]
    return record


def chunk_records_for_doc(doc: dict[str, object]) -> list[dict[str, object]]:
    text = str(doc.get("text", ""))
    return [
        chunk_record(doc, chunk, index)
        for index, chunk in enumerate(markdown_chunks(text), start=1)
    ]


def stable_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(f"{kind}:{value}".encode("utf-8")).hexdigest()[:20]
    return f"{kind}:{digest}"


def edge_id(edge_type: str, source: str, target: str, evidence: str = "") -> str:
    digest = hashlib.sha256(f"{edge_type}:{source}:{target}:{evidence}".encode("utf-8")).hexdigest()[:20]
    return f"edge:{digest}"


def normalize_graph_path(path: str) -> str:
    return path.strip().strip("`").strip().replace("\\", "/")


def resolve_reference_path(root: Path, doc_path: str, reference: str) -> str:
    value = normalize_graph_path(reference)
    raw = Path(value)
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        resolved = (root / Path(doc_path).parent / raw).resolve()
    try:
        return relpath(resolved, root)
    except ValueError:
        return value


SCRIPT_PATH_RE = re.compile(r"(?P<path>(?:\.codex|\.claude|\.agents|scripts|src|tests|\.github)[\\/][A-Za-z0-9_.\\/-]+)")
SEMANTIC_PREFIXES = {
    "backlog": "backlog_item",
    "backlog item": "backlog_item",
    "capability": "capability",
    "constraint": "constraint",
    "feature": "feature",
    "risk": "risk",
    "verification": "verification",
}
SEMANTIC_RELATIONS = {
    "backlog_item": "related_to",
    "capability": "implements",
    "constraint": "depends_on",
    "feature": "implements",
    "risk": "blocked_by",
    "verification": "verifies",
}


def referenced_paths(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in SCRIPT_PATH_RE.finditer(text):
        ref = normalize_graph_path(match.group("path")).rstrip(".,);:")
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs


def semantic_items(text: str) -> list[tuple[str, str]]:
    chunks = section(text, (
        "durable fact or decision",
        "evidence",
        "risks",
        "residual risk",
        "verification",
        "constraints",
        "operational use",
        "revalidation",
    ))
    items: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in chunks.splitlines():
        value = line.strip().lstrip("-").strip()
        if not value or value.startswith("```"):
            continue
        match = re.match(r"(?i)^([a-z][a-z ]{2,24}):\s*(.+)$", value)
        if not match:
            continue
        prefix = match.group(1).strip().lower()
        kind = SEMANTIC_PREFIXES.get(prefix)
        label = match.group(2).strip()
        if not kind or not label:
            continue
        key = (kind, label.lower())
        if key not in seen:
            seen.add(key)
            items.append((kind, label[:240]))
    return items


def command_lines(text: str) -> list[str]:
    chunks = section(text, ("verify", "verification", "evidence"))
    commands: list[str] = []
    seen: set[str] = set()
    for command in re.findall(r"`([^`]+)`", chunks):
        value = command.strip()
        if not value:
            continue
        first = value.split()[0].lower() if value.split() else ""
        if first in {"python", "py", "node", "npm", "yarn", "pnpm", "pytest", "git"} or "test" in value.lower():
            if value not in seen:
                seen.add(value)
                commands.append(value)
    return commands


def decision_snippets(text: str, limit: int = 3) -> list[str]:
    chunks = section(text, ("decide", "decision", "decisions", "durable fact or decision", "durable decision"))
    snippets: list[str] = []
    for line in chunks.splitlines():
        value = line.strip().lstrip("-").strip()
        if not value or value.startswith("```"):
            continue
        snippets.append(value[:220])
        if len(snippets) >= limit:
            break
    return snippets


def dormant_manifest_path(local_dir: Path) -> Path:
    return local_dir / "memory" / "dormant" / "manifest.json"


def load_dormant_manifest(local_dir: Path) -> dict[str, object]:
    path = dormant_manifest_path(local_dir)
    if not path.exists():
        return {"version": 1, "items": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "items": []}
    if not isinstance(data, dict):
        return {"version": 1, "items": []}
    if not isinstance(data.get("items"), list):
        data["items"] = []
    data.setdefault("version", 1)
    return data


def write_dormant_manifest(local_dir: Path, manifest: dict[str, object]) -> None:
    manifest["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(dormant_manifest_path(local_dir), manifest)


def dormant_excluded_paths(local_dir: Path) -> set[str]:
    manifest = load_dormant_manifest(local_dir)
    items = manifest.get("items", [])
    if not isinstance(items, list):
        return set()
    excluded: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or item.get("state") != "dormant":
            continue
        original_path = item.get("original_path")
        if isinstance(original_path, str) and original_path.strip():
            excluded.add(normalize_graph_path(original_path))
    return excluded


def iter_markdown_docs(local_dir: Path, exclude_paths: set[str] | None = None) -> list[dict[str, object]]:
    docs: list[dict[str, object]] = []
    excluded = {normalize_graph_path(path) for path in (exclude_paths or set())}
    for base, doc_type in [(local_dir / "notes", "note"), (local_dir / "decision-traces", "trace")]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name == "_index.md":
                continue
            rel = relpath(path, local_dir.parent)
            if rel in excluded:
                continue
            text = path.read_text(encoding="utf-8")
            title = file_title(text, path.stem)
            metadata = note_metadata(text, path, local_dir, doc_type)
            term_text = " ".join([
                text,
                str(metadata.get("thesis", "")),
                " ".join(str(tag) for tag in metadata.get("tags", [])),
                " ".join(str(prop) for prop in metadata.get("properties", [])),
                str(metadata.get("moc", "")),
                " ".join(str(link) for link in metadata.get("links", [])),
            ])
            base_terms = top_terms(term_text)
            for term in metadata_terms(metadata):
                if term not in base_terms:
                    base_terms.append(term)
            doc = {
                "id": hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16],
                "type": doc_type,
                "path": rel,
                "title": title,
                "summary": compact_summary(text),
                "terms": base_terms[:32],
                "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "vector": vector(text),
                "sources": source_lines(text),
                "text": text,
            }
            doc.update({key: value for key, value in metadata.items() if value not in ("", [], None)})
            docs.append(doc)
    return docs


def reset_jsonl_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.glob("*.jsonl"):
        child.unlink()
    for child in path.glob("*.json"):
        child.unlink()


def append_jsonl(path: Path, item: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def ensure_memory_layout(local_dir: Path) -> None:
    memory = local_dir / "memory"
    (memory / "shards").mkdir(parents=True, exist_ok=True)
    (memory / "graph").mkdir(parents=True, exist_ok=True)
    (memory / "cache").mkdir(parents=True, exist_ok=True)
    manifest = memory / "manifest.json"
    if not manifest.exists():
        manifest.write_text(
            json.dumps({
                "version": 1,
                "storage": "sharded-jsonl",
                "embedding": "local-hash-v1",
                "vector_dims": VECTOR_DIMS,
                "document_count": 0,
                "shards": [],
            }, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def chunk_cache_path(local_dir: Path) -> Path:
    return local_dir / "memory" / "cache" / "documents.json"


def load_chunk_cache(local_dir: Path) -> dict[str, object]:
    path = chunk_cache_path(local_dir)
    if not path.exists():
        return {"version": 1, "chunking": CHUNKING_STRATEGY, "documents": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "chunking": CHUNKING_STRATEGY, "documents": {}}
    if not isinstance(data, dict):
        return {"version": 1, "chunking": CHUNKING_STRATEGY, "documents": {}}
    if not isinstance(data.get("documents"), dict):
        data["documents"] = {}
    return data


def write_chunk_cache(local_dir: Path, data: dict[str, object]) -> None:
    data["version"] = 1
    data["chunking"] = CHUNKING_STRATEGY
    data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    path = chunk_cache_path(local_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")


def iter_semantic_note_paths(notes: Path) -> list[Path]:
    if not notes.exists():
        return []
    return [
        path
        for path in sorted(notes.rglob("*.md"))
        if path.name != "_index.md" and "_moc" not in path.relative_to(notes).parts
    ]


def update_note_mocs(local_dir: Path) -> None:
    notes = local_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[Path]] = {}
    for path in iter_semantic_note_paths(notes):
        rel_parts = path.relative_to(notes).parts
        if not rel_parts:
            continue
        category = rel_parts[0]
        if category.startswith("_"):
            continue
        groups.setdefault(category, []).append(path)
    moc_dir = notes / "_moc"
    moc_dir.mkdir(parents=True, exist_ok=True)
    for category, paths in sorted(groups.items()):
        lines = [
            f"# {category.replace('-', ' ').title()} MOC",
            "",
            "Map of content for this note cluster.",
            "",
            "## Notes",
            "",
        ]
        for path in sorted(paths):
            rel = relpath(path, moc_dir)
            title = file_title(path.read_text(encoding="utf-8"), path.stem)
            lines.append(f"- [{title}]({rel})")
        (moc_dir / f"{slugify(category)}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def update_notes_index(local_dir: Path) -> None:
    notes = local_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    update_note_mocs(local_dir)
    lines = ["# Semantic Notes Index", "", "Compact project memory for future agents.", "", "## Notes", ""]
    for path in iter_semantic_note_paths(notes):
        rel = relpath(path, notes)
        title = file_title(path.read_text(encoding="utf-8"), path.stem)
        lines.append(f"- [{title}]({rel})")
    moc_paths = sorted((notes / "_moc").glob("*.md")) if (notes / "_moc").exists() else []
    if moc_paths:
        lines.extend(["", "## Maps Of Content", ""])
        for path in moc_paths:
            rel = relpath(path, notes)
            title = file_title(path.read_text(encoding="utf-8"), path.stem)
            lines.append(f"- [{title}]({rel})")
    (notes / "_index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_memory(root: Path, agent: str = "auto") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    ensure_memory_layout(local_dir)
    update_notes_index(local_dir)

    memory = local_dir / "memory"
    shards_dir = memory / "shards"
    graph_dir = memory / "graph"
    reset_jsonl_dir(shards_dir)
    reset_jsonl_dir(graph_dir)

    docs = iter_markdown_docs(local_dir, dormant_excluded_paths(local_dir))
    for doc in docs:
        doc["kind"] = "document"
        doc["graph_terms"] = graph_terms_for_doc(doc)

    old_cache = load_chunk_cache(local_dir)
    old_cache_docs = old_cache.get("documents", {})
    if not isinstance(old_cache_docs, dict):
        old_cache_docs = {}
    new_cache_docs: dict[str, object] = {}
    chunk_records_by_path: dict[str, list[dict[str, object]]] = {}
    cache_hits = 0
    cache_misses = 0
    for doc in docs:
        doc_path = str(doc["path"])
        cached = old_cache_docs.get(doc_path)
        chunks: list[dict[str, object]]
        if (
            isinstance(cached, dict)
            and cached.get("text_hash") == doc.get("text_hash")
            and cached.get("chunking") == CHUNKING_STRATEGY
            and isinstance(cached.get("chunks"), list)
        ):
            chunks = [item for item in cached["chunks"] if isinstance(item, dict)]  # type: ignore[index]
            cache_hits += 1
        else:
            chunks = chunk_records_for_doc(doc)
            cache_misses += 1
        chunk_records_by_path[doc_path] = chunks
        new_cache_docs[doc_path] = {
            "text_hash": doc.get("text_hash"),
            "chunking": CHUNKING_STRATEGY,
            "chunk_count": len(chunks),
            "chunks": chunks,
        }

    shard_meta: dict[str, dict[str, object]] = {}
    doc_id_by_path = {str(doc["path"]): str(doc["id"]) for doc in docs}
    nodes: dict[str, dict[str, object]] = {}
    edges: dict[str, dict[str, object]] = {}

    def append_shard_record(record: dict[str, object]) -> None:
        shard_id = str(record["id"])[:2]
        shard_path = shards_dir / f"{shard_id}.jsonl"
        append_jsonl(shard_path, record)
        meta = shard_meta.setdefault(shard_id, {
            "id": shard_id,
            "path": relpath(shard_path, root),
            "doc_count": 0,
            "terms": set(),
        })
        meta["doc_count"] = int(meta["doc_count"]) + 1
        meta["terms"].update(record.get("terms", []))  # type: ignore[union-attr]

    def add_node(item: dict[str, object]) -> None:
        node_id = str(item["id"])
        existing = nodes.get(node_id)
        if existing:
            existing.update({key: value for key, value in item.items() if key not in existing or existing[key] in ("", None)})
        else:
            nodes[node_id] = item

    def add_edge(source: str, target: str, edge_type: str, evidence: str = "") -> None:
        item = {
            "id": edge_id(edge_type, source, target, evidence),
            "from": source,
            "to": target,
            "type": edge_type,
        }
        if evidence:
            item["evidence"] = evidence[:240]
        edges[str(item["id"])] = item

    def add_source_edge(doc: dict[str, object], source: str) -> None:
        resolved = resolve_reference_path(root, str(doc["path"]), source)
        target = doc_id_by_path.get(resolved)
        if not target:
            target = stable_id("source", resolved)
            add_node({"id": target, "kind": "source", "path": resolved, "title": resolved})
        add_edge(str(doc["id"]), target, "sourced_by", source)

    def add_script_reference(doc: dict[str, object], reference: str) -> None:
        ref = normalize_graph_path(reference)
        target = stable_id("script", ref)
        add_node({"id": target, "kind": "script", "path": ref, "title": Path(ref).name})
        add_edge(str(doc["id"]), target, "depends_on", ref)

    def add_command_reference(doc: dict[str, object], command: str) -> None:
        target = stable_id("command", command)
        add_node({"id": target, "kind": "command", "command": command, "title": command})
        add_edge(str(doc["id"]), target, "verifies", command)

    def add_decision_reference(doc: dict[str, object], snippet: str) -> None:
        target = stable_id("decision", f"{doc['path']}:{snippet}")
        add_node({"id": target, "kind": "decision", "title": snippet[:120], "summary": snippet, "source": doc["path"]})
        add_edge(str(doc["id"]), target, "implements", snippet)

    def add_semantic_reference(doc: dict[str, object], kind: str, label: str) -> None:
        target = stable_id(kind, f"{doc['path']}:{label}")
        add_node({
            "id": target,
            "kind": kind,
            "title": label[:120],
            "summary": label,
            "source": doc["path"],
        })
        add_edge(str(doc["id"]), target, SEMANTIC_RELATIONS.get(kind, "related_to"), label)

    def first_text(item: dict[str, object], keys: tuple[str, ...]) -> str:
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return ""

    def dormant_title(item: dict[str, object], path: str) -> str:
        title = first_text(item, ("title", "name"))
        return title or Path(path).name

    def subagent_domain_records(manifest: dict[str, object]) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        domains = manifest.get("domains")
        if isinstance(domains, list):
            for domain in domains:
                if not isinstance(domain, dict):
                    continue
                name = first_text(domain, ("name", "domain", "slug"))
                slug = first_text(domain, ("slug",)) or slugify(name)
                brief = first_text(domain, ("brief", "path"))
                wave = domain.get("wave")
                depends_on = domain.get("depends_on")
                records.append({
                    "name": name or slug,
                    "slug": slug,
                    "brief": brief,
                    "wave": wave,
                    "depends_on": depends_on if isinstance(depends_on, list) else [],
                })
        if records:
            return records
        briefs = manifest.get("briefs", [])
        if isinstance(briefs, list):
            for brief in briefs:
                if not isinstance(brief, str):
                    continue
                slug = Path(brief).stem
                records.append({
                    "name": slug.replace("-", " "),
                    "slug": slug,
                    "brief": normalize_graph_path(brief),
                    "wave": None,
                    "depends_on": [],
                })
        return records

    def add_subagent_package(plan_dir: Path, manifest: dict[str, object]) -> None:
        package_rel = relpath(plan_dir, root)
        package_id = stable_id("subagent_package", package_rel)
        task = first_text(manifest, ("task",)) or plan_dir.name
        add_node({
            "id": package_id,
            "kind": "subagent_package",
            "path": package_rel,
            "title": task,
            "dispatch_mode": manifest.get("dispatch_mode", "sequential"),
        })

        brief_by_slug: dict[str, str] = {}
        for record in subagent_domain_records(manifest):
            slug = str(record.get("slug") or slugify(str(record.get("name", ""))))
            brief_path = normalize_graph_path(str(record.get("brief") or ""))
            if not brief_path:
                brief_path = f"{package_rel}/{slug}.md"
            brief_id = stable_id("subagent_brief", brief_path)
            brief_by_slug[slug] = brief_id
            node = {
                "id": brief_id,
                "kind": "subagent_brief",
                "path": brief_path,
                "title": str(record.get("name") or slug),
                "domain": str(record.get("name") or slug),
            }
            if record.get("wave") not in (None, ""):
                node["wave"] = record["wave"]
            add_node(node)
            add_edge(package_id, brief_id, "delegates_to", str(record.get("name") or slug))
            for dependency in record.get("depends_on", []):
                if not isinstance(dependency, str):
                    continue
                dep_id = brief_by_slug.get(dependency) or stable_id("subagent_brief", f"{package_rel}/{dependency}.md")
                add_node({
                    "id": dep_id,
                    "kind": "subagent_brief",
                    "path": f"{package_rel}/{dependency}.md",
                    "title": dependency,
                    "domain": dependency,
                })
                add_edge(brief_id, dep_id, "depends_on", dependency)

        results = manifest.get("results", [])
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                result_path = normalize_graph_path(first_text(result, ("path",)))
                domain = first_text(result, ("domain",))
                slug = slugify(domain)
                result_id = stable_id("subagent_result", result_path or f"{package_rel}:{slug}:result")
                add_node({
                    "id": result_id,
                    "kind": "subagent_result",
                    "path": result_path,
                    "title": domain or slug,
                    "domain": domain or slug,
                    "status": first_text(result, ("status",)),
                    "summary": first_text(result, ("summary",)),
                })
                brief_id = brief_by_slug.get(slug)
                if brief_id:
                    add_edge(brief_id, result_id, "produces", first_text(result, ("status", "summary")))
                accepted_by = first_text(result, ("accepted_by",))
                if accepted_by:
                    actor_id = stable_id("actor", accepted_by)
                    add_node({"id": actor_id, "kind": "actor", "title": accepted_by})
                    add_edge(result_id, actor_id, "accepted_by", accepted_by)

    def add_dormant_node(item: dict[str, object], dormant_path: str, original_path: str = "") -> str:
        target = stable_id("dormant", dormant_path)
        node = {
            "id": target,
            "kind": "dormant",
            "path": dormant_path,
            "title": dormant_title(item, dormant_path),
        }
        if original_path:
            node["original_path"] = original_path
        add_node(node)
        return target

    for doc in docs:
        shard_doc = {key: value for key, value in doc.items() if key != "text"}
        append_shard_record(shard_doc)
        for chunk in chunk_records_by_path.get(str(doc["path"]), []):
            append_shard_record(chunk)

        doc_node = {
            "id": doc["id"],
            "kind": doc["type"],
            "path": doc["path"],
            "title": doc["title"],
            "summary": doc["summary"],
            "text_hash": doc["text_hash"],
        }
        for key in ["memory_schema", "thesis", "atomic", "tags", "properties", "moc", "links", "validation"]:
            if key in doc:
                doc_node[key] = doc[key]
        add_node(doc_node)
        for term in list(doc["terms"])[:8]:
            term_id = f"term:{term}"
            add_node({"id": term_id, "kind": "term", "title": term})
            add_edge(str(doc["id"]), term_id, "mentions", term)
        for source in doc["sources"]:
            add_source_edge(doc, source)
        text = str(doc.get("text", ""))
        for reference in referenced_paths(text):
            add_script_reference(doc, reference)
        for command in command_lines(text):
            add_command_reference(doc, command)
        for snippet in decision_snippets(text):
            add_decision_reference(doc, snippet)
        for kind, label in semantic_items(text):
            add_semantic_reference(doc, kind, label)

    promotion_log = memory / "promotion_log.jsonl"
    if promotion_log.exists():
        for line in promotion_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            trace = normalize_graph_path(str(item.get("trace", "")))
            note = normalize_graph_path(str(item.get("note", "")))
            trace_id = doc_id_by_path.get(trace)
            note_id = doc_id_by_path.get(note)
            if trace_id and note_id:
                add_edge(trace_id, note_id, "promotes", f"{trace} -> {note}")

    dormant_manifest = load_dormant_manifest(local_dir)
    dormant_node_by_path: dict[str, str] = {}
    items = dormant_manifest.get("items", [])
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            original_path = first_text(item, ("original_path", "path"))
            dormant_path = first_text(item, ("dormant_path", "dormant"))
            if not original_path or not dormant_path:
                continue
            original = normalize_graph_path(original_path)
            dormant = normalize_graph_path(dormant_path)
            source_id = doc_id_by_path.get(original)
            if not source_id:
                source_kind = first_text(item, ("kind",)) or "source"
                if "/decision-traces/" in f"/{original}":
                    source_kind = "trace"
                if source_kind == "dormant":
                    source_kind = "source"
                source_id = stable_id(source_kind, original)
                add_node({
                    "id": source_id,
                    "kind": source_kind,
                    "path": original,
                    "title": dormant_title(item, original),
                })
            dormant_id = add_dormant_node(item, dormant, original)
            dormant_node_by_path[dormant] = dormant_id
            evidence = first_text(item, ("source_run", "reason", "action"))
            add_edge(source_id, dormant_id, "archives", evidence)

    reactivations = dormant_manifest.get("reactivations", [])
    if isinstance(reactivations, list):
        for item in reactivations:
            if not isinstance(item, dict):
                continue
            dormant_path = first_text(item, ("dormant_path", "dormant", "from", "source"))
            note_path = first_text(item, ("note_path", "note", "reactivated_path", "to", "target"))
            if not dormant_path or not note_path:
                continue
            dormant = normalize_graph_path(dormant_path)
            note = normalize_graph_path(note_path)
            dormant_id = dormant_node_by_path.get(dormant) or add_dormant_node(item, dormant)
            note_id = doc_id_by_path.get(note)
            if not note_id:
                note_id = stable_id("note", note)
                add_node({"id": note_id, "kind": "note", "path": note, "title": Path(note).name})
            evidence = first_text(item, ("source_run", "reason", "run_id", "action"))
            add_edge(dormant_id, note_id, "reactivates", evidence)

    subagents_dir = local_dir / "subagents"
    if subagents_dir.exists():
        for manifest_path in sorted(subagents_dir.glob("*/manifest.json")):
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(manifest_data, dict):
                add_subagent_package(manifest_path.parent, manifest_data)

    for node in sorted(nodes.values(), key=lambda item: str(item["id"])):
        append_jsonl(graph_dir / "nodes.jsonl", node)
    for edge in sorted(edges.values(), key=lambda item: str(item["id"])):
        append_jsonl(graph_dir / "edges.jsonl", edge)

    indexes = graph_dir / "indexes"
    indexes.mkdir(parents=True, exist_ok=True)
    by_kind: dict[str, list[str]] = {}
    by_path: dict[str, str] = {}
    by_relation: dict[str, list[str]] = {}
    for node in nodes.values():
        by_kind.setdefault(str(node["kind"]), []).append(str(node["id"]))
        if node.get("path"):
            by_path[str(node["path"])] = str(node["id"])
    for edge in edges.values():
        by_relation.setdefault(str(edge["type"]), []).append(str(edge["id"]))
    (indexes / "by-kind.json").write_text(json.dumps({key: sorted(value) for key, value in sorted(by_kind.items())}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (indexes / "by-path.json").write_text(json.dumps(dict(sorted(by_path.items())), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (indexes / "by-relation.json").write_text(json.dumps({key: sorted(value) for key, value in sorted(by_relation.items())}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    shards = []
    for meta in sorted(shard_meta.values(), key=lambda item: str(item["id"])):
        shards.append({
            "id": meta["id"],
            "path": meta["path"],
            "doc_count": meta["doc_count"],
            "terms": sorted(meta["terms"])[:64],
        })

    chunk_count = sum(len(chunks) for chunks in chunk_records_by_path.values())
    source_hashes = {str(doc["path"]): str(doc["text_hash"]) for doc in docs}
    write_chunk_cache(local_dir, {
        "documents": new_cache_docs,
        "source_hashes": source_hashes,
    })

    manifest = {
        "version": 2,
        "schema": MEMORY_SCHEMA,
        "storage": "sharded-jsonl",
        "embedding": "local-hash-v1",
        "vector_dims": VECTOR_DIMS,
        "chunking": CHUNKING_STRATEGY,
        "document_count": len(docs),
        "chunk_count": chunk_count,
        "record_count": len(docs) + chunk_count,
        "cache": {
            "path": relpath(chunk_cache_path(local_dir), root),
            "hits": cache_hits,
            "misses": cache_misses,
            "documents": len(new_cache_docs),
        },
        "source_hashes": source_hashes,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "shards": shards,
    }
    (memory / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (graph_dir / "manifest.json").write_text(
        json.dumps({
            "version": 1,
            "schema": GRAPH_SCHEMA,
            "node_file": "nodes.jsonl",
            "edge_file": "edges.jsonl",
            "source_manifest": "../manifest.json",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_kinds": sorted(by_kind),
            "edge_types": sorted(by_relation),
            "indexes": [
                "indexes/by-kind.json",
                "indexes/by-path.json",
                "indexes/by-relation.json",
            ],
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_jsonl(path: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def read_json(path: Path, default: object | None = None) -> object:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {} if default is None else default


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def frontmatter_value(text: str, key: str) -> str | None:
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not in_frontmatter:
            in_frontmatter = True
            continue
        if stripped == "---" and in_frontmatter:
            break
        if in_frontmatter and stripped.startswith(f"{key}:"):
            return stripped.split(":", 1)[1].strip()
    return None


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def touch_index_path(local_dir: Path) -> Path:
    return local_dir / "memory" / "touch_index.json"


def load_touch_index(local_dir: Path) -> dict[str, object]:
    data = read_json(touch_index_path(local_dir), {"version": 1, "items": {}})
    if not isinstance(data, dict):
        return {"version": 1, "items": {}}
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    data.setdefault("version", 1)
    return data


def write_touch_index(local_dir: Path, data: dict[str, object]) -> None:
    data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(touch_index_path(local_dir), data)


def touch_entry(index: dict[str, object], path: str) -> dict[str, object]:
    items = index.get("items")
    if not isinstance(items, dict):
        return {}
    value = items.get(normalize_graph_path(path))
    return value if isinstance(value, dict) else {}


class TouchIndexLock:
    def __init__(self, local_dir: Path, timeout_seconds: float = 10.0) -> None:
        self.path = local_dir / "memory" / "touch_index.lock"
        self.timeout_seconds = timeout_seconds
        self.handle: int | None = None

    def __enter__(self) -> "TouchIndexLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                self.handle = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.handle, str(os.getpid()).encode("utf-8"))
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                    if age > 60:
                        self.path.unlink()
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for memory touch lock: {self.path}")
                time.sleep(0.025)

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.handle is not None:
            os.close(self.handle)
            self.handle = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def memory_kind_for_path(path: str) -> str:
    normalized = f"/{normalize_graph_path(path)}"
    if "/notes/" in normalized:
        return "note"
    if "/decision-traces/" in normalized:
        return "trace"
    if "/memory/dormant/" in normalized:
        return "dormant"
    return "memory"


def record_memory_touch(root: Path, path: str, reason: str = "", agent: str = "auto") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    ensure_memory_layout(local_dir)
    target = resolve_memory_reference(root, local_dir, path)
    if target is None:
        raise ValueError(f"memory path not found: {path}")
    rel = relpath(target.resolve(), root)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    kind = memory_kind_for_path(rel)
    event = {
        "timestamp": now,
        "path": rel,
        "kind": kind,
        "reason": reason,
    }
    with TouchIndexLock(local_dir):
        append_jsonl(local_dir / "memory" / "touches.jsonl", event)

        index = load_touch_index(local_dir)
        items = index.setdefault("items", {})
        if not isinstance(items, dict):
            items = {}
            index["items"] = items
        existing = items.get(rel)
        entry = existing if isinstance(existing, dict) else {}
        use_count = int(entry.get("use_count", 0)) + 1
        entry.update({
            "path": rel,
            "kind": kind,
            "use_count": use_count,
            "last_used_at": now,
            "last_reason": reason,
        })
        entry.setdefault("first_used_at", now)
        items[rel] = entry
        write_touch_index(local_dir, index)
    return {
        "path": rel,
        "kind": kind,
        "reason": reason,
        "use_count": use_count,
        "last_used_at": now,
        "touch_log": relpath(local_dir / "memory" / "touches.jsonl", root),
        "touch_index": relpath(touch_index_path(local_dir), root),
    }


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dream_run_id(root: Path) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    digest = hashlib.sha256(f"{root.resolve()}:{stamp}".encode("utf-8")).hexdigest()[:8]
    return f"{stamp}-{digest}"


def load_graph(root: Path, agent: str = "auto") -> dict[str, object]:
    local_dir = find_local_dir(root.resolve(), agent)
    graph_dir = local_dir / "memory" / "graph"
    manifest_path = graph_dir / "manifest.json"
    manifest: dict[str, object] = {}
    if manifest_path.exists():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
        except json.JSONDecodeError:
            manifest = {"error": "manifest is not valid JSON"}
    return {
        "graph_dir": graph_dir,
        "manifest": manifest,
        "nodes": read_jsonl(graph_dir / "nodes.jsonl"),
        "edges": read_jsonl(graph_dir / "edges.jsonl"),
    }


def query_graph(
    root: Path,
    agent: str = "auto",
    kind: str | None = None,
    path: str | None = None,
    node: str | None = None,
    relation: str | None = None,
    q: str | None = None,
) -> dict[str, object]:
    graph = load_graph(root, agent)
    nodes = list(graph["nodes"])  # type: ignore[arg-type]
    edges = list(graph["edges"])  # type: ignore[arg-type]
    if kind:
        nodes = [item for item in nodes if item.get("kind") == kind]
    if path:
        wanted = normalize_graph_path(path)
        nodes = [item for item in nodes if item.get("path") == wanted]
        node_ids = {str(item["id"]) for item in nodes if "id" in item}
        edges = [item for item in edges if item.get("from") in node_ids or item.get("to") in node_ids]
    if node:
        nodes = [item for item in nodes if item.get("id") == node]
        edges = [item for item in edges if item.get("from") == node or item.get("to") == node]
    if relation:
        edges = [item for item in edges if item.get("type") == relation]
    if q:
        wanted_terms = tokens(q)
        if wanted_terms:
            def haystack(item: dict[str, object]) -> str:
                return json.dumps(item, ensure_ascii=False, sort_keys=True).lower()

            matched_nodes = [
                item for item in nodes
                if all(term in haystack(item) for term in wanted_terms)
            ]
            matched_ids = {str(item["id"]) for item in matched_nodes if "id" in item}
            matched_edges = [
                item for item in edges
                if all(term in haystack(item) for term in wanted_terms)
                or item.get("from") in matched_ids
                or item.get("to") in matched_ids
            ]
            nodes = matched_nodes
            edges = matched_edges
    return {"nodes": nodes, "edges": edges, "manifest": graph["manifest"]}


def check_graph(root: Path, agent: str = "auto", strict: bool = False) -> dict[str, object]:
    graph = load_graph(root, agent)
    graph_dir = graph["graph_dir"]
    assert isinstance(graph_dir, Path)
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    errors: list[str] = []
    node_ids: set[str] = set()
    edge_ids: set[str] = set()
    for item in nodes:
        if not isinstance(item, dict):
            errors.append("malformed node record")
            continue
        node_id = item.get("id")
        if not node_id:
            errors.append("node missing id")
            continue
        if str(node_id) in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(str(node_id))
        if not item.get("kind"):
            errors.append(f"node missing kind: {node_id}")
    for item in edges:
        if not isinstance(item, dict):
            errors.append("malformed edge record")
            continue
        edge = item.get("id")
        source = item.get("from")
        target = item.get("to")
        edge_type = item.get("type")
        if not edge:
            errors.append("edge missing id")
            continue
        if str(edge) in edge_ids:
            errors.append(f"duplicate edge id: {edge}")
        edge_ids.add(str(edge))
        if not edge_type:
            errors.append(f"edge missing type: {edge}")
        if source not in node_ids:
            errors.append(f"dangling edge source: {edge}")
        if target not in node_ids:
            errors.append(f"dangling edge target: {edge}")
    for index_file in ["indexes/by-kind.json", "indexes/by-path.json", "indexes/by-relation.json"]:
        if not (graph_dir / index_file).is_file():
            errors.append(f"missing graph index: {index_file}")
    manifest = graph["manifest"]
    if isinstance(manifest, dict):
        if strict and manifest.get("schema") != GRAPH_SCHEMA:
            errors.append(f"manifest schema is not {GRAPH_SCHEMA}")
        if strict and manifest.get("node_count") != len(nodes):
            errors.append("manifest node_count does not match nodes.jsonl")
        if strict and manifest.get("edge_count") != len(edges):
            errors.append("manifest edge_count does not match edges.jsonl")
        if strict:
            for expected in ["indexes/by-kind.json", "indexes/by-path.json", "indexes/by-relation.json"]:
                indexes = manifest.get("indexes")
                if not isinstance(indexes, list) or expected not in indexes:
                    errors.append(f"manifest missing graph index entry: {expected}")
    elif strict:
        errors.append("manifest is missing or invalid")
    status = "ok" if not errors else "failed"
    return {
        "status": status,
        "errors": errors,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
        "manifest": graph["manifest"],
    }


def doc_snapshot(doc: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in doc.items()
        if key in {"id", "type", "path", "title", "summary", "terms", "text_hash", "sources"}
    }


def resolve_memory_reference(root: Path, local_dir: Path, value: str) -> Path | None:
    ref = normalize_graph_path(value)
    if not ref:
        return None
    raw = Path(ref)
    candidates = [raw] if raw.is_absolute() else [root / raw, local_dir / raw]
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    return None


def local_relative_path(path: Path, local_dir: Path, root: Path) -> str:
    try:
        return path.relative_to(local_dir).as_posix()
    except ValueError:
        return relpath(path, root)


DREAM_SCHEMA = "fable-harness-memory-dream-v2"
DREAM_NOTE_COMPACT_BYTES = 2400
DREAM_NOTE_STALE_DAYS = 180
DREAM_CONTEXT_RELEVANCE_THRESHOLD = 0.35


def dream_action(
    action: str,
    path: str,
    reason: str,
    mode: str,
    risk: str,
    safe_to_apply: bool,
    requires_review: bool,
    source: str,
    signals: dict[str, object] | None = None,
    **extra: object,
) -> dict[str, object]:
    item: dict[str, object] = {
        "action": action,
        "path": normalize_graph_path(path),
        "reason": reason,
        "mode": mode,
        "risk": risk,
        "safe_to_apply": safe_to_apply,
        "requires_review": requires_review,
        "source": source,
        "signals": signals or {},
    }
    item.update(extra)
    return item


def note_dream_signals(root: Path, doc: dict[str, object], touch_index: dict[str, object]) -> dict[str, object]:
    path_value = normalize_graph_path(str(doc.get("path", "")))
    path = (root / path_value).resolve()
    text = str(doc.get("text", ""))
    size = path.stat().st_size if path.is_file() else len(text.encode("utf-8"))
    verified = frontmatter_value(text, "last_verified") or ""
    verified_date = parse_date(verified) if verified else None
    stale_days = None
    if verified_date:
        stale_days = (dt.date.today() - verified_date).days
    touch = touch_entry(touch_index, path_value)
    return {
        "size_bytes": size,
        "size_limit_bytes": DREAM_NOTE_COMPACT_BYTES,
        "last_verified": verified,
        "stale_days": stale_days,
        "use_count": int(touch.get("use_count", 0)) if touch else 0,
        "last_used_at": str(touch.get("last_used_at", "")) if touch else "",
        "last_reason": str(touch.get("last_reason", "")) if touch else "",
    }


def compact_note_reason(signals: dict[str, object]) -> str:
    reasons: list[str] = []
    if int(signals.get("size_bytes", 0)) > DREAM_NOTE_COMPACT_BYTES:
        reasons.append(f"note exceeds {DREAM_NOTE_COMPACT_BYTES} bytes")
    stale_days = signals.get("stale_days")
    if isinstance(stale_days, int) and stale_days > DREAM_NOTE_STALE_DAYS:
        reasons.append(f"last_verified is older than {DREAM_NOTE_STALE_DAYS} days")
    return "; ".join(reasons)


def review_only_dream_actions(root: Path, docs: list[dict[str, object]], touch_index: dict[str, object]) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    for doc in docs:
        if doc.get("type") != "note":
            continue
        path = normalize_graph_path(str(doc.get("path", "")))
        signals = note_dream_signals(root, doc, touch_index)
        reason = compact_note_reason(signals)
        if not reason:
            continue
        actions.append(dream_action(
            "compact-note",
            path,
            reason + "; create or update a compact canonical note only after orchestrator review",
            "semantic-review",
            "medium",
            False,
            True,
            "active-index",
            signals,
        ))
    return actions


def dream_action_context_text(action: dict[str, object]) -> str:
    signals = action.get("signals")
    signal_text = ""
    if isinstance(signals, dict):
        signal_text = " ".join(str(value) for value in signals.values() if isinstance(value, (str, int)))
    return " ".join([
        str(action.get("action", "")),
        str(action.get("path", "")),
        str(action.get("reason", "")),
        str(action.get("source", "")),
        str(action.get("dormant_copy", "")),
        signal_text,
    ])


def dream_context_relevance(action: dict[str, object], context: str) -> dict[str, object]:
    context = context.strip()
    if not context:
        return {
            "context": "",
            "score": 0.0,
            "threshold": DREAM_CONTEXT_RELEVANCE_THRESHOLD,
            "decision": "no-context",
        }
    action_text = dream_action_context_text(action)
    context_terms = set(top_terms(context, limit=32))
    action_terms = set(top_terms(action_text, limit=64))
    lexical = 0.0
    if context_terms:
        lexical = len(context_terms & action_terms) / len(context_terms)
    semantic = max(0.0, cosine(vector(context), vector(action_text)))
    score = round(max(lexical, semantic * 0.5), 4)
    decision = "context-cold" if score < DREAM_CONTEXT_RELEVANCE_THRESHOLD else "agent-review"
    return {
        "context": context,
        "score": score,
        "threshold": DREAM_CONTEXT_RELEVANCE_THRESHOLD,
        "decision": decision,
        "overlap_terms": sorted(context_terms & action_terms),
    }


def annotate_dream_actions_for_context(actions: list[dict[str, object]], context: str) -> None:
    for action in actions:
        relevance = dream_context_relevance(action, context)
        signals = action.setdefault("signals", {})
        if isinstance(signals, dict):
            signals["context_relevance"] = relevance
        if not context:
            continue
        if (
            action.get("mode") == "mechanical"
            and action.get("risk") == "low"
            and action.get("safe_to_apply") is True
            and action.get("requires_review") is False
            and relevance["decision"] == "agent-review"
        ):
            action["safe_to_apply"] = False
            action["requires_review"] = True
            action["mode"] = "agent-review"
            action["risk"] = "medium"
            action["reason"] = str(action.get("reason", "")) + "; held for agent review because it is relevant to the current context"


def write_agent_review_packet(run_dir: Path, diff: dict[str, object], context: str) -> Path:
    actions = diff.get("actions", [])
    review_actions = [
        action
        for action in actions
        if isinstance(action, dict) and action.get("requires_review") is True
    ] if isinstance(actions, list) else []
    lines = [
        "# Agent Memory Review",
        "",
        f"- Run ID: `{diff.get('run_id', run_dir.name)}`",
        f"- Context: {context or '(none supplied)'}",
        f"- Review actions: {len(review_actions)}",
        "",
        "## Orchestrator Instructions",
        "",
        "- Decide whether each item is still needed for the current task, plan, or project stage.",
        "- Keep active memory when it is relevant to current work.",
        "- Compact or archive only after preserving durable facts in canonical notes.",
        "- Escalate to the user only for product decisions, conflicting canonical decisions, or possible loss of primary evidence.",
        "",
        "## Review Queue",
        "",
    ]
    if not review_actions:
        lines.append("- none")
    for action in review_actions:
        signals = action.get("signals", {})
        relevance = signals.get("context_relevance", {}) if isinstance(signals, dict) else {}
        score = relevance.get("score", "") if isinstance(relevance, dict) else ""
        lines.extend([
            f"- `{action.get('action', '')}`: `{action.get('path', '')}`",
            f"  - mode: {action.get('mode', '')}",
            f"  - risk: {action.get('risk', '')}",
            f"  - reason: {action.get('reason', '')}",
            f"  - context_score: {score}",
        ])
    review_path = run_dir / "agent-review.md"
    review_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return review_path


def write_auto_applied_packet(run_dir: Path, diff: dict[str, object]) -> Path:
    actions = diff.get("actions", [])
    auto_path = run_dir / "auto-applied.jsonl"
    auto_path.write_text("", encoding="utf-8")
    if isinstance(actions, list):
        for action in actions:
            if not isinstance(action, dict):
                continue
            if action.get("safe_to_apply") is True and action.get("requires_review") is False:
                append_jsonl(auto_path, {
                    "action": action.get("action", ""),
                    "path": action.get("path", ""),
                    "mode": action.get("mode", ""),
                    "risk": action.get("risk", ""),
                    "reason": action.get("reason", ""),
                    "source": action.get("source", ""),
                    "signals": action.get("signals", {}),
                })
    return auto_path


def initialize_agent_decisions_packet(run_dir: Path) -> Path:
    decisions_path = run_dir / "agent-decisions.jsonl"
    decisions_path.write_text("", encoding="utf-8")
    return decisions_path


def create_dream_plan(root: Path, agent: str = "auto", context: str = "") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    memory_dir = local_dir / "memory"
    dreams_dir = memory_dir / "dreams"
    runs_dir = dreams_dir / "runs"
    run_id = dream_run_id(root)
    run_dir = runs_dir / run_id
    while run_dir.exists():
        run_id = dream_run_id(root)
        run_dir = runs_dir / run_id

    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    dormant_dir = output_dir / "dormant-items"
    dormant_dir.mkdir(parents=True, exist_ok=True)
    created_at = dt.datetime.now(dt.timezone.utc).isoformat()

    docs = iter_markdown_docs(local_dir, dormant_excluded_paths(local_dir))
    active_index = {
        "generated_at": created_at,
        "local_dir": relpath(local_dir, root),
        "documents": [doc_snapshot(doc) for doc in docs],
    }
    write_json(input_dir / "active-index.json", active_index)

    existing_dormant = read_json(dreams_dir / "dormant-index.json", {"items": []})
    write_json(input_dir / "dormant-index.json", existing_dormant)

    touch_index = load_touch_index(local_dir)
    write_json(input_dir / "touch-index.json", touch_index)

    graph = load_graph(root, agent)
    graph_snapshot = {
        "manifest": graph["manifest"],
        "nodes": graph["nodes"],
        "edges": graph["edges"],
    }
    write_json(input_dir / "graph-snapshot.json", graph_snapshot)

    actions: list[dict[str, object]] = []
    dormant_items: list[dict[str, object]] = []
    seen_traces: set[str] = set()
    promotion_log = read_jsonl(memory_dir / "promotion_log.jsonl")
    for entry in promotion_log:
        trace_ref = str(entry.get("trace", ""))
        trace_path = resolve_memory_reference(root, local_dir, trace_ref)
        if trace_path is None:
            continue
        trace_rel = relpath(trace_path, root)
        if trace_rel in seen_traces:
            continue
        seen_traces.add(trace_rel)
        text = trace_path.read_text(encoding="utf-8")
        dormant_rel = local_relative_path(trace_path, local_dir, root)
        dormant_path = dormant_dir / dormant_rel
        dormant_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(trace_path, dormant_path)
        trace_hash = file_hash(trace_path)
        dormant_copy = relpath(dormant_path, run_dir)
        item = {
            "path": trace_rel,
            "title": file_title(text, trace_path.stem),
            "summary": compact_summary(text),
            "terms": top_terms(text),
            "sha256": trace_hash,
            "copy": dormant_copy,
        }
        dormant_items.append(item)
        actions.append(dream_action(
            "archive-promoted-trace",
            trace_rel,
            "trace has promotion-log evidence; dry-run copied it into dormant review output",
            "mechanical",
            "low",
            True,
            False,
            "promotion-log",
            {
                "promotion_log": True,
                "sha256": trace_hash,
                "title": item["title"],
            },
            dormant_copy=dormant_copy,
            sha256=trace_hash,
        ))

    actions.extend(review_only_dream_actions(root, docs, touch_index))
    annotate_dream_actions_for_context(actions, context)

    maintenance_report = {
        "generated_at": created_at,
        "mode": "dream-plan-dry-run",
        "context": context,
        "candidates": actions,
        "counts": {
            "active_documents": len(docs),
            "dormant_items": len(dormant_items),
        },
    }
    write_json(input_dir / "maintenance-report.json", maintenance_report)

    write_json(output_dir / "dormant-index.json", {
        "generated_at": created_at,
        "items": dormant_items,
    })
    diff = {
        "schema": DREAM_SCHEMA,
        "version": 2,
        "run_id": run_id,
        "generated_at": created_at,
        "dry_run": True,
        "context": context,
        "actions": actions,
    }
    write_json(run_dir / "diff.json", diff)

    manifest = {
        "version": 1,
        "kind": "memory-dream-plan",
        "schema": DREAM_SCHEMA,
        "run_id": run_id,
        "created_at": created_at,
        "root": str(root),
        "local_dir": relpath(local_dir, root),
        "dry_run": True,
        "context": context,
        "action_count": len(actions),
        "safe_action_count": len([action for action in actions if action.get("safe_to_apply") is True]),
        "review_action_count": len([action for action in actions if action.get("requires_review") is True]),
        "inputs": [
            "input/active-index.json",
            "input/dormant-index.json",
            "input/touch-index.json",
            "input/graph-snapshot.json",
            "input/maintenance-report.json",
        ],
        "outputs": [
            "output/dormant-index.json",
            "output/dormant-items",
            "diff.json",
            "report.md",
        ],
    }
    write_json(run_dir / "manifest.json", manifest)

    lines = [
        "# Memory Dream Plan",
        "",
        f"- Run ID: `{run_id}`",
        f"- Created: {created_at}",
        f"- Mode: dry-run",
        f"- Context: {context or '(none supplied)'}",
        f"- Actions: {len(actions)}",
        "",
        "## Actions",
        "",
    ]
    if actions:
        for action in actions:
            if action.get("dormant_copy"):
                lines.append(f"- {action['action']} ({action['mode']}, {action['risk']}): `{action['path']}` -> `{action['dormant_copy']}`")
            else:
                lines.append(f"- {action['action']} ({action['mode']}, {action['risk']}): `{action['path']}`")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Review Files",
        "",
        "- `manifest.json`",
        "- `diff.json`",
        "- `input/active-index.json`",
        "- `output/dormant-items/`",
    ])
    (run_dir / "report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    append_jsonl(dreams_dir / "log.jsonl", {
        "run_id": run_id,
        "run_dir": relpath(run_dir, root),
        "created_at": created_at,
        "action_count": len(actions),
        "status": "planned",
    })
    return {"run_id": run_id, "run_dir": str(run_dir), "action_count": len(actions)}


def resolve_dream_run(root: Path, local_dir: Path, run: str) -> Path:
    raw = Path(run)
    candidates = [raw] if raw.is_absolute() else [
        root / raw,
        local_dir / "memory" / "dreams" / "runs" / run,
    ]
    runs_dir = (local_dir / "memory" / "dreams" / "runs").resolve()
    for candidate in candidates:
        resolved = candidate.resolve()
        if not resolved.exists():
            continue
        if not is_relative_to(resolved, runs_dir):
            raise ValueError(f"dream run is outside memory dreams runs directory: {run}")
        if not resolved.is_dir():
            raise ValueError(f"dream run is not a directory: {run}")
        return resolved
    raise ValueError(f"dream run not found: {run}")


def dormant_item_tail(dormant_copy: str, original_path: str) -> str:
    value = normalize_graph_path(dormant_copy)
    prefix = "output/dormant-items/"
    if value.startswith(prefix):
        tail = value[len(prefix):]
    else:
        tail = normalize_graph_path(original_path)
    return tail.lstrip("/")


def upsert_dormant_item(
    manifest: dict[str, object],
    original_path: str,
    dormant_path: str,
    sha256: str,
    run_id: str,
    action: dict[str, object],
) -> bool:
    items = manifest.setdefault("items", [])
    if not isinstance(items, list):
        items = []
        manifest["items"] = items
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("original_path") == original_path and item.get("sha256") == sha256:
            item.update({
                "dormant_path": dormant_path,
                "state": "dormant",
                "last_applied_run": run_id,
            })
            return False
    items.append({
        "id": hashlib.sha256(f"{original_path}:{sha256}".encode("utf-8")).hexdigest()[:20],
        "original_path": original_path,
        "dormant_path": dormant_path,
        "sha256": sha256,
        "state": "dormant",
        "archived_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_run": run_id,
        "action": action.get("action", "archive-promoted-trace"),
        "reason": action.get("reason", ""),
    })
    return True


def apply_dream_run(root: Path, run: str, agent: str = "auto") -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    run_dir = resolve_dream_run(root, local_dir, run)
    diff = read_json(run_dir / "diff.json")
    if not isinstance(diff, dict):
        raise ValueError("dream run diff.json must contain an object")
    if diff.get("schema") != DREAM_SCHEMA or diff.get("version") != 2:
        raise ValueError(f"dream run diff.json schema must be {DREAM_SCHEMA} version 2")
    actions = diff.get("actions")
    if not isinstance(actions, list):
        raise ValueError("dream run diff.json is missing actions")
    run_id = str(diff.get("run_id") or run_dir.name)

    manifest = load_dormant_manifest(local_dir)
    copied = 0
    new_items = 0
    skipped_review_actions = 0
    skipped_unsafe_actions = 0
    skipped_unsupported_actions = 0
    unsupported_actions: list[dict[str, object]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        safe_to_apply = action.get("safe_to_apply")
        requires_review = action.get("requires_review")
        if requires_review is True:
            skipped_review_actions += 1
            continue
        if safe_to_apply is not True or requires_review is not False:
            skipped_unsafe_actions += 1
            continue
        if action.get("action") != "archive-promoted-trace":
            skipped_unsupported_actions += 1
            unsupported_actions.append({
                "action": action.get("action", ""),
                "path": action.get("path", ""),
                "reason": "safe action type is not supported by this apply implementation",
            })
            continue
        original_value = action.get("path")
        dormant_copy_value = action.get("dormant_copy")
        sha256_value = action.get("sha256")
        if not isinstance(original_value, str) or not isinstance(dormant_copy_value, str) or not isinstance(sha256_value, str):
            raise ValueError("archive-promoted-trace action requires path, dormant_copy, and sha256")
        original_ref = Path(normalize_graph_path(original_value))
        source_path = (original_ref if original_ref.is_absolute() else root / original_ref).resolve()
        if not is_relative_to(source_path, root):
            raise ValueError(f"dream action path is outside workspace: {original_value}")
        original_path = relpath(source_path, root)
        if not source_path.is_file():
            raise ValueError(f"dream action source is missing: {original_path}")
        if file_hash(source_path) != sha256_value:
            raise ValueError(f"dream action source hash changed: {original_path}")

        dormant_copy = (run_dir / normalize_graph_path(dormant_copy_value)).resolve()
        if not is_relative_to(dormant_copy, run_dir):
            raise ValueError(f"dream dormant copy is outside the run: {dormant_copy_value}")
        if not dormant_copy.is_file():
            raise ValueError(f"dream dormant copy is missing: {dormant_copy_value}")
        if file_hash(dormant_copy) != sha256_value:
            raise ValueError(f"dream dormant copy hash does not match source: {dormant_copy_value}")

        items_dir = (local_dir / "memory" / "dormant" / "items").resolve()
        destination = (items_dir / dormant_item_tail(dormant_copy_value, original_path)).resolve()
        if not is_relative_to(destination, items_dir):
            raise ValueError(f"dream dormant destination is outside dormant items: {dormant_copy_value}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dormant_copy, destination)
        copied += 1
        if upsert_dormant_item(
            manifest,
            original_path,
            relpath(destination, root),
            sha256_value,
            run_id,
            action,
        ):
            new_items += 1

    write_dormant_manifest(local_dir, manifest)
    append_jsonl(local_dir / "memory" / "dreams" / "log.jsonl", {
        "run_id": run_id,
        "run_dir": relpath(run_dir, root),
        "applied_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "copied": copied,
        "new_items": new_items,
        "skipped_review_actions": skipped_review_actions,
        "skipped_unsafe_actions": skipped_unsafe_actions,
        "skipped_unsupported_actions": skipped_unsupported_actions,
        "unsupported_actions": unsupported_actions,
        "status": "applied",
    })
    memory_manifest = build_memory(root, agent)
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "copied": copied,
        "new_items": new_items,
        "skipped_review_actions": skipped_review_actions,
        "skipped_unsafe_actions": skipped_unsafe_actions,
        "skipped_unsupported_actions": skipped_unsupported_actions,
        "unsupported_actions": unsupported_actions,
        "dormant_manifest": str(dormant_manifest_path(local_dir)),
        "memory_document_count": memory_manifest["document_count"],
    }


def maintain_memory_dream(
    root: Path,
    agent: str = "auto",
    context: str = "",
    auto_safe: bool = False,
    agent_review: bool = True,
) -> dict[str, object]:
    plan = create_dream_plan(root, agent, context)
    run_dir = Path(str(plan["run_dir"]))
    diff = read_json(run_dir / "diff.json")
    if not isinstance(diff, dict):
        raise ValueError("dream run diff.json must contain an object")

    review_path: Path | None = None
    decisions_path: Path | None = None
    if agent_review:
        review_path = write_agent_review_packet(run_dir, diff, context)
        decisions_path = initialize_agent_decisions_packet(run_dir)

    applied = {
        "copied": 0,
        "new_items": 0,
        "skipped_review_actions": 0,
        "skipped_unsafe_actions": 0,
        "skipped_unsupported_actions": 0,
        "unsupported_actions": [],
        "memory_document_count": None,
    }
    auto_applied_path: Path | None = None
    if auto_safe:
        applied = apply_dream_run(root, str(run_dir), agent)
        auto_applied_path = write_auto_applied_packet(run_dir, diff)

    actions = diff.get("actions", [])
    review_action_count = len([
        action
        for action in actions
        if isinstance(action, dict) and action.get("requires_review") is True
    ]) if isinstance(actions, list) else 0
    safe_action_count = len([
        action
        for action in actions
        if isinstance(action, dict) and action.get("safe_to_apply") is True
    ]) if isinstance(actions, list) else 0

    manifest_path = run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if isinstance(manifest, dict):
        manifest["kind"] = "memory-dream-maintenance"
        manifest["auto_safe"] = auto_safe
        manifest["agent_review"] = relpath(review_path, run_dir) if review_path else ""
        manifest["agent_decisions"] = relpath(decisions_path, run_dir) if decisions_path else ""
        manifest["auto_applied_log"] = relpath(auto_applied_path, run_dir) if auto_applied_path else ""
        manifest["review_action_count"] = review_action_count
        manifest["safe_action_count"] = safe_action_count
        manifest["auto_applied"] = {
            "copied": applied.get("copied", 0),
            "new_items": applied.get("new_items", 0),
            "skipped_review_actions": applied.get("skipped_review_actions", 0),
            "skipped_unsafe_actions": applied.get("skipped_unsafe_actions", 0),
            "skipped_unsupported_actions": applied.get("skipped_unsupported_actions", 0),
        }
        outputs = manifest.setdefault("outputs", [])
        if isinstance(outputs, list) and review_path:
            outputs.append("agent-review.md")
        if isinstance(outputs, list) and decisions_path:
            outputs.append("agent-decisions.jsonl")
        if isinstance(outputs, list) and auto_applied_path:
            outputs.append("auto-applied.jsonl")
        write_json(manifest_path, manifest)

    local_dir = find_local_dir(root.resolve(), agent)
    append_jsonl(local_dir / "memory" / "dreams" / "log.jsonl", {
        "run_id": plan["run_id"],
        "run_dir": relpath(run_dir, root.resolve()),
        "maintained_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "context": context,
        "auto_safe": auto_safe,
        "agent_review": relpath(review_path, root.resolve()) if review_path else "",
        "safe_action_count": safe_action_count,
        "review_action_count": review_action_count,
        "copied": applied.get("copied", 0),
        "status": "maintained",
    })

    return {
        "run_id": plan["run_id"],
        "run_dir": str(run_dir),
        "context": context,
        "auto_safe": auto_safe,
        "safe_action_count": safe_action_count,
        "review_action_count": review_action_count,
        "agent_review": str(review_path) if review_path else "",
        "agent_decisions": str(decisions_path) if decisions_path else "",
        "auto_applied_log": str(auto_applied_path) if auto_applied_path else "",
        "auto_applied": applied,
    }


def dormant_item_kind(item: dict[str, object], original_path: str) -> str:
    kind = str(item.get("kind", "")).strip()
    if kind:
        return kind
    normalized = f"/{normalize_graph_path(original_path)}"
    if "/decision-traces/" in normalized:
        return "trace"
    if "/notes/" in normalized:
        return "note"
    return "dormant"


def search_dormant_memory(root: Path, query: str, agent: str = "auto", limit: int = 5) -> list[dict[str, object]]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    manifest = load_dormant_manifest(local_dir)
    query_terms = set(top_terms(query, limit=32))
    query_vector = vector(query)
    results: list[dict[str, object]] = []
    items = manifest.get("items", [])
    if not isinstance(items, list):
        return results
    for item in items:
        if not isinstance(item, dict) or item.get("state") != "dormant":
            continue
        dormant_value = item.get("dormant_path")
        original_value = item.get("original_path") or item.get("path")
        if not isinstance(dormant_value, str) or not isinstance(original_value, str):
            continue
        dormant_path = normalize_graph_path(dormant_value)
        original_path = normalize_graph_path(original_value)
        raw_path = Path(dormant_path)
        path = (raw_path if raw_path.is_absolute() else root / raw_path).resolve()
        if not is_relative_to(path, root) or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        terms = set(top_terms(text, limit=64))
        score = cosine(query_vector, vector(text))
        if query_terms:
            score += len(query_terms.intersection(terms)) * 0.05
        if score <= 0:
            continue
        results.append({
            "score": round(score, 6),
            "title": str(item.get("title") or file_title(text, Path(original_path).stem)),
            "original_path": original_path,
            "dormant_path": dormant_path,
            "kind": dormant_item_kind(item, original_path),
            "summary": compact_summary(text),
        })
    results.sort(key=lambda item: (-float(item["score"]), str(item["original_path"])))
    return results[:limit]


def note_path(local_dir: Path, category: str, area: str | None, topic: str) -> Path:
    pieces = [slugify(category)]
    if area:
        pieces.append(slugify(area))
    pieces.append(slugify(topic) + ".md")
    return local_dir / "notes" / Path(*pieces)


def create_note(
    root: Path,
    category: str,
    area: str | None,
    topic: str,
    title: str | None = None,
    source_trace: Path | None = None,
    body: str | None = None,
    agent: str = "auto",
) -> Path:
    local_dir = find_local_dir(root.resolve(), agent)
    path = note_path(local_dir, category, area, topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    title = title or topic.replace("-", " ").title()
    scope = "/".join(slugify(piece) for piece in [category, area, topic] if piece)
    category_slug = slugify(category)
    area_slug = slugify(area) if area else ""
    topic_slug = slugify(topic)
    moc_rel = relpath(note_moc_path(local_dir, category_slug), path.parent)
    tags = [f"category/{category_slug}"]
    if area_slug:
        tags.append(f"area/{area_slug}")
    tags.append(f"topic/{topic_slug}")
    properties = [f"category={category_slug}", f"topic={topic_slug}", f"scope={scope}"]
    if area_slug:
        properties.insert(1, f"area={area_slug}")
    tag_lines = "".join(f"  - {tag}\n" for tag in tags)
    property_lines = "".join(f"  - {prop}\n" for prop in properties)
    source_block = ""
    if source_trace:
        source_block = f"  - {relpath(source_trace.resolve(), path.parent)}\n"
    sources_section = source_block
    default_body = """## Durable Fact Or Decision

-

## Connections

- MOC: `{moc_rel}`
- Related:

## Validation

- Atomic: one idea only.
- Thesis title: the title states the claim.
- Connects: this note links to its MOC.
- Unique: scope is unique among active canonical notes.
- Metadata: tags and properties are queryable.

## Evidence

-

## Operational Use

-

## Revalidation

-""".format(moc_rel=moc_rel)
    body_text = body or default_body
    content = f"""# {title}

---
memory_schema: atomic-v1
type: canonical-decision
status: active
scope: {scope}
canonical: true
thesis: {title}
atomic: true
tags:
{tag_lines}properties:
{property_lines}moc: {moc_rel}
links:
  - {moc_rel}
sources:
{sources_section}last_verified: {dt.date.today().isoformat()}
supersedes:
validation:
  - atomic
  - thesis-title
  - connects
  - unique
  - metadata
---

{body_text}
"""
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    update_notes_index(local_dir)
    build_memory(root, agent)
    return path


def bounded_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def lexical_relevance(query_terms: set[str], record_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    return bounded_score(len(query_terms.intersection(record_terms)) / max(1, len(query_terms)))


def graph_relevance(query_terms: set[str], record: dict[str, object]) -> float:
    graph_terms = {str(term) for term in record.get("graph_terms", [])}
    if not query_terms or not graph_terms:
        return 0.0
    return bounded_score(len(query_terms.intersection(graph_terms)) / max(1, len(query_terms)))


def rerank_relevance(query: str, query_terms: set[str], record: dict[str, object]) -> float:
    haystack_parts = [
        str(record.get("title", "")),
        str(record.get("thesis", "")),
        str(record.get("heading", "")),
        str(record.get("summary", "")),
        str(record.get("snippet", "")),
        " ".join(str(tag) for tag in record.get("tags", [])),
        " ".join(str(prop) for prop in record.get("properties", [])),
        str(record.get("moc", "")),
        " ".join(str(link) for link in record.get("links", [])),
        str(record.get("path", "")),
    ]
    haystack = " ".join(haystack_parts).lower()
    score = 0.0
    normalized_query = " ".join(tokens(query)).lower()
    if normalized_query and normalized_query in haystack:
        score += 0.45
    if query_terms:
        title_heading = " ".join(haystack_parts[:2]).lower()
        heading_hits = sum(1 for term in query_terms if term in title_heading)
        snippet_hits = sum(1 for term in query_terms if term in haystack)
        score += min(0.35, heading_hits * 0.07)
        score += min(0.20, snippet_hits * 0.03)
    if record.get("kind") == "chunk":
        score += 0.08
    return bounded_score(score)


def score_memory_record(query: str, query_terms: set[str], query_vector: list[list[float]], record: dict[str, object]) -> tuple[float, dict[str, float]]:
    record_terms = {str(term) for term in record.get("terms", [])}
    vector_score = bounded_score(cosine(query_vector, record.get("vector", [])))
    lexical_score = lexical_relevance(query_terms, record_terms)
    graph_score = graph_relevance(query_terms, record)
    rerank_score = rerank_relevance(query, query_terms, record)
    type_boost = 0.05 if record.get("type") == "note" else 0.0
    score = (
        vector_score * HYBRID_SCORE_WEIGHTS["vector"]
        + lexical_score * HYBRID_SCORE_WEIGHTS["lexical"]
        + graph_score * HYBRID_SCORE_WEIGHTS["graph"]
        + rerank_score * HYBRID_SCORE_WEIGHTS["rerank"]
        + type_boost
    )
    return score, {
        "vector": round(vector_score, 6),
        "lexical": round(lexical_score, 6),
        "graph": round(graph_score, 6),
        "rerank": round(rerank_score, 6),
        "type_boost": round(type_boost, 6),
    }


def search_result(record: dict[str, object], shard_id: str, score: float, breakdown: dict[str, float]) -> dict[str, object]:
    path = str(record.get("parent_path") or record.get("path", ""))
    start_line = record.get("start_line")
    end_line = record.get("end_line")
    if isinstance(start_line, int):
        citation = str(record.get("citation") or citation_for(path, start_line, int(end_line or start_line)))
    else:
        citation = str(record.get("citation") or citation_for(path))
    result = {
        "score": round(score, 6),
        "path": path,
        "title": record.get("title", ""),
        "type": record.get("type", ""),
        "kind": record.get("kind", "document"),
        "summary": record.get("summary", ""),
        "snippet": record.get("snippet") or record.get("summary", ""),
        "heading": record.get("heading", record.get("title", "")),
        "citation": citation,
        "score_breakdown": breakdown,
        "shard": shard_id,
    }
    if isinstance(start_line, int):
        result["start_line"] = start_line
    if isinstance(end_line, int):
        result["end_line"] = end_line
    if record.get("parent_id"):
        result["parent_id"] = record["parent_id"]
    for key in ["memory_schema", "thesis", "atomic", "tags", "properties", "moc", "links", "validation"]:
        if key in record:
            result[key] = record[key]
    return result


def diversify_results(results: list[dict[str, object]]) -> list[dict[str, object]]:
    parent_counts: dict[str, int] = {}
    adjusted: list[dict[str, object]] = []
    for item in sorted(results, key=lambda value: -float(value["score"])):
        parent = str(item.get("parent_id") or item.get("path"))
        count = parent_counts.get(parent, 0)
        if count:
            item = dict(item)
            penalty = min(0.12, count * 0.04)
            item["score"] = round(max(0.0, float(item["score"]) - penalty), 6)
            breakdown = dict(item.get("score_breakdown", {}))
            breakdown["diversity_penalty"] = round(penalty, 6)
            item["score_breakdown"] = breakdown
        parent_counts[parent] = count + 1
        adjusted.append(item)
    adjusted.sort(key=lambda item: (0 if item.get("type") == "note" else 1, -float(item["score"]), str(item.get("path", "")), int(item.get("start_line", 0) or 0)))
    return adjusted


def reactivation_body(query: str, candidate: dict[str, object], dormant_text: str) -> str:
    summary = compact_summary(dormant_text, limit=700) or "No compact excerpt was available."
    original_path = normalize_graph_path(str(candidate["original_path"]))
    dormant_path = normalize_graph_path(str(candidate["dormant_path"]))
    return "\n".join([
        "## Durable Fact Or Decision",
        "",
        f"Dormant evidence matched `{query}` and was reactivated as a compact active note.",
        "",
        "## Dormant Evidence",
        "",
        f"- Original path: `{original_path}`",
        f"- Dormant path: `{dormant_path}`",
        f"- Matched excerpt: {summary}",
        "",
        "## Operational Use",
        "",
        "Use this note as the active retrieval surface and keep the dormant file as source evidence.",
        "",
        "## Revalidation",
        "",
        "- Re-run memory graph checks after changing dormant reactivation records.",
    ])


def upsert_reactivation(
    manifest: dict[str, object],
    entry: dict[str, object],
) -> None:
    reactivations = manifest.setdefault("reactivations", [])
    if not isinstance(reactivations, list):
        reactivations = []
        manifest["reactivations"] = reactivations
    for existing in reactivations:
        if not isinstance(existing, dict):
            continue
        if (
            existing.get("query") == entry.get("query")
            and existing.get("dormant_path") == entry.get("dormant_path")
            and existing.get("note_path") == entry.get("note_path")
        ):
            existing.update(entry)
            return
    reactivations.append(entry)


def reactivate_dormant_memory(
    root: Path,
    query: str,
    category: str,
    area: str | None,
    topic: str,
    agent: str = "auto",
    apply: bool = False,
) -> dict[str, object]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    target_note = note_path(local_dir, category, area, topic)
    note_rel = relpath(target_note, root)
    matches = search_dormant_memory(root, query, agent=agent, limit=1)
    if not matches:
        return {
            "status": "not-found",
            "query": query,
            "note_path": note_rel,
            "candidate": None,
        }

    candidate = matches[0]
    result: dict[str, object] = {
        "status": "planned",
        "query": query,
        "note_path": note_rel,
        "candidate": candidate,
    }
    if not apply:
        return result

    dormant_value = normalize_graph_path(str(candidate["dormant_path"]))
    dormant_path = (root / dormant_value).resolve()
    if not is_relative_to(dormant_path, root) or not dormant_path.is_file():
        raise ValueError(f"dormant evidence is missing: {dormant_value}")
    dormant_text = dormant_path.read_text(encoding="utf-8")
    note = create_note(
        root,
        category,
        area,
        topic,
        title=str(candidate.get("title") or topic.replace("-", " ").title()),
        source_trace=dormant_path,
        body=reactivation_body(query, candidate, dormant_text),
        agent=agent,
    )

    manifest = load_dormant_manifest(local_dir)
    entry = {
        "reactivated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "query": query,
        "dormant_path": dormant_value,
        "original_path": normalize_graph_path(str(candidate["original_path"])),
        "note_path": relpath(note, root),
        "action": "reactivate-dormant-memory",
        "reason": "dormant evidence matched reactivation query",
    }
    upsert_reactivation(manifest, entry)
    write_dormant_manifest(local_dir, manifest)
    memory_manifest = build_memory(root, agent)
    result.update({
        "status": "applied",
        "note_path": relpath(note, root),
        "reactivation": entry,
        "memory_document_count": memory_manifest["document_count"],
    })
    return result


def append_source_to_existing_note(path: Path, source: str) -> None:
    text = path.read_text(encoding="utf-8")
    if source in text:
        return
    lines = text.splitlines()
    output: list[str] = []
    inserted = False
    in_sources = False
    for line in lines:
        stripped = line.strip()
        if stripped == "sources:":
            in_sources = True
            output.append(line)
            continue
        if in_sources and stripped and not line.startswith(" ") and not line.startswith("-"):
            output.append(f"  - {source}")
            inserted = True
            in_sources = False
        output.append(line)
    if in_sources and not inserted:
        output.append(f"  - {source}")
        inserted = True
    if not inserted:
        insert_at = len(output)
        for idx, line in enumerate(output):
            if idx > 0 and line.strip() == "---":
                insert_at = idx
                break
        output[insert_at:insert_at] = ["sources:", f"  - {source}"]
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def refresh_note_last_verified(path: Path) -> None:
    today = dt.date.today().isoformat()
    lines = []
    replaced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("last_verified:"):
            lines.append(f"last_verified: {today}")
            replaced = True
        else:
            lines.append(line)
    if not replaced:
        for idx, line in enumerate(lines):
            if idx > 0 and line.strip() == "---":
                lines.insert(idx, f"last_verified: {today}")
                break
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def append_trace_evidence(path: Path, trace: Path, root: Path, fact: str, verification: str) -> None:
    source = relpath(trace, root)
    text = path.read_text(encoding="utf-8").rstrip()
    if "## Additional Trace Evidence" not in text:
        text += "\n\n## Additional Trace Evidence\n"
    entry = f"\n- Source trace: `{source}`"
    if fact:
        entry += f" - {fact.replace(chr(10), ' ')}"
    if verification:
        entry += f" Verification: {verification.replace(chr(10), ' ')}"
    path.write_text(text.rstrip() + entry + "\n", encoding="utf-8")


def promote_trace(
    root: Path,
    trace: Path,
    category: str,
    area: str | None,
    topic: str,
    agent: str = "auto",
) -> Path:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    trace = trace.resolve()
    text = trace.read_text(encoding="utf-8")
    title = file_title(text, topic.replace("-", " ").title())
    objective = section(text, ("Objective",)) or compact_summary(text)
    decision = section(text, ("Decide", "Decision", "Durable Decision"))
    verification = section(text, ("Verify", "Verification"))
    fact = decision or objective
    verification_line = "- Verification: not recorded in trace"
    if verification:
        verification_line = "- Verification: " + verification.replace("\n", " ")
    path = note_path(local_dir, category, area, topic)
    if path.exists():
        append_source_to_existing_note(path, relpath(trace, path.parent))
        append_trace_evidence(path, trace, root, fact, verification)
        refresh_note_last_verified(path)
        update_notes_index(local_dir)
        memory = local_dir / "memory"
        append_jsonl(memory / "promotion_log.jsonl", {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "trace": relpath(trace, root),
            "note": relpath(path, root),
            "category": category,
            "area": area,
            "topic": topic,
        })
        build_memory(root, agent)
        return path
    body = f"""## Durable Fact Or Decision

{fact}

## Evidence

- Source trace: `{relpath(trace, root)}`
{verification_line}

## Operational Use

- Load this note before opening the full trace when the task touches `{area or category}`.

## Revalidation

- Reopen the source trace if this decision becomes contested or stale.
"""
    path = create_note(root, category, area, topic, title=title, source_trace=trace, body=body, agent=agent)
    memory = local_dir / "memory"
    append_jsonl(memory / "promotion_log.jsonl", {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "trace": relpath(trace, root),
        "note": relpath(path, root),
        "category": category,
        "area": area,
        "topic": topic,
    })
    build_memory(root, agent)
    return path


def search_memory(root: Path, query: str, agent: str = "auto", limit: int = 5, max_shards: int = 32) -> list[dict[str, object]]:
    root = root.resolve()
    local_dir = find_local_dir(root, agent)
    manifest_path = local_dir / "memory" / "manifest.json"
    if not manifest_path.exists():
        build_memory(root, agent)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    query_terms = set(top_terms(query, limit=32))
    query_vector = vector(query)
    shards = manifest.get("shards", [])
    candidates = [
        shard for shard in shards
        if query_terms.intersection(set(shard.get("terms", [])))
    ]
    if not candidates:
        candidates = shards[:max_shards]
    else:
        candidates = candidates[:max_shards]

    results: list[dict[str, object]] = []
    for shard in candidates:
        shard_path = root / str(shard["path"])
        if not shard_path.exists():
            continue
        for line in shard_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            score, breakdown = score_memory_record(query, query_terms, query_vector, doc)
            if score <= 0:
                continue
            results.append(search_result(doc, str(shard["id"]), score, breakdown))
    return diversify_results(results)[:limit]
'''

NEW_NOTE_SCRIPT = r'''#!/usr/bin/env python3
"""Create or update a semantic note in category/area/topic layout."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_core import create_note


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Fable Harness semantic note.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--category", required=True)
    parser.add_argument("--area")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--title")
    parser.add_argument("--source-trace")
    args = parser.parse_args()

    path = create_note(
        Path(args.root),
        args.category,
        args.area,
        args.topic,
        title=args.title,
        source_trace=Path(args.source_trace) if args.source_trace else None,
        agent=args.agent,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

PROMOTE_TRACE_SCRIPT = r'''#!/usr/bin/env python3
"""Promote a decision trace into a compact semantic note."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_core import promote_trace


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a trace into semantic memory.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--area")
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    path = promote_trace(
        Path(args.root),
        Path(args.trace),
        args.category,
        args.area,
        args.topic,
        agent=args.agent,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

REBUILD_MEMORY_SCRIPT = r'''#!/usr/bin/env python3
"""Rebuild sharded vector memory and knowledge graph from notes/traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import build_memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Fable Harness memory indexes.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    args = parser.parse_args()
    manifest = build_memory(Path(args.root), args.agent)
    print(json.dumps({
        "document_count": manifest["document_count"],
        "chunk_count": manifest.get("chunk_count", 0),
        "record_count": manifest.get("record_count", manifest["document_count"]),
        "chunking": manifest.get("chunking"),
        "cache_hits": manifest.get("cache", {}).get("hits", 0),
        "cache_misses": manifest.get("cache", {}).get("misses", 0),
        "shard_count": len(manifest["shards"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

MEMORY_SEARCH_SCRIPT = r'''#!/usr/bin/env python3
"""Search compact semantic notes and traces using local sharded embeddings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import search_memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Fable Harness memory.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = search_memory(
        Path(args.root),
        args.query,
        agent=args.agent,
        limit=args.limit,
        max_shards=args.max_shards,
    )
    if args.json:
        print(json.dumps(results, ensure_ascii=False))
    else:
        for result in results:
            print(f"{result['score']:.4f} {result['path']} - {result['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

RAG_EVAL_SCRIPT = r'''#!/usr/bin/env python3
"""Evaluate Fable Harness retrieval with local recall/precision metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import normalize_graph_path, search_memory


def load_cases(path: Path) -> list[dict[str, object]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("cases", [])
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    cases: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            cases.append(item)
    return cases


def relevant_targets(case: dict[str, object]) -> list[str]:
    raw = case.get("relevant", [])
    if isinstance(raw, str):
        return [normalize_graph_path(raw)]
    if not isinstance(raw, list):
        return []
    return [normalize_graph_path(str(item)) for item in raw if str(item).strip()]


def result_matches(result: dict[str, object], target: str) -> bool:
    path = normalize_graph_path(str(result.get("path", "")))
    citation = normalize_graph_path(str(result.get("citation", "")))
    target_path = target.split("#", 1)[0]
    if path == target_path:
        return True
    if citation == target:
        return True
    return bool(target_path and citation.startswith(f"{target_path}#"))


def evaluate(root: Path, eval_file: Path, agent: str, k: int, max_shards: int) -> dict[str, object]:
    cases = load_cases(eval_file)
    per_query: list[dict[str, object]] = []
    precision_total = 0.0
    recall_total = 0.0
    hit_total = 0.0
    mrr_total = 0.0
    for case in cases:
        query = str(case.get("query", "")).strip()
        targets = relevant_targets(case)
        if not query or not targets:
            continue
        results = search_memory(root, query, agent=agent, limit=k, max_shards=max_shards)
        hit_ranks: list[int] = []
        matched_targets: set[str] = set()
        for rank, result in enumerate(results, start=1):
            for target in targets:
                if result_matches(result, target):
                    hit_ranks.append(rank)
                    matched_targets.add(target)
                    break
        hits = len(hit_ranks)
        precision = hits / max(1, k)
        recall = len(matched_targets) / max(1, len(targets))
        mrr = 1.0 / min(hit_ranks) if hit_ranks else 0.0
        precision_total += precision
        recall_total += recall
        hit_total += 1.0 if hits else 0.0
        mrr_total += mrr
        per_query.append({
            "query": query,
            "relevant": targets,
            "hits": hits,
            "precision_at_k": round(precision, 6),
            "recall_at_k": round(recall, 6),
            "mrr": round(mrr, 6),
            "top_results": [
                {
                    "path": result.get("path"),
                    "citation": result.get("citation"),
                    "score": result.get("score"),
                }
                for result in results
            ],
        })
    count = len(per_query)
    return {
        "query_count": count,
        "k": k,
        "precision_at_k": round(precision_total / count, 6) if count else 0.0,
        "recall_at_k": round(recall_total / count, 6) if count else 0.0,
        "hit_rate_at_k": round(hit_total / count, 6) if count else 0.0,
        "mrr": round(mrr_total / count, 6) if count else 0.0,
        "cases": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Fable Harness RAG retrieval.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--eval-file", required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    metrics = evaluate(Path(args.root), Path(args.eval_file), args.agent, args.k, args.max_shards)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"queries={metrics['query_count']} "
            f"precision@{metrics['k']}={metrics['precision_at_k']:.4f} "
            f"recall@{metrics['k']}={metrics['recall_at_k']:.4f} "
            f"mrr={metrics['mrr']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

RAG_PIPELINE_SCRIPT = r'''#!/usr/bin/env python3
"""Create a retrieve -> inspect sources -> answer/plan evidence pack."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from memory_core import find_local_dir, relpath, search_memory, slugify


def source_excerpt(root: Path, result: dict[str, object], max_lines: int = 16) -> str:
    path_value = str(result.get("path", ""))
    if not path_value:
        return ""
    path = (root / path_value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return ""
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = int(result.get("start_line", 1) or 1)
    end = int(result.get("end_line", start) or start)
    start = max(1, min(start, len(lines) or 1))
    end = max(start, min(end, len(lines)))
    if end - start + 1 > max_lines:
        end = start + max_lines - 1
    excerpt = []
    for number in range(start, end + 1):
        excerpt.append(f"{number}: {lines[number - 1]}")
    return "\n".join(excerpt)


def write_report(root: Path, agent: str, query: str, results: list[dict[str, object]]) -> Path:
    local_dir = find_local_dir(root, agent)
    reports_dir = local_dir / "memory" / "retrieval"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = reports_dir / f"{stamp}-{slugify(query)[:60]}.md"
    lines = [
        f"# Retrieval Pipeline: {query}",
        "",
        "## Retrieve",
        "",
    ]
    if not results:
        lines.append("- No local memory results matched the query.")
    for index, result in enumerate(results, start=1):
        lines.append(
            f"{index}. `{result.get('citation', result.get('path'))}` "
            f"score={result.get('score')} kind={result.get('kind')} type={result.get('type')}"
        )
        lines.append(f"   - heading: {result.get('heading', '')}")
        lines.append(f"   - snippet: {result.get('snippet', '')}")
        lines.append(f"   - score_breakdown: `{json.dumps(result.get('score_breakdown', {}), sort_keys=True)}`")
    lines.extend(["", "## Inspect Sources", ""])
    for index, result in enumerate(results, start=1):
        citation = result.get("citation", result.get("path"))
        lines.append(f"### Source {index}: `{citation}`")
        excerpt = source_excerpt(root, result)
        if excerpt:
            lines.extend(["", "```text", excerpt, "```", ""])
        else:
            lines.append("")
            lines.append("- Source excerpt unavailable; open the source path before relying on this result.")
            lines.append("")
    lines.extend([
        "## Answer Or Plan With Citations",
        "",
        "- Use the cited source lines above before answering or planning.",
        "- If the cited sources are weak, stale, missing, or contradictory, inspect project files, web sources, or ask the user before planning.",
    ])
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an explicit Fable Harness RAG pipeline.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results = search_memory(root, args.query, agent=args.agent, limit=args.limit, max_shards=args.max_shards)
    report = write_report(root, args.agent, args.query, results)
    payload = {
        "report_path": relpath(report, root),
        "result_count": len(results),
        "citations": [result.get("citation") for result in results],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(payload["report_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

SOURCE_ARBITRATE_SCRIPT = r'''#!/usr/bin/env python3
"""Compare retrieved harness memory with real project sources before edits."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from memory_core import find_local_dir, relpath, search_memory, slugify, top_terms


NEGATIVE_PATTERNS = [
    r"\bmust\s+not\b",
    r"\bshould\s+not\b",
    r"\bdo\s+not\b",
    r"\bdoes\s+not\b",
    r"\bnever\b",
    r"\bforbid(?:den|s)?\b",
    r"\bdisabled?\b",
    r"\bfalse\b",
    r"\bavoid\b",
    r"\bwithout\b",
]

POSITIVE_PATTERNS = [
    r"\bmust\s+use\b",
    r"\bshould\s+use\b",
    r"\buses?\b",
    r"\benabled?\b",
    r"\btrue\b",
    r"\brequir(?:e|es|ed)\b",
]


def polarity(text: str) -> str:
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in NEGATIVE_PATTERNS):
        return "negative"
    if any(re.search(pattern, lowered) for pattern in POSITIVE_PATTERNS):
        return "positive"
    return "neutral"


def resolve_source(root: Path, value: str) -> Path | None:
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root / raw
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved if resolved.is_file() else None


def source_paths(root: Path, sources: list[str], globs: list[str]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for value in sources:
        resolved = resolve_source(root, value)
        if resolved and resolved not in seen:
            paths.append(resolved)
            seen.add(resolved)
    for pattern in globs:
        for candidate in sorted(root.glob(pattern)):
            if not candidate.is_file() or ".git" in candidate.parts:
                continue
            resolved = candidate.resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                continue
            if resolved not in seen:
                paths.append(resolved)
                seen.add(resolved)
    return paths


def matching_lines(path: Path, query_terms: set[str], max_lines: int = 8) -> list[dict[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []
    matches: list[dict[str, object]] = []
    fallback: list[dict[str, object]] = []
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        entry = {"line": line_no, "text": stripped, "polarity": polarity(stripped)}
        if len(fallback) < max_lines:
            fallback.append(entry)
        haystack = stripped.lower()
        if not query_terms or any(term in haystack for term in query_terms):
            matches.append(entry)
            if len(matches) >= max_lines:
                break
    return matches or fallback[:max_lines]


def project_claims(root: Path, paths: list[Path], query_terms: set[str]) -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    for path in paths:
        for item in matching_lines(path, query_terms):
            citation = f"{relpath(path, root)}#L{item['line']}"
            claims.append({
                "path": relpath(path, root),
                "line": item["line"],
                "text": item["text"],
                "polarity": item["polarity"],
                "citation": citation,
            })
    return claims


def rag_claims(results: list[dict[str, object]]) -> list[dict[str, object]]:
    claims: list[dict[str, object]] = []
    for result in results:
        snippet = str(result.get("snippet") or result.get("summary") or "")
        if not snippet.strip():
            continue
        claims.append({
            "path": result.get("path", ""),
            "heading": result.get("heading", ""),
            "text": snippet,
            "polarity": polarity(snippet),
            "citation": result.get("citation", result.get("path", "")),
            "score": result.get("score"),
        })
    return claims


def conflict_pairs(rag_items: list[dict[str, object]], source_items: list[dict[str, object]]) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    opposites = {("positive", "negative"), ("negative", "positive")}
    for rag in rag_items:
        for source in source_items:
            if (str(rag.get("polarity")), str(source.get("polarity"))) not in opposites:
                continue
            conflicts.append({
                "rag": rag,
                "project": source,
                "reason": "opposite polarity over retrieved project-relevant evidence",
            })
    return conflicts


def write_report(
    root: Path,
    agent: str,
    query: str,
    results: list[dict[str, object]],
    rag_items: list[dict[str, object]],
    source_items: list[dict[str, object]],
    conflicts: list[dict[str, object]],
    decision: str,
) -> Path:
    local_dir = find_local_dir(root, agent)
    reports_dir = local_dir / "memory" / "retrieval"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = reports_dir / f"{stamp}-source-arbitration-{slugify(query)[:52]}.md"

    lines = [
        f"# Source Arbitration: {query}",
        "",
        "## Light Gate",
        "",
        f"- Decision: `{decision}`",
        f"- RAG results inspected: {len(results)}",
        f"- Project source claims inspected: {len(source_items)}",
        f"- Material conflicts: {len(conflicts)}",
        "",
    ]
    if not conflicts:
        lines.extend([
            "No material conflict detected by the lightweight gate.",
            "",
            "Keep inspecting real project files before editing.",
            "",
        ])
    lines.extend(["## RAG Evidence", ""])
    if not rag_items:
        lines.append("- No retrieved RAG evidence was available.")
    for item in rag_items:
        lines.append(f"- RAG says `{item['citation']}` polarity={item['polarity']} score={item.get('score')}: {item['text']}")
    lines.extend(["", "## Project Source Evidence", ""])
    if not source_items:
        lines.append("- No project source evidence was provided. Inspect real project files before planning or editing.")
    for item in source_items:
        lines.append(f"- Project source says `{item['citation']}` polarity={item['polarity']}: {item['text']}")
    lines.extend(["", "## Evidence Dispute", ""])
    if not conflicts:
        lines.append("- No full Evidence Dispute is required by the lightweight gate.")
    for index, conflict in enumerate(conflicts, start=1):
        rag = conflict["rag"]
        project = conflict["project"]
        lines.extend([
            f"### Conflict {index}",
            "",
            f"- RAG says `{rag['citation']}`: {rag['text']}",
            f"- Project source says `{project['citation']}`: {project['text']}",
            f"- Difference: {conflict['reason']}",
            "- User gate: Ask the user before replacing project facts with RAG-derived facts.",
            "",
        ])
    lines.extend([
        "## Recommendation Matrix",
        "",
        "| Option | What changes | Pros | Cons |",
        "|---|---|---|---|",
        "| Keep project source | Treat current code/docs as operational truth and update memory if stale | Safest for current behavior | May preserve an outdated or inconsistent project fact |",
        "| Update project source from RAG | Change code/docs to match retrieved canonical memory | Aligns project with prior decisions | Requires user approval and verification because RAG may be stale |",
        "| Update memory from project source | Mark RAG memory stale/superseded and promote current source truth | Keeps retrieval honest | Can erase a useful architectural correction if source is wrong |",
        "| Gather more evidence | Add tests, inspect more files, or ask the user | Best for low-confidence conflicts | Slower |",
        "",
        "## Next Step",
        "",
        "- If `decision` is `full-dispute-required`, present the dispute, recommendation, pros, and cons to the user before mutating code/docs.",
        "- If `decision` is `light-gate-only`, continue with normal planning, but keep cited project files as the stronger operational evidence.",
    ])
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Fable Harness source arbitration.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--query", required=True)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--source-glob", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-shards", type=int, default=32)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    query_terms = set(top_terms(args.query, limit=24))
    results = search_memory(root, args.query, agent=args.agent, limit=args.limit, max_shards=args.max_shards)
    paths = source_paths(root, args.source, args.source_glob)
    rag_items = rag_claims(results)
    source_items = project_claims(root, paths, query_terms)
    conflicts = conflict_pairs(rag_items, source_items)
    if conflicts:
        decision = "full-dispute-required"
    elif not source_items:
        decision = "source-inspection-required"
    else:
        decision = "light-gate-only"
    report = write_report(root, args.agent, args.query, results, rag_items, source_items, conflicts, decision)
    payload = {
        "decision": decision,
        "report_path": relpath(report, root),
        "rag_result_count": len(results),
        "project_source_count": len(paths),
        "project_claim_count": len(source_items),
        "material_conflict_count": len(conflicts),
        "conflicts": conflicts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(payload["report_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

GRAPH_QUERY_SCRIPT = r'''#!/usr/bin/env python3
"""Query the generated Fable Harness knowledge graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import query_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Fable Harness graph nodes and edges.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--kind")
    parser.add_argument("--path")
    parser.add_argument("--node")
    parser.add_argument("--relation")
    parser.add_argument("--q")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = query_graph(
        Path(args.root),
        agent=args.agent,
        kind=args.kind,
        path=args.path,
        node=args.node,
        relation=args.relation,
        q=args.q,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        for node in result["nodes"]:
            print(f"node {node['id']} {node.get('kind', '')} {node.get('path', node.get('title', ''))}")
        for edge in result["edges"]:
            print(f"edge {edge['id']} {edge.get('type', '')} {edge.get('from', '')} -> {edge.get('to', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

GRAPH_CHECK_SCRIPT = r'''#!/usr/bin/env python3
"""Validate the generated Fable Harness knowledge graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_core import check_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fable Harness graph integrity.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_graph(Path(args.root), agent=args.agent, strict=args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Fable Harness graph check {result['status']}.")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

CODE_GRAPH_CORE_SCRIPT = r'''#!/usr/bin/env python3
"""Generated local code graph support for Fable Harness."""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path


SCHEMA = "fable-harness-code-graph-v1"
EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "temp_files",
    ".worktrees",
    "worktrees",
}


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def find_local_dir(root: Path, agent: str = "auto") -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(kind: str, *parts: object) -> str:
    value = ":".join(str(part) for part in parts)
    digest = hashlib.sha256(f"{kind}:{value}".encode("utf-8")).hexdigest()[:20]
    return f"code-{kind}:{digest}"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def graph_dir(root: Path, agent: str = "auto") -> Path:
    return find_local_dir(root, agent) / "memory" / "code-graph"


def normalize_path(value: str) -> str:
    return value.strip().strip("`").replace("\\", "/")


def module_name_for_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if "src" in parts:
        parts = parts[parts.index("src") + 1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) or path.stem


def resolve_import_module(module_name: str, rel: str, level: int, module: str | None) -> str:
    if level <= 0:
        return module or ""
    module_parts = module_name.split(".") if module_name else []
    if not rel.endswith("__init__.py"):
        module_parts = module_parts[:-1]
    up = max(level - 1, 0)
    if up:
        module_parts = module_parts[:-up]
    suffix = [part for part in (module or "").split(".") if part]
    return ".".join([*module_parts, *suffix])


def should_skip_source_path(path: Path, root: Path, local_dir: Path) -> bool:
    try:
        resolved = path.resolve()
        if is_relative_to(resolved, local_dir.resolve()):
            return True
        rel_parts = path.relative_to(root.resolve()).parts
    except ValueError:
        return True
    if any(part in EXCLUDED_DIR_NAMES for part in rel_parts):
        return True
    return "memory" in rel_parts and "code-graph" in rel_parts


def iter_source_files(root: Path, local_dir: Path, extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    root = root.resolve()
    local_dir = local_dir.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        if should_skip_source_path(path, root, local_dir):
            continue
        files.append(path)
    return sorted(files, key=lambda item: relpath(item, root))


def iter_python_files(root: Path, local_dir: Path) -> list[Path]:
    return iter_source_files(root, local_dir, {".py"})


def span(node: ast.AST, fallback_end: int = 1) -> dict[str, int]:
    return {
        "line_start": int(getattr(node, "lineno", 1) or 1),
        "line_end": int(getattr(node, "end_lineno", getattr(node, "lineno", fallback_end)) or fallback_end),
        "col_start": int(getattr(node, "col_offset", 0) or 0),
        "col_end": int(getattr(node, "end_col_offset", getattr(node, "col_offset", 0)) or 0),
    }


def call_name(expr: ast.AST) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        base = call_name(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    if isinstance(expr, ast.Call):
        return call_name(expr.func)
    return None


class GraphBuilder:
    def __init__(self, root: Path, agent: str = "auto") -> None:
        self.root = root.resolve()
        self.agent = agent
        self.local_dir = find_local_dir(self.root, agent)
        self.nodes: dict[str, dict[str, object]] = {}
        self.edges: dict[str, dict[str, object]] = {}
        self.symbol_by_full: dict[str, str] = {}
        self.symbols_by_name: dict[str, list[str]] = {}
        self.records: list[dict[str, object]] = []

    def add_node(self, node: dict[str, object]) -> str:
        node_id = str(node["id"])
        self.nodes[node_id] = node
        return node_id

    def add_edge(self, relation: str, source: str, target: str, **attributes: object) -> str:
        edge_id = stable_id("edge", relation, source, target, json.dumps(attributes, sort_keys=True))
        edge = {
            "id": edge_id,
            "relation": relation,
            "from": source,
            "to": target,
        }
        if attributes:
            edge["attributes"] = attributes
        self.edges[edge_id] = edge
        return edge_id

    def add_symbol(self, rel: str, language: str, name: str, full_name: str, symbol_kind: str, node: ast.AST, file_id: str, parent_id: str) -> str:
        node_id = stable_id("symbol", language, rel, full_name)
        item: dict[str, object] = {
            "id": node_id,
            "kind": "symbol",
            "language": language,
            "path": rel,
            "name": name,
            "full_name": full_name,
            "symbol_kind": symbol_kind,
            **span(node),
            "attributes": {},
        }
        self.add_node(item)
        self.symbol_by_full[full_name] = node_id
        self.symbols_by_name.setdefault(name, []).append(node_id)
        self.add_edge("contains", parent_id, node_id)
        self.add_edge("defines", file_id, node_id)
        return node_id

    def collect_imports(self, tree: ast.AST, rel: str, file_id: str, module_name: str) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    aliases[local] = alias.name
                    import_id = stable_id("import", rel, getattr(node, "lineno", 1), local, alias.name)
                    self.add_node({
                        "id": import_id,
                        "kind": "import",
                        "language": "python",
                        "path": rel,
                        "name": local,
                        "module": alias.name,
                        **span(node),
                    })
                    self.add_edge("imports", file_id, import_id, imported=alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = resolve_import_module(module_name, rel, int(node.level or 0), node.module)
                for alias in node.names:
                    local = alias.asname or alias.name
                    imported = f"{module}.{alias.name}" if module else alias.name
                    aliases[local] = imported
                    import_id = stable_id("import", rel, getattr(node, "lineno", 1), local, imported)
                    self.add_node({
                        "id": import_id,
                        "kind": "import",
                        "language": "python",
                        "path": rel,
                        "name": local,
                        "module": module,
                        "imported": imported,
                        **span(node),
                    })
                    self.add_edge("imports", file_id, import_id, imported=imported)
        return aliases

    def collect_definitions(self, tree: ast.Module, rel: str, module_name: str, file_id: str) -> dict[ast.AST, str]:
        defs_by_node: dict[ast.AST, str] = {}
        module_id = stable_id("symbol", "python", rel, module_name)
        module_node = {
            "id": module_id,
            "kind": "symbol",
            "language": "python",
            "path": rel,
            "name": module_name.split(".")[-1],
            "full_name": module_name,
            "symbol_kind": "module",
            "line_start": 1,
            "line_end": max(1, len(getattr(tree, "body", []))),
            "col_start": 0,
            "col_end": 0,
            "attributes": {},
        }
        self.add_node(module_node)
        self.symbol_by_full[module_name] = module_id
        self.symbols_by_name.setdefault(module_node["name"], []).append(module_id)  # type: ignore[index]
        self.add_edge("contains", file_id, module_id)
        self.add_edge("defines", file_id, module_id)
        defs_by_node[tree] = module_id

        def visit_body(body: list[ast.stmt], parent_id: str, prefix: list[str], in_class: bool = False) -> None:
            for child in body:
                if isinstance(child, ast.ClassDef):
                    full = ".".join([module_name, *prefix, child.name])
                    class_id = self.add_symbol(rel, "python", child.name, full, "class", child, file_id, parent_id)
                    defs_by_node[child] = class_id
                    visit_body(child.body, class_id, [*prefix, child.name], True)
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    full = ".".join([module_name, *prefix, child.name])
                    if child.name.startswith("test_") or rel.startswith("tests/") or Path(rel).name.startswith("test_"):
                        symbol_kind = "test"
                    elif isinstance(child, ast.AsyncFunctionDef):
                        symbol_kind = "async_function"
                    elif in_class:
                        symbol_kind = "method"
                    else:
                        symbol_kind = "function"
                    function_id = self.add_symbol(rel, "python", child.name, full, symbol_kind, child, file_id, parent_id)
                    defs_by_node[child] = function_id
                    visit_body([stmt for stmt in child.body if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))], function_id, [*prefix, child.name], False)

        visit_body(tree.body, module_id, [])
        return defs_by_node

    def parse_file(self, path: Path) -> None:
        rel = relpath(path, self.root)
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=rel)
        module_name = module_name_for_path(path, self.root)
        file_id = stable_id("file", rel)
        self.add_node({
            "id": file_id,
            "kind": "file",
            "language": "python",
            "path": rel,
            "name": Path(rel).name,
            "sha256": sha256_text(text),
            "size": len(text.encode("utf-8")),
        })
        aliases = self.collect_imports(tree, rel, file_id, module_name)
        defs_by_node = self.collect_definitions(tree, rel, module_name, file_id)
        self.records.append({
            "path": path,
            "rel": rel,
            "tree": tree,
            "file_id": file_id,
            "module_name": module_name,
            "module_id": defs_by_node[tree],
            "aliases": aliases,
            "defs_by_node": defs_by_node,
        })

    def resolve_symbol(self, name: str, aliases: dict[str, str], rel: str) -> tuple[str | None, str]:
        parts = name.split(".")
        resolved_name = name
        if parts and parts[0] in aliases:
            resolved_name = ".".join([aliases[parts[0]], *parts[1:]])
        if resolved_name in self.symbol_by_full:
            return self.symbol_by_full[resolved_name], resolved_name
        if "." in resolved_name:
            suffix = f".{resolved_name}"
            matches = [
                node_id
                for full, node_id in self.symbol_by_full.items()
                if full.endswith(suffix) and self.nodes.get(node_id, {}).get("path") == rel
            ]
            if len(matches) == 1:
                return matches[0], resolved_name
        matches = self.symbols_by_name.get(resolved_name, [])
        matches = [node_id for node_id in matches if self.nodes.get(node_id, {}).get("path") == rel]
        if len(matches) == 1:
            return matches[0], resolved_name
        return None, resolved_name

    def add_reference(self, rel: str, name: str, node: ast.AST) -> str:
        ref_id = stable_id("reference", rel, getattr(node, "lineno", 1), name)
        self.add_node({
            "id": ref_id,
            "kind": "reference",
            "language": "python",
            "path": rel,
            "name": name,
            **span(node),
            "attributes": {"resolved": False},
        })
        return ref_id

    def collect_calls(self, record: dict[str, object]) -> None:
        rel = str(record["rel"])
        tree = record["tree"]
        aliases = record["aliases"]
        defs_by_node = record["defs_by_node"]
        assert isinstance(tree, ast.AST)
        assert isinstance(aliases, dict)
        assert isinstance(defs_by_node, dict)

        def visit(node: ast.AST, current_symbol: str) -> None:
            if node in defs_by_node:
                current_symbol = str(defs_by_node[node])
            if isinstance(node, ast.Call):
                name = call_name(node.func)
                if name:
                    target_id, resolved_name = self.resolve_symbol(name, aliases, rel)  # type: ignore[arg-type]
                    if not target_id:
                        target_id = self.add_reference(rel, resolved_name, node)
                    self.add_edge("calls", current_symbol, target_id, name=name, resolved_name=resolved_name, **span(node))
                    source_node = self.nodes.get(current_symbol, {})
                    target_node = self.nodes.get(target_id, {})
                    if source_node.get("symbol_kind") == "test" and target_node.get("kind") == "symbol":
                        self.add_edge("tests", current_symbol, target_id, heuristic=True, **span(node))
            for child in ast.iter_child_nodes(node):
                visit(child, current_symbol)

        visit(tree, str(record["module_id"]))

    def build(self) -> dict[str, object]:
        for path in iter_python_files(self.root, self.local_dir):
            try:
                self.parse_file(path)
            except (SyntaxError, UnicodeDecodeError) as exc:
                rel = relpath(path, self.root)
                node_id = stable_id("diagnostic", rel, type(exc).__name__, str(exc))
                self.add_node({
                    "id": node_id,
                    "kind": "diagnostic",
                    "language": "python",
                    "path": rel,
                    "name": type(exc).__name__,
                    "message": str(exc),
                })
        for record in self.records:
            self.collect_calls(record)
        return write_code_graph(self.root, self.agent, list(self.nodes.values()), list(self.edges.values()))


def build_indexes(nodes: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, dict[str, list[str]]]:
    by_kind: dict[str, list[str]] = {}
    by_path: dict[str, list[str]] = {}
    by_symbol: dict[str, list[str]] = {}
    by_relation: dict[str, list[str]] = {}
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            continue
        for key in [node.get("kind"), node.get("symbol_kind")]:
            if key:
                by_kind.setdefault(str(key), []).append(node_id)
        if node.get("path"):
            by_path.setdefault(str(node["path"]), []).append(node_id)
        for key in [node.get("name"), node.get("full_name")]:
            if key:
                by_symbol.setdefault(str(key), []).append(node_id)
        full_name = str(node.get("full_name", ""))
        if full_name:
            for suffix in full_name.split("."):
                by_symbol.setdefault(suffix, []).append(node_id)
    for edge in edges:
        edge_id = str(edge.get("id", ""))
        relation = str(edge.get("relation", ""))
        if edge_id and relation:
            by_relation.setdefault(relation, []).append(edge_id)
    return {
        "by-kind": {key: sorted(set(value)) for key, value in sorted(by_kind.items())},
        "by-path": {key: sorted(set(value)) for key, value in sorted(by_path.items())},
        "by-symbol": {key: sorted(set(value)) for key, value in sorted(by_symbol.items())},
        "by-relation": {key: sorted(set(value)) for key, value in sorted(by_relation.items())},
    }


def clear_generated_graph_dir(root: Path, local_dir: Path, target: Path) -> None:
    resolved_root = root.resolve()
    if local_dir.exists() and not is_relative_to(local_dir.resolve(), resolved_root):
        raise ValueError(f"refusing to clear code graph through local dir outside workspace: {local_dir}")
    memory_dir = local_dir / "memory"
    if memory_dir.exists() and not is_relative_to(memory_dir.resolve(), resolved_root):
        raise ValueError(f"refusing to clear code graph through memory directory outside workspace: {memory_dir}")
    if memory_dir.exists() and memory_dir.is_symlink():
        raise ValueError(f"refusing to clear code graph through symlinked memory directory: {memory_dir}")
    if target.exists():
        if target.is_symlink():
            raise ValueError(f"refusing to clear symlinked code graph directory: {target}")
        resolved_memory = memory_dir.resolve()
        resolved_target = target.resolve()
        if not is_relative_to(resolved_target, resolved_root):
            raise ValueError(f"refusing to clear code graph outside workspace: {target}")
        if not is_relative_to(resolved_target, resolved_memory):
            raise ValueError(f"refusing to clear code graph outside generated memory directory: {target}")
        shutil.rmtree(target)


def write_code_graph(root: Path, agent: str, nodes: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
    local_dir = find_local_dir(root, agent)
    target = local_dir / "memory" / "code-graph"
    clear_generated_graph_dir(root, local_dir, target)
    (target / "indexes").mkdir(parents=True, exist_ok=True)
    nodes = sorted(nodes, key=lambda item: str(item.get("id", "")))
    edges = sorted(edges, key=lambda item: str(item.get("id", "")))
    write_jsonl(target / "nodes.jsonl", nodes)
    write_jsonl(target / "edges.jsonl", edges)
    indexes = build_indexes(nodes, edges)
    for name, data in indexes.items():
        write_json(target / "indexes" / f"{name}.json", data)
    manifest = {
        "schema": SCHEMA,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_kinds": sorted({str(node.get("kind", "")) for node in nodes if node.get("kind")}),
        "symbol_kinds": sorted({str(node.get("symbol_kind", "")) for node in nodes if node.get("symbol_kind")}),
        "relations": sorted({str(edge.get("relation", "")) for edge in edges if edge.get("relation")}),
        "indexes": [
            "indexes/by-kind.json",
            "indexes/by-path.json",
            "indexes/by-symbol.json",
            "indexes/by-relation.json",
        ],
        "files": [
            {"path": str(node["path"]), "sha256": str(node["sha256"])}
            for node in nodes
            if node.get("kind") == "file" and node.get("sha256") and node.get("path")
        ],
    }
    write_json(target / "manifest.json", manifest)
    return manifest


def build_code_graph(root: Path, agent: str = "auto") -> dict[str, object]:
    builder = GraphBuilder(root, agent)
    return builder.build()


def load_code_graph(root: Path, agent: str = "auto") -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    target = graph_dir(root, agent)
    manifest = read_json(target / "manifest.json", {})
    if not isinstance(manifest, dict):
        manifest = {}
    return manifest, read_jsonl(target / "nodes.jsonl"), read_jsonl(target / "edges.jsonl")


def match_symbol(node: dict[str, object], value: str) -> bool:
    value = value.strip()
    name = str(node.get("name", ""))
    full = str(node.get("full_name", ""))
    return value in {name, full} or full.endswith(f".{value}") or name.endswith(value)


def query_code_graph(
    root: Path,
    agent: str = "auto",
    path: str | None = None,
    symbol: str | None = None,
    kind: str | None = None,
    relation: str | None = None,
    from_value: str | None = None,
    to_value: str | None = None,
    impact: str | None = None,
) -> dict[str, object]:
    manifest, nodes, edges = load_code_graph(root, agent)
    node_by_id = {str(node.get("id")): node for node in nodes}
    selected_nodes: dict[str, dict[str, object]] = {}
    selected_edges: dict[str, dict[str, object]] = {}

    def add_node_id(node_id: str) -> None:
        if node_id in node_by_id:
            selected_nodes[node_id] = node_by_id[node_id]

    def node_matches_ref(node: dict[str, object], value: str) -> bool:
        return str(node.get("id")) == value or str(node.get("path", "")) == normalize_path(value) or match_symbol(node, value)

    if path:
        wanted = normalize_path(path)
        for node in nodes:
            if str(node.get("path", "")) == wanted:
                add_node_id(str(node.get("id")))
    if symbol:
        for node in nodes:
            if match_symbol(node, symbol):
                add_node_id(str(node.get("id")))
    if kind:
        for node in nodes:
            if node.get("kind") == kind or node.get("symbol_kind") == kind:
                add_node_id(str(node.get("id")))
    if relation:
        for edge in edges:
            if edge.get("relation") == relation:
                selected_edges[str(edge.get("id"))] = edge
                add_node_id(str(edge.get("from")))
                add_node_id(str(edge.get("to")))
    if from_value or to_value:
        from_ids = {
            str(node.get("id"))
            for node in nodes
            if from_value and node_matches_ref(node, from_value)
        } if from_value else set()
        to_ids = {
            str(node.get("id"))
            for node in nodes
            if to_value and node_matches_ref(node, to_value)
        } if to_value else set()
        if (from_value and not from_ids) or (to_value and not to_ids):
            return {"schema": manifest.get("schema", SCHEMA), "nodes": [], "edges": []}
        for edge in edges:
            if from_ids and edge.get("from") not in from_ids:
                continue
            if to_ids and edge.get("to") not in to_ids:
                continue
            selected_edges[str(edge.get("id"))] = edge
            add_node_id(str(edge.get("from")))
            add_node_id(str(edge.get("to")))
    if impact:
        seeds = {
            str(node.get("id"))
            for node in nodes
            if node_matches_ref(node, impact)
        }
        frontier = set(seeds)
        seen = set(seeds)
        impact_relations = {"calls", "imports", "tests"}
        while frontier:
            current = frontier
            frontier = set()
            for edge in edges:
                if edge.get("relation") not in impact_relations:
                    continue
                source = str(edge.get("from"))
                target = str(edge.get("to"))
                if target in current:
                    selected_edges[str(edge.get("id"))] = edge
                    for node_id in [source, target]:
                        add_node_id(node_id)
                        if node_id not in seen:
                            seen.add(node_id)
                            frontier.add(node_id)
    if not any([path, symbol, kind, relation, from_value, to_value, impact]):
        selected_nodes = {str(node.get("id")): node for node in nodes}
        selected_edges = {str(edge.get("id")): edge for edge in edges}

    result = {
        "schema": manifest.get("schema", SCHEMA),
        "nodes": sorted(selected_nodes.values(), key=lambda item: str(item.get("id", ""))),
        "edges": sorted(selected_edges.values(), key=lambda item: str(item.get("id", ""))),
    }
    if impact:
        result["query_mode"] = "static-impact"
        result["impact_query"] = impact
    return result


def check_code_graph(root: Path, agent: str = "auto", strict: bool = False) -> dict[str, object]:
    manifest, nodes, edges = load_code_graph(root, agent)
    target = graph_dir(root, agent)
    errors: list[str] = []
    if manifest.get("schema") != SCHEMA:
        errors.append("manifest schema is missing or invalid")
    node_ids: set[str] = set()
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            errors.append("node missing id")
            continue
        if node_id in node_ids:
            errors.append(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
    edge_ids: set[str] = set()
    for edge in edges:
        edge_id = str(edge.get("id", ""))
        if not edge_id:
            errors.append("edge missing id")
            continue
        if edge_id in edge_ids:
            errors.append(f"duplicate edge id: {edge_id}")
        edge_ids.add(edge_id)
        source = str(edge.get("from", ""))
        target_id = str(edge.get("to", ""))
        if source not in node_ids or target_id not in node_ids:
            errors.append(f"dangling edge {edge_id}: {source} -> {target_id}")
    if manifest.get("node_count") != len(nodes):
        errors.append("manifest node_count does not match nodes.jsonl")
    if manifest.get("edge_count") != len(edges):
        errors.append("manifest edge_count does not match edges.jsonl")
    indexes = build_indexes(nodes, edges)
    for name, expected in indexes.items():
        path = target / "indexes" / f"{name}.json"
        actual = read_json(path, None)
        if actual != expected:
            errors.append(f"index mismatch: indexes/{name}.json")
    if strict:
        for item in manifest.get("files", []):
            if not isinstance(item, dict):
                continue
            path_value = item.get("path")
            expected_hash = item.get("sha256")
            if not isinstance(path_value, str) or not isinstance(expected_hash, str):
                continue
            file_path = root / path_value
            if not file_path.is_file():
                errors.append(f"source file missing: {path_value}")
                continue
            current_hash = sha256_text(file_path.read_text(encoding="utf-8"))
            if current_hash != expected_hash:
                errors.append(f"source hash changed: {path_value}")
    return {
        "status": "ok" if not errors else "failed",
        "schema": manifest.get("schema", SCHEMA),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "errors": errors,
    }
'''

CODE_GRAPH_BUILD_SCRIPT = r'''#!/usr/bin/env python3
"""Build the generated Fable Harness code graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from code_graph_core import build_code_graph, graph_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Fable Harness code graph.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = build_code_graph(Path(args.root), args.agent)
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    else:
        print(graph_dir(Path(args.root).resolve(), args.agent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

CODE_GRAPH_QUERY_SCRIPT = r'''#!/usr/bin/env python3
"""Query the generated Fable Harness code graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from code_graph_core import query_code_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Fable Harness code graph.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--path")
    parser.add_argument("--symbol")
    parser.add_argument("--kind")
    parser.add_argument("--relation")
    parser.add_argument("--from", dest="from_value")
    parser.add_argument("--to", dest="to_value")
    parser.add_argument("--impact")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = query_code_graph(
        Path(args.root),
        agent=args.agent,
        path=args.path,
        symbol=args.symbol,
        kind=args.kind,
        relation=args.relation,
        from_value=args.from_value,
        to_value=args.to_value,
        impact=args.impact,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        for node in result["nodes"]:
            print(f"node {node['id']} {node.get('kind', '')} {node.get('full_name', node.get('path', ''))}")
        for edge in result["edges"]:
            print(f"edge {edge['id']} {edge.get('relation', '')} {edge.get('from', '')} -> {edge.get('to', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

CODE_GRAPH_CHECK_SCRIPT = r'''#!/usr/bin/env python3
"""Validate the generated Fable Harness code graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from code_graph_core import check_code_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fable Harness code graph integrity.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_code_graph(Path(args.root), agent=args.agent, strict=args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Fable Harness code graph check {result['status']}.")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

RELEASE_NOTICE_SCRIPT = r'''#!/usr/bin/env python3
"""Warn when a newer Fable Harness GitHub release is available."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.request
from pathlib import Path


CURRENT_VERSION = "__FABLE_HARNESS_VERSION__"
LATEST_RELEASE_API = "https://api.github.com/repos/AAO-SH/fable-harness/releases/latest"
LATEST_RELEASE_URL = "https://github.com/AAO-SH/fable-harness/releases/latest"


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def parse_time(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def now_utc(value: str | None) -> dt.datetime:
    parsed = parse_time(value or "")
    return parsed or dt.datetime.now(dt.timezone.utc)


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+){0,3}", str(value))
    if not match:
        return ()
    parts = [int(part) for part in match.group(0).split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer(latest: str, current: str) -> bool:
    latest_tuple = version_tuple(latest)
    current_tuple = version_tuple(current)
    return bool(latest_tuple and current_tuple and latest_tuple > current_tuple)


def state_path(local_dir: Path) -> Path:
    return local_dir / "harness" / "release-notice.json"


def read_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_latest_release(latest_json: str) -> dict[str, object]:
    if latest_json:
        candidate = Path(latest_json)
        text = candidate.read_text(encoding="utf-8-sig") if candidate.exists() else latest_json
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("latest release payload must be a JSON object")
        return data
    request = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "fable-harness-release-notice",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("latest release payload must be a JSON object")
    return data


def notice_text(result: dict[str, object]) -> str:
    return (
        "Fable Harness update available: "
        f"installed {result['current_version']}, latest {result['latest_version']}.\n"
        f"Manual update: {result['latest_url']}\n"
        "No automatic update was applied."
    )


def check(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    path = state_path(local_dir)
    state = read_state(path)
    current_version = args.current_version or CURRENT_VERSION
    now = now_utc(args.now)
    interval = dt.timedelta(hours=args.interval_hours)
    last_checked = parse_time(str(state.get("last_checked_at") or ""))
    if last_checked and not args.force and now - last_checked < interval:
        return {
            "checked": False,
            "reason": "throttled",
            "current_version": current_version,
            "latest_version": state.get("latest_version"),
            "latest_url": state.get("latest_url", LATEST_RELEASE_URL),
            "update_available": bool(state.get("update_available")),
            "state_path": str(path),
        }

    result: dict[str, object] = {
        "checked": True,
        "reason": "checked",
        "current_version": current_version,
        "latest_version": None,
        "latest_url": LATEST_RELEASE_URL,
        "update_available": False,
        "state_path": str(path),
    }
    try:
        latest = load_latest_release(args.latest_json)
        latest_version = str(latest.get("tag_name") or latest.get("name") or "").strip()
        latest_url = str(latest.get("html_url") or LATEST_RELEASE_URL).strip()
        result["latest_version"] = latest_version
        result["latest_url"] = latest_url or LATEST_RELEASE_URL
        result["update_available"] = is_newer(latest_version, current_version)
    except Exception as exc:
        result["reason"] = "check-error"
        result["error"] = str(exc)

    state = {
        "checked_at": now.isoformat(),
        "current_version": result["current_version"],
        "last_checked_at": now.isoformat(),
        "latest_version": result["latest_version"],
        "latest_url": result["latest_url"],
        "update_available": result["update_available"],
        "reason": result["reason"],
    }
    if "error" in result:
        state["error"] = result["error"]
    write_state(path, state)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for newer Fable Harness releases without updating.")
    parser.add_argument("command", nargs="?", choices=["check"], default="check")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--current-version", default=CURRENT_VERSION)
    parser.add_argument("--interval-hours", type=float, default=24.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--latest-json", default="")
    parser.add_argument("--now")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check(args)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif result.get("checked") and result.get("update_available"):
        print(notice_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


SUBAGENT_PLAN_SCRIPT = r'''#!/usr/bin/env python3
"""Create dispatchable subagent briefs for a Fable Harness task."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from memory_core import find_local_dir, relpath, slugify


def lines(items: list[str], prefix: str = "- ", empty: str = "None provided. Orchestrator must fill this before dispatch.") -> str:
    if not items:
        return f"{prefix}{empty}\n"
    return "\n".join(f"{prefix}{item}" for item in items) + "\n"


def parse_dependencies(values: list[str], slugs: list[str]) -> dict[str, list[str]]:
    known = set(slugs)
    dependencies: dict[str, list[str]] = {slug: [] for slug in slugs}
    for value in values:
        if ":" not in value:
            raise ValueError(f"dependency must use dependent:dependency format: {value}")
        dependent_raw, dependency_raw = value.split(":", 1)
        dependent = slugify(dependent_raw)
        dependency = slugify(dependency_raw)
        if dependent not in known:
            raise ValueError(f"dependency references unknown domain: {dependent_raw}")
        if dependency not in known:
            raise ValueError(f"dependency references unknown domain: {dependency_raw}")
        if dependency not in dependencies[dependent]:
            dependencies[dependent].append(dependency)
    return {slug: deps for slug, deps in dependencies.items() if deps}


def build_waves(slugs: list[str], dependencies: dict[str, list[str]], parallel: bool) -> list[dict[str, object]]:
    if not parallel:
        return [{"index": index + 1, "domains": [slug]} for index, slug in enumerate(slugs)]
    remaining = list(slugs)
    completed: set[str] = set()
    waves: list[dict[str, object]] = []
    while remaining:
        ready = [
            slug for slug in remaining
            if all(dependency in completed for dependency in dependencies.get(slug, []))
        ]
        if not ready:
            raise ValueError("cyclic or unsatisfied subagent dependencies")
        waves.append({"index": len(waves) + 1, "domains": ready})
        completed.update(ready)
        remaining = [slug for slug in remaining if slug not in set(ready)]
    return waves


def brief_text(
    task: str,
    domain: str,
    root: Path,
    trace: Path | None,
    files: list[str],
    protected_tests: list[str],
    verification: str,
) -> str:
    trace_line = relpath(trace.resolve(), root) if trace else "No active trace provided."
    return f"""# Subagent Brief: {domain}

## Objective

- Help the orchestrator with this task: {task}
- Assigned domain: {domain}

## Scope

- Read:
{lines(files, "  - ").rstrip()}
- Edit:
  - Only edit files explicitly assigned later by the orchestrator.
- Do not touch:
  - Protected tests unless the orchestrator explicitly says the test itself is wrong and replaces it with an equally strict test.
  - Semantic notes or memory indexes.

## Active Decisions

- The main orchestrator owns final decisions, memory promotion, and integration.
- This subagent returns evidence and recommendations, not durable memory changes.

## Protected Tests

{lines(protected_tests).rstrip()}

## Current Trace

- {trace_line}

## Operating Rules

- Stay inside the assigned domain.
- Prefer read/check/report unless the orchestrator explicitly permits edits.
- Do not promote semantic notes or memory directly.
- Return concise evidence for acceptance or rejection.

## Expected Evidence

- Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- Files read:
- Commands run:
- Findings:
- Risks:
- Suggested memory updates:

## Verification Command

```text
{verification}
```
"""


def dispatch_text(
    task: str,
    plan_dir: Path,
    domain_records: list[dict[str, object]],
    waves: list[dict[str, object]],
    root: Path,
    dispatch_mode: str,
    workflow_pattern: str,
    wave_purpose: str,
) -> str:
    rows = "\n".join(
        f"| {record['slug']} | `{record['brief']}` | pending | |"
        for record in domain_records
    )
    commands = "\n\n".join(
        "Use the available subagent spawn tool with this brief as the message "
        "(for example, `spawn_agent` when that tool is exposed):\n"
        f"`{record['brief']}`"
        for record in domain_records
    )
    by_slug = {str(record["slug"]): record for record in domain_records}
    wave_sections: list[str] = []
    for wave in waves:
        domains = [str(domain) for domain in wave.get("domains", []) if str(domain) in by_slug]
        wave_rows = "\n".join(
            f"| {slug} | `{by_slug[slug]['brief']}` | pending | |"
            for slug in domains
        )
        wave_sections.append(
            f"""## Wave {wave['index']}

Dispatch all domains in the same wave simultaneously when a platform subagent tool is available.

| Domain | Brief | Status | Accepted By Orchestrator |
|---|---|---|---|
{wave_rows}"""
        )
    wave_text = "\n\n".join(wave_sections)
    workflow_text = "None declared."
    if workflow_pattern:
        workflow_text = f"Pattern: `{workflow_pattern}`\nWave purpose: {wave_purpose or 'not specified'}"
    return f"""# Subagent Dispatch

## Task

{task}

## Workflow Role

{workflow_text}

## Invocation

Dispatch using the available subagent tool. In Codex, first verify which subagent spawn tool is exposed, then use it.
The installed Fable Harness instructions are standing project-level user authorization for this automatic dispatch when the independence check passes.
Do not ask the user for another trigger phrase or per-prompt permission before dispatching these briefs.
If no subagent tool is available, or a higher-priority runtime policy blocks dispatch, execute these briefs sequentially and record that as a platform limitation in the active decision trace.
Dispatch mode: `{dispatch_mode}`.

## Briefs

| Domain | Brief | Status | Accepted By Orchestrator |
|---|---|---|---|
{rows}

## Parallel Waves

{wave_text}

## Dispatch Prompts

{commands}

## Orchestrator Duties

- Pass one brief per subagent.
- Keep subagent scopes disjoint when edits are allowed.
- Review returned evidence before accepting it.
- Promote durable facts only through semantic notes after verification.
- Update this dispatch file and the active trace with outcomes.

## Plan Directory

`{relpath(plan_dir, root)}`
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create subagent briefs and a dispatch manifest.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--task", required=True)
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--trace")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--protected-test", action="append", default=[])
    parser.add_argument("--verification", default="No verification command provided.")
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument("--depends-on", action="append", default=[])
    parser.add_argument("--workflow-pattern", choices=["fan-out-and-synthesize", "adversarial-verification"], default="")
    parser.add_argument("--wave-purpose", default="")
    parser.add_argument("--slug")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    domains = args.domain or ["implementation"]
    slugs = [slugify(domain) for domain in domains]
    if len(set(slugs)) != len(slugs):
        parser.error("domains must have unique slugs")
    try:
        dependencies = parse_dependencies(args.depends_on, slugs)
        waves = build_waves(slugs, dependencies, args.parallel)
    except ValueError as exc:
        parser.error(str(exc))
    wave_by_slug: dict[str, int] = {}
    for wave in waves:
        for slug in wave["domains"]:
            wave_by_slug[str(slug)] = int(wave["index"])
    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(args.slug or args.task)
    plan_dir = local_dir / "subagents" / f"{stamp}-{slug}"
    plan_dir.mkdir(parents=True, exist_ok=True)

    trace = None
    if args.trace:
        trace = Path(args.trace)
        if not trace.is_absolute():
            trace = root / trace
        trace = trace.resolve()
    briefs: list[Path] = []
    domain_records: list[dict[str, object]] = []
    for domain, domain_slug in zip(domains, slugs):
        path = plan_dir / f"{domain_slug}.md"
        path.write_text(
            brief_text(
                args.task,
                domain,
                root,
                trace,
                args.file,
                args.protected_test,
                args.verification,
            ).rstrip() + "\n",
            encoding="utf-8",
        )
        briefs.append(path)
        domain_records.append({
            "name": domain,
            "slug": domain_slug,
            "brief": relpath(path, root),
            "wave": wave_by_slug[domain_slug],
            "depends_on": dependencies.get(domain_slug, []),
        })

    dispatch = plan_dir / "_dispatch.md"
    dispatch_mode = "parallel" if args.parallel else "sequential"
    dispatch.write_text(
        dispatch_text(
            args.task,
            plan_dir,
            domain_records,
            waves,
            root,
            dispatch_mode,
            args.workflow_pattern,
            args.wave_purpose,
        ).rstrip() + "\n",
        encoding="utf-8",
    )
    (plan_dir / "manifest.json").write_text(
        json.dumps({
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "task": args.task,
            "trace": relpath(trace, root) if trace else None,
            "briefs": [relpath(path, root) for path in briefs],
            "domains": domain_records,
            "dependencies": dependencies,
            "dispatch_mode": dispatch_mode,
            "domain_status": {
                record["slug"]: {
                    "accepted_by": None,
                    "domain": record["name"],
                    "result": None,
                    "status": "pending",
                    "summary": "",
                    "wave": record["wave"],
                }
                for record in domain_records
            },
            "waves": waves,
            "verification": args.verification,
            "workflow": {
                "pattern": args.workflow_pattern,
                "wave_purpose": args.wave_purpose,
            },
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(plan_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

SUBAGENT_RESULT_SCRIPT = r'''#!/usr/bin/env python3
"""Record a subagent result in the dispatch package and active trace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from memory_core import relpath, slugify


STATUSES = ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED")
SESSION_STATES = ("open", "closed", "keep-open", "close-unavailable")


def resolve_path(value: str, root: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def bullet_lines(items: list[str]) -> str:
    if not items:
        return "- none\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def load_manifest(plan_dir: Path) -> dict[str, object]:
    path = plan_dir / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(plan_dir: Path, manifest: dict[str, object]) -> None:
    target = plan_dir / "manifest.json"
    tmp = plan_dir / "manifest.json.tmp"
    tmp.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def session_state(args: argparse.Namespace) -> tuple[str, str]:
    if args.closed:
        return "closed", "closed while recording result"
    if args.keep_open_reason:
        return "keep-open", args.keep_open_reason
    if args.close_unavailable_reason:
        return "close-unavailable", args.close_unavailable_reason
    return "open", ""


def update_dispatch(dispatch: Path, slug: str, status: str, accepted_by: str, result_rel: str, summary: str) -> None:
    text = dispatch.read_text(encoding="utf-8") if dispatch.exists() else "# Subagent Dispatch\n"
    lines = []
    updated = False
    for line in text.splitlines():
        if line.startswith(f"| {slug} |"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            brief = cells[1] if len(cells) > 1 else ""
            lines.append(f"| {slug} | {brief} | {status} | {accepted_by or 'pending'} |")
            updated = True
        else:
            lines.append(line)
    text = "\n".join(lines).rstrip() + "\n"
    if not updated:
        text += f"\n| {slug} | `{result_rel}` | {status} | {accepted_by or 'pending'} |\n"
    entry = f"- `{result_rel}`: {status}"
    if accepted_by:
        entry += f", accepted by {accepted_by}"
    if summary:
        entry += f" - {summary}"
    if "## Result Log" not in text:
        text += "\n## Result Log\n\n"
    text = text.rstrip() + "\n" + entry + "\n"
    dispatch.write_text(text, encoding="utf-8")


def append_trace(trace: Path, slug: str, status: str, result_rel: str, accepted_by: str, summary: str) -> None:
    if not trace.exists():
        return
    text = trace.read_text(encoding="utf-8")
    entry = f"- `{slug}`: {status}; evidence `{result_rel}`"
    if accepted_by:
        entry += f"; accepted by {accepted_by}"
    if summary:
        entry += f"; {summary}"
    if "## Subagent Results" not in text:
        text = text.rstrip() + "\n\n## Subagent Results\n\n"
    text = text.rstrip() + "\n" + entry + "\n"
    trace.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a subagent result.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--status", choices=STATUSES, required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--accepted-by", default="")
    parser.add_argument("--files-read", action="append", default=[])
    parser.add_argument("--commands-run", action="append", default=[])
    parser.add_argument("--finding", action="append", default=[])
    parser.add_argument("--risk", action="append", default=[])
    parser.add_argument("--suggested-memory-update", action="append", default=[])
    parser.add_argument("--session-id", default="")
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument("--closed", action="store_true")
    session_group.add_argument("--keep-open-reason", default="")
    session_group.add_argument("--close-unavailable-reason", default="")
    parser.add_argument("--trace")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan_dir = resolve_path(args.plan_dir, root)
    plan_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.domain)
    results_dir = plan_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    result_path = results_dir / f"{slug}-result.md"
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    session_status, session_reason = session_state(args)
    session_closed_at = timestamp if session_status == "closed" else ""
    session_record = {
        "session_id": args.session_id or None,
        "session_state": session_status,
        "session_reason": session_reason,
        "session_updated_at": timestamp,
    }
    if session_closed_at:
        session_record["session_closed_at"] = session_closed_at

    result_text = f"""# Subagent Result: {args.domain}

## Status

{args.status}

## Summary

{args.summary or "none"}

## Accepted By Orchestrator

{args.accepted_by or "pending"}

## Session

- ID: {args.session_id or "unknown"}
- State: {session_status}
- Reason: {session_reason or "none"}

## Files Read

{bullet_lines(args.files_read).rstrip()}

## Commands Run

{bullet_lines(args.commands_run).rstrip()}

## Findings

{bullet_lines(args.finding).rstrip()}

## Risks

{bullet_lines(args.risk).rstrip()}

## Suggested Memory Updates

{bullet_lines(args.suggested_memory_update).rstrip()}
"""
    result_path.write_text(result_text.rstrip() + "\n", encoding="utf-8")

    manifest = load_manifest(plan_dir)
    trace_value = args.trace or manifest.get("trace")
    result_rel = relpath(result_path, root)
    result_record = {
        "accepted_by": args.accepted_by or None,
        "domain": args.domain,
        "path": result_rel,
        "status": args.status,
        "summary": args.summary,
        "timestamp": timestamp,
        **session_record,
    }
    manifest.setdefault("results", [])
    assert isinstance(manifest["results"], list)
    manifest["results"].append(result_record)
    domain_status = manifest.get("domain_status")
    if isinstance(domain_status, dict):
        if slug not in domain_status:
            print(f"domain is not in dispatch manifest: {args.domain}", file=sys.stderr)
            return 2
        status_record = domain_status.get(slug)
        if not isinstance(status_record, dict):
            status_record = {}
        status_record.update({
            "accepted_by": args.accepted_by or None,
            "domain": args.domain,
            "result": result_rel,
            "status": args.status,
            "summary": args.summary,
            "updated_at": result_record["timestamp"],
            **session_record,
        })
        domain_status[slug] = status_record
    save_manifest(plan_dir, manifest)

    update_dispatch(
        plan_dir / "_dispatch.md",
        slug,
        args.status,
        args.accepted_by,
        result_rel,
        args.summary,
    )

    if trace_value:
        append_trace(
            resolve_path(str(trace_value), root),
            slug,
            args.status,
            result_rel,
            args.accepted_by,
            args.summary,
        )

    print(result_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

SELECTIVE_REVERT_SCRIPT = r'''#!/usr/bin/env python3
"""Create and apply auditable selective rollback plans.

The script defaults to planning only. Mutating operations require the `apply`
subcommand and the explicit `--apply` flag.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


EXCLUDED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "rollback"


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def resolve_inside(root: Path, value: str | Path) -> Path:
    raw = Path(value)
    path = raw if raw.is_absolute() else root / raw
    resolved = path.resolve()
    if not is_relative_to(resolved, root):
        raise ValueError(f"path is outside workspace: {value}")
    return resolved


def excluded_for_auto_collect(path: Path, root: Path, local_dir: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    if any(part in EXCLUDED_PARTS for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == local_dir.name and parts[1] in {"rollback", "memory"}:
        return True
    return False


def collect_workspace_files(root: Path, local_dir: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not excluded_for_auto_collect(path, root, local_dir):
            files.append(relpath(path, root))
    return files


def expand_requested_paths(root: Path, values: list[str], local_dir: Path, auto_collect: bool = False) -> list[str]:
    if not values and auto_collect:
        return collect_workspace_files(root, local_dir)
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        resolved = resolve_inside(root, value)
        if resolved.is_dir():
            for child in sorted(resolved.rglob("*")):
                if child.is_file():
                    rel = relpath(child, root)
                    if rel not in seen:
                        seen.add(rel)
                        result.append(rel)
            continue
        rel = relpath(resolved, root)
        if rel not in seen:
            seen.add(rel)
            result.append(rel)
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_if_file(source: Path, dest: Path) -> bool:
    if not source.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return True


def backup_current(root: Path, rel_paths: list[str], dest: Path) -> list[str]:
    copied: list[str] = []
    for rel in rel_paths:
        source = root / rel
        if copy_if_file(source, dest / rel):
            copied.append(rel)
    return copied


def read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit(result: dict[str, object], json_output: bool) -> None:
    if json_output:
        print(json.dumps(result, sort_keys=True))
    else:
        print(result["manifest"])


def run_git(root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result


def require_git_repo(root: Path) -> None:
    result = run_git(root, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise ValueError("git mode requires a Git repository; create a checkpoint or run inside a Git repo")
    top = Path(result.stdout.strip()).resolve()
    if not is_relative_to(root, top) and top != root:
        raise ValueError(f"workspace root is outside Git repository root: {top}")


def ensure_no_staged_changes(root: Path, paths: list[str]) -> None:
    result = run_git(root, ["diff", "--cached", "--quiet", "--", *paths])
    if result.returncode == 1:
        raise ValueError("selected paths have staged changes; unstage them before selective revert")
    if result.returncode not in (0, 1):
        raise ValueError(result.stderr.strip() or "could not inspect staged changes")


def make_run_dir(local_dir: Path, kind: str, label: str) -> Path:
    path = local_dir / "rollback" / kind / f"{utc_stamp()}-{slugify(label)}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def checkpoint(root: Path, local_dir: Path, label: str, paths: list[str], json_output: bool) -> int:
    rel_paths = expand_requested_paths(root, paths, local_dir, auto_collect=True)
    run_dir = make_run_dir(local_dir, "checkpoints", label)
    files_dir = run_dir / "files"
    entries: list[dict[str, object]] = []
    for rel in rel_paths:
        source = root / rel
        entry: dict[str, object] = {"path": rel, "exists": source.is_file()}
        if source.is_file():
            copy_if_file(source, files_dir / rel)
            entry["bytes"] = source.stat().st_size
            entry["sha256"] = sha256_file(source)
            entry["snapshot"] = rel
        entries.append(entry)

    manifest = {
        "version": 1,
        "kind": "checkpoint",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "label": label,
        "root": str(root),
        "entries": entries,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    (run_dir / "plan.md").write_text(
        "\n".join(
            [
                f"# Checkpoint: {label}",
                "",
                f"- Root: `{root}`",
                f"- Files recorded: {len(entries)}",
                "",
                "Use this checkpoint with:",
                "",
                f"`selective-revert.py plan --root {root} --checkpoint {manifest_path}`",
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    emit({"manifest": str(manifest_path), "entries": len(entries), "kind": "checkpoint"}, json_output)
    return 0


def load_manifest(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"manifest must contain a JSON object: {path}")
    return data


def resolve_manifest(root: Path, local_dir: Path, value: str) -> Path:
    raw = Path(value)
    if raw.is_absolute() or raw.exists() or raw.suffix == ".json":
        path = raw if raw.is_absolute() else root / raw
    else:
        path = local_dir / "rollback" / "checkpoints" / value / "manifest.json"
    resolved = path.resolve()
    if not is_relative_to(resolved, root):
        raise ValueError(f"manifest is outside workspace: {value}")
    if not resolved.is_file():
        raise ValueError(f"manifest not found: {value}")
    return resolved


def write_git_plan_md(path: Path, root: Path, paths: list[str], base: str, patch_path: Path) -> None:
    lines = [
        "# Selective Revert Plan",
        "",
        "- Mode: git",
        f"- Root: `{root}`",
        f"- Base: `{base}`",
        f"- Patch: `{patch_path}`",
        "",
        "## Selected Paths",
        "",
    ]
    lines.extend(f"- `{rel}`" for rel in paths)
    lines.extend(
        [
            "",
            "## Apply",
            "",
            "Inspect `reverse.patch` first. You may delete unrelated hunks from the patch, but keep paths inside the selected set.",
            "",
            f"`selective-revert.py apply --root {root} --plan {path / 'manifest.json'} --apply`",
        ]
    )
    (path / "plan.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def plan_git(root: Path, local_dir: Path, paths: list[str], base: str, label: str, json_output: bool) -> int:
    if not paths:
        raise ValueError("git selective revert requires at least one --path")
    require_git_repo(root)
    rel_paths = expand_requested_paths(root, paths, local_dir)
    ensure_no_staged_changes(root, rel_paths)
    run_dir = make_run_dir(local_dir, "plans", label)
    backup_current(root, rel_paths, run_dir / "backups" / "current")
    diff = run_git(root, ["diff", "--binary", "-R", base, "--", *rel_paths], check=True).stdout
    patch_path = run_dir / "reverse.patch"
    patch_path.write_text(diff, encoding="utf-8")
    check = run_git(root, ["apply", "--check", str(patch_path)])
    if check.returncode != 0:
        raise ValueError(check.stderr.strip() or "reverse patch does not apply cleanly")
    manifest = {
        "version": 1,
        "kind": "rollback-plan",
        "mode": "git",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "base": base,
        "paths": rel_paths,
        "reverse_patch": "reverse.patch",
        "backup_dir": "backups/current",
        "requires_apply_flag": True,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    write_git_plan_md(run_dir, root, rel_paths, base, patch_path)
    emit({"manifest": str(manifest_path), "paths": rel_paths, "mode": "git"}, json_output)
    return 0


def text_diff_for_checkpoint(root: Path, checkpoint_dir: Path, operations: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for op in operations:
        rel = str(op["path"])
        action = str(op["action"])
        current = root / rel
        snap = checkpoint_dir / "files" / rel
        if action == "restore":
            current_text = read_text_or_none(current) if current.exists() else ""
            target_text = read_text_or_none(snap)
            if target_text is None or current_text is None:
                chunks.append(f"# Binary or unreadable restore: {rel}\n")
                continue
            chunks.extend(
                difflib.unified_diff(
                    current_text.splitlines(keepends=True),
                    target_text.splitlines(keepends=True),
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                )
            )
        elif action == "delete":
            chunks.append(f"# Delete created file with --allow-delete: {rel}\n")
    return "".join(chunks)


def plan_checkpoint(root: Path, local_dir: Path, checkpoint_value: str, paths: list[str], label: str, json_output: bool) -> int:
    checkpoint_manifest_path = resolve_manifest(root, local_dir, checkpoint_value)
    checkpoint_data = load_manifest(checkpoint_manifest_path)
    if checkpoint_data.get("kind") != "checkpoint":
        raise ValueError("checkpoint plan requires a checkpoint manifest")
    checkpoint_dir = checkpoint_manifest_path.parent
    entries = checkpoint_data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("checkpoint manifest is missing entries")
    by_path: dict[str, dict[str, object]] = {}
    for item in entries:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            by_path[str(item["path"])] = item

    rel_paths = expand_requested_paths(root, paths, local_dir) if paths else sorted(by_path)
    operations: list[dict[str, object]] = []
    for rel in rel_paths:
        if rel not in by_path:
            raise ValueError(f"path was not captured in checkpoint: {rel}")
        entry = by_path[rel]
        existed = bool(entry.get("exists"))
        current = root / rel
        if existed:
            snap = checkpoint_dir / "files" / rel
            if not snap.is_file():
                raise ValueError(f"checkpoint snapshot missing for: {rel}")
            current_hash = sha256_file(current) if current.is_file() else None
            snap_hash = sha256_file(snap)
            action = "noop" if current_hash == snap_hash else "restore"
            operations.append({"path": rel, "action": action})
        else:
            operations.append({"path": rel, "action": "delete" if current.exists() else "noop", "requires_allow_delete": current.exists()})

    run_dir = make_run_dir(local_dir, "plans", label)
    backup_current(root, rel_paths, run_dir / "backups" / "current")
    (run_dir / "reverse.patch").write_text(text_diff_for_checkpoint(root, checkpoint_dir, operations), encoding="utf-8")
    manifest = {
        "version": 1,
        "kind": "rollback-plan",
        "mode": "checkpoint",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root),
        "checkpoint_manifest": relpath(checkpoint_manifest_path, root),
        "paths": rel_paths,
        "operations": operations,
        "backup_dir": "backups/current",
        "requires_apply_flag": True,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    lines = [
        "# Selective Revert Plan",
        "",
        "- Mode: checkpoint",
        f"- Root: `{root}`",
        f"- Checkpoint: `{checkpoint_manifest_path}`",
        "",
        "## Operations",
        "",
    ]
    lines.extend(f"- {item['action']}: `{item['path']}`" for item in operations)
    lines.extend(["", "## Apply", "", f"`selective-revert.py apply --root {root} --plan {manifest_path} --apply`"])
    (run_dir / "plan.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    emit({"manifest": str(manifest_path), "paths": rel_paths, "mode": "checkpoint"}, json_output)
    return 0


def patch_paths(patch_text: str) -> set[str]:
    paths: set[str] = set()
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            for token in parts[2:4]:
                if token.startswith(("a/", "b/")):
                    paths.add(token[2:])
    return paths


def apply_git_plan(root: Path, plan_path: Path) -> None:
    manifest = load_manifest(plan_path)
    patch = plan_path.parent / str(manifest.get("reverse_patch", "reverse.patch"))
    if not patch.is_file():
        raise ValueError(f"reverse patch not found: {patch}")
    allowed = {str(path).replace("\\", "/") for path in manifest.get("paths", []) if isinstance(path, str)}
    touched = patch_paths(patch.read_text(encoding="utf-8"))
    outside = sorted(touched - allowed)
    if outside:
        raise ValueError(f"reverse patch touches paths outside the plan: {', '.join(outside)}")
    check = run_git(root, ["apply", "--check", str(patch)])
    if check.returncode != 0:
        raise ValueError(check.stderr.strip() or "reverse patch does not apply cleanly")
    run_git(root, ["apply", str(patch)], check=True)


def apply_checkpoint_plan(root: Path, plan_path: Path, allow_delete: bool) -> None:
    manifest = load_manifest(plan_path)
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        raise ValueError("checkpoint rollback plan is missing operations")
    checkpoint_rel = manifest.get("checkpoint_manifest")
    if not isinstance(checkpoint_rel, str):
        raise ValueError("checkpoint rollback plan is missing checkpoint_manifest")
    checkpoint_path = resolve_inside(root, checkpoint_rel)
    checkpoint_dir = checkpoint_path.parent
    delete_ops = [op for op in operations if isinstance(op, dict) and op.get("action") == "delete"]
    if delete_ops and not allow_delete:
        raise ValueError("plan would delete files created after the checkpoint; rerun with --allow-delete")
    for op in operations:
        if not isinstance(op, dict) or not isinstance(op.get("path"), str):
            continue
        rel = str(op["path"])
        target = resolve_inside(root, rel)
        action = op.get("action")
        if action == "restore":
            source = checkpoint_dir / "files" / rel
            if not source.is_file():
                raise ValueError(f"checkpoint snapshot missing for: {rel}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif action == "delete":
            if target.is_dir():
                raise ValueError(f"refusing to delete directory: {rel}")
            if target.exists():
                target.unlink()


def apply_plan(root: Path, plan_value: str, allow_delete: bool, confirm_apply: bool) -> int:
    plan_path = resolve_inside(root, plan_value)
    if not plan_path.is_file():
        raise ValueError(f"plan manifest not found: {plan_value}")
    if not confirm_apply:
        raise ValueError("refusing to mutate without --apply")
    manifest = load_manifest(plan_path)
    if manifest.get("kind") != "rollback-plan":
        raise ValueError("apply requires a rollback-plan manifest")
    mode = manifest.get("mode")
    if mode == "git":
        apply_git_plan(root, plan_path)
    elif mode == "checkpoint":
        apply_checkpoint_plan(root, plan_path, allow_delete)
    else:
        raise ValueError(f"unknown rollback plan mode: {mode}")
    (plan_path.parent / "result.md").write_text(
        "\n".join(
            [
                "# Selective Revert Result",
                "",
                f"- Applied at: {dt.datetime.now(dt.timezone.utc).isoformat()}",
                f"- Mode: {mode}",
                f"- Plan: `{plan_path}`",
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    print(plan_path.parent / "result.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and apply safe selective file reverts.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    sub = parser.add_subparsers(dest="command", required=True)

    checkpoint_parser = sub.add_parser("checkpoint", help="Record a native rollback checkpoint.")
    checkpoint_parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    checkpoint_parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)
    checkpoint_parser.add_argument("--label", required=True)
    checkpoint_parser.add_argument("--path", action="append", default=[])
    checkpoint_parser.add_argument("--json", action="store_true")

    plan_parser = sub.add_parser("plan", help="Create a rollback plan without mutating files.")
    plan_parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    plan_parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)
    plan_parser.add_argument("--path", action="append", default=[])
    plan_parser.add_argument("--base", default="HEAD")
    plan_parser.add_argument("--checkpoint")
    plan_parser.add_argument("--label", default="selective-revert")
    plan_parser.add_argument("--json", action="store_true")

    apply_parser = sub.add_parser("apply", help="Apply a previously generated rollback plan.")
    apply_parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    apply_parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--apply", action="store_true")
    apply_parser.add_argument("--allow-delete", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    try:
        if args.command == "checkpoint":
            return checkpoint(root, local_dir, args.label, args.path, args.json)
        if args.command == "plan":
            if args.checkpoint:
                return plan_checkpoint(root, local_dir, args.checkpoint, args.path, args.label, args.json)
            return plan_git(root, local_dir, args.path, args.base, args.label, args.json)
        if args.command == "apply":
            return apply_plan(root, args.plan, args.allow_delete, args.apply)
    except (RuntimeError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''

MEMORY_MAINTENANCE_SCRIPT = r'''#!/usr/bin/env python3
"""Report memory growth and retrieval-maintenance candidates without deleting source files."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from memory_core import file_title, find_local_dir, relpath, source_lines
from memory_policy import has_high_severity, policy_candidates


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def frontmatter_value(text: str, key: str) -> str | None:
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not in_frontmatter:
            in_frontmatter = True
            continue
        if stripped == "---" and in_frontmatter:
            break
        if in_frontmatter and stripped.startswith(f"{key}:"):
            return stripped.split(":", 1)[1].strip()
    return None


def resolve_source(note: Path, source: str) -> Path:
    path = Path(source.strip().strip("`"))
    if not path.is_absolute():
        path = note.parent / path
    return path.resolve()


def promoted_traces(root: Path, local_dir: Path) -> set[str]:
    traces: set[str] = set()
    log = local_dir / "memory" / "promotion_log.jsonl"
    if not log.exists():
        return traces
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        trace = str(item.get("trace", "")).replace("\\", "/")
        if trace:
            traces.add(trace)
            traces.add(Path(trace).name)
    return traces


def add_candidate(candidates: list[dict[str, object]], action: str, path: Path, root: Path, reason: str, size: int | None = None) -> None:
    item: dict[str, object] = {
        "action": action,
        "path": relpath(path, root),
        "reason": reason,
    }
    if size is not None:
        item["bytes"] = size
    candidates.append(item)


def build_report(root: Path, agent: str, max_note_bytes: int, max_trace_bytes: int, stale_days: int) -> dict[str, object]:
    local_dir = find_local_dir(root, agent)
    today = dt.date.today()
    candidates: list[dict[str, object]] = []
    note_count = 0
    trace_count = 0
    note_bytes = 0
    trace_bytes = 0

    notes = local_dir / "notes"
    if notes.exists():
        for note in sorted(notes.rglob("*.md")):
            if note.name == "_index.md":
                continue
            note_count += 1
            size = note.stat().st_size
            note_bytes += size
            text = note.read_text(encoding="utf-8")
            if size > max_note_bytes:
                add_candidate(candidates, "compact-note", note, root, f"note exceeds {max_note_bytes} bytes", size)
            verified = frontmatter_value(text, "last_verified")
            verified_date = parse_date(verified or "")
            if verified_date and (today - verified_date).days > stale_days:
                add_candidate(candidates, "revalidate-note", note, root, f"last_verified is older than {stale_days} days")
            for source in source_lines(text):
                if not resolve_source(note, source).exists():
                    add_candidate(candidates, "repair-source", note, root, f"missing source: {source}")

    promoted = promoted_traces(root, local_dir)
    traces = local_dir / "decision-traces"
    if traces.exists():
        for trace in sorted(traces.rglob("*.md")):
            if trace.name == "_index.md":
                continue
            trace_count += 1
            size = trace.stat().st_size
            trace_bytes += size
            rel = relpath(trace, root)
            if size > max_trace_bytes:
                add_candidate(candidates, "summarize-trace", trace, root, f"trace exceeds {max_trace_bytes} bytes", size)
            if rel in promoted or trace.name in promoted:
                add_candidate(candidates, "archive-promoted-trace", trace, root, "trace has promotion-log evidence; keep audit path but remove it from routine retrieval when ready")

    candidates.extend(policy_candidates(root, local_dir, max_trace_bytes=max_trace_bytes))

    manifest_path = local_dir / "memory" / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"error": "manifest is not valid JSON"}

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": {
            "max_note_bytes": max_note_bytes,
            "max_trace_bytes": max_trace_bytes,
            "stale_days": stale_days,
            "mode": "report-only",
        },
        "counts": {
            "notes": note_count,
            "traces": trace_count,
            "note_bytes": note_bytes,
            "trace_bytes": trace_bytes,
            "memory_documents": manifest.get("document_count"),
            "memory_shards": len(manifest.get("shards", [])) if isinstance(manifest.get("shards"), list) else None,
        },
        "candidates": candidates,
    }


def write_report(root: Path, local_dir: Path, report: dict[str, object]) -> None:
    out = local_dir / "memory" / "maintenance"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Memory Maintenance Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Counts",
        "",
    ]
    counts = report["counts"]
    assert isinstance(counts, dict)
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Candidates", ""])
    candidates = report["candidates"]
    assert isinstance(candidates, list)
    if not candidates:
        lines.append("- none")
    else:
        for item in candidates:
            assert isinstance(item, dict)
            lines.append(f"- {item['action']}: `{item['path']}` - {item['reason']}")
    (out / "latest-report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report memory maintenance candidates.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--max-note-bytes", type=int, default=8192)
    parser.add_argument("--max-trace-bytes", type=int, default=24576)
    parser.add_argument("--stale-days", type=int, default=90)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when high-severity hygiene issues are found.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    report = build_report(root, args.agent, args.max_note_bytes, args.max_trace_bytes, args.stale_days)
    write_report(root, local_dir, report)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(local_dir / "memory" / "maintenance" / "latest-report.md")
    if args.strict and has_high_severity(report["candidates"]):  # type: ignore[arg-type]
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

MEMORY_TOUCH_SCRIPT = r'''#!/usr/bin/env python3
"""Record Fable Harness memory use without editing the source memory file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_core import record_memory_touch


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a note, trace, or dormant memory touch.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--path", required=True, help="Memory path that was loaded or used.")
    parser.add_argument("--reason", default="", help="Short reason for the memory touch.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = record_memory_touch(Path(args.root), args.path, args.reason, args.agent)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{result['path']} use_count={result['use_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

MEMORY_DREAM_SCRIPT = r'''#!/usr/bin/env python3
"""Plan, apply, search, and reactivate Fable Harness memory dreams."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_core import apply_dream_run, create_dream_plan, maintain_memory_dream, reactivate_dormant_memory, search_dormant_memory


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=argparse.SUPPRESS, help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default=argparse.SUPPRESS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Fable Harness memory dreams.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Plan a memory dreaming consolidation run.")
    add_common_args(plan_parser)
    plan_parser.add_argument("--context", default="", help="Current task context used for relevance scoring.")
    plan_parser.add_argument("--json", action="store_true")

    maintain_parser = sub.add_parser("maintain", help="Plan memory dreaming, apply safe mechanical actions, and write agent review.")
    add_common_args(maintain_parser)
    maintain_parser.add_argument("--context", default="", help="Current task context used for relevance scoring.")
    maintain_parser.add_argument("--auto-safe", action="store_true", help="Apply context-cold safe mechanical actions.")
    maintain_parser.add_argument("--agent-review", action="store_true", help="Write agent-review.md for semantic decisions.")
    maintain_parser.add_argument("--json", action="store_true")

    apply_parser = sub.add_parser("apply", help="Apply a reviewed memory dreaming plan.")
    add_common_args(apply_parser)
    apply_parser.add_argument("--run", required=True, help="Reviewed memory dream run directory or run id.")
    apply_parser.add_argument("--apply", action="store_true", help="Confirm intentional mutation.")
    apply_parser.add_argument("--json", action="store_true")

    search_parser = sub.add_parser("search-dormant", help="Search dormant memory before declaring context unavailable.")
    add_common_args(search_parser)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--json", action="store_true")

    reactivate_parser = sub.add_parser("reactivate", help="Reactivate dormant memory into compact notes.")
    add_common_args(reactivate_parser)
    reactivate_parser.add_argument("--query", required=True)
    reactivate_parser.add_argument("--category", required=True)
    reactivate_parser.add_argument("--area")
    reactivate_parser.add_argument("--topic", required=True)
    reactivate_parser.add_argument("--apply", action="store_true")
    reactivate_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "plan":
            result = create_dream_plan(root, args.agent, args.context)
            if args.json:
                print(json.dumps(result, sort_keys=True))
            else:
                print(result["run_dir"])
            return 0
        if args.command == "maintain":
            result = maintain_memory_dream(root, args.agent, args.context, args.auto_safe, args.agent_review)
            if args.json:
                print(json.dumps(result, sort_keys=True))
            else:
                print(result["run_dir"])
            return 0
        if args.command == "apply":
            if not args.apply:
                raise ValueError("refusing to mutate without --apply")
            result = apply_dream_run(root, args.run, args.agent)
            if args.json:
                print(json.dumps(result, sort_keys=True))
            else:
                print(result["dormant_manifest"])
            return 0
        if args.command == "search-dormant":
            results = search_dormant_memory(root, args.query, args.agent, args.limit)
            if args.json:
                print(json.dumps(results, ensure_ascii=False, sort_keys=True))
            else:
                for result in results:
                    print(f"{result['score']:.4f} {result['original_path']} -> {result['dormant_path']} - {result['title']}")
            return 0
        if args.command == "reactivate":
            result = reactivate_dormant_memory(
                root,
                args.query,
                args.category,
                args.area,
                args.topic,
                args.agent,
                args.apply,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            else:
                print(result["note_path"])
            return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("memory-dream.py is not implemented yet")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''


SUBAGENT_SWEEP_SCRIPT = r'''#!/usr/bin/env python3
"""Close or justify completed subagent sessions before final loop closure."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from memory_core import slugify


DONE_STATUSES = {"DONE", "DONE_WITH_CONCERNS"}
FINAL_SESSION_STATES = {"closed", "keep-open", "close-unavailable"}


def resolve_path(value: str, root: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def load_manifest(plan_dir: Path) -> dict[str, object]:
    path = plan_dir / "manifest.json"
    if not path.exists():
        raise ValueError(f"dispatch manifest not found: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"invalid dispatch manifest: {path}")
    return manifest


def save_manifest(plan_dir: Path, manifest: dict[str, object]) -> None:
    target = plan_dir / "manifest.json"
    tmp = plan_dir / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def parse_domain_reasons(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            raise ValueError(f"expected DOMAIN:REASON, got: {value}")
        domain, reason = value.split(":", 1)
        slug = slugify(domain)
        reason = reason.strip()
        if not slug or not reason:
            raise ValueError(f"expected non-empty DOMAIN:REASON, got: {value}")
        parsed[slug] = reason
    return parsed


def is_finalized(status_record: dict[str, object]) -> bool:
    state = str(status_record.get("session_state") or "").strip()
    if state == "closed":
        return True
    if state in {"keep-open", "close-unavailable"}:
        return bool(str(status_record.get("session_reason") or "").strip())
    return False


def append_dispatch_log(plan_dir: Path, report: dict[str, object]) -> None:
    dispatch = plan_dir / "_dispatch.md"
    text = dispatch.read_text(encoding="utf-8") if dispatch.exists() else "# Subagent Dispatch\n"
    if "## Session Closure Log" not in text:
        text = text.rstrip() + "\n\n## Session Closure Log\n"
    entry = (
        f"- {report['timestamp']}: closed={', '.join(report['closed']) or 'none'}; "
        f"kept-open={', '.join(report['kept_open']) or 'none'}; "
        f"close-unavailable={', '.join(report['close_unavailable']) or 'none'}; "
        f"unchanged={', '.join(report['unchanged']) or 'none'}"
    )
    text = text.rstrip() + "\n" + entry + "\n"
    dispatch.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Close or justify completed subagent sessions.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--close-completed", action="store_true")
    parser.add_argument("--close-unavailable", action="store_true")
    parser.add_argument("--keep-open", action="append", default=[], metavar="DOMAIN:REASON")
    parser.add_argument("--reason", default="final subagent session sweep")
    parser.add_argument("--closed-by", default="orchestrator")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan_dir = resolve_path(args.plan_dir, root)
    try:
        keep_open = parse_domain_reasons(args.keep_open)
        manifest = load_manifest(plan_dir)
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    domain_status = manifest.get("domain_status", {})
    if not isinstance(domain_status, dict):
        print("dispatch manifest has no domain_status object", file=sys.stderr)
        return 2

    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    report: dict[str, object] = {
        "timestamp": timestamp,
        "closed": [],
        "kept_open": [],
        "close_unavailable": [],
        "skipped": [],
        "unchanged": [],
    }

    for domain, raw_status in sorted(domain_status.items()):
        slug = str(domain)
        if not isinstance(raw_status, dict):
            report["skipped"].append(slug)
            continue
        status = str(raw_status.get("status", "")).strip()
        accepted_by = str(raw_status.get("accepted_by") or "").strip()
        if status not in DONE_STATUSES or not accepted_by:
            report["skipped"].append(slug)
            continue
        if is_finalized(raw_status):
            report["unchanged"].append(slug)
            continue
        if slug in keep_open:
            raw_status.update({
                "session_state": "keep-open",
                "session_reason": keep_open[slug],
                "session_updated_at": timestamp,
                "session_closed_by": args.closed_by,
            })
            report["kept_open"].append(slug)
            continue
        if not args.close_completed:
            report["skipped"].append(slug)
            continue
        if args.close_unavailable:
            raw_status.update({
                "session_state": "close-unavailable",
                "session_reason": args.reason,
                "session_updated_at": timestamp,
                "session_closed_by": args.closed_by,
            })
            report["close_unavailable"].append(slug)
        else:
            raw_status.update({
                "session_state": "closed",
                "session_reason": args.reason,
                "session_updated_at": timestamp,
                "session_closed_at": timestamp,
                "session_closed_by": args.closed_by,
            })
            report["closed"].append(slug)
        domain_status[slug] = raw_status

    manifest["domain_status"] = domain_status
    manifest["session_closure"] = report
    save_manifest(plan_dir, manifest)

    report_path = plan_dir / "session-closure.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_dispatch_log(plan_dir, report)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


LOOP_CORE_SCRIPT = r'''#!/usr/bin/env python3
"""Shared helpers for Fable Harness native loop governance scripts."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

try:
    from workflow_core import workflow_errors
except Exception:
    workflow_errors = None


SCHEMA = "fable-harness-loop-governance-v1"
STATES = {
    "created",
    "oriented",
    "inspecting",
    "decided",
    "acting",
    "verifying",
    "repairing",
    "memory_closure",
    "closed",
    "blocked",
}
INSPECT_KINDS = {
    "file.read",
    "note.read",
    "trace.opened",
    "memory.search",
    "graph.query",
    "code-graph.query",
    "subagent.result.recorded",
    "subagent.result.accepted",
}
DECIDE_KINDS = {"decision.recorded", "loop.decided"}
MUTATION_KINDS = {
    "file.edited",
    "mutation.started",
    "mutation.finished",
    "command.mutating",
    "note.promoted",
    "memory.rebuilt",
}
VERIFY_KINDS = {
    "test.run",
    "test.passed",
    "test.failed",
    "verification.passed",
    "verification.failed",
    "check.passed",
    "check.failed",
    "closure.passed",
    "memory.closure.passed",
}
VERIFY_PASS_KINDS = {"test.passed", "verification.passed", "check.passed", "closure.passed", "memory.closure.passed"}
VERIFY_FAIL_KINDS = {"test.failed", "verification.failed", "check.failed"}
CLOSURE_KINDS = {"closure.passed", "memory.closure.passed"}
REPAIR_KINDS = {"repair.started"}
SUBAGENT_RESULT_KINDS = {"subagent.result.recorded"}
SUBAGENT_ACCEPTANCE_KINDS = {"subagent.result.accepted", "subagent.result.rejected"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "loop"


def find_local_dir(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / ".codex"
    if agent == "claude":
        return root / ".claude"
    if agent == "any":
        return root / ".agents"
    if (root / ".codex").exists():
        return root / ".codex"
    if (root / ".claude").exists():
        return root / ".claude"
    return root / ".agents"


def relpath(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def display_path(root: Path, value: str | None) -> str | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        return value.replace("\\", "/")
    try:
        return relpath(path.resolve(), root)
    except ValueError:
        return str(path)


def loop_runs_dir(local_dir: Path) -> Path:
    return local_dir / "loop" / "runs"


def resolve_run_dir(root: Path, local_dir: Path, run: str) -> Path:
    candidate = Path(run).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    direct = (root / candidate).resolve()
    if direct.exists():
        return direct
    return (loop_runs_dir(local_dir) / run).resolve()


def state_path(run_dir: Path) -> Path:
    return run_dir / "state.json"


def events_path(run_dir: Path) -> Path:
    return run_dir / "events.jsonl"


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_state(run_dir: Path) -> dict[str, object]:
    path = state_path(run_dir)
    if not path.exists():
        raise ValueError(f"loop state not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid loop state: {path}")
    if data.get("schema") != SCHEMA:
        raise ValueError(f"unsupported loop schema: {data.get('schema')}")
    return data


def write_state(run_dir: Path, state: dict[str, object]) -> None:
    state["updated_at"] = now()
    write_json(state_path(run_dir), state)


def read_events(run_dir: Path) -> list[dict[str, object]]:
    path = events_path(run_dir)
    if not path.exists():
        return []
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if isinstance(event, dict):
            events.append(event)
    return events


def event_key(event: dict[str, object]) -> str:
    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        domain = metadata.get("domain")
        if domain:
            return str(domain)
    if event.get("path"):
        return str(event["path"])
    return str(event.get("summary") or event.get("id") or "subagent-result")


def analyze_events(events: list[dict[str, object]]) -> dict[str, object]:
    first_inspect: int | None = None
    first_decide: int | None = None
    first_mutation: int | None = None
    last_mutation: int | None = None
    last_verify: int | None = None
    last_verify_after_mutation: int | None = None
    closure_passed = False
    repair_attempts = 0
    latest_verification_result = ""
    latest_verification_result_after_mutation = ""
    pending_results: set[str] = set()
    accepted_results: set[str] = set()

    for index, event in enumerate(events):
        kind = str(event.get("kind", "")).strip()
        if kind in INSPECT_KINDS and first_inspect is None:
            first_inspect = index
        if kind in DECIDE_KINDS and first_decide is None:
            first_decide = index
        if kind in MUTATION_KINDS:
            if first_mutation is None:
                first_mutation = index
            last_mutation = index
        if kind in VERIFY_KINDS:
            last_verify = index
            if kind in VERIFY_PASS_KINDS:
                latest_verification_result = "passed"
            elif kind in VERIFY_FAIL_KINDS:
                latest_verification_result = "failed"
            else:
                latest_verification_result = "observed"
            if last_mutation is not None and index > last_mutation:
                last_verify_after_mutation = index
                latest_verification_result_after_mutation = latest_verification_result
        if kind in CLOSURE_KINDS:
            closure_passed = True
        if kind in REPAIR_KINDS:
            repair_attempts += 1
        if kind in SUBAGENT_RESULT_KINDS:
            pending_results.add(event_key(event))
        if kind in SUBAGENT_ACCEPTANCE_KINDS:
            key = event_key(event)
            accepted_results.add(key)
            pending_results.discard(key)

    has_mutation = first_mutation is not None
    flags = {
        "inspected": first_inspect is not None,
        "decided": first_decide is not None,
        "mutated": has_mutation,
        "verified": last_verify is not None,
        "closure_passed": closure_passed,
        "subagent_results_pending": bool(pending_results - accepted_results),
    }
    return {
        "event_count": len(events),
        "flags": flags,
        "first_inspect": first_inspect,
        "first_decide": first_decide,
        "first_mutation": first_mutation,
        "last_mutation": last_mutation,
        "last_verify": last_verify,
        "last_verify_after_mutation": last_verify_after_mutation,
        "latest_verification_result": latest_verification_result,
        "latest_verification_result_after_mutation": latest_verification_result_after_mutation,
        "repair_attempts": repair_attempts,
        "pending_subagent_results": sorted(pending_results - accepted_results),
    }


def resolve_state_reference(root: Path | None, value: object) -> Path | None:
    if not root or not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def unaccepted_subagent_domains(root: Path | None, state: dict[str, object]) -> list[str]:
    plan_ref = resolve_state_reference(root, state.get("subagent_plan"))
    if not plan_ref:
        return []
    manifest_path = plan_ref / "manifest.json" if plan_ref.is_dir() else plan_ref
    if not manifest_path.exists():
        return [f"missing-manifest:{manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"invalid-manifest:{manifest_path}"]
    if not isinstance(manifest, dict):
        return [f"invalid-manifest:{manifest_path}"]
    domain_status = manifest.get("domain_status", {})
    if not isinstance(domain_status, dict):
        return []
    unaccepted: list[str] = []
    for domain, raw_status in sorted(domain_status.items()):
        if not isinstance(raw_status, dict):
            unaccepted.append(str(domain))
            continue
        status = str(raw_status.get("status", "")).strip()
        accepted_by = str(raw_status.get("accepted_by", "")).strip()
        if status not in {"DONE", "DONE_WITH_CONCERNS"} or not accepted_by:
            unaccepted.append(str(domain))
    return unaccepted


def unclosed_subagent_sessions(root: Path | None, state: dict[str, object]) -> list[str]:
    plan_ref = resolve_state_reference(root, state.get("subagent_plan"))
    if not plan_ref:
        return []
    manifest_path = plan_ref / "manifest.json" if plan_ref.is_dir() else plan_ref
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(manifest, dict):
        return []
    domain_status = manifest.get("domain_status", {})
    if not isinstance(domain_status, dict):
        return []
    unclosed: list[str] = []
    for domain, raw_status in sorted(domain_status.items()):
        if not isinstance(raw_status, dict):
            continue
        status = str(raw_status.get("status", "")).strip()
        accepted_by = str(raw_status.get("accepted_by", "")).strip()
        if status not in {"DONE", "DONE_WITH_CONCERNS"} or not accepted_by:
            continue
        session_state = str(raw_status.get("session_state") or "").strip()
        session_reason = str(raw_status.get("session_reason") or "").strip()
        if session_state == "closed":
            continue
        if session_state in {"keep-open", "close-unavailable"} and session_reason:
            continue
        unclosed.append(str(domain))
    return unclosed


def sync_state(run_dir: Path) -> dict[str, object]:
    state = load_state(run_dir)
    events = read_events(run_dir)
    analysis = analyze_events(events)
    state["flags"] = analysis["flags"]
    state["event_count"] = analysis["event_count"]
    state["repair_attempts"] = analysis["repair_attempts"]
    if events:
        state["last_event"] = events[-1]
    write_state(run_dir, state)
    return state


def append_event(
    run_dir: Path,
    kind: str,
    summary: str = "",
    paths: list[str] | None = None,
    tool: str | None = None,
    metadata: dict[str, str] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    state = load_state(run_dir)
    events = read_events(run_dir)
    timestamp = now()
    sequence = len(events) + 1
    event: dict[str, object] = {
        "schema": SCHEMA,
        "id": f"{timestamp}-{sequence:04d}",
        "timestamp": timestamp,
        "sequence": sequence,
        "kind": kind,
        "summary": summary,
    }
    clean_paths = [path for path in (paths or []) if path]
    if clean_paths:
        event["path"] = clean_paths[0]
        if len(clean_paths) > 1:
            event["paths"] = clean_paths
    if tool:
        event["tool"] = tool
    if metadata:
        event["metadata"] = metadata
    with events_path(run_dir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    events.append(event)
    analysis = analyze_events(events)
    state["flags"] = analysis["flags"]
    state["event_count"] = analysis["event_count"]
    state["repair_attempts"] = analysis["repair_attempts"]
    state["last_event"] = event
    write_state(run_dir, state)
    return state, event


def validate_run(
    state: dict[str, object],
    events: list[dict[str, object]],
    strict: bool,
    max_repair_attempts: int,
    root: Path | None = None,
) -> dict[str, object]:
    analysis = analyze_events(events)
    flags = dict(analysis["flags"])
    errors: list[str] = []
    warnings: list[str] = []
    first_mutation = analysis["first_mutation"]
    first_inspect = analysis["first_inspect"]
    first_decide = analysis["first_decide"]
    last_verify_after_mutation = analysis["last_verify_after_mutation"]

    if first_mutation is not None:
        if first_inspect is None or first_inspect > first_mutation:
            errors.append("mutation occurred before inspect evidence")
        if first_decide is None or first_decide > first_mutation:
            errors.append("mutation occurred before decision evidence")
        if last_verify_after_mutation is None:
            errors.append("mutation has no later verification evidence")
        if strict and analysis["latest_verification_result_after_mutation"] == "failed":
            errors.append("latest verification after mutation failed")

    repair_attempts = int(analysis["repair_attempts"])
    if repair_attempts > max_repair_attempts:
        errors.append(f"repair attempts exceeded limit: {repair_attempts}>{max_repair_attempts}")

    if strict and str(state.get("status")) == "closed" and not flags["closure_passed"]:
        errors.append("closed loop is missing closure evidence")

    pending = analysis["pending_subagent_results"]
    if strict and pending:
        errors.append("subagent results are recorded but not accepted or rejected: " + ", ".join(pending))

    unaccepted_domains = unaccepted_subagent_domains(root, state) if strict else []
    if unaccepted_domains:
        errors.append("subagent plan has unaccepted domains: " + ", ".join(unaccepted_domains))

    unclosed_sessions = (
        unclosed_subagent_sessions(root, state)
        if strict and str(state.get("status")) == "closed"
        else []
    )
    flags["subagent_sessions_open"] = bool(unclosed_sessions)
    if unclosed_sessions:
        errors.append("subagent sessions are not closed or justified: " + ", ".join(unclosed_sessions))

    if not events:
        warnings.append("loop has no events")

    if workflow_errors:
        try:
            workflow_failures, workflow_warnings = workflow_errors(
                state.get("workflow"),
                events,
                state,
                strict,
            )
        except ValueError as exc:
            workflow_failures = [str(exc)]
            workflow_warnings = []
        errors.extend(workflow_failures)
        warnings.extend(workflow_warnings)

    return {
        "status": "fail" if errors else "ok",
        "state_status": state.get("status"),
        "run_id": state.get("run_id"),
        "event_count": analysis["event_count"],
        "flags": flags,
        "repair_attempts": repair_attempts,
        "pending_subagent_results": pending,
        "unaccepted_subagent_domains": unaccepted_domains,
        "unclosed_subagent_sessions": unclosed_sessions,
        "errors": errors,
        "warnings": warnings,
    }
'''


LOOP_START_SCRIPT = r'''#!/usr/bin/env python3
"""Start a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import SCHEMA, append_event, display_path, find_local_dir, loop_runs_dir, now, slugify, write_json
from workflow_core import DEFAULT_BUDGET, PATTERNS, normalize_workflow


def checklist(task: str, trace: str | None, subagent_plan: str | None) -> str:
    return f"""# Loop Governance Checklist

Task: {task}

- [ ] Inspect evidence recorded before mutation.
- [ ] Decision evidence recorded before mutation.
- [ ] Mutation evidence recorded, if work changes files or state.
- [ ] Verification evidence recorded after mutation.
- [ ] Repair attempts recorded and bounded.
- [ ] Subagent results accepted or rejected by the orchestrator.
- [ ] Completed subagent sessions closed or explicitly justified.
- [ ] Closure evidence recorded before closing.

Trace: {trace or "none"}
Subagent plan: {subagent_plan or "none"}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a loop-governance run.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--task", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--trace")
    parser.add_argument("--subagent-plan")
    parser.add_argument("--pattern", choices=sorted(PATTERNS), default=None)
    parser.add_argument("--recipe", action="append", default=[])
    parser.add_argument("--budget-max-iterations", type=int, default=None)
    parser.add_argument("--budget-max-subagent-waves", type=int, default=None)
    parser.add_argument("--routing-confidence", type=float, default=None)
    parser.add_argument("--routing-reason", default="")
    parser.add_argument("--routing-fallback", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    runs = loop_runs_dir(local_dir)
    runs.mkdir(parents=True, exist_ok=True)
    stamp = now().replace(":", "").replace("+0000", "Z").replace("+00:00", "Z")
    run_id = slugify(args.run_id or f"{stamp}-{args.task}")
    run_dir = runs / run_id
    if run_dir.exists():
        print(f"loop run already exists: {run_dir}", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True)

    trace = display_path(root, args.trace)
    subagent_plan = display_path(root, args.subagent_plan)
    raw_workflow = None
    if args.pattern or args.recipe:
        budget = dict(DEFAULT_BUDGET)
        if args.budget_max_iterations is not None:
            budget["max_iterations"] = args.budget_max_iterations
        if args.budget_max_subagent_waves is not None:
            budget["max_subagent_waves"] = args.budget_max_subagent_waves
        raw_workflow = {
            "primary": args.pattern,
            "recipe": args.recipe,
            "budget": budget,
            "routing": {
                "confidence": args.routing_confidence,
                "reason": args.routing_reason,
                "fallback": args.routing_fallback,
            },
        }
    try:
        workflow = normalize_workflow(raw_workflow)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    state = {
        "schema": SCHEMA,
        "run_id": run_id,
        "task": args.task,
        "status": "created",
        "created_at": now(),
        "updated_at": now(),
        "local_dir": display_path(root, str(local_dir)) or local_dir.name,
        "trace": trace,
        "subagent_plan": subagent_plan,
        "workflow": workflow,
        "event_count": 0,
        "repair_attempts": 0,
        "flags": {
            "inspected": False,
            "decided": False,
            "mutated": False,
            "verified": False,
            "closure_passed": False,
            "subagent_results_pending": False,
        },
    }
    write_json(run_dir / "state.json", state)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "checklist.md").write_text(checklist(args.task, trace, subagent_plan), encoding="utf-8")
    state, event = append_event(run_dir, "loop.started", f"Started loop: {args.task}")
    result = {"run_dir": str(run_dir), "event": event, "state": state}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


LOOP_EVENT_SCRIPT = r'''#!/usr/bin/env python3
"""Record an event in a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import append_event, find_local_dir, resolve_run_dir


def parse_metadata(values: list[str], domain: str | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if domain:
        metadata["domain"] = domain
    for value in values:
        if "=" not in value:
            raise ValueError(f"metadata must use key=value: {value}")
        key, item = value.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"metadata key must not be empty: {value}")
        metadata[key] = item.strip()
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a loop-governance event.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--run", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--tool")
    parser.add_argument("--domain")
    parser.add_argument("--metadata", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    run_dir = resolve_run_dir(root, local_dir, args.run)
    try:
        metadata = parse_metadata(args.metadata, args.domain)
        state, event = append_event(run_dir, args.kind, args.summary, args.path, args.tool, metadata)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = {"run_dir": str(run_dir), "event": event, "state": state}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(event["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


LOOP_TRANSITION_SCRIPT = r'''#!/usr/bin/env python3
"""Transition a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import STATES, append_event, find_local_dir, load_state, resolve_run_dir, write_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Transition a loop-governance run.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--run", required=True)
    parser.add_argument("--to", required=True, choices=sorted(STATES))
    parser.add_argument("--reason", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    run_dir = resolve_run_dir(root, local_dir, args.run)
    try:
        state = load_state(run_dir)
        previous = str(state.get("status"))
        state, event = append_event(
            run_dir,
            "loop.transition",
            args.reason or f"{previous} -> {args.to}",
            metadata={"from": previous, "to": args.to},
        )
        state["status"] = args.to
        write_state(run_dir, state)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = {"run_dir": str(run_dir), "event": event, "state": state}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(args.to)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


LOOP_CHECK_SCRIPT = r'''#!/usr/bin/env python3
"""Validate a native Fable Harness loop-governance run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_core import find_local_dir, read_events, resolve_run_dir, sync_state, validate_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a loop-governance run.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any"], default="auto")
    parser.add_argument("--run", required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--max-repair-attempts", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    run_dir = resolve_run_dir(root, local_dir, args.run)
    try:
        state = sync_state(run_dir)
        events = read_events(run_dir)
        report = validate_run(state, events, args.strict, args.max_repair_attempts, root)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report["run_dir"] = str(run_dir)
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"loop check {report['status']}: {run_dir}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def target_agents(agent: str, root: Path) -> list[str]:
    if agent == "both":
        return ["codex", "claude", "any"]
    if agent in AGENTS:
        return [agent]
    if (root / "CLAUDE.md").exists() and not (root / "AGENTS.md").exists() and not (root / ".codex").exists():
        return ["claude"]
    if (root / ".codex").exists():
        return ["codex"]
    if (root / ".agents").exists():
        return ["any"]
    return ["any"]


def upsert_block(path: Path, block: str) -> None:
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = f"# {path.stem} Instructions\n"

    pattern = re.compile(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        flags=re.DOTALL,
    )
    if pattern.search(text):
        updated = pattern.sub(block.strip(), text)
    else:
        updated = text.rstrip() + "\n\n" + block.strip() + "\n"
    path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def write_text(path: Path, content: str, overwrite: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not path.exists():
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


def ensure_index(path: Path, title: str) -> None:
    write_text(path, f"# {title}\n\n", overwrite=False)


def ensure_memory_files(local_dir: Path) -> None:
    memory = local_dir / "memory"
    (memory / "shards").mkdir(parents=True, exist_ok=True)
    (memory / "graph").mkdir(parents=True, exist_ok=True)
    (memory / "code-graph").mkdir(parents=True, exist_ok=True)
    (local_dir / "loop" / "runs").mkdir(parents=True, exist_ok=True)
    write_text(
        memory / "manifest.json",
        """{
  "document_count": 0,
  "embedding": "local-hash-v1",
  "shards": [],
  "storage": "sharded-jsonl",
  "vector_dims": 64,
  "version": 1
}""",
        overwrite=False,
    )
    write_text(memory / "promotion_log.jsonl", "", overwrite=False)
    write_text(memory / "touches.jsonl", "", overwrite=False)
    write_text(memory / "touch_index.json", '{"items": {}, "version": 1}', overwrite=False)


def superpowers_skill_path(root: Path) -> Path:
    return root / ".agents" / "skills" / "using-superpowers" / "SKILL.md"


def superpowers_manifest_path(root: Path) -> Path:
    return root / ".agents" / "vendor" / "superpowers" / "manifest.json"


def load_superpowers_manifest(root: Path) -> dict[str, object]:
    path = superpowers_manifest_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def infer_superpowers_version(value: str) -> str:
    match = re.search(r"v\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9_.-]+)?", value)
    if match:
        return match.group(0)
    return "local"


def directory_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(str(child.relative_to(path)).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_archive(path: Path, target: Path) -> Path:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            archive.extractall(target)
    else:
        raise ValueError(f"unsupported Superpowers archive: {path}")
    roots = [item for item in target.iterdir() if item.is_dir()]
    if len(roots) == 1 and (roots[0] / "skills").is_dir():
        return roots[0]
    if (target / "skills").is_dir():
        return target
    raise ValueError("Superpowers archive does not contain a skills directory")


def resolve_latest_superpowers_download(tmp: Path) -> tuple[Path, str, str, str]:
    request = urllib.request.Request(
        SUPERPOWERS_LATEST_URL,
        headers={"User-Agent": "fable-harness-installer"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        final_url = response.geturl()
    tag = infer_superpowers_version(final_url)
    if tag == "local":
        raise ValueError(f"could not resolve latest Superpowers tag from {final_url}")
    archive_url = SUPERPOWERS_REPO_ZIP_URL.format(tag=tag)
    archive_path = tmp / f"superpowers-{tag}.zip"
    request = urllib.request.Request(
        archive_url,
        headers={"User-Agent": "fable-harness-installer"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        archive_path.write_bytes(response.read())
    source_dir = extract_archive(archive_path, tmp / "extracted")
    return source_dir, tag, archive_url, file_sha256(archive_path)


def resolve_superpowers_source(source: str, tmp: Path) -> tuple[Path, str, str, str]:
    if source in {"latest", SUPERPOWERS_LATEST_URL}:
        return resolve_latest_superpowers_download(tmp)
    path = Path(source).expanduser()
    if path.exists():
        resolved = path.resolve()
        if resolved.is_dir():
            return resolved, infer_superpowers_version(resolved.name), str(resolved), directory_sha256(resolved)
        source_dir = extract_archive(resolved, tmp / "extracted")
        return source_dir, infer_superpowers_version(resolved.name), str(resolved), file_sha256(resolved)
    raise ValueError(f"Superpowers source not found: {source}")


def discover_superpowers_skills(source_dir: Path) -> list[Path]:
    skills_dir = source_dir / "skills"
    if not skills_dir.is_dir():
        raise ValueError("Superpowers source is missing skills/")
    skills = [
        path
        for path in sorted(skills_dir.iterdir())
        if path.is_dir() and (path / "SKILL.md").is_file()
    ]
    if not any(path.name == "using-superpowers" for path in skills):
        raise ValueError("Superpowers source is missing skills/using-superpowers/SKILL.md")
    return skills


def prompt_yes_no(question: str, default: bool = False) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    try:
        answer = input(question + suffix).strip().lower()
    except EOFError:
        print(f"{question} {'yes' if default else 'no'} (no interactive input)")
        return default
    if not answer:
        return default
    return answer in {"y", "yes", "s", "sim"}


def install_superpowers_from_source(root: Path, source: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp_name:
        source_dir, version, resolved_source, source_hash = resolve_superpowers_source(source, Path(tmp_name))
        skills = discover_superpowers_skills(source_dir)
        target_skills = root / ".agents" / "skills"
        target_vendor = root / ".agents" / "vendor" / "superpowers"
        target_skills.mkdir(parents=True, exist_ok=True)
        target_vendor.mkdir(parents=True, exist_ok=True)
        installed: list[str] = []
        for skill in skills:
            target = target_skills / skill.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill, target)
            installed.append(skill.name)
        license_path = source_dir / "LICENSE"
        if license_path.is_file():
            shutil.copy2(license_path, target_vendor / "LICENSE")
        manifest = {
            "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "resolved_version": version,
            "sha256": source_hash,
            "skills": sorted(installed),
            "source": resolved_source,
        }
        (target_vendor / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest


def should_prompt_for_superpowers(source: str) -> bool:
    return source != "latest" or sys.stdin.isatty()


def maybe_install_superpowers(
    root: Path,
    source: str,
    with_superpowers: bool,
    without_superpowers: bool,
    upgrade_superpowers: bool,
) -> list[Path]:
    if without_superpowers:
        print("Skipped Superpowers companion install by request.")
        return []

    installed = superpowers_skill_path(root).is_file()
    manifest = load_superpowers_manifest(root)
    installed_version = str(manifest.get("resolved_version", "") or "")

    if installed and source == "latest" and not (with_superpowers or upgrade_superpowers) and not sys.stdin.isatty():
        print("Superpowers is installed; skipped update check in non-interactive mode.")
        return []

    latest_version = ""
    if installed:
        try:
            with tempfile.TemporaryDirectory() as tmp_name:
                _source_dir, latest_version, _resolved_source, _source_hash = resolve_superpowers_source(source, Path(tmp_name))
        except (OSError, ValueError) as exc:
            print(f"Warning: could not check Superpowers version: {exc}", file=sys.stderr)
            return []
        if installed_version == latest_version:
            print(f"Superpowers already up to date ({installed_version}).")
            return []
        if not (with_superpowers or upgrade_superpowers):
            if not should_prompt_for_superpowers(source):
                print(f"Superpowers is installed ({installed_version or 'unknown'}); latest is {latest_version}. Skipped update in non-interactive mode.")
                return []
            if not prompt_yes_no(f"Superpowers {installed_version or 'unknown'} is installed; update to {latest_version}?"):
                print("Kept existing Superpowers install.")
                return []
    else:
        if not with_superpowers:
            if not should_prompt_for_superpowers(source):
                print("Superpowers is not installed. Re-run with --with-superpowers to install it.")
                return []
            if not prompt_yes_no("Superpowers is not installed. Install it with Fable Harness?"):
                print("Skipped Superpowers companion install.")
                return []

    try:
        manifest = install_superpowers_from_source(root, source)
    except (OSError, ValueError) as exc:
        print(f"Warning: could not install Superpowers companion: {exc}", file=sys.stderr)
        return []
    print(f"Installed Superpowers companion {manifest['resolved_version']} with {len(manifest['skills'])} skills.")
    return [
        root / ".agents" / "skills" / "using-superpowers" / "SKILL.md",
        superpowers_manifest_path(root),
    ]


def install_for(root: Path, agent: str) -> list[Path]:
    cfg = AGENTS[agent]
    local_dir = root / cfg["local_dir"]
    created_or_updated: list[Path] = []

    templates = {
        "decision-trace.md": DECISION_TRACE_TEMPLATE,
        "semantic-note.md": SEMANTIC_NOTE_TEMPLATE,
        "subagent-brief.md": SUBAGENT_BRIEF_TEMPLATE,
        "memory-closure.md": MEMORY_CLOSURE_TEMPLATE,
        "workflow-profile.md": WORKFLOW_PROFILE_TEMPLATE,
    }
    for name, content in templates.items():
        path = local_dir / "templates" / name
        write_text(path, content)
        created_or_updated.append(path)

    scripts = {
        "new-trace.py": NEW_TRACE_SCRIPT,
        "check-closure.py": CHECK_CLOSURE_SCRIPT,
        "memory_policy.py": MEMORY_POLICY_SCRIPT,
        "workflow_core.py": WORKFLOW_CORE_SCRIPT,
        "memory_core.py": MEMORY_CORE_SCRIPT,
        "new-note.py": NEW_NOTE_SCRIPT,
        "promote-trace.py": PROMOTE_TRACE_SCRIPT,
        "memory-search.py": MEMORY_SEARCH_SCRIPT,
        "rebuild-memory.py": REBUILD_MEMORY_SCRIPT,
        "rag-eval.py": RAG_EVAL_SCRIPT,
        "rag-pipeline.py": RAG_PIPELINE_SCRIPT,
        "source-arbitrate.py": SOURCE_ARBITRATE_SCRIPT,
        "graph-query.py": GRAPH_QUERY_SCRIPT,
        "graph-check.py": GRAPH_CHECK_SCRIPT,
        "code_graph_core.py": CODE_GRAPH_CORE_SCRIPT,
        "code-graph-build.py": CODE_GRAPH_BUILD_SCRIPT,
        "code-graph-query.py": CODE_GRAPH_QUERY_SCRIPT,
        "code-graph-check.py": CODE_GRAPH_CHECK_SCRIPT,
        "release-notice.py": RELEASE_NOTICE_SCRIPT.replace("__FABLE_HARNESS_VERSION__", FABLE_HARNESS_VERSION),
        "subagent-plan.py": SUBAGENT_PLAN_SCRIPT,
        "subagent-result.py": SUBAGENT_RESULT_SCRIPT,
        "subagent-sweep.py": SUBAGENT_SWEEP_SCRIPT,
        "selective-revert.py": SELECTIVE_REVERT_SCRIPT,
        "memory-maintenance.py": MEMORY_MAINTENANCE_SCRIPT,
        "memory-touch.py": MEMORY_TOUCH_SCRIPT,
        "memory-dream.py": MEMORY_DREAM_SCRIPT,
        "loop_core.py": LOOP_CORE_SCRIPT,
        "loop-start.py": LOOP_START_SCRIPT,
        "loop-event.py": LOOP_EVENT_SCRIPT,
        "loop-transition.py": LOOP_TRANSITION_SCRIPT,
        "loop-check.py": LOOP_CHECK_SCRIPT,
    }
    for name, content in scripts.items():
        path = local_dir / "scripts" / name
        write_text(path, content)
        created_or_updated.append(path)

    ensure_index(local_dir / "notes" / "_index.md", "Semantic Notes Index")
    ensure_index(local_dir / "decision-traces" / "_index.md", "Decision Trace Index")
    ensure_memory_files(local_dir)

    instruction_path = root / cfg["instruction_file"]
    upsert_block(
        instruction_path,
        harness_block(cfg["local_dir"], cfg["agent_name"]),
    )
    created_or_updated.append(instruction_path)
    return created_or_updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or update the Fable Harness.")
    parser.add_argument("workspace", help="Project workspace root.")
    parser.add_argument("--agent", choices=["auto", "codex", "claude", "any", "both"], default="auto")
    parser.add_argument("--with-superpowers", action="store_true", help="Install Superpowers companion skills when absent.")
    parser.add_argument("--without-superpowers", action="store_true", help="Do not install or update Superpowers companion skills.")
    parser.add_argument("--upgrade-superpowers", action="store_true", help="Update Superpowers companion skills when an older version is installed.")
    parser.add_argument("--superpowers-source", default="latest", help="Superpowers source: latest, release URL, local checkout, or zip archive.")
    args = parser.parse_args()

    if args.with_superpowers and args.without_superpowers:
        parser.error("--with-superpowers and --without-superpowers cannot be used together")
    if args.upgrade_superpowers and args.without_superpowers:
        parser.error("--upgrade-superpowers and --without-superpowers cannot be used together")

    root = Path(args.workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    agents = target_agents(args.agent, root)

    changed: list[Path] = []
    for agent in agents:
        changed.extend(install_for(root, agent))
    changed.extend(
        maybe_install_superpowers(
            root,
            args.superpowers_source,
            args.with_superpowers,
            args.without_superpowers,
            args.upgrade_superpowers,
        )
    )

    print(f"Installed Fable Harness for {', '.join(agents)} in {root}")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
