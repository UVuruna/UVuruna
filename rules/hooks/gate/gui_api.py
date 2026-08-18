"""Blocks GUI APIs that cut content off or freeze the free space.

Ported from layout_guard.py's PreToolUse half: the same banned pattern list and
the same per-line escape, written `layout-ok: <reason>` (the older
`layout-law: exempt - <reason>` is still accepted).
"""

from __future__ import annotations

import re
from pathlib import Path

EXEMPT_RE = re.compile(
    r"layout-ok\s*[:(\-—]\s*\S{3,}|layout-law:\s*exempt\s*[-—:]\s*\S")

BANNED = (
    (re.compile(r"\bElide(Right|Left|Middle)\b|setTextElideMode|setElideMode"),
     "Qt text elision — the user cannot read what the ellipsis ate"),
    (re.compile(r"TextTrimming\s*=\s*[\"'](?!None)"),
     "WPF TextTrimming"),
    (re.compile(r"text-overflow\s*:\s*ellipsis"),
     "CSS text-overflow: ellipsis"),
    (re.compile(r"\bsetFixed(Size|Width|Height)\s*\("),
     "Qt hard size — the element can no longer take the free space"),
    (re.compile(r"\bsetWordWrap\s*\(\s*(False|false|0)\s*\)"),
     "word wrap disabled — kills reflow (ladder step 2)"),
    (re.compile(r"\bTextWrapping\s*=\s*[\"']NoWrap"),
     "WPF TextWrapping=NoWrap — kills reflow (ladder step 2)"),
    (re.compile(r"ScrollBarAlwaysOn"),
     "scrollbar forced ON — scrolling is step 4, only when the window is full"),
    (re.compile(r"ScrollBarVisibility\s*=\s*[\"']Visible"),
     "scrollbar forced Visible — scrolling is step 4"),
    (re.compile(r"<(TextBlock|TextBox|Label|Button|ComboBox|CheckBox"
                r"|RadioButton)\b[^>]*\b(Width|Height)\s*=\s*[\"']\d"),
     "hard pixel size on a text-bearing XAML element"),
)


def scan(text: str) -> list[str]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if EXEMPT_RE.search(line):
            continue
        for pattern, why in BANNED:
            match = pattern.search(line)
            if match:
                findings.append(f"line {number}: {match.group(0).strip()} "
                                f"({why})")
                break
    return findings


def check(path: str, text: str) -> list[str] | None:
    """Block lines, or None. The caller decides whether `path` is a GUI file."""
    if not text:
        return None
    findings = scan(text)
    if not findings:
        return None
    return [
        f"Forbidden GUI API in {Path(path).name}: {findings[0]}",
        "FIX in ladder order: take the free space → reflow → raise the window "
        "minimum → scroll. A legitimate line says `layout-ok: <reason>`.",
        f"where: {path}",
    ]
