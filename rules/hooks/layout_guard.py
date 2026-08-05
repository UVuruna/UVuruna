#!/usr/bin/env python3
"""Layout guard - owner decree 2026-08-05.

Enforces THE SPACE & LEGIBILITY LAW (rules/GUI.md -> Law - Space & Legibility)
across ALL sessions on this machine (wired in ~/.claude/settings.json), so no
project has to be migrated before the teeth start biting:

  PreToolUse (Write|Edit|NotebookEdit)
      Blocks writing a GUI source that cuts content off or makes the free space
      unreachable: elide/trim APIs, forced scrollbars, no-wrap, hard sizes on
      text-bearing widgets. A line may opt out only with a REASON, written as
      `layout-law: exempt - <why>` in that line's comment.

  Stop
      A session that edited any GUI file may not end without layout proof:
      `.claude/layout-proof.md` naming the CURRENT session, every touched GUI
      file, and a PASS for each window it checked at its declared minimum size.

Born from the same two screenshots arriving project after project: a list
scrolling three rows while 300+ px of the dialog stood empty, and shortcut
fields rendering "ift+tab" while the column beside them carried slack.

Contract: exit 2 = BLOCK (stderr is fed back to the agent); exit 0 = pass.
Fail-open on any parse error - a broken guard must never brick a session.
"""

import json
import os
import re
import sys
from pathlib import Path

PROOF_FILENAME = "layout-proof.md"

# --- what counts as a GUI source -------------------------------------------

MARKUP_EXTENSIONS = {".xaml", ".axaml", ".ui", ".qml", ".qss", ".css", ".scss"}
CODE_EXTENSIONS = {".py", ".cs", ".vb", ".ts", ".tsx", ".js", ".jsx"}

# path components that mark a GUI area ("ui" is exact-component only, or every
# "build"/"guide" path would match)
PATH_HINTS = (
    "gui", "view", "widget", "window", "dialog", "screen",
    "panel", "form", "component", "layout", "frontend",
)
EXACT_HINTS = ("ui",)

# a code file with no GUI-ish path still counts when it builds widgets
CODE_MARKERS = re.compile(
    r"\bQ(Widget|Dialog|MainWindow|VBoxLayout|HBoxLayout|GridLayout|FormLayout"
    r"|Label|LineEdit|TableView|ListWidget|ScrollArea)\b"
    r"|\bInitializeComponent\s*\(|\bSystem\.Windows\b|\bsetLayout\s*\(",
)

# never inspected: the rulebook and its guards NAME the banned patterns, and
# docs/tests quote them on purpose
SKIP_COMPONENTS = {"rules", "tests", "test", "docs", "doc",
                   "node_modules", "__pycache__", ".git", "vendor"}

# --- the banned patterns ----------------------------------------------------

EXEMPT_RE = re.compile(r"layout-law:\s*exempt\s*[-—:]\s*\S")

BANNED = (
    (re.compile(r"\bElide(Right|Left|Middle)\b|setTextElideMode|setElideMode"),
     "Qt text elision - the user cannot read what the ellipsis ate"),
    (re.compile(r"TextTrimming\s*=\s*[\"'](?!None)"),
     "WPF TextTrimming - same failure as Qt elision, in XAML"),
    (re.compile(r"text-overflow\s*:\s*ellipsis"),
     "CSS text-overflow: ellipsis"),
    (re.compile(r"\bsetFixed(Size|Width|Height)\s*\("),
     "Qt hard size - freezes the element so it cannot take the free space "
     "(step 1 of the ladder)"),
    (re.compile(r"\bsetWordWrap\s*\(\s*(False|false|0)\s*\)"),
     "word wrap disabled - kills step 2 of the ladder (reflow)"),
    (re.compile(r"\bTextWrapping\s*=\s*[\"']NoWrap"),
     "WPF TextWrapping=NoWrap - kills step 2 of the ladder (reflow)"),
    (re.compile(r"ScrollBarAlwaysOn"),
     "a scrollbar forced ON - scrolling is step 4, legal only when the window "
     "is genuinely full"),
    (re.compile(r"ScrollBarVisibility\s*=\s*[\"']Visible"),
     "a scrollbar forced Visible - scrolling is step 4, legal only when the "
     "window is genuinely full"),
    (re.compile(
        r"<(TextBlock|TextBox|Label|Button|ComboBox|CheckBox|RadioButton)\b"
        r"[^>]*\b(Width|Height)\s*=\s*[\"']\d"),
     "hard pixel size on a text-bearing XAML element"),
)

BLOCK_PATTERN = (
    "THE SPACE & LEGIBILITY LAW (rules/GUI.md -> Law - Space & Legibility, LAW "
    "of 2026-08-05): this edit to {path} cuts content off or takes the free "
    "space away from it.\n{findings}\n"
    "The owner has reported these same two bugs by hand in project after "
    "project: a list scrolling while 300+ px of the same dialog stood empty, "
    "and shortcut fields rendering 'ift+tab' while the column beside them had "
    "slack to give up.\n"
    "Fix in the ladder's order, and a later step is legal only when the "
    "earlier ones are exhausted:\n"
    "  1. TAKE THE FREE SPACE - the starving element gets the stretch; a "
    "spacer or trailing stretch NEVER outranks content that does not fit\n"
    "  2. REFLOW - wrap the text, break into more rows/columns, make "
    "neighbours with slack give it up first\n"
    "  3. RAISE THE WINDOW MINIMUM - computed from the longest real content, "
    "never guessed\n"
    "  4. SCROLL - last, and only when the window is genuinely full in that "
    "axis\n"
    "If this one line is genuinely legitimate (a fixed-size icon, an "
    "intentionally decorative label), say so ON THAT LINE in a comment: "
    "layout-law: exempt - <the reason>. An exemption without a reason does not "
    "count."
)

