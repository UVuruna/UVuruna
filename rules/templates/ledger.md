# <session title — what the owner asked for>
kategorija: TODO · klasa: TODO · agenti: TODO

struktura:
  <module path> ← <unit>: <why it belongs there>   (or: NEW <module>: <responsibility>)

- [ ] T1 <first deliverable>

<!-- kategorija: one or more of GUI FEATURE BUGFIX REFACTOR DOCS PLAN BUILD
     klasa: Trivial | Standard | Wide · agenti: none, or "1 sonnet grader"
     States: [ ] not started · [>] in progress · [?] waits for the owner (needs
     a ? line) · [~] done, unproven · [x] done WITH evidence (needs a ! line
     naming an ev-NNNN id from evidence.jsonl). Indent 2 spaces per level.
     Evidence comes ONLY from `python rules/tools/uv.py test|shot|run|device`.

- [x] T1 Card "Watch face" in Settings @fable
    ! ev-0003 shot SettingsDialog laptop-avg — looked — grade 9 (nothing clipped)
- [~] T2 New watch "Nautilus" @sonnet
    ! ev-0007 test 12/12 · matrix 5/6 (row phone-landscape: emulator unavailable)
- [?] T3 BUILD & RELEASE — waits for the owner's word
    ? build v0.0.288 with T1+T2? command: python setup/build.py

Code categories (Standard/Wide) fill `struktura:` BEFORE the first product
edit — every new def/class must be placed there; a reviewer sub-agent then
writes `pregled N` (≥ 8) for FEATURE/REFACTOR. FEATURE writes this BEFORE its first product edit; BUGFIX writes `uzrok: <root
cause>`, a repeat also `proces-uzrok: <why the previous claim was false>`:
matrica:
| # | scenario | input/state | device | evidence |
| 1 | average device: laptop-avg start + main flow | fresh install | laptop-avg | ev-0009 |
| 2 | fresh install — no owner paths/hooks/rules used | — | pc-low | ev-0010 | -->
