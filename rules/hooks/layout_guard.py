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
# RENDERING is GUI too (owner ruling 2026-08-07). A module that paints the
# product's own canvas changes what the user sees exactly as a dialog does —
# and `render/layers/ring.py` used to pass both this gate and the visual one
# because "layers" is not "layout" and a QPainter is not a QWidget.
#
# These are EXACT components, never substrings (owner decree 2026-08-14):
# "paint" as a substring made every file of the PromptPainter package a GUI
# file — `painter/config/paths.py` matched because the PACKAGE IS CALLED
# painter — so a pure path-logic fix demanded screenshots of twelve windows
# it never touched. A hint that matches a project's own name is not a hint.
EXACT_HINTS = ("ui", "render", "rendering", "paint", "painting",
               "draw", "drawing", "canvas")

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

# The screen every GUI must survive. Overridable per project in
# .claude/layout-frame.json: {"floor_width":1280,"floor_height":720,
# "reason":"why this project may demand more"} - a different floor without a
# reason does not count.
FLOOR_WIDTH = 1280
FLOOR_HEIGHT = 720
FRAME_FILENAME = "layout-frame.json"

MIN_GRADE = 8
MIN_SHOT_BYTES = 5000

SESSION_RE = re.compile(r"^SESSION:\s*(\S+)", re.M)
MIN_RE = re.compile(r"\bMIN\s+(\d{2,6})\s*[xX×]\s*(\d{2,6})")
SHOT_RE = re.compile(r"\bSHOT\s+(\S+\.(?:png|jpg|jpeg))", re.I)
GRADE_RE = re.compile(r"\bGRADE\s+(\d{1,2})(?:[.,]\d+)?\s*/\s*10")

PROOF_TEMPLATE = (
    "    SESSION: {session}\n"
    "    - SetsDialog (gui/sets_dialog.py) - MIN 980x720 - "
    "SHOT .claude/shots/sets_dialog.png - GRADE 9/10 - audit: PASS\n"
)

