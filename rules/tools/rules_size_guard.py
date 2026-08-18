"""Byte-size ceiling for the constitution and the per-category rulebooks
(rules/history/2026-08-18-rework-design.md ch.1 item 3, ch.8 item 1):
`CLAUDE.md` <= 6000 bytes, `rules/CODE.md` and each per-category
`rules/<CATEGORY>.md` <= 5000 bytes, and — with `--project <dir>` — that
project's own `CLAUDE.md` <= 6000 bytes.

A rulebook that does not exist yet (they are being written) is a SKIP,
never a fail — the guard only blocks once a file exists and is over
budget.

CLI: python rules_size_guard.py [--project <dir>]
Importable API: check(project=None) -> list[(path, bytes, limit, ok, note)]
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CATEGORY_FILES = ["GUI.md", "FEATURE.md", "BUGFIX.md", "REFACTOR.md",
                   "DOCS.md", "PLAN.md", "BUILD.md"]

ROOT_CHECKS = [
    (REPO_ROOT / "CLAUDE.md", 6000),
    (REPO_ROOT / "rules" / "CODE.md", 5000),
] + [(REPO_ROOT / "rules" / name, 5000) for name in CATEGORY_FILES]


def _row(path: Path, limit: int):
    if not path.exists():
        return (str(path), None, limit, True, "missing — skipped (being written)")
    size = path.stat().st_size
    ok = size <= limit
    return (str(path), size, limit, ok, "")


def check(project=None):
    rows = [_row(path, limit) for path, limit in ROOT_CHECKS]
    if project is not None:
        rows.append(_row(Path(project) / "CLAUDE.md", 6000))
    return rows


def _print_table(rows) -> bool:
    all_ok = True
    width = max((len(r[0]) for r in rows), default=4)
    print(f"{'file':<{width}}  {'bytes':>6}  {'limit':>6}  status")
    for path, size, limit, ok, note in rows:
        size_str = "-" if size is None else str(size)
        status = "OK" if ok else "OVER"
        if not ok:
            all_ok = False
        line = f"{path:<{width}}  {size_str:>6}  {limit:>6}  {status}"
        if note:
            line += f"  ({note})"
        print(line)
    return all_ok


def main(argv) -> int:
    project = None
    if "--project" in argv:
        idx = argv.index("--project")
        try:
            project = argv[idx + 1]
        except IndexError:
            print("rules_size_guard: --project needs a directory", file=sys.stderr)
            return 2
    rows = check(project)
    ok = _print_table(rows)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
