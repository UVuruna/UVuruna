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
- [Appendix — Name Inspiration](#name-tables)

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

**Owner decree 2026-08-10, class GATE — supersedes the 2026-08-01 order.**
The monorepo over-insisted on the `UV` initials for years and paid for it in
names that served the letters instead of the product. Initials are no longer a
target of any kind. This section governs **new projects AND renames** of
existing ones (rename mechanics: [Renaming](#rename)).

**Priority order:**

1. **A term the market already speaks, aimed at what the app does.** The best
   name sounds like it shipped this year: it borrows a word or phrase that is
   live in the industry's vocabulary right now — *vibe, copilot, forge, mesh,
   stream, pulse, canvas, agent, twin* — and lands so that the borrowed term
   ALSO describes the product's actual job. The reference case is
   `Remote User → Vibe Coder`: "remote user" described the plumbing, "vibe
   coder" names the thing the owner is buying, in the words the market is
   already using for it this year.
2. **Associative and memorable, pleasant to say.** Two short words at most,
   readable at a glance in a window title and on a desktop icon. A plain
   descriptive name always beats a forced clever one — cleverness that needs
   explaining is a worse name than a boring one that doesn't.
3. **Letter bonus, never a requirement — `V`, `U`, `M`, `B`.** A candidate that
   happens to carry one of these letters, best of all as an initial, gets a
   small plus in the comparison. That is the whole weight it carries. It never
   breaks a tie against a name that reads better, and **no name is ever bent to
   produce one**.
4. **Symbolism is free, and it is decoration.** `V` may be read as *Vuruna*,
   *Vibe*, *Velocity*, *Victory* — anything at all; `B` as *Build*, *Brain*,
   *Beat*. Invent the reading AFTER a name has already won on points 1–3.
   Symbolism is never an argument for picking a name, only a nice line to put
   in the story below.

**Procedure:** propose 3–5 candidates. Each candidate is one line: the name,
then the [name story](#name-story) it would carry in the README. Mark the
letter bonus where it happens to land. The owner picks — an agent never renames
or names a project on its own judgment.

The [appendix below](#name-tables) is inspiration only, never a checklist.

<a id="name-story"></a>

### The Name Story (owner decree 2026-08-10, class GATE)

**Every project's README explains its own name, in the README, in one or two
sentences.** A name that has to be decoded by the reader is a name that failed;
a name whose story is written down turns into the project's pitch.

The story says what the name promises and how the product delivers it — it is
about the USER'S experience, not the implementation:

> **Why "Vibe Coder"** — because it turns your phone into the machine: you
> write code from the beach, from the bath, thumbing a controller like you are
> playing a game, and what comes out the other end is a running program.

Placement: immediately after the README's opening paragraph (the paragraph that
is also the GitHub About — [DOCS](DOCS.md#github-about)), as a short
`## Why "<Name>"` section or a single italic line under the title. Renaming a
project rewrites this section in the same commit as the rename.

<a id="rename"></a>

### Renaming an existing project

Same priority order, same story requirement, plus the mechanics: the folder
follows the official name, `rules/tools/rename_project.py` does the sweep (it
carries session transcripts across and takes `--exclude` for dated records —
`REPORT-*.md` and "born from" narratives describe what a project was CALLED
then and are never rewritten). Re-check afterwards: the GitHub repo name, the
About text, `logos/{Name}.svg`, [PROJECTS.md](../PROJECTS.md), the root README
line, and any machine-wide hook path that contains the old name.

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

<a id="name-tables"></a>

## Appendix — Name Inspiration

Inspiration only. Nothing here is a checklist, and a name that appears in no
table is not worse for it — Step 2 decides, the owner picks.

### Patterns that produce names people repeat

| Pattern | Words it draws on | Why it works |
|---------|-------------------|--------------|
| **The act, named** | the user's own activity, said out loud | *Vibe Coder*, *Prompt Painter* — the user reads it and thinks "that is what I am doing" |
| **The workshop** | Forge, Foundry, Studio, Workbench, Kiln, Press | says a thing gets MADE here — generators, converters, builders |
| **The instrument** | Lens, Compass, Dial, Gauge, Beacon, Pulse, Vitals | says a thing gets MEASURED or SHOWN — monitors, viewers, dashboards |
| **The companion** | Copilot, Sidekick, Scout, Sentry, Butler, Twin | says a thing acts FOR you — agents, automation, watchdogs |
| **The material** | DNA, Grain, Fabric, Mesh, Thread, Signal, Trace | names the stuff the app works with — capture, data, ML |
| **The moment** | Dawn, Drift, Echo, Afterglow, Halo | fits time-based, ambient and visual products |

Two words at most, and the second word carries the job: `<flavour> <job>`.
A term borrowed from what the industry is talking about **this year** ages
faster than a plain one but sells far better today — worth it for anything with
an audience, wrong for infrastructure that must still make sense in five years.

### Letter-bonus word bank — `V` · `U` · `M` · `B`

Only for breaking a tie between names that already won on their own merit.

| Letter | Words |
|--------|-------|
| **V** | Vibe, Vivid, Vector, Velocity, Vantage, Vault, Verge, Vista, Vital, Voyager, Vertex, Vessel |
| **U** | Uplink, Unison, Uptake, Umbra, Uplift, Utility, Uniform, Upstream |
| **M** | Mesh, Muse, Mosaic, Momentum, Mirror, Marker, Mainline, Motive |
| **B** | Beacon, Bloom, Bridge, Bench, Blueprint, Beat, Bolt, Bounty |

### House history — the retired UV tables

Until 2026-08-10 this appendix held sixty `U*/V*` word pairs and Step 2 pushed
every new project toward an initials pattern. Two live names came out of that
era honestly (*Ultra Vivid*, *Input DNA*); the practice as a whole produced
names that explained the letters instead of the product, which is why the owner
retired it. The full tables remain in this file's git history for anyone
curious — they are not to be reinstated.
