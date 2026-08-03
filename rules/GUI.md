# GUI — Interface Rules

**Who reads this:** every session doing ANY GUI work — new interface, redesign,
visual polish, theming, i18n.
A new or changed GUI element starts with a layout sketch shown to the owner —
[Present Before Building](PLAN.md#present).

## Table of Contents

- [Law — Logic Before Looks](#logic-first)
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
