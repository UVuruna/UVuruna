#!/usr/bin/env python3
"""Communication guard — owner decree 2026-08-02.

Enforces the Communication Law (rules/PLAN.md -> Communication with the Owner)
across ALL sessions on this machine (wired in ~/.claude/settings.json):

  Stop hook        — blocks ending the turn when the assistant's chat text
                     contains raw diagram source (Mermaid/flowchart), which the
                     owner sees as unrendered garbage, or a terse enumerated
                     question block instead of fully explained questions.
  PreToolUse hook  — matcher AskUserQuestion: blocks questions that lack the
                     minimum substance (context + explanation + option detail).
  PreToolUse hook  — matcher Write|Edit|NotebookEdit: blocks the first
                     file-mutating call of a session until THE DELIVERABLE LINE
                     has been written (PLAN.md -> The Deliverable Line, GATE of
                     2026-08-05).
  PreToolUse hook  — matcher Artifact: blocks publishing a rendered page that
                     relies on the viewer's theme detection (prefers-color-scheme
                     / data-theme tokens) or that never sets its own background —
                     the exact recipe that rendered white-on-white garbage for
                     the owner (PLAN.md -> Communication, LAW of 2026-08-03).

Contract: exit 2 = BLOCK (stderr is fed back to the agent); exit 0 = pass.
Fail-open on any parse error — a broken guard must never brick a session.
"""

import json
import os
import re
import sys
from pathlib import Path

# ═══════════════════════════ THRESHOLDS ═══════════════════════════

MIN_QUESTION_CHARS = 100      # AskUserQuestion: question text must carry context
MIN_OPTION_DESC_CHARS = 40    # AskUserQuestion: each option needs a real explanation
TERSE_ENUM_MAX_CHARS = 600    # chat text shorter than this with (1)(2)... asks = terse

DIAGRAM_FENCE_RE = re.compile(r"```\s*(mermaid|graphviz|dot|plantuml)\b", re.I)
DIAGRAM_SOURCE_RE = re.compile(
    r"^\s*(flowchart|graph)\s+(TB|TD|LR|RL|BT)\b"
    r"|^\s*(sequenceDiagram|stateDiagram(-v2)?|classDiagram|erDiagram|gantt|journey)\s*$",
    re.M,
)
ENUM_MARKER_RE = re.compile(r"\(\d\)")
# THE DELIVERABLE LINE (PLAN.md, GATE of 2026-08-05): "ISPORUKA: kod = ... ·
# dokument = ...". Accepted in either language and with either separator, since
# the point is the DECLARATION, not its punctuation. Both halves must be named
# — a line that mentions only one of them is the very substitution the rule
# exists to stop.
DELIVERABLE_RE = re.compile(
    r"^\s*(ISPORUKA|DELIVERABLE)\b.*?\b(kod|code)\b.*?\b(dokument|document|doc)\b",
    re.I | re.M | re.S,
)

BLOCK_DIAGRAM = (
    "COMMUNICATION LAW (rules/PLAN.md -> Communication with the Owner): your chat "
    "message contains raw diagram source (Mermaid/flowchart). The owner's interface "
    "shows this as unrendered source text - to him it is garbage. Re-present now: "
    "explain the algorithm/flow in DETAILED plain prose (numbered steps, full "
    "sentences, in Serbian). If a visual sketch is genuinely needed, render it as an "
    "Artifact or an HTML file opened for the owner - NEVER paste diagram source into "
    "the conversation. Diagram source is allowed only inside doc FILES (__flow/), "
    "never in chat."
)

BLOCK_DELIVERABLE = (
    "THE DELIVERABLE LINE (rules/PLAN.md -> The Deliverable Line, GATE of "
    "2026-08-05): this session has not declared what it ships, and you are "
    "about to change a file. Write the line FIRST, in chat, beside the triage "
    "class:\n\n"
    "    ISPORUKA: kod = <what lands in the repository> - dokument = <what is "
    "written>\n\n"
    "Either half may be a dash, and saying so is the point. A document that "
    "DESCRIBES the code is 'dokument', never 'kod' - a page, a brief, a "
    "diagram or a prompt sheet does not discharge a code deliverable. The rule "
    "exists because a session once built the page that described a registry, "
    "called that the deliverable, and reported the work finished. Declare the "
    "line, then continue."
)

BLOCK_TERSE = (
    "COMMUNICATION LAW (rules/PLAN.md -> Communication with the Owner): your chat "
    "message asks the owner enumerated one-line questions with no explanation. This "
    "is forbidden - it has repeatedly caused total misunderstanding. Rewrite each "
    "question as a full block: (a) the context - what you are working on and where "
    "the decision arises, (b) the question itself in complete sentences, (c) why it "
    "matters and what depends on the answer, (d) the options with their concrete "
    "consequences, (e) your recommendation. Write it in Serbian, then end the turn."
)

# ── RAD SA AGENTIMA (owner decree 2026-08-08) ──────────────────────────────
# When images are presented to the owner, their names are CLICKABLE LINKS —
# to each image AND to the folder that groups them — never bare filenames he
# has to hunt for by hand.

