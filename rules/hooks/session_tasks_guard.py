#!/usr/bin/env python3
"""Session task list guard — owner decree 2026-08-05.

Enforces THE SESSION TASK LIST (rules/PLAN.md -> The Session Task List)
across ALL sessions on this machine (wired in ~/.claude/settings.json):

  Stop hook — when the session's project carries a `.claude/session-tasks.md`
              with unchecked tasks, ending the session is BLOCKED unless the
              file says the turn is genuinely waiting on the owner's answer
              (`WAITING_ON_OWNER: yes`). Born from sessions that drifted into
              pure conversation and lost the task list the owner opened with.

The data file is per project, written by the agent at session start when the
owner defines tasks:

    WAITING_ON_OWNER: yes|no
    - [ ] task …
    - [~] shipped, but HE has not seen it work yet
    - [x] done task …

A task is checked ONLY when FIXED = VERIFIED (root CLAUDE.md -> The Laws).
`WAITING_ON_OWNER: yes` is legal ONLY when the turn ends with questions or a
presentation the owner must answer; it goes back to `no` when work resumes.

THE REPEAT LAW (owner decree 2026-08-07, root CLAUDE.md -> The Laws) has its
teeth here. He had spent a week being told that ten tasks were done and finding
half of them unchanged, and the reason was never dishonesty — it was that "done"
had quietly come to mean "my own test is green". A test written by the same
reasoning that produced the bug cannot falsify that reasoning. So:

  * a task block that says REPEAT must also say PROCESS CAUSE: — WHY the
    previous round's claim was false, in words, beside the task;
  * a REPEAT task may be `[x]` only with OWNER CONFIRMED or HIS EVIDENCE:
    (his log, his installed binary, his screenshot). Otherwise it is `[~]`:
    shipped and honest about it.

`[~]` never blocks a session — it is the state that stops a round from having
to choose between lying and never finishing.

Contract: exit 2 = BLOCK (stderr is fed back to the agent); exit 0 = pass.
Fail-open on any parse error — a broken guard must never brick a session.
"""

import json
import os
import re
import sys
from pathlib import Path

TASKS_FILENAME = "session-tasks.md"
OPEN_TASK_RE = re.compile(r"^- \[ \] (.+)$", re.M)
WAITING_RE = re.compile(r"^WAITING_ON_OWNER:\s*yes\b", re.M)

# A task and everything indented under it, up to the next task or heading.
TASK_BLOCK_RE = re.compile(r"^- \[([ x~])\] (.+(?:\n(?!- \[|#).*)*)", re.M)
REPEAT_RE = re.compile(r"\bREPEAT\b")
PROCESS_CAUSE_RE = re.compile(r"\bPROCESS CAUSE:")
HIS_EVIDENCE_RE = re.compile(r"\bOWNER CONFIRMED\b|\bHIS EVIDENCE:")

BLOCK_REPEAT = (
    "THE REPEAT LAW (root CLAUDE.md -> The Laws, owner decree 2026-08-07): the "
    "owner reported something an earlier round had already closed, and the "
    "FIRST deliverable of this round is why that earlier claim was false - not "
    "the code fix. These task blocks in {path} say REPEAT and do not answer "
    "it:\n{tasks}\n"
    "Add a `PROCESS CAUSE:` line to each - the mechanism, named: what was "
    "claimed, what the claim rested on, and why that evidence could be green "
    "while the app was broken. A repeat is proof the PROCESS failed; fixing "
    "only the code spends the same week again."
)

BLOCK_UNCONFIRMED = (
    "THE REPEAT LAW (root CLAUDE.md -> The Laws): a task that has ALREADY come "
    "back once may not be checked `[x]` on our own evidence. These are `[x]` "
    "in {path} with neither `OWNER CONFIRMED` nor `HIS EVIDENCE:`:\n{tasks}\n"
    "A guard written by the same reasoning that produced the bug proves the "
    "fix matches the theory, never that the theory was right - that is exactly "
    "how the last rounds shipped 'fixed' bugs. Mark them `[~]` (shipped, he "
    "has not seen it) and carry them into the Final Report, or cite evidence "
    "from HIS machine: his log, his installed binary, his screenshot, his word."
)

BLOCK_TASKS = (
    "THE SESSION TASK LIST (rules/PLAN.md -> The Session Task List, GATE of "
    "2026-08-05): the owner opened this session with a defined task list and "
    "it is not finished - the session may not end. Open tasks in {path}:\n"
    "{tasks}\n"
    "Finish them (a task is checked ONLY when FIXED = VERIFIED - root cause, "
    "fix, evidence). If you are truly blocked on the owner's input, end the "
    "turn with the fully-explained questions and set WAITING_ON_OWNER: yes; "
    "set it back to 'no' the moment work resumes."
)


def find_tasks_file(start: Path) -> Path | None:
    """`.claude/session-tasks.md` in the session's directory or any parent —
    sessions sometimes start in a subdirectory of the project."""
    for directory in (start, *start.parents):
        candidate = directory / ".claude" / TASKS_FILENAME
        if candidate.is_file():
            return candidate
    return None


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return  # already continuing because of a Stop hook - never loop
    cwd = Path(payload.get("cwd") or os.getcwd())
    tasks_file = find_tasks_file(cwd)
    if tasks_file is None:
        return
    try:
        text = tasks_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    check_repeat_law(tasks_file, text)
    open_tasks = OPEN_TASK_RE.findall(text)
    if not open_tasks or WAITING_RE.search(text):
        return
    listing = "".join(f"  - [ ] {t}\n" for t in open_tasks)
    print(
        BLOCK_TASKS.format(path=tasks_file, tasks=listing),
        file=sys.stderr,
    )
    sys.exit(2)


def first_line(block: str) -> str:
    return block.splitlines()[0].strip()[:110]


def check_repeat_law(tasks_file: Path, text: str) -> None:
    """THE REPEAT LAW's two mechanical halves. Runs BEFORE the open-task check
    and before WAITING_ON_OWNER can excuse anything: a round that ends with an
    unexplained repeat is the failure this law exists to stop, and 'I am
    waiting on the owner' is not an answer to why we told him it was fixed."""
    unexplained, unconfirmed = [], []
    for state, block in TASK_BLOCK_RE.findall(text):
        if not REPEAT_RE.search(block):
            continue
        if not PROCESS_CAUSE_RE.search(block):
            unexplained.append(first_line(block))
        elif state == "x" and not HIS_EVIDENCE_RE.search(block):
            unconfirmed.append(first_line(block))
    if unexplained:
        listing = "".join(f"  - {t}\n" for t in unexplained)
        print(BLOCK_REPEAT.format(path=tasks_file, tasks=listing),
              file=sys.stderr)
        sys.exit(2)
    if unconfirmed:
        listing = "".join(f"  - {t}\n" for t in unconfirmed)
        print(BLOCK_UNCONFIRMED.format(path=tasks_file, tasks=listing),
              file=sys.stderr)
        sys.exit(2)


def main() -> None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    if payload.get("hook_event_name", "") == "Stop":
        check_stop(payload)
    sys.exit(0)


if __name__ == "__main__":
    main()
