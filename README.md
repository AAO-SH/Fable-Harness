# Fable Harness

[![Publish](https://github.com/AAO-SH/Fable-Harness/actions/workflows/publish-package.yml/badge.svg)](https://github.com/AAO-SH/Fable-Harness/actions/workflows/publish-package.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Node >=18](https://img.shields.io/badge/node-%3E%3D18-43853d.svg)
![Python >=3.9](https://img.shields.io/badge/python-%3E%3D3.9-3776ab.svg)

Fable Harness is a project-local agent harness for Codex, Claude Code, and compatible AI agent workflows. It installs lightweight operating instructions, templates, and scripts that help an agent follow a traceable decision loop instead of improvising hidden process state.

## What it does

- Adds or updates root agent instructions for Codex, Claude, or neutral agent surfaces.
- Installs compact templates for decision traces, semantic notes, subagent briefs, and memory closure checks.
- Provides scripts to create new traces and verify closure before reporting work as complete.
- Installs native loop governance scripts that record loop state, events, and checklist evidence for audit-sensitive work.
- Records composable workflow patterns for complex tasks: classify, fan out, verify adversarially, generate/filter options, run tournaments, and loop until done with explicit budgets.
- Enforces note and trace hygiene with atomic permanent-note metadata, canonical note schema, duplicate canonical-note detection, MOCs, and strict maintenance gates.
- Generates a typed local semantic knowledge graph for notes, traces, promotions, scripts, verification evidence, memory dreaming, and subagent work.
- Strengthens local RAG with heading-aware chunking, hybrid lexical/vector/graph scoring, reranking, chunk citations, incremental chunk cache, retrieval reports, and recall/precision evaluation.
- Adds source arbitration so RAG-informed code/doc changes get a lightweight comparison against real project files, escalating to an Evidence Dispute only when material conflict appears.
- Generates a local code graph for currently supported source symbols, imports, calls, tests, and static impact checks.
- Warns, at most once every 24 hours, when a newer GitHub release is available.
- Closes or justifies completed subagent sessions before final loop closure.
- Creates reviewable Memory Dreaming runs that track memory use, consolidate memory, copy promoted evidence into dormant storage, and reactivate compact notes on demand.
- Preserves existing root instructions and only updates the marked `fable-harness` block.
- Protects TDD audit rails by making pre-implementation tests explicit evidence rather than disposable scaffolding.
- Can install Superpowers as a project-local companion skill library when it is absent or outdated.

## Install into a project

The preferred path is to call the skill from your agent and ask it to install the harness into the current workspace:

```text
Use the fable-harness skill to install this workspace for Codex.
```

If you are installing manually, run the installer directly from this repository:

```powershell
python ".\scripts\install_fable_harness.py" "C:\path\to\project" --agent codex
```

Package-manager entry points are available for automation, but direct skill invocation is the intended interactive install path.

During an interactive install, Fable Harness checks for Superpowers at `.agents/skills/using-superpowers/SKILL.md`. If it is missing, the installer asks whether to install Superpowers from the latest official release. If it is present but older than the selected source, the installer asks whether to update it. Declining keeps Fable Harness standalone and leaves any existing Superpowers install unchanged.

Non-interactive installs never block on this prompt. Use explicit flags when scripting:

```powershell
python ".\scripts\install_fable_harness.py" "C:\path\to\project" --agent codex --with-superpowers
python ".\scripts\install_fable_harness.py" "C:\path\to\project" --agent codex --without-superpowers
python ".\scripts\install_fable_harness.py" "C:\path\to\project" --agent codex --upgrade-superpowers
```

Superpowers is copied into `.agents/skills/` and tracked in `.agents/vendor/superpowers/manifest.json`. The installer does not add Superpowers-specific usage instructions to `AGENTS.md` or `CLAUDE.md`.

Agent modes:

| Mode | Creates or updates |
|---|---|
| `codex` | `AGENTS.md` and `.codex/` |
| `claude` | `CLAUDE.md` and `.claude/` |
| `any` | `AGENTS.md` and `.agents/` |
| `both` | Codex, Claude, and neutral agent surfaces |
| `auto` | Detects the best target from the workspace |

## Typical workflow

After installation, create a decision trace for substantial work:

```powershell
python ".codex\scripts\release-notice.py" check --root "."
```

The release notice check only prints when a newer GitHub release exists. It does not download or apply updates.

```powershell
python ".codex\scripts\new-trace.py" --root "." --title "Short Task Title"
```

Start a governed loop for audit-sensitive work:

```powershell
python ".codex\scripts\loop-start.py" --root "." --task "Short Task Title"
python ".codex\scripts\loop-check.py" --root "." --run ".codex\loop\runs\<run>" --strict
```

For complex work, record a composable workflow recipe:

```powershell
python ".codex\scripts\loop-start.py" --root "." --task "Harden workflow" --pattern loop-until-done --recipe classify-and-act --recipe fan-out-and-synthesize --recipe adversarial-verification --budget-max-iterations 3 --json
```

Before reporting completion, run the closure check:

```powershell
python ".codex\scripts\check-closure.py" --root "." --trace ".codex\decision-traces\<trace>.md"
```

For memory-heavy work, run strict hygiene:

```powershell
python ".codex\scripts\memory-maintenance.py" --root "." --strict --json
```

For memory-heavy recall, materialize retrieval evidence before answering or planning:

```powershell
python ".codex\scripts\memory-search.py" --root "." --query "current task" --json
python ".codex\scripts\rag-pipeline.py" --root "." --query "current task" --json
python ".codex\scripts\source-arbitrate.py" --root "." --query "current task" --source "docs\relevant.md" --json
```

When tuning retrieval, evaluate it against a local JSON/JSONL set:

```powershell
python ".codex\scripts\rag-eval.py" --root "." --eval-file ".codex\memory\rag-eval.jsonl" --k 5 --json
```

Inspect or validate the generated knowledge graph:

```powershell
python ".codex\scripts\graph-query.py" --root "." --relation promotes
python ".codex\scripts\graph-query.py" --root "." --q "semantic retrieval" --json
python ".codex\scripts\graph-check.py" --root "." --strict --json
```

Create subagent briefs for simultaneous waves:

```powershell
python ".codex\scripts\subagent-plan.py" --root "." --task "Harden harness" --domain "graph" --domain "docs" --parallel --depends-on "docs:graph"
python ".codex\scripts\subagent-result.py" --root "." --plan-dir ".codex\subagents\<plan>" --domain "graph" --status DONE --accepted-by orchestrator
python ".codex\scripts\subagent-sweep.py" --root "." --plan-dir ".codex\subagents\<plan>" --close-completed
```

Build, query, and validate the generated code graph:

```powershell
python ".codex\scripts\code-graph-build.py" --root "." --json
python ".codex\scripts\code-graph-query.py" --root "." --symbol "install_harness" --json
python ".codex\scripts\code-graph-check.py" --root "." --json
```

For non-trivial programming work, the generated instructions use Programming Recall: semantic recall explains why, Code Graph maps where and what may break, and source files remain the final operational authority. The agent uses memory/RAG/semantic graph for prior decisions, architecture intent, constraints, and verification history; it uses Code Graph for files, symbols, dependencies, callers, tests, and static impact before broad source-code edits.

Run agent-reviewed Memory Dreaming maintenance:

```powershell
python ".codex\scripts\memory-touch.py" --root "." --path ".codex\notes\decisions\memory\example.md" --reason "loaded for task context" --json
python ".codex\scripts\memory-dream.py" maintain --root "." --context "current task" --auto-safe --agent-review --json
```

`maintain` applies context-cold safe mechanical actions automatically and writes `agent-review.md` for semantic decisions. The orchestrating agent reviews that file; the user is only needed for conflicts, product decisions, or possible loss of primary evidence.

Create and apply a manual Memory Dreaming run when you need an explicit two-step review:

```powershell
python ".codex\scripts\memory-touch.py" --root "." --path ".codex\notes\decisions\memory\example.md" --reason "loaded for task context" --json
python ".codex\scripts\memory-dream.py" plan --root "." --json
python ".codex\scripts\memory-dream.py" apply --root "." --run ".codex\memory\dreams\runs\<run>" --apply
```

For memory-heavy work, run `memory-dream.py maintain --auto-safe --agent-review` as a background memory curator/subagent task when possible.
Inspect the run's `agent-review.md`, `report.md`, and `diff.json` before changing semantic notes.

Search dormant memory and reactivate a compact note:

```powershell
python ".codex\scripts\memory-dream.py" search-dormant --root "." --query "old release decision" --json
python ".codex\scripts\memory-dream.py" reactivate --root "." --query "old release decision" --category decisions --area memory --topic old-release-decision --apply
```

The generated agent instructions include a Recall Ladder for non-trivial work: hybrid memory search, retrieval pipeline with cited source inspection, notes index, compact active notes, touch tracking, graph lookup, dormant search, traces only when needed, then project docs/source files. When RAG informs a task that may edit code or docs, the agent runs a lightweight source-arbitration check against real project files; material conflicts become an Evidence Dispute with user approval before replacing project facts with RAG-derived facts. If local sources do not provide a verifiable structured basis, the agent must research the web before planning; if strong web references are still unavailable for a new task, it interviews the user before creating a plan. For non-trivial programming work, Programming Recall combines semantic memory with Code Graph before edits: semantic recall explains why, Code Graph maps where and what may break, and source files remain the final operational authority. Closure then promotes durable decisions, rebuilds memory, runs strict maintenance, and runs agent-reviewed dream maintenance when memory-heavy.

The generated instructions also include Parallel Agent Dispatch And Safety: during Orient/Classify, automatically evaluate whether complex or multidisciplinary work has independent domains that should go to subagents. The installed Fable Harness block is standing project-level user authorization to invoke available subagent or parallel-agent tools automatically when the independence check passes, without a trigger phrase or per-prompt permission. If a higher-priority runtime policy blocks dispatch anyway, record that platform limitation in the trace and execute the briefs sequentially. Keep dependent steps inside one domain causally ordered; synchronize subagent waves before integration, verification, memory promotion, rebuilds, session sweep, and closure.

For a user-requested selective rollback, create a plan first:

```powershell
python ".codex\scripts\selective-revert.py" plan --root "." --path "src/example.py"
```

For a native checkpoint that does not depend on Git:

```powershell
python ".codex\scripts\selective-revert.py" checkpoint --root "." --label "before-risky-change" --path "src/example.py"
```

Rollback plans are written under `rollback/`, include current-file backups, and only mutate files when applied with `--apply`.

Use `.claude\scripts\...` for Claude installs or `.agents\scripts\...` for neutral installs.

Semantic notes use required frontmatter:

```yaml
memory_schema: atomic-v1
type: canonical-decision | trace-summary | operational-note | migration-note
status: active | superseded | archived
scope: category/area/topic
canonical: true | false
thesis: Title States The Claim
atomic: true
tags:
properties:
moc:
links:
sources:
supersedes:
last_verified: YYYY-MM-DD
validation:
  - atomic
  - thesis-title
  - connects
  - unique
  - metadata
```

Keep one active `canonical-decision` per `scope`. New permanent notes use `memory_schema: atomic-v1`: one idea, title as thesis, explicit connections, unique scope, and queryable metadata. Decision traces are audit evidence; notes are canonical memory; `memory/` is generated retrieval state.

## Validation

Run the bundled test suite:

```powershell
python -m unittest discover ".\scripts" "test_*.py"
```

The tests install the harness into temporary workspaces and verify that generated instructions, templates, scripts, and closure checks behave as expected.

## License

MIT License. See [LICENSE](LICENSE).
