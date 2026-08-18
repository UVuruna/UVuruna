# MD-First 2.0 — the story and the pilot lessons

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="living-docs"></a>

## The Living Docs Rule (owner decree 2026-08-01)

**Files are living bodies — their documentation lives and dies with them.**
The historical failure: docs are written once at file creation and never touched
again, so they slowly become lies — and a doc that lies is worse than no doc,
because agents trust it.

Therefore, in EVERY session, for EVERY file you change:

1. Open its `__about/` doc (and `__flow/` if it has one) and ask: *does my
   change alter what this says?* If yes — update it NOW, in the same session.
2. Walk the chain UPWARD: the folder's `___folder.md`, its parent's, up to
   `README.md` — update every level your change touched (new file listed,
   moved responsibility, changed connection).
3. A change without its doc update is UNFINISHED WORK — the Stop-hook guard
   (docs coverage + links) catches the structural part; the content part is
   the session's duty.

---

## Tiers — Which File Gets Which Docs

Docs are written where they carry information — never for ritual (the
compute-don't-generate principle applied to documentation; real case: a project
accumulated 441 doc files against 298 code files).

| Tier | Definition | Obligation |
|------|-----------|------------|
| **Trivial** | glue, `__init__`, re-exports, < ~60 lines of plain wiring | one line in `___folder.md` only — NO own docs |
| **Standard** | ordinary module | `__about/{name}.md` |
| **Algorithmic** | a file whose logic a DIAGRAM genuinely tells better than the code itself | `__about/{name}.md` **+** `__flow/{name}.md` |
| tests/ | test modules | `___tests.md` folder doc only |

**The flow doc must EARN its place (owner decision 2026-08-01).** Being a
widget, a config table or a protocol does NOT automatically make a file
Algorithmic — the first pilot migrations proved that reading turns ~80% of
files "Algorithmic" and doubles the doc count. The test: *would the diagram
just restate the code?* Then the file is Standard. Reserve `__flow/` for
real multi-step algorithms, nontrivial GUI layouts and configs whose
structure needs a picture. Concrete signals that a file EARNS its flow:
a background-thread or process handoff, cascading multi-level state, a real
state machine, nontrivial geometry/math, a protocol with ordered steps. (Projects migrated before this narrowing carry
wider flow lists — they get trimmed in a dedicated revision pass, recorded
as a debt.)

The project's `test_docs_coverage.py` encodes the tier assignment (trivial
list / flow-required list) — changing a file's tier means updating that test in
the same commit.

Tier judgment rules (lessons from the 2026-08-01 pilot):

- **Nature beats the line band — in BOTH directions.** The ~60-line bound is a
  heuristic; a 300-line `__init__.py` of pure mechanical re-exports is still
  Trivial, and an 86-line Qt widget is still Algorithmic. When nature and line
  count disagree, nature decides — and the coverage test's tier list records
  the override.
- An `__init__.py` at Standard tier or above documents as
  `__about/__init__.md` — the identical-basename rule applies unchanged.
- `.md` files that are DATA, not documentation (e.g. `tests/fixtures/*.md`
  sample sheets), are exempt from the navigation chain via an explicit EXEMPT
  list inside `test_doc_links.py`.

---

