"""SubagentStop: a sub-agent that edited product files must have RUN something."""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import paths, transcript as transcript_mod

RUN_RE = re.compile(r"uv\.py|\buv\s+(test|shot|run|device)\b|pytest"
                    r"|run_guards|python\s+-m\b", re.I)
#: `! ev-…` at line start, also behind a list marker, backticks or bold
BANG_RE = re.compile(r"^\s*(?:[-*>]\s*)?[`*_]*!\s*[`*_]*\S", re.M)


def _agent_transcript(payload: dict) -> str:
    """The SUB-AGENT's own transcript. The harness hands SubagentStop the
    PARENT session's path, so resolve the agent file: an explicit
    `agent_transcript_path`/`agent_id` when present, else the most recently
    modified `agent-*.jsonl` under the parent's `subagents/` folder."""
    given = str(payload.get("agent_transcript_path") or "")
    if given and os.path.isfile(given):
        return given
    parent = str(payload.get("transcript_path") or "")
    if transcript_mod.is_subagent_transcript(parent):
        return parent
    if not parent:
        return ""
    sub = Path(parent).with_suffix("") / "subagents"
    agent_id = str(payload.get("agent_id") or "")
    if agent_id:
        candidate = sub / f"agent-{agent_id}.jsonl"
        if candidate.is_file():
            return str(candidate)
    try:
        files = sorted(sub.glob("agent-*.jsonl"),
                       key=lambda f: f.stat().st_mtime, reverse=True)
    except OSError:
        files = []
    return str(files[0]) if files else parent


def run(payload: dict) -> list[str] | None:
    cwd = Path(payload.get("cwd") or os.getcwd())
    root = paths.project_root(cwd)
    model = transcript_mod.load(_agent_transcript(payload))

    product_edits = model.product_edits(root)
    if not product_edits:
        return None
    last_edit = max((t.index for t in product_edits), default=-1)

    ran = [t for t in model.runs()
           if t.index > last_edit
           and RUN_RE.search(str(t.input.get("command") or ""))]
    if not ran:
        return [
            "This sub-agent edited product files but ran nothing after its "
            "last edit.",
            "FIX: run `python rules/tools/uv.py test|shot` (or the project's "
            "run_guards) and report the result.",
            f"where: {product_edits[-1].file_path}",
        ]
    # The sub-agent's report may not be flushed to its transcript when the
    # SubagentStop hook fires, and every block is appended as a user record;
    # so look at the LAST assistant texts overall, never only "after the last
    # user message" — otherwise a blocked agent can never unblock itself.
    texts = [m.text for m in model.messages
             if m.role == "assistant" and m.text.strip()]
    recent = "\n".join(texts[-3:])
    if not BANG_RE.search(recent):
        return [
            "This sub-agent's report carries no `! ` evidence line.",
            "FIX: add plain lines starting with `! ` (e.g. "
            "`! ev-0004 test tests/test_x.py 6/6`) at the end of your final "
            "message; keep the rest of the report as it is.",
            "where: final report",
        ]
    return None
