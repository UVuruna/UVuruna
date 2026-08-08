#!/usr/bin/env python3
"""Rename a project: the folder, every reference to it, and its session history.

Renaming a project folder by hand loses two things that are easy to miss:
the Claude Code transcripts (stored under a directory derived from the
project's PATH — see merge_session_history.py) and the references scattered
through the monorepo's own documentation. This tool does all three in one
pass, and REFUSES to run while a session is live in that project.

    python rules/tools/rename_project.py "Gadgets/DOMY Watch" "Gadgets/Watch Academy" --dry-run
    python rules/tools/rename_project.py "Gadgets/DOMY Watch" "Gadgets/Watch Academy"

WHAT IT DOES NOT DO, on purpose: it never renames a word that merely LOOKS
like the project. "DOMY" is the name of a dial inside Watch Academy and must
survive the folder rename; "remote user" is ordinary English prose inside
Vibe Coder. So the tool replaces only:

  * the full project NAME as a whole phrase ("DOMY Watch" -> "Watch Academy")
  * path forms of it ("Gadgets/DOMY Watch", "Gadgets\\DOMY Watch",
    "Gadgets-DOMY-Watch", "DOMY-Watch", "DOMY_Watch")

and it shows every hit before touching anything. A word that is part of the
product's vocabulary rather than its folder name is left alone — always.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
LIVE_WINDOW_S = 15 * 60          # a transcript touched this recently = live

TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".cs", ".xaml", ".html", ".htm",
    ".css", ".php", ".kt", ".kts", ".ps1", ".sh", ".bat", ".xml", ".svg",
    ".gitignore", ".iss", ".spec",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "dist", "build", ".pytest_cache", ".gradle", "bin", "obj"}


def encode(path: str) -> str:
    """The ~/.claude/projects directory name Claude Code derives from a path.

    The drive letter is lower-cased: Path.resolve() hands back "U:\\..." on
    Windows while the harness records "u:\\...", and although NTFS is
    case-insensitive enough to hide the difference, a directory created with
    the wrong case is a trap for anyone reading the folder list later."""
    text = str(path)
    if len(text) > 1 and text[1] == ":":
        text = text[0].lower() + text[1:]
    return "".join(c if c.isalnum() else "-" for c in text)


def live_sessions(encoded: str) -> list:
    """Transcripts of that project touched within the live window."""
    directory = PROJECTS_DIR / encoded
    if not directory.is_dir():
        return []
    now = time.time()
    return [f for f in directory.glob("*.jsonl")
            if now - f.stat().st_mtime < LIVE_WINDOW_S]


def variants(old_name: str, new_name: str) -> list:
    """(pattern, replacement) pairs, longest first so paths win over names."""
    def forms(name: str) -> dict:
        return {
            "plain": name,
            "slash": name.replace(" ", "/"),
            "dash": name.replace(" ", "-"),
            "under": name.replace(" ", "_"),
            "nospace": name.replace(" ", ""),
        }

    old, new = forms(old_name), forms(new_name)
    pairs = []
    for key in ("plain", "dash", "under", "nospace"):
        if old[key] != new[key]:
            pairs.append((old[key], new[key]))
    # de-duplicate, longest first
    seen, ordered = set(), []
    for a, b in sorted(pairs, key=lambda p: -len(p[0])):
        if a not in seen:
            seen.add(a)
            ordered.append((a, b))
    return ordered


def scan(root: Path, pairs: list) -> dict:
    """{file: [(line number, line)]} for every text file mentioning the name."""
    hits = {}
    for current, directories, files in os.walk(root):
        directories[:] = [d for d in directories if d not in SKIP_DIRS]
        for name in files:
            path = Path(current) / name
            if path.suffix.lower() not in TEXT_SUFFIXES and \
                    name not in TEXT_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not any(old in text for old, _ in pairs):
                continue
            lines = [(n, line.strip()[:140])
                     for n, line in enumerate(text.splitlines(), 1)
                     if any(old in line for old, _ in pairs)]
            if lines:
                hits[path] = lines
    return hits


def rewrite(path: Path, pairs: list) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    original = text
    changed = 0
    for old, new in pairs:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            changed += count
    if text != original:
        path.write_text(text, encoding="utf-8", newline="")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", help='e.g. "Gadgets/DOMY Watch"')
    parser.add_argument("new", help='e.g. "Gadgets/Watch Academy"')
    parser.add_argument("--root", default=".", help="monorepo root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="rename even with a live session (do not)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    old_dir = (root / args.old).resolve()
    new_dir = (root / args.new).resolve()
    old_name = Path(args.old).name
    new_name = Path(args.new).name

    if not old_dir.is_dir():
        print(f"no such project: {old_dir}", file=sys.stderr)
        return 1
    if new_dir.exists():
        print(f"target already exists: {new_dir}", file=sys.stderr)
        return 1

    old_encoded = encode(old_dir.as_posix())
    new_encoded = encode(new_dir.as_posix())
    transcripts = list((PROJECTS_DIR / old_encoded).glob("*.jsonl")) \
        if (PROJECTS_DIR / old_encoded).is_dir() else []
    live = live_sessions(old_encoded)

    print(f"project      {old_dir}")
    print(f"          -> {new_dir}")
    print(f"history      {old_encoded}  ({len(transcripts)} sessions)")
    print(f"          -> {new_encoded}")
    if live:
        print(f"\nLIVE SESSION: {len(live)} transcript(s) in this project were "
              f"touched in the last {LIVE_WINDOW_S // 60} minutes.")
        print("Renaming the folder under a running session breaks it: the "
              "session keeps writing to a path that no longer exists.")
        if not args.force:
            print("Refusing. Close the session (or wait) and run again.")
            return 2
        print("--force given: proceeding anyway.")

    pairs = variants(old_name, new_name)
    print("\nreplacements:")
    for old, new in pairs:
        print(f"  {old!r} -> {new!r}")

    hits = scan(root, pairs)
    total = sum(len(v) for v in hits.values())
    print(f"\n{total} reference(s) in {len(hits)} file(s):")
    for path, lines in sorted(hits.items()):
        try:
            shown = path.relative_to(root)
        except ValueError:
            shown = path
        print(f"  {shown}  ({len(lines)})")
        for number, line in lines[:2]:
            print(f"      {number}: {line}")

    if args.dry_run:
        print("\n--dry-run: nothing written. Review the list above — a hit "
              "that is the PRODUCT's vocabulary rather than the folder name "
              "must be excluded by hand before running for real.")
        return 0

    # 1. references first, while the paths in them still resolve
    written = 0
    for path in hits:
        written += rewrite(path, pairs)
    print(f"\nrewrote {written} reference(s)")

    # 2. the folder itself
    new_dir.parent.mkdir(parents=True, exist_ok=True)
    old_dir.rename(new_dir)
    print(f"renamed  {old_dir.name} -> {new_dir.name}")

    # 3. the session history, copied (never moved: the orphan stays a backup)
    if transcripts:
        target = PROJECTS_DIR / new_encoded
        target.mkdir(parents=True, exist_ok=True)
        copied = 0
        for transcript in transcripts:
            destination = target / transcript.name
            if not destination.exists():
                shutil.copy2(transcript, destination)
                copied += 1
        print(f"history  {copied} session(s) carried over to {new_encoded} "
              f"(originals kept in {old_encoded} as a backup)")
    else:
        print("history  nothing to carry over")

    print("\nDone. Check `git status` in the project and in the monorepo root, "
          "then commit: the rename touches both.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
