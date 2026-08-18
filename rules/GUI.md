# GUI — category rules

Read with `CODE.md` and `DESIGN.md`. A changed GUI element starts with a sketch
shown to him (`PLAN.md`). These checks run ONLY when a GUI file was touched
(`rules/hooks/changed_files.py`; "cannot tell" means RUN them).

## Logic before looks

Complete functionality on a MINIMAL GUI first; the visual pass follows once the
logic is feature-complete. Polish asked for earlier → WARN him (Guardrail #1),
proceed only after he confirms. · reviewer.

## Space & Legibility

Nothing he must read is cut off, nothing starves while its window holds empty
space. An element that does not fit is fixed IN THIS ORDER, a later step legal
only when the earlier are exhausted:

1. **Take the free space** — content outranks spacer, filler, stretch.
2. **Reflow** — wrap, break the row, second column, neighbours give up slack.
3. **Raise the window minimum.**
4. **Scroll** — last, only when the window is genuinely full in that axis.

**Never:** ellipsis or truncation on content he must read · clipped elements ·
fixed height/width on a text-bearing widget · a neighbour holding slack beside a
starving element · a scrollbar with unused space in the window.

**Every window declares a minimum** derived from measured content (longest real
string, tallest real row). **There is no fixed screen floor** (owner decree
2026-08-18) — a window is judged on the device profiles it is shot on: nothing
clipped or starving there; what is genuinely taller than the screen scrolls
(ladder step 4); the runner reports the minimum as information, not a verdict.

· `gate.py pre` (banned clipping/eliding/hard-size APIs, escape
`layout-ok: <reason>`), `run_guards` (`test_layout_law.py`,
`test_layout_audit.py`), the tooth below · history →
`history/space-legibility-law.md`. Device floor: the project's `profiles:`
(`rules/devices.json`), one never `pc-owner`.

## The GUI tooth (`gate.py stop`)

For every GUI file the session edited:

1. **Two shots per touched window, on two DIFFERENT profiles** — the declared
   minimum and an average one (usually `pc-low` + `laptop-avg`), never
   `pc-owner`. `uv shot --window <Name> --profile <p>` (or `--all`) writes the
   PNG, runs the ALG checks, appends the `ev-` row.
2. **The agent OPENS each PNG with Read** — a claim about a picture nobody
   looked at is a lie.
3. **A grade ≥ 8 per shot in the ledger**, from this checklist, each item
   PASS/VIOLATION with where in the shot: (1) nothing clipped or elided · (2) no
   scrollbar beside unused space · (3) contrast ≥ 4.5:1 (3:1 large), hover
   included · (4) same-kind siblings share dimensions (±2 px) · (5) no band half
   empty while content stacks below · (6) radius in PERCENT, ≤ 30 % of the
   shorter side when squarish, inset ≥ 0.3·r · (7) controls sit in the section
   their concept names · (8) would a layman accept this, what would he notice
   first (in sentences). `grade = 10 − Σ deductions` (LAW −3, GATE −2, STYLE
   −1), any LAW violation caps it at 5. Below 8: fix, re-shoot, re-grade.
4. **Evidence newer than the last GUI edit** — the gate compares timestamps.
5. **Standard/Wide: an INDEPENDENT grader** — a sonnet sub-agent given ONLY the
   shots and the checklist (never the code, never the implementer's claims),
   grading blind and whole-frame; Trivial GUI grades itself. History →
   `history/visual-proof.md`, `history/zubi-v2.md` (ALG-1..9 are code now, in
   the runner and the layout-check templates).

Shots live in TOPIC folders under `.claude/evidence/<session>/`; a message with
images links the folder AND each image, as monorepo-root paths that exist.

## Silent audits

No window an audit or agent builds ever reaches his screen or takes focus: Qt
`WA_DontShowOnScreen` before `show()` (or offscreen platform) · Tk `withdraw()`
+ `alpha 0` before the first `update()` · WPF `RenderTargetBitmap`, never
`Show()` · history → `history/silent-audits.md`.

## Modern UI and responsiveness

- A gray, default-widget interface is a bug at the visual pass: palette,
  radius, breathing room, depth, SVG icons. Read `DESIGN.md` first. · reviewer.
- The UI thread renders and takes input, nothing else — workers are separate
  PROCESSES (Python: never threads for CPU work); updates arrive BATCHED
  10–30×/s, never per event; long lists virtualize. · `uv run` timing.
- Effects are GPU-composited or they do not ship — banned: Qt
  `QGraphicsDropShadowEffect`, `WA_TranslucentBackground` hacks, per-tick
  layout mutation. · guard test.
- New GUI stack: `START.md` → Technology Selection (C# + WPF front by default,
  Python only as IPC workers) · history → `history/gui-tech-policy.md` · briefs:
  `briefs/MIGRATE-GUI.md`, `briefs/MIGRATE-LAYOUT.md`.
- i18n: develop in ENGLISH; the Serbian bundle lands in one session before a
  build. · reviewer.
- Stories → `history/gui-laws.md`.
