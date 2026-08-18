"""Structure guard: a file over the wall needs a ratchet entry, and a
ratcheted file may only SHRINK — never grow again while it "waits for a
split" (owner decree 2026-08-18: WatchAcademy controller.py grew 3,449 →
4,483 lines while ratcheted; that must be impossible).

Usage:
    python structure_guard.py <src-root> [--ratchet tests/structure_ratchet.json]
                              [--wall 1000] [--write-ratchet] [--json]

Ratchet file: {"<relative path>": {"lines": <logic lines at adoption>,
                                   "why": "<one line>", "owes": "<who/what>"}}
`--write-ratchet` records CURRENT sizes for files over the wall — new files
are added, existing entries only go DOWN (a grown file is a failure, never a
new baseline). Exit 1 on: over-wall file with no entry · ratcheted file that
grew · stale entry (file gone or under the wall — remove it, the ratchet only
shrinks). Importable: `check(root, ratchet, wall) -> list[str]`.

The wall is not a magic number that forces a cut at 1,020 lines: it is the
size at which a file needs a WRITTEN reason to stay whole, and from which it
may only shrink. Placement by responsibility (rules/CODE.md) is what keeps
files small; this guard only stops the slow slide back.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".claude", "__pycache__", ".venv", "venv", "build",
             "dist", "node_modules", "htmlcov", ".pytest_cache", "tests",
             "test", "support", "UV"}


def logic_lines(path: Path) -> int:
    """Non-blank, non-comment lines (docstrings count: they are read)."""
    count = 0
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                count += 1
    except OSError:
        return 0
    return count


def scan(root: Path) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        sizes[path.relative_to(root).as_posix()] = logic_lines(path)
    return sizes


def load_ratchet(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def check(root: Path, ratchet_path: Path, wall: int) -> list[str]:
    sizes = scan(root)
    ratchet = load_ratchet(ratchet_path)
    problems: list[str] = []
    for rel, lines in sorted(sizes.items()):
        entry = ratchet.get(rel)
        if lines > wall and not entry:
            problems.append(
                f"OVER THE WALL without a ratchet entry: {rel} ({lines} logic "
                f"lines > {wall}) — split by responsibility, or record it in "
                f"{ratchet_path.name} with a written reason (it may then only shrink)")
        elif entry:
            recorded = int(entry.get("lines") or 0)
            if lines > recorded:
                problems.append(
                    f"RATCHETED FILE GREW: {rel} {recorded} → {lines} logic lines "
                    f"— a file waiting for its split may only shrink; put the new "
                    f"code in the module whose responsibility it serves, or split now")
    for rel, entry in ratchet.items():
        if rel not in sizes:
            problems.append(f"STALE ratchet entry (file gone): {rel} — remove it")
        elif sizes[rel] <= wall:
            problems.append(
                f"STALE ratchet entry (under the wall now: {sizes[rel]}): {rel} "
                f"— remove it, the ratchet only shrinks")
    return problems


def write_ratchet(root: Path, ratchet_path: Path, wall: int) -> dict:
    sizes = scan(root)
    ratchet = load_ratchet(ratchet_path)
    for rel, lines in sizes.items():
        if lines > wall:
            entry = ratchet.get(rel) or {"why": "adopted as-is (write the reason)",
                                         "owes": "the split"}
            entry["lines"] = min(lines, int(entry.get("lines") or lines))
            ratchet[rel] = entry
    ratchet = {k: v for k, v in ratchet.items()
               if k in sizes and sizes[k] > wall}
    ratchet_path.parent.mkdir(parents=True, exist_ok=True)
    ratchet_path.write_text(json.dumps(ratchet, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    return ratchet


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root")
    parser.add_argument("--ratchet", default="tests/structure_ratchet.json")
    parser.add_argument("--wall", type=int, default=1000)
    parser.add_argument("--write-ratchet", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    ratchet_path = Path(args.ratchet)
    if not ratchet_path.is_absolute():
        ratchet_path = root / ratchet_path
    if args.write_ratchet:
        written = write_ratchet(root, ratchet_path, args.wall)
        print(f"ratchet written: {len(written)} file(s) over {args.wall} → {ratchet_path}")
        return 0
    problems = check(root, ratchet_path, args.wall)
    if args.json:
        print(json.dumps(problems, indent=2, ensure_ascii=False))
    else:
        for line in problems:
            print(line)
        print(f"structure guard: {len(problems)} problem(s), wall {args.wall}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(run())
