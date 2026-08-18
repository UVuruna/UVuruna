"""Per-category teeth at Stop: what each category must have PROVEN.

GUI needs graded shots on two profiles, FEATURE a filled matrix, BUGFIX a red
test before and a green test after, REFACTOR unchanged test totals plus green
project guards. DOCS/PLAN/BUILD carry no tooth here.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import ledger as ledger_mod

GRADE_FLOOR = 8
OWNER_PROFILE = "pc-owner"

REPEAT_RE = re.compile(r"\b(opet|ponovo|again|still|i dalje)\b", re.I)
GRADER_RE = re.compile(r"grader", re.I)

AVERAGE_ROW_RE = re.compile(r"average device|prose[čc]an", re.I)
FRESH_ROW_RE = re.compile(r"fresh install|sve[žz]a instalacija", re.I)
OLD_PATH_ROW_RE = re.compile(r"old path|stari put", re.I)

RUN_GUARDS_CANDIDATES = (
    Path("tests") / "run_guards.py",
    Path("desktop") / "tests" / "run_guards.py",
    Path("run_guards.py"),
)


def _last_ts(tools) -> datetime | None:
    stamps = [t.ts for t in tools if t.ts is not None]
    return max(stamps) if stamps else None


def _first_ts(tools) -> datetime | None:
    stamps = [t.ts for t in tools if t.ts is not None]
    return min(stamps) if stamps else None


# ═══════════════════════════ GUI ═══════════════════════════

def gui(led, evid, model, gui_edits) -> list[str] | None:
    if not gui_edits:
        return None
    last_edit = _last_ts(gui_edits)
    shots = evid.usable_of_kind("shot", after=last_edit)
    profiles = {row.profile for row in shots if row.profile}
    if len(shots) < 2 or len(profiles) < 2 or profiles <= {OWNER_PROFILE}:
        return [
            f"GUI tooth: {len(shots)} usable shot row(s) on {len(profiles)} "
            "profile(s) after the last GUI edit — two profiles are required, "
            "one of them not pc-owner.",
            "FIX: run `python rules/tools/uv.py shot --window <Name> --profile "
            "laptop-avg` and again with --profile pc-low, then look at both.",
            f"where: {evid.path}",
        ]
    looked_at = {name: stamp for name, stamp in model.image_reads()}
    for row in shots:
        stamp = looked_at.get(row.artifact_name)
        if row.artifact_name and (stamp is None
                                  or (row.ts is not None and stamp is not None
                                      and stamp < row.ts)):
            return [
                f"GUI tooth: shot {row.id} ({row.artifact_name}) was never "
                "OPENED after it was taken — an ungraded screenshot proves "
                "nothing.",
                "FIX: Read the PNG (the Read tool renders images), grade it "
                "against DESIGN.md and write the grade on its ! line.",
                f"where: {row.artifact}",
            ]
    for row in shots:
        line = next((b for b in led.bang_lines() if row.id in b), None)
        if line is None:
            return [
                f"GUI tooth: shot {row.id} has no ! line in the ledger.",
                "FIX: add `! {id} shot <window> <profile> — looked — grade N "
                "(what you saw)` under the task.".replace("{id}", row.id),
                f"where: {led.path}",
            ]
        grades = [int(value) for _, value in ledger_mod.GRADE_RE.findall(line)]
        if not grades or min(grades) < GRADE_FLOOR:
            return [
                f"GUI tooth: shot {row.id} is graded "
                f"{grades[0] if grades else 'not at all'} — below {GRADE_FLOOR}"
                "/10 nothing ships.",
                "FIX: fix the window, re-shoot, look again, and write an "
                "honest `grade N` on that ! line.",
                f"where: {led.path}",
            ]
    if not led.trivial and led.klass:
        last_shot = max((r.ts for r in shots if r.ts), default=None)
        graders = [t for t in model.agent_launches()
                   if GRADER_RE.search(str(t.input.get("prompt") or "")
                                       + str(t.input.get("description") or ""))
                   and (last_shot is None or t.ts is None or t.ts > last_shot)]
        if not graders:
            return [
                f"GUI tooth (class {led.klass}): no independent grader ran "
                "after the shots.",
                "FIX: launch one sub-agent whose prompt says `grader` — it "
                "opens the PNGs and grades them against DESIGN.md.",
                f"where: {led.path}",
            ]
    return None


# ═══════════════════════════ FEATURE ═══════════════════════════

def feature(led, evid, product_edits) -> list[str] | None:
    if not led.has_matrix:
        return [
            "FEATURE tooth: the ledger has no `matrica:` table.",
            "FIX: write the matrix BEFORE the first product edit — one row per "
            "scenario with device and evidence columns.",
            f"where: {led.path}",
        ]
    body = "\n".join(" ".join(row) for row in led.matrix_rows)
    for pattern, what in ((AVERAGE_ROW_RE, "average device"),
                          (FRESH_ROW_RE, "fresh install")):
        if not pattern.search(body):
            return [
                f"FEATURE tooth: the matrix has no `{what}` row.",
                "FIX: add it — we build for others, so an average device and a "
                "fresh install are mandatory scenarios.",
                f"where: {led.path}",
            ]
    if led.mentions_replacement() and not OLD_PATH_ROW_RE.search(body):
        return [
            "FEATURE tooth: this session replaces something, but the matrix "
            "has no `old path` row.",
            "FIX: add a row proving the old path is gone (grep the old symbol).",
            f"where: {led.path}",
        ]
    if not led.done_tasks():
        return None  # honest incompleteness: nothing is claimed done
    last_edit = _last_ts(product_edits)
    for row in led.matrix_rows:
        cell = row[-1] if row else ""
        ids = [f"ev-{n}" for n in ledger_mod.EVIDENCE_ID_RE.findall(cell)]
        if not ids:
            return [
                f"FEATURE tooth: matrix row `{(row[1] if len(row) > 1 else cell)[:40]}` "
                "names no evidence.",
                "FIX: run the scenario with `uv run/device/test` and put its "
                "ev-id in the evidence column — or mark the task [~].",
                f"where: {led.path}",
            ]
        for ident in ids:
            found = evid.by_id(ident)
            if found is None or not found.usable:
                return [
                    f"FEATURE tooth: {ident} is "
                    + ("missing from evidence.jsonl" if found is None
                       else f"kind={found.kind} rc={found.rc}") + ".",
                    "FIX: re-run that scenario until it produces a real row — "
                    "an `unavailable` row never satisfies a tooth.",
                    f"where: {evid.path}",
                ]
            if not found.newer_than(last_edit):
                return [
                    f"FEATURE tooth: {ident} is OLDER than the last product "
                    "edit — it proves the previous version.",
                    "FIX: re-run the scenario after the last edit.",
                    f"where: {evid.path}",
                ]
    return None


# ═══════════════════════════ BUGFIX ═══════════════════════════

def bugfix(led, evid, model, product_edits) -> list[str] | None:
    first_edit = _first_ts(product_edits)
    last_edit = _last_ts(product_edits)
    tests = evid.of_kind("test")
    red = [r for r in tests if r.rc != 0 and r.kind == "test"
           and (first_edit is None or (r.ts is not None and r.ts < first_edit))]
    green = [r for r in tests if r.rc == 0 and r.newer_than(last_edit)]
    if not red:
        return [
            "BUGFIX tooth: no FAILING test row before the first edit — the bug "
            "was never reproduced by a machine.",
            "FIX: write the regression test, run `uv test` while it still "
            "fails, then fix the code.",
            f"where: {evid.path}",
        ]
    if not green:
        return [
            "BUGFIX tooth: no passing test row after the last edit.",
            "FIX: run `python rules/tools/uv.py test <the regression test>` "
            "again now that the fix is in.",
            f"where: {evid.path}",
        ]
    if not led.cause:
        return [
            "BUGFIX tooth: the ledger has no `uzrok:` (root cause) line.",
            "FIX: write `uzrok: <what actually caused it>` — a symptom patch "
            "is not a fix (FIXED = VERIFIED).",
            f"where: {led.path}",
        ]
    first_owner = model.first_owner_message()
    if first_owner and REPEAT_RE.search(first_owner.text) \
            and not led.process_cause:
        return [
            "THE REPEAT LAW: the owner reported this AGAIN, so the first "
            "deliverable is why the previous round's claim was false.",
            "FIX: write `proces-uzrok: <why the previous claim was false>` in "
            "the ledger before closing the code task.",
            f"where: {led.path}",
        ]
    return None


# ═══════════════════════════ REFACTOR ═══════════════════════════

def refactor(led, evid, product_edits, root: Path) -> list[str] | None:
    first_edit = _first_ts(product_edits)
    last_edit = _last_ts(product_edits)
    tests = [r for r in evid.of_kind("test") if r.rc == 0]
    before = [r for r in tests
              if first_edit is None or (r.ts is not None and r.ts < first_edit)]
    after = [r for r in tests if r.newer_than(last_edit)]
    if not before or not after:
        return [
            "REFACTOR tooth: a green test run is missing "
            f"({'before' if not before else 'after'} the edits) — behaviour "
            "was never pinned.",
            "FIX: `uv test` before touching anything and again at the end; the "
            "totals must match.",
            f"where: {evid.path}",
        ]
    totals_before = {r.number("total") for r in before if r.number("total")}
    totals_after = {r.number("total") for r in after if r.number("total")}
    if totals_before and totals_after and \
            max(totals_before) != max(totals_after):
        return [
            f"REFACTOR tooth: test total changed {max(totals_before)} → "
            f"{max(totals_after)} — a refactor may not add or lose tests.",
            "FIX: restore the missing tests, or declare the work FEATURE "
            "instead of REFACTOR.",
            f"where: {evid.path}",
        ]
    return run_guards(root)


def run_guards(root: Path) -> list[str] | None:
    """Run the project's FULL guards when it has them; missing = skip."""
    script = next((root / c for c in RUN_GUARDS_CANDIDATES
                   if (root / c).is_file()), None)
    if script is None:
        return None
    try:
        done = subprocess.run([sys.executable, str(script)], cwd=str(root),
                              capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError):
        return None  # the gate could not run the tool; it does not invent a verdict
    if done.returncode == 0:
        return None
    tail = (done.stdout or done.stderr or "").strip().splitlines()
    return [
        f"REFACTOR tooth: {script.name} FULL exits {done.returncode}.",
        "FIX: read its output, fix what it names (clone guard included), run "
        "it again.",
        f"where: {tail[-1][:100] if tail else script}",
    ]
