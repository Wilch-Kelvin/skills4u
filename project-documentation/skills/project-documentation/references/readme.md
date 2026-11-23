# The GitHub README

File: `docs/README.md`. Reader: someone who just found the repo on GitHub.
The first screen answers: what is this, who is it for, how do I try it.

**Where GitHub shows it:** GitHub displays the first README it finds in
`.github/`, then the repo root, then `docs/`. If the repo already has a root
`README.md`, `docs/README.md` won't be the front page. Don't delete the root
one: tell the user, and offer to replace it or make it a short pointer to
`docs/README.md`.

## Order

1. Name and a one-sentence summary.
2. Badges only if real and current (CI, licence, version).
3. The problem, who it's for, key features (short list).
4. One screenshot or diagram only if it really helps, with alt text.
5. Platforms and stack, in one line or a small table.
6. Prerequisites and tested versions.
7. Quickstart: exact install, config and run commands, and what you should see.
8. Configuration: env var names and whether each is required; point to
   `.env.example`. Never values.
9. Tests and checks.
10. Documentation: link the Word document
    (`[Full project documentation](<Project>-Documentation.docx)`) and the
    diagrams.
11. Contributing, support, security reporting and licence, only when
    confirmed.
12. Credits: the verified author or team.

Keep it short: the Word document carries the depth. Links are relative to
`docs/` (for example `../package.json`). Preview it rendered as GitHub
Markdown before finishing.
