"""Reads and validates the session ledger `.claude/sessions/<sid>.md`.

Grammar (design §3): a `kategorija:`/`category:` header line, tasks in the
states `[ ] [>] [?] [~] [x]`, `!` evidence lines, `?` owner questions, and the
optional `matrica:`, `uzrok:`, `proces-uzrok:` blocks. Serbian and English keys
are both accepted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = ("GUI", "FEATURE", "BUGFIX", "REFACTOR", "DOCS", "PLAN", "BUILD")
CLASSES = ("Trivial", "Standard", "Wide")

CATEGORY_RE = re.compile(r"^\s*(kategorija|category)\s*:\s*(.+)$", re.I | re.M)
CLASS_RE = re.compile(r"\b(klasa|class)\s*:\s*(Trivial|Standard|Wide)\b", re.I)
AGENTS_RE = re.compile(r"\b(agenti|agents)\s*:\s*([^\n·]+)", re.I)
MATRIX_RE = re.compile(r"^[ 	]*(matrica|matrix)[ 	]*:[ 	]*$", re.I)
CAUSE_RE = re.compile(r"^\s*(uzrok|cause)\s*:\s*(\S.*)$", re.I | re.M)
PROCESS_CAUSE_RE = re.compile(
    r"^\s*(proces-uzrok|process-cause)\s*:\s*(\S.*)$", re.I | re.M)
TASK_RE = re.compile(r"^(\s*)-\s*\[([ xX~>?])\]\s*(.*)$")
EVIDENCE_ID_RE = re.compile(r"\bev-(\d{1,6})\b")
GRADE_RE = re.compile(r"\b(grade|ocena)\s*[:=]?\s*(\d{1,2})(?:\s*/\s*10)?\b",
                      re.I)
REPLACEMENT_RE = re.compile(r"\b(zamena|zamjena|replacement)\b", re.I)
#: HTML comments carry the template's EXAMPLES — never real tasks or evidence
COMMENT_RE = re.compile(r"<!--.*?(?:-->|\Z)", re.S)


@dataclass
class Task:
    state: str          # " " ">" "?" "~" "x"
    text: str
    line: int
    bangs: list[str] = field(default_factory=list)   # "! ..." lines
    questions: list[str] = field(default_factory=list)  # "? ..." lines

    @property
    def open(self) -> bool:
        return self.state in (" ", ">")

    @property
    def done(self) -> bool:
        return self.state == "x"

    def evidence_ids(self) -> list[str]:
        found = []
        for bang in self.bangs:
            found += [f"ev-{n}" for n in EVIDENCE_ID_RE.findall(bang)]
        return found


@dataclass
class Ledger:
    path: Path
    exists: bool = False
    text: str = ""
    mtime: float = 0.0
    categories: list[str] = field(default_factory=list)
    klass: str = ""
    agents: str = ""
    tasks: list[Task] = field(default_factory=list)
    matrix_rows: list[list[str]] = field(default_factory=list)
    has_matrix: bool = False
    cause: str = ""
    process_cause: str = ""

    def has(self, category: str) -> bool:
        return category.upper() in self.categories

    @property
    def trivial(self) -> bool:
        return self.klass.lower() == "trivial"

    def open_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.open]

    def waiting_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.state == "?"]

    def done_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.done]

    def evidence_ids(self) -> list[str]:
        return [f"ev-{n}" for n in EVIDENCE_ID_RE.findall(self.text)]

    def grades(self) -> list[int]:
        return [int(value) for _, value in GRADE_RE.findall(self.text)]

    def bang_lines(self) -> list[str]:
        return [b for task in self.tasks for b in task.bangs]

    def mentions_replacement(self) -> bool:
        return bool(REPLACEMENT_RE.search(self.text))


def _parse_categories(raw: str) -> list[str]:
    found = []
    for token in re.split(r"[+,/·|]| and ", raw.split("·")[0]):
        name = token.strip().upper()
        if name in CATEGORIES and name not in found:
            found.append(name)
    return found


def _parse_matrix(lines: list[str], start: int) -> list[list[str]]:
    rows = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            break
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells):
            continue                      # separator row
        if cells and cells[0].lower() in ("#", "no", "br"):
            continue                      # header row
        rows.append(cells)
    return rows


def load(path: Path) -> Ledger:
    path = Path(path)
    ledger = Ledger(path=path)
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        ledger.mtime = path.stat().st_mtime
        ledger.exists = True
    except OSError:
        return ledger
    # keep the line numbering, drop the commented-out example ledger
    ledger.text = COMMENT_RE.sub(
        lambda m: "\n" * m.group(0).count("\n"), raw)

    header = CATEGORY_RE.search(ledger.text)
    if header:
        ledger.categories = _parse_categories(header.group(2))
    klass = CLASS_RE.search(ledger.text)
    ledger.klass = klass.group(2) if klass else ""
    agents = AGENTS_RE.search(ledger.text)
    ledger.agents = agents.group(2).strip() if agents else ""
    cause = CAUSE_RE.search(ledger.text)
    ledger.cause = cause.group(2).strip() if cause else ""
    process = PROCESS_CAUSE_RE.search(ledger.text)
    ledger.process_cause = process.group(2).strip() if process else ""

    lines = ledger.text.splitlines()
    current: Task | None = None
    for number, line in enumerate(lines, start=1):
        task = TASK_RE.match(line)
        if task:
            current = Task(state=task.group(2).lower().replace("X", "x"),
                           text=task.group(3).strip(), line=number)
            ledger.tasks.append(current)
            continue
        stripped = line.strip()
        if current is not None and stripped.startswith("!"):
            current.bangs.append(stripped.lstrip("! ").strip())
        elif current is not None and stripped.startswith("?"):
            current.questions.append(stripped.lstrip("? ").strip())
        elif stripped and not stripped.startswith(("|", "#")):
            if not re.match(r"^(matrica|matrix|uzrok|cause|proces-uzrok"
                            r"|process-cause)\s*:", stripped, re.I):
                current = None

    for number, line in enumerate(lines):
        if MATRIX_RE.match(line):
            ledger.has_matrix = True
            ledger.matrix_rows = _parse_matrix(lines, number)
            break
    return ledger
