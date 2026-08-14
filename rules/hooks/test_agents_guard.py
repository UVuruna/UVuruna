"""Checks for `agents_guard.py` — THE FIRST TEST ANY HOOK IN THIS FOLDER HAS.

Written 2026-08-14, on the owner's instruction to fix two long-standing
annoyances. The hook blocks the end of a session while an agent it spawned is
still running, and it was blocking sessions in which nothing was running at
all: a turn cut off mid-flight — he interrupts, the window closes, the process
dies — leaves the assistant record carrying the `tool_use` block on disk while
the `tool_result` never gets written, and the hook read that as "an agent is
still starting".

WHY THIS FILE EXISTS AT ALL, and it is the more useful half of the round:
every guard in this folder is enforcement that nothing enforces back. Driving
this one over synthetic transcripts immediately found a SECOND defect nobody
had reported, because its symptom is silence rather than a block —
`launch_result[:80] in raw` compared a DECODED result string, carrying real
newlines, against the JSON line where those newlines are an escape sequence.
Every launch result contains a newline, so the comparison could never be true,
the launch record always counted as its own life sign, and a background agent
that never finished has NEVER been reported by this guard for as long as that
branch has existed. A guard that cannot fire is worse than no guard: it is
believed.

Both fixes are held here, and each check was proven by planting its own defect
(revert the fix, watch that one check go red, restore).

ONE WARNING FOR WHOEVER PLANTS NEXT, because it cost an hour and produced a
convincing wrong answer: `__pycache__` MUST be cleared between plants. Swapping
one defect for another writes the file faster than the filesystem's mtime
granularity can distinguish, so Python happily reuses the PREVIOUS plant's
compiled module — which made a restored, correct file look broken and would
just as easily have made a broken one look fixed. A planting sweep that does
not clear the cache is not evidence.

Run:  python rules/hooks/test_agents_guard.py
"""

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agents_guard  # noqa: E402


# ═══════════════════════════ TRANSCRIPT BUILDING ═══════════════════════════
def _record(**kw) -> str:
    return json.dumps(kw) + "\n"


def _tool_use(uid: str, desc: str = "my agent") -> str:
    """The record the harness writes when an agent is SPAWNED."""
    return _record(message={"content": [{
        "type": "tool_use", "name": "Task", "id": uid,
        "input": {"description": desc}}]})


def _tool_result(uid: str, text: str) -> str:
    """The record the harness writes when that call RETURNS. For a background
    agent this is only the launch metadata; for a synchronous one it is the
    agent's whole report, which IS the completion."""
    return _record(message={"content": [{
        "type": "tool_result", "tool_use_id": uid, "content": text}]})


def _chat(n: int = 1) -> str:
    """Ordinary conversation records — what "the transcript moved on" means."""
    return "".join(_record(message={"content": [{"type": "text",
                                                 "text": f"turn {i}"}]})
                   for i in range(n))


ASYNC_LAUNCH = ("Async agent launched successfully.\n"
                "agentId: abc123xyz (internal ID)")


def _blocks(lines: list) -> bool:
    """Runs the real hook over a real file and reports whether it BLOCKED —
    never a re-implementation of its logic, which would only prove this file
    agrees with itself. Output is swallowed: the hook prints its complaint to
    stdout/stderr and this is not the place to read it."""
    # `mkstemp` hands back an OPEN descriptor, and Windows refuses to unlink a
    # file another handle still holds — close it before writing, or every
    # check after the first dies in the `finally` below.
    handle, name = tempfile.mkstemp(suffix=".jsonl")
    os.close(handle)
    path = Path(name)
    path.write_text("".join(lines), encoding="utf-8")
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            agents_guard.check_stop({"transcript_path": str(path)})
        return False
    except SystemExit as exit_code:
        return bool(exit_code.code)
    finally:
        path.unlink(missing_ok=True)


