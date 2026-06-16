---
name: fable-harness
description: Use when installing or updating a project-local Fable Harness for Codex, Claude Code, or compatible agent workflows; when a workspace needs AGENTS.md or CLAUDE.md boot instructions, .codex/.claude/.agents templates, decision traces, semantic notes, subagent briefs, memory closure checks, or protected TDD audit rails.
---

# Fable Harness

## Overview

Install a lightweight project-local harness that turns the Fable decision-loop playbook into repeatable files, scripts, and agent boot instructions.

The harness is instructional plus mechanical: root instructions load the operating rules, templates standardize audit artifacts, and scripts create traces and check closure.

## Quick Start

When a user asks to install or update Fable Harness, run the installer from this skill. Do not stop at explaining the command.

```powershell
python "<skill-dir>\scripts\install_fable_harness.py" "<project-root>" --agent codex
```

Use the directory containing this `SKILL.md` as `<skill-dir>`. Use the current workspace as `<project-root>` unless the user names another target. If the user does not choose an agent mode, use `auto`.

Agent options:

| Option | Creates or updates |
|---|---|
| `codex` | `AGENTS.md` and `.codex/` |
| `claude` | `CLAUDE.md` and `.claude/` |
| `any` | `AGENTS.md` and `.agents/` |
| `both` | both Codex, Claude and any surfaces |
| `auto` | Claude if only `CLAUDE.md` exists, Codex if only `.codex/` exists, otherwise any |

## What Gets Installed

The installer preserves existing root instructions and updates only the marked `fable-harness` block.

```text
<.codex or .claude or .agents>/
  templates/
    decision-trace.md
    semantic-note.md
    subagent-brief.md
    memory-closure.md
  scripts/
    new-trace.py
    check-closure.py
    subagent-plan.py
    new-note.py
    promote-trace.py
    memory-search.py
    rebuild-memory.py
    subagent-result.py
    memory-maintenance.py
  notes/
    _index.md
  decision-traces/
    _index.md
  memory/
    manifest.json
    promotion_log.jsonl
    shards/*.jsonl
    graph/
      nodes.jsonl
      edges.jsonl
```

## Operating Rules It Wires In

- Read project instructions first, then compact semantic notes, then only selected traces when audit is needed, then real project files before edits.
- Use the loop: Orient, Inspect, Decide, Act, Verify, Report.
- For non-trivial or mutating work, create or continue a decision trace.
- Keep `.codex/notes/` or `.claude/notes/` or `.agents/notes/` compact and semantic; use traces as proof of the decision path.
- Store notes as `.codex/notes/<category>/<optional-area>/<topic>.md`, using `.claude` or `.agents` for those install targets.
- Promote durable trace evidence into notes with `promote-trace.py` instead of making every future agent reread raw traces.
- Keep retrieval state generated under `memory/`: sharded local embeddings, a promotion log, and a JSONL knowledge graph.
- Use `memory-search.py` for semantic recall before broad manual reading, and `rebuild-memory.py` after manual note or trace edits.
- The main orchestrating agent owns memory coherence.
- Subagents gather evidence and suggest memory updates; they do not silently promote durable memory.
- Break complex or multidisciplinary work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Use `subagent-plan.py` to generate dispatchable briefs and a manifest before broad execution when the task has independent domains.
- Dispatch subagents from those briefs with the available platform tool; if no subagent tool exists, execute the briefs sequentially and record the fallback.
- Use `subagent-result.py` to record each subagent result in the dispatch package and active trace before accepting it.
- Use `memory-maintenance.py` after large tasks or periodically to report oversized notes, stale notes, broken sources, and archive-ready promoted traces. It is report-only and does not delete source files.
- Protect TDD tests created before implementation. Do not weaken, skip, rename, delete, or rewrite them just to make the loop pass.
- Update cadence: trace during the work, semantic notes after verified evidence, indexes at closure.
- Closure checks fail when a trace records a durable decision that has not been promoted into compact semantic memory.

## After Installing

Create a trace when beginning substantial work:

```powershell
python ".codex\scripts\new-trace.py" --root "." --title "Short Task Title"
```

Run closure checks before reporting completion:

```powershell
python ".codex\scripts\check-closure.py" --root "." --trace ".codex\decision-traces\<trace>.md"
```

Use `.claude\scripts\...` instead for Claude installs.
Use `.agents\scripts\...` instead for any installs.

Create a semantic note directly:

```powershell
python ".codex\scripts\new-note.py" --root "." --category decisions --area architecture --topic memory-ownership
```

Promote a trace into semantic memory:

```powershell
python ".codex\scripts\promote-trace.py" --root "." --trace ".codex\decision-traces\<trace>.md" --category decisions --area workflow --topic memory-ownership
```

Search local memory:

```powershell
python ".codex\scripts\memory-search.py" --root "." --query "protected TDD tests"
```

Create subagent briefs:

```powershell
python ".codex\scripts\subagent-plan.py" --root "." --task "Harden harness" --domain "closure gate" --domain "subagent invocation" --trace ".codex\decision-traces\<trace>.md" --verification "python scripts/test_install_fable_harness.py"
```

Record a subagent result:

```powershell
python ".codex\scripts\subagent-result.py" --root "." --plan-dir ".codex\subagents\<plan>" --domain "closure gate" --status DONE_WITH_CONCERNS --summary "Found exact-promotion risk" --accepted-by orchestrator
```

Run memory maintenance:

```powershell
python ".codex\scripts\memory-maintenance.py" --root "." --json
```

Rebuild generated indexes:

```powershell
python ".codex\scripts\rebuild-memory.py" --root "."
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Reading every trace in a new context | Read notes first; open traces only for audit or continuation. |
| Letting subagents update memory silently | Require orchestrator review and acceptance. |
| Asking one agent to do a complex multidisciplinary task alone | Generate briefs with `subagent-plan.py` and dispatch focused subagents. |
| Losing subagent results in chat history | Record them with `subagent-result.py` before closure. |
| Treating traces as prose summaries | Record evidence: files, commands, decisions, outcomes, risks. |
| Leaving durable trace decisions only in raw traces | Promote them into compact notes before closure. |
| Letting memory grow until retrieval slows down | Run `memory-maintenance.py`; compact notes, repair sources, and archive promoted traces manually from its report. |
| Editing protected TDD tests to pass | Stop and explain; only replace a wrong test with an equally strict corrected test. |
| Reporting done without closure | Run the closure checklist or state the blocker. |