BLOCK_NO_PROOF = (
    "THE SPACE & LEGIBILITY LAW (rules/GUI.md -> Law - Space & Legibility, "
    "GATE of 2026-08-05): this session edited GUI files, and its layout proof "
    "is missing or does not hold. The session may not end.\n"
    "GUI files touched:\n{files}\n"
    "WHAT IS WRONG:\n{detail}\n"
    "Write {proof} - one line per window you touched:\n\n"
    "{template}\n"
    "Every field is checked, and every one of them is work you actually do:\n"
    "  MIN    the window's declared minimum size. It MUST fit inside "
    "{fw}x{fh} - a two-item menu that demands a 6000px minimum is an absurdity "
    "the ladder was supposed to prevent (reflow, do not widen). A project that "
    "genuinely needs a bigger floor declares it in "
    ".claude/layout-frame.json with a reason.\n"
    "  SHOT   a real screenshot of THAT window, captured at MIN (the audit "
    "test writes them; widget.grab().save(...) / RenderTargetBitmap otherwise). "
    "The file must exist and be a real image.\n"
    "  GRADE  YOUR OWN grade of that screenshot, 1-10, after you OPEN IT with "
    "the Read tool and look at it against DESIGN.md - crowding, alignment, "
    "empty holes, cut text, ugly defaults. This hook verifies you actually "
    "opened the image in this session. Anything below {grade}/10 does not "
    "ship: fix the GUI and re-shoot. Grading your own work honestly is the "
    "point - a 9 written under a 2/10 screenshot is a capacity lie "
    "(CLAUDE.md -> Universal Conduct).\n"
    "  PASS   the runtime audit passed: nothing clipped, no text elided, no "
    "scrollbar while that window still holds unused space.\n"
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
    if Path(stem).stem in EXACT_HINTS:
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


# --- SILENT AUDITS (owner decree 2026-08-06) --------------------------------
# No window an audit builds may ever reach the owner's screen or take his
# focus. Born live: an audit's factories called show() before
# WA_DontShowOnScreen, so every guard run flashed the real main window
# across the owner's desktop and broke his typing mid-sentence.

AUDIT_FILE_RE = re.compile(r"test_layout_audit[^/\\]*\.(py|cs)$", re.IGNORECASE)

WINDOW_BUILDER_RE = re.compile(
    r"QApplication|tb\.Window|tk\.Tk\b|Toplevel|new\s+Window\b|"
    r"Application\.Current")

SILENCE_MARKERS = ("DontShowOnScreen", "offscreen", "-alpha", "withdraw",
                   "RenderTargetBitmap", "ShowInTaskbar")

BLOCK_LOUD_AUDIT = (
    "SILENT AUDITS (rules/GUI.md, owner decree 2026-08-06): {path} builds "
    "windows but carries NO way of keeping them off the owner's screen.\n"
    "An audit that shows real windows flashes over the owner's desktop and "
    "steals his keyboard focus on EVERY guard run - this happened live, "
    "mid-sentence, repeatedly.\n"
    "Add the silencing before ANY window can map: Qt - "
    "setAttribute(WA_DontShowOnScreen, True) BEFORE every show() (or the "
    "offscreen platform); Tk - withdraw()/geometry off-screen AND "
    "attributes('-alpha', 0) before the first update; WPF - render to "
    "RenderTargetBitmap, never Show()."
)


def check_silent_audit(path: str, text: str) -> None:
    if not AUDIT_FILE_RE.search(path or ""):
        return
    if not WINDOW_BUILDER_RE.search(text):
        return
    # An Edit fragment inherits the silencing already in the file on disk.
    combined = text
    try:
        combined += Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    if any(marker in combined for marker in SILENCE_MARKERS):
        return
    print(BLOCK_LOUD_AUDIT.format(path=path), file=sys.stderr)
    sys.exit(2)


def check_pre_tool_use(payload: dict) -> None:
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    text = written_text(tool_input)
    if not text:
        return
    check_silent_audit(path, text)
    if not is_gui_file(path, text):
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


def iter_tool_uses(transcript_path: str):
    """(tool_name, tool_input) for every tool call of the session."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return
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
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    yield block.get("name") or "", block.get("input") or {}


def gui_files_of_session(transcript_path: str) -> list:
    """Every GUI file this session wrote to, oldest first, de-duplicated."""
    touched = []
    for name, tool_input in iter_tool_uses(transcript_path):
        if name not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            continue
        path = (tool_input.get("file_path")
                or tool_input.get("notebook_path") or "")
        if path and is_gui_file(path, written_text(tool_input)):
            if path not in touched:
                touched.append(path)
    return touched


def images_looked_at(transcript_path: str) -> set:
    """Basenames of every image the session OPENED with Read - the only
    machine-checkable trace that the agent actually looked at its own GUI."""
    seen = set()
    for name, tool_input in iter_tool_uses(transcript_path):
        if name != "Read":
            continue
        path = tool_input.get("file_path") or ""
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            seen.add(Path(path).name.lower())
    return seen


def resolve_floor(proof: Path) -> tuple:
    """The project's screen floor, and whether its override is justified."""
    frame = proof.parent / FRAME_FILENAME
    if not frame.is_file():
        return FLOOR_WIDTH, FLOOR_HEIGHT, None
    try:
        data = json.loads(frame.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, ValueError, OSError):
        return FLOOR_WIDTH, FLOOR_HEIGHT, f"{frame} is not readable JSON"
    width = int(data.get("floor_width") or FLOOR_WIDTH)
    height = int(data.get("floor_height") or FLOOR_HEIGHT)
    reason = str(data.get("reason") or "").strip()
    if (width, height) != (FLOOR_WIDTH, FLOOR_HEIGHT) and len(reason) < 20:
        return (FLOOR_WIDTH, FLOOR_HEIGHT,
                f"{frame} raises the screen floor to {width}x{height} without "
                "a stated reason - an override needs one, in the file")
    return width, height, None


def proof_problems(proof: Path, text: str, session: str, touched: list,
                   looked_at: set) -> list:
    """Everything the proof fails to establish. Empty list = the session may
    end."""
    problems = []
    root = proof.parent.parent

    if session not in text:
        problems.append(
            f"  - it does not name this session ({session}); an earlier "
            "session's proof does not carry over")

    unproven = [p for p in touched
                if Path(p).stem.lower() not in text.lower()]
    if unproven:
        problems.append("  - these touched files appear nowhere in it: "
                        + ", ".join(unproven))

    if "PASS" not in text:
        problems.append("  - no PASS: no window is claimed to have survived "
                        "the runtime audit")

    floor_width, floor_height, frame_problem = resolve_floor(proof)
    if frame_problem:
        problems.append(f"  - {frame_problem}")

    minimums = MIN_RE.findall(text)
    if not minimums:
        problems.append("  - no MIN <width>x<height>: every window declares a "
                        "COMPUTED minimum size, and it is checked here")
    for width, height in minimums:
        width, height = int(width), int(height)
        if width > floor_width or height > floor_height:
            problems.append(
                f"  - MIN {width}x{height} does not fit the screen floor "
                f"{floor_width}x{floor_height}. This is the absurd-minimum "
                "bug: the window demands a screen the user does not have. "
                "REFLOW it (ladder step 2) - never widen your way out")

    shots = SHOT_RE.findall(text)
    if not shots:
        problems.append("  - no SHOT <file.png>: a screenshot of each window "
                        "at its minimum is what makes the grade real")
    for shot in shots:
        candidate = Path(shot)
        if not candidate.is_absolute():
            candidate = root / shot
        if not candidate.is_file():
            problems.append(f"  - SHOT {shot} does not exist on disk "
                            f"(looked for {candidate})")
        elif candidate.stat().st_size < MIN_SHOT_BYTES:
            problems.append(f"  - SHOT {shot} is {candidate.stat().st_size} "
                            "bytes - that is not a screenshot of a window")
        elif candidate.name.lower() not in looked_at:
            problems.append(
                f"  - SHOT {shot} was never OPENED in this session. Read it "
                "(the Read tool renders images) and grade what you actually "
                "see - a grade written without looking is worthless")

    grades = GRADE_RE.findall(text)
    if not grades:
        problems.append(
            f"  - no GRADE <n>/10: after looking at each screenshot, grade it "
            f"against DESIGN.md. Below {MIN_GRADE}/10 nothing ships")
    for grade in grades:
        if int(grade) < MIN_GRADE:
            problems.append(
                f"  - GRADE {grade}/10 - you graded your own GUI below the "
                f"bar of {MIN_GRADE}/10 and that is an honest grade, so the "
                "session does not end here: FIX what the screenshot shows, "
                "re-shoot, re-grade. Raising the number without changing the "
                "GUI is a capacity lie")

    return problems


# --- shots hygiene (owner decree 2026-08-08 - Rad sa agentima) --------------
# Screenshots live in TOPIC subfolders whose names say what was being worked
# on - never dumped loose into .claude/shots/. Born from a real pile: 60+
# files named Controls_and_wheel__dark__colored__... that nobody could
# navigate. Only THIS session's files are judged (a gate judges only what
# the session did); legacy piles are cleaned by their own projects.

SHOT_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}

