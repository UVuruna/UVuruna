# BUGFIX — category rules

A reported bug. Read with `CODE.md`. Fix first with the cheapest probe,
investigate after; a bug report is Trivial class unless it proves otherwise.

## The tooth (`gate.py stop`)

1. **RED before** — a recorded reproduction that FAILS before the fix:
   `uv test <the failing test>` (rc ≠ 0) or `uv run` whose log carries the
   error. This is the only proof the agent ever saw the bug. Without it there
   is no fix, only a theory.
2. **GREEN after** — the same reproduction passes, run AFTER the last product
   edit. Both rows sit in `evidence.jsonl` and the ledger `!` line names them
   (runner usage: `howto/runner.md`, ledger grammar: `howto/ledger.md`).
3. **`uzrok: <root cause>`** in the ledger — the mechanism, not the symptom.
   FIXED = VERIFIED: a session ends FIXED (cause + fix + evidence), CANNOT FIX
   HERE (why + what would unblock) or IMPOSSIBLE (technical reason).
4. **A repeat is a PROCESS failure first** — when he reports something a
   previous round closed, the FIRST line is `proces-uzrok:`: what was claimed,
   what that claim rested on, and why that evidence could be green while the app
   was broken. The code fix comes second. · `gate.py stop` requires it when his
   message says `opet · ponovo · again · still · i dalje`.
5. **Before believing a report is stale, check what he is RUNNING** — the
   installed version against the latest release answers "bug or undelivered
   fix" in one command, and it is the cheapest question in this monorepo.

## Honest states

- `[x]` only on HIS confirmation or evidence from HIS machine (his log, his
  installed binary, his screenshot). A test written by the same reasoning that
  produced the bug cannot falsify that reasoning.
- `[~]` — shipped, unconfirmed: the fix is in, but the repro exists only on his
  device (a phone bug no emulator shows) or the runner reported the profile
  unavailable. Every `[~]` is carried into the next round's report until he
  closes it, and it is said out loud, never buried mid-text.
- Anything unfinished, partial, deferred or reinterpreted OPENS the final
  message, before any success. A debt claim names the evidence looked at
  ("grepped render/, no such element") — a guess about "impossible" is the
  costliest lie, because it cancels planned work.

## While fixing

- No error masking, no defensive noise, no hardcoded patch value (`CODE.md`).
- The regression test lands in the project's suite, not in a scratch file.
- Docs of the changed file are updated in the same session (`DOCS.md`).
- A fix that touches a GUI file carries the GUI tooth too (`GUI.md`).

History → `history/session-ledger.md` (the week of ten "done" tasks that were
not done, and the decree that created `[~]`).
