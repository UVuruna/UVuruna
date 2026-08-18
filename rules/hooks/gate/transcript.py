"""Parses the hook transcript (JSONL) ONCE into a small dataclass model.

Every check receives this model instead of re-reading the file. The file is
streamed line by line and never concatenated into one string: transcripts
reach tens of megabytes because pasted screenshots ride in them as base64.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import paths

AGENT_TOOLS = {"Task", "Agent"}
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")

# Harness wrappers around a user record that are NOT the owner speaking.
WRAPPER_RE = re.compile(
    r"<(system-reminder|local-command-caveat|local-command-stdout|command-name"
    r"|command-message|command-args|ide_opened_file|ide_selection"
    r"|user-prompt-submit-hook)>.*?</\1>",
    re.S | re.I,
)
OPEN_WRAPPER_RE = re.compile(r"</?(system-reminder|command-[a-z]+)[^>]*>", re.I)

# A record whose line is huge and carries none of these keys is an attachment
# or a pasted image — parsing its JSON costs more than everything else here.
INTERESTING = ('"tool_use"', '"tool_result"', '"text"')
BIG_LINE = 120_000


@dataclass(slots=True)
class ToolUse:
    index: int
    id: str
    name: str
    input: dict
    ts: datetime | None

    @property
    def file_path(self) -> str:
        return str(self.input.get("file_path")
                   or self.input.get("notebook_path") or "")


@dataclass(slots=True)
class ToolResult:
    index: int
    tool_use_id: str
    text: str


@dataclass(slots=True)
class Message:
    index: int
    role: str          # "user" | "assistant"
    text: str
    ts: datetime | None
    owner: bool        # a real message from the owner, not a harness wrapper


@dataclass
class Transcript:
    path: str = ""
    is_subagent: bool = False
    last_index: int = -1
    messages: list[Message] = field(default_factory=list)
    tool_uses: list[ToolUse] = field(default_factory=list)
    tool_results: dict[str, ToolResult] = field(default_factory=dict)

    # ── owner side ───────────────────────────────────────────────
    @property
    def owner_messages(self) -> list[Message]:
        return [m for m in self.messages if m.owner]

    def last_owner_message(self) -> Message | None:
        owner = self.owner_messages
        return owner[-1] if owner else None

    def first_owner_message(self) -> Message | None:
        owner = self.owner_messages
        return owner[0] if owner else None

    # ── assistant side ───────────────────────────────────────────
    def final_turn_texts(self) -> list[str]:
        """Assistant text blocks written since the owner's last message."""
        start = -1
        for message in self.messages:
            if message.owner:
                start = message.index
        return [m.text for m in self.messages
                if m.role == "assistant" and m.index > start and m.text.strip()]

    def final_text(self) -> str:
        texts = self.final_turn_texts()
        return texts[-1] if texts else ""

    # ── tools ────────────────────────────────────────────────────
    def edits(self) -> list[ToolUse]:
        return [t for t in self.tool_uses if t.name in paths.EDIT_TOOLS]

    def product_edits(self, root: Path) -> list[ToolUse]:
        return [t for t in self.edits()
                if paths.is_product_file(t.file_path, root)]

    def gui_edits(self, root: Path, is_gui_path) -> list[ToolUse]:
        return [t for t in self.product_edits(root) if is_gui_path(t.file_path)]

    def image_reads(self) -> list[tuple[str, datetime | None]]:
        """(basename, ts) of every image the session OPENED with Read."""
        found = []
        for tool in self.tool_uses:
            if tool.name != "Read":
                continue
            path = tool.file_path
            if path.lower().endswith(IMAGE_SUFFIXES):
                found.append((Path(path).name.lower(), tool.ts))
        return found

    def runs(self) -> list[ToolUse]:
        return [t for t in self.tool_uses if t.name in ("Bash", "PowerShell")]

    def agent_launches(self) -> list[ToolUse]:
        return [t for t in self.tool_uses if t.name in AGENT_TOOLS]


# ═══════════════════════════ PARSING ═══════════════════════════

def parse_ts(value) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp


def _blocks_text(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = [b.get("text", "") for b in content
             if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(p for p in parts if p)


def _is_owner_message(entry: dict, text: str) -> bool:
    if entry.get("type") != "user" or entry.get("isMeta") or \
            entry.get("isSidechain"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result"
            for b in content):
        return False
    stripped = OPEN_WRAPPER_RE.sub("", WRAPPER_RE.sub("", text)).strip()
    return bool(stripped)


def owner_text(text: str) -> str:
    """The owner's own words, with harness wrappers removed."""
    return OPEN_WRAPPER_RE.sub("", WRAPPER_RE.sub("", text)).strip()


def is_subagent_transcript(path: str) -> bool:
    parts = [p.lower() for p in re.split(r"[\\/]+", str(path)) if p]
    return "subagents" in parts


def load(path: str) -> Transcript:
    model = Transcript(path=path or "",
                       is_subagent=is_subagent_transcript(path or ""))
    if not path or not os.path.isfile(path):
        return model
    with open(path, encoding="utf-8", errors="replace") as handle:
        for index, raw in enumerate(handle):
            model.last_index = index
            if len(raw) > BIG_LINE and not any(k in raw for k in INTERESTING):
                continue  # pasted image / attachment record
            # cheap pre-filter; both compact and pretty JSON must survive it
            if '"user"' not in raw and '"assistant"' not in raw:
                continue
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            kind = entry.get("type")
            if kind not in ("user", "assistant"):
                continue
            message = entry.get("message") or {}
            content = message.get("content")
            stamp = parse_ts(entry.get("timestamp"))
            text = _blocks_text(content)
            if text.strip():
                model.messages.append(Message(
                    index=index, role=kind, text=text, ts=stamp,
                    owner=_is_owner_message(entry, text)))
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    model.tool_uses.append(ToolUse(
                        index=index, id=str(block.get("id") or ""),
                        name=str(block.get("name") or ""),
                        input=block.get("input") or {}, ts=stamp))
                elif block.get("type") == "tool_result":
                    body = block.get("content")
                    if not isinstance(body, str):
                        try:
                            body = json.dumps(body, ensure_ascii=False)
                        except (TypeError, ValueError):
                            body = str(body)
                    model.tool_results[str(block.get("tool_use_id") or "")] = \
                        ToolResult(index=index,
                                   tool_use_id=str(block.get("tool_use_id")
                                                   or ""), text=body)
    return model
