#!/usr/bin/env python3
"""Final report guard — owner decree 2026-08-06.

Enforces THE FINAL REPORT (rules/PLAN.md -> The Final Report) across ALL
sessions on this machine (wired in ~/.claude/settings.json):

  Stop hook — a session whose task list is DONE may not end until a
              session-stamped report exists that walks that list task by
              task: status + evidence on every line, and a RELEASE line.

Born the same hour as its sibling guards' worst failure mode: the owner got a
closing message he could not read anything from — "nemam pojma ni dal si
uradio ni šta si uradio". The session-tasks guard forces the WORK to finish;
this guard forces the session to SAY what happened to each task, in a form
the owner can read diagonally: per-task status, the evidence, the release.

The data file is per project, written by the agent when the delivery ends:

    .claude/session-report.md
    ------------------------------------------------------------------
    SESSION: <session id>
    RELEASE: <release URL | none — why no release>
    - [x] <task text exactly as in session-tasks.md> — DONE — <evidence:
          commits, tests run, files, measurements>
    - [ ] <task text> — BLOCKED — <why + what would unblock it>
    ------------------------------------------------------------------

Status vocabulary: DONE | PARTIAL | BLOCKED | NOT DONE. A DONE without
evidence is not a report line — FIXED = VERIFIED applies to the report as to
any claim of finished work. The SAME report, rendered readably, is what the
final chat message carries (Loud Incompleteness: NOT DONE items first).

Division of labour with session_tasks_guard.py (both run on Stop):
  - open tasks, not waiting        -> the TASKS guard blocks; this one stays
                                      silent (one wall at a time)
  - WAITING_ON_OWNER: yes          -> both pass: the turn ends with a
                                      question, not a delivery
  - every task checked             -> THIS guard demands the report
  - no session-tasks.md / no tasks -> both pass (no defined list, nothing to
                                      report against)

Contract: exit 2 = BLOCK (stderr is fed back to the agent); exit 0 = pass.
Fail-open on any parse error — a broken guard must never brick a session.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

TASKS_FILENAME = "session-tasks.md"
REPORT_FILENAME = "session-report.md"

TASK_RE = re.compile(r"^- \[( |x)\] (.+)$", re.M)
WAITING_RE = re.compile(r"^WAITING_ON_OWNER:\s*yes\b", re.M)
SESSION_RE = re.compile(r"^SESSION:\s*(\S+)", re.M)
RELEASE_RE = re.compile(r"^RELEASE:\s*\S", re.M)
STATUS_RE = re.compile(r"\b(DONE|PARTIAL|BLOCKED|NOT DONE)\b")

# How much of a task's text must reappear in the report to count as covered.
# The agent writes both files, so copying the task line verbatim is the
# expected (and easiest) way to satisfy this.
NEEDLE_CHARS = 60
EVIDENCE_MIN_CHARS = 20  # after the status word, something must follow

BLOCK_REPORT = (
    "THE FINAL REPORT (rules/PLAN.md -> The Final Report, GATE of 2026-08-06): "
    "this session's task list is done, so it may not end without the "
    "session-stamped final report.\n"
    "{problem}\n"
    "Write {report_path} in exactly this shape:\n"
    "    SESSION: {session_id}\n"
    "    RELEASE: <release URL, or: none — why no release>\n"
    "    - [x] <task text as it stands in session-tasks.md> — DONE — "
    "<evidence: commits, tests run, files, measurements>\n"
    "    - [ ] <task text> — BLOCKED — <why + what would unblock>\n"
    "One line per task in {tasks_path} — status from DONE | PARTIAL | BLOCKED "
    "| NOT DONE, and the evidence tail is NOT optional (FIXED = VERIFIED "
    "applies to report lines like any claim of finished work). Then end the "
    "session with the SAME report rendered readably in chat: NOT DONE items "
    "first (Loud Incompleteness), then per-task status + evidence, then the "
    "release link."
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def find_project_file(start: Path, name: str) -> Path | None:
    """`.claude/<name>` in the session's directory or any parent — sessions
    sometimes start in a subdirectory of the project."""
    for directory in (start, *start.parents):
        candidate = directory / ".claude" / name
        if candidate.is_file():
            return candidate
    return None


def report_problem(report_path: Path, session_id: str,
                   tasks: list[str], report_text: str | None) -> str | None:
    """What is wrong with the report — None when it satisfies the gate."""
    if report_text is None:
        return f"{report_path} does not exist yet."
    stamped = SESSION_RE.search(report_text)
    if not stamped or stamped.group(1) != session_id:
        found = stamped.group(1) if stamped else "no SESSION line"
        return (f"{report_path} does not name this session ({session_id}) - "
                f"it carries {found}; an earlier session's report does not "
                "carry over.")
    if not RELEASE_RE.search(report_text):
        return (f"{report_path} has no RELEASE line - state the release URL, "
                "or 'none — <why no release>' if this session honestly "
                "shipped nothing installable.")
    flat = normalize(report_text)
    missing: list[str] = []
    for task in tasks:
        needle = normalize(task)[:NEEDLE_CHARS]
        if needle and needle not in flat:
            missing.append(task)
    if missing:
        listing = "".join(f"  - {t}\n" for t in missing)
        return ("these tasks from session-tasks.md have no line in the "
                f"report (copy each task's text verbatim):\n{listing}".rstrip())
    weak: list[str] = []
    for line in report_text.splitlines():
        if not line.lstrip().startswith("- ["):
            continue
        status = STATUS_RE.search(line)
        if not status:
            weak.append(f"{line.strip()}  <- no status word")
        elif len(line[status.end():].strip(" —-–·:")) < EVIDENCE_MIN_CHARS:
            weak.append(f"{line.strip()}  <- status without evidence")
    if weak:
        listing = "".join(f"  {w}\n" for w in weak)
        return ("every report line needs a status (DONE | PARTIAL | BLOCKED "
                f"| NOT DONE) AND an evidence tail:\n{listing}".rstrip())
    return None


def _session_changed_files(cwd: Path) -> bool:
    """True when the working tree carries staged/unstaged changes.

    Owner decree 2026-08-14: a session that answered a question and
    touched nothing has NOTHING to report - demanding a final report
    from it turns every conversation into paperwork. Cannot tell (no
    git, error) -> guard, never skip silently.
    """
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=cwd, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    if out.returncode != 0:
        return True
    return bool(out.stdout.strip())


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return  # already continuing because of a Stop hook - never loop
    cwd = Path(payload.get("cwd") or os.getcwd())
    if not _session_changed_files(cwd):
        return  # nothing delivered, nothing to report
    tasks_file = find_project_file(cwd, TASKS_FILENAME)
    if tasks_file is None:
        return
    try:
        tasks_text = tasks_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    matches = TASK_RE.findall(tasks_text)
    if not matches:
        return  # no checkbox tasks defined - nothing to report against
    if WAITING_RE.search(tasks_text):
        return  # the turn ends with a question, not a delivery
    if any(state == " " for state, _ in matches):
        return  # open tasks: session_tasks_guard is the wall for that state
    tasks = [text for _, text in matches]
    session_id = str(payload.get("session_id") or "")
    report_path = tasks_file.parent / REPORT_FILENAME
    try:
        report_text = report_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        report_text = None
    problem = report_problem(report_path, session_id, tasks, report_text)
    if problem is None:
        return
    print(
        BLOCK_REPORT.format(problem=problem, report_path=report_path,
                            session_id=session_id or "<this session's id>",
                            tasks_path=tasks_file),
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
