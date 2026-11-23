# Writing, formatting and accessibility

## Voice

- Plain, direct and respectful. Active voice, concrete verbs.
- Answer or result first, background after.
- One name per thing; define uncommon acronyms the first time.
- Sentence-case headings unless the project has its own style.
- Headings say what the section is for, are unique, and never skip a level.
- Short paragraphs. Lists for parallel items and steps. Tables only for
  comparable facts with clear headers, never for layout.
- Bold for a few labels or key terms; italics for titles. Never all caps,
  emoji as status, repeated warnings or meaning carried by colour alone.

## Code, commands and links

- Inline code for identifiers, filenames, paths, flags and literal values.
- Fenced blocks always carry a language tag.
- Placeholders look like placeholders: `<PROJECT_DIR>`. No real secrets.
- For a non-obvious command, say where to run it, what it does, what you should
  see and any platform assumption. Only use commands checked against the repo
  or the tool's own docs.
- Link text names the destination ("the setup guide", not "here"). Use
  relative links inside the repo, and check they resolve.
- Callouts: only Note, Warning or Important, only when there is a real
  consequence, and the text states the action or impact.

## Accessibility and graphics

- Real heading syntax in Markdown and heading styles in Word; never fake a
  hierarchy with font size.
- Logical reading order, selectable text, enough contrast, left-aligned prose.
- Alt text on informative images; decorative images add nothing.
- Diagrams get a caption and a short text description. Prefer Mermaid in
  repos so the diagram lives next to the code.
- Prefer text over screenshots of text, code or terminals. If a screenshot is
  needed, crop it to the task, remove personal data and keep it current.

## Sources

GitHub Docs style guide, Google developer documentation style guide and its
accessibility page, Google technical writing courses, Write the Docs, Microsoft
Writing Style Guide. Re-check them when a rule might have changed.