# ═══════════════════════════ THE CHECKS ═══════════════════════════
def check_a_truncated_turn_does_not_block() -> bool:
    """THE OWNER'S OWN COMPLAINT. A `tool_use` with no `tool_result`, and then
    the conversation carries on for several records — which can only mean the
    call was abandoned when a turn was cut, because the harness writes a
    result before the conversation can move past it.

    PLANTED DEFECT: remove the `STALE_AFTER_RECORDS` branch and this check goes
    red while every other one stays green."""
    return not _blocks([_tool_use("u1"), _chat(6)])


def check_a_spawn_at_the_very_end_still_blocks() -> bool:
    """The other side of the same coin, and the reason the fix is a MARGIN
    rather than "ignore a missing result": an agent launched a moment before
    the Stop hook fires legitimately has no result yet, and that one must
    still hold the session open. Without this check the fix above could be
    "never block", which would be no guard at all.

    PLANTED DEFECT: widen `STALE_AFTER_RECORDS` to a large number and this
    check goes red."""
    return _blocks([_chat(3), _tool_use("u2")])


def check_a_finished_synchronous_agent_does_not_block() -> bool:
    """A synchronous agent's `tool_result` IS its report, so the call is over
    the moment the result exists. Held so a fix aimed at the background case
    cannot start blocking on ordinary finished work."""
    return not _blocks([_tool_use("u3"),
                        _tool_result("u3", "here is the report"),
                        _chat(3)])


def check_a_background_agent_with_no_life_sign_still_blocks() -> bool:
    """THE DEFECT NOBODY REPORTED, found by driving the hook rather than by
    reading it. A background agent launched with an `agentId` and never
    mentioned again is exactly what this guard exists to catch — and it never
    once caught it, because the launch record was matched against itself with
    a comparison that could not be true (see the module docstring). The record
    is skipped by its INDEX now.

    PLANTED DEFECT: restore `if launch_result[:80] in raw: continue` and this
    check goes red."""
    return _blocks([_tool_use("u4"), _tool_result("u4", ASYNC_LAUNCH), _chat(3)])


def check_a_background_agent_with_a_life_sign_does_not_block() -> bool:
    """…and the index skip must not go the other way: a later record naming
    that agent (the harness's completion notification) is the life sign, and a
    fix that counted the launch record as one would make every background
    agent look finished the instant it started.

    PLANTED DEFECT: skip by index >= instead of ==, so real mentions are
    swallowed too, and this check goes red."""
    return not _blocks([
        _tool_use("u5"), _tool_result("u5", ASYNC_LAUNCH),
        _record(message={"content": [{"type": "text",
                                      "text": "task abc123xyz completed"}]}),
        _chat(2)])


def check_a_session_with_no_agents_never_blocks() -> bool:
    """The commonest session of all. Cheap, and it is the check that would
    catch a fix which accidentally blocks on an empty transcript."""
    return not _blocks([_chat(10)])


CHECKS = [
    ("a truncated turn is not an unfinished agent",
     check_a_truncated_turn_does_not_block),
    ("an agent spawned at the very end still holds the session open",
     check_a_spawn_at_the_very_end_still_blocks),
    ("a finished synchronous agent never blocks",
     check_a_finished_synchronous_agent_does_not_block),
    ("a background agent with no life sign DOES block (it never did)",
     check_a_background_agent_with_no_life_sign_still_blocks),
    ("a background agent with a life sign does not block",
     check_a_background_agent_with_a_life_sign_does_not_block),
    ("a session that spawned nothing never blocks",
     check_a_session_with_no_agents_never_blocks),
]


if __name__ == "__main__":
    print("=== AGENTS GUARD CHECKS ===")
    failed = 0
    for name, fn in CHECKS:
        try:
            ok = fn()
        except Exception as exc:  # a check may not die silently
            print(f"  ERROR {name}: {exc!r}")
            ok = False
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        failed += 0 if ok else 1
    if failed:
        print(f"\nAGENTS GUARD CHECKS FAILED — {failed} check(s).")
        sys.exit(1)
    print("\nAGENTS GUARD CHECKS PASSED — a cut-off turn ends the session, and "
          "an agent that really is running still holds it open.")
