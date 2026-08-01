# PLAN — Brainstorming & Planning Rules

**Who reads this:** sessions that think WITH the owner — brainstorming, idea
shaping, direction choices, implementation planning. (Init/context-gathering
sessions too — see Read-Only on Init.)

## Table of Contents

- [Plans Are Discussions](#plans)
- [Constructive Disagreement](#disagreement)
- [Read-Only on Init](#init)
- [Rule Classes — Law / Gate / Style](#rule-classes)
- [Owner Guardrails](#guardrails)

---

<a id="plans"></a>

## Plans Are Discussions

- A plan explains WHAT will be done and WHICH files change — it is
  brainstorming, not a code preview
- Do NOT write full code blocks in plans that will later be copied into files
- Before starting any work: read the task carefully, identify ambiguities, read
  the relevant docs (`___folder.md`, `__about/`), ASK about everything unclear
  ("Should I modify X or create new?", "You said Y — did you mean Z?"), propose
  the approach, and START ONLY AFTER CONFIRMATION

---

<a id="disagreement"></a>

## Constructive Disagreement

If a proposed approach is suboptimal, the agent MUST: (1) explain WHY with
concrete technical reasons, (2) propose an alternative, (3) ask for confirmation
after the trade-offs are understood. Blind acceptance is a defect:

```
❌ Owner: "Let's read the TOP 50 twice"  → Agent: "OK."
✅ Agent: "I see a problem: the list already contains all the data — reading it
   twice wastes resources. Proposal: read once. Agreed?"
```

Better a short pause for discussion than an inefficient build that must be
undone.

---

<a id="init"></a>

## Read-Only on Init

When a session starts in a project to gather context: READ the docs
(`CLAUDE.md`, `README.md`, relevant `___folder.md`) — do NOT propose
improvements, additions or modifications unprompted. Init is context gathering,
not a review.

---

<a id="rule-classes"></a>

## Rule Classes — Law / Gate / Style

Written rules that nothing enforces do not hold (proven repeatedly in this
monorepo). When the owner proposes a NEW rule, the planning agent asks:
**"What check guards it?"** and classifies it:

| Class | Meaning | Home |
|-------|---------|------|
| **LAW** | a guard test / hook fails the build or session on violation | guard tests + hooks ([CODE](CODE.md) → Enforcement) |
| **GATE** | checked at end of work (Stop hook, checklist, Definition of Done) | task briefs, hooks |
| **STYLE** | advisory; kept to ONE sentence | rules files |

A rule that cannot become a LAW or GATE is written as a single STYLE sentence —
or not at all.

---

<a id="guardrails"></a>

## Owner Guardrails (living list — owner decree 2026-08-01)

The owner explicitly asks to be PROTECTED from his own known mistakes. When a
planning session sees one of these patterns, it is the agent's DUTY to warn —
clearly, before work starts. Warning is not disobedience; silence is.

1. **GUI before functionality.** Visual polish requested before the logic is
   feature-complete → point to the Logic-Before-Looks law ([GUI](GUI.md)) and
   propose finishing functionality on the minimal GUI first.
2. **New project before the duplication check.** Founding a project without
   first checking whether an equivalent already exists — in the monorepo or as
   available software ([START](START.md) → Step 1).
3. **New project before the feasibility check.** Entering a build without
   naming the hard part and how it will be handled; when feasibility is
   unknown, the first milestone is a throwaway probe ([START](START.md) → Step 1).
4. **Tech insistence against engineering reality.** When the owner insists on a
   technology that is infeasible or clearly inferior for the task, the agent
   must lay out the technical reality and alternatives — NEVER silently accept.
   (Constructive Disagreement, escalated: here the agent warns even without
   being asked for an opinion.)
5. **Vocabulary mix-ups.** The owner's wording is sometimes imprecise; if a
   request contains an apparent illogic or contradiction, assume a possible
   word mix-up and ASK — "did you mean X?" — before acting on the literal
   reading.
6. **Generating what can be computed.** An asset request that skips the
   derivation check ([CODE](CODE.md) → Compute, Don't Generate).
7. **Rules without teeth.** A new rule proposed with no enforcement — apply
   [Rule Classes](#rule-classes).

The owner adds new guardrails as he identifies them; sessions may PROPOSE
candidates (at the end of work, never mid-task).
