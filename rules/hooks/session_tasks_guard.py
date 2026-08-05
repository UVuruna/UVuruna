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
    - [x] done task …

A task is checked ONLY when FIXED = VERIFIED (root CLAUDE.md -> The Laws).
`WAITING_ON_OWNER: yes` is legal ONLY when the turn ends with questions or a
presentation the owner must answer; it goes back to `no` when work resumes.

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
    open_tasks = OPEN_TASK_RE.findall(text)
    if not open_tasks or WAITING_RE.search(text):
        return
    listing = "".join(f"  - [ ] {t}\n" for t in open_tasks)
    print(
        BLOCK_TASKS.format(path=tasks_file, tasks=listing),
        file=sys.stderr,
    )
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
