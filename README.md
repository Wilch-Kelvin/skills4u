# Skills

Claude Code skills and agents for two jobs that usually get rushed:
**documenting a project properly** and **designing UI that doesn't look like
a template**. They're general-purpose: drop them into any project, web or
mobile.

| Plugin | What you get | Use it for |
|---|---|---|
| [`project-documentation`](project-documentation/) | Skill: `project-documentation` | "Document this project", "write a README", "a Word doc about the app for my lecturer or client" |
| [`ui-ux`](ui-ux/) | Skill: `ui-ux-design`. Agents: `ui-ux-designer`, `ui-ux-reviewer` | "Design the onboarding", "this looks generic", "pick our colours", "review this screen" |

## Install

### As a Claude Code plugin (recommended)

In Claude Code, add this repo as a plugin marketplace, then install what you
want:

```text
/plugin marketplace add <github-user>/<repo>
```

```text
/plugin install project-documentation@kelvin-skills
```

```text
/plugin install ui-ux@kelvin-skills
```

Plugin skills are namespaced, so they may appear as
`project-documentation:project-documentation` and `ui-ux:ui-ux-design`.

### By hand

Clone the repo, then copy the folders you want into your user folder (all
projects) or a project's `.claude/` folder (that project only):

```bash
git clone https://github.com/<github-user>/<repo>.git
```

```bash
cp -R <repo>/project-documentation/skills/project-documentation ~/.claude/skills/
```

```bash
cp -R <repo>/ui-ux/skills/ui-ux-design ~/.claude/skills/ && cp <repo>/ui-ux/agents/*.md ~/.claude/agents/
```

The skills use the open `SKILL.md` format, so other tools that read Agent
Skills can load them too. The two agents are Claude Code subagent files.

## What each one does

### project-documentation

Writes two files into the project's `docs/` folder:

- `<Project>-Documentation.docx`: a full, professionally styled Word document
  (cover, contents, architecture, data, key flows, security, setup, testing,
  release, design, decisions, roadmap), with diagrams where they help.
- `README.md`: a GitHub-ready summary that links to the Word document.

It reads the repo first and never invents commands, env vars, features or
authors. It runs safe setup and test commands, renders every page of the Word
file to check the layout, and reports what it verified and what it couldn't.

Works best with a `.docx` skill installed (such as Anthropic's `docx` skill);
otherwise it falls back to `python-docx` or the `docx` npm package.

### ui-ux-design (skill)

A design rulebook the agent follows on every UI task:

1. **Find the project's design system first** (`DESIGN.md`,
   `design-system/MASTER.md`, token files, existing screens) and follow it.
2. **No system yet?** Propose three distinct directions (style family, brand
   colour, type pairing, signature detail), let you pick, and write
   `DESIGN.md` so every later session stays consistent.
3. **Build with tokens**, in light and dark, with every state (loading,
   empty, error, success).
4. **Check** with a priority-ranked checklist: accessibility, touch, layout,
   navigation, forms, type and colour, motion, performance, consistency,
   charts.
5. **Anti-generic pass:** name the template smells and give each screen at
   least one signature detail.

Includes a WCAG contrast checker (`scripts/contrast.py`), a palette preview
page, a `DESIGN.md` template, and notes for Next.js, React Native, SwiftUI and
Jetpack Compose.

### ui-ux-designer and ui-ux-reviewer (agents)

- **`ui-ux-designer`** plans the flow and mocks up screens (HTML, Figma when
  connected, or code), mobile first, light and dark.
- **`ui-ux-reviewer`** independently tests a running app, URL, mockup or
  screenshots. It can't edit your code, and it returns a scored report (Flow,
  Accessibility, Design-system fit, Distinctiveness) with findings ranked
  Blocker → Major → Minor → Polish, each with a concrete fix.

They work well as a loop: design, review, apply the top fixes, review again.

Optional extras the agents use when present: the Figma MCP server, a browser
tool for screenshots, and the iOS Simulator or Android emulator tools.

## Repo layout

```text
.claude-plugin/marketplace.json     lists both plugins
project-documentation/
  .claude-plugin/plugin.json
  skills/project-documentation/     SKILL.md, references/, evals/
ui-ux/
  .claude-plugin/plugin.json
  skills/ui-ux-design/              SKILL.md, references/, scripts/, assets/, evals/
  agents/                           ui-ux-designer.md, ui-ux-reviewer.md
```

Each skill has an `evals/evals.json` with example prompts and the expected
behaviour, so you can test it after changing it.

## Contributing

Issues and pull requests are welcome. Keep each `SKILL.md` short and put
detail in `references/`; when you change a skill's behaviour, update its evals.

## Credits

Created by Kelvin Wilch. The design checklist draws on WCAG 2.2, Apple's Human
Interface Guidelines and Material Design 3. Its priority-ranked structure and
the `DESIGN.md` / `design-system/` pattern were inspired by the open-source
UI UX Pro Max skill.

## Licence

[MIT](LICENSE)
