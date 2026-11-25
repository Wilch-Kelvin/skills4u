"""Tests for audit_wiki.py. Standard library only, like the script.

    python3 -m unittest discover -s wiki-health/skills/wiki-health/scripts
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Dict, List, Optional

from audit_wiki import DEFAULT_CONFIG, audit, load_config, main


class Folder:
    """A throwaway folder built from {path: text}."""

    def __init__(self, files: Dict[str, str]) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(text), encoding="utf-8")

    def run(self, max_lines: int = 300, max_bytes: int = 12_288,
            ignore: Optional[List[str]] = None) -> dict:
        config, source = load_config(self.root, None)
        config["default"] = {"max_lines": max_lines, "max_bytes": max_bytes}
        return audit(self.root, config, ignore, source)

    def close(self) -> None:
        self._tmp.cleanup()


def files_of(entries: list) -> set:
    return {e["file"] for e in entries}


class Measuring(unittest.TestCase):
    def test_flags_files_over_the_line_or_byte_limit(self) -> None:
        folder = Folder({
            "README.md": "[a](docs/long.md) [b](docs/wide.md) [c](docs/ok.md)\n",
            "docs/long.md": "line\n" * 50,
            "docs/wide.md": "x" * 600,
            "docs/ok.md": "fine\n",
        })
        report = folder.run(max_lines=20, max_bytes=500)
        folder.close()
        self.assertEqual(report["config"], "built-in defaults")
        self.assertEqual(files_of(report["oversized"]), {"docs/long.md", "docs/wide.md"})

    def test_orphans_ignore_entrypoints_and_self_links(self) -> None:
        folder = Folder({
            "README.md": "[guide](guide.md)\n",
            "guide.md": "# Guide\n",
            "lonely.md": "[[lonely]] links only to itself\n",
            ".claude/skills/x/SKILL.md": "loaded by the harness\n",
        })
        report = folder.run()
        folder.close()
        self.assertEqual(files_of(report["orphans"]), {"lonely.md"})

    def test_markdown_links(self) -> None:
        folder = Folder({
            "README.md": """\
                [ok](docs/Setup%20Guide.md) [ok2](<docs/Setup Guide.md>)
                [web](https://example.com) [mail](mailto:a@b.c)
                [gone](docs/setup-guid.md)
                ```
                [example](not/real.md)
                ```
                and `[inline](also/not/real.md)`
                """,
            "docs/Setup Guide.md": "# Setup\n",
            "docs/setup-guide.md": "# Other\n",
        })
        report = folder.run()
        folder.close()
        broken = report["broken_links"]
        self.assertEqual([b["target"] for b in broken], ["docs/setup-guid.md"])
        self.assertEqual(broken[0]["line"], 3)
        self.assertEqual(broken[0]["suggestion"], "docs/setup-guide.md")

    def test_markdown_anchor_uses_github_slugs(self) -> None:
        folder = Folder({
            "README.md": "[a](guide.md#install-it) [b](guide.md#missing)\n",
            "guide.md": "# Guide\n## Install it\n",
        })
        report = folder.run()
        folder.close()
        self.assertEqual([a["anchor"] for a in report["broken_anchors"]], ["missing"])

    def test_inline_code_paths_count_as_links(self) -> None:
        folder = Folder({
            ".claude/skills/x/SKILL.md": "Read `references/deep.md` first.\n",
            ".claude/skills/x/references/deep.md": "detail\n",
        })
        report = folder.run()
        folder.close()
        self.assertEqual(report["orphans"], [])

    def test_symlinked_folders_are_not_counted_twice(self) -> None:
        folder = Folder({"README.md": "[a](agents/a.md)\n", "agents/a.md": "agent\n"})
        os.symlink(folder.root / "agents", folder.root / ".claude-agents-link")
        (folder.root / ".claude").mkdir()
        os.symlink(folder.root / "agents", folder.root / ".claude" / "agents")
        report = folder.run()
        folder.close()
        self.assertEqual(report["summary"]["files"], 2)


    def test_worktree_copies_are_skipped(self) -> None:
        folder = Folder({
            "README.md": "hi\n",
            ".claude/worktrees/feat-x/README.md": "copy\n",
            "sibling-worktree/.git": "gitdir: ../.git/worktrees/x\n",
            "sibling-worktree/README.md": "copy\n",
        })
        report = folder.run()
        folder.close()
        self.assertEqual(report["summary"]["files"], 1)

    def test_ignored_files_are_not_measured_but_links_to_them_resolve(self) -> None:
        folder = Folder({
            "README.md": "[plan](port/phase-01.md)\n",
            "port/phase-01.md": "x" * 900 + "\n[gone](missing.md)\n",
        })
        report = folder.run(max_bytes=500, ignore=["port/phase-*"])
        folder.close()
        self.assertEqual(report["oversized"], [])
        self.assertEqual(report["broken_links"], [])
        self.assertEqual(report["summary"]["ignored"], 1)


class Wikilinks(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Folder({
            "README.md": """\
                | Agent | Note |
                |---|---|
                | [[agents/ui-ux\\|ui-ux]] | [[Guide#Agents]] |
                ![[Projects.base]] ![[diagram.png]]
                [[Guide#No such heading]] [[Missing Note]] [[Dup]]
                `[[Not A Link]]`
                """,
            "agents/ui-ux.md": "agent\n",
            "Guide.md": "# Guide\n## Agents\n",
            "Projects.base": "views: []\n",
            "diagram.png": "",
            "a/Dup.md": "one\n",
            "b/Dup.md": "two\n",
        })
        self.report = self.folder.run()

    def tearDown(self) -> None:
        self.folder.close()

    def test_escaped_alias_paths_and_assets_resolve(self) -> None:
        targets = [b["target"] for b in self.report["broken_links"]]
        self.assertEqual(targets, ["[[Missing Note]]"])

    def test_bad_heading_is_reported(self) -> None:
        self.assertEqual([a["anchor"] for a in self.report["broken_anchors"]], ["No such heading"])

    def test_ambiguous_name_is_reported(self) -> None:
        ambiguous = self.report["ambiguous_links"]
        self.assertEqual(len(ambiguous), 1)
        self.assertEqual(sorted(ambiguous[0]["candidates"]), ["a/Dup.md", "b/Dup.md"])



class Budgets(unittest.TestCase):
    def test_agent_context_files_get_tighter_default_budgets(self) -> None:
        folder = Folder({
            "CLAUDE.md": "rule\n" * 250,                       # over 200 lines
            ".claude/skills/x/SKILL.md": "step\n" * 400,       # under 500 lines
            ".claude/agents/a.md": "x" * 13_000,               # over 12 KB
            "CHANGELOG.md": "entry\n" * 5_000,                # never budgeted
            "notes/long.md": "line\n" * 250,                  # under the 300 default
            "my-plugin/agents/b.md": "x" * 13_000,             # plugin agents too
            "README.md": "[n](notes/long.md)\n",
        })
        report = audit(folder.root)
        folder.close()
        kinds = {e["file"]: e["kind"] for e in report["oversized"]}
        self.assertEqual(kinds, {"CLAUDE.md": "guide", ".claude/agents/a.md": "agent",
                                 "my-plugin/agents/b.md": "agent"})
        self.assertEqual(report["orphans"], [])
        self.assertEqual(report["oversized"][0]["remedy"].split(":")[0], "trim")

    def test_config_file_adds_types_rules_and_replaces_lists(self) -> None:
        folder = Folder({
            ".wiki-health.json": json.dumps({
                "default": {"max_bytes": 50_000},
                "types": {"hub": {"max_bytes": 100, "kind": "hub"},
                          "log-archive": {"unbudgeted": True}},
                "rules": [{"match": "drafts/*", "kind": "draft", "max_bytes": 10}],
                "inbox": ["0 Inbox/*"],
                "not_linked": ["snippets/*"],
            }),
            "README.md": "[[Hub]] [[Old]]\n",
            "Hub.md": "---\ntype: hub\n---\n" + "x" * 200 + "\n[[draft]]\n",
            "Old.md": "---\ntype: log-archive\n---\n" + "old\n" * 20_000,
            "drafts/draft.md": "x" * 20,
            "0 Inbox/idea.md": "loose\n",
            "snippets/s.md": "copied, never linked\n",
            "CLAUDE.md": "rule\n" * 250,   # built-in guide rule still applies
        })
        report = main_report(folder)
        folder.close()
        self.assertTrue(report["config"].endswith(".wiki-health.json"))
        self.assertEqual({e["file"]: e["kind"] for e in report["oversized"]},
                         {"Hub.md": "hub", "drafts/draft.md": "draft", "CLAUDE.md": "guide"})
        self.assertEqual(report["inbox"], ["0 Inbox/idea.md"])
        self.assertEqual(report["orphans"], [])

    def test_builtin_rules_can_be_switched_off(self) -> None:
        folder = Folder({".wiki-health.json": '{"builtin_rules": false}', "CLAUDE.md": "rule\n" * 250})
        report = main_report(folder)
        folder.close()
        self.assertEqual(report["oversized"], [])

    def test_bad_config_stops_with_a_clear_message(self) -> None:
        folder = Folder({".wiki-health.json": "{not json"})
        with self.assertRaises(SystemExit) as raised:
            load_config(folder.root, None)
        folder.close()
        self.assertIn("not valid JSON", str(raised.exception))

    def test_defaults_are_not_mutated_between_runs(self) -> None:
        folder = Folder({".wiki-health.json": '{"rules": [{"match": "*.md", "max_bytes": 1}]}'})
        load_config(folder.root, None)
        folder.close()
        self.assertEqual(len(DEFAULT_CONFIG["rules"]), 7)


class Logs(unittest.TestCase):
    def test_long_log_gets_an_archive_cut_at_80_percent_of_budget(self) -> None:
        entries = "".join(f"## 2026-10-{day:02d} · Entry\n" + "w" * 1_500 + "\n" for day in range(30, 0, -1))
        folder = Folder({
            ".wiki-health.json": '{"types": {"log": {"max_bytes": 12000, "kind": "log"}}}',
            "README.md": "[[P Log]]\n",
            "P Log.md": "---\ntype: log\n---\n# P Log\n" + entries,
        })
        report = main_report(folder)
        folder.close()
        log = report["oversized"][0]
        plan = log["archive_plan"]
        self.assertLessEqual(plan["bytes_after"], 9_600)
        self.assertEqual(plan["keep_entries"] + plan["move_entries"], 30)
        self.assertTrue(log["remedy"].startswith("archive"))

    def test_suggested_hub_matches_a_prefixed_folder_note(self) -> None:
        folder = Folder({
            "README.md": "[[P]]\n",
            "wiki/P/P.md": "[[P UI Diff]]\n",
            "wiki/P/UI Diff/P UI Diff.md": "hub of the folder\n",
            "wiki/P/UI Diff/P UI Extra.md": "unlinked\n",
        })
        report = audit(folder.root)
        folder.close()
        self.assertEqual(report["orphans"][0]["suggested_hub"], "wiki/P/UI Diff/P UI Diff.md")


def main_report(folder: "Folder") -> dict:
    config, source = load_config(folder.root, None)
    return audit(folder.root, config, None, source)


class Cli(unittest.TestCase):
    def test_strict_exit_code_and_missing_folder(self) -> None:
        folder = Folder({"README.md": "[gone](missing.md)\n"})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--dir", str(folder.root), "--strict", "--text"]), 1)
        folder.close()
        with self.assertRaises(SystemExit):
            main(["--dir", "/no/such/folder"])


if __name__ == "__main__":
    unittest.main()
