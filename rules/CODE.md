# CODE — shared checklist for GUI · FEATURE · BUGFIX · REFACTOR

Every line: WHAT · WHO CHECKS · EVIDENCE. Before editing read the folder's
`___folder.md` and `__about/` docs of the files you touch; update them after.

## Laws

- **STRUCTURE (S, supreme)** — new code goes into the module whose
  RESPONSIBILITY it serves, or into a NEW module born with its docs. Appending
  to whichever file was open is a defect. **Decide BEFORE writing:** the ledger
  carries a `struktura:` block — one line per new/grown unit, `<module> ←
  <unit>: why it belongs there` or `NEW <module>: responsibility`; a `def`/
  `class` the block never placed blocks the session. · `gate.py pre/stop` ·
  evidence: the block + reviewer's `pregled ≥ 8` (Standard/Wide).
- **The wall is a reason to think, not a saw** (owner 2026-08-18) — ~1,000
  logic lines is where a file needs a WRITTEN reason to stay whole, never a
  place to cut a 1,020-line file into unnatural pieces; and never an excuse
  for a 4,000-line procedural file. Split by responsibility (a piece with no
  clean name is not a piece); mechanical `part1/part2` is forbidden;
  procedure: `rules/briefs/REFACTOR-GODFILES.md`. · `structure_guard.py` in
  `run_guards` FULL · evidence: guard green.
- **A declarative table is not logic** — the guard subtracts top-level pure
  literals; the moment a table computes (call, comprehension, lambda) it counts
  in full. · `run_guards`.
- **RATCHET only shrinks** — `tests/structure_ratchet.json` names the file,
  its size, WHY it stays whole and who owes the split; a ratcheted file that
  GROWS fails the guard; a new entry needs the owner's word that session. ·
  `structure_guard.py`.
- **CONFIG SECTION** — config/data files live under one-line section banners
  (`# ══ POINTER SHAPES ══`); a table is written ONCE, whole, in its section;
  `TABLE["x"]["y"] = …`, module-level `.update(...)` or an entry dumped at file
  end fails. · `run_guards` (`test_config_sections`).
- **ONE KIND, ONE CLASS** — things sharing behaviour (cards, watches, themes,
  pages, panels, buttons of a kind) are instances of ONE class or entries of ONE
  registry; adding one is "add an object", never a copied block. · reviewer +
  `rules/tools/clone_guard.py` in `run_guards` FULL · escape `clone-ok: <reason>`
  on the block · history → `rules/history/one-kind-one-class.md`.

## Guards

Four guard tests per project, standard names: `test_structure_law.py` ·
`test_config_sections.py` · `test_docs_coverage.py` · `test_doc_links.py`.
GUI projects add `test_layout_law.py` + `test_layout_audit.py` (`rules/GUI.md`).

- `python tests/run_guards.py --fast` on PostToolUse (structure + config only,
  exits 0 for non-source files); `python tests/run_guards.py` FULL on Stop, and
  FULL runs only when `rules/hooks/changed_files.py` says source was touched.
  Exit 2 = block. Template: `rules/templates/run_guards.py`.
- FULL includes the clone guard and the layout audit for touched windows only.
- A new or changed guard is SHOWN failing on a planted violation and passing
  after its removal (undo the plant by hand, never `git checkout --`). · reviewer.
- Guards skip their own `tests/`. A run that cannot fix a violation may add a
  ratchet entry `pending owner ratification` and says so at the TOP of its
  report; a silently red guard is never an option.

## Core rules — one line each

- **No error masking** — never `except: pass`, never a silent default; catch
  the specific error, log, re-raise; GUI apps log uncaught exceptions. · reviewer.
- **No hardcoded values** — thresholds, sizes, colors, paths live in the
  project's config; hardcode only what never changes. Unsure → ask. · reviewer.
- **No duplicate code** — before a new class/method, ask whether it exists and
  whether more of its kind will come; extract a base or registry. · clone guard.
- **No backward compatibility** — grep ALL callers, update each, DELETE the old
  path; no wrapper "for compatibility". · reviewer + FEATURE matrix row.
- **No defensive programming for impossible scenarios** — defend only at real
  boundaries (input, I/O, network, OS). · reviewer.
- **Progress logging** — long operations log every N items (elapsed, done/total,
  rate); silent long loops are forbidden. **Logging scaled to the project** —
  `logging`, `logs/`, rotation; every app has SOME error visibility. · reviewer.

## Compute, don't generate

- An asset is GENERATED only when irreducibly artistic; every variant is
  COMPUTED from one master (tint, lighting, phase, orientation, size). The
  derivation check is answered IN WRITING before an asset enters a prompt
  sheet or the repo. · reviewer (Owner Guardrail #6).

## Pointers

Profiling: `rules/howto/profiling.md` · stories and decrees:
`rules/history/code-laws.md`, `rules/history/one-kind-one-class.md`.