BLOCK_LOOSE_SHOTS = (
    "RAD SA AGENTIMA (rules/GUI.md -> Zubi v2, GATE of 2026-08-08): this "
    "session dropped screenshots straight into the ROOT of {shots}:\n"
    "{files}\n"
    "Every screenshot lives in a TOPIC subfolder whose name says what was "
    "being worked on there - shots/decision-dark-theme/, "
    "shots/hover-contrast-fix/ - so the owner opens one folder and sees one "
    "story, not a dump of 60 cryptic names. Move this session's images into "
    "a named subfolder, update any proof lines that point at them, and link "
    "folder + images in your message."
)


def check_shots_hygiene(payload: dict) -> None:
    transcript = payload.get("transcript_path") or ""
    if not transcript or not os.path.isfile(transcript):
        return
    try:
        session_start = os.path.getctime(transcript)
    except OSError:
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    shots_dir = None
    for directory in (cwd, *cwd.parents):
        candidate = directory / ".claude" / "shots"
        if candidate.is_dir():
            shots_dir = candidate
            break
    if shots_dir is None:
        return
    loose = []
    try:
        for item in shots_dir.iterdir():
            if (item.is_file() and item.suffix.lower() in SHOT_SUFFIXES
                    and item.stat().st_mtime >= session_start - 60):
                loose.append(item.name)
    except OSError:
        return
    if loose:
        listing = "".join(f"  - {name}\n" for name in sorted(loose)).rstrip()
        print(BLOCK_LOOSE_SHOTS.format(shots=shots_dir, files=listing),
              file=sys.stderr)
        sys.exit(2)


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return  # already continuing because of a Stop hook - never loop
    check_shots_hygiene(payload)
    transcript = payload.get("transcript_path") or ""
    touched = gui_files_of_session(transcript)
    if not touched:
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    session = str(payload.get("session_id") or "").strip() or "<session id>"
    proof = find_proof_file(cwd)
    listing = "".join(f"  - {p}\n" for p in touched)

    if proof is None:
        target = cwd / ".claude" / PROOF_FILENAME
        detail = f"  - {target} does not exist: no proof at all"
        floor_width, floor_height = FLOOR_WIDTH, FLOOR_HEIGHT
    else:
        target = proof
        text = proof.read_text(encoding="utf-8", errors="replace")
        floor_width, floor_height, _ = resolve_floor(proof)
        problems = proof_problems(proof, text, session, touched,
                                  images_looked_at(transcript))
        if not problems:
            return
        detail = "\n".join(problems)

    print(
        BLOCK_NO_PROOF.format(
            files=listing, detail=detail, proof=target,
            template=PROOF_TEMPLATE.format(session=session),
            fw=floor_width, fh=floor_height, grade=MIN_GRADE),
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
