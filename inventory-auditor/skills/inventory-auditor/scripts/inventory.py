#!/usr/bin/env python3
"""Inventory the skills, agents and hooks an agent can load; measure load cost and usage.

Passes 1-3 of the inventory auditor (see ../references/schema.md):

1. inventory  - every skill and agent the host can load, plus hook events
2. load cost  - description bytes (paid every turn) and body bytes against a
                size budget (paid when the item triggers)
3. usage      - Skill/Agent tool calls and typed /commands in Claude Code
                transcripts

It only reads. It writes inventory.json and inventory-report.md to --out and
changes nothing else. Judgment calls (overlap, merges, drift) are left to the
model, which is why this script never prints a verdict.

    python3 inventory.py --root . --out /tmp/inventory
    python3 inventory.py --root . --extra ~/my-plugins/review --out /tmp/inventory

Sources: <root>/.claude/skills, <root>/.claude/agents, <root>/.agents/skills,
~/.claude/skills, ~/.claude/agents, and any --extra folder (plugins are stored
differently by each host, so point --extra at a plugin's folder to include it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

SCHEMA_VERSION = 1
DESCRIPTION_LIMIT_CHARS = 1_024   # Agent Skills spec maximum for `description`
NEAR_BUDGET_RATIO = 0.85          # flag an item at 85% of its budget
SKILL_BUDGET = 20_000             # SKILL.md body; detail belongs in references/
AGENT_BUDGET = 12_000             # a subagent's whole system prompt
BYTES_PER_TOKEN = 4               # rough English average; labelled as an estimate
RESOURCE_DIRS = ("references", "scripts", "assets", "evals")
COMMAND_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
# A regex instead of json.loads on every line: most lines are large tool
# results, and we only need the date range from them.
TIMESTAMP_RE = re.compile(r'"timestamp":\s*"([^"]+)"')


# ---------------------------------------------------------------- data shapes
# Dataclasses mirror references/schema.md so the JSON shape is written down once.

@dataclass
class Usage:
    tool_calls: int = 0
    typed: int = 0
    last_used: Optional[str] = None

    def record(self, timestamp: Optional[str], typed: bool) -> None:
        if typed:
            self.typed += 1
        else:
            self.tool_calls += 1
        if timestamp and (self.last_used is None or timestamp > self.last_used):
            self.last_used = timestamp

    @property
    def total(self) -> int:
        return self.tool_calls + self.typed


@dataclass
class Item:
    id: str
    kind: str
    name: str
    source: str
    host: str                     # which agent loads it: "claude" or "agents" (Codex etc.)
    path: str
    description: str
    description_bytes: int
    body_bytes: int
    budget_bytes: Optional[int]
    budget_ratio: Optional[float]
    resources: list[str]
    sha256: str                   # short content hash, to spot drifted copies
    usage: Usage = field(default_factory=Usage)


@dataclass
class Hook:
    event: str
    source: str
    matcher: str
    commands: int


@dataclass
class Finding:
    rule: str
    item: str
    severity: str
    evidence: str
    decided_by: str = "script"


@dataclass
class TranscriptWindow:
    files: int = 0
    first: Optional[str] = None
    last: Optional[str] = None
    host: str = "claude-code"
    skipped: int = 0              # files that existed but couldn't be read
    error: Optional[str] = None   # why no transcripts were read at all

    def see(self, timestamp: Optional[str]) -> None:
        if not timestamp:
            return
        if self.first is None or timestamp < self.first:
            self.first = timestamp
        if self.last is None or timestamp > self.last:
            self.last = timestamp


# ------------------------------------------------------------------ pass 1

def frontmatter(text: str) -> dict[str, str]:
    """Read flat `key: value` frontmatter without PyYAML (standard library only).

    Handles plain, quoted and folded (`>` / `|`) values, which covers typical
    SKILL.md and agent files. Nested YAML is ignored on purpose:
    only `name` and `description` matter for routing.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    lines = text[3:end].strip("\n").splitlines()
    i = 0
    while i < len(lines):
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
        i += 1
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in (">", "|", ">-", "|-"):
            block: list[str] = []
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            joiner = " " if value.startswith(">") else "\n"
            value = joiner.join(part for part in block if part)
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = json.loads(value) if value[0] == '"' else value[1:-1]
        result[key] = value
    return result


