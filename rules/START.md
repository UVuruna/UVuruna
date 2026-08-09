# START — Starting a New Project

**Who reads this:** ONLY sessions that create a new project (or formally re-found an
existing one). Implementation, fix, GUI and docs sessions do NOT need this file —
see the Router in [CLAUDE.md](../CLAUDE.md).

A new project is founded in five steps, in this order. Every step produces a
WRITTEN artifact — nothing is "understood silently".

## Table of Contents

- [Step 1 — Feasibility & Duplication Gate](#gate)
- [Step 2 — Project Name](#name)
- [Step 3 — Technology Selection](#tech)
- [Step 4 — Scaffold](#scaffold)
- [Step 5 — Registration](#registration)
- [Appendix — UV Name Inspiration Tables](#uv-tables)

---

<a id="gate"></a>

## Step 1 — Feasibility & Duplication Gate

Before ANY other step, answer both questions in writing and show the owner
(these exist because skipping them is a known owner mistake — see
[PLAN](PLAN.md), Owner Guardrails #2 and #3):

1. **Does an equivalent already exist?** Check the monorepo ([PROJECTS.md](../PROJECTS.md),
   local `PRIVATE.md`) AND the outside world (an off-the-shelf tool that already
   does this). If yes: extending or adopting it beats founding a duplicate.
2. **Is it feasible?** Name the hard part (API access, OS capability, latency
   budget, legal constraint) and how it will be handled. If feasibility is
   unknown, the FIRST milestone of the project is a throwaway feasibility probe —
   not a GUI, not a scaffold.

Only after the owner accepts both answers does the project exist.

---

<a id="name"></a>

## Step 2 — Project Name

**Priority order (owner decree 2026-08-01):**

1. **Associative and memorable FIRST.** The name must evoke what the project
   does, be easy to remember, and sound good — "interesting to the ears".
   A plain descriptive name always beats a forced clever one.
2. **Initials are a BONUS, never a requirement.** If the name *naturally* lands
   on one of the house initial patterns, take the bonus:
   `UV`, `MUV`, `SUV`, `UVS`, `USV`, `VU`, `VUS`, `VSU`.
   If it doesn't — that is completely fine. Never bend a good name to fit
   initials.

Procedure: propose 3–5 candidates with one line each on the association it
carries; mark any that happen to hit an initials pattern; the owner picks.

The [appendix below](#uv-tables) holds UV word-pair tables — **inspiration only**.

---

<a id="tech"></a>

## Step 3 — Technology Selection

**This monorepo has NO house language** (owner decree; Python dominance is
historical, not normative). Every new project picks the stack most adequate for
its task. The choice is a DECISION WITH A PAPER TRAIL, never a habit.

**GUI default policy (owner decree 2026-08-04, class GATE — a Step-3 checklist
item).** Python is no longer a candidate for the GUI layer of new projects: its
GUI stacks repeatedly failed the responsiveness bar (resize / move / in-window
lag) that the owner requires ALONGSIDE a modern look — never instead of it
([GUI](GUI.md) → Responsiveness). Python remains first choice exactly where it
is strongest: automation, OCR, ML, scripting — as a backend worker, never as
the front. The decision tree:

| Project shape | First choice |
|---------------|--------------|
| No GUI — script / automation / ML | **Python** (still first choice) |
| CLI / background service, footprint matters | Go or Rust (single binary) |
| Desktop GUI, backend not Python-bound | **C# / .NET + WPF**, Fluent-themed per [DESIGN.md](../DESIGN.md) |
| Desktop GUI, backend needs the Python ecosystem (OCR / ML / Playwright) | **C# WPF front ◄─ IPC (JSON) ─► Python worker processes** — the front only renders and takes input; ALL work lives in workers; updates arrive batched ([GUI](GUI.md) → Responsiveness) |
| Cross-platform desktop genuinely required | **Avalonia** (C#, same split model) |
| Website | Static + vanilla JS; framework only when state demands it |
| Game | Engine (Godot, Unity) or web canvas |

Web-tech desktop fronts (Tauri / WebView2 / Electron) are chosen ONLY when the
owner explicitly demands a CSS/web design AND accepts, eyes open, their known
live-resize artifacts on Windows — the exact symptom this policy exists to kill.

Departures from the tree are possible — but only through the written
justification below. Answer in the project's `README.md` (or `CLAUDE.md`):
*"Which language/stack fits this task best, and why?"* — with **at least one
alternative considered and rejected for stated reasons**.

Criteria, in the order they usually decide:

1. **Performance profile** — hot paths, latency, memory footprint
2. **Ecosystem** — the libraries that actually solve the problem (OS hooks,
   ML, capture, rendering)
3. **Target platform** — Windows desktop, web, service, mobile, embedded
4. **Deployment** — single EXE, installer, browser, background daemon
5. **GUI responsiveness & modern feel** — for any project with a GUI, the stack
   must be able to deliver the [DESIGN.md](../DESIGN.md) quality bar with smooth,
   responsive rendering. "We already know X" is not an argument.

Language-specific recipes elsewhere in the rules (PyInstaller pipeline, py-spy,
`logging`) are **recipes for Python projects, not a mandate** — a non-Python
project defines its own equivalents following the same principles.

**Docs stay owner-readable:** `.md` files explain algorithms in language-neutral
pseudocode (see [DOCS](DOCS.md)) so the owner can follow logic in any stack.

---

<a id="scaffold"></a>

## Step 4 — Scaffold

**The teeth are installed at birth — never retrofitted.** Day one of every
project creates:

```
📁 {Category}/{Project}/
  📝 README.md          ← opening paragraph = GitHub About (see Step 5)
  📝 CLAUDE.md          ← project rules: inherits root, states the chosen stack,
                           may only ADD or TIGHTEN rules — never loosen
  📁 UV/                ← owner's inbox — gitignored, read at session start,
                           owner's files never edited or deleted
  📁 assets/
    🖼️ logo.svg         ← required for every project (copy → logos/{Name}.svg)
  📁 tests/
    🐍 test_structure_law.py    ← guard tests, preinstalled from day one
    🐍 test_config_sections.py     (spec in rules/CODE.md → Enforcement)
    🐍 test_docs_coverage.py
    🐍 test_doc_links.py
    🐍 run_guards.py            ← fast wrapper the hooks call
  📁 .claude/           ← NEVER tracked (see .gitignore below)
    ⚙️ settings.json    ← PostToolUse + Stop hooks wired to run_guards.py
  📄 .gitignore         ← MUST contain: UV/ and .claude/  (plus stack-appropriate
                           entries). `.claude/` is the agent tooling's own
                           working folder — hook settings, session task lists,
                           audit screenshots, generated proof artifacts — and
                           NONE of it belongs to the product's history (owner
                           decree 2026-08-09, after 26 MB of audit PNGs reached
                           one repo purely because no rule existed anywhere)
```

Plus for installable desktop apps: the `setup/` folder per [SHIP](SHIP.md)
(build orchestrator, cert, NSIS, `app_info.json`).

Docs start with the [DOCS](DOCS.md) skeleton from the first module onward:
`___folder.md` + `__about/` + `__flow/`.

The project `CLAUDE.md` must contain: chosen stack + the written justification
(or a link to it in README), the project's guard-test ratchet policy, and any
project-specific laws. It must NOT restate root rules.

---

<a id="registration"></a>

## Step 5 — Registration

1. **Decide visibility** — Public / Private / Hidden (definitions in
   [CLAUDE.md](../CLAUDE.md) → Project Visibility). A **Hidden** project is
   registered ONLY in local `PRIVATE.md` and SKIPS everything below.
2. **[PROJECTS.md](../PROJECTS.md)** — full entry: tech stack, architecture,
   status, visibility, links.
3. **Root README.md** — compact-list line (the Featured section is curated by
   the owner).
4. **logos/** — copy `assets/logo.svg` as `logos/{ProjectName}.svg`.
5. **GitHub About sync** ([Docs Rules](DOCS.md#github-about)): the README's opening paragraph (1–3 plain
   sentences, ≤ ~350 chars: what it does, for whom, on what platform) IS the
   GitHub About. Whenever a session writes or changes it and a repo exists:

   ```bash
   gh repo edit <owner>/<repo> --description "<the opening paragraph>"
   ```

   Longer intro → its first sentence is the About. No repo yet → sync the moment
   one exists.

---

<a id="uv-tables"></a>

## Appendix — UV Name Inspiration Tables

Optional flavor for Step 2 — never an obligation.

### Tech / Science

| Name | Use For |
|------|---------|
| **Ultra Violet** | Brand identity, visual tools, anything light/color-related |
| **Under Voltage** | Power monitoring, low-resource mode, energy-efficient systems |
| **Unit Vector** | Math/ML modules, normalization, direction-based algorithms |
| **Universal Variable** | Config systems, dynamic settings, shared state containers |
| **Unknown Variable** | Placeholder names, mystery inputs, unsolved parameters |
| **Unified View** | Dashboard components, aggregated data displays |
| **Upstream Validation** | Input sanitization layers, pre-processing checks |
| **Unit Verification** | Test runners, assertion modules, QA tools |
| **Uncompressed Video** | Raw media pipelines, lossless capture modules |
| **Unreal Visuals** | Rendering engines, visual effects, graphics pipelines |
| **Ultrasonic Vibration** | Hardware interfaces, sensor modules, signal processing |
| **Universal Version** | Cross-platform builds, version management systems |

### Vehicles / Industry

| Name | Use For |
|------|---------|
| **Utility Vehicle** | General-purpose tools, multi-function desktop utilities |
| **Urban Vehicle** | City-scale automation, location-aware applications |
| **Unmanned Vehicle** | Autonomous agents, bots, headless automation scripts |
| **Underground Vessel** | Background services, hidden system processes |
| **Underwater Vessel** | Deep data mining, subterranean data pipelines |

### Psychology / Concepts

| Name | Use For |
|------|---------|
| **Uncanny Valley** | AI behavior replication, humanlike simulations (InputDNA platform) |
| **Unconscious Voice** | Passive input capture, background listeners |
| **Unfiltered Vision** | Raw data views, unprocessed output displays |
| **Underlying Values** | Core config, base settings, foundational constants |
| **Unspoken Vulnerability** | Security audit tools, silent failure detectors |
| **Untamed Vitality** | High-performance modes, uncapped processing |
| **Unbroken Vigilance** | Watchdog processes, uptime monitors, always-on services |
| **Unleashed Velocity** | Performance optimization modules, fast-path pipelines |

### Creative / Branding

| Name | Use For |
|------|---------|
| **Unveiled Vision** | Launch features, reveal systems, first-run experiences |
| **Unbound Velocity** | Speed benchmarks, unlimited execution modes |
| **Untold Version** | Hidden builds, internal-only releases, secret branches |
| **Uncharted Venture** | Experimental projects, proof-of-concept prototypes |
| **Unique Voice** | Personalization engines, user profiling (InputDNA) |
| **Unique Vibe** | Signature detection, behavioral fingerprinting |
| **Unique Value** | Differentiator features, competitive advantages |
| **Urban Vibrance** | UI themes, city-aesthetic visual styles |
| **Urban Vision** | Location-aware apps, map-based interfaces |
| **Unstoppable Vision** | Long-running processes, persistent background tasks |
| **Unreal Velocity** | Extreme performance targets, benchmark goals |
| **Unlimited Views** | Analytics dashboards, view counters, open-access systems |
| **Unyielding Vision** | Resilient systems, fault-tolerant architectures |

### Wordplay / Descriptive

| Name | Use For |
|------|---------|
| **Ultra Vague** | Fuzzy matching, approximate search, ambiguous inputs |
| **Ultra Vivid** | High-contrast UIs, enhanced display modes |
| **Unusually Verbose** | Debug/logging modes, verbose output flags |
| **Universally Valid** | Cross-format validators, schema-agnostic checks |
| **Undeniably Valuable** | Premium features, high-impact modules |
| **Unexpectedly Viral** | Sharing mechanisms, distribution systems |
| **Underrated Virtuoso** | Hidden gems, underused but powerful utilities |
| **Unnamed Visionary** | Anonymous/pseudonym systems, identity-masked profiles |
