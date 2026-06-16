#!/usr/bin/env python3
"""Install or update the Fable Harness in a local project workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


START = "<!-- fable-harness:start -->"
END = "<!-- fable-harness:end -->"

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
2. Read `{local_dir}/notes/_index.md` when it exists.
3. Read only the compact notes relevant to the task.
4. Open decision traces only when audit or continuation requires the decision path.
5. Read the real project files before editing them.

### Decision Loop

1. Orient: restate the task operationally and identify the smallest relevant surface.
2. Inspect: read the files, logs, docs, or state that govern that surface.
3. Decide: name the intended change or conclusion before the first mutating action.
4. Act: make the smallest coherent mutation or produce the narrowest requested artifact.
5. Verify: run the real gate when it exists; otherwise run the strongest available structural check.
6. Report: give files, numbers, verification, and limits without inflating certainty.

### Harness Rules

- For non-trivial or mutating work, create or continue a trace in `{local_dir}/decision-traces/`.
- Use `{local_dir}/scripts/new-trace.py` to create a trace when practical.
- Keep `{local_dir}/notes/` compact and semantic. Use traces for audit evidence.
- The main orchestrating agent owns memory coherence.
- Subagents may gather evidence, run checks, and suggest memory updates, but do not silently decide what becomes durable project memory.
- For complex or multidisciplinary tasks, break work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Pass subagents minimal context: objective, relevant files, active decisions, protected tests, current trace, and verification command.
- TDD tests written before implementation are protected evidence. Do not weaken, skip, rename, delete, or rewrite them just to make the loop pass.
- Update cadence: trace during the work, semantic notes after verified evidence, indexes at closure.
- Before reporting completion, run the memory closure check in `{local_dir}/templates/memory-closure.md`; use `{local_dir}/scripts/check-closure.py` when practical.

{END}
"""


DECISION_TRACE_TEMPLATE = """# {title}

## Objective

{objective}

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
status: active
layer:
sources:
  - ../decision-traces/<trace>.md
last_verified:
---

## Durable Fact Or Decision

-

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

## Expected Evidence

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
- [ ] Is the current decision trace linked from the relevant index or note?
- [ ] Do compact notes point back to the trace that proves them?
- [ ] Are residual risks named in the trace and final answer?
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

CHECK_CLOSURE_SCRIPT = r'''#!/usr/bin/env python3
"""Check whether a project has the expected Fable Harness closure surface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_TEMPLATES = [
    "decision-trace.md",
    "semantic-note.md",
    "subagent-brief.md",
    "memory-closure.md",
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
        local_dir / "notes" / "_index.md",
        local_dir / "decision-traces" / "_index.md",
    ]:
        if not path.exists():
            missing.append(str(path))

    if args.trace and not Path(args.trace).exists():
        missing.append(args.trace)

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


def install_for(root: Path, agent: str) -> list[Path]:
    cfg = AGENTS[agent]
    local_dir = root / cfg["local_dir"]
    created_or_updated: list[Path] = []

    templates = {
        "decision-trace.md": DECISION_TRACE_TEMPLATE,
        "semantic-note.md": SEMANTIC_NOTE_TEMPLATE,
        "subagent-brief.md": SUBAGENT_BRIEF_TEMPLATE,
        "memory-closure.md": MEMORY_CLOSURE_TEMPLATE,
    }
    for name, content in templates.items():
        path = local_dir / "templates" / name
        write_text(path, content)
        created_or_updated.append(path)

    scripts = {
        "new-trace.py": NEW_TRACE_SCRIPT,
        "check-closure.py": CHECK_CLOSURE_SCRIPT,
    }
    for name, content in scripts.items():
        path = local_dir / "scripts" / name
        write_text(path, content)
        created_or_updated.append(path)

    ensure_index(local_dir / "notes" / "_index.md", "Semantic Notes Index")
    ensure_index(local_dir / "decision-traces" / "_index.md", "Decision Trace Index")

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
    args = parser.parse_args()

    root = Path(args.workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    agents = target_agents(args.agent, root)

    changed: list[Path] = []
    for agent in agents:
        changed.extend(install_for(root, agent))

    print(f"Installed Fable Harness for {', '.join(agents)} in {root}")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
