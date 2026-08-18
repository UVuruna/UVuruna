"""A session cannot end while a sub-agent it launched is still running.

Ported verbatim from agents_guard.py (owner decree 2026-08-06). Only the
harness's own records decide: a launch is closed by its tool_result, and a
BACKGROUND launch (`Async agent launched`, `agentId: <token>`) is closed only
by a later record mentioning that agentId. Unknown is not finished.
"""

from __future__ import annotations

import json
import os
import re

ASYNC_LAUNCH_RE = re.compile(r"Async agent launched", re.IGNORECASE)
AGENT_ID_RE = re.compile(r"agentId:\s*([A-Za-z0-9_-]+)")

# How many records may stand on top of a `tool_use` before a missing
# `tool_result` reads as a turn that was CUT OFF rather than an agent that is
# still starting. A launch and its result are written adjacently.
STALE_AFTER_RECORDS = 2


def _lines(path: str):
    if not path or not os.path.isfile(path):
        return
    with open(path, encoding="utf-8", errors="replace") as handle:
        yield from handle


def still_running(model) -> list[tuple[str, str]]:
    """[(label, why)] for every agent with no completion record."""
    spawns = {}
    for tool in model.agent_launches():
        label = (tool.input.get("description")
                 or str(tool.input.get("prompt") or "")[:60] or "<agent>")
        spawns[tool.id] = (str(label).strip(), tool.index)
    if not spawns:
        return []

    open_agents: list[tuple[str, str]] = []
    launch_texts = {}
    for use_id, (label, spawn_at) in spawns.items():
        result = model.tool_results.get(use_id)
        if result is None:
            # A truncated turn is not an unfinished agent: the harness writes
            # a tool_result before the conversation can move on, so a spawn
            # with later records on top of it was abandoned.
            if model.last_index - spawn_at > STALE_AFTER_RECORDS:
                continue
            open_agents.append((label, "no tool_result — still starting"))
            continue
        if not ASYNC_LAUNCH_RE.search(result.text):
            continue  # synchronous agent — its result IS the completion
        match = AGENT_ID_RE.search(result.text)
        if not match:
            open_agents.append((label, "background launch with no parseable "
                                       "agentId — unknown is not finished"))
            continue
        launch_texts[match.group(1)] = (label, result.index)

    if launch_texts:
        seen = {agent_id: 0 for agent_id in launch_texts}
        for index, raw in enumerate(_lines(model.path)):
            for agent_id, (_, result_index) in launch_texts.items():
                # the launch record is skipped BY ITS INDEX, never by matching
                # its own decoded text against the raw JSON line
                if agent_id in raw and index != result_index:
                    seen[agent_id] += 1
        for agent_id, count in seen.items():
            if count == 0:
                open_agents.append((launch_texts[agent_id][0],
                                    "background agent with NO completion "
                                    "record"))
    return open_agents


def check(model) -> list[str] | None:
    open_agents = still_running(model)
    if not open_agents:
        return None
    names = "; ".join(f"{label} ({why})" for label, why in open_agents[:2])
    return [
        f"{len(open_agents)} sub-agent(s) have no completion record — they are "
        "still running.",
        "FIX: wait for the completion notification, verify each result, report "
        "it — nothing you write can unlock this.",
        f"where: {names}",
    ]


def parse_result_text(value) -> str:
    """Kept for callers that hold a raw tool_result payload."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)
