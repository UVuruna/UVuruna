"""THE DELEGATION GUARD — owner decree 2026-08-06 ("zubi, ne memorija").

Born from a real failure the same day: a session finished a Wide planning
round, every verdict was settled, the scope stood approved — and the agent
ended the turn asking the owner "do I start now or in a fresh session?".
The owner had to answer a scheduling question that was never his to answer:
once the verdicts are in, the coordinator designs the agent roster,
presents it, and LAUNCHES in the same turn. A memory note had already
recorded this once; the owner's ruling is that only a CHECK holds.

The mechanically catchable defect is the SCHEDULING ASK: ending a turn that
still has open session tasks while the chat text asks the owner whether or
when to start the already-approved work. That is what this Stop hook
blocks — even when `WAITING_ON_OWNER: yes` is set, because a scheduling
question is precisely the illegitimate use of that flag. The wider mandate
("a big task is EXECUTED BY AGENTS, the session only coordinates") rides
this gate: with the scheduling ask blocked, the only lawful ways to end are
genuine content questions or finished work.

Class: GATE — wired machine-wide in ~/.claude/settings.json (Stop).
"""

import json
import os
import re
import sys
from pathlib import Path

# Serbian (Latin) and English forms of "do I start now / this session or a
# fresh one / awaiting your word to begin". Deliberately narrow: a genuine
# CONTENT question to the owner must never trip this — only the
# start-scheduling ask does.
SCHEDULING_ASK_RE = re.compile(
    r"da li da\s+(odmah\s+)?(krenem|po[čc]nem)"
    r"|kada?\s+da\s+(krenem|po[čc]nem)"
    r"|da li\s+([žz]eli[šs]|ho[ćc]e[šs])\s+da\s+(krenem|po[čc]nem)"
    r"|ako\s+ka[žz]e[šs]\s*[„\"‚'„“]*\s*(kreni|nova sesija)"
    r"|preporu[čc]ujem\s+(sve[žz]u|novu)\s+sesiju"
    r"|(ovoj|istoj)\s+sesiji\s+ili\s+"
    r"|[čc]ekam\s+(tvoju\s+)?re[čc]\s+da\s+(krenem|po[čc]nem)"
    r"|awaiting the owner'?s word to start"
    r"|(when|shall|should)\s+i\s+(start|begin)\b"
    r"|this session or a fresh",
    re.I,
)

BLOCK_SCHEDULING = (
    "THE DELEGATION GUARD (rules/PLAN.md -> Delegation Is Not a Question, "
    "GATE of 2026-08-06): this turn asks the owner WHETHER or WHEN to start "
    "work that is already approved and still open in session-tasks.md. "
    "Scheduling is not the owner's job. Once the verdicts are settled: "
    "(1) design which agent executes which job (each job its own agent "
    "session, weakest capable tier, exact files, structured deliverable), "
    "(2) present the roster in one message, (3) LAUNCH the first wave in "
    "that same message, (4) report between waves. Remove the scheduling "
    "question, launch, then end the turn."
)


def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def entry_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
    return "\n".join(parts)


def is_real_user_prompt(entry: dict) -> bool:
    if entry.get("type") != "user":
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(
            isinstance(item, dict) and item.get("type") == "tool_result"
            for item in content
        )
    return False


def collect_final_text(transcript_path: str) -> str:
    """The LAST assistant message only. The scheduling ask matters at the
    moment of ENDING — and scanning the whole turn bit its own tail the
    day this guard was born: an earlier status message QUOTED the banned
    phrase while describing this very rule ('pitanje "kada da krenem" je
    defekt'), and the turn-wide scan then blocked every Stop until the
    next owner prompt. The final message is where the decision to end
    lives; it is the only one this guard reads."""
    final = ""
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "assistant":
                text = entry_text(entry.get("message") or {})
                if text:
                    final = text
    return final


# Text standing inside quotation marks is someone's words being CITED —
# a rule being documented, an owner sentence being echoed back — never
# the agent asking. Stripped before the ask patterns run.
QUOTED_SPAN_RE = re.compile(r"[„\"“‚'»]([^„“”\"‚'«»]{0,120}?)[”“\"'«]")


def strip_quotations(text: str) -> str:
    return QUOTED_SPAN_RE.sub(" ", text)


def open_tasks_exist(cwd: Path) -> bool:
    for directory in (cwd, *cwd.parents):
        tasks_file = directory / ".claude" / "session-tasks.md"
        try:
            if tasks_file.is_file():
                text = tasks_file.read_text(encoding="utf-8", errors="replace")
                return bool(re.search(r"^\s*- \[ \]", text, re.M))
        except OSError:
            return False
    return False


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    if not open_tasks_exist(cwd):
        return
    path = payload.get("transcript_path") or ""
    try:
        text = collect_final_text(path)
    except OSError:
        return
    if not text:
        return
    if SCHEDULING_ASK_RE.search(strip_quotations(text)):
        block(BLOCK_SCHEDULING)


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
