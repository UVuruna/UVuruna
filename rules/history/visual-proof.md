# The Visual Proof — the story

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="visual-proof"></a>

## The Visual Proof (owner decree 2026-08-06)

Born the same day as the Silent Audits law, from the same failure: agents
shipped a live time crown that was microscopic and mis-metaled on the real
dial, a bottom location line that was never implemented, and jewels sitting
sideways — while 1800 tests and every existing hook, including the DESIGN
REVIEW above, passed clean. The reason the review above did not catch it:
sub-agents never pass through the coordinator's Stop gates at all, and the
implementer graded its own work on zoomed crops that never showed the defect.
A self-graded close-up is not proof — it is the failure mode this law exists
to name.

**No session whose work changes what the user SEES may end without an
INDEPENDENT grader's screenshot proof.** Independent means: not the agent
that wrote the code. The grader launches the real app at its real default
size, takes FULL-window / FULL-dial screenshots — never a cropped or zoomed
region — and grades each one against the text of the ruling it is meant to
satisfy (a decree, a spec line, an owner instruction). Grade ≥ 8 per touched
ruling; below that the answer is fix, re-shoot, re-grade, exactly as in
DESIGN REVIEW above — never round up.

**Proof file:** `.claude/visual-proof.json`, JSON:

```json
{
  "commit": "<git rev-parse HEAD of the project, exactly>",
  "implementer": "<who wrote the code>",
  "grader": "<who graded it — MUST differ from implementer>",
  "items": [
    {"ruling": "<the text being checked>", "image": "<path>", "grade": 9}
  ]
}
```

Every `image` must exist, be a real screenshot (≥ 200 KB or ≥ 700 px on its
shorter side), and be newer than the commit it claims to prove — a stale
screenshot proves nothing. `commit` must match the project's current HEAD.

**Exemption:** a session that provably touched no rendering/GUI code may
write `VISUAL_PROOF: exempt` into `.claude/session-tasks.md` instead of
producing a proof file. The coordinator owns the honesty of that line — a
false exemption is a lie under **FIXED = VERIFIED** ([root
CLAUDE.md](../../CLAUDE.md) Law #5), no different from an inflated grade.

<a id="visual-proof-scope"></a>

### Scope — the gate judges only what the session DID (owner decree 2026-08-07)

**A gate may only ask about projects THIS session actually wrote to.** Version
one of the hook keyed off the harness cwd, so a session designing a brand-new
component was blocked by a failing grade another, still-running session had
left in DOMY Watch — a project it had only READ one markdown file from. The
owner named the defect exactly: *"nema on šta da provjerava dizajn domija ako
ti radiš totalno 2. projekat"*. A gate that judges work the session did not do
trains agents to silence gates, which is the opposite of what teeth are for.

- **Scope comes from the transcript** — the file paths of this session's own
  `Write` / `Edit` / `NotebookEdit` calls, each mapped to its project root.
  Every such project is gated; nothing else is.
- **`.claude/` paths are never scope** — harness state, not product, exactly as
  in the doc guards.
- **Wrote to no project → nothing to prove**, and the session ends clean. No
  exemption line is needed for a session that only read, searched or ran things.
- **Scope UNKNOWN falls back to the cwd project** — an unreadable transcript,
  or a session that launched SUBAGENTS (their writes live in their own
  transcripts, and sub-agent GUI work is the very failure this law was born
  from). Unknown scope must never be cheaper than known scope.
- Honest limit: a file written by a shell heredoc instead of the file tools is
  invisible to this scoping. Closing that would mean parsing arbitrary shell,
  whose false positives are the bug being fixed here.

- Class: **GATE** — machine-enforced by `rules/hooks/visual_proof_guard.py`
  (Stop, machine-wide). An unreadable or incomplete proof file BLOCKS — it is
  never treated as an absent proof to fail open on.

---

