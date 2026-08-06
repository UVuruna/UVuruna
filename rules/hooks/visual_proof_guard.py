#!/usr/bin/env python3
"""THE VISUAL PROOF GUARD — owner decree 2026-08-06.

Born from a real failure the same day: agents shipped a live time crown that
was microscopic/mis-metaled on the real dial, an unimplemented bottom
location line, and sideways jewels — 1800 tests and every existing hook
passed while the owner's first five minutes of LOOKING failed it all. The
graded-screenshot law already existed (rules/GUI.md -> Space & Legibility),
but sub-agents never pass Stop gates, and the implementer graded its OWN
work on zoomed crops — self-grading a full-size defect out of view.

This Stop hook closes that hole: a session whose work changed what the user
SEES may not end without an INDEPENDENT grader's proof — full-size
screenshots, one grade >= 8 per touched ruling, from someone other than the
implementer.

Class: GATE — wired machine-wide in ~/.claude/settings.json (Stop).
Contract: exit 2 = BLOCK (stderr fed back to the agent); exit 0 = pass.
Fail-open ONLY on harness payload errors (unreadable transcript, missing
cwd, ...) — never on the proof file itself. An unreadable proof file is a
FAILED proof, not a free pass; the whole point of this tooth is that a
missing/garbled/self-graded proof blocks the session.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

MIN_GRADE = 8
MIN_IMAGE_BYTES = 200 * 1024  # 200 KB
MIN_IMAGE_SHORT_SIDE = 700    # px

EXEMPT_MARK = "VISUAL_PROOF: exempt"

BLOCK_MISSING = """THE VISUAL PROOF (rules/GUI.md -> The Visual Proof, GATE of 2026-08-06):
this session may have changed what the user SEES, and there is no valid
{proof} in {claude_dir}.

Produce it before ending:
  1. An INDEPENDENT agent (never the implementer) launches the real app at
     its real default size and takes FULL-dial / FULL-window screenshots —
     never a zoomed crop, never a cherry-picked region.
  2. That same independent agent grades each screenshot against the text of
     the ruling it is meant to satisfy (a decree, a spec line, an owner
     instruction) and writes a one-line verdict.
  3. Write {proof} as JSON:

     {{
       "commit": "<git rev-parse HEAD of this project, exactly>",
       "implementer": "<who wrote the code>",
       "grader": "<who graded it — MUST differ from implementer>",
       "items": [
         {{"ruling": "<the text being checked>", "image": "<path>", "grade": 9}}
       ]
     }}

  Every image must exist on disk, be a real screenshot (>= 200 KB or
  >= 700px on its shorter side), and be newer than the commit it claims to
  prove. Every grade must be >= {min_grade} — a lower grade means FIX and
  re-shoot, never round up.

