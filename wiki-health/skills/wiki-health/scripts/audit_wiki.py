#!/usr/bin/env python3
"""Measure a wiki or docs folder so an agent can plan fixes without reading it.

Why this exists: counting bytes, following every link and finding notes nobody
links to is slow and unreliable for a model, and reading 50 KB of notes to do
it burns the context the fixes need. This script does the counting and prints
JSON, plus a heading outline of every oversized file, so the plan can be
written from the report alone.

    python3 audit_wiki.py --dir ~/notes            # an Obsidian vault or wiki
    python3 audit_wiki.py --dir . --text           # a repo's docs, short summary

Budgets come from built-in defaults (agent context files such as CLAUDE.md
and SKILL.md get tighter ones, because an agent loads them often) or from an
optional .wiki-health.json in the audited folder; see references/config.md.

Python 3.9+, standard library only. It never edits a file.
"""
from __future__ import annotations

import argparse
import difflib
import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import unquote

# Folders that hold dependencies or build output, never documentation.
SKIP_DIRS = {
    "node_modules", "dist", "build", "out", "Pods", "vendor", "DerivedData",
    "target", "venv", ".venv", "__pycache__", "coverage",
}
# Dot-folders are tooling or generated copies (.git, .obsidian, ...), except
# the ones where agent skills and subagents live.
VISIBLE_DOT_DIRS = {".claude", ".agents", ".github"}
# Files a person or a harness opens directly, so nothing has to link to them.
ENTRYPOINTS = {
    "readme.md", "claude.md", "agents.md", "gemini.md", "index.md", "skill.md",
    "home.md", "changelog.md", "license.md", "contributing.md", "security.md",
    "code_of_conduct.md",
}
CONFIG_NAME = ".wiki-health.json"

WATCH_RATIO = 0.85     # flag a file at 85% of its budget before it goes over
ARCHIVE_RATIO = 0.8    # archive a log until what stays is ~80% of its budget
OUTLINE_LIMIT = 40     # cap the outline so a 60-entry log stays readable

# Built-in budgets. A `match` without "/" matches the file name anywhere;
# with "/" it matches the path from the audited folder. First match wins.
# Agent context files are tight because an agent may load them on every task.
DEFAULT_CONFIG: Dict[str, Any] = {
    "default": {"max_bytes": 12_288, "max_lines": 300},
    "rules": [
        {"match": "CLAUDE.md", "kind": "guide", "max_bytes": 8_000, "max_lines": 200},
        {"match": "AGENTS.md", "kind": "guide", "max_bytes": 8_000, "max_lines": 200},
        {"match": "GEMINI.md", "kind": "guide", "max_bytes": 8_000, "max_lines": 200},
        {"match": "SKILL.md", "kind": "skill", "max_bytes": 20_000, "max_lines": 500},
        {"match": "agents/*.md", "kind": "agent", "max_bytes": 12_000},
        {"match": "*/agents/*.md", "kind": "agent", "max_bytes": 12_000},
        {"match": "CHANGELOG.md", "kind": "changelog", "unbudgeted": True},
    ],
    "types": {},
    "ignore": [],
    # Loaded by the harness (subagents, slash commands) or copied (templates).
    "not_linked": ["agents/*", "*/agents/*", "commands/*", "*/commands/*",
                   "templates/*", "*/templates/*"],
    "inbox": ["inbox/*", "*/inbox/*"],
    "log_kinds": ["log"],
}

FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
WIKILINK_RE = re.compile(r"\[\[([^\]\n]+)\]\]")
# [text](target) or [text](<target with spaces>), with an optional "title".
MD_LINK_RE = re.compile(r"\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^)\s]+)(?:\s+[\"'][^)\n]*[\"'])?\s*\)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
PATH_MENTION_RE = re.compile(r"^[~\w./@ -]+\.md$")


# ---------------------------------------------------------------- reading


@dataclass
class Note:
    rel: str                  # path from the root, with forward slashes
    path: Path
    text: str
    prose: str                # text with code blanked out, same line numbers
    mentions: List[str]       # `some/file.md` paths written in inline code
    note_type: str
    headings: List[Tuple[int, str, int]]  # (level, text, byte offset)

    @property
    def size(self) -> int:
        return len(self.text.encode("utf-8"))

    @property
    def lines(self) -> int:
        return len(self.text.splitlines())


def frontmatter_type(text: str) -> str:
    """The `type:` property, which can set a note's budget via config `types`."""
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        return ""
    found = re.search(r"^type:\s*(.+?)\s*$", match.group(1), re.MULTILINE)
    return found.group(1).strip("\"'") if found else ""


def strip_code(text: str) -> Tuple[str, List[str]]:
    """Blank out code so example links aren't read as real ones.

    Line numbers are kept (code becomes spaces, not nothing) so a broken link
    can be reported at its real line. Inline code is returned separately,
    because skills point at their references as `references/x.md`.
    """
    out: List[str] = []
    mentions: List[str] = []
    in_fence = False
    for line in text.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        mentions.extend(m.strip() for m in INLINE_CODE_RE.findall(line))
        out.append(INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line))
    return "\n".join(out), [m for m in mentions if PATH_MENTION_RE.match(m)]


def find_headings(text: str, prose: str) -> List[Tuple[int, str, int]]:
    """Headings outside code, with byte offsets into the original text."""
    headings: List[Tuple[int, str, int]] = []
    offset = 0
    for original, cleaned in zip(text.split("\n"), prose.split("\n")):
        match = HEADING_RE.match(cleaned)
        if match:
            headings.append((len(match.group(1)), match.group(2), offset))
        offset += len((original + "\n").encode("utf-8"))
    return headings


def read_note(root: Path, path: Path) -> Note:
    text = path.read_text(encoding="utf-8", errors="replace")
    prose, mentions = strip_code(text)
    return Note(
        rel=path.relative_to(root).as_posix(), path=path, text=text, prose=prose,
        mentions=mentions, note_type=frontmatter_type(text), headings=find_headings(text, prose),
    )


def is_copy(folder: Path) -> bool:
    """A git worktree or submodule: its `.git` is a file, not a folder.

    Claude Code puts worktrees in .claude/worktrees/, and they hold a second
    copy of every doc, so auditing them would report each problem twice.
    """
    return folder.name == "worktrees" and folder.parent.name == ".claude" or (folder / ".git").is_file()


def ignored(rel: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel, p.rstrip("/") + "/*") for p in patterns)


def walk(root: Path) -> Tuple[List[Path], Set[str]]:
    """Markdown files, plus the names of every other file (for ![[image.png]]).

    os.walk lets us prune node_modules before entering it; rglob would not.
    Symlinked folders are skipped so a linked copy isn't counted twice
    (for example .claude/agents linked to a top-level agents/ folder).
    """
    notes: List[Path] = []
    assets: Set[str] = set()
    for folder, dirs, files in os.walk(root):
        here = Path(folder)
        dirs[:] = sorted(
            d for d in dirs
            if d not in SKIP_DIRS
            and (not d.startswith(".") or d in VISIBLE_DOT_DIRS)
            and not (here / d).is_symlink()
            and not is_copy(here / d)
        )
        for name in sorted(files):
            path = here / name
            if path.is_symlink():
                continue
            if name.lower().endswith(".md"):
                notes.append(path)
            else:
                assets.add(name.lower())
    return notes, assets


# ---------------------------------------------------------------- budgets


@dataclass(frozen=True)
class Budget:
    max_bytes: Optional[int]   # None: never read top to bottom, so no budget
    max_lines: Optional[int]
    kind: str                  # which rule set the budget, shown in the report


def matches(rel: str, pattern: str) -> bool:
    """Case-insensitive glob. No "/" in the pattern: match the file name anywhere."""
    rel, pattern = rel.lower(), pattern.lower()
    if "/" not in pattern:
        return fnmatch.fnmatch(rel.rsplit("/", 1)[-1], pattern)
    return fnmatch.fnmatch(rel, pattern)


