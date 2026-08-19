"""Where things live: project root, ledger, evidence, and what a product file is."""

from __future__ import annotations

import re
from pathlib import Path

#: directories that are session/owner state, never product
NON_PRODUCT_DIRS = {
    ".claude", ".git", "uv", "scratchpad", "temp", "tmp",
    "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache",
}

EDIT_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def project_root(cwd: Path) -> Path:
    """Nearest ancestor of `cwd` (cwd included) holding `.claude/` or `.git`."""
    cwd = Path(cwd)
    for directory in (cwd, *cwd.parents):
        if (directory / ".claude").is_dir() or (directory / ".git").exists():
            return directory
    return cwd


def sessions_dir(root: Path) -> Path:
    return Path(root) / ".claude" / "sessions"


def ledger_path(root: Path, session_id: str) -> Path:
    return sessions_dir(root) / f"{session_id}.md"


def session_root(cwd: Path, session_id: str) -> Path:
    """The project root whose `.claude/sessions/` holds THIS session's ledger.

    `project_root` alone breaks the moment a Bash `cd` parks the session's
    working directory inside a NESTED project with its own `.git`: the nearest
    root wins, the session's ledger is not there, and every ledger-based check
    runs against an empty ledger (2026-08-19: the stop gate blocked a
    coordinator whose ledger full of `[>]` lived one root higher). When the
    nearest root has no ledger for this session, climb to the next enclosing
    root; the nearest root stays the answer when nobody has one (a fresh
    session that has not written its ledger yet).
    """
    nearest = project_root(cwd)
    if not session_id or session_id == "unknown":
        return nearest
    # One walk up, nearest first — every ancestor that is itself a root
    # (`.claude`/`.git`) is a candidate; re-deriving project_root per step
    # would re-scan the same ancestors quadratically on this hot path
    # (pregled 2026-08-19, finding 3).
    for directory in (nearest, *nearest.parents):
        is_root = (directory / ".claude").is_dir() or (directory / ".git").exists()
        if is_root and ledger_path(directory, session_id).is_file():
            return directory
    return nearest


def evidence_dir(root: Path, session_id: str) -> Path:
    return Path(root) / ".claude" / "evidence" / session_id


def evidence_file(root: Path, session_id: str) -> Path:
    return evidence_dir(root, session_id) / "evidence.jsonl"


def evidence_current(root: Path) -> Path:
    return Path(root) / ".claude" / "evidence" / "current"


def resolve(path: str, cwd: Path) -> Path | None:
    """Absolute form of a tool_input path, or None when it is unusable."""
    if not path:
        return None
    try:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        return Path(candidate.as_posix())
    except (OSError, ValueError):
        return None


def under(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except (ValueError, OSError):
        return False


def is_evidence_path(path: str) -> bool:
    parts = [p.lower() for p in re.split(r"[\\/]+", str(path)) if p]
    return "evidence" in parts and ".claude" in parts


def is_product_file(path: str, root: Path) -> bool:
    """A file of the PRODUCT: inside the project, outside session state."""
    if not path:
        return False
    absolute = resolve(path, Path(root))
    if absolute is None or not under(absolute, root):
        return False
    try:
        relative = absolute.resolve().relative_to(Path(root).resolve())
    except (ValueError, OSError):
        return False
    parts = [p.lower() for p in relative.parts]
    return not any(part in NON_PRODUCT_DIRS for part in parts)
