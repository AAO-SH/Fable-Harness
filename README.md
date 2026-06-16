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
- Preserves existing root instructions and only updates the marked `fable-harness` block.
- Protects TDD audit rails by making pre-implementation tests explicit evidence rather than disposable scaffolding.

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

Agent modes:

| Mode | Creates or updates |
|---|---|
| `codex` | `AGENTS.md` and `.codex/` |
| `claude` | `CLAUDE.md` and `.claude/` |
| `any` | `AGENTS.md`, `README.md`, and `.agents/` |
| `both` | Codex, Claude, and neutral agent surfaces |
| `auto` | Detects the best target from the workspace |

## Typical workflow

After installation, create a decision trace for substantial work:

```powershell
python ".codex\scripts\new-trace.py" --root "." --title "Short Task Title"
```

Before reporting completion, run the closure check:

```powershell
python ".codex\scripts\check-closure.py" --root "." --trace ".codex\decision-traces\<trace>.md"
```

Use `.claude\scripts\...` for Claude installs or `.agents\scripts\...` for neutral installs.

## Validation

Run the bundled test suite:

```powershell
python ".\scripts\test_install_fable_harness.py"
```

The tests install the harness into temporary workspaces and verify that generated instructions, templates, scripts, and closure checks behave as expected.

## License

MIT License. See [LICENSE](LICENSE).
