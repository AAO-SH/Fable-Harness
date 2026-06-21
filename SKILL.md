---
name: fable-harness
description: Use when installing or updating a project-local Fable Harness for Codex, Claude Code, or compatible agent workflows; when a workspace needs AGENTS.md or CLAUDE.md boot instructions, .codex/.claude/.agents templates, decision traces, semantic notes, native loop governance, loop state, event logs, checklist evidence, subagent briefs, memory closure checks, or protected TDD audit rails.
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

During an interactive install, the installer checks for Superpowers at `<project-root>/.agents/skills/using-superpowers/SKILL.md`. If Superpowers is missing, it asks whether to install it from the latest official release. If Superpowers is installed but older than the selected source, it asks whether to update. If the user declines, Fable Harness remains standalone. Do not add Superpowers-specific usage instructions to generated `AGENTS.md` or `CLAUDE.md`; Superpowers is discovered as installed skills.

For scripted runs, use explicit flags:

```powershell
python "<skill-dir>\scripts\install_fable_harness.py" "<project-root>" --agent codex --with-superpowers
python "<skill-dir>\scripts\install_fable_harness.py" "<project-root>" --agent codex --without-superpowers
python "<skill-dir>\scripts\install_fable_harness.py" "<project-root>" --agent codex --upgrade-superpowers
```

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
    workflow-profile.md
  scripts/
    new-trace.py
    check-closure.py
    workflow_core.py
    subagent-plan.py
    new-note.py
    promote-trace.py
    memory-search.py
    rebuild-memory.py
    rag-eval.py
    rag-pipeline.py
    source-arbitrate.py
    graph-query.py
    graph-check.py
    code_graph_core.py
    code-graph-build.py
    code-graph-query.py
    code-graph-check.py
    release-notice.py
    subagent-result.py
    subagent-sweep.py
    selective-revert.py
    memory-maintenance.py
    memory-touch.py
    memory-dream.py
    loop_core.py
    loop-start.py
    loop-event.py
    loop-transition.py
    loop-check.py
  notes/
    _index.md
  decision-traces/
    _index.md
  loop/
    runs/<run-id>/
      state.json
      events.jsonl
      checklist.md
  memory/
    manifest.json
    promotion_log.jsonl
    touches.jsonl
    touch_index.json
    shards/*.jsonl
    cache/documents.json
    retrieval/*.md
    graph/
      nodes.jsonl
      edges.jsonl
    code-graph/
      nodes.jsonl
      edges.jsonl
```

## Operating Rules It Wires In

- Read project instructions first, then compact semantic notes, then only selected traces when audit is needed, then real project files before edits.
- At boot, run `release-notice.py check` when available. It checks at most once every 24 hours and only prints when a newer GitHub release exists; it never downloads or applies updates.
- When the user asks to save, memorize, remember, store, register, persist, or update project context, the installed project-local harness surface is mandatory. Use `.codex/`, `.claude/`, or `.agents/` first; global/model memory, user-level agent storage, chat summaries, or external notes may only be additional mirrors.
- For local durable memory work, use the installed scripts such as `new-note.py`, `promote-trace.py`, `rebuild-memory.py`, and `memory-touch.py`; prefer local harness scripts over equivalent global or model-native memory actions whenever they exist.
- Use the Recall Ladder for non-trivial recall: `memory-search.py`, `rag-pipeline.py` for memory-heavy cited source inspection, lightweight `source-arbitrate.py` before RAG-informed code/doc edits, `notes/_index.md`, compact active notes, `memory-touch.py`, `graph-query.py --q`, dormant search, traces only when needed, project docs/source files, then closure maintenance.
- Do not create a plan from an empty evidence base. If local memory, notes, traces, docs, and source files do not provide a verifiable structured source, research the web before planning.
- Use primary or official web sources when available, record links or citations in the trace, and treat web results as planning evidence only when they are relevant, credible, and specific.
- If neither project sources nor strong web references provide enough planning ground for a completely new task, interview the user about intent, constraints, success criteria, examples, non-goals, and verification before creating a plan.
- Use Programming Recall for non-trivial programming work: semantic recall explains why, Code Graph maps where and what may break, and source files remain the final operational authority.
- Combine semantic memory and Code Graph before broad source-code edits: use memory/RAG/semantic graph for prior decisions, architecture intent, constraints, and verification history; use Code Graph for files, symbols, dependencies, callers, tests, and static impact.
- Treat Code Graph output as orientation evidence only. Read the real source files before editing and let source files win when graph output disagrees.
- Use the loop: Orient, Inspect, Decide, Act, Verify, Report.
- Treat Six Workflow Patterns as composable workflow recipes above the loop: `classify-and-act`, `fan-out-and-synthesize`, `adversarial-verification`, `generate-and-filter`, `tournament`, and `loop-until-done`.
- Use `loop-start.py --pattern` and repeated `--recipe` flags to record workflow-aware runs; pattern-specific strict checks apply only to workflow-aware runs, while legacy loops remain compatible.
- During Orient/Classify, automatically evaluate whether the task has independent domains that should be delegated to subagents. Treat the installed Fable Harness block as standing project-level user authorization to invoke available subagent or parallel-agent tools automatically when the independence check passes. Do not wait for the user to say `Dispatching Parallel Agents` or any other trigger phrase, and do not ask for per-prompt permission before dispatching subagents when these conditions are met.
- If the platform exposes a subagent or parallel-agent tool and the independence check passes, invoke it.
- If the platform exposes no subagent tool, or a higher-priority runtime policy forbids delegation despite this standing project-level user authorization, create the dispatch briefs, execute them sequentially, and record that platform limitation in the trace.
- Parallelize independent tasks or independent loop runs, not dependent steps inside one loop; a single loop run is sequential by default.
- Default to subagent dispatch for complex or multidisciplinary work when at least two domains can progress independently.
- Sequential loop order applies inside one domain or dependency chain; it is not a reason to collapse independent domains back into the orchestrator.
- The independence check is a dispatch test, not a prohibition. If domains have separate inputs, outputs, and responsibility boundaries, create a simultaneous subagent wave.
- Synchronize each subagent wave before integration, verification, memory promotion, or closure.
- Do not run `loop-event.py`, `loop-transition.py`, or `loop-check.py` concurrently for the same run.
- Do not run `rebuild-memory.py` concurrently with `memory-maintenance.py`, `graph-check.py`, or `memory-dream.py plan`; generated state is one-writer by default.
- If parallel work creates out-of-order evidence or a race, stop, record a repair event, and continue sequentially until the loop is healthy again.
- For non-trivial or mutating work, create or continue a decision trace.
- Use `release-notice.py check` as a notification-only release check. The user decides whether to manually download or update from GitHub.
- Keep `.codex/notes/` or `.claude/notes/` or `.agents/notes/` compact and semantic; use traces as proof of the decision path.
- Store notes as `.codex/notes/<category>/<optional-area>/<topic>.md`, using `.claude` or `.agents` for those install targets.
- Promote durable trace evidence into notes with `promote-trace.py` instead of making every future agent reread raw traces.
- Keep retrieval state generated under `memory/`: sharded local embeddings, a promotion log, and a JSONL knowledge graph.
- Use `memory-search.py` for semantic recall before broad manual reading. It returns hybrid lexical/vector/graph scores, rerank details, chunk snippets, and citations when available.
- Use `rag-pipeline.py` for memory-heavy answers or plans so the agent follows `retrieve -> inspect sources -> answer/plan with citations` before relying on memory.
- Use `source-arbitrate.py` when RAG informs work that may change project code or docs: run a lightweight source-arbitration check against real project files before planning or editing; if material conflict is found, escalate to a full Evidence Dispute and ask the user before replacing project facts with RAG-derived facts.
- Use `rag-eval.py` with a local JSON/JSONL eval set to report precision@k, recall@k, hit-rate@k, and MRR when tuning retrieval behavior.
- Use `rebuild-memory.py` after manual note or trace edits.
- Use `loop-start.py` for native loop governance when work needs auditable progress; record events/transitions with `loop-event.py` and `loop-transition.py`, and run `loop-check.py --strict` before reporting completion.
- Loop governance writes machine-readable `state.json`, `events.jsonl`, and `checklist.md` under `loop/runs/<run-id>/`; it references traces, notes, verification, and subagent plans instead of replacing them.
- Use `graph-query.py` to inspect generated semantic graph entities/relations, including `--q` text lookup, and `graph-check.py --strict` to validate graph integrity after graph-sensitive memory changes.
- Use `code-graph-build.py` and `code-graph-query.py` before broad source-code edits when symbol, import, call, test, or static impact orientation would reduce risk.
- Treat code graph output as orientation evidence only; read the source files before editing, and let source files win if the graph disagrees.
- Use `memory-dream.py maintain --context "<current task>" --auto-safe --agent-review` after memory-heavy work; it applies context-cold safe mechanical actions and writes `agent-review.md` for semantic decisions.
- Use `memory-dream.py plan` and `apply --apply` only when a manual two-step review workflow is needed.
- Use `memory-dream.py search-dormant` before declaring older context unavailable, and `memory-dream.py reactivate --apply` to restore compact active notes from dormant evidence.
- Use `selective-revert.py` when the user asks to revert specific agent changes; create a plan first, inspect it, and apply only with explicit user intent and `--apply`.
- The main orchestrating agent owns memory coherence.
- Subagents gather evidence and suggest memory updates; they do not silently promote durable memory.
- Break complex or multidisciplinary work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Use `subagent-plan.py` to generate dispatchable briefs and a manifest before broad execution when the task has independent domains; use `--parallel` and `--depends-on dependent:dependency` to create simultaneous dispatch waves.
- Dispatch all briefs in the same generated wave with the available platform tool; if no subagent tool exists, execute those briefs sequentially and record the fallback.
- Use `subagent-result.py` to record each subagent result in the dispatch package and active trace before accepting it.
- Use `subagent-sweep.py --close-completed` near final closure when a subagent plan was used. Close completed sessions unless a domain is explicitly kept open or closure is unavailable with a reason.
- Use `memory-maintenance.py` after large tasks or periodically to report oversized notes, stale notes, broken sources, and archive-ready promoted traces. It is report-only and does not delete source files.
- Use `memory-maintenance.py --strict` before closing memory-heavy work. Strict mode exits non-zero on high-severity hygiene failures such as umbrella traces, invalid note schema, duplicate active canonical notes, and generic trace titles.
- Use `memory-touch.py` when a note, trace, or dormant item is loaded for task context. It records recency and use count in generated memory state without editing the source file.
- Protect TDD tests created before implementation. Do not weaken, skip, rename, delete, or rewrite them just to make the loop pass.
- Update cadence: trace during the work, semantic notes after verified evidence, indexes at closure.
- Closure checks fail when a trace records a durable decision that has not been promoted into compact semantic memory.
- Closure checks also fail when notes do not follow the canonical frontmatter contract or when two active canonical notes claim the same scope.
- Keep one trace per coherent task or task block. `session-index` and `migration-trace` are the only accepted umbrella trace roles.
- Semantic notes must declare `memory_schema`, `type`, `status`, `scope`, `canonical`, `thesis`, `atomic`, `tags`, `properties`, `moc`, `links`, `sources`, `supersedes`, and `last_verified`. New permanent notes use `memory_schema: atomic-v1`: one idea, title as thesis, explicit connections, unique scope, and queryable metadata. Use `canonical-decision` for the active memory of record, `trace-summary` for compressed historical trace context, `operational-note` for procedural facts, and `migration-note` for memory restructuring work.

## After Installing

Create a trace when beginning substantial work:

```powershell
python ".codex\scripts\release-notice.py" check --root "."
```

The release notice check is throttled to once every 24 hours and only prints a warning when a newer GitHub release is available.

```powershell
python ".codex\scripts\new-trace.py" --root "." --title "Short Task Title"
```

Start a native loop-governance run:

```powershell
python ".codex\scripts\loop-start.py" --root "." --task "Short Task Title" --trace ".codex\decision-traces\<trace>.md" --json
python ".codex\scripts\loop-event.py" --root "." --run ".codex\loop\runs\<run>" --kind file.read --summary "Read the source file" --path "src/example.py"
python ".codex\scripts\loop-event.py" --root "." --run ".codex\loop\runs\<run>" --kind decision.recorded --summary "Use the smallest compatible change"
python ".codex\scripts\loop-transition.py" --root "." --run ".codex\loop\runs\<run>" --to acting --reason "Decision recorded"
python ".codex\scripts\loop-check.py" --root "." --run ".codex\loop\runs\<run>" --strict --json
```

Start a workflow-aware loop with a composable recipe:

```powershell
python ".codex\scripts\loop-start.py" --root "." --task "Harden workflow" --pattern loop-until-done --recipe classify-and-act --recipe fan-out-and-synthesize --recipe adversarial-verification --budget-max-iterations 3 --json
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

Run source arbitration before RAG-informed code/doc edits:

```powershell
python ".codex\scripts\source-arbitrate.py" --root "." --query "protected TDD tests" --source "docs\relevant.md" --json
```

Recall from fast to deep:

1. `memory-search.py` with a concise task query.
2. `rag-pipeline.py` for memory-heavy cited source inspection.
3. `source-arbitrate.py` before RAG-informed code/doc edits.
4. `notes/_index.md` and compact active notes.
5. `memory-touch.py` for every loaded note, trace, or dormant item.
6. `graph-query.py --q` for relationships, sources, and prior verification paths.
7. `memory-dream.py search-dormant` before saying old context is unavailable.
8. Decision traces only for audit, continuation, disputed decisions, or missing evidence.
9. Project docs and source files before edits.
10. Closure maintenance: promote durable decisions, rebuild memory, strict maintenance, and dream planning when memory-heavy.

Run agent-reviewed Memory Dreaming maintenance:

```powershell
python ".codex\scripts\memory-touch.py" --root "." --path ".codex\notes\decisions\memory\example.md" --reason "loaded for task context" --json
python ".codex\scripts\memory-dream.py" maintain --root "." --context "current task" --auto-safe --agent-review --json
```

Create a manual Memory Dreaming run when you need an explicit two-step review:

```powershell
python ".codex\scripts\memory-touch.py" --root "." --path ".codex\notes\decisions\memory\example.md" --reason "loaded for task context" --json
python ".codex\scripts\memory-dream.py" plan --root "." --json
python ".codex\scripts\memory-dream.py" apply --root "." --run ".codex\memory\dreams\runs\<run>" --apply
```

`memory-dream.py maintain` can be run by a background memory curator subagent after memory-heavy work. The script applies only context-cold safe mechanical actions; semantic compaction suggestions go to `agent-review.md` for the orchestrator, not the user by default.
Inspect the run's `agent-review.md`, `report.md`, and `diff.json` before changing semantic notes.

Search dormant memory and reactivate compact active notes:

```powershell
python ".codex\scripts\memory-dream.py" search-dormant --root "." --query "old release decision" --json
python ".codex\scripts\memory-dream.py" reactivate --root "." --query "old release decision" --category decisions --area memory --topic old-release-decision --apply
```

Inspect and validate the generated knowledge graph:

```powershell
python ".codex\scripts\graph-query.py" --root "." --relation promotes
python ".codex\scripts\graph-query.py" --root "." --q "semantic retrieval" --json
python ".codex\scripts\graph-check.py" --root "." --strict --json
```

Build, query, and validate the generated code graph:

```powershell
python ".codex\scripts\code-graph-build.py" --root "." --json
python ".codex\scripts\code-graph-query.py" --root "." --symbol "install_harness" --json
python ".codex\scripts\code-graph-check.py" --root "." --json
```

Create subagent briefs:

```powershell
python ".codex\scripts\subagent-plan.py" --root "." --task "Harden harness" --domain "closure gate" --domain "subagent invocation" --trace ".codex\decision-traces\<trace>.md" --verification "python scripts/test_install_fable_harness.py"
python ".codex\scripts\subagent-plan.py" --root "." --task "Harden harness" --domain "graph" --domain "docs" --parallel --depends-on "docs:graph"
```

Record a subagent result:

```powershell
python ".codex\scripts\subagent-result.py" --root "." --plan-dir ".codex\subagents\<plan>" --domain "closure gate" --status DONE_WITH_CONCERNS --summary "Found exact-promotion risk" --accepted-by orchestrator
```

Sweep completed subagent sessions before final closure:

```powershell
python ".codex\scripts\subagent-sweep.py" --root "." --plan-dir ".codex\subagents\<plan>" --close-completed
```

Run memory maintenance:

```powershell
python ".codex\scripts\memory-maintenance.py" --root "." --json
```

Run strict hygiene before closing memory-heavy work:

```powershell
python ".codex\scripts\memory-maintenance.py" --root "." --strict --json
```

Create a selective rollback plan for a Git-tracked file:

```powershell
python ".codex\scripts\selective-revert.py" plan --root "." --path "src/example.py"
```

Create a native checkpoint before risky work, then plan against it later:

```powershell
python ".codex\scripts\selective-revert.py" checkpoint --root "." --label "before-risky-change" --path "src/example.py"
python ".codex\scripts\selective-revert.py" plan --root "." --checkpoint ".codex\rollback\checkpoints\<checkpoint>\manifest.json" --path "src/example.py"
```

Apply a reviewed rollback plan only when the user explicitly wants it:

```powershell
python ".codex\scripts\selective-revert.py" apply --root "." --plan ".codex\rollback\plans\<plan>\manifest.json" --apply
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
| Treating sequential loop order as a ban on subagents | Serialize only dependent steps inside one domain; dispatch independent domains in parallel waves. |
| Losing subagent results in chat history | Record them with `subagent-result.py` before closure. |
| Leaving subagent sessions open after all work is integrated | Run `subagent-sweep.py --close-completed`, or record `keep-open` / `close-unavailable` with a reason. |
| Running a complex task as hidden process state | Start a native loop with `loop-start.py`, record events, and close with `loop-check.py --strict`. |
| Treating traces as prose summaries | Record evidence: files, commands, decisions, outcomes, risks. |
| Leaving durable trace decisions only in raw traces | Promote them into compact notes before closure. |
| Letting memory grow until retrieval slows down | Run `memory-maintenance.py`; compact notes, repair sources, and archive promoted traces manually from its report. |
| Treating Memory Dreaming as a user chore | Run `memory-dream.py maintain --auto-safe --agent-review`; the script applies safe mechanical actions and the agent reviews semantic suggestions. |
| Declaring old context unavailable without checking dormant memory | Run `memory-dream.py search-dormant` first, then reactivate only a compact note if needed. |
| Using one broad trace for unrelated work | Split the work into one trace per coherent task; use `session-index` only as an index. |
| Creating duplicate active notes for the same decision | Keep one active `canonical-decision` per `scope`; mark older notes `superseded` or convert them to `trace-summary`. |
| Treating trace summaries as canonical memory | Link them from the canonical note or mark them non-canonical. |
| Reverting with `git reset --hard` or broad checkout | Use `selective-revert.py` to plan file/hunk-level rollback with backups and explicit `--apply`. |
| Editing protected TDD tests to pass | Stop and explain; only replace a wrong test with an equally strict corrected test. |
| Reporting done without closure | Run the closure checklist or state the blocker. |
