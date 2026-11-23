---
name: project-documentation
description: Use when the user asks to document a project, "write the docs", "make the project documentation", "a Word doc about the project", "a README for GitHub", "explain the whole app", "the docs are out of date", or to prepare a handoff, review or submission copy. Produces two files in the project's docs/ folder, a professional, well-formatted Word document covering every aspect of the project (with diagrams where they help) and a GitHub README.md, both checked against the repo before they're written.
---

# Project documentation

**The job:** document a project as two files saved in its `docs/` folder.

| File | For | Guide |
|---|---|---|
| `docs/<Project>-Documentation.docx` | A complete, professional picture of the project: what, why, how it's built, how to run, ship and extend it | `references/word-document.md` |
| `docs/README.md` | GitHub visitors: what it is, how to run it, where to go next | `references/readme.md` |

Diagrams used in the Word file go in `docs/diagrams/` (source plus PNG).
Writing rules for both: `references/style.md`.

**The repo is the authority.** Never invent a command, env var, feature,
version, badge, licence, author or support channel. Leave out what you can't
verify, or mark it "unverified".

## Rules

- **Credit the real author.** Take it from the `LICENSE`, the manifest's
  `author` field, the existing README or the git history. If it's unclear,
  ask; never guess.
- **Accent colour:** the project's brand colour from `DESIGN.md`, its token
  files or its theme. With no brand, use a neutral dark blue and check it
  passes 4.5:1 on white. Body font: a safe sans everyone has (Aptos, Calibri
  or Arial).
- **Secrets:** env var *names* only, never values; point to `.env.example`.
- **Decisions:** summarise existing ADRs (`docs/adr/`, `docs/decisions/`) or
  design notes. Don't start an ADR folder unless asked.
- **Git:** follow the project's conventions. In a git repo, work on a branch
  (for example `docs/project-documentation`) unless told otherwise; make small
  commits; never push or open a pull request without asking.

## Workflow

### 1. Gather evidence
Read: any project notes the user points to (wiki, Notion export, design doc);
the repo's `README*`, `docs/`, `CLAUDE.md` / `AGENTS.md`, `DESIGN.md`;
manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, Gradle,
Xcode project); CI workflows; config and `.env.example`; schema or
migrations; the main source folders; `CHANGELOG` and recent git history. Note
what's stale in the existing docs as you go.

### 2. Outline the Word document
Start from the section list in `references/word-document.md` and keep only
sections with real content. Decide which 1–4 diagrams earn their place:
architecture almost always; a flow (sign-in, sync, payment, release) when
there is one; a data model when there's a schema.

### 3. Verify before writing
Run the setup and test commands when it's safe (a scratch database, no
network writes, nothing that costs money). Check every path and link. Record
which commands you ran and which you only read.

### 4. Build the diagrams
Write each as Mermaid or SVG in `docs/diagrams/<name>.mmd|.svg`, render it to
PNG (the Mermaid CLI, or headless Chrome when nothing else is installed), and
give each a caption and alt text. Use the accent colour and plain labels.

### 5. Build the Word document
Use a `.docx` skill if one is installed (for example Anthropic's `docx`
skill); otherwise generate it with `python-docx` or the `docx` npm package
from a scratch folder outside the repo. Follow the structure, styling and QA
rules in `references/word-document.md`: cover, contents, real heading styles,
page numbers, tables with header rows, embedded diagrams with captions.

### 6. Write the README
Follow `references/readme.md`. It summarises; the Word document carries the
depth. Link the README to the `.docx` and diagrams with relative links.

### 7. Check
- Render every page of the `.docx` to images and look at each one. Fix and
  re-render until clean (fallback when there's no renderer: see the reference).
- Check every link, path, command, env var name and version in both files.
- Preview the README as GitHub Markdown.
- Review the diff for unrelated changes. Don't commit QA images or build
  tools.

## Finish with

The two file paths (and diagrams), what was verified and how, what's
unverified, and anything stale found in the old docs.
