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
- Use `{local_dir}/scripts/new-note.py` for compact semantic notes in `category/area/topic.md` layout.
- Use `{local_dir}/scripts/promote-trace.py` to promote durable trace evidence into semantic notes.
- Use `{local_dir}/scripts/subagent-result.py` to record subagent outcomes in the dispatch package and active trace.
- Before broad filesystem exploration or planning a non-trivial task, run `{local_dir}/scripts/memory-search.py` with a concise query derived from the user request, unless the task is clearly self-contained.
- Use `{local_dir}/scripts/rebuild-memory.py` when notes or traces were edited manually.
- Use `{local_dir}/scripts/memory-maintenance.py` periodically or after large tasks to report oversized notes, broken sources, stale notes, and archive-ready promoted traces.
- Keep `{local_dir}/notes/` compact and semantic. Use traces for audit evidence.
- Keep `{local_dir}/memory/` as generated retrieval state: sharded local embeddings, promotion log, and knowledge graph.
- The main orchestrating agent owns memory coherence.
- Subagents may gather evidence, run checks, and suggest memory updates, but do not silently decide what becomes durable project memory.
- For complex or multidisciplinary tasks, break work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Use `{local_dir}/scripts/subagent-plan.py` to create dispatchable subagent briefs before broad execution when the task has independent domains.
- Dispatch subagents from the generated briefs using the available subagent tool. If no subagent tool exists, execute the briefs sequentially and record that fallback in the trace.
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
import json
import os
import re
import sys
from pathlib import Path


REQUIRED_TEMPLATES = [
    "decision-trace.md",
    "semantic-note.md",
    "subagent-brief.md",
    "memory-closure.md",
]

REQUIRED_MEMORY_SCRIPTS = [
    "memory_core.py",
    "new-note.py",
    "promote-trace.py",
    "memory-search.py",
    "rebuild-memory.py",
    "subagent-plan.py",
    "subagent-result.py",
    "memory-maintenance.py",
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
from pathlib import Path


VECTOR_DIMS = 64
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


def iter_markdown_docs(local_dir: Path) -> list[dict[str, object]]:
    docs: list[dict[str, object]] = []
    for base, doc_type in [(local_dir / "notes", "note"), (local_dir / "decision-traces", "trace")]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name == "_index.md":
                continue
            text = path.read_text(encoding="utf-8")
            rel = relpath(path, local_dir.parent)
            docs.append({
                "id": hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16],
                "type": doc_type,
                "path": rel,
                "title": file_title(text, path.stem),
                "summary": compact_summary(text),
                "terms": top_terms(text),
                "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "vector": vector(text),
                "sources": source_lines(text),
            })
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


