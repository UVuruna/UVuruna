#!/usr/bin/env python3
"""Agents guard - owner decree 2026-08-06, hardened the same evening.

THE MECHANIC, AND NOTHING ELSE: a session that launched subagents CANNOT
END while any of them is still running. It waits, in silence, until the
harness records every agent's completion. No ledger, no "handed over", no
paperwork a session could write to unlock itself - NOTHING the session
writes counts. Only the transcript's own machine records decide:

  LAUNCH      an assistant tool_use block, tool name Task/Agent
  BACKGROUND  its tool_result says "Async agent launched" and carries
              `agentId: <token>` (a synchronous agent's tool_result IS its
              completed result - nothing further to wait for)
  COMPLETION  a later transcript record that mentions that agentId again -
              the task-notification the harness enqueues when the agent
              ends (the launch metadata itself is excluded from the count)

No completion record => the agent is presumed STILL RUNNING => exit 2,
block, wait. A spawn whose result cannot be parsed is treated as running
too - unknown is not finished.

Born from the real evening this rule exists for: a session launched two
background agents, lost them to context summarization, told the owner they
were someone else's, and CLOSED - while the agents kept editing two
projects with nobody attached to them. The owner: "glavna sesija ne sme da
stane dok njeni agenti nisu svi zavrsili" - and no written rule, only this.

Wired MACHINE-WIDE in ~/.claude/settings.json (Stop).
Contract: exit 2 = BLOCK (stderr fed back); exit 0 = pass. Fail-open only
on a crash of the guard itself - never on an unparseable agent state.
"""

import json
import os
import re
import sys

#: tool names that launch a subagent in this harness
AGENT_TOOLS = {"Task", "Agent"}

ASYNC_LAUNCH_RE = re.compile(r"Async agent launched", re.IGNORECASE)
AGENT_ID_RE = re.compile(r"agentId:\s*([A-Za-z0-9_-]+)")

BLOCK = (
    "AGENTS ARE NOT DAEMONS (owner decree 2026-08-06): this session "
    "launched {total} subagent(s) and {open_count} of them HAVE NO "
    "COMPLETION RECORD in the transcript - they are presumed STILL "
    "RUNNING. The session that launches agents cannot end before ALL of "
    "them finish. There is no unlock the session can write for itself: "
    "no ledger line, no handover note, nothing - only the harness's own "
    "completion notification counts.\n"
    "Still running:\n{open_list}\n"
    "WAIT for the completion notification(s), collect and verify each "
    "result, report them - and only then end. If an agent is stuck, that "
    "is a fact for the OWNER, in chat, while this session stays alive "
    "watching it - never a reason to close."
)


# How many transcript records may stand on top of an agent's `tool_use` before
# a missing `tool_result` is read as an ABANDONED call rather than one that is
# still starting. A launch and its result are written adjacently, so this is
# generous: it only has to survive the harness interleaving a record or two.
STALE_AFTER_RECORDS = 2


def transcript_lines(path: str):
    if not path or not os.path.isfile(path):
        return
    with open(path, encoding="utf-8", errors="replace") as handle:
        yield from handle


