---
name: inventory-auditor
description: "Inventories the skills, subagents and hooks an agent can load, measures what each costs in context every turn and how often session transcripts show it used, flags duplicate, overlapping or vague triggers, and proposes keep, refactor, merge, defer or retire verdicts without changing anything. Use when the user asks to audit their skills or agents, asks which skills overlap, cost the most context or go unused, asks whether two skills are duplicates or should be merged, or whether to retire one, or says /inventory-auditor. For file sizes, orphans and broken links in docs or a wiki, use wiki-health instead."
---

# Inventory auditor

Read first, propose second. This skill never edits, deletes or disables a
skill, agent or hook; it writes a report and waits for the user's approval.

## 1. Measure (script)

```bash
python3 <this-skill-dir>/scripts/inventory.py --root <project> --out <scratch>/inventory
```

It reads `<project>/.claude/skills`, `<project>/.claude/agents`,
`<project>/.agents/skills`, `~/.claude/skills` and `~/.claude/agents`. Add
`--extra <folder>` (repeatable) for a plugin or any other skills folder: hosts
store installed plugins differently, so they aren't found automatically. Ask
which plugins matter if the user mentions them.

It writes `inventory.json` (shape: `references/schema.md`) and
`inventory-report.md`: every item, its description bytes (loaded every turn),
its body bytes against a budget (`SKILL.md` 20 KB, agents 12 KB; change with
`--skill-budget` / `--agent-budget`), duplicate names, hook events, and use
counts from Claude Code transcripts (`~/.claude/projects`) with their date
window. Don't re-measure anything it reports; read the JSON.

## 2. Judge (you, labelled as judgment)

For each pair of items whose descriptions could answer the same request:

1. Write 2 phrases that should route to A, 2 to B, and 2 near-misses that sit
   between them.
2. Say which item each phrase should reach and whether the descriptions make
   that clear. Only a pair that fails this is an overlap.

Also flag descriptions that don't say *when* to use the item, and, if a
transcript shows an item triggered but its rules were broken, quote the line
as possible instruction drift (low confidence).

## 3. Propose

Give every item its own row in one table, `| Item | Verdict | Evidence |
Change |`: exactly one verdict word, never two items in a row, and evidence
that is a number from `inventory.json` (bytes, budget %, uses) or a step 2
trigger result. Verdicts:

| Verdict | When |
|---|---|
| KEEP | Clear trigger, within budget, used or rare by design |
| REFACTOR | Useful, but vague or long description, or body near/over budget |
| MERGE | Overlap confirmed by step 2, not by similarity alone |
| DEFER | Should load on demand rather than every turn |
| RETIRE | Superseded, or unused *and* the user confirms it isn't rare by design |

`duplicate_name` findings come first: the same name twice for one agent means
it may load either copy. Zero uses is a question for the user, never a RETIRE
on its own: the transcript window may be short, and other agents' (Codex)
usage isn't counted. End with a numbered, reversible change list and the bytes
each change would save from the always-loaded total. Stop there.

## After approval

Apply only the approved items (on a branch in a git repo), then re-run step 1
and show the before and after totals.
