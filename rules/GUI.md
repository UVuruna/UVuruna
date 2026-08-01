# GUI — Interface Rules

**Who reads this:** every session doing ANY GUI work — new interface, redesign,
visual polish, theming, i18n.
A new or changed GUI element starts with a layout sketch shown to the owner —
[Present Before Building](PLAN.md#present).

## Table of Contents

- [Law — Logic Before Looks](#logic-first)
- [Modern UI — No Old-Fashioned Interfaces](#modern-ui)
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

<a id="stack"></a>

## Stack Choice for GUIs

The design LANGUAGE in DESIGN.md (dark-first, tokens, soft depth, typography)
is **stack-agnostic** — it does not mandate any library. The GUI stack is chosen
per project ([START](START.md) → Technology Selection) by what best delivers
**responsiveness and a modern visual impression** for that application — never
by habit. DESIGN.md carries recipes for stacks already in use (Qt, web); a new
stack gets its recipe section on first use.

---

<a id="translation"></a>

## Translation Policy — English During Development

For projects with user-facing i18n: development is **English-only**. Texts
churn — translating unfinished text is write-then-delete waste.

- Sessions write ENGLISH ONLY; new UI keys may ship untranslated (English is
  the documented fallback)
- The Serbian bundle reaches full coverage in ONE dedicated TRANSLATION session
  immediately before a build/release
