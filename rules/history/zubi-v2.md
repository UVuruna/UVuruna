# Zubi v2 — ALG-1..9 and Grader v2, the story

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

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
the owner's go ([MIGRATE-LAYOUT](../briefs/MIGRATE-LAYOUT.md)). Gaps that STAY on
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
that show him images link the FOLDER and EACH IMAGE — as paths relative to
the monorepo root, verified to exist, so his click actually opens them, per
[PLAN → Communication](../PLAN.md#communication). Loose images in the shots
root block the session. — **GATE**, `rules/hooks/layout_guard.py` (Stop,
machine-wide).

---

