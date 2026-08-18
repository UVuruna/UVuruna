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


def run(payload: dict) -> list[str] | None:
    cwd = Path(payload.get("cwd") or os.getcwd())
    root = paths.project_root(cwd)
    model = transcript_mod.load(payload.get("transcript_path") or "")

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
    if not BANG_RE.search(model.final_text()):
        return [
            "This sub-agent's report carries no `! ` evidence line.",
            "FIX: add plain lines starting with `! ` (e.g. "
            "`! ev-0004 test tests/test_x.py 6/6`) at the end of your final "
            "message; keep the rest of the report as it is.",
            "where: final report",
        ]
    return None