def load_config(root: Path, path: Optional[Path]) -> Tuple[Dict[str, Any], str]:
    """Built-in defaults, overlaid by .wiki-health.json if there is one.

    The user's `rules` are checked before the built-in ones (so they win);
    `"builtin_rules": false` drops the built-ins. Other keys replace defaults.
    """
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    source = path or root / CONFIG_NAME
    if not source.is_file():
        if path is not None:
            raise SystemExit(f"config file not found: {path}")
        return config, "built-in defaults"
    try:
        user = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"{source} is not valid JSON: {error}") from error
    if not isinstance(user, dict):
        raise SystemExit(f"{source} must hold a JSON object")
    builtin = config["rules"] if user.pop("builtin_rules", True) else []
    config["rules"] = list(user.pop("rules", [])) + builtin
    if "default" in user:
        config["default"].update(user.pop("default"))
    config.update(user)
    return config, str(source)


def budget_for(config: Dict[str, Any], note: Note) -> Budget:
    """Frontmatter `type` first (it's explicit), then path rules, then the default."""
    default = config["default"]
    rule: Optional[Dict[str, Any]] = config["types"].get(note.note_type) if note.note_type else None
    kind = note.note_type
    if rule is None:
        rule = next((r for r in config["rules"] if matches(note.rel, r["match"])), None)
        kind = "file"
    if rule is None:
        return Budget(default.get("max_bytes"), default.get("max_lines"), "file")
    kind = rule.get("kind", kind)
    if rule.get("unbudgeted"):
        return Budget(None, None, kind)
    # A rule without max_lines checks bytes only; without max_bytes, the default.
    return Budget(rule.get("max_bytes", default.get("max_bytes")), rule.get("max_lines"), kind)


def remedy_for(kind: str, log_kinds: List[str]) -> str:
    """The usual fix for this kind of file when it's too big."""
    if kind in log_kinds:
        return "archive: move the oldest entries, word for word, to an archive note"
    if kind in ("hub", "index", "moc", "project"):
        return "move-detail: move detail into linked feature notes; keep the hub short"
    if kind == "skill":
        return "move-to-references: keep the steps in SKILL.md, move detail to references/"
    if kind in ("guide", "agent"):
        return "trim: these load on every task, so cut or move rules into a skill"
    return "split: break at its headings into a short router note plus linked parts"


# ---------------------------------------------------------------- outlines


def outline(note: Note) -> List[Dict[str, object]]:
    """Top-level sections with their sizes, so a split can be planned unread."""
    level = 2 if any(h[0] == 2 for h in note.headings) else 1
    marks = [h for h in note.headings if h[0] == level]
    ends = [m[2] for m in marks[1:]] + [note.size]
    sections = [{"heading": m[1], "bytes": end - m[2]} for m, end in zip(marks, ends)]
    if len(sections) > OUTLINE_LIMIT:
        hidden = sections[OUTLINE_LIMIT:]
        sections = sections[:OUTLINE_LIMIT] + [{
            "heading": f"... {len(hidden)} more sections",
            "bytes": sum(int(s["bytes"]) for s in hidden),
        }]
    return sections


def archive_plan(note: Note, target: int) -> Optional[Dict[str, object]]:
    """Where to cut a newest-first log so what stays is about `target` bytes."""
    entries = [h for h in note.headings if h[0] == 2]
    if len(entries) < 2:
        return None
    keep = 1  # always keep the newest entry, however long it is
    while keep < len(entries):
        end = entries[keep + 1][2] if keep + 1 < len(entries) else note.size
        if end > target:
            break
        keep += 1
    if keep == len(entries):
        return None
    cut = entries[keep][2]
    return {
        "keep_entries": keep,
        "move_entries": len(entries) - keep,
        "first_heading_to_move": entries[keep][1],
        "bytes_after": cut,
        "bytes_moved": note.size - cut,
    }


# ---------------------------------------------------------------- links


@dataclass
class Index:
    by_rel: Dict[str, Note]
    by_path: Dict[str, str]             # "docs/setup" -> rel
    by_name: Dict[str, List[str]]       # "setup" -> [rels]
    assets: Set[str]                    # lower-case names of non-Markdown files
    asset_stems: Set[str] = field(default_factory=set)


def build_index(notes: List[Note], assets: Set[str]) -> Index:
    by_name: Dict[str, List[str]] = {}
    for note in notes:
        by_name.setdefault(Path(note.rel).stem.lower(), []).append(note.rel)
    return Index(
        by_rel={n.rel: n for n in notes},
        by_path={n.rel[:-3].lower(): n.rel for n in notes},
        by_name=by_name,
        assets=assets,
        asset_stems={Path(a).stem for a in assets},
    )


