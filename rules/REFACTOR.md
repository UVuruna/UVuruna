# REFACTOR — category rules

Splitting a file, moving code, introducing a class or registry, cleaning up.
Read with `CODE.md`. A refactor changes STRUCTURE and never behaviour.

## The tooth (`gate.py stop`)

1. **The same tests green BEFORE and AFTER** — `uv test` before the first edit
   and after the last one, both rc = 0 and with the SAME total count. A changed
   total means behaviour or coverage moved: say so and stop, or it is not a
   refactor (runner usage: `howto/runner.md`).
2. **Structural guards green** — `run_guards` FULL: structure law, config
   sections, docs coverage, doc links, plus the clone guard
   (`rules/tools/clone_guard.py`). A clone that must stay carries
   `clone-ok: <reason>` on the block.
3. **The RATCHET only shrinks** — a split removes its entry in the same commit;
   no new entry without the owner's word in that session.
4. **Standard/Wide: a reviewer ≥ 8** — a cheap sonnet agent walks the "one kind,
   one class" checklist (repeated kind without a class · new thing added by
   copying · config in code instead of a registry · a layer doing another
   layer's job · a file standing at the wall · tests changed to make them pass)
   and writes the grade plus its three best next refactors into the ledger.
   Below 8 the refactor is not finished.

## Rules while moving code

- **Split by RESPONSIBILITY, never mechanically** — `gui_part1.py`/`part2.py` is
  forbidden, and so is the opposite extreme of dozens of 30-line files.
  Procedure: `briefs/REFACTOR-GODFILES.md`.
- **No backward compatibility** — grep ALL callers, update each, DELETE the old
  path; never a wrapper "for compatibility". The removal is a matrix row when a
  feature depended on it (`FEATURE.md`).
- **Docs move with the code** — `___folder.md`, `__about/`, `__flow/` follow the
  file in the same session, and the navigation chain stays unbroken (`DOCS.md`).
- **One commit per coherent move**, numbered per the constitution; a pure move
  may cite `commit <sha>` as its `!` evidence line.
- **Behaviour questions belong to the owner** — a refactor that would change
  what the user sees stops and asks (`PLAN.md`).

History → `history/one-kind-one-class.md` (the four-project probe that produced
the law), `history/code-laws.md` (the god-files that produced the wall).
