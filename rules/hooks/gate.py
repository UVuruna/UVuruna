#!/usr/bin/env python3
"""THE hook dispatcher: `gate.py prompt|pre|stop|subagent`.

Reads the hook payload from stdin (session_id, transcript_path, cwd,
hook_event_name, tool_name, tool_input), parses the transcript once and runs
the checks of that event (rules/hooks/gate/*.py).

Contract: exit 2 = BLOCK, stderr is at most three lines — WHAT is wrong, the
exact FIX, where. Exit 0 = pass. A crash of the gate itself fails OPEN with a
one-line warning: a broken guard must never brick a session.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

EVENTS = ("prompt", "pre", "stop", "subagent")
MAX_BLOCK_LINES = 3


def emit(lines) -> None:
    text = "\n".join(str(line).strip() for line in lines[:MAX_BLOCK_LINES])
    print(text, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    event = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
    if event not in EVENTS:
        print(f"gate: unknown event {event!r} (use {'|'.join(EVENTS)})",
              file=sys.stderr)
        sys.exit(0)

    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            sys.exit(0)
    except (json.JSONDecodeError, ValueError, OSError):
        sys.exit(0)

    try:
        if event == "prompt":
            from gate.prompt import run
        elif event == "pre":
            from gate.pre import run
        elif event == "stop":
            from gate.stop import run
        else:
            from gate.subagent import run
        problem = run(payload)
    except SystemExit:
        raise
    except Exception as error:  # the gate itself broke — never brick a session
        print(f"gate({event}) failed open: {type(error).__name__}: {error}",
              file=sys.stderr)
        sys.exit(0)

    if problem:
        emit(problem)
    sys.exit(0)


if __name__ == "__main__":
    main()
