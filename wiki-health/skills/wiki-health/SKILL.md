---
name: wiki-health
description: Use when the user asks to audit, health-check or tidy a Markdown wiki, an Obsidian vault, a docs folder or a repo's agent files (CLAUDE.md, AGENTS.md, SKILL.md), or asks "which notes are too long?", "is this file over budget?", "find orphaned notes", "find broken links", "what needs splitting?" or "/wiki-health". Runs a bundled script that measures every Markdown file against a size budget, finds notes nothing links to and broken links or headings, then writes a numbered fix plan and changes nothing until the user approves it.
---

# Wiki health

**The job:** measure, don't read. The script does the counting and
link-following (fast and exact). You read its JSON and write a fix plan from
it, opening a file only when the JSON can't tell you enough. **No edits until
the user approves.**

## 1. Run the audit

```bash
python3 <this-skill-dir>/scripts/audit_wiki.py --dir <folder>
```

- **Budgets.** Without a config, every Markdown file gets 300 lines / 12 KB
  (about 3,000 tokens). Agent context files get tighter budgets because an
  agent loads them often: `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` 200 lines /
  8 KB, `SKILL.md` 500 lines / 20 KB, subagent files 12 KB. `CHANGELOG.md` is
  never budgeted.
- **The folder's own rules.** If it has a `.wiki-health.json`, the script uses
  it (budgets by path or by frontmatter `type:`, ignore globs, inbox and
  template folders). Format: `references/config.md`. If the user states limits
  but has no config, pass `--max-lines` / `--max-bytes`, or offer to write one.
- **History docs** (dated plans, old reports, archives) are read on purpose,
  never loaded as context. If they swamp the report, rerun with
  `--ignore 'archive/*'` (repeatable) and say what you ignored.

Add `--text` for a quick human summary; read the JSON yourself.

## 2. Read only what the JSON doesn't tell you

| Report key | What it gives you | Open the file? |
|---|---|---|
| `oversized` | size, budget, `kind`, a `remedy`, an `outline` of sections with their bytes; logs also get an `archive_plan` (where to cut, how much moves) | Only to name split parts the outline doesn't make obvious. Use `grep -n '^#'`, not a full read |
| `near_budget` | files at 85%+ of their budget | No |
| `orphans` | notes nothing links to, with a `suggested_hub` | The first 15 lines, to see if it's current or obsolete |
| `inbox` | notes in an inbox folder, waiting to be filed | The first 15 lines |
| `broken_links` | source, line, target and a close-match `suggestion` | Only if there's no suggestion |
| `broken_anchors` | `[[Note#Heading]]` or `file.md#frag` pointing at a heading that isn't there | `grep -n '^#'` the target |
| `ambiguous_links` | `[[Name]]` matching more than one note | No |

Links inside code are ignored. A `` `references/x.md` `` path in inline code
counts as a link, because that's how skills point at their files.

## 3. Write the report

Four sections, in this order, short and specific.

### 1. Health summary
One line: files scanned, healthy, oversized, near budget, orphans, broken
links and anchors, inbox, and which budgets were used (`config`).

### 2. Oversized files
For each: path, bytes and lines against budget, estimated tokens, and a fix
that follows its `remedy`:

- **archive** (logs): move the entries from `first_heading_to_move` down,
  **word for word**, to the top of an archive note next to it (for example
  `<Name> Archive.md`), keeping `keep_entries` in the log.
- **move-detail** (hubs, indexes): name the sections that move into which new
  linked notes, and what stays in the hub.
- **move-to-references** (`SKILL.md`): keep the steps; name which sections move
  to `references/`.
- **trim** (`CLAUDE.md`, `AGENTS.md`, subagents): these load on every task.
  Name the rules to cut or move into a skill.
- **split** (anything else): split at the outline's headings into a short
  router note (under 150 lines) plus linked parts, giving every new file name.

Follow the folder's naming style for new files. List `near_budget` files in
one line as a watch list.

### 3. Disconnected and broken links
- **Orphans:** for each, the exact line to add to its `suggested_hub`, or, if
  it's obsolete, where to archive it.
- **Inbox:** where each note should be filed.
- **Broken links and anchors:** source:line, what it points at, the corrected
  link. If nothing close exists, say so and ask.

### 4. Execution checklist
A numbered list, one edit per step, most valuable first (shrinking files read
on every task beats tidying a rarely opened note), so the user can say "do 1
and 3" or "apply all".

## 4. After the user approves

- Do only the approved steps. In a git repo, work on a branch.
- Never delete a note: archive or link it instead. Move archived text word
  for word.
- Rerun the audit and show the summary line before and after.
