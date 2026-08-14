"""What did THIS session actually change? — the one authority.

Owner decree 2026-08-14: **GUI PROVERE SAMO AKO SU MENJANI GUI
FAJLOVI.** A gate that builds windows and measures pixels at the end
of a turn in which no GUI file was touched — or in which NOTHING was
touched — is not enforcement, it is a tax on talking to the agent.

"Changed" means both halves, because a session commits as it goes:
  * the working tree (staged + unstaged), AND
  * every commit not yet on the upstream branch.
Cannot tell (no git, no upstream, an error) -> report CHANGED, so a
guard runs. A gate never goes quiet because a command failed.

Used by the machine-wide Stop guards and by each project's
`tests/run_guards.py`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# A path is GUI when it lives in a GUI SOURCE directory. Nothing else
# counts: the first version of this also matched filenames containing
# "panel"/"window"/"layout", and editing a TEST named
# `test_tool_panels_image_checker.py` fired the whole runtime window
# audit — real windows flashing across the owner's screen for a change
# that never touched the GUI. Directory, not vocabulary.
GUI_DIR_MARKERS = ("gui", "ui", "widgets", "views", "qml", "windows")
# ...except the GUI guards themselves: editing one must re-run it.
GUI_TEST_FILES = ("test_layout_law.py", "test_layout_audit_tk.py",
                  "test_layout_zubi_tk.py", "layout_checks_tk.py",
                  "test_layout_audit.py", "layout_checks.py")


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True,
            text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def changed_files(cwd: Path) -> list[str] | None:
    """Repo-relative paths this session touched, or None when unknown.

    None is the "cannot tell" answer and callers MUST treat it as
    "assume everything changed" — never as "nothing changed".
    """
    status = _git(["status", "--porcelain", "--untracked-files=no"], cwd)
    if status is None:
        return None
    paths = {
        line[3:].split(" -> ")[-1].strip().strip('"')
        for line in status.splitlines() if line.strip()
    }
    # commits this session already made but has not pushed
    ahead = _git(["diff", "--name-only", "@{upstream}..HEAD"], cwd)
    if ahead is None:
        return None  # detached / no upstream -> cannot bound the session
    paths.update(p.strip() for p in ahead.splitlines() if p.strip())
    return sorted(paths)


def is_gui_path(path: str) -> bool:
    parts = [p.lower() for p in path.replace("\\", "/").split("/")]
    if any(part in GUI_DIR_MARKERS for part in parts[:-1]):
        return True
    return (parts[-1] if parts else "") in GUI_TEST_FILES


def touched_anything(cwd: Path) -> bool:
    """False ONLY when git is certain the session changed nothing."""
    paths = changed_files(cwd)
    return True if paths is None else bool(paths)


def touched_gui(cwd: Path) -> bool:
    """False ONLY when git is certain no GUI file was changed."""
    paths = changed_files(cwd)
    return True if paths is None else any(is_gui_path(p) for p in paths)
