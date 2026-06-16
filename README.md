# Fable Harness

Fable Harness is a project-local agent harness for Codex, Claude Code, and compatible AI agent workflows. It installs lightweight operating instructions, templates, and scripts that help an agent follow a traceable decision loop instead of improvising hidden process state.

## What it does

- Adds or updates root agent instructions for Codex, Claude, or neutral agent surfaces.
- Installs compact templates for decision traces, semantic notes, subagent briefs, and memory closure checks.
- Provides scripts to create new traces and verify closure before reporting work as complete.
- Preserves existing root instructions and only updates the marked `fable-harness` block.
- Protects TDD audit rails by making pre-implementation tests explicit evidence rather than disposable scaffolding.

## Repository contents

```text
fable-harness/
  SKILL.md
  agents/
    openai.yaml
  scripts/
    install_fable_harness.py
    test_install_fable_harness.py
```

## Install into a project

Run the installer directly from this repository:

```powershell
python ".\scripts\install_fable_harness.py" "C:\path\to\project" --agent codex
```

Or install/run it from GitHub Packages after authenticating npm to
`npm.pkg.github.com`:

```powershell
npm config set @aao-sh:registry https://npm.pkg.github.com
npm login --scope=@aao-sh --registry=https://npm.pkg.github.com
npx @aao-sh/fable-harness "C:\path\to\project" --agent codex
```

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

Check the npm package contents before publishing:

```powershell
npm run pack:check
```

The tests install the harness into temporary workspaces and verify that generated instructions, templates, scripts, and closure checks behave as expected.

## GitHub Packages

This repository is configured to publish `@aao-sh/fable-harness` to GitHub
Packages. Publishing is handled by `.github/workflows/publish-package.yml` on a
published GitHub Release or by manual workflow dispatch.

## License

MIT License. See [LICENSE](LICENSE).
