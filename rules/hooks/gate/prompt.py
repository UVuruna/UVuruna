"""UserPromptSubmit: make the session's ledger and evidence dir exist. Never blocks."""

from __future__ import annotations

import os
from pathlib import Path

from . import paths

TEMPLATE = Path(__file__).resolve().parent.parent.parent / "templates" / \
    "ledger.md"

REMINDER = (
    "ledger: {path}",
    "  Header: `kategorija: GUI|FEATURE|BUGFIX|REFACTOR|DOCS|PLAN|BUILD · "
    "klasa: Trivial|Standard|Wide · agenti: <n model role>`",
    "  Tasks: `- [ ]` not started · `[>]` in progress · `[?]` waits for the "
    "owner (needs a `?` line) · `[~]` done, unproven · `[x]` done WITH "
    "evidence (needs a `!` line)",
    "  `!` lines name an ev-NNNN id from evidence.jsonl; evidence is written "
    "ONLY by `python rules/tools/uv.py test|shot|run|device`.",
    "  FEATURE writes its `matrica:` table BEFORE the first product edit; "
    "BUGFIX writes `uzrok:`; a repeat writes `proces-uzrok:`.",
    "  No product-file edit happens before the header line exists.",
)


def run(payload: dict) -> list[str] | None:
    cwd = Path(payload.get("cwd") or os.getcwd())
    root = paths.project_root(cwd)
    session_id = str(payload.get("session_id") or "").strip() or "unknown"

    ledger = paths.ledger_path(root, session_id)
    try:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        paths.evidence_dir(root, session_id).mkdir(parents=True, exist_ok=True)
        paths.evidence_current(root).write_text(session_id + "\n",
                                                encoding="utf-8")
    except OSError:
        pass

    fresh = not ledger.is_file()
    if fresh:
        try:
            skeleton = TEMPLATE.read_text(encoding="utf-8")
        except OSError:
            skeleton = ("# <session title>\n"
                        "kategorija: <CATEGORY> · klasa: <class> · "
                        "agenti: <none>\n")
        try:
            ledger.write_text(skeleton, encoding="utf-8")
        except OSError:
            fresh = False

    if fresh:
        print("\n".join(line.format(path=ledger) for line in REMINDER))
    else:
        print(f"ledger: {ledger}")
    return None
