"""Stop: agents, ledger grammar, category teeth, evidence integrity, the
final message, and the build question. First block wins.
"""

from __future__ import annotations

import os
import re
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
RELEASE_WORD_RE = re.compile(r"(release|rilis|objav\w*)", re.I)

SHORT_FINAL = 120
LONG_EARLIER = 600

#: which edits make the size guard run — the LIMITS live only in
#: rules/tools/rules_size_guard.py
SIZE_PATTERNS = (
    re.compile(r"(^|/)CLAUDE\.md$", re.I),
    re.compile(r"(^|/)rules/[A-Z0-9_-]+\.md$"),
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

def _ledger_checks(led, model, agents_running: bool = False) -> list[str] | None:
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
    if agents_running:
        # delegated work in flight is honest as `[>]`; only untouched `[ ]`
        # tasks need a `[?]` beside them
        open_tasks = [t for t in open_tasks if t.state != ">"]
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
    """When a rulebook or a project CLAUDE.md was edited, ask THE size guard
    (rules/tools/rules_size_guard.py) — the one place the limits live."""
    touched = False
    for tool in model.edits():
        path = tool.file_path.replace("\\", "/")
        if SIZE_EXEMPT.search(path):
            continue
        if any(pattern.search(path) for pattern in SIZE_PATTERNS):
            touched = True
            break
    if not touched:
        return None
    tools_dir = str(Path(__file__).resolve().parents[2] / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import rules_size_guard
    except ImportError:
        return None
    repo_root = Path(__file__).resolve().parents[3]
    project = None if Path(root).resolve() == repo_root else root
    over = [row for row in rules_size_guard.check(project) if not row[3]]
    if not over:
        return None
    path, size, limit = over[0][0], over[0][1], over[0][2]
    return [
        f"{Path(str(path)).name} is {size} B, over its {limit} B limit.",
        "FIX: rules are checklists — move the story to rules/history/ and "
        "keep WHAT · WHO CHECKS · EVIDENCE.",
        f"where: {path}",
    ]


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


def _release(led, model) -> list[str] | None:
    """`build.py` alone is HALF the job.

    "Build" means the installer a user can download from GitHub Releases
    (owner decree 2026-08-19). Once a build ran on his word, the turn does not
    end until the release is out — or until a task says, in his language, why
    it cannot be (hidden project, no repo, a failed step).
    """
    built = False
    for tool in model.runs():
        command = str(tool.input.get("command") or "")
        if build_guard.is_release_command(command):
            return None
        if build_guard.is_build_command(command):
            built = True
    if not built:
        return None
    excused = [t for t in led.tasks if t.state in ('?', '~')]
    for task in excused:
        if RELEASE_WORD_RE.search(task.text):
            return None
    return [
        "A build ran but nothing was released — the installer sits in dist/ "
        "where no user can reach it, and his app still sees the old version.",
        "FIX: finish it: `git push origin HEAD` → `gh release create "
        "v{version} \"dist/{Project}_Setup.exe\"`. If it truly cannot ship, "
        "say why in a [?] or [~] task naming the release.",
        f"where: {led.path}",
    ]


# ═══════════════════════════ entry ═══════════════════════════

def run(payload: dict) -> list[str] | None:
    from . import transcript as transcript_mod

    if payload.get("stop_hook_active"):
        return None
    cwd = Path(payload.get("cwd") or os.getcwd())
    session_id = str(payload.get("session_id") or "").strip() or "unknown"
    root = paths.session_root(cwd, session_id)
    model = transcript_mod.load(payload.get("transcript_path") or "")

    led = ledger_mod.load(paths.ledger_path(root, session_id))
    problem = agents.check(model, led)
    if problem:
        return problem
    agents_running = bool(agents.still_running(model))

    evid = evidence_mod.load(paths.evidence_file(root, session_id))
    product_edits = model.product_edits(root)

    # Every group reports its first problem, and ALL groups report in ONE
    # message — one fix round instead of one round per tooth (owner
    # 2026-08-19: agents "3 puta šalju oproštajnu poruku").
    problems: list[str] = []
    if product_edits or led.open_tasks():
        for step in (
            lambda: _ledger_checks(led, model, agents_running),
            lambda: _teeth(led, evid, model, root, product_edits),
            lambda: _evidence_integrity(model, root),
            lambda: _rules_size(model, root),
        ):
            problem = step()
            if problem:
                problems += (["—"] if problems else []) + problem
    for step in (lambda: _communication(model, root, cwd),
                 lambda: _release(led, model)):
        problem = step()
        if problem:
            problems += (["—"] if problems else []) + problem
    return problems or None
