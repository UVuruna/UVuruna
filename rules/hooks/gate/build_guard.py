"""Build runs ONLY on the owner's word — and when it runs, it runs TO THE END.

"Build" in the owner's vocabulary means *the installer any user can download
from GitHub Releases*, never *a file in dist/* (owner decree 2026-08-19):
`setup/build.py` alone is half a job, and half a job is worse than none.
"""

from __future__ import annotations

import re

#: makes the artifact — worthless on its own
BUILD_PATTERNS = (
    re.compile(r"\bbuild\.py\b", re.I),
    re.compile(r"\bpyinstaller\b", re.I),
    re.compile(r"\bmakensis\b", re.I),
    re.compile(r"\bgradlew\b[^\n]*\b(assemble|bundle)", re.I),
    re.compile(r"\bmsbuild\b[^\n]*/t:\s*Publish", re.I),
    re.compile(r"\bdotnet\s+publish\b", re.I),
)

#: puts it where the user can reach it — this is what he asked for
RELEASE_PATTERNS = (
    re.compile(r"\bgh\s+release\s+create\b", re.I),
    re.compile(r"\bgh\s+release\s+upload\b", re.I),
)

#: commands that only READ text: `grep -n build.py`, `sed -n 1,5p build.py`
#: and friends are not builds, and blocking them taught agents to avoid the
#: whole subject (owner 2026-08-19, four blocks on one `sed && grep`).
READERS = frozenset((
    "grep", "rg", "egrep", "fgrep", "sed", "awk", "cat", "head", "tail",
    "less", "more", "find", "ls", "dir", "echo", "wc", "diff", "stat",
    "type", "select-string", "get-content", "get-childitem",
))

_SEGMENT_RE = re.compile(r"&&|\|\||[;|\n]")
_LEADING_NOISE_RE = re.compile(
    r"^\s*(?:(?:cd|pushd)\s+\S+\s*|[A-Za-z_][A-Za-z_0-9]*=\S*\s+|"
    r"(?:sudo|time|env|nohup)\s+)*", re.I)


def _executed_segments(command: str) -> list[str]:
    """The parts of a command line that actually RUN something."""
    live = []
    for segment in _SEGMENT_RE.split(command or ""):
        segment = _LEADING_NOISE_RE.sub("", segment).strip()
        if not segment:
            continue
        head = re.split(r"[\s]", segment, 1)[0]
        head = head.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if head.removesuffix(".exe") in READERS:
            continue
        live.append(segment)
    return live


def _matches(command: str, patterns) -> bool:
    return any(p.search(s) for s in _executed_segments(command)
               for p in patterns)


def is_build_command(command: str) -> bool:
    """Produces an artifact (dist/, apk, exe) — needs his word."""
    return bool(command) and _matches(command, BUILD_PATTERNS)


def is_release_command(command: str) -> bool:
    """Publishes it where a user can download it — the actual deliverable."""
    return bool(command) and _matches(command, RELEASE_PATTERNS)


def needs_owner_word(command: str) -> bool:
    return is_build_command(command) or is_release_command(command)


#: the owner's word — Serbian and English, any inflection. "apk" counts: the
#: owner orders Android builds with "pravi apk" (2026-08-19). "bill" counts:
#: voice typing renders his "build" as "bill" ("preko interneta bill",
#: 2026-08-19 evening). ANY message of the session carries it, including a
#: conditional one ("kad završiš sve, uradi build") — he does not repeat
#: himself and nobody asks him again (owner 2026-08-19 night).
OWNER_WORD_RE = re.compile(
    r"\b(build|release|bild|bildu?j|bill|rilis|objavi|izbilduj|apk)\w*", re.I)


def check(command: str, is_subagent: bool, owner_last_message: str
          ) -> list[str] | None:
    """Block lines, or None when this command may run."""
    if not needs_owner_word(command):
        return None
    if not is_subagent and OWNER_WORD_RE.search(owner_last_message or ""):
        return None
    return [
        "Build/release without the owner's word"
        + (" (and sub-agents never build)" if is_subagent else "") + ".",
        "FIX: do not ask him about it — carry on with the work; build when he "
        "says the word, and then build AND release in one go.",
        f"where: {command.strip()[:100]}",
    ]
