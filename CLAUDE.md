# CLAUDE.md — UVuruna Constitution

Universal law for **ALL projects**; one rulebook per CATEGORY in `rules/`
([Router](#router)), plus `history/`, `howto/` and `briefs/`. Project
`CLAUDE.md` files may only ADD or TIGHTEN it.

## Organization

Projects sit under `Applications/ Gadgets/ Games/ Machine Learning/ WebSites/`;
root also holds `logos/` and `rules/`. **Max 2 levels: `Category/Project/`**;
every project has its own git repo, and the root repo tracks only root docs,
`rules/` and `logos/`.

## Project Visibility

**Public** — public repo, described publicly, listed in README/PROJECTS ·
**Private** — private repo or none, description only, still listed ·
**Hidden** — never on GitHub, never described, only in `PRIVATE.md`.

**Hidden projects must never appear in any tracked file** — no name, no path,
no logo; `PRIVATE.md` stays untracked.

**Main projects (owner decree 2026-08-17):** the projects under ACTIVE,
INTENSIVE development — the current focus — carry a ⭐ beside their name in
`README.md` / `PROJECTS.md` (a hidden main project is starred only in
`PRIVATE.md`). When the owner says "glavni projekti" he means exactly the
starred set; it changes only by his word.

## Priorities (higher wins)

**S. STRUCTURE** (supreme) · **A. Performance** (absolute on hot paths, never at
clarity's cost off them) · **B. Readability** · **C. Inheritance over
duplication** · **D. Logging**, scaled.

## The Laws

1. **STRUCTURE** (`CODE.md`) — code lands in the module whose responsibility it
   serves; split before the ~1,000-line wall; over it needs a ratchet entry.
2. **CONFIG SECTION** (`CODE.md`) — defined once, whole, in its banner section,
   never patched after the fact.
3. **DOCS** (`DOCS.md`) — MD-First 2.0 coverage + nav chain from README.
4. **BUILD & RELEASE — NEVER AUTOMATIC** (`BUILD.md`, owner verdict
   2026-08-18) — never without his word in that session; a session that changed
   an installable app ends with `## BUILD & RELEASE?` and the exact command;
   sub-agents never build.
5. **FIXED = VERIFIED** (`BUGFIX.md`) — a session ends FIXED (root cause + fix +
   evidence), CANNOT FIX HERE (why + what unblocks) or IMPOSSIBLE — never
   "solved" for a symptom patch.
6. **REPEAT** (`BUGFIX.md`) — when he reports something a previous round closed,
   the FIRST deliverable is `proces-uzrok:` (why the old claim was false), the
   code second; `[x]` only on his confirmation or evidence from HIS machine,
   else `[~]`, carried forward.
7. **SPACE & LEGIBILITY** (`GUI.md`) — nothing readable cut off, nothing
   starving beside empty space; free space → reflow → raised minimum → scroll;
   every minimum fits 1280×720; checks run only on touched GUI files.
8. **ONE KIND, ONE CLASS** (`CODE.md`) — things sharing behaviour are instances of
   ONE class or entries of ONE registry; a new one is an entry or subclass,
   never a copied block.

<a id="router"></a>

## Router — by category

The first ledger line names the category, which picks the rulebook and the
tooth; several may combine, each bringing its own.

- GUI → `rules/CODE.md` + `rules/GUI.md` + `DESIGN.md`
- FEATURE / BUGFIX / REFACTOR → `rules/CODE.md` + `rules/<CATEGORY>.md`
- DOCS / PLAN / BUILD → `rules/<CATEGORY>.md`
- New project → `rules/START.md` + `rules/DOCS.md`

## Session flow

1. **START** — ledger line `kategorija: GUI + FEATURE · klasa: Standard ·
   agenti: 1 sonnet`; no product edit without it (`gate.py pre`). Grammar:
   `rules/howto/ledger.md`.
2. **SKICA** — Trivial: nothing · Standard: sketch + scenario MATRIX · Wide:
   echo-brief; wait for his yes.
3. **RAD** — code; `run_guards --fast` on every edit.
4. **ZUB** — `uv shot/test/run/device`; evidence NEWER than the last product
   edit, and the agent opens the images it claims.
5. **LEDGER** — tasks `[ ] [>] [?] [~] [x]`, an `!` evidence line each.
6. **KRAJ** — open items FIRST, then `## BUILD & RELEASE?`.

## Universal Conduct

- **Language:** Serbian (Latin) with him, English in code, comments, docs and
  commits (`gate.py pre`; escapes `lang-ok:`, `lang-ok-begin/end`,
  `.claude/language-frame.json` for customer-facing copy).
- **The LAST text block of a turn is the whole message** — he sees only that
  block: every question he asked answered there, never a one-liner after tool
  calls, never a working turn ending with no message.
- **Sub-agents carry their own tooth** — one that edited product files runs
  something after its last edit and reports `! ` evidence lines.
- **Session start:** read the project's `UV/` inbox (never edit or delete his
  files) and the relevant `___folder.md`. **Ask before assuming** — better 100
  questions than 1 bug; disagreeing constructively is a duty (`PLAN.md`).
- **Token economy:** triage in one line — **Trivial** (inline, no agents) /
  **Standard** (+ a few agents for parallel pieces) / **Wide** (agents, sized to
  the ask); weakest capable tier per delegated task; a multi-agent workflow only
  on his explicit request; reuse research, never rerun it.
- **Honesty:** no capacity lies, no error masking, evidence for every claim of
  finished work. **Scope:** only what was asked; propose the rest at the end.
- **We build for OTHERS, never for his machine** (owner decree 2026-08-16): a
  product never leans on this monorepo's `rules/`, hooks, `CLAUDE.md`, his
  `.claude/`, paths or habits — it ships what it needs, proven on the profiles
  in `rules/devices.json`.
- **Files:** no `_v2`/`_new`/`_backup` — git is the history; ask before
  deleting. **After the work:** update the docs you touched, and commit.

## Version & Commits

**`0.0.000 description`** — patch zero-padded to 3, short English phrase, em
dash `—` for detail. Related work in one session: +1 (`1.0.500 → 1.0.501`);
unrelated: next round (`1.0.508 → 1.0.510`). Bump from `git log --oneline -5`,
group by topic, stage the exact files (**never** `git add .`).