def make_item(kind: str, file: Path, fallback_name: str, source: str, host: str, budget: int) -> Item:
    raw = file.read_bytes()
    meta = frontmatter(raw.decode("utf-8", errors="replace"))
    name = meta.get("name") or fallback_name
    description = meta.get("description", "")
    folder = file.parent if kind == "skill" else None
    resources = sorted(d for d in RESOURCE_DIRS if folder and (folder / d).is_dir())
    return Item(
        id=f"{kind}:{name}",
        kind=kind,
        name=name,
        source=source,
        host=host,
        path=str(file),
        description=description,
        description_bytes=len(description.encode("utf-8")),
        body_bytes=len(raw),
        budget_bytes=budget,
        budget_ratio=round(len(raw) / budget, 2),
        resources=resources,
        sha256=hashlib.sha256(raw).hexdigest()[:12],
    )


def skill_files(folder: Path) -> Iterator[Path]:
    if folder.is_dir():
        yield from sorted(folder.glob("*/SKILL.md"))


def agent_files(folder: Path) -> Iterator[Path]:
    if folder.is_dir():
        yield from sorted(folder.glob("*.md"))


def sources(root: Path, home: Path, extras: list[Path]) -> list[tuple[str, str, str, Path]]:
    """(kind, source label, host, folder) for every place an agent loads items from.

    Claude Code reads .claude/ folders; other agents (Codex and tools following
    the open Agent Skills layout) read .agents/skills. A copy in each isn't a
    conflict, because no single host sees both.
    """
    found = [
        ("skill", "project", "claude", root / ".claude" / "skills"),
        ("agent", "project", "claude", root / ".claude" / "agents"),
        ("skill", "project-agents", "agents", root / ".agents" / "skills"),
        ("skill", "user", "claude", home / ".claude" / "skills"),
        ("agent", "user", "claude", home / ".claude" / "agents"),
    ]
    for extra in extras:
        # A plugin keeps skills/<name>/SKILL.md and agents/*.md; a bare skills
        # folder keeps <name>/SKILL.md directly. Plugins load into Claude Code.
        label = f"extra:{extra.name}"
        found += [("skill", label, "claude", extra / "skills"),
                  ("agent", label, "claude", extra / "agents"),
                  ("skill", label, "claude", extra)]
    return found


def collect_items(root: Path, home: Path, extras: list[Path],
                  skill_budget: int = SKILL_BUDGET, agent_budget: int = AGENT_BUDGET) -> list[Item]:
    items: list[Item] = []
    seen: set[Path] = set()  # resolved paths: a symlinked copy is the same item
    for kind, source, host, folder in sources(root, home, extras):
        files = skill_files(folder) if kind == "skill" else agent_files(folder)
        for file in files:
            real = file.resolve()
            if real in seen:
                continue
            seen.add(real)
            fallback = file.parent.name if kind == "skill" else file.stem
            budget = skill_budget if kind == "skill" else agent_budget
            items.append(make_item(kind, file, fallback, source, host, budget))
    # The same name in two places is a real routing problem; keep ids unique.
    counts: dict[str, int] = {}
    for item in items:
        counts[item.id] = counts.get(item.id, 0) + 1
    for item in items:
        if counts[item.id] > 1:
            item.id = f"{item.id}@{item.source}"
    return items


def collect_hooks(paths: Iterable[Path]) -> list[Hook]:
    """List hook events from settings.json-style files: {"hooks": {event: [...]}}."""
    hooks: list[Hook] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        events = data.get("hooks", {}) if isinstance(data, dict) else {}
        for event, groups in (events.items() if isinstance(events, dict) else []):
            for group in groups if isinstance(groups, list) else []:
                if not isinstance(group, dict):
                    continue
                commands = group.get("hooks", [])
                hooks.append(Hook(
                    event=event,
                    source=str(path),
                    matcher=str(group.get("matcher", "")),
                    commands=len(commands) if isinstance(commands, list) else 0,
                ))
    return hooks


# ------------------------------------------------------------------ pass 3

