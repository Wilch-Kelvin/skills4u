# The Word document

File: `docs/<Project>-Documentation.docx`, built with a `.docx` skill or library
(see the skill's step 5).
Reader: someone who needs the whole picture (a reviewer, a new developer, a
lecturer or client, the author in six months).

## Sections

Keep only sections with real content, in this order. Lead each with a one- or
two-sentence summary, then the detail.

1. **Cover:** project name, tagline, version, date, the verified author.
2. **Contents.**
3. **Overview:** what it is, the problem, who it's for, current status.
4. **Features:** grouped by area; a table when platforms differ.
5. **Platforms and stack:** each platform, language, framework, key libraries,
   hosting. Table.
6. **Architecture:** components and how they connect. Diagram plus a short text
   description.
7. **Data:** what's stored, where, the main tables or models, the sync and
   offline model. Diagram if there's a schema.
8. **Key flows:** sign-in, sync, payments, release, whatever the project has.
   A diagram for each flow that crosses parts.
9. **Security and privacy:** auth, access rules (for example database
   row-level security), secrets handling, what data leaves the device.
10. **Getting started:** prerequisites with versions, then numbered setup and
    run steps, and the result you should see.
11. **Configuration:** env var names, required or optional, what each does.
12. **Testing and quality:** how to run the tests and checks, and what CI runs.
13. **Build and release:** how each platform ships; manual steps only the
    maintainer can do.
14. **Design:** brand colour, fonts, dark mode, from `DESIGN.md`, the token
    files or design notes.
15. **Decisions:** a short table of the important ones from the ADRs or
    design notes (ID, decision, why).
16. **Status, roadmap and known issues.**
17. **Appendix:** glossary, file map, links.

## Styling

- A4 or Letter, 2.5 cm (1 in) margins.
- Real styles: Title, Heading 1–3, Normal, Caption, a code style. Headings use
  the accent colour; body text stays near-black for contrast.
- Body font Aptos, Calibri or Arial at 10.5–11 pt; code in Consolas or Menlo.
  Brand fonts only if they will be embedded or the reader has them.
- Cover on its own page; contents next; each Heading 1 starts a new page in
  long documents.
- Header: project name. Footer: "Page X of Y".
- Tables: shaded header row that repeats across pages, rows that don't split,
  no wider than the text column.
- Callouts (Note, Important, Warning) as a shaded single-cell table, used
  rarely.
- Numbered lists restart where they should; bullets for parallel items.

## Graphics

- 1–4 diagrams usually; never decoration.
- PNG at 2× resolution, fitted to the text width, each with a numbered caption
  ("Figure 2: How sync works") and alt text.
- Sources stay in `docs/diagrams/` so they can be updated with the code.
- Screenshots only if they show something words can't; crop, remove personal
  data, add alt text.

## Visual QA

Render the `.docx` and look at every page: clipping, awkward breaks, a heading
alone at a page bottom, overflowing tables, unreadable diagram labels, missing
glyphs, uneven spacing, contrast. Fix and render again until clean. Don't
deliver or commit QA images.

**No Word or LibreOffice on the machine?** Don't install system software
unasked. Preview another way (for example `docx-preview` in headless Chrome,
then PDF to images) and say plainly that real Word page breaks, fields and
fonts are unchecked, and that `brew install --cask libreoffice` would allow a
true render.

Keep any build script and npm packages outside the repo (scratchpad) unless
the user asks to keep them for rebuilding.