# --- the Stop proof gate ----------------------------------------------------

BLOCK_NO_PROOF = (
    "THE SPACE & LEGIBILITY LAW (rules/GUI.md -> Law - Space & Legibility, "
    "GATE of 2026-08-05): this session edited GUI files and has shipped no "
    "layout proof, so it may not end.\n"
    "GUI files touched:\n{files}\n"
    "{detail}\n"
    "Write {proof} like this - one line per window you touched, and a window "
    "counts as PASS only when you actually checked it (audit test, or the app "
    "opened and inspected at that size):\n\n"
    "    SESSION: {session}\n"
    "    - SetsDialog (gui/sets_dialog.py) - minimum 980x720 - audit: PASS - "
    "pytest tests/test_layout_audit.py, min + 1400x900\n\n"
    "Each window's PASS means all three hold at the declared minimum AND "
    "larger: nothing is clipped, no text is elided, and no scrollbar is "
    "visible while that window still has unused space in the same axis. If "
    "one of them does not hold, FIX IT - do not write PASS. FIXED = VERIFIED "
    "(CLAUDE.md -> The Laws) applies to the proof line as it does to any other "
    "claim of finished work."
)


def norm_components(path: str) -> list:
    return [c.lower() for c in re.split(r"[\\/]+", path) if c]


def is_gui_file(path: str, content: str) -> bool:
    if not path:
        return False
    components = norm_components(path)
    if any(c in SKIP_COMPONENTS for c in components):
        return False
    suffix = Path(path).suffix.lower()
    if suffix in MARKUP_EXTENSIONS:
        return True
    if suffix not in CODE_EXTENSIONS:
        return False
    directories = components[:-1]
    if any(h in c for c in directories for h in PATH_HINTS):
        return True
    if any(c in EXACT_HINTS for c in directories):
        return True
    stem = components[-1] if components else ""
    if any(h in stem for h in PATH_HINTS):
        return True
    return bool(content and CODE_MARKERS.search(content))


def written_text(tool_input: dict) -> str:
    """Everything this call would put INTO the file."""
    parts = [
        tool_input.get("content"),
        tool_input.get("new_string"),
        tool_input.get("new_source"),
    ]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    return "\n".join(p for p in parts if isinstance(p, str))


def scan(text: str) -> list:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if EXEMPT_RE.search(line):
            continue
        for pattern, why in BANNED:
            match = pattern.search(line)
            if match:
                findings.append(
                    f"  line {number}: {match.group(0).strip()}  <- {why}")
                break
    return findings


def check_pre_tool_use(payload: dict) -> None:
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    text = written_text(tool_input)
    if not text or not is_gui_file(path, text):
        return
    findings = scan(text)
    if not findings:
        return
    print(
        BLOCK_PATTERN.format(path=path, findings="\n".join(findings)),
        file=sys.stderr,
    )
    sys.exit(2)


def find_proof_file(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / ".claude" / PROOF_FILENAME
        if candidate.is_file():
            return candidate
    return None


def gui_files_of_session(transcript_path: str) -> list:
    """Every GUI file this session wrote to, oldest first, de-duplicated."""
    touched = []
    if not transcript_path or not os.path.isfile(transcript_path):
        return touched
    with open(transcript_path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            message = entry.get("message") or {}
            blocks = message.get("content")
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                if block.get("name") not in ("Write", "Edit", "MultiEdit",
                                             "NotebookEdit"):
                    continue
                tool_input = block.get("input") or {}
                path = (tool_input.get("file_path")
                        or tool_input.get("notebook_path") or "")
                if path and is_gui_file(path, written_text(tool_input)):
                    if path not in touched:
                        touched.append(path)
    return touched


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return  # already continuing because of a Stop hook - never loop
    touched = gui_files_of_session(payload.get("transcript_path") or "")
    if not touched:
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    session = str(payload.get("session_id") or "").strip() or "<session id>"
    proof = find_proof_file(cwd)
    listing = "".join(f"  - {p}\n" for p in touched)

    if proof is None:
        detail = (f"No {PROOF_FILENAME} exists anywhere above {cwd}.")
        target = cwd / ".claude" / PROOF_FILENAME
    else:
        text = proof.read_text(encoding="utf-8", errors="replace")
        target = proof
        missing = []
        if session not in text:
            missing.append(
                f"it does not name this session ({session}) - the proof of an "
                "earlier session does not carry over")
        if "PASS" not in text:
            missing.append("it contains no PASS line")
        unproven = [p for p in touched if Path(p).stem.lower()
                    not in text.lower()]
        if unproven:
            missing.append("these touched files appear nowhere in it: "
                           + ", ".join(unproven))
        if not missing:
            return
        detail = f"{proof} exists, but " + "; ".join(missing) + "."

    print(
        BLOCK_NO_PROOF.format(files=listing, detail=detail, proof=target,
                              session=session),
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    event = payload.get("hook_event_name", "")
    try:
        if event == "PreToolUse":
            check_pre_tool_use(payload)
        elif event == "Stop":
            check_stop(payload)
    except SystemExit:
        raise
    except Exception:  # a broken guard must never brick a session
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
