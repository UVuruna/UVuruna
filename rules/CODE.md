# CODE — shared checklist for GUI · FEATURE · BUGFIX · REFACTOR

Read this plus your category file. Every line: WHAT · WHO CHECKS · EVIDENCE.
Before editing, read the folder's `___folder.md` and the `__about/` docs of the
files you touch; update them after (`DOCS.md`).

## Laws

- **STRUCTURE (S, supreme)** — new code goes into the module whose
  RESPONSIBILITY it serves, or into a NEW module born with its docs. Appending
  to whichever file was open is a defect. · `run_guards` (`test_structure_law`)
  · evidence: guard green.
- **Split by responsibility BEFORE the wall** — ≤ ~500 lines of logic normal ·
  ~500–1,000 ask in writing whether the file holds two responsibilities ·
  > ~1,000 split, or a RATCHET entry approved by the owner in that session.
  Mechanical splits (`gui_part1.py`) are forbidden; procedure:
  `rules/briefs/REFACTOR-GODFILES.md`. · `run_guards` · evidence: guard green.
- **A declarative table is not logic** — the guard subtracts top-level pure
  literals; the moment a table computes (call, comprehension, lambda) it counts
  in full. · `run_guards`.
- **RATCHET only shrinks** — an entry names the file, WHY it stays whole and
  who owes the split; a new one needs the owner's word that session. · reviewer.
- **CONFIG SECTION** — every config/data file is organised under one-line
  section banners (`# ══ POINTER SHAPES ══`, ≥ 8 box/`=` characters); a table is
  written ONCE, whole, in its section; `TABLE["x"]["y"] = …`, module-level
  `.update(...)` or an entry dumped at file end fails. · `run_guards`
  (`test_config_sections`) · evidence: guard green.
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
  after its removal — undo the plant by removing exactly what you planted, never
  `git checkout --` over uncommitted work. · reviewer · evidence: both runs.
- Guards exclude their own `tests/` directory when scanning sources.
- An autonomous run that cannot safely fix a violation may add a ratchet entry
  marked `pending owner ratification` and MUST surface it at the top of its
  report. Leaving a guard silently red is never an option.

## Core rules — one line each

- **No error masking** — never `except: pass`, never a silent default; catch
  the specific error, log it, re-raise. Fallbacks only as documented behaviour
  or retry-with-escalation; GUI apps log uncaught exceptions. · reviewer.
- **No hardcoded values** — thresholds, sizes, colors, paths live in the
  project's config; hardcode only what never changes. Unsure → ask. · reviewer.
- **No duplicate code** — before a new class/method, ask whether it exists and
  whether more of its kind will come; extract a base or registry. · clone guard.
- **No backward compatibility** — grep ALL callers, update each, DELETE the old
  path; no wrapper "for compatibility". · reviewer + FEATURE matrix row.
- **No defensive programming for impossible scenarios** — trust internal
  guarantees; defend only at real boundaries (input, I/O, network, OS). · reviewer.
- **Progress logging** — a long-running operation logs every N items: elapsed,
  processed/total, percent, rate. Silent long loops are forbidden. · reviewer.
- **Logging scaled to the project** — Python `logging`, `logs/`, rotating
  handler; every application has SOME error visibility. · reviewer.

## Compute, don't generate

- An asset is GENERATED only when irreducibly artistic; every variant of it is
  COMPUTED from one master (tint, lighting, phase, orientation, size).
- Answer the derivation check IN WRITING before any asset enters a prompt sheet,
  a queue or the repo — legacy sheets are re-asked before regenerating.
- Class LAW by conduct, checked by the reviewer; it is Owner Guardrail #6.

## Pointers

Profiling a slow Python process: `rules/howto/profiling.md`.
Stories, decrees and the born-from cases: `rules/history/code-laws.md`,
`rules/history/one-kind-one-class.md`.