def norm_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def github_slug(text: str) -> str:
    """How GitHub turns a heading into a #fragment, for [text](file.md#frag)."""
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


def has_anchor(note: Note, anchor: str) -> bool:
    if anchor.startswith("^"):
        return True  # block references aren't headings; not checked
    wanted = norm_heading(anchor.split("#")[-1])  # [[Note#A#B]] targets B
    for _level, text, _offset in note.headings:
        if norm_heading(text) == wanted or github_slug(text) == wanted:
            return True
    return False


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def suggest(index: Index, target: str, source: Note) -> Optional[str]:
    """A close note name, given as a relative path from the source's folder."""
    stem = Path(target).stem.lower()
    match = difflib.get_close_matches(stem, list(index.by_name), n=1, cutoff=0.75)
    if not match:
        return None
    candidate = index.by_name[match[0]][0]
    return os.path.relpath(candidate, Path(source.rel).parent.as_posix() or ".")


@dataclass
class LinkResults:
    incoming: Dict[str, Set[str]]
    broken: List[Dict[str, object]] = field(default_factory=list)
    anchors: List[Dict[str, object]] = field(default_factory=list)
    ambiguous: List[Dict[str, object]] = field(default_factory=list)

    def link(self, source: Note, target_rel: str) -> None:
        if target_rel != source.rel:  # a note linking to itself isn't connected
            self.incoming[target_rel].add(source.rel)


def check_wikilinks(note: Note, index: Index, out: LinkResults) -> None:
    for match in WIKILINK_RE.finditer(note.prose):
        # In a table the alias pipe is escaped (\|) so it doesn't end the cell.
        inner = re.split(r"\\?\|", match.group(1), maxsplit=1)[0]
        target, _, anchor = inner.partition("#")
        target = target.strip()
        line = line_of(note.prose, match.start())
        key = target.lower()
        key = key[:-3] if key.endswith(".md") else key
        if not target:  # [[#Heading]] points inside this note
            if anchor and not has_anchor(note, anchor):
                out.anchors.append({"source": note.rel, "line": line, "target": match.group(0), "anchor": anchor})
            continue
        if key in index.by_path:
            hits = [index.by_path[key]]
        else:
            hits = index.by_name.get(key, [])
        if not hits:
            if key in index.assets or key in index.asset_stems:
                continue  # ![[Projects.base]] or ![[diagram.png]]
            out.broken.append({
                "source": note.rel, "line": line, "target": match.group(0),
                "kind": "wikilink", "suggestion": suggest(index, target, note),
            })
            continue
        if len(hits) > 1:
            out.ambiguous.append({"source": note.rel, "line": line, "target": match.group(0), "candidates": hits})
        for hit in hits:
            out.link(note, hit)
        if anchor and len(hits) == 1 and not has_anchor(index.by_rel[hits[0]], anchor):
            out.anchors.append({"source": note.rel, "line": line, "target": match.group(0), "anchor": anchor})


def resolve_path(root: Path, note: Note, raw: str) -> Optional[Path]:
    """Relative to the note first, then to the root (Obsidian allows both)."""
    for base in (note.path.parent, root):
        candidate = (base / raw.lstrip("/")).resolve()
        if candidate.exists():
            return candidate
    return None


def check_markdown_links(root: Path, note: Note, index: Index, out: LinkResults) -> None:
    for match in MD_LINK_RE.finditer(note.prose):
        raw = match.group(1).strip("<>")
        if SCHEME_RE.match(raw):
            continue  # http:, mailto:, obsidian: and friends aren't files
        path_part, _, anchor = raw.partition("#")
        line = line_of(note.prose, match.start())
        target_note: Optional[Note] = note
        if path_part:
            found = resolve_path(root, note, unquote(path_part))
            if found is None:
                out.broken.append({
                    "source": note.rel, "line": line, "target": raw,
                    "kind": "markdown", "suggestion": suggest(index, unquote(path_part), note),
                })
                continue
            rel = found.relative_to(root).as_posix() if found.is_relative_to(root) else ""
            target_note = index.by_rel.get(rel)
            if target_note is not None:
                out.link(note, rel)
        if anchor and target_note is not None and not has_anchor(target_note, anchor):
            out.anchors.append({"source": note.rel, "line": line, "target": raw, "anchor": anchor})