def transcript_events(line: str) -> Iterator[tuple[str, Optional[str], bool]]:
    """Yield (name, timestamp, typed) for each skill/agent use in one JSONL line."""
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return
    if not isinstance(entry, dict):
        return
    timestamp = entry.get("timestamp")
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None

    if entry.get("type") == "user":
        texts = [content] if isinstance(content, str) else [
            block.get("text", "") for block in content or []
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        for text in texts:
            for name in COMMAND_RE.findall(text):
                yield name, timestamp, True
        return

    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        tool_input = block.get("input") or {}
        if block.get("name") == "Skill":
            name = tool_input.get("skill")
        elif block.get("name") in ("Agent", "Task"):
            name = tool_input.get("subagent_type")
        else:
            continue
        if isinstance(name, str) and name:
            yield name, timestamp, False


def resolve(name: str, by_name: dict[str, list[Item]]) -> list[Item]:
    """Exact name first; `plugin:skill` falls back to `skill`.

    When two items share a name the transcript can't say which one ran, so the
    use is counted on both and the duplicate_name finding says so.
    """
    if name in by_name:
        return by_name[name]
    return by_name.get(name.rsplit(":", 1)[-1], [])


def count_usage(items: list[Item], transcripts: Path) -> TranscriptWindow:
    window = TranscriptWindow()
    by_name: dict[str, list[Item]] = {}
    for item in items:
        by_name.setdefault(item.name, []).append(item)
    # A sandbox can answer "permission denied" instead of "not found", and
    # is_dir() raises on that. Either way usage is unknown, never zero, so
    # record why and carry on (an eval run crashed here before this guard).
    try:
        if not transcripts.is_dir():
            window.error = f"no transcripts folder at {transcripts}"
            return window
        files = sorted(transcripts.rglob("*.jsonl"))
    except OSError as error:
        window.error = f"can't read {transcripts}: {error.strerror or error}"
        return window
    for file in files:
        try:
            read_transcript(file, by_name, window)
            window.files += 1
        except OSError:
            window.skipped += 1
    return window


def read_transcript(file: Path, by_name: dict[str, list[Item]], window: TranscriptWindow) -> None:
    with file.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if '"timestamp"' in line:
                match = TIMESTAMP_RE.search(line)
                window.see(match.group(1) if match else None)
            # Cheap filter: most lines are neither tool calls nor commands.
            if "tool_use" not in line and "command-name" not in line:
                continue
            for name, timestamp, typed in transcript_events(line):
                for item in resolve(name, by_name):
                    item.usage.record(timestamp, typed)


# ---------------------------------------------------------------- findings

def find_problems(items: list[Item], window: TranscriptWindow) -> list[Finding]:
    findings: list[Finding] = []
    span = f"{(window.first or '?')[:10]} to {(window.last or '?')[:10]}"
    for item in items:
        if not item.description:
            findings.append(Finding("missing_description", item.id, "high",
                                    "no description in frontmatter"))
        elif len(item.description) > DESCRIPTION_LIMIT_CHARS:
            findings.append(Finding("description_over_limit", item.id, "high",
                                    f"{len(item.description):,} chars; limit {DESCRIPTION_LIMIT_CHARS:,}"))
        if item.budget_ratio is not None and item.budget_bytes:
            evidence = f"{item.body_bytes:,} of {item.budget_bytes:,} bytes ({item.budget_ratio:.0%})"
            if item.budget_ratio > 1:
                findings.append(Finding("over_budget", item.id, "high", evidence))
            elif item.budget_ratio >= NEAR_BUDGET_RATIO:
                findings.append(Finding("near_budget", item.id, "low", evidence))
        if window.files and item.usage.total == 0:
            findings.append(Finding("unused_in_window", item.id, "low",
                                    f"0 uses in {window.files} transcripts, {span}"))
    findings += duplicates(items)
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(findings, key=lambda f: (order[f.severity], f.rule, f.item))


def duplicates(items: list[Item]) -> list[Finding]:
    """Same name twice for one host: a real conflict. Across hosts: only drift."""
    findings: list[Finding] = []
    by_name: dict[str, list[Item]] = {}
    for item in items:
        by_name.setdefault(f"{item.kind}:{item.name}", []).append(item)
    for key, group in by_name.items():
        by_host: dict[str, list[Item]] = {}
        for item in group:
            by_host.setdefault(item.host, []).append(item)
        for host, same in by_host.items():
            if len(same) > 1:
                where = ", ".join(i.path for i in same)
                findings += [Finding("duplicate_name", i.id, "high",
                                     f"{key} is defined {len(same)} times for {host} ({where}); "
                                     "it may load either, and usage is shared") for i in same]
        if len(by_host) > 1 and len({i.sha256 for i in group}) > 1:
            where = ", ".join(f"{i.source}: {i.path}" for i in group)
            # Low: copies are often adapted per agent on purpose (CLAUDE.md -> AGENTS.md).
            findings += [Finding("copies_differ", i.id, "low",
                                 f"{key} has copies for different agents that differ; "
                                 f"check the difference is intended ({where})")
                         for i in group]
    return findings


# ------------------------------------------------------------------ output

def build(root: Path, home: Path, transcripts: Path, extras: Optional[list[Path]] = None,
          skill_budget: int = SKILL_BUDGET, agent_budget: int = AGENT_BUDGET) -> dict[str, object]:
    extras = extras or []
    items = collect_items(root, home, extras, skill_budget, agent_budget)
    hooks = collect_hooks([
        home / ".claude" / "settings.json",
        root / ".claude" / "settings.json",
        root / ".claude" / "settings.local.json",
        *(extra / "hooks" / "hooks.json" for extra in extras),
    ])
    window = count_usage(items, transcripts)
    always_loaded = sum(item.description_bytes for item in items)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "transcripts": asdict(window),
        "totals": {
            "items": len(items),
            "always_loaded_bytes": always_loaded,
            "always_loaded_tokens_est": always_loaded // BYTES_PER_TOKEN,
        },
        "items": [asdict(item) for item in items],
        "hooks": [asdict(hook) for hook in hooks],
        "findings": [asdict(f) for f in find_problems(items, window)],
    }


