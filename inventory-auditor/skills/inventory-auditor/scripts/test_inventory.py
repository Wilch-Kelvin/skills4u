"""Tests for inventory.py. Standard library only, like the script.

    python3 -m unittest discover -s inventory-auditor/skills/inventory-auditor/scripts
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventory import build, frontmatter, main, report, transcript_events


def write(base: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def skill(name: str, description: str, body: str = "") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n{body}"


def tool_use(name: str, tool_input: dict[str, str], ts: str) -> str:
    return json.dumps({
        "type": "assistant", "timestamp": ts,
        "message": {"content": [{"type": "tool_use", "name": name, "input": tool_input}]},
    })


def typed(command: str, ts: str) -> str:
    return json.dumps({
        "type": "user", "timestamp": ts,
        "message": {"content": f"<command-name>/{command}</command-name>"},
    })


class InventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root, self.home, self.plugin = base / "project", base / "home", base / "my-plugin"
        write(self.root, {
            ".claude/skills/release/SKILL.md": skill("release", "Use when shipping a release."),
            ".claude/skills/release/references/x.md": "ref",
            ".claude/skills/big/SKILL.md": skill("big", "Use when big.", "x" * 21_000),
            ".claude/skills/nodesc/SKILL.md": "---\nname: nodesc\n---\n# none\n",
            ".claude/agents/designer.md": skill("designer", "Designs screens."),
            ".agents/skills/release/SKILL.md": skill("release", "Old copy for another host."),
            ".claude/settings.json": json.dumps({"hooks": {"PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "true"}]}]}}),
        })
        write(self.plugin, {
            "skills/review/SKILL.md": skill("review", "Use when reviewing a diff."),
            "agents/reviewer.md": skill("reviewer", "Reviews code."),
        })
        write(self.home, {
            ".claude/skills/notes/SKILL.md": skill("notes", "Take notes."),
            ".claude/projects/p/a.jsonl": "\n".join([
                tool_use("Skill", {"skill": "release"}, "2026-11-05T10:00:00Z"),
                tool_use("Skill", {"skill": "my-plugin:review"}, "2026-11-06T10:00:00Z"),
                typed("release", "2026-11-07T10:00:00Z"),
                tool_use("Agent", {"subagent_type": "designer"}, "2026-11-08T10:00:00Z"),
                tool_use("Bash", {"command": "ls"}, "2026-11-09T10:00:00Z"),
                "not json",
            ]),
        })
        # A user-level symlink back into the project must not be counted twice.
        os.symlink(self.root / ".claude/skills/big", self.home / ".claude/skills/big")
        self.data = build(self.root, self.home, self.home / ".claude/projects", [self.plugin])
        self.items = {i["id"]: i for i in self.data["items"]}  # type: ignore[union-attr]
        self.rules = {(f["rule"], f["item"]) for f in self.data["findings"]}  # type: ignore[union-attr]

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_finds_project_user_and_extra_items_once(self) -> None:
        self.assertEqual(sorted(self.items), [
            "agent:designer", "agent:reviewer", "skill:big", "skill:nodesc", "skill:notes",
            "skill:release@project", "skill:release@project-agents", "skill:review",
        ])
        self.assertEqual(self.items["skill:notes"]["source"], "user")
        self.assertEqual(self.items["skill:review"]["source"], "extra:my-plugin")
        self.assertEqual(self.items["skill:big"]["source"], "project")  # symlink not counted
        self.assertEqual(self.items["skill:release@project"]["resources"], ["references"])

    def test_cross_host_copies_only_flag_drift(self) -> None:
        # .claude/skills/release and .agents/skills/release are for different
        # agents, so they aren't duplicates, but their content differs.
        rules = {(f["rule"], f["item"]) for f in self.data["findings"]}  # type: ignore[union-attr]
        self.assertNotIn(("duplicate_name", "skill:release@project"), rules)
        self.assertIn(("copies_differ", "skill:release@project"), rules)
        self.assertEqual(self.items["skill:release@project-agents"]["host"], "agents")

    def test_same_name_twice_for_one_host_is_a_conflict(self) -> None:
        write(self.home, {".claude/skills/release/SKILL.md": skill("release", "Another release.")})
        data = build(self.root, self.home, self.home / "missing", [self.plugin])
        dupes = {f["item"] for f in data["findings"] if f["rule"] == "duplicate_name"}  # type: ignore[union-attr]
        self.assertEqual(dupes, {"skill:release@project", "skill:release@user"})

    def test_identical_cross_host_copies_are_fine(self) -> None:
        same = skill("release", "Use when shipping a release.")
        write(self.root, {".agents/skills/release/SKILL.md": same})
        data = build(self.root, self.home, self.home / "missing")
        self.assertFalse([f for f in data["findings"] if f["item"].startswith("skill:release")])  # type: ignore[union-attr]

    def test_usage_counts_calls_namespaces_and_typed_commands(self) -> None:
        for copy in ("skill:release@project", "skill:release@project-agents"):  # shared, can't tell apart
            usage = self.items[copy]["usage"]
            self.assertEqual((usage["tool_calls"], usage["typed"]), (1, 1))
        self.assertEqual(self.items["skill:review"]["usage"]["tool_calls"], 1)
        self.assertEqual(self.items["agent:designer"]["usage"]["tool_calls"], 1)
        window = self.data["transcripts"]
        self.assertEqual((window["first"], window["last"]), ("2026-11-05T10:00:00Z", "2026-11-09T10:00:00Z"))

    def test_findings_and_hooks(self) -> None:
        self.assertIn(("over_budget", "skill:big"), self.rules)
        self.assertIn(("missing_description", "skill:nodesc"), self.rules)
        self.assertIn(("unused_in_window", "skill:notes"), self.rules)
        self.assertNotIn(("unused_in_window", "skill:review"), self.rules)
        self.assertEqual([(h["event"], h["matcher"]) for h in self.data["hooks"]], [("PreToolUse", "Bash")])  # type: ignore[union-attr]

    def test_budgets_can_be_changed(self) -> None:
        data = build(self.root, self.home, self.home / "missing", [], skill_budget=40)
        rules = {(f["rule"], f["item"]) for f in data["findings"]}  # type: ignore[union-attr]
        self.assertIn(("over_budget", "skill:notes"), rules)

    def test_no_transcripts_means_usage_unknown(self) -> None:
        data = build(self.root, self.home, self.home / "missing")
        self.assertEqual(data["transcripts"]["files"], 0)  # type: ignore[index]
        self.assertFalse([f for f in data["findings"] if f["rule"] == "unused_in_window"])  # type: ignore[union-attr]
        self.assertIn("usage is unknown", report(data))

    def test_unreadable_transcripts_folder_is_unknown_not_a_crash(self) -> None:
        # Seen in an eval sandbox: stat on the folder raised EPERM.
        real_is_dir = Path.is_dir

        def is_dir(path: Path) -> bool:
            if path.name == "locked":
                raise PermissionError(1, "Operation not permitted")
            return real_is_dir(path)

        with mock.patch.object(Path, "is_dir", autospec=True, side_effect=is_dir):
            data = build(self.root, self.home, self.home / "locked")
        self.assertIn("Operation not permitted", data["transcripts"]["error"])  # type: ignore[index]
        self.assertIn("usage is unknown", report(data))

    def test_report_states_window_and_codex_gap(self) -> None:
        text = report(self.data)
        self.assertIn("2026-11-05 to 2026-11-09", text)
        self.assertIn("Codex usage is not counted", text)

    def test_cli_writes_both_files_and_rejects_bad_folders(self) -> None:
        out = Path(self.tmp.name) / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(["--root", str(self.root), "--home", str(self.home), "--out", str(out)])
        self.assertEqual(code, 0)
        self.assertTrue((out / "inventory.json").is_file() and (out / "inventory-report.md").is_file())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--root", "/no/such", "--out", str(out)]), 2)
            self.assertEqual(main(["--root", str(self.root), "--extra", "/no/such", "--out", str(out)]), 2)


class FrontmatterTest(unittest.TestCase):
    def test_plain_quoted_and_folded(self) -> None:
        self.assertEqual(frontmatter('---\ndescription: "a: b"\n---\n')["description"], "a: b")
        folded = frontmatter("---\ndescription: >\n  one\n  two\nname: x\n---\n")
        self.assertEqual((folded["description"], folded["name"]), ("one two", "x"))
        self.assertEqual(frontmatter("no frontmatter"), {})


class TranscriptTest(unittest.TestCase):
    def test_ignores_other_tools_and_bad_lines(self) -> None:
        self.assertEqual(list(transcript_events(tool_use("Bash", {}, "t"))), [])
        self.assertEqual(list(transcript_events("{broken")), [])
        self.assertEqual(list(transcript_events(typed("wiki-health", "t"))), [("wiki-health", "t", True)])


if __name__ == "__main__":
    unittest.main()
