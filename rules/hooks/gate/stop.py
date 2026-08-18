"""Stop: agents, ledger grammar, category teeth, evidence integrity, the
final message, and the build question. First block wins.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import changed_files

from . import (agents, build_guard, evidence as evidence_mod, ledger as
               ledger_mod, paths, teeth, structure)

MERMAID_RE = re.compile(r"```\s*(mermaid|graphviz|dot|plantuml)\b", re.I)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^()\s]+)\)")
IMAGE_SUFFIX_RE = re.compile(r"\.(?:png|jpe?g|svg|gif|bmp)$", re.I)
FENCE_RE = re.compile(r"^\s*```")
BUILD_HEADING_RE = re.compile(r"##\s*BUILD\s*&\s*RELEASE\s*\?", re.I)
INSTALLABLE_RE = re.compile(r"^\s*installable\s*:\s*yes\b", re.I | re.M)

SHORT_FINAL = 120
LONG_EARLIER = 600

SIZE_LIMITS = (
    (re.compile(r"(^|/)CLAUDE\.md$", re.I), 6 * 1024),
    (re.compile(r"(^|/)rules/[A-Z0-9_-]+\.md$"), 5 * 1024),
)
SIZE_EXEMPT = re.compile(r"(^|/)rules/(START\.md|history/|howto/|briefs/)",
                         re.I)


# ═══════════════════════════ helpers ═══════════════════════════

def _visible_lines(text: str):
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced or line.startswith("    "):
            continue
        yield re.sub(r"`[^`]*`", "", line)


def _mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


# ═══════════════════════════ checks ═══════════════════════════

def _ledger_checks(led, model) -> list[str] | None:
    if not led.exists or not led.categories:
        return [
            "No session ledger (or no `kategorija:` line) — work happened with "
            "nothing recorded.",
            "FIX: write the ledger: header line, one task per deliverable, `!` "
            "evidence lines under each finished task.",
            f"where: {led.path}",
        ]
    owner = model.last_owner_message()
    stamp = _mtime(led.path)
    if owner and owner.ts and stamp and stamp < owner.ts:
        return [
            "The ledger was not touched this turn — its tasks describe an "
            "older round.",
            "FIX: update task states and `!` evidence lines before ending.",
            f"where: {led.path}",
        ]
    for task in led.done_tasks():
        if not task.bangs:
            return [
                f"Task `{task.text[:50]}` is [x] with no `!` evidence line.",
                "FIX: add `! ev-NNNN <what ran> <result>` under it, or mark it "
                "[~] (done, unproven).",
                f"where: {led.path}:{task.line}",
            ]
    for task in led.waiting_tasks():
        if not task.questions:
            return [
                f"Task `{task.text[:50]}` is [?] with no `?` question.",
                "FIX: write the question the owner must answer on a `?` line "
                "under it.",
                f"where: {led.path}:{task.line}",
            ]
    open_tasks = led.open_tasks()
    if open_tasks and not led.waiting_tasks():
        return [
            f"{len(open_tasks)} task(s) are still open and nothing waits on "
            "the owner.",
            "FIX: finish them, mark [~] with what is missing, or turn one into "
            "[?] with a `?` question.",
            f"where: {led.path}:{open_tasks[0].line}",
        ]
    return None


def _teeth(led, evid, model, root: Path, product_edits) -> list[str] | None:
    problem = structure.check_stop(led, model, product_edits)
    if problem:
        return problem
    if led.has("GUI"):
        gui_edits = [t for t in product_edits
                     if changed_files.is_gui_path(t.file_path)]
        problem = teeth.gui(led, evid, model, gui_edits)
        if problem:
            return problem
    if led.has("FEATURE"):
        problem = teeth.feature(led, evid, product_edits)
        if problem:
            return problem
    if led.has("BUGFIX"):
        problem = teeth.bugfix(led, evid, model, product_edits)
        if problem:
            return problem
    if led.has("REFACTOR"):
        problem = teeth.refactor(led, evid, product_edits, root)
        if problem:
            return problem
    return structure.check_review(led, model, product_edits)


def _evidence_integrity(model, root: Path) -> list[str] | None:
    for tool in model.edits():
        if paths.is_evidence_path(tool.file_path):
            return [
                "An agent wrote into the evidence file — evidence is produced "
                "by the machine only.",
                "FIX: revert that edit and produce the rows with `python "
                "rules/tools/uv.py test|shot|run|device`.",
                f"where: {tool.file_path}",
            ]
    return None


def _rules_size(model, root: Path) -> list[str] | None:
    edited = []
    for tool in model.edits():
        path = tool.file_path.replace("\\", "/")
        if SIZE_EXEMPT.search(path):
            continue
        for pattern, limit in SIZE_LIMITS:
            if pattern.search(path):
                edited.append((Path(path), limit))
                break
    if not edited:
        return None
    script = root / "rules" / "tools" / "rules_size_guard.py"
    if script.is_file():
        try:
            done = subprocess.run([sys.executable, str(script)], cwd=str(root),
                                  capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0:
            tail = (done.stdout or done.stderr or "").strip().splitlines()
            return [
                "Rules-size guard fails — a rulebook grew past its limit.",
                "FIX: move the story to rules/history/ and keep the checklist.",
                f"where: {tail[-1][:100] if tail else script}",
            ]
        return None
    for path, limit in edited:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > limit:
            return [
                f"{path.name} is {size // 1024} KB, over its {limit // 1024} "
                "KB limit.",
                "FIX: rules are checklists — move the story to "
                "rules/history/ and keep WHAT · WHO CHECKS · EVIDENCE.",
                f"where: {path}",
            ]
    return None


def _communication(model, root: Path, cwd: Path) -> list[str] | None:
    texts = model.final_turn_texts()
    if not texts:
        return [
            "The turn ends with no message — the owner sees nothing.",
            "FIX: write the final block: what was done, evidence, what he must "
            "answer.",
            "where: end of turn",
        ]
    final = texts[-1]
    if MERMAID_RE.search(final):
        return [
            "The final message contains raw diagram source — the owner's "
            "interface shows it as garbage text.",
            "FIX: describe the flow in prose, or render it as an Artifact "
            "page; diagram source belongs in doc files only.",
            "where: final message",
        ]
    dead = []
    for line in _visible_lines(final):
        for target in MD_LINK_RE.findall(line):
            if re.match(r"^(?:https?|mailto|#)", target, re.I):
                continue
            raw = target.split("#", 1)[0].replace("%20", " ")
            if not (IMAGE_SUFFIX_RE.search(raw) or raw.endswith("/")):
                continue
            candidate = Path(raw)
            alive = (candidate.exists() if candidate.is_absolute()
                     or re.match(r"^[A-Za-z]:", raw)
                     else any((base / raw).exists() for base in (root, cwd)))
            if not alive:
                dead.append(raw)
    if dead:
        return [
            f"Link(s) in the final message open nothing: {', '.join(dead[:3])}",
            "FIX: write every target as a path from the monorepo root with "
            "forward slashes, and check it exists.",
            "where: final message",
        ]
    if len(final.strip()) < SHORT_FINAL and \
            any(len(t.strip()) > LONG_EARLIER for t in texts[:-1]):
        return [
            "The turn ends with a one-liner after a long block — on his phone "
            "the owner sees ONLY the last block.",
            "FIX: repeat the whole report in the final message: status per "
            "task, evidence, and the answer to every question he asked.",
            "where: final message",
        ]
    return None


def _installable(led, model, root: Path, product_edits) -> list[str] | None:
    if not product_edits:
        return None
    claude = root / "CLAUDE.md"
    declared = False
    try:
        declared = bool(INSTALLABLE_RE.search(
            claude.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        pass
    has_builder = (root / "setup" / "build.py").is_file() or \
        (root / "build.py").is_file()
    if not (declared or has_builder):
        return None
    for tool in model.runs():
        if build_guard.is_build_command(str(tool.input.get("command") or "")):
            return None  # a build already ran on his word
    final = model.final_text()
    waiting_build = any("build" in task.text.lower()
                        for task in led.waiting_tasks())
    if BUILD_HEADING_RE.search(final) and waiting_build:
        return None
    return [
        "This project is installable and product files changed, but the owner "
        "is never asked to build.",
        "FIX: end with a `## BUILD & RELEASE?` heading naming the version and "
        "the command, and add a `[?]` BUILD task with its `?` line.",
        f"where: {led.path}",
    ]


# ═══════════════════════════ entry ═══════════════════════════

def run(payload: dict) -> list[str] | None:
    from . import transcript as transcript_mod

    if payload.get("stop_hook_active"):
        return None
    cwd = Path(payload.get("cwd") or os.getcwd())
    root = paths.project_root(cwd)
    session_id = str(payload.get("session_id") or "").strip() or "unknown"
    model = transcript_mod.load(payload.get("transcript_path") or "")

    problem = agents.check(model)
    if problem:
        return problem

    led = ledger_mod.load(paths.ledger_path(root, session_id))
    evid = evidence_mod.load(paths.evidence_file(root, session_id))
    product_edits = model.product_edits(root)

    if product_edits or led.open_tasks():
        for step in (
            lambda: _ledger_checks(led, model),
            lambda: _teeth(led, evid, model, root, product_edits),
            lambda: _evidence_integrity(model, root),
            lambda: _rules_size(model, root),
        ):
            problem = step()
            if problem:
                return problem

    problem = _communication(model, root, cwd)
    if problem:
        return problem
    return _installable(led, model, root, product_edits)
