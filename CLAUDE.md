# CLAUDE.md — UVuruna Constitution

Universal law for **ALL projects** in this monorepo. Deliberately SHORT: the
detailed rulebooks live in `rules/` and are read **per job type** via the
[Router](#router) — an agent loads only what its job needs.

**Project `CLAUDE.md` files inherit from this** and may only ADD or TIGHTEN
rules — never loosen them.

---

## Organization

UVuruna is a personal development organization. All projects live in this
monorepo, organized by category:

```
📁 UVuruna/
  📁 Applications/     ← Desktop and automation applications
  📁 Gadgets/          ← Small utilities and tools
  📁 Games/            ← Games and experiments
  📁 Machine Learning/ ← ML projects (behavior capture and replication)
  📁 WebSites/         ← Web projects
  📁 logos/            ← Project logos (SVG), one per project
  📁 rules/            ← Rulebooks per job type (see Router)
  📝 CLAUDE.md         ← This file — the constitution
  📝 README.md         ← GitHub profile landing page (repo UVuruna/UVuruna)
  📝 PROJECTS.md       ← Detailed project index
  📝 DESIGN.md         ← Universal UI design system (stack-agnostic language + per-stack recipes)
  📝 MIGRATE-DOCS.md   ← Task brief: bring an existing project onto MD-First 2.0 + enforcement
  📝 REFACTOR-GODFILES.md ← Task brief: god-file split procedure
  📝 MIGRATE-GUI.md    ← Task brief: GUI responsiveness verification + front migration (4 phases)
  📝 PRIVATE.md        ← LOCAL-ONLY index of hidden projects (never tracked)
  ⚙️ company.json      ← Company/developer info (shared by all build pipelines)
```

- **Maximum 2 levels: `Category/Project/`.** One grouping-level exception may
  exist for a multi-module platform — currently unused.
- **Each project has its own git repository** — the root repo tracks ONLY root
  documentation, `rules/` and `logos/` (enforced by the `.gitignore` whitelist).

<a id="project-visibility"></a>

## Project Visibility

| Level | Code on GitHub | Description in public docs | Listed in README/PROJECTS |
|-------|----------------|----------------------------|---------------------------|
| **Public** | Public repo | Yes | Yes |
| **Private** | Private repo / none | Yes (description only) | Yes |
| **Hidden** | Never | Never | No — ONLY in local `PRIVATE.md` |

**Hidden projects must never appear in any tracked file** — no name, no path,
no logo. `PRIVATE.md` stays untracked.

---

## Priorities

When goals conflict, higher wins:

- **S. STRUCTURE** — supreme (owner decree 2026-07-29). Code lands in the module
  whose responsibility it serves, or a new module is born. See THE STRUCTURE
  LAW in [Code Rules](rules/CODE.md).
- **A. Performance** — absolute on hot paths; off them, never at clarity's cost.
- **B. Readability** — everything not hot is written for the reader first.
- **C. Inheritance over duplication** — never write the same function twice.
- **D. Logging** — scaled to the project; every app has SOME error visibility.

---

## The Laws

Mechanically enforced — violating one fails a build or blocks a session's end.
Every project carries **four guard tests + Claude Code hooks**
(spec: [Code Rules](rules/CODE.md) → Enforcement).

1. **THE STRUCTURE LAW** — placement by responsibility; >~1,000-line files fail
   the guard unless ratcheted → [Code Rules](rules/CODE.md)
2. **THE CONFIG SECTION LAW** — defined once, whole, in its section; no
   post-definition patching → [Code Rules](rules/CODE.md)
3. **THE DOCS LAW** — MD-First 2.0 coverage + unbroken navigation chain from
   README → [Docs Rules](rules/DOCS.md)
4. **THE RELEASE LAW** — successful build of an installable app ⇒ automatic GIT
   RELEASE, standing authorization, never ask → [Ship Rules](rules/SHIP.md)
5. **FIXED = VERIFIED** (owner decree 2026-07-26) — a session ends in exactly
   one honest state: **FIXED** (root cause named + fix + regression test +
   evidence), **CANNOT FIX HERE** (concrete why + what would unblock), or
   **IMPOSSIBLE** (technical reason). Never "solved" for a symptom patch; a
   problem that returns proves the previous diagnosis wrong — record root cause
   in the component's docs and session memory.

<a id="router"></a>

## Router — read ONLY what your job needs

| Your job this session | Read |
|-----------------------|------|
| Start a new project | [Start Rules](rules/START.md) + [Docs Rules](rules/DOCS.md) |
| Brainstorm / plan with the owner | [Plan Rules](rules/PLAN.md) |
| Implement features / fix bugs | [Code Rules](rules/CODE.md) + the folder's `___folder.md` |
| Any GUI work | [GUI Rules](rules/GUI.md) + [DESIGN.md](DESIGN.md) |
| Write documentation | [Docs Rules](rules/DOCS.md) |
| Migrate an existing project onto this system | [MIGRATE-DOCS.md](MIGRATE-DOCS.md) + [Docs Rules](rules/DOCS.md) |
| Build / release an installable | [Ship Rules](rules/SHIP.md) |
| Split a god-file | [REFACTOR-GODFILES.md](REFACTOR-GODFILES.md) |
| Verify / migrate a GUI's responsiveness | [MIGRATE-GUI.md](MIGRATE-GUI.md) + [GUI Rules](rules/GUI.md) |

---

## Universal Conduct (every session, every job)

- **Language:** Serbian (Latin) with the owner; English in all code, comments,
  docs and commit messages.
- **Session start:** read the project's `UV/` folder — the owner's gitignored
  inbox of instructions (treat as product decisions; never edit or delete his
  files) — and the relevant `___folder.md` docs.
- **Ask before assuming.** Identify ambiguities and ask; propose the approach;
  start after confirmation. Better 100 questions than 1 bug. Constructive
  disagreement is a duty ([Plan Rules](rules/PLAN.md)).
- **Communication (owner decree 2026-08-02):** every question to the owner is a
  fully explained block (context + why + options with consequences +
  recommendation) — never enumerated one-liners. Every algorithm / GUI /
  config-structure presentation carries an OBLIGATORY visual: box-drawing
  sketch in chat for simple, rendered page (Artifact/HTML) for complex —
  Mermaid source never in chat. Enforced by a machine-wide hook
  ([Plan Rules](rules/PLAN.md) → Communication).
- **Present before building:** implementation starts only after the envisioned
  algorithm / GUI sketch (or echo-brief for Wide tasks) has been shown —
  scaled by triage class, automatically ([Plan Rules](rules/PLAN.md)).
- **Token economy (owner decree 2026-07-26 — HARD weekly cap):** triage FIRST,
  in one written line — **Trivial** (inline, zero agents; most bug reports) /
  **Standard** (inline + at most a few agents for genuinely parallel pieces) /
  **Wide** (agents/workflow, sized to what was asked). Never exceed the stated
  class without saying so and getting a yes. Bugs: fix first with the cheapest
  probe, investigate after. Every delegated task gets the WEAKEST model tier
  that can do it (haiku → mechanical; sonnet → standard; opus → genuinely hard;
  session model NEVER for routine subagent work) and a structured deliverable
  with exact files. Multi-agent workflows ONLY on the owner's explicit request.
  Reuse (resume, read existing research) instead of rerun.
- **Honesty:** no capacity lies — an honest "I can't" beats a fake "I did".
  Verify before claiming: concrete evidence (files, lines, output) for any
  claim of completed work. No error masking — see [Code Rules](rules/CODE.md).
- **Scope:** only what was asked. Unrequested fixes/features noticed along the
  way are PROPOSED at the end, never implemented uninvited.
- **Files:** no version-suffix files (`_v2`, `_new`, `_backup`) — Git is the
  history. Ask before deleting anything you are not certain is obsolete.
- **After the work:** update the docs of everything you changed (Living Docs
  Rule — [Docs Rules](rules/DOCS.md)), commit per the system below, and for
  installable apps BUILD + GIT RELEASE automatically ([Ship Rules](rules/SHIP.md)).

---

## Version & Commit System

Format: **`0.0.000 description`** — `MAJOR.MINOR.PATCH`, PATCH zero-padded to 3
digits; short English phrase; em dash `—` for extra detail.

| Scenario | Increment |
|----------|-----------|
| Same session, related work | +1 per commit (`1.0.500 → 1.0.501`) |
| Unrelated / independent work | next round number (`1.0.508 → 1.0.510`) |

Procedure: `git log --oneline -5` for the latest version → group changes into
logical commits by topic/module → stage specific files (**never** `git add .`)
→ commit with the next number. Complex work = multiple commits, +1 each.

---

## Enforcement Note

Rules held only when a check enforced them — that is this monorepo's proven
history. The teeth: the four guard tests + PostToolUse/Stop hooks in every
project ([Code Rules](rules/CODE.md) → Enforcement). New projects are born with
them ([Start Rules](rules/START.md) → Scaffold); existing projects receive them
via [MIGRATE-DOCS.md](MIGRATE-DOCS.md). A new rule enters the books only with
its class declared: LAW, GATE or STYLE ([Plan Rules](rules/PLAN.md)).