IMAGE_MENTION_RE = re.compile(r"\S+\.(?:png|jpe?g|svg|gif|bmp)\b", re.I)
MD_LINK_RE = re.compile(r"\]\(")
FENCE_RE = re.compile(r"^\s*```")

VISUAL_WORDS_RE = re.compile(
    r"\b(dizajn\w*|izgled\w*|layout|GUI|font\w*|ikon\w*|palet\w*"
    r"|boj(?:a|e|u|om|ama)|slik\w*|screenshot\w*|wireframe|mockup"
    r"|tem(?:a|u|e))\b", re.I)

BLOCK_IMAGE_LINKS = (
    "RAD SA AGENTIMA (rules/PLAN.md -> Communication, GATE of 2026-08-08): "
    "this message names image files as bare text:\n{lines}\n"
    "When the owner is shown images - especially for a decision - every "
    "image name is a CLICKABLE markdown link ([name](relative/path.png)) "
    "and the message also links the FOLDER that groups them "
    "([folder](path/)). He clicks; he does not hunt through a file tree by "
    "hand. Rewrite the references as links, then end the turn."
)

BLOCK_VISUAL_NO_IMAGE = (
    "RAD SA AGENTIMA (rules/PLAN.md -> Communication, GATE of 2026-08-08): "
    "this turn ends waiting on the owner with a VISUAL question (design/"
    "look/color/layout vocabulary) but shows him NOTHING - no image link, "
    "no rendered page, no folder of screenshots. A visual decision without "
    "pictures is not a question he can answer. Attach the evidence: links "
    "to the screenshots (and their topic folder), or a rendered "
    "Artifact/HTML page - then ask again."
)


def visible_lines(text: str):
    """Chat lines the owner actually reads - code fences and indented
    blocks are quoted material (report lines, file contents), not prose."""
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced or line.startswith("    "):
            continue
        yield line


def check_image_links(text: str) -> None:
    offenders = []
    for line in visible_lines(text):
        if IMAGE_MENTION_RE.search(line) and not MD_LINK_RE.search(line):
            offenders.append(f"  {line.strip()[:100]}")
    if offenders:
        block(BLOCK_IMAGE_LINKS.format(lines="\n".join(offenders[:8])))


def waiting_on_owner(cwd: Path) -> bool:
    for directory in (cwd, *cwd.parents):
        tasks = directory / ".claude" / "session-tasks.md"
        try:
            if tasks.is_file():
                return bool(re.search(
                    r"^WAITING_ON_OWNER:\s*yes\b",
                    tasks.read_text(encoding="utf-8", errors="replace"),
                    re.M))
        except OSError:
            return False
    return False


def check_visual_question(text: str, cwd: Path) -> None:
    if "?" not in text or not VISUAL_WORDS_RE.search(text):
        return
    if MD_LINK_RE.search(text) or "http" in text \
            or IMAGE_MENTION_RE.search(text):
        return
    if not waiting_on_owner(cwd):
        return
    block(BLOCK_VISUAL_NO_IMAGE)

ADAPTIVE_THEME_RE = re.compile(
    r"prefers-color-scheme|\[\s*data-theme|data-theme\s*=", re.I
)
BACKGROUND_RE = re.compile(r"background(-color)?\s*:", re.I)

BLOCK_ARTIFACT_THEME = (
    "COMMUNICATION LAW (rules/PLAN.md -> Communication with the Owner, LAW of "
    "2026-08-03): this page styles itself with ADAPTIVE theme tokens "
    "(prefers-color-scheme media queries / data-theme stamping). In the owner's "
    "artifact viewer this has repeatedly rendered as WHITE TEXT ON WHITE "
    "BACKGROUND. A rendered page commits to ONE explicit scheme: dark (matching "
    "the owner's environment) unless he asked otherwise, with background AND "
    "text color both set explicitly on the page body as fixed hex values - no "
    "media queries, no data-theme selectors, nothing inherited from the host. "
    "Rewrite the stylesheet with fixed colors and publish again."
)

BLOCK_ARTIFACT_NO_BG = (
    "COMMUNICATION LAW (rules/PLAN.md -> Communication with the Owner, LAW of "
    "2026-08-03): this page never sets its own background color, so it inherits "
    "the host shell's - the exact recipe for white-on-white garbage. Set an "
    "explicit fixed background AND text color on the page body (dark scheme, "
    "matching the owner's environment, unless he asked otherwise), then publish "
    "again."
)

BLOCK_ASK_TOOL = (
    "COMMUNICATION LAW (rules/PLAN.md -> Communication with the Owner): this "
    "AskUserQuestion call is too terse. Every question must carry its own context "
    "(what you are working on, where the decision arises, why it matters, what "
    "depends on the answer) inside the question text, and every option description "
    "must explain the concrete consequence of choosing it. Minimums: question >= "
    f"{MIN_QUESTION_CHARS} chars, each option description >= "
    f"{MIN_OPTION_DESC_CHARS} chars. Expand and call again (questions in Serbian)."
)

