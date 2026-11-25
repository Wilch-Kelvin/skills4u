# .wiki-health.json

Optional. Put it in the folder you audit (or pass `--config <file>`). Every
key is optional; anything you leave out keeps its built-in default.

```json
{
  "default": { "max_bytes": 12288, "max_lines": 300 },
  "types": {
    "hub":         { "kind": "hub", "max_bytes": 8000 },
    "log":         { "kind": "log", "max_bytes": 12000 },
    "log-archive": { "unbudgeted": true }
  },
  "rules": [
    { "match": "wiki/Knowledge/*", "kind": "note", "max_bytes": 20000 },
    { "match": "*.draft.md", "unbudgeted": true }
  ],
  "ignore": ["archive/*", "port/phase-*"],
  "inbox": ["0 Inbox/*"],
  "not_linked": ["agents/*", "*/agents/*", "templates/*", "*/templates/*"],
  "log_kinds": ["log"]
}
```

## How a file gets its budget

1. **`types`**: the note's frontmatter `type:` (for example `type: hub`). An
   explicit type wins over its path.
2. **`rules`**: your rules first, then the built-in ones; the first `match`
   wins. A pattern without `/` matches the file name anywhere (`SKILL.md`); a
   pattern with `/` matches the path from the audited folder (`docs/*`).
   Matching ignores case, and `*` also crosses folders.
3. **`default`**: everything else.

A rule or type without `max_lines` checks bytes only. `"unbudgeted": true`
means the file is never measured. Use it for archives and changelogs, which
are searched rather than read top to bottom.

## Built-in rules

| Match | Kind | Budget | Why |
|---|---|---|---|
| `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` | guide | 200 lines / 8 KB | An agent loads these every session |
| `SKILL.md` | skill | 500 lines / 20 KB | Loaded whenever the skill triggers; detail belongs in `references/` |
| `agents/*.md`, `*/agents/*.md` | agent | 12 KB | A subagent's whole system prompt |
| `CHANGELOG.md` | changelog | none | Append-only history |

Set `"builtin_rules": false` to drop them.

## Other keys

| Key | Meaning | Default |
|---|---|---|
| `ignore` | Files not measured or link-checked (links *to* them still resolve) | none |
| `inbox` | Notes waiting to be filed: listed, never called orphans | `inbox/*`, `*/inbox/*` |
| `not_linked` | Files nothing needs to link to (loaded by a harness, or copied) | agents, commands, templates folders |
| `log_kinds` | Kinds that get an `archive_plan` (newest-first `##` entries) | `["log"]` |

Lists you set replace the default list rather than adding to it.
