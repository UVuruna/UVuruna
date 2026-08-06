#!/usr/bin/env python3
"""Agents guard - owner decree 2026-08-06 ("Agents Are Not Daemons").

Born from a real breakdown, the same evening the delegation rule landed:
a coordinator launched background agents per project and then went on with
its own life - nobody could say WHICH agents ran, WHAT they were doing or
WHEN they finished; the owner learned about them from windows flashing
across his screen and from phone notifications he could not attribute.
Months of established practice say the opposite: THE SESSION THAT LAUNCHES
AGENTS OWNS THEM - it presents the roster, tracks every agent, collects
every result, and reports the outcomes. An agent is a delegated JOB with an
owner, never a daemon.

Wired MACHINE-WIDE in ~/.claude/settings.json (Stop):

  A session whose transcript launched subagents (Task/Agent tool calls) may
  not end unless `.claude/agents-ledger.md` (found from cwd upward, like the
  layout proof) names the CURRENT session and accounts for every launched
  agent - and no agent is still marked RUNNING. Ending with a running agent
  means either WAIT AND COLLECT, or explicitly hand the state to the owner
  in the ledger (HANDED OVER - <what, where, how to check>).

Ledger format (one line per launched agent):

    SESSION: <session id>
    - [x] sonnet - Aviator layout audit - DONE - commit 1.1.052, verified
    - [ ] sonnet - PromptPainter audit expansion - RUNNING - started 18:40
    - [x] sonnet - X - HANDED OVER - uncommitted tree in <path>, owner told

Contract: exit 2 = BLOCK (stderr fed back); exit 0 = pass. Fail-open on any
parse error - a broken guard must never brick a session.
"""

import json
import os
import re
import sys
from pathlib import Path

LEDGER_FILENAME = "agents-ledger.md"

#: tool names that launch a subagent in this harness
AGENT_TOOLS = {"Task", "Agent"}

RUNNING_RE = re.compile(r"\bRUNNING\b", re.IGNORECASE)

BLOCK = (
    "AGENTS ARE NOT DAEMONS (rules/PLAN.md, owner decree 2026-08-06): this "
    "session LAUNCHED {count} subagent(s) and its ledger does not account "
    "for them, so it may not end.\n"
    "Launched:\n{spawned}\n"
    "{detail}\n"
    "The session that launches agents OWNS them: write {target} with one "
    "line per agent -\n\n"
    "    SESSION: {session}\n"
    "    - [x] <tier> - <job> - DONE - <evidence: commits, files, results "
    "you actually verified>\n"
    "    - [x] <tier> - <job> - HANDED OVER - <exact state left behind + "
    "where + how the owner checks it>\n\n"
    "An agent still RUNNING is not an exit: WAIT for it and collect its "
    "result, or hand it over EXPLICITLY (HANDED OVER line + tell the owner "
    "in chat). A launched agent nobody accounts for is a daemon, and the "
    "owner has already lived the consequence: unattributable windows "
    "flashing over his work."
)


def spawned_agents(transcript_path: str) -> list:
    """Every subagent this session launched: (label, is_background)."""
    agents = []
    if not transcript_path or not os.path.isfile(transcript_path):
        return agents
    with open(transcript_path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            message = entry.get("message") or {}
            blocks = message.get("content")
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                if block.get("name") not in AGENT_TOOLS:
                    continue
                tool_input = block.get("input") or {}
                label = (tool_input.get("description")
                         or str(tool_input.get("prompt") or "")[:60]
                         or "<agent>")
                agents.append(str(label).strip())
    return agents


def find_ledger(start: Path):
    for directory in (start, *start.parents):
        candidate = directory / ".claude" / LEDGER_FILENAME
        if candidate.is_file():
            return candidate
    return None


def _snippet(label: str) -> str:
    """The comparable core of an agent label: lowercased, whitespace
    collapsed, first 24 chars - enough to demand the ledger really names
    THIS job, loose enough to survive rephrasing."""
    return re.sub(r"\s+", " ", label.lower()).strip()[:24]


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return
    agents = spawned_agents(payload.get("transcript_path") or "")
    if not agents:
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    session = str(payload.get("session_id") or "").strip() or "<session id>"
    ledger = find_ledger(cwd)
    listing = "".join(f"  - {a}\n" for a in agents)

    missing = []
    if ledger is None:
        detail = f"No {LEDGER_FILENAME} exists anywhere above {cwd}."
        target = cwd / ".claude" / LEDGER_FILENAME
    else:
        text = ledger.read_text(encoding="utf-8", errors="replace")
        target = ledger
        lower = text.lower()
        if session not in text:
            missing.append(f"it does not name this session ({session}) - "
                           "an earlier session's ledger does not carry over")
        if RUNNING_RE.search(text):
            missing.append("it still holds a RUNNING agent - wait and "
                           "collect, or mark it HANDED OVER with the exact "
                           "state left behind")
        bullet_count = len(re.findall(r"^\s*-\s*\[", text, re.MULTILINE))
        unnamed = [a for a in agents
                   if _snippet(a) and _snippet(a) not in lower]
        if unnamed and bullet_count < len(agents):
            missing.append("these launched agents appear nowhere in it: "
                           + "; ".join(unnamed))
        if not missing:
            return
        detail = f"{ledger} exists, but " + "; ".join(missing) + "."

    print(BLOCK.format(count=len(agents), spawned=listing, detail=detail,
                       target=target, session=session), file=sys.stderr)
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
    except Exception:  # a broken guard must never brick a session
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
