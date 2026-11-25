# inventory.json schema (v1)

Written by `scripts/inventory.py`. One file per run; nothing else is changed.

```jsonc
{
  "schema_version": 1,
  "generated_at": "2026-11-24T20:00:00Z",      // UTC, ISO 8601
  "root": "/path/to/project",
  "transcripts": {
    "files": 95,                                // .jsonl files read
    "first": "2026-11-05T00:02:17Z",            // earliest timestamp seen, or null
    "last": "2026-11-24T19:58:01Z",             // latest timestamp seen, or null
    "host": "claude-code",                      // Codex usage is not in these files
    "skipped": 0,                               // files found but unreadable
    "error": null                               // why no transcripts were read; usage is then unknown, not zero
  },
  "totals": {
    "items": 21,
    "always_loaded_bytes": 9120,                // sum of description_bytes: paid every turn
    "always_loaded_tokens_est": 2280            // bytes / 4, an estimate, not a tokenizer count
  },
  "items": [Item],
  "hooks": [Hook],
  "findings": [Finding]
}
```

## Item

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `<kind>:<name>`, plus `@<source>` when the name appears more than once |
| `kind` | `"skill"` \| `"agent"` | What the host loads |
| `name` | string | Frontmatter `name`, else the folder or file name |
| `source` | string | `project`, `project-agents` (`.agents/skills`), `user`, or `extra:<folder>` |
| `host` | `"claude"` \| `"agents"` | Which agent loads it: Claude Code, or agents using `.agents/skills` (Codex and others) |
| `path` | string | Path of the `SKILL.md` or agent file |
| `description` | string | Frontmatter `description` (empty if missing) |
| `description_bytes` | int | UTF-8 bytes of `description`; loads every turn |
| `body_bytes` | int | Whole file; loads only when the item triggers |
| `budget_bytes` | int | `--skill-budget` (20,000) or `--agent-budget` (12,000) |
| `budget_ratio` | float | `body_bytes / budget_bytes`, 2 decimals |
| `resources` | string[] | Sub-folders present: `references`, `scripts`, `assets`, `evals` |
| `sha256` | string | First 12 hex digits of the file's hash, to spot drifted copies |
| `usage` | Usage | Pass 3 |

A symlink to a file already listed is skipped, so linked copies count once.

## Usage

| Field | Type | Meaning |
|---|---|---|
| `tool_calls` | int | `Skill` calls (`input.skill`) or `Agent` calls (`input.subagent_type`) naming this item |
| `typed` | int | `<command-name>/name</command-name>` in user turns |
| `last_used` | string \| null | Latest timestamp of either |

A namespaced call such as `my-plugin:review` counts for `review` when no item
has the full name. Items sharing a name share their counts, because the
transcript can't say which copy ran.

## Hook

```jsonc
{ "event": "PreToolUse", "source": "/path/.claude/settings.json", "matcher": "Bash", "commands": 1 }
```

Read from `~/.claude/settings.json`, `<project>/.claude/settings.json`,
`<project>/.claude/settings.local.json` and `<extra>/hooks/hooks.json`.

## Finding

| Field | Type | Meaning |
|---|---|---|
| `rule` | string | One of the rules below |
| `item` | string | Item `id` |
| `severity` | `"high"` \| `"medium"` \| `"low"` | |
| `evidence` | string | The number or fact behind it |
| `decided_by` | `"script"` | Findings the model adds in steps 2–3 say `"model"` |

| Rule | Severity | When |
|---|---|---|
| `missing_description` | high | No description: the item can't be routed to |
| `description_over_limit` | high | Description over 1,024 characters (Agent Skills limit) |
| `duplicate_name` | high | Same kind and name twice for one host: it may load either |
| `over_budget` | high | `budget_ratio` > 1.0 |
| `copies_differ` | low | Copies for different hosts differ; often intended (for example `CLAUDE.md` → `AGENTS.md`) |
| `near_budget` | low | `budget_ratio` ≥ 0.85 |
| `unused_in_window` | low | No calls in the transcript window. A question, never a verdict |
