"""Self-test for clone_guard.py — plants clones and verifies detection.

Covers: cross-file clone (fail), renamed-identifier clone still caught,
short bodies below the statement floor ignored, `clone-ok:` exemption,
and the ratchet allow/stale lifecycle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import clone_guard  # noqa: E402

TEN_STMTS = "\n".join(f"    {name}{i} = {i}" for i, name in enumerate(["x"] * 10, 1))
FIVE_STMTS = "\n".join(f"    x{i} = {i}" for i in range(1, 6))


def _write(path: Path, code: str):
    path.write_text(code, encoding="utf-8")


def test_cross_file_clone_fails(tmp_path):
    _write(tmp_path / "a.py", f"def foo():\n{TEN_STMTS}\n")
    _write(tmp_path / "b.py", f"def bar():\n{TEN_STMTS}\n")
    groups = clone_guard.find_clones(tmp_path, min_statements=8)
    cross = [g for g in groups if g.cross_file]
    assert len(cross) == 1
    assert clone_guard.run([str(tmp_path)]) == 1


def test_renamed_identifiers_still_detected(tmp_path):
    body_a = "\n".join(f"    a{i} = {i}" for i in range(1, 11))
    body_b = "\n".join(f"    zzz{i} = {i}" for i in range(1, 11))
    _write(tmp_path / "a.py", f"def foo():\n{body_a}\n")
    _write(tmp_path / "b.py", f"def bar():\n{body_b}\n")
    groups = clone_guard.find_clones(tmp_path, min_statements=8)
    cross = [g for g in groups if g.cross_file]
    assert len(cross) == 1


def test_short_bodies_ignored(tmp_path):
    _write(tmp_path / "a.py", f"def foo():\n{FIVE_STMTS}\n")
    _write(tmp_path / "b.py", f"def bar():\n{FIVE_STMTS}\n")
    groups = clone_guard.find_clones(tmp_path, min_statements=8)
    assert groups == []


def test_clone_ok_exempts(tmp_path):
    _write(tmp_path / "a.py", f"def foo():\n{TEN_STMTS}\n")
    _write(
        tmp_path / "b.py",
        f"def bar():\n    # clone-ok: shared boilerplate, tracked in ticket 42\n{TEN_STMTS}\n",
    )
    assert clone_guard.run([str(tmp_path)]) == 0


def test_ratchet_allows_then_stale_fails(tmp_path):
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    _write(a, f"def foo():\n{TEN_STMTS}\n")
    _write(b, f"def bar():\n{TEN_STMTS}\n")
    ratchet = tmp_path / "ratchet.json"

    assert clone_guard.run([str(tmp_path), "--ratchet", str(ratchet), "--write-ratchet"]) == 0
    assert ratchet.exists()

    # ratchet now allows the group -> passes
    assert clone_guard.run([str(tmp_path), "--ratchet", str(ratchet)]) == 0

    # the clone disappears from the code -> the ratchet id is now stale
    _write(b, "def bar():\n    return 1\n")
    assert clone_guard.run([str(tmp_path), "--ratchet", str(ratchet)]) == 1

    data = json.loads(ratchet.read_text(encoding="utf-8"))
    assert data  # unchanged by a failing run — shrinks only by hand