# ═══════════════════════════ HELPERS ═══════════════════════════


def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def entry_text(message: dict) -> str:
    """Concatenated text blocks of a transcript message; '' if none."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
    return "\n".join(parts)


def is_real_user_prompt(entry: dict) -> bool:
    """True for an actual owner message (not a tool_result carrier)."""
    if entry.get("type") != "user":
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(
            isinstance(item, dict) and item.get("type") == "tool_result"
            for item in content
        )
    return False


def collect_turn_text(transcript_path: str) -> str:
    """All assistant chat text since the owner's last real message."""
    texts = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if is_real_user_prompt(entry):
                texts = []
            elif entry.get("type") == "assistant":
                text = entry_text(entry.get("message") or {})
                if text:
                    texts.append(text)
    return "\n".join(texts)


# ═══════════════════════════ CHECKS ═══════════════════════════


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return  # already continuing because of a Stop hook - never loop
    path = payload.get("transcript_path") or ""
    try:
        text = collect_turn_text(path)
    except OSError:
        return
    if not text:
        return
    if DIAGRAM_FENCE_RE.search(text) or DIAGRAM_SOURCE_RE.search(text):
        block(BLOCK_DIAGRAM)
    if (
        len(text) < TERSE_ENUM_MAX_CHARS
        and "?" in text
        and len(ENUM_MARKER_RE.findall(text)) >= 2
    ):
        block(BLOCK_TERSE)
    check_image_links(text)
    check_visual_question(text, Path(payload.get("cwd") or os.getcwd()))


def check_artifact(payload: dict) -> None:
    """Block publishing a page that depends on the viewer's theme.

    Reads the file the Artifact call is about to publish. Fail-open on
    anything unreadable (list action, missing path, IO error) - the guard
    exists to catch the adaptive-theme recipe, not to brick publishing.
    """
    tool_input = payload.get("tool_input") or {}
    if tool_input.get("action") == "list":
        return
    path = tool_input.get("file_path")
    if not path:
        return
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            page = fh.read()
    except OSError:
        return
    if ADAPTIVE_THEME_RE.search(page):
        block(BLOCK_ARTIFACT_THEME)
    if "<style" in page.lower() and not BACKGROUND_RE.search(page):
        block(BLOCK_ARTIFACT_NO_BG)


def collect_session_text(transcript_path: str) -> str:
    """ALL assistant chat text of the session — the deliverable line is
    declared once and stands for the whole session, unlike the per-turn
    checks above."""
    texts = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "assistant":
                text = entry_text(entry.get("message") or {})
                if text:
                    texts.append(text)
    return "\n".join(texts)


def check_deliverable(payload: dict) -> None:
    """Block the first file-mutating call until the session has said what
    it ships. Fail-open on an unreadable transcript: a guard that cannot
    read must never brick the work.

    The chat transcript is the primary source, but NOT the only one: the
    VSCode-extension harness flushes an assistant message's text to the
    transcript only after the turn ends (verified live 2026-08-05 — the
    line stood twice in chat while the file held zero copies), so a line
    written and followed by file edits in the SAME turn is invisible here
    and the gate would deadlock every fresh session's first working turn.
    The same declaration at the top of the project's
    `.claude/session-tasks.md` (the session's on-disk contract, PLAN.md ->
    The Session Task List) is therefore accepted too (owner approval
    2026-08-05)."""
    path = payload.get("transcript_path") or ""
    if not path:
        return
    try:
        text = collect_session_text(path)
    except OSError:
        return
    if DELIVERABLE_RE.search(text):
        return
    cwd = Path(payload.get("cwd") or os.getcwd())
    for directory in (cwd, *cwd.parents):
        tasks_file = directory / ".claude" / "session-tasks.md"
        try:
            if tasks_file.is_file() and DELIVERABLE_RE.search(
                tasks_file.read_text(encoding="utf-8", errors="replace")
            ):
                return
        except OSError:
            pass
    block(BLOCK_DELIVERABLE)


def check_ask_user_question(payload: dict) -> None:
    tool_input = payload.get("tool_input") or {}
    for question in tool_input.get("questions") or []:
        if len((question.get("question") or "").strip()) < MIN_QUESTION_CHARS:
            block(BLOCK_ASK_TOOL)
        for option in question.get("options") or []:
            if len((option.get("description") or "").strip()) < MIN_OPTION_DESC_CHARS:
                block(BLOCK_ASK_TOOL)


# ═══════════════════════════ ENTRY POINT ═══════════════════════════


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
    if event == "Stop":
        check_stop(payload)
    elif event == "PreToolUse" and payload.get("tool_name") == "AskUserQuestion":
        check_ask_user_question(payload)
    elif event == "PreToolUse" and payload.get("tool_name") == "Artifact":
        check_artifact(payload)
    elif event == "PreToolUse" and payload.get("tool_name") in (
        "Write", "Edit", "NotebookEdit",
    ):
        check_deliverable(payload)
    sys.exit(0)


if __name__ == "__main__":
    main()
