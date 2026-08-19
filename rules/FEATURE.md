# FEATURE — category rules

New functionality, a new setting, or a replacement of an existing function.
Read with `CODE.md`. GUI work in the same session also reads `GUI.md`.

## Before the first product edit

1. **Present what you understood** — Trivial: one sentence of intent · Standard:
   algorithm sketch or GUI wireframe (box-drawing in chat, rendered page when
   complex) + prose walkthrough + why this approach + what is unclear, then wait
   for his yes · Wide: echo-brief (all instructions regrouped into wholes, "this
   is how I understood everything" + open questions), then wait.
   · `gate.py stop` + conduct · history → `history/present-before-building.md`.
2. **Write the scenario MATRIX into the ledger** — before the first edit, and
   for Standard/Wide he sees it in the sketch and may add rows.
   · `gate.py pre` blocks the first product edit without it (Trivial exempt).

```
matrica:
| # | scenario | input/state | device | evidence |
| 1 | average device: start + main flow | fresh install | laptop-avg | ev-0009 |
| 2 | fresh install — no owner paths/hooks/rules used | — | pc-low | ev-0010 |
| 3 | old path removed (replacement) | grep old symbol | — | ev-0011 |
```

**Mandatory rows** (the gate looks for the keywords): `average device` ·
`fresh install` — nothing of the owner's environment is used · and when the
feature REPLACES something, `old path removed`, proven by a grep for the old
symbol. Add the real rows of the feature: empty state, error path, the
second-largest input, both orientations for a phone target.

## After the code

- **Every row carries evidence produced by the runner**, newer than the last
  product edit: `uv test <pytest args>` · `uv run "<cmd>" --profile <p>` ·
  `uv device <profile> <url|apk>`. A row's `evidence` column names its `ev-`
  id (runner usage: `howto/runner.md`). · `gate.py stop`.
- **Virtual devices are HEADLESS and SILENT** — an emulator or browser the
  runner boots never opens a window or plays sound on the owner's desk (owner
  decree 2026-08-18); the agent looks at `adb screencap` PNGs. · runner.
- **A row that cannot be proven is honest, not hidden** — the runner writes a
  `kind: unavailable` row (missing emulator, no hardware), the task stays `[~]`
  and the final message says which scenario is unproven and why. Never `[x]`.
- **Docs follow the code in the same session** (`DOCS.md`), and the feature's
  own config lives in the project config, never hardcoded (`CODE.md`).
- **Standard/Wide: a reviewer pass** — a cheap sonnet agent answers six
  questions and writes a grade plus its three best refactors into the ledger:
  is a repeated kind living without a class? was the new thing added by
  copying? is config sitting in code instead of a registry? does a layer do
  another layer's job? is a file standing at the wall? were tests changed to
  make them pass? Below 8, the feature is not done. · reviewer.

## Definition of done

Matrix complete with fresh evidence, guards green (`run_guards` FULL), docs
updated, ledger tasks `[x]` with `!` lines (or honest `[~]`), open items named
FIRST in the final message. The build is not mentioned unless he asked for it
(`BUILD.md`).
