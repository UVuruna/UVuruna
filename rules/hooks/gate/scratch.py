"""Scratch files stay in the scratchpad: no agent writes outside its project,
the harness scratchpad, or ~/.claude — and no shell write to a drive root or
above the project (Git Bash maps `/x` to the drive root; `../../..` walks out).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

#: shell write targets that leave the project: `> /tmp_x`, `cat > /x`,
#: `tee /x`, `> ../../../x`, `open("/x", "w")`, `.write_text` on `../../..`
SHELL_WRITE_RE = re.compile(
    r"(?:(?<![A-Za-z_\-])>{1,2}|\btee\b|\bcp\b[^|;&\n]*|\bmv\b[^|;&\n]*|--output[= ]|-o )"
    r"\s*[\"']?"
    r"((?<![\w.])/(?![a-zA-Z]/|dev/|proc/|tmp/|c/|mnt/)[\w.\-]+"       # /tmp_x -> drive root
    r"|(?:\.\./){3,}[\w.\-]+"                                  # ../../../x
    r"|[a-zA-Z]:[\\/][\w.\-]+\.(?:txt|png|py|md|json|log)\b)"  # X:\file at a drive root
)
PY_WRITE_RE = re.compile(
    r"(?:open|Path|write_text|save|imwrite)\(\s*[\"']"
    r"((?<![\w.])/(?![a-zA-Z]/|dev/|proc/|tmp/|c/|mnt/)[\w.\-]+"
    r"|(?:\.\./){3,}[\w.\-]+"
    r"|[a-zA-Z]:[\\/][\w.\-]+\.(?:txt|png|py|md|json|log))"
)

FIX = ("FIX: write scratch under the session scratchpad "
       "(AppData/Local/Temp/claude/…/scratchpad) or <project>/.claude/tmp/, "
       "and delete it when done.")


def _allowed_roots(root: Path) -> list[Path]:
    home = Path(os.path.expanduser("~"))
    roots = [Path(root), home / ".claude"]
    tmp = os.environ.get("TEMP") or os.environ.get("TMP")
    if tmp:
        roots.append(Path(tmp))
    roots.append(home / "AppData" / "Local" / "Temp")
    return [r.resolve() for r in roots if str(r)]


def check_edit_path(path: str, root: Path, cwd: Path) -> list[str] | None:
    """Write/Edit target outside every allowed root → block lines."""
    if not path:
        return None
    try:
        target = Path(path)
        if not target.is_absolute():
            target = Path(cwd) / target
        target = target.resolve()
    except (OSError, ValueError):
        return None
    for allowed in _allowed_roots(root):
        try:
            target.relative_to(allowed)
            return None
        except ValueError:
            continue
    # a sibling project inside the same monorepo is legitimate work, not scratch
    if "Coding" in target.parts and target.suffix.lower() not in (
            ".txt", ".png", ".jpg", ".log", ".tmp"):
        return None
    return [
        f"Writing outside the project: {target}",
        FIX,
        f"project: {root}",
    ]


def check_command(command: str) -> list[str] | None:
    """Shell command that writes to a drive root or above the project."""
    if not command:
        return None
    m = SHELL_WRITE_RE.search(command) or PY_WRITE_RE.search(command)
    if not m:
        return None
    return [
        f"Shell write leaves the project: {m.group(1)}",
        FIX,
        "note: in Git Bash `/name` is the DRIVE ROOT (U:\\name), not /tmp.",
    ]
