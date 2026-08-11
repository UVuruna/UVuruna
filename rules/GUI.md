# GUI — Interface Rules

**Who reads this:** every session doing ANY GUI work — new interface, redesign,
visual polish, theming, i18n.
A new or changed GUI element starts with a layout sketch shown to the owner —
[Present Before Building](PLAN.md#present).

## Table of Contents

- [Law — Logic Before Looks](#logic-first)
- [Law — Space & Legibility](#space)
- [The Visual Proof](#visual-proof)
- [Zubi v2 — Algorithmic Teeth & Grader v2](#zubi-v2)
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
CLAUDE.md](../CLAUDE.md) Law #5), no different from an inflated grade.

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

<a id="zubi-v2"></a>

## Zubi v2 — Algorithmic Teeth & Grader v2 (owner decrees 2026-08-08)

Born from thirteen screenshots of DOMY Watch that shipped with 9/10 grades
while any layman would have rejected them. Four mechanisms let them through,
and each one now has a named answer here: the audit measured only DEFAULT
state (extremes and the owner's real profile were never visited); an audit
FAILING against the owner's live settings was written off in a proof file as
"the environment, not this change"; hover popups were invisible to the
widget-tree walk; and the grade was a free number given in a narrow frame.

### The algorithmic teeth — no AI in the loop

Measured by plain code. STATUS 2026-08-08: the Qt library
`rules/templates/layout_checks_qt.py` (+ thin entry `test_layout_audit_qt.py`
— split so adopting projects do not trip THE STRUCTURE LAW) implements
ALG-1..9 and is fixture-verified: 13/13 planted violations caught, each by
its own check, clean window passing. The WPF `LayoutAuditTests.cs` mirrors
it with identical rule-name messages but is **UNCOMPILED** (no dotnet on the
dev machine) — the first WPF rollout MUST compile-verify it and see it fail
on a deliberately broken window before trusting a green run. First Qt
rollout: DOMY Watch — the first audit run found **1667 violations across 7
windows** (recorded in its `.claude/zubi-v2-findings.md`, deliberately
unfixed per the owner's install-only boundary). Remaining projects adopt on
the owner's go ([MIGRATE-LAYOUT](../MIGRATE-LAYOUT.md)). Gaps that STAY on
the grader's checklist, documented in-file: ALG-6's content-inset ≥ 0.3·r
and ALG-2's hover/pressed contrast states.

| # | Rule | Class | Teeth |
|---|------|-------|-------|
| ALG-1 | **EXTREME STATE MATRIX** — every numeric control the session touched is audited at min / default / max, every toggle and small enum through all options; after each change: nothing paints outside the window, concentric elements share a center, the scroll rules hold. "Tested" without extremes is not tested. | LAW | template v2 — live |
| ALG-2 | **CONTRAST** — text vs its REAL background ≥ 4.5:1 (3:1 for large text), sampled from screenshots; hover and tooltip states included. | LAW | template v2 — live |
| ALG-3 | **HOVER GEOMETRY** — the audit triggers every tooltip/hover it finds; hover text wraps at ≤ 72 chars per line, never renders wider than its window, never off-screen. | LAW | template v2 — live |
| ALG-4 | **SPACE CEILING** — measured in LOGICAL px (the units layouts actually use). The ladder: **~1000×1000 ideal** (1:1 is a STYLE recommendation for canvases and presentational wholes, not for forms) → **1600 working width** for desktop settings pages → **2560×1440 ABSOLUTE ceiling, no exception, no written excuse** (that is a fullscreen demand). Each step up is legal only when the previous one is exhausted by reflow AND a reason is written down. Phone-targeted UI is designed portrait-first at device logical width (~360–480) — and every target follows the COMMON hardware of real users, never the best available. Horizontal scroll on a settings page fails at every step. | LAW | template v2 — live |
| ALG-5 | **UNIFORM SIBLINGS** — same-kind elements in one container share dimensions (the widest content decides, tolerance ±2px); a control's size never depends on the length of its own text. | GATE | template v2 — live |
| ALG-6 | **RADIUS BY ASPECT RATIO** — always in PERCENT of the element's own size, never absolute px (owner decree 2026-08-11: *"ako pričamo u px to ne može nego u %"* — lang-ok: owner quote). AR = width/height. AR ≥ 2: radius up to 50% of height (a pill is legitimate on a wide element); 1.4 ≤ AR < 2: ≤ 30% of height; AR < 1.4 (squarish/portrait — where circles and eggs are born): ≤ **30%** of the shorter side. The squarish tier was ≤ 15% until 2026-08-11, when the owner judged the two side-by-side at real size and kept his standing 58px/16px (27.6%) buttons: *"promeni pravilo onda ako ne dozvoljava ovo — to je greška"* (lang-ok: owner quote) — a squircle is deliberate design; the CIRCLE/EGG the law hunts begins past ~30%, and 50% IS the circle. ALWAYS: inner text/image inset ≥ 0.3·r from every edge — that is what a rounded corner geometrically eats. True-circle content (color swatch, avatar) is exempt. | LAW | template v2 — live |
| ALG-7 | **ROW OCCUPANCY** — at minimum width, a band whose right half stands empty while content stacks BELOW it fails: reflow into columns before stacking into height. The measurable form of "nothing starves beside empty space". | GATE | template v2 — live |
| ALG-8 | **LIVE PROFILE** — the audit ALSO runs against a read-only copy of the owner's real settings file, not only the pristine default (owner approval 2026-08-08). A failure there is a failure of this change's session to deal with. *"That is the environment, not this change"* is not a legal sentence in any proof file. | LAW | template v2 — live |
| ALG-9 | **SECTION TAXONOMY** — when a section named for a concept exists (Size, Colors, Opacity…), a control carrying that concept in its label outside that section fails, absent a written reason beside it. | GATE | template v2 — live |

### Grader v2 — the grade is computed, never felt

The owner's verdict, verbatim in spirit: an algorithm must not judge the
qualitative — but an agent must not judge WITHOUT A LEDGER.

1. **GRD-1 — the checklist is the grade.** The grader fills a checklist
   (every ALG rule above + this rulebook + DESIGN.md), each item PASS or
   VIOLATION with pixel evidence (where in the shot). Then:
   `grade = 10 − Σ deductions` (LAW violation −3, GATE −2, STYLE −1), and
   **any LAW violation caps the grade at 5**. A bare number with no
   checklist is not a grade. — **GATE**
2. **GRD-2 — the anchor gallery.** Local, NEVER in git (the rules and hooks
   are public; the owner's screenshots are not): `.claude/design-anchors/`
   holds shots of patterns the owner has REJECTED, each with his verdict in
   WORDS — an anchor is a violation pattern, not a number. A window
   repeating an anchor's pattern cannot grade ≥ 8 until the pattern is
   gone. An anchor RETIRES the day its failure becomes an ALG check — the
   algorithm carries it from then on; and the agent warns the owner when
   the gallery exceeds ~100 MB or an anchor outlives its rule. Nothing is
   hoarded. — **GATE**
3. **GRD-3 — blind first, whole frame always.** The grader writes what it
   sees and would deduct BEFORE reading the implementer's claims. The whole
   window is always graded; a narrow ruling is an additional item, never
   the only one — that exact narrowing is how four honest 9s coexisted
   with an unacceptable window. — **GATE**
4. **GRD-4 — states in frame.** Full-window shots at min / default / max
   control states plus hover states; crops and zooms stay banned (Visual
   Proof above). — **GATE**
5. **GRD-5 — the layman question.** Every checklist ends with, answered in
   sentences, never a number: *"Would someone with no design background
   accept this? What would they notice first?"* A grade ≥ 8 written above
   VIOLATION items is a capacity lie (root CLAUDE.md → Universal
   Conduct). — **GATE**

### Screenshots live in TOPIC folders

`.claude/shots/<topic>/` — the folder name says what was being worked on
(`decision-dark-theme/`, `hover-contrast-fix/`), so the owner opens one
folder and sees one story, never a dump of sixty cryptic names. Messages
that show him images link the FOLDER and EACH IMAGE (clickable), per
[PLAN → Communication](PLAN.md#communication). Loose images in the shots
root block the session. — **GATE**, `rules/hooks/layout_guard.py` (Stop,
machine-wide).

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
