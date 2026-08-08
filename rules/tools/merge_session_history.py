#!/usr/bin/env python3
"""Reunite Claude Code session history after a folder rename.

Claude Code stores a project's transcripts in
``~/.claude/projects/<path-with-every-non-alphanumeric-turned-into-a-dash>``.
The directory name is derived from the project's PATH, so renaming or moving
a project folder makes the harness look in a NEW, empty directory — the old
transcripts are not deleted, they are orphaned, and ``claude --resume`` stops
offering them (owner's question, 2026-08-08: "kada promenim ime foldera sva
istorija CLAUDE sesija nestane").

This tool finds those orphans and COPIES them into the directory the current
path maps to. It never deletes and never overwrites, so running it twice is
harmless and the orphan stays behind as a backup.

    python rules/tools/merge_session_history.py --list
    python rules/tools/merge_session_history.py "u:/Coding/UVuruna/Gadgets/DOMY Watch"
    python rules/tools/merge_session_history.py --from <orphan-dir-name> --into <project-path>

Without --from, the orphan is guessed by matching the LAST path components
(a rename usually keeps the project's own folder name, only its parents
change) — and a guess is always shown for confirmation before anything is
copied, unless --yes is given.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"


def encode(path: str) -> str:
    """The directory name Claude Code derives from a project path."""
    return "".join(c if c.isalnum() else "-" for c in str(path))


def transcripts(directory: Path) -> list:
    try:
        return sorted(directory.glob("*.jsonl"))
    except OSError:
        return []


def recorded_cwd(transcript: Path) -> str:
    """The working directory a transcript was recorded in — the honest way
    to tell WHICH project an orphaned directory belonged to."""
    try:
        with open(transcript, encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                if index > 40:
                    break
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict) and entry.get("cwd"):
                    return str(entry["cwd"])
    except OSError:
        pass
    return ""


def survey() -> list:
    rows = []
    for directory in sorted(PROJECTS_DIR.iterdir()):
        if not directory.is_dir():
            continue
        files = transcripts(directory)
        if not files:
            continue
        newest = max(f.stat().st_mtime for f in files)
        rows.append((directory, len(files), newest, recorded_cwd(files[0])))
    return rows


def tail_key(name: str, depth: int = 2) -> str:
    return "-".join(name.strip("-").split("-")[-depth:]).lower()


def guess_orphans(target_dir: Path, rows: list) -> list:
    """Directories whose name ends the same way the target's does — a rename
    usually keeps the project's own folder name."""
    key = tail_key(target_dir.name)
    return [row for row in rows
            if row[0] != target_dir and tail_key(row[0].name) == key]


def merge(source: Path, target: Path, dry_run: bool) -> int:
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for transcript in transcripts(source):
        destination = target / transcript.name
        if destination.exists():
            continue
        if not dry_run:
            shutil.copy2(transcript, destination)
        copied += 1
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?",
                        help="current path of the project to restore")
    parser.add_argument("--list", action="store_true",
                        help="show every history directory and its real cwd")
    parser.add_argument("--from", dest="source",
                        help="orphan directory NAME under ~/.claude/projects")
    parser.add_argument("--yes", action="store_true",
                        help="copy without asking")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not PROJECTS_DIR.is_dir():
        print(f"no history directory at {PROJECTS_DIR}", file=sys.stderr)
        return 1

    rows = survey()

    if args.list or not args.project:
        for directory, count, _, cwd in rows:
            print(f"{directory.name:<56} {count:>3} sessions   {cwd}")
        if not args.project:
            print("\nPass a project path to merge its orphaned history into "
                  "the directory its CURRENT path maps to.")
        return 0

    target = PROJECTS_DIR / encode(Path(args.project).as_posix())
    print(f"target: {target.name}"
          f"  ({len(transcripts(target))} sessions there now)")

    if args.source:
        sources = [PROJECTS_DIR / args.source]
        if not sources[0].is_dir():
            print(f"no such directory: {sources[0]}", file=sys.stderr)
            return 1
    else:
        sources = [row[0] for row in guess_orphans(target, rows)]
        if not sources:
            print("no orphaned history found for that path — either nothing "
                  "was renamed, or the folder name changed too (use --from "
                  "with a name from --list)")
            return 0

    total = 0
    for source in sources:
        cwd = recorded_cwd(transcripts(source)[0]) if transcripts(source) else ""
        print(f"  from {source.name}  ({len(transcripts(source))} sessions, "
              f"recorded in: {cwd})")
        if not args.yes and not args.dry_run:
            answer = input("  copy these? [y/N] ").strip().lower()
            if answer != "y":
                print("  skipped")
                continue
        copied = merge(source, target, args.dry_run)
        total += copied
        print(f"  {'would copy' if args.dry_run else 'copied'} {copied} "
              "(originals left in place as a backup)")

    print(f"\n{total} transcript(s) reunited. Restart `claude --resume` in "
          "the project to see them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