def report(data: dict[str, object]) -> str:
    """Render the human report. Numbers only; verdicts are the model's job."""
    totals = data["totals"]
    window = data["transcripts"]
    items = data["items"]
    findings = data["findings"]
    hooks = data["hooks"]
    assert isinstance(totals, dict) and isinstance(window, dict)
    assert isinstance(items, list) and isinstance(findings, list) and isinstance(hooks, list)

    first = (window["first"] or "?")[:10]
    last = (window["last"] or "?")[:10]
    # Zero transcripts must read as "unknown", never as "nothing is used".
    usage_line = (
        f"usage from {window['files']} Claude Code transcripts, {first} to {last}."
        if window["files"] else
        f"no transcripts were read ({window['error'] or 'none found'}), so usage is unknown."
    )
    if window["skipped"]:
        usage_line += f" {window['skipped']} transcript files couldn't be read."
    lines = [
        "# Inventory report",
        "",
        f"{totals['items']} items · {len(hooks)} hooks · "
        f"{totals['always_loaded_bytes']:,} description bytes load every turn "
        f"(~{totals['always_loaded_tokens_est']:,} tokens, estimated) · "
        f"{usage_line} Codex usage is not counted.",
        "",
        "## Findings",
        "",
    ]
    if findings:
        lines += ["| Severity | Rule | Item | Evidence |", "|---|---|---|---|"]
        lines += [f"| {f['severity']} | {f['rule']} | `{f['item']}` | {f['evidence']} |" for f in findings]
    else:
        lines.append("None.")
    lines += [
        "",
        "## Items by load cost",
        "",
        "| Item | Source | Description bytes | Body / budget | Uses | Last used |",
        "|---|---|---|---|---|---|",
    ]
    for item in sorted(items, key=lambda i: -i["description_bytes"]):
        budget = f"{item['body_bytes']:,} / {item['budget_bytes']:,}" if item["budget_bytes"] else f"{item['body_bytes']:,} / –"
        usage = item["usage"]
        uses = usage["tool_calls"] + usage["typed"]
        last_used = (usage["last_used"] or "–")[:10]
        lines.append(f"| `{item['id']}` | {item['source']} | {item['description_bytes']:,} | {budget} | {uses} | {last_used} |")
    lines += ["", "## Hooks", ""]
    lines += [f"- {h['event']} ({h['matcher'] or 'all'}) in `{h['source']}`" for h in hooks] or ["None configured."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("."), help="project folder (default: here)")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--extra", type=Path, action="append", default=[], metavar="DIR",
                        help="a plugin or skills folder to include (repeatable)")
    parser.add_argument("--skill-budget", type=int, default=SKILL_BUDGET, help="SKILL.md bytes")
    parser.add_argument("--agent-budget", type=int, default=AGENT_BUDGET, help="agent file bytes")
    parser.add_argument("--transcripts", type=Path, default=None,
                        help="default: <home>/.claude/projects")
    parser.add_argument("--out", type=Path, required=True, help="folder for inventory.json and the report")
    args = parser.parse_args(argv)

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: {root} is not a folder", file=sys.stderr)
        return 2
    extras = [e.expanduser().resolve() for e in args.extra]
    missing = [str(e) for e in extras if not e.is_dir()]
    if missing:
        print(f"error: not a folder: {', '.join(missing)}", file=sys.stderr)
        return 2
    transcripts = args.transcripts or args.home / ".claude" / "projects"
    data = build(root, args.home.expanduser(), transcripts.expanduser(), extras,
                 args.skill_budget, args.agent_budget)
    if not data["items"]:
        print("note: no skills or agents found; check --root, or add --extra", file=sys.stderr)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "inventory.json").write_text(json.dumps(data, indent=2) + "\n")
    (args.out / "inventory-report.md").write_text(report(data))
    totals = data["totals"]
    assert isinstance(totals, dict)
    print(f"{totals['items']} items, {len(data['findings'])} findings -> {args.out}")  # type: ignore[arg-type]
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