def check_mentions(root: Path, note: Note, index: Index, out: LinkResults) -> None:
    """`references/x.md` in a SKILL.md is how skills load files; count it as a link."""
    for mention in note.mentions:
        clean = mention.lstrip("~/")
        found = resolve_path(root, note, clean)
        if found is not None and found.is_relative_to(root):
            rel = found.relative_to(root).as_posix()
            if rel in index.by_rel:
                out.link(note, rel)
                continue
        # `~/notes/wiki/X.md` names a note in this folder by its full path.
        for rel in index.by_rel:
            if clean.endswith("/" + rel):
                out.link(note, rel)


# ---------------------------------------------------------------- report


def nearest_hub(rel: str, index: Index) -> str:
    """The note a person would expect to link here: the folder's own hub."""
    folder = Path(rel).parent
    while True:
        prefix = "" if folder == Path(".") else f"{folder.as_posix()}/"
        siblings = [r for r in index.by_rel if r.startswith(prefix) and "/" not in r[len(prefix):]]
        # Folder notes often carry a prefix: "UI Diff/" may hold
        # "Acme UI Diff.md", so match on the end of the name.
        named = sorted(r for r in siblings if folder.name and Path(r).stem.endswith(folder.name))
        for candidate in named + [prefix + n for n in ("README.md", "index.md", "Home.md")]:
            if candidate in index.by_rel and candidate != rel:
                return candidate
        if folder == Path("."):
            break
        folder = folder.parent
    return "CLAUDE.md" if "CLAUDE.md" in index.by_rel else "README.md"


def in_any(rel: str, patterns: List[str]) -> bool:
    return any(matches(rel, p) for p in patterns)


def audit(
    root: Path,
    config: Optional[Dict[str, Any]] = None,
    ignore: Optional[List[str]] = None,
    config_source: str = "built-in defaults",
) -> Dict[str, object]:
    config = config if config is not None else load_config(root, None)[0]
    log_kinds: List[str] = list(config["log_kinds"])

    # Ignored files are not measured, but links to them still resolve.
    paths, assets = walk(root)
    notes = [read_note(root, p) for p in paths]
    index = build_index(notes, assets)
    patterns = list(config["ignore"]) + list(ignore or [])
    skipped = {n.rel for n in notes if ignored(n.rel, patterns)}
    measured = [n for n in notes if n.rel not in skipped]

    oversized: List[Dict[str, object]] = []
    near: List[Dict[str, object]] = []
    for note in measured:
        budget = budget_for(config, note)
        if budget.max_bytes is None:
            continue
        over_bytes = note.size > budget.max_bytes
        over_lines = budget.max_lines is not None and note.lines > budget.max_lines
        if over_bytes or over_lines:
            entry: Dict[str, object] = {
                "file": note.rel, "kind": budget.kind, "bytes": note.size, "lines": note.lines,
                "est_tokens": note.size // 4, "budget_bytes": budget.max_bytes,
                "budget_lines": budget.max_lines,
                "over_by_bytes": max(0, note.size - budget.max_bytes),
                "remedy": remedy_for(budget.kind, log_kinds), "outline": outline(note),
            }
            if budget.kind in log_kinds:
                entry["archive_plan"] = archive_plan(note, int(budget.max_bytes * ARCHIVE_RATIO))
            oversized.append(entry)
        elif note.size >= budget.max_bytes * WATCH_RATIO:
            near.append({"file": note.rel, "bytes": note.size, "budget_bytes": budget.max_bytes,
                         "percent": round(100 * note.size / budget.max_bytes)})

    links = LinkResults(incoming={n.rel: set() for n in notes})
    for note in notes:
        check_wikilinks(note, index, links)
        check_markdown_links(root, note, index, links)
        check_mentions(root, note, index, links)

    orphans = [
        {"file": n.rel, "type": n.note_type, "suggested_hub": nearest_hub(n.rel, index)}
        for n in measured
        if Path(n.rel).name.lower() not in ENTRYPOINTS
        and not in_any(n.rel, config["not_linked"])
        and not in_any(n.rel, config["inbox"])
        and not links.incoming[n.rel]
    ]
    inbox = [n.rel for n in measured if in_any(n.rel, config["inbox"])]
    for found in (links.broken, links.anchors, links.ambiguous):
        found[:] = [f for f in found if f["source"] not in skipped]

    flagged = {e["file"] for e in oversized} | {o["file"] for o in orphans}
    flagged |= {b["source"] for b in links.broken}
    return {
        "scanned_root": str(root),
        "config": config_source,
        "default_budget": config["default"],
        "summary": {
            "files": len(measured), "healthy": len(measured) - len(flagged), "ignored": len(skipped),
            "oversized": len(oversized), "near_budget": len(near), "orphans": len(orphans),
            "broken_links": len(links.broken), "broken_anchors": len(links.anchors),
            "ambiguous_links": len(links.ambiguous), "inbox": len(inbox),
        },
        "oversized": sorted(oversized, key=lambda e: -int(e["over_by_bytes"])),
        "near_budget": sorted(near, key=lambda e: -int(e["percent"])),
        "orphans": orphans,
        "inbox": inbox,
        "broken_links": links.broken,
        "broken_anchors": links.anchors,
        "ambiguous_links": links.ambiguous,
    }