If this session genuinely touched no rendering/GUI code, the coordinator may
instead write a line `{exempt}` into {tasks} — but a false exemption is a lie
under FIXED = VERIFIED (root CLAUDE.md Law #5)."""

BLOCK_INVALID = """THE VISUAL PROOF (rules/GUI.md -> The Visual Proof, GATE of 2026-08-06):
{proof} exists but does not establish proof. An unreadable or incomplete
proof file is a FAILED proof, not a pass.

{detail}

Fix the file (see the schema in the missing-proof message this hook prints
when {proof} does not exist) and end the turn again."""


def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def find_claude_dir(cwd: Path) -> Path | None:
    """Walk cwd and its parents for a .claude/ directory (delegation_guard
    style) — the project root is not always the harness cwd."""
    for directory in (cwd, *cwd.parents):
        candidate = directory / ".claude"
        if candidate.is_dir():
            return candidate
    return None


def is_exempt(claude_dir: Path) -> bool:
    tasks_file = claude_dir / "session-tasks.md"
    try:
        if tasks_file.is_file():
            text = tasks_file.read_text(encoding="utf-8", errors="replace")
            return EXEMPT_MARK in text
    except OSError:
        pass
    return False


def current_commit(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def commit_timestamp(project_root: Path, commit: str) -> float | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "show", "-s", "--format=%ct", commit],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def image_is_real(path: Path) -> tuple:
    """(ok, reason-if-not-ok). Fail-OPEN per item only when PIL itself is
    unimportable — a real missing/tiny file always fails the item."""
    if not path.is_file():
        return False, f"image {path} does not exist"
    size = path.stat().st_size
    if size >= MIN_IMAGE_BYTES:
        return True, ""
    try:
        from PIL import Image
    except ImportError:
        # PIL unavailable: file-size-only check already failed above, and
        # we cannot check pixel dimensions — fail OPEN on this one item
        # rather than block a real screenshot for lacking a dependency.
        return True, ""
    try:
        with Image.open(path) as img:
            w, h = img.size
    except Exception as exc:  # noqa: BLE001 - any decode failure fails the item
        return False, f"image {path} could not be opened as an image ({exc})"
    if min(w, h) >= MIN_IMAGE_SHORT_SIDE:
        return True, ""
    return False, (f"image {path} is {size} bytes and {w}x{h} — below both "
                    f"the {MIN_IMAGE_BYTES} byte floor and the "
                    f"{MIN_IMAGE_SHORT_SIDE}px shorter-side floor")


def validate_proof(proof_path: Path, project_root: Path) -> list:
    """Returns a list of problem strings; empty = proof passes."""
    try:
        raw = proof_path.read_text(encoding="utf-8", errors="strict")
    except OSError as exc:
        return [f"{proof_path} could not be read ({exc})"]

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"{proof_path} is not valid JSON ({exc})"]

    if not isinstance(data, dict):
        return [f"{proof_path} must contain a JSON object"]

    problems = []

    commit = data.get("commit")
    head = current_commit(project_root)
    if head is None:
        problems.append(f"could not run git in {project_root} to verify 'commit'")
    elif not commit or commit != head:
        problems.append(
            f"'commit' is {commit!r} but the project HEAD is {head!r} — the "
            "proof is stale, re-shoot against the current commit")

    grader = str(data.get("grader") or "").strip()
    implementer = str(data.get("implementer") or "").strip()
    if not grader:
        problems.append("'grader' is missing or empty")
    elif implementer and grader == implementer:
        problems.append(
            f"'grader' ({grader!r}) is the same as 'implementer' — the "
            "implementer may never grade its own visual work")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        problems.append("'items' must be a non-empty list of "
                        "{ruling, image, grade}")
        items = []

    commit_ts = commit_timestamp(project_root, commit) if commit else None

    failing = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            failing.append(f"items[{i}] is not an object")
            continue
        ruling = str(item.get("ruling") or "").strip()
        image = item.get("image")
        grade = item.get("grade")
        label = ruling[:60] if ruling else f"items[{i}]"

        if not ruling:
            failing.append(f"items[{i}]: 'ruling' is missing or empty")
        if not image:
            failing.append(f"{label}: 'image' is missing")
        else:
            img_path = Path(image)
            if not img_path.is_absolute():
                img_path = project_root / img_path
            ok, reason = image_is_real(img_path)
            if not ok:
                failing.append(f"{label}: {reason}")
            elif commit_ts is not None:
                try:
                    mtime = img_path.stat().st_mtime
                except OSError:
                    mtime = None
                if mtime is not None and mtime < commit_ts:
                    failing.append(
                        f"{label}: image {img_path} is OLDER than the commit "
                        "it claims to prove — it cannot be a screenshot of "
                        "this code")
        if not isinstance(grade, (int, float)):
            failing.append(f"{label}: 'grade' is missing or not a number")
        elif grade < MIN_GRADE:
            failing.append(f"{label}: grade {grade} < {MIN_GRADE}")

    problems.extend(failing)
    return problems


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    claude_dir = find_claude_dir(cwd)
    if claude_dir is None:
        return  # no project structure here at all — nothing to gate
    if is_exempt(claude_dir):
        return

    proof_path = claude_dir / "visual-proof.json"
    project_root = claude_dir.parent

    if not proof_path.is_file():
        block(BLOCK_MISSING.format(
            proof=proof_path, claude_dir=claude_dir, min_grade=MIN_GRADE,
            exempt=EXEMPT_MARK, tasks=claude_dir / "session-tasks.md",
        ))

    problems = validate_proof(proof_path, project_root)
    if problems:
        detail = "\n".join(f"  - {p}" for p in problems)
        block(BLOCK_INVALID.format(proof=proof_path, detail=detail))


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
        try:
            check_stop(payload)
        except SystemExit:
            raise
        except Exception:  # noqa: BLE001 - harness-level failure only, fail-open
            sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
