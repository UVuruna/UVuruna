"""Self-test for rules_size_guard.py — files over/under/missing a limit."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_size_guard  # noqa: E402


def test_row_under_limit_is_ok(tmp_path):
    f = tmp_path / "small.md"
    f.write_text("x" * 100, encoding="utf-8")
    path, size, limit, ok, note = rules_size_guard._row(f, 5000)
    assert size == 100
    assert ok is True
    assert note == ""


def test_row_over_limit_fails(tmp_path):
    f = tmp_path / "big.md"
    f.write_text("x" * 6000, encoding="utf-8")
    path, size, limit, ok, note = rules_size_guard._row(f, 5000)
    assert size == 6000
    assert ok is False


def test_row_missing_file_is_skipped_not_failed(tmp_path):
    f = tmp_path / "absent.md"
    path, size, limit, ok, note = rules_size_guard._row(f, 5000)
    assert size is None
    assert ok is True
    assert "skipped" in note


def test_project_claude_md_checked(tmp_path):
    proj = tmp_path / "MyProject"
    proj.mkdir()
    (proj / "CLAUDE.md").write_text("x" * 7000, encoding="utf-8")
    rows = rules_size_guard.check(project=str(proj))
    project_rows = [r for r in rows if r[0] == str(proj / "CLAUDE.md")]
    assert len(project_rows) == 1
    assert project_rows[0][3] is False  # over the 6000 limit


def test_main_exit_code_reflects_over(tmp_path, monkeypatch, capsys):
    # isolate from the real repo's rules/*.md — other agents may have them
    # mid-rewrite and over budget right now; this test only cares about
    # the --project row's own effect on the exit code.
    monkeypatch.setattr(rules_size_guard, "ROOT_CHECKS", [])

    proj = tmp_path / "OkProject"
    proj.mkdir()
    (proj / "CLAUDE.md").write_text("small", encoding="utf-8")
    assert rules_size_guard.main(["--project", str(proj)]) == 0

    proj2 = tmp_path / "OverProject"
    proj2.mkdir()
    (proj2 / "CLAUDE.md").write_text("x" * 6001, encoding="utf-8")
    assert rules_size_guard.main(["--project", str(proj2)]) == 1