def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        return
    path = payload.get("transcript_path") or ""

    spawns = {}          # tool_use_id -> description
    results = {}         # tool_use_id -> raw result text
    spawn_at = {}        # tool_use_id -> the record index it was written at
    result_at = {}       # tool_use_id -> the record index its result landed at
    last_index = -1      # the last record index in the whole transcript
    for index, raw in enumerate(transcript_lines(path)):
        last_index = index
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
            if (block.get("type") == "tool_use"
                    and block.get("name") in AGENT_TOOLS):
                tool_input = block.get("input") or {}
                label = (tool_input.get("description")
                         or str(tool_input.get("prompt") or "")[:60]
                         or "<agent>")
                spawns[block.get("id")] = str(label).strip()
                spawn_at[block.get("id")] = index
            if block.get("type") == "tool_result":
                content = block.get("content")
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False)
                results[block.get("tool_use_id")] = content
                result_at[block.get("tool_use_id")] = index

    if not spawns:
        return

    # background agents: launch metadata carries the agentId; completion is
    # ANY LATER transcript record mentioning that id outside the launch
    # metadata itself (the harness's task-notification when the agent ends)
    open_agents = []
    launch_texts = {}
    for use_id, label in spawns.items():
        result = results.get(use_id)
        if result is None:
            # A TRUNCATED TURN IS NOT AN UNFINISHED AGENT (owner report,
            # fixed 2026-08-14). When a turn is cut off mid-flight — he
            # interrupts, the window closes, the process dies — the assistant
            # record carrying the `tool_use` block is already on disk while
            # the `tool_result` never gets written. Reading that as "an agent
            # is still starting" blocked the end of sessions in which nothing
            # was running at all.
            #
            # The two cases are told apart by what came AFTER, which is the
            # only evidence that exists: the harness writes a tool_result
            # before the conversation can move on, so a spawn with later
            # records standing on top of it was ABANDONED, while a spawn
            # sitting at the very end of the transcript may genuinely still
            # be starting. `STALE_AFTER_RECORDS` is the margin — a launch
            # record and its result are adjacent, so anything beyond a couple
            # of records means the transcript moved on without it.
            #
            # FAILING OPEN HERE IS THE RIGHT DIRECTION, and it is a deliberate
            # trade rather than an oversight: the cost of a missed unfinished
            # agent is that a session ends with work still running, which the
            # task list and the final report both catch. The cost of the false
            # positive is that he cannot end a session at all — and a gate
            # that blocks on ordinary, correct behaviour is one everybody
            # learns to work around, which costs more than the case it guards.
            if last_index - spawn_at.get(use_id, last_index) > STALE_AFTER_RECORDS:
                continue  # abandoned by a truncated turn, not running
            open_agents.append((label, "no tool_result - still starting"))
            continue
        if not ASYNC_LAUNCH_RE.search(result):
            continue  # synchronous agent - its result IS the completion
        match = AGENT_ID_RE.search(result)
        if not match:
            open_agents.append((label, "background launch with no "
                                       "parseable agentId - unknown is "
                                       "not finished"))
            continue
        launch_texts[match.group(1)] = (label, result, result_at.get(use_id, -1))

    if launch_texts:
        seen = {agent_id: 0 for agent_id in launch_texts}
        for index, raw in enumerate(transcript_lines(path)):
            for agent_id in launch_texts:
                if agent_id not in raw:
                    continue
                # THE LAUNCH RECORD IS SKIPPED BY ITS INDEX, NEVER BY MATCHING
                # ITS OWN TEXT AGAINST THE RAW LINE (fixed 2026-08-14, found by
                # driving this guard over synthetic transcripts rather than by
                # reading it). The old test was `launch_result[:80] in raw`,
                # and it could not fire: `launch_result` is the DECODED result
                # string, carrying real newlines, while `raw` is the JSON line
                # where those same newlines are an escape sequence. Every
                # launch result contains a newline — "Async agent launched
                # successfully." and the `agentId:` line are always on separate
                # lines — so the comparison always failed, the launch record
                # always counted as its own life sign, and a background agent
                # that never finished has NEVER been reported by this guard.
                # It has been open the whole time this branch has existed, and
                # nothing noticed because the guard only ever spoke up about
                # the missing-tool_result case above, which is precisely the
                # case that was firing wrongly.
                if index == launch_texts[agent_id][2]:
                    continue
                seen[agent_id] += 1
        for agent_id, count in seen.items():
            if count == 0:
                label = launch_texts[agent_id][0]
                open_agents.append(
                    (label, "background agent with NO completion record"))

    if not open_agents:
        return

    listing = "".join(f"  - {label}  <- {why}\n"
                      for label, why in open_agents)
    print(BLOCK.format(total=len(spawns), open_count=len(open_agents),
                       open_list=listing), file=sys.stderr)
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
    if payload.get("hook_event_name", "") != "Stop":
        sys.exit(0)
    try:
        check_stop(payload)
    except SystemExit:
        raise
    except Exception:  # a crash of the guard itself must not brick sessions
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
