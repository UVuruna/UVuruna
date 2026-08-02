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

Contract: exit 2 = BLOCK (stderr is fed back to the agent); exit 0 = pass.
Fail-open on any parse error — a broken guard must never brick a session.
"""

import json
import re
import sys

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

BLOCK_TERSE = (
    "COMMUNICATION LAW (rules/PLAN.md -> Communication with the Owner): your chat "
    "message asks the owner enumerated one-line questions with no explanation. This "
    "is forbidden - it has repeatedly caused total misunderstanding. Rewrite each "
    "question as a full block: (a) the context - what you are working on and where "
    "the decision arises, (b) the question itself in complete sentences, (c) why it "
    "matters and what depends on the answer, (d) the options with their concrete "
    "consequences, (e) your recommendation. Write it in Serbian, then end the turn."
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
    sys.exit(0)


if __name__ == "__main__":
    main()
