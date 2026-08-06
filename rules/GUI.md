# GUI — Interface Rules

**Who reads this:** every session doing ANY GUI work — new interface, redesign,
visual polish, theming, i18n.
A new or changed GUI element starts with a layout sketch shown to the owner —
[Present Before Building](PLAN.md#present).

## Table of Contents

- [Law — Logic Before Looks](#logic-first)
- [Law — Space & Legibility](#space)
- [Modern UI — No Old-Fashioned Interfaces](#modern-ui)
- [Law — Responsiveness](#responsiveness)
- [Stack Choice for GUIs](#stack)
- [Translation Policy](#translation)

---

<a id="logic-first"></a>

## LAW — Logic Before Looks (owner decree 2026-08-01)

**Complete functionality on a MINIMAL GUI first; the visual pass comes after the
logic is feature-complete.**

The failure this kills: polishing elements visually, adjusting, re-adjusting —
then the design changes with the next feature and the polish is deleted. Order
of work in every GUI project:

1. Minimal necessary GUI (default-ish widgets are FINE at this stage) + the
   COMPLETE logic and every planned functionality
2. Only then: the visual pass — theme, effects, assets, per DESIGN.md

**Agent duty:** when the owner requests visual polish before the logic is
feature-complete, the agent MUST flag it (this is Owner Guardrail #1 — see
[PLAN](PLAN.md)) — and proceed only if the owner confirms after the warning.

---

<a id="space"></a>

## LAW — Space & Legibility (owner decree 2026-08-05)

**Nothing the user must read may be cut off, and no element may starve while
its window has empty space.** These are the two failures the owner has had to
report by hand in project after project:

```
BUG A — element scrolls, window empty          BUG B — content clipped / elided
┌──────────────────────────────────┐           ┌──────────────────────────────────┐
│ ┌──────────────┐▲                │           │ Left   │Shortcut ▾│Prev│ ift+tab │
│ │ esc          │█                │           │ Right  │Shortcut ▾│Next│ tab     │
│ │ Prev         │█ ← SCROLLBAR    │           │ Bottom │Shortcut ▾│Find│ ctrl+f  │
│ │ Next         │▼                │           └──────────────────────────────────┘
│ └──────────────┘                 │              "shift+tab" rendered "ift+tab"
│                                  │              "e.g. ctrl+shift+p" → "e.g. ..."
│         E M P T Y                │              …while the column to the left
│         (300+ px unused)         │                had slack to give up
└──────────────────────────────────┘
```

Both have one cause: **space was distributed by how the layout happened to be
written, instead of by who needs it.** This law fixes the distribution order.

### The resolution ladder — an element that does not fit is fixed IN THIS ORDER

A later step is legal ONLY when every earlier step is exhausted:

1. **TAKE THE FREE SPACE.** The starving element grows into the window's unused
   space. Stretch/`Grid` star-sizing belongs to content that needs it; a spacer,
   a filler or a trailing stretch NEVER outranks content that does not fit.
2. **REFLOW.** No free space left → wrap the text, break the row into several
   rows, move to a second column, let neighbours with slack give their slack up
   first.
3. **RAISE THE WINDOW MINIMUM.** Still does not fit → the window's minimum size
   is too small; raise it, and the window can no longer be shrunk below it.
4. **SCROLL — last.** A scrollbar is legal ONLY when the window is genuinely
   full in that axis. **A visible scrollbar with unused space in the same window
   is a bug**, not a style choice.

### Never, in any situation

- **Ellipsis or truncation on content the user must read** — a shortcut, a name,
  a value, a path. An unreadable control is worse than a bigger window.
- **Clipped elements** — half a character, a cut-off edge. If it renders, it
  renders whole.
- **Fixed height/width on a widget that carries text**, and any hard size that
  makes step 1 impossible.
- **A neighbour holding slack next to a starving element.**

### Every window declares a minimum size, and it FITS THE SCREEN FLOOR

The minimum is the size at which the fullest state of the window still satisfies
everything above — derived from measured content (longest real string, tallest
real row), never guessed at a round number.

**And it must fit inside 1280×720.** A window whose minimum exceeds the screen
floor demands a monitor the user does not have — a two-item menu that computes
a 6,000 px minimum is not a minimum, it is a bug in step 1 or 2 of the ladder.
**The answer to a minimum that does not fit is REFLOW, never widen.** A project
that genuinely needs a bigger floor declares it in `.claude/layout-frame.json`
with a written reason; without the reason the override does not count.

### DESIGN REVIEW — the agent looks at its own GUI and grades it

**Every window an agent touches is screenshotted, OPENED, and graded 1–10
against [DESIGN.md](../DESIGN.md). Below 8/10 nothing ships.** An agent can see
a picture exactly as the owner can — crowding, misalignment, holes of empty
space, cut text, ugly defaults. Having the owner point at a screenshot and say
"this is a 2 out of 5" is a failure of the session, not a feature of review.

1. The audit test writes the screenshot at the window's minimum size
   (`.claude/shots/<Window>.png`) — captured, not staged.
2. The agent **opens the image with the Read tool** (which renders it) and
   grades what it actually sees.
3. Grade and screenshot go into `.claude/layout-proof.md`; the Stop hook
   verifies the file exists, that the agent really opened it in this session,
   and that no grade is below 8.
4. **A grade is honest or it is a capacity lie** ([CLAUDE.md](../CLAUDE.md) →
   Universal Conduct). A 9 written under a 2/10 screenshot is the worst defect
   in this rulebook: it defeats every other check by hand. Below 8 the answer is
   to fix the GUI, re-shoot, re-grade — never to raise the number.

### Classes and teeth

| # | Rule | Class | Guarded by |
|---|------|-------|-----------|
| 1 | No banned clipping/eliding/hard-size API in GUI sources | **LAW** | `rules/hooks/layout_guard.py` (PreToolUse, machine-wide) + `tests/test_layout_law.py` (per project) |
| 2 | No clipping, no elision, no scroll-with-free-space at runtime | **LAW** | `tests/test_layout_audit.py` — instantiates every window offscreen at its declared minimum and larger, walks the widget tree ([MIGRATE-LAYOUT.md](../MIGRATE-LAYOUT.md)) |
| 3 | Every window's minimum fits the 1280×720 screen floor | **LAW** | the audit test refuses an absurd minimum; the Stop hook re-checks every `MIN` in the proof |
| 4 | DESIGN REVIEW — screenshot opened and graded ≥ 8/10 | **LAW** | `rules/hooks/layout_guard.py` (Stop): the shot must exist, must have been READ this session, and no grade may be below 8 |
| 5 | A session that touched a GUI file ships layout proof | **GATE** | `rules/hooks/layout_guard.py` (Stop, machine-wide) — `.claude/layout-proof.md` for the current session |
| 6 | The ladder order itself (free space → reflow → minimum → scroll) | **GATE** | Definition of Done of every GUI task; the audit catches its visible consequences |

The proof line the hook parses, one per window:

```
SESSION: <session id>
- SetsDialog (gui/sets_dialog.py) - MIN 980x720 - SHOT .claude/shots/sets_dialog.png - GRADE 9/10 - audit: PASS
```

What the teeth still cannot bite: whether a grade was given honestly. Everything
else in that line is verified — the file exists, the image was opened, the
number is above the bar, the minimum fits the screen. The grade itself rests on
the same rule as every other claim of finished work: **FIXED = VERIFIED**, and
inflating it to end a session is a capacity lie, the one defect that defeats all
the others.

---

<a id="silent-audits"></a>

## LAW — Silent Audits (owner decree 2026-08-06)

**No window an audit, guard run or agent builds may ever reach the owner's
screen or take his focus.** Born live, the same day the design-review teeth
landed: an audit's factories called `show()` before `WA_DontShowOnScreen`,
so every guard run flashed the real main window across the owner's desktop
and broke his typing mid-sentence, repeatedly, while background agents ran.

- **Qt:** `setAttribute(WA_DontShowOnScreen, True)` BEFORE every `show()` —
  including shows inside window factories — or the offscreen platform.
- **Tk:** `withdraw()` / off-screen geometry AND `attributes("-alpha", 0)`
  before the first `update()`; every `Toplevel` pinned the instant it is born.
- **WPF:** render to `RenderTargetBitmap`, never `Show()`.

Class: **LAW** — `rules/hooks/layout_guard.py` (PreToolUse, machine-wide)
refuses to write any `test_layout_audit*` file that builds windows without a
silencing mechanism. The order of calls inside stays on session discipline —
the hook catches the missing mechanism, the reviewer catches the wrong order.

---

<a id="modern-ui"></a>

## Modern UI — No Old-Fashioned Interfaces

**Every GUI we ship must look MODERN. A gray, blocky, default-widget interface
is a bug** — at the visual-pass stage. Required visual language: a real palette
with accents and gradients (dark-first where it fits), rounded corners and
breathing room, glow/shadow/layering depth, SVG icons (emoji where they help),
charts and styled tables wherever there is data.

Procedure for the visual pass (or any redesign):

1. **Read [DESIGN.md](../DESIGN.md) FIRST** — the universal design system
   (palette, effects, per-stack recipes). It exists so we do NOT re-research
   the internet per project.
2. **Only if DESIGN.md does not cover the stack or has gone stale** (Last
   researched > 1 year) — launch a web-research agent (cheapest capable tier),
   then FOLD the findings back into DESIGN.md, including a recipe section for
   the new stack.
3. Projects may define their own theme ON TOP of DESIGN.md — the baseline
   quality bar is non-negotiable.

---

<a id="responsiveness"></a>

## LAW — Responsiveness (owner decree 2026-08-04)

**Modern looks and responsiveness are NOT a trade-off — we keep BOTH.** Games
composite full 3D scenes at hundreds of frames per second; a desktop GUI with
tables and panels is trivial work for a GPU. When our GUIs lag on resize, move,
or in-window changes (expand/collapse, state switches), the cause is TECHNIQUE
— never "too much beauty". Binding rules for every GUI, in every stack:

1. **The UI thread renders and takes input — nothing else.** No OCR, no browser
   automation, no long queries, no file I/O. Workers run in separate
   **processes** (in Python specifically: never threads for CPU-bound work —
   the GIL stalls the event loop even though Qt itself renders in C++).
2. **Updates arrive batched, never per-event.** An aggregator groups worker
   output and delivers it to the GUI 10–30 times per second (every 33–100 ms).
   The user perceives it as instant; the event queue stays empty. The
   aggregator's message format doubles as the IPC contract if the front ever
   migrates ([MIGRATE-GUI.md](../MIGRATE-GUI.md)).
3. **Effects are GPU-composited or they do not ship.** The banned list
   (guard-greppable per stack; GPU replacements live in
   [DESIGN.md](../DESIGN.md)):
   - Qt: `QGraphicsDropShadowEffect` (CPU-rendered blur),
     `WA_TranslucentBackground` and frameless-window hacks that take move/resize
     away from DWM
   - any stack: per-tick layout mutation from code where a compositor animation
     exists (WPF animations, CSS `transform`/`opacity`)
4. **Large lists and tables are virtualized** — render the visible rows, never
   the dataset.

Classes: rule 3 is **LAW** — a banned-API guard test greps the project's stack
list; rules 1, 2 and 4 are **GATE** — Definition-of-Done items for every GUI
task.

---

<a id="stack"></a>

## Stack Choice for GUIs

The design LANGUAGE in DESIGN.md (dark-first, tokens, soft depth, typography)
is **stack-agnostic** — it does not mandate any library. For NEW projects the
stack comes from the default decision tree in [START](START.md) → Technology
Selection (C# + WPF front by default; Python only as worker processes behind
IPC) — departures need the written justification there. DESIGN.md carries
recipes for stacks already in use (Qt, web); a new stack gets its recipe
section on first use.

---

<a id="translation"></a>

## Translation Policy — English During Development

For projects with user-facing i18n: development is **English-only**. Texts
churn — translating unfinished text is write-then-delete waste.

- Sessions write ENGLISH ONLY; new UI keys may ship untranslated (English is
  the documented fallback)
- The Serbian bundle reaches full coverage in ONE dedicated TRANSLATION session
  immediately before a build/release
