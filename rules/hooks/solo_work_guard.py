#!/usr/bin/env python3
"""THE SOLO-WORK GUARD — owner decree 2026-08-09, and it exists because two
guards that look like this one both guard something else.

His instruction at the START of a ten-hour session was one sentence: I lead the
work, I ENGAGE OTHER AGENTS, I verify them. I did every line of it myself. Ten
hours later I told him so as an observation, and his answer was that a rule
nobody checks is not a rule:

    "ako sam ti rekao da angažuješ agente, ni slučajno ne smiješ da radiš sam
     i 1 zadatak koji uradiš sam"          (lang-ok: his own words, quoted)

WHY THE EXISTING GUARDS DID NOT CATCH IT — this is the part worth keeping:

  * agents_guard.py   blocks a session from ENDING while agents it launched are
                      still running. It guards agents that EXIST.
  * delegation_guard.py blocks ending a turn that asks the owner WHEN to start
                      already-approved work. It guards one question.

Neither ever asks whether a single agent was launched at all. A session that
quietly does everything itself, launches nothing and asks nothing, sails
through both — which is exactly what happened. The gap was not in either
guard's logic; it was that no guard owned this question.

THE MECHANIC: with delegation REQUIRED for this project, a turn that WROTE to
product files and launched NO agent cannot end. Reading, measuring, running
tests and answering him are always free — the rule is about who WRITES.

Coordinator bookkeeping is exempt by path, and the exemption is the honest one:
the task list, the proofs and the reports ARE the coordinator's own job, and
delegating them would be delegating the thing he asked me to do personally.

Turning it on: put a `.claude/delegation-required` file in the project (any
content; a line saying who asked and when is good manners). Absent = the guard
sleeps, so no other project is affected by his ruling here.

Class: GATE — wired machine-wide in ~/.claude/settings.json (Stop).
Contract: exit 2 = BLOCK (stderr is fed back to the session); exit 0 = pass.
Fail-open on a crash of the guard itself, never on an unreadable transcript.
"""

import json
import os
import sys
from pathlib import Path

MARKER = ".claude/delegation-required"

#: tool names that launch a subagent in this harness
AGENT_TOOLS = {"Task", "Agent"}

#: tool names that WRITE. Reading and measuring are always free.
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

#: Paths the coordinator owns personally — the task list, the proofs, the
#: reports, and its own scratch. Writing these is not the work he meant.
EXEMPT_PARTS = (
    "/.claude/",
    "\\.claude\\",
    "/scratchpad/",
    "\\scratchpad\\",
    "session-tasks.md",
    "session-report.md",
    "layout-proof.md",
    "visual-proof.json",
)

BLOCK = """DELEGATION IS REQUIRED HERE (owner decree 2026-08-09, {marker}):
this turn wrote to {count} product file(s) and launched NO agent.

His instruction, at the start of the session he then watched go wrong:
"ako sam ti rekao da angazujes agente, ni slucajno ne smijes da radis sam i
1 zadatak koji uradis sam."

Files this turn wrote:
{files}

WHAT TO DO — not "acknowledge", DO:
  1. Decide what the piece of work actually is, and give it to an agent with
     the Agent tool: exact files, exact deliverable, the weakest model tier
     that can do it.
  2. VERIFY what comes back. That half is yours and cannot be delegated:
     run the gates, read the diff, open the pictures.
  3. Your OWN hands stay free for coordination, measurement, the task list,
     the proofs and answering him.

Reading, measuring, running tests and writing the task list are always
allowed. This blocks WRITING product code with nobody checking you.
"""


def transcript_lines(path: str):
    if not path or not os.path.isfile(path):
        return
    with open(path, encoding="utf-8", errors="replace") as handle:
        yield from handle


def is_exempt(target: str) -> bool:
    low = target.replace("\\", "/").lower()
    return any(part.replace("\\", "/").lower() in low for part in EXEMPT_PARTS)


def marker_for(cwd: str) -> Path | None:
    """The project's own opt-in, searched from the working directory upward —
    a session may be running in a subfolder of the project that carries it."""
    here = Path(cwd or ".").resolve()
    for folder in (here, *here.parents):
        candidate = folder / MARKER
        if candidate.is_file():
            return candidate
    return None


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return
    marker = marker_for(payload.get("cwd") or os.getcwd())
    if marker is None:
        return                      # this project never asked for delegation

    written: list[str] = []
    launched = 0
    for raw in transcript_lines(payload.get("transcript_path") or ""):
        try:
            entry = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        message = entry.get("message") or {}
        blocks = message.get("content")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if name in AGENT_TOOLS:
                launched += 1
                continue
            if name not in WRITE_TOOLS:
                continue
            target = str((block.get("input") or {}).get("file_path") or "")
            if target and not is_exempt(target):
                written.append(target)

    if launched or not written:
        return

    # Newest first, and only a handful: the point is to be recognised, not
    # to be exhaustive.
    unique: list[str] = []
    for path in reversed(written):
        if path not in unique:
            unique.append(path)
        if len(unique) >= 8:
            break
    listing = "\n".join(f"  - {p}" for p in unique)
    if len(written) > len(unique):
        listing += f"\n  … and {len(written) - len(unique)} more write(s)"
    sys.stderr.write(BLOCK.format(marker=marker, count=len(set(written)),
                                  files=listing))
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
    if payload.get("hook_event_name", "") != "Stop":
        sys.exit(0)
    try:
        check_stop(payload)
    except SystemExit:
        raise
    except Exception:   # a crash of the guard itself must not brick sessions
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
