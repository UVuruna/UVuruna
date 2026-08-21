# DOCS — MD-First 2.0

Documentation-Driven Development is how this organization programs: an agent
that starts in a project sees structure, responsibilities and connections
without reading code first. Read this for a DOCS session and at the "update
docs" step of every code session.

## Living docs (LAW)

For EVERY file you changed, in the SAME session:

1. Open its `__about/` doc (and `__flow/` if it has one) and ask whether your
   change alters what it says — if yes, update it now.
2. Walk the chain UPWARD: the folder's `___folder.md`, its parent's, up to
   `README.md`; update every level your change touched.
3. A change without its doc update is UNFINISHED work. · `run_guards`
   (`test_docs_coverage.py`, `test_doc_links.py`) catch the structural half; the
   content half is the session's duty.

## Structure

```
📁 gui/
  📝 ___gui.md      ← purpose, file table, connections, design decisions
  📁 __about/       ← WHAT: per file — purpose, Uses / Used by, classes
  📁 __flow/        ← HOW: per file — Mermaid diagram + neutral pseudocode
  🐍 main_window.py
```

- `___folder.md` (triple underscore, sorts first) lists every file in one line
  each and links into `__about/` and `__flow/`.
- `__about/{name}.md` and `__flow/{name}.md` carry the IDENTICAL basename as the
  script they describe.
- Flat, root-level projects put `__about/`/`__flow/` in the project root and let
  `README.md` play the folder-doc role — per LOOSE FILE, not per project.

## Tiers — who gets which docs

| Tier | Definition | Obligation |
|------|-----------|------------|
| Trivial | glue, `__init__`, re-exports, < ~60 lines of wiring | one line in `___folder.md` |
| Standard | ordinary module | `__about/{name}.md` |
| Algorithmic | a file a DIAGRAM tells better than the code | `__about/` + `__flow/` |
| tests/ | test modules | `___tests.md` only |

**A flow doc must EARN its place** — the test is "would the diagram just restate
the code?". Signals that it earns one: a thread or process handoff, cascading
state, a real state machine, nontrivial geometry, an ordered protocol. **Nature
beats the line band in both directions**, and the tier list inside
`test_docs_coverage.py` records every override — changing a tier means editing
that test in the same commit.

## Templates

`___folder.md`: title, purpose, `## Files` table (file · tier · one line ·
`[about](__about/x.md) · [flow](__flow/x.md)`), `## Connections` (Uses / Used
by, each with a why), `## Design Decisions`.
`__about/{name}.md`: script link (+ flow link if Algorithmic), `## Purpose`,
`## Connections` (Uses / Used by), `## Classes` — role, key attributes and
methods one line each.
`__flow/{name}.md`: about-link, `## Algorithm` — Mermaid flowchart plus
language-neutral pseudocode; GUI files sketch zones, config files draw their
section/key tree.

## Navigation chain

From `README.md` every project `.md` must be reachable, with no broken relative
link. · `test_doc_links.py`. Encoded exceptions: `.claude/`, `UV/`, caches and
vendored dirs are not walked; links into `UV/` are not asserted; data `.md`
files sit in the test's EXEMPT list; **monorepo-root docs are cited as plain
backticked text, never as markdown links**.

Link rules: links point at `.md` files (scripts only via an explicit
"(script)" link) · link text is human-readable, never a raw path · one `../`
per level including the doc subfolder · link a `___folder.md` when the target's
`__about/` doc does not exist yet or the file is Trivial · `Used by: none
(entry point)` is written out, never left off.

## README

- The opening 1–3 sentence paragraph (≤ ~350 chars) IS the GitHub About; when it
  changes and a repo exists: `gh repo edit <owner>/<repo> --description "…"`.
- **The name story** (owner decree 2026-08-10, GATE) — directly under it, one or
  two sentences on why the project carries its name, sold as the user's
  experience, never the implementation. A rename rewrites it in the same commit.

## FEATURES.md (owner decree 2026-08-21)

Every project keeps `docs/FEATURES.md`, README-level: the product's MAIN
functionalities, briefly described, **grouped by kinship**, written for the
future USER — never the implementation. Feature headings end with a slug
(`` ### <Name> · `slug` ``); ledger tasks tag their feature with `#slug`, so
work history and catalogue link both ways. Linked from README. First
instance: `Applications/VibeCoder/docs/FEATURES.md`.

## Markdown conventions

Folder trees use emoji + 2-space indent (never ASCII box-drawing): 📁 📂 📄 🐍
🔧 ⚙️ 📝 🖼️ 🗄️ · diagrams are Mermaid, never ASCII art, and every diagram with
subgraphs opens with the `subGraphTitleMargin` init line · headers referenced
from a TOC carry an explicit `<a id="…"></a>`.

History and pilot lessons → `history/docs-md-first.md`; the completed migration
brief → `history/MIGRATE-DOCS.md`.
