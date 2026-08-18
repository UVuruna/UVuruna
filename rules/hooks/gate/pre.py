"""PreToolUse: category first, evidence untouchable, English, GUI APIs, builds."""

from __future__ import annotations

import os
from pathlib import Path

import changed_files

from . import (agents, ballot, build_guard, gui_api, language, scratch,
               ledger as ledger_mod, paths, transcript)


def _written(tool_input: dict) -> str:
    return language.written_text(tool_input)


def _edit(tool_input: dict, root: Path, session_id: str,
          model_of, cwd: Path) -> list[str] | None:
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    problem = scratch.check_edit_path(path, root, cwd)
    if problem:
        return problem
    if paths.is_evidence_path(path):
        return [
            "evidence.jsonl is written by the machine, never by an agent.",
            "FIX: produce the row with `python rules/tools/uv.py "
            "test|shot|run|device` and reference its ev-id in the ledger.",
            f"where: {path}",
        ]

    problem = language.check(tool_input)
    if problem:
        return problem

    text = _written(tool_input)
    if changed_files.is_gui_path(path):
        problem = gui_api.check(path, text)
        if problem:
            return problem

    if not paths.is_product_file(path, root):
        return None

    led = ledger_mod.load(paths.ledger_path(root, session_id))
    if not led.categories:
        return [
            "No category for this session — a product file may not be edited "
            "yet.",
            "FIX: write `kategorija: GUI|FEATURE|BUGFIX|REFACTOR|DOCS|PLAN|"
            "BUILD · klasa: … · agenti: …` at the top of the ledger.",
            f"where: {paths.ledger_path(root, session_id)}",
        ]

    if led.has("FEATURE") and not led.trivial and not led.has_matrix:
        model = model_of()
        if not model.product_edits(root):
            return [
                "FEATURE without a `matrica:` — the scenario table is written "
                "BEFORE the first product edit.",
                "FIX: add the matrix (row per scenario, mandatory rows: "
                "average device, fresh install; replacement ⇒ old path) with "
                "an evidence column.",
                f"where: {led.path}",
            ]
    return None


def _bash(tool_input: dict, model_of) -> list[str] | None:
    command = str(tool_input.get("command") or "")
    problem = scratch.check_command(command)
    if problem:
        return problem
    if not build_guard.is_build_command(command):
        return None
    model = model_of()
    last = model.last_owner_message()
    words = transcript.owner_text(last.text) if last else ""
    # The harness may hand a sub-agent's PreToolUse the PARENT transcript, so
    # "a sub-agent is running" counts as "this may be a sub-agent": while any
    # agent runs, nobody builds — the main session builds at the end, alone.
    subagent = model.is_subagent or bool(agents.still_running(model))
    return build_guard.check(command, subagent, words)


def run(payload: dict) -> list[str] | None:
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    cwd = Path(payload.get("cwd") or os.getcwd())
    root = paths.project_root(cwd)
    session_id = str(payload.get("session_id") or "").strip() or "unknown"

    cache: dict = {}

    def model_of():
        if "model" not in cache:
            cache["model"] = transcript.load(
                payload.get("transcript_path") or "")
        return cache["model"]

    if tool in paths.EDIT_TOOLS:
        return _edit(tool_input, root, session_id, model_of, cwd)
    if tool in ("Bash", "PowerShell"):
        return _bash(tool_input, model_of)
    if tool == "Artifact":
        if tool_input.get("action") in ("list", "comments", "reply", "resolve"):
            return None
        page_path = str(tool_input.get("file_path") or "")
        if not page_path:
            return None
        try:
            page = Path(page_path).read_text(encoding="utf-8",
                                             errors="replace")
        except OSError:
            return None
        problem = ballot.check(page_path, page,
                               [Path(page_path).parent, cwd, root])
        if problem:
            return problem
        return _seen_before_publish(page_path, root, session_id, model_of)
    return None


def _seen_before_publish(page_path: str, root: Path, session_id: str,
                         model_of) -> list[str] | None:
    """A page goes out only after the runner rendered it AND the agent opened
    the render (2026-08-18: an unreadable ballot reached the owner)."""
    from datetime import datetime, timezone
    from . import evidence as evidence_mod
    page = Path(page_path)
    try:
        edited = datetime.fromtimestamp(page.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None
    name = page.name.lower()
    rows = [r for r in evidence_mod.load(
                paths.evidence_file(root, session_id)).of_kind("device")
            if r.kind != "unavailable" and r.newer_than(edited)
            and name in str(r.data.get("cmd") or "").lower()]
    fix = (f"FIX: python rules/tools/uv.py device web-desktop "
           f"file:///{page.as_posix()} → open the PNG with Read → publish.")
    if not rows:
        return ["Publishing a page nobody rendered after its last edit.",
                fix, f"where: {page_path}"]
    latest = max((r.ts for r in rows if r.ts), default=None)
    seen = any(ts is not None and latest is not None and ts >= latest
               for _, ts in model_of().image_reads())
    if not seen:
        return ["The page was rendered but no one LOOKED at the render.",
                fix, f"where: {page_path}"]
    return None
