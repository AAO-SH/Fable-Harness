---
name: fable-harness
description: Use when installing or updating a project-local Fable Harness for Codex, Claude Code, or compatible agent workflows; when a workspace needs AGENTS.md or CLAUDE.md boot instructions, .codex/.claude/.agents templates, decision traces, semantic notes, subagent briefs, memory closure checks, or protected TDD audit rails.
---

# Fable Harness

## Overview

Install a lightweight project-local harness that turns the Fable decision-loop playbook into repeatable files, scripts, and agent boot instructions.

The harness is instructional plus mechanical: root instructions load the operating rules, templates standardize audit artifacts, and scripts create traces and check closure.

## Quick Start

Run the installer from this skill:

```powershell
python "<skill-dir>\scripts\install_fable_harness.py" "<project-root>" --agent codex
```

Agent options:

| Option | Creates or updates |
|---|---|
| `codex` | `AGENTS.md` and `.codex/` |
| `claude` | `CLAUDE.md` and `.claude/` |
| `any` | `AGENTS.md`, `README.md` and `.agents/` |
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
  notes/
    _index.md
  decision-traces/
    _index.md
```

## Operating Rules It Wires In

- Read project instructions first, then compact semantic notes, then only selected traces when audit is needed, then real project files before edits.
- Use the loop: Orient, Inspect, Decide, Act, Verify, Report.
- For non-trivial or mutating work, create or continue a decision trace.
- Keep `.codex/notes/` or `.claude/notes/` or `.agents/notes/` compact and semantic; use traces as proof of the decision path.
- The main orchestrating agent owns memory coherence.
- Subagents gather evidence and suggest memory updates; they do not silently promote durable memory.
- Break complex or multidisciplinary work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Protect TDD tests created before implementation. Do not weaken, skip, rename, delete, or rewrite them just to make the loop pass.
- Update cadence: trace during the work, semantic notes after verified evidence, indexes at closure.

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

## Common Mistakes

| Mistake | Fix |
|---|---|
| Reading every trace in a new context | Read notes first; open traces only for audit or continuation. |
| Letting subagents update memory silently | Require orchestrator review and acceptance. |
| Treating traces as prose summaries | Record evidence: files, commands, decisions, outcomes, risks. |
| Editing protected TDD tests to pass | Stop and explain; only replace a wrong test with an equally strict corrected test. |
| Reporting done without closure | Run the closure checklist or state the blocker. |
