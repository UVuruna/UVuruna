"""The STRUCTURE tooth (owner decree 2026-08-18): an agent spends tokens on
WHERE code goes before it writes it, and a reviewer confirms it after.

- `struktura:` block in the ledger, written BEFORE the first product edit of a
  code category (GUI/FEATURE/BUGFIX/REFACTOR, class Standard/Wide): one line
  per new or grown unit — `<module path> ← <unit>: <why it belongs there>` or
  `NEW <module path>: <responsibility>` when nothing fits.
- Every top-level `def`/`class` ADDED in the session (Write/Edit new text
  minus old text) must be named in that block, or its module must be — an
  addition nobody placed is the procedural slide the owner forbids.
- Standard/Wide FEATURE/REFACTOR: an independent `reviewer` sub-agent ran
  after the last product edit and the ledger carries `pregled N` / `review N`
  ≥ 8 (the reviewer's checklist is in rules/FEATURE.md).
"""

from __future__ import annotations

import re
from pathlib import Path

STRUCTURE_HEAD_RE = re.compile(r"^\s*(struktura|structure)\s*:", re.I | re.M)
UNIT_RE = re.compile(r"^(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)", re.M)
REVIEW_RE = re.compile(r"\b(pregled|review)\s*[:=]?\s*(\d{1,2})(?:\s*/\s*10)?\b",
                       re.I)
REVIEWER_RE = re.compile(r"reviewer|pregleda[čc]", re.I)
CODE_CATEGORIES = ("GUI", "FEATURE", "BUGFIX", "REFACTOR")
CODE_SUFFIXES = (".py", ".js", ".ts", ".kt", ".cs", ".java")


def block(text: str) -> str:
    """The `struktura:` block: from its heading to the next blank line."""
    match = STRUCTURE_HEAD_RE.search(text)
    if not match:
        return ""
    rest = text[match.end():]
    lines = []
    for line in rest.splitlines():
        if not line.strip() and lines:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def has_block(text: str) -> bool:
    return bool(block(text))


def added_units(edits) -> dict[str, list[str]]:
    """{file_path: [unit names added]} from Write/Edit tool inputs — units
    present in the new text and absent from the old text of the same call."""
    found: dict[str, list[str]] = {}
    for tool in edits:
        path = tool.file_path
        if not path.lower().endswith(CODE_SUFFIXES):
            continue
        new = str(tool.input.get("new_string") or tool.input.get("content") or "")
        old = str(tool.input.get("old_string") or "")
        added = [u for u in UNIT_RE.findall(new) if u not in UNIT_RE.findall(old)]
        if added:
            found.setdefault(path, []).extend(added)
    return found


def unplaced(text: str, edits) -> list[tuple[str, str]]:
    """(file, unit) pairs the struktura block never mentions — by unit name
    or by the module's file name."""
    placed = block(text).lower()
    missing = []
    for path, units in added_units(edits).items():
        stem = Path(path).name.lower()
        for unit in units:
            if unit.lower() in placed or stem in placed:
                continue
            missing.append((path, unit))
    return missing


def check_stop(led, model, product_edits) -> list[str] | None:
    """Stop-time structure tooth for code categories."""
    if led.trivial or not any(led.has(c) for c in CODE_CATEGORIES):
        return None
    if not product_edits:
        return None
    if not has_block(led.text):
        return [
            "STRUCTURE tooth: no `struktura:` block — code was written without "
            "deciding where it belongs.",
            "FIX: add `struktura:` lines (`<module> ← <unit>: why` or `NEW "
            "<module>: responsibility`) for what this session added.",
            f"where: {led.path}",
        ]
    missing = unplaced(led.text, product_edits)
    if missing:
        path, unit = missing[0]
        return [
            f"STRUCTURE tooth: `{unit}` was added to {Path(path).name} but the "
            "`struktura:` block never places it.",
            "FIX: name it in the block with the module it belongs to and why "
            "(or the NEW module born for it) — then it may stay.",
            f"where: {led.path}",
        ]
    return None


def check_review(led, model, product_edits) -> list[str] | None:
    """The reviewer runs LAST — after the category teeth are satisfied."""
    if led.trivial or not product_edits:
        return None
    if led.klass and (led.has("FEATURE") or led.has("REFACTOR")):
        last_edit = max((t.ts for t in product_edits if t.ts), default=None)
        reviewers = [t for t in model.agent_launches()
                     if REVIEWER_RE.search(str(t.input.get("prompt") or "")
                                           + str(t.input.get("description") or ""))
                     and (last_edit is None or t.ts is None or t.ts > last_edit)]
        if not reviewers:
            return [
                f"STRUCTURE tooth (class {led.klass}): no independent reviewer "
                "ran after the last edit.",
                "FIX: launch one sub-agent whose prompt says `reviewer` with the "
                "six-question checklist (rules/FEATURE.md); it writes `pregled N`.",
                f"where: {led.path}",
            ]
        grades = [int(v) for _, v in REVIEW_RE.findall(led.text)]
        if not grades or min(grades) < 8:
            return [
                "STRUCTURE tooth: the reviewer's `pregled N` is missing or < 8.",
                "FIX: act on the reviewer's three refactors (or refute them in "
                "the ledger), re-review, write the honest grade.",
                f"where: {led.path}",
            ]
    return None
