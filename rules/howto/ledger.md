# HOWTO — the session ledger

One file per session, project-local and gitignored:
`.claude/sessions/<session_id>.md`. It replaces session-tasks.md,
session-report.md, agents-ledger.md, layout-proof.md and visual-proof.json — the
ledger IS the report. `gate.py prompt` creates it from
`rules/templates/ledger.md` on the first prompt and prints its path.

## Shape

```
# <session title>
kategorija: GUI + FEATURE · klasa: Standard · agenti: 1 sonnet grader
- [x] T1 Card "Watch face" in Settings @fable
    ! ev-0003 shot SettingsDialog laptop-avg — looked — grade 9 (contrast ok, siblings ok, nothing clipped)
    ! ev-0004 test tests/test_settings_card.py 6/6
- [~] T2 New watch "Nautilus" @sonnet
    ! ev-0007 test 12/12 · matrix 5/6 (row phone-landscape: emulator unavailable)
- [?] T3 BUILD & RELEASE — waits for the owner's word
    ? build v0.0.288 with T1+T2? command: python setup/build.py
```

## Grammar

- **The `kategorija:` line comes first** and names at least one of
  `GUI FEATURE BUGFIX REFACTOR DOCS PLAN BUILD`, the triage class and the
  agents. No product-file edit is allowed before it exists (`gate.py pre`). When
  the work grows into another category, append it in the same turn — the gate
  reads the LAST state.
- **States:** `[ ]` not started · `[>]` in progress · `[?]` waits for the owner
  (must carry a `?` line with the actual question) · `[~]` done but unconfirmed
  or unprovable by machine · `[x]` done WITH evidence (must carry a `!` line).
- **Indent 2 spaces per level.** One task per line, his wording preserved.
- **A message he sends mid-session joins the list in the same turn** — new
  tasks, changed states, a restamped `?`. A ledger older than his last message
  blocks the turn.
- **Open `[ ]`/`[>]` tasks block the end of a session** unless a `[?]` exists.
- The final message opens with the open items (`[ ]`, `[~]`, `[?]`), then the
  finished ones with their evidence, then `## BUILD & RELEASE?` when the project
  is installable.

## Evidence lines

- `!` lines under GUI / FEATURE / BUGFIX / REFACTOR tasks reference at least one
  `ev-NNNN` id from `.claude/evidence/<session_id>/evidence.jsonl` (or
  `commit <sha>` for a pure move). DOCS and PLAN `!` lines are free text.
- Only `rules/tools/uv.py` writes `evidence.jsonl`; a Write or Edit aimed at it
  fails the session.
- Every referenced row must be NEWER than the last edit of a product file, must
  not be `kind: unavailable`, and — for shots — its PNG must have been opened
  with Read after the row's timestamp.
- A sub-agent reports its own `! ` lines in its final text; the coordinator
  copies the ids into the ledger.

## Optional blocks

```
matrica:                      (FEATURE — written BEFORE the first product edit)
| # | scenario | input/state | device | evidence |
| 1 | average device: start + main flow | fresh install | laptop-avg | ev-0009 |
| 2 | fresh install — no owner paths/hooks/rules used | — | pc-low | ev-0010 |
| 3 | old path removed (replacement) | grep old symbol | — | ev-0011 |
uzrok: <root cause>                                (BUGFIX)
proces-uzrok: <why the previous claim was false>   (REPEAT)
```