def update_notes_index(local_dir: Path) -> None:
    notes = local_dir / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    lines = ["# Semantic Notes Index", "", "Compact project memory for future agents.", "", "## Notes", ""]
    for path in sorted(notes.rglob("*.md")):
        if path.name == "_index.md":
            continue
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

    docs = iter_markdown_docs(local_dir)
    shard_meta: dict[str, dict[str, object]] = {}

    for doc in docs:
        shard_id = str(doc["id"])[:2]
        shard_path = shards_dir / f"{shard_id}.jsonl"
        append_jsonl(shard_path, doc)
        meta = shard_meta.setdefault(shard_id, {
            "id": shard_id,
            "path": relpath(shard_path, root),
            "doc_count": 0,
            "terms": set(),
        })
        meta["doc_count"] = int(meta["doc_count"]) + 1
        meta["terms"].update(doc["terms"])  # type: ignore[union-attr]

        append_jsonl(graph_dir / "nodes.jsonl", {
            "id": doc["id"],
            "kind": doc["type"],
            "path": doc["path"],
            "title": doc["title"],
        })
        for term in list(doc["terms"])[:8]:
            term_id = f"term:{term}"
            append_jsonl(graph_dir / "nodes.jsonl", {"id": term_id, "kind": "term", "title": term})
            append_jsonl(graph_dir / "edges.jsonl", {
                "from": doc["id"],
                "to": term_id,
                "type": "mentions",
            })
        for source in doc["sources"]:
            append_jsonl(graph_dir / "edges.jsonl", {
                "from": doc["id"],
                "to": source,
                "type": "sourced_by",
            })

    shards = []
    for meta in sorted(shard_meta.values(), key=lambda item: str(item["id"])):
        shards.append({
            "id": meta["id"],
            "path": meta["path"],
            "doc_count": meta["doc_count"],
            "terms": sorted(meta["terms"])[:64],
        })

    manifest = {
        "version": 1,
        "storage": "sharded-jsonl",
        "embedding": "local-hash-v1",
        "vector_dims": VECTOR_DIMS,
        "document_count": len(docs),
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
            "node_file": "nodes.jsonl",
            "edge_file": "edges.jsonl",
            "source_manifest": "../manifest.json",
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


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
    layer = area or category
    source_block = ""
    if source_trace:
        source_block = f"  - {relpath(source_trace.resolve(), path.parent)}\n"
    sources_section = source_block if source_block else "  - \n"
    default_body = "## Durable Fact Or Decision\n\n-\n\n## Evidence\n\n-\n\n## Operational Use\n\n-\n\n## Revalidation\n\n-"
    body_text = body or default_body
    content = f"""# {title}

---
status: active
layer: {layer}
sources:
{sources_section}last_verified: {dt.date.today().isoformat()}
---

{body_text}
"""
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    update_notes_index(local_dir)
    build_memory(root, agent)
    return path


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
            score = cosine(query_vector, doc.get("vector", []))
            if query_terms:
                overlap = len(query_terms.intersection(set(doc.get("terms", []))))
                score += overlap * 0.05
            if doc.get("type") == "note":
                score += 0.15
            if score <= 0:
                continue
            results.append({
                "score": round(score, 6),
                "path": doc["path"],
                "title": doc["title"],
                "type": doc["type"],
                "summary": doc.get("summary", ""),
                "shard": shard["id"],
            })
    results.sort(key=lambda item: (0 if item["type"] == "note" else 1, -float(item["score"]), str(item["path"])))
    return results[:limit]
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

SUBAGENT_PLAN_SCRIPT = r'''#!/usr/bin/env python3
"""Create dispatchable subagent briefs for a Fable Harness task."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from memory_core import find_local_dir, relpath, slugify


def lines(items: list[str], prefix: str = "- ", empty: str = "None provided. Orchestrator must fill this before dispatch.") -> str:
    if not items:
        return f"{prefix}{empty}\n"
    return "\n".join(f"{prefix}{item}" for item in items) + "\n"


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


def dispatch_text(task: str, plan_dir: Path, briefs: list[Path], root: Path) -> str:
    rows = "\n".join(
        f"| {brief.stem} | `{relpath(brief, root)}` | pending | |"
        for brief in briefs
    )
    commands = "\n\n".join(
        "Use the available subagent spawn tool with this brief as the message "
        "(for example, `spawn_agent` when that tool is exposed):\n"
        f"`{relpath(brief, root)}`"
        for brief in briefs
    )
    return f"""# Subagent Dispatch

## Task

{task}

## Invocation

Dispatch using the available subagent tool. In Codex, first verify which subagent spawn tool is exposed, then use it.
If no subagent tool is available, execute these briefs sequentially and record that fallback in the active decision trace.

## Briefs

| Domain | Brief | Status | Accepted By Orchestrator |
|---|---|---|---|
{rows}

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
    parser.add_argument("--slug")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    domains = args.domain or ["implementation"]
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
    for domain in domains:
        path = plan_dir / f"{slugify(domain)}.md"
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

    dispatch = plan_dir / "_dispatch.md"
    dispatch.write_text(dispatch_text(args.task, plan_dir, briefs, root).rstrip() + "\n", encoding="utf-8")
    (plan_dir / "manifest.json").write_text(
        json.dumps({
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "task": args.task,
            "trace": relpath(trace, root) if trace else None,
            "briefs": [relpath(path, root) for path in briefs],
            "verification": args.verification,
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
from pathlib import Path

from memory_core import relpath, slugify


STATUSES = ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED")


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
    (plan_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    parser.add_argument("--trace")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan_dir = resolve_path(args.plan_dir, root)
    plan_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.domain)
    results_dir = plan_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    result_path = results_dir / f"{slug}-result.md"

    result_text = f"""# Subagent Result: {args.domain}

## Status

{args.status}

## Summary

{args.summary or "none"}

## Accepted By Orchestrator

{args.accepted_by or "pending"}

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
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    manifest.setdefault("results", [])
    assert isinstance(manifest["results"], list)
    manifest["results"].append(result_record)
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

MEMORY_MAINTENANCE_SCRIPT = r'''#!/usr/bin/env python3
"""Report memory growth and retrieval-maintenance candidates without deleting source files."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from memory_core import file_title, find_local_dir, relpath, source_lines


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
    args = parser.parse_args()

    root = Path(args.root).resolve()
    local_dir = find_local_dir(root, args.agent)
    report = build_report(root, args.agent, args.max_note_bytes, args.max_trace_bytes, args.stale_days)
    write_report(root, local_dir, report)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(local_dir / "memory" / "maintenance" / "latest-report.md")
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


def ensure_memory_files(local_dir: Path) -> None:
    memory = local_dir / "memory"
    (memory / "shards").mkdir(parents=True, exist_ok=True)
    (memory / "graph").mkdir(parents=True, exist_ok=True)
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
        "memory_core.py": MEMORY_CORE_SCRIPT,
        "new-note.py": NEW_NOTE_SCRIPT,
        "promote-trace.py": PROMOTE_TRACE_SCRIPT,
        "memory-search.py": MEMORY_SEARCH_SCRIPT,
        "rebuild-memory.py": REBUILD_MEMORY_SCRIPT,
        "subagent-plan.py": SUBAGENT_PLAN_SCRIPT,
        "subagent-result.py": SUBAGENT_RESULT_SCRIPT,
        "memory-maintenance.py": MEMORY_MAINTENANCE_SCRIPT,
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