def as_text(report: Dict[str, object]) -> str:
    """A short human summary; agents should read the JSON instead."""
    s = report["summary"]
    assert isinstance(s, dict)
    lines = [f"{s['files']} files · {s['healthy']} healthy · budgets: {report['config']}"]
    for e in report["oversized"]:  # type: ignore[union-attr]
        lines.append(f"  oversized  {e['file']}  {e['bytes']:,} B (budget {e['budget_bytes']:,})")
    for e in report["near_budget"]:  # type: ignore[union-attr]
        lines.append(f"  near       {e['file']}  {e['percent']}% of budget")
    for e in report["orphans"]:  # type: ignore[union-attr]
        lines.append(f"  orphan     {e['file']}  -> link from {e['suggested_hub']}")
    for e in report["broken_links"]:  # type: ignore[union-attr]
        hint = f"  (did you mean {e['suggestion']}?)" if e["suggestion"] else ""
        lines.append(f"  broken     {e['source']}:{e['line']}  {e['target']}{hint}")
    for e in report["broken_anchors"]:  # type: ignore[union-attr]
        lines.append(f"  anchor     {e['source']}:{e['line']}  {e['target']}")
    for e in report["ambiguous_links"]:  # type: ignore[union-attr]
        lines.append(f"  ambiguous  {e['source']}:{e['line']}  {e['target']}")
    for rel in report["inbox"]:  # type: ignore[union-attr]
        lines.append(f"  inbox      {rel}  (waiting to be filed)")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", default=".", help="folder to audit (default: here)")
    parser.add_argument("--config", type=Path, default=None,
                        help=f"budget file (default: <dir>/{CONFIG_NAME} if present)")
    parser.add_argument("--max-lines", type=int, default=None, help="override the default line budget")
    parser.add_argument("--max-bytes", type=int, default=None, help="override the default byte budget")
    parser.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                        help="skip files or folders, e.g. 'archive/*' (repeatable)")
    parser.add_argument("--text", action="store_true", help="print a short summary, not JSON")
    parser.add_argument("--strict", action="store_true", help="exit 1 if anything is flagged")
    args = parser.parse_args(argv)

    root = Path(args.dir).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"not a folder: {root}")
    config, source = load_config(root, args.config.expanduser() if args.config else None)
    if args.max_lines is not None:
        config["default"]["max_lines"] = args.max_lines
    if args.max_bytes is not None:
        config["default"]["max_bytes"] = args.max_bytes
    report = audit(root, config, args.ignore, source)
    print(as_text(report) if args.text else json.dumps(report, indent=2, ensure_ascii=False))
    s = report["summary"]
    assert isinstance(s, dict)
    problems = s["oversized"] + s["orphans"] + s["broken_links"] + s["broken_anchors"]
    return 1 if args.strict and problems else 0


if __name__ == "__main__":
    sys.exit(main())
