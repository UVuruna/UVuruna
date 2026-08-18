"""Build and release run ONLY on the owner's word, and never in a sub-agent."""

from __future__ import annotations

import re

BUILD_PATTERNS = (
    re.compile(r"\bbuild\.py\b", re.I),
    re.compile(r"\bpyinstaller\b", re.I),
    re.compile(r"\bmakensis\b", re.I),
    re.compile(r"\bgradlew\b[^\n]*\b(assemble|bundle)", re.I),
    re.compile(r"\bgh\s+release\b", re.I),
    re.compile(r"\bgit\s+tag\s+v", re.I),
    re.compile(r"\bmsbuild\b[^\n]*/t:\s*Publish", re.I),
    re.compile(r"\bdotnet\s+publish\b", re.I),
)

#: the owner's word — Serbian and English, any inflection
OWNER_WORD_RE = re.compile(
    r"\b(build|release|bild|bildu?j|rilis|objavi|izbilduj)\w*", re.I)


def is_build_command(command: str) -> bool:
    return bool(command) and any(p.search(command) for p in BUILD_PATTERNS)


def check(command: str, is_subagent: bool, owner_last_message: str
          ) -> list[str] | None:
    """Block lines, or None when this command may run."""
    if not is_build_command(command):
        return None
    if not is_subagent and OWNER_WORD_RE.search(owner_last_message or ""):
        return None
    return [
        "Build/release without the owner's word"
        + (" (and sub-agents never build)" if is_subagent else "") + ".",
        "FIX: end the turn with a `## BUILD & RELEASE?` question and a [?] "
        "BUILD task; run it only after he answers.",
        f"where: {command.strip()[:100]}",
    ]
