# CODE — Implementation & Fixing Rules

**Who reads this:** every session that writes or changes code — features, fixes,
refactors. Read the target folder's `___folder.md` (and `__about/` docs of the
files you touch) BEFORE editing; update docs after ([DOCS](DOCS.md)).
New functionality starts with an algorithm sketch shown to the owner —
[Present Before Building](PLAN.md#present).

## Table of Contents

- [The Structure Law](#structure-law)
- [The Config Section Law](#config-law)
- [Enforcement — Guard Tests & Hooks](#enforcement)
- [Core Code Rules](#core-rules)
- [Compute, Don't Generate](#compute)
- [Profiling — Python CPU (py-spy)](#profiling)

---

<a id="structure-law"></a>

## THE STRUCTURE LAW — Priority S (owner decree 2026-07-29, SUPREME)

A program is a STRUCTURE of small, cohesive modules — never an accretion of code
that happens to run. "It works" is not the bar: a single 10-million-line file can
work. This law outranks performance, readability, everything.

1. **Placement is law, not style.** New code goes into the module whose
   RESPONSIBILITY it serves, or into a NEW module created for it (with its
   docs). Appending to whichever file was open is a DEFECT of the same severity
   as a failing test. Before writing, ALWAYS check: does a module (or a section
   within the right file) already own this responsibility?
2. **Thresholds (per file) — counted in LINES OF LOGIC:**

   | Lines of logic | Status | Action |
   |-------|--------|--------|
   | ≤ ~500 | Normal | Nothing — size alone is fine |
   | ~500–1,000 | Smell | ASK in writing: "Does this file hold more than one responsibility?" |
   | > ~1,000 | Violation | Split by responsibility — or a documented ratchet entry (below) |

   **A declarative table is not logic** (owner ruling 2026-08-05). The
   threshold measures what a reader must hold in their head at once —
   BEHAVIOUR. A registry, a roster, a lookup table is a DIRECTORY: sibling
   entries of one kind, read by looking one up, never top to bottom. Splitting
   such a table across files makes one subject live in several places and
   forces the reader to chase imports to compare two entries — the opposite of
   what this law is for. The guard therefore subtracts top-level assignments
   whose value is a pure literal (dict/list/tuple/set, plus the module
   docstring) before applying the threshold, so a file that is ALL table may be
   as long as its subject is. **The moment a table computes** — a call, a
   comprehension or a lambda inside the literal — **it is logic again** and
   counts in full.

   Born from a real over-correction: a theme registry of 35 sibling entries was
   cut into eight group files purely to get under 1,000 lines, which made one
   subject unreadable. It went back into one file the same day and the MEASURE
   was fixed instead.

3. **Split by RESPONSIBILITY, never mechanically.** `gui_part1.py`/`gui_part2.py`
   is forbidden; so is the opposite extreme (dozens of 30-line files = import
   spaghetti). Cohesion is the criterion; line count only forces the question.
   Full split procedure: [REFACTOR-GODFILES.md](../REFACTOR-GODFILES.md).
   Splitting follows Rule "No Backward Compatibility" (update ALL callers, no
   shims) and changes NO behavior.
4. **This law outranks feature work.** A session that must extend an
   over-threshold file first splits it — or obtains the owner's explicit
   deferral, recorded as a ratchet entry.

History that produced the law: PromptPainter `gui.py` reached 8,800+ lines;
Watch Academy accumulated multiple 3,000+-line modules — all flagged, all
tolerated, because no test failed. Only what breaks the build holds.

---

<a id="config-law"></a>

## THE CONFIG SECTION LAW (owner decree 2026-08-01)

Config files and data tables are STRUCTURES, not notebooks. The canonical
failure this law kills: a config defines POINTER shapes, each with color
variants — and a later session, adding one color, doesn't even look where shapes
live and dumps the new entry at the end of the file.

1. **Named section banners.** Every config/data file is organized under visible
   section banners. Canonical form — ONE comment line, the section name on
   that same line, with a run of **at least 8** box-drawing/`=` characters
   (multi-line `# ---` sandwiches are not banners; every project's guard must
   recognize the same form or the law means different things per repo):

   ```python
   # ═══════════════════════════ POINTER SHAPES ═══════════════════════════
   ```

2. **Defined once, whole, in its section.** A table/class/constant is written
   ONCE, complete, in the section that owns it. Adding a variant means editing
   the EXISTING structure in place.
3. **Post-definition patching is FORBIDDEN.** `TABLE["x"]["y"] = ...` far below
   the table, `.update(...)` at module level, or an entry dumped at file end are
   defects — the guard test fails the build on them.
4. **Checkable semantics for the guard** (so implementations don't diverge):
   after the module docstring and imports, the file's FIRST top-level statement
   must be preceded by a section banner; every top-level definition belongs to
   the banner above it. The guard fails on: any top-level definition before the
   first banner (imports/docstring exempt), duplicate dict keys, and
   post-definition patching of an earlier module-level table.

```python
# ❌ FORBIDDEN — new variant dumped at file end, far from its family
POINTER_SHAPES = { "arrow": {...}, "circle": {...} }
# ... 400 lines later ...
POINTER_SHAPES["arrow"]["colors"]["crimson"] = "#DC143C"   # guard test FAILS

# ✅ REQUIRED — the variant lives inside its structure, in its section
POINTER_SHAPES = {
    "arrow":  { "colors": { "green": "#22C55E", "crimson": "#DC143C" } },
    "circle": { "colors": { "green": "#22C55E" } },
}
```

---

<a id="enforcement"></a>

## Enforcement — Guard Tests & Hooks

**A rule without a check is a request.** Every project carries FOUR guard tests
(standard names — no local variants) plus a fast runner, wired into Claude Code
hooks. New projects get them from the scaffold ([START](START.md)); existing
projects get them via [MIGRATE-DOCS.md](../MIGRATE-DOCS.md).

| Test | Fails the build when |
|------|----------------------|
| `tests/test_structure_law.py` | any source file exceeds ~1,000 lines OF LOGIC (declarative tables subtracted) and is not in the RATCHET allowlist |
| `tests/test_config_sections.py` | a file listed in its `CONFIG_FILES` has: module-level post-definition patching of an earlier table (`X[...] = ...` / `X.update(...)`), duplicate dict keys, or top-level definitions outside any section banner |
| `tests/test_docs_coverage.py` | a source file lacks the docs its tier requires (spec in [DOCS](DOCS.md)) |
| `tests/test_doc_links.py` | any project `.md` is unreachable from `README.md`, or any relative `.md` link is broken |

**GUI projects carry two more** (THE SPACE & LEGIBILITY LAW —
[GUI](GUI.md) → Law — Space & Legibility; installed via
[MIGRATE-LAYOUT.md](../MIGRATE-LAYOUT.md), templates in `rules/templates/`):

| Test | Fails the build when |
|------|----------------------|
| `tests/test_layout_law.py` | a GUI source elides/trims text, forces a scrollbar, disables wrapping, or hard-sizes a text-bearing widget — unless the line carries `layout-law: exempt - <reason>` or the file is in its `RATCHET` |
| `tests/test_layout_audit.py` | a window opened offscreen at its declared minimum (and larger) clips a widget, cannot fit its own text, has no declared minimum, or shows a scrollbar while a spacer in the same window holds unused space |

The audit is the only guard that INSTANTIATES the product; it stays in the full
Stop run, never in `--fast`. It has **no ratchet** by design — a runtime layout
failure is a visible bug, and ratcheting one would report it as solved.

**RATCHET allowlist rules:** each entry names the file, WHY it stays whole, and
the session that owes the split. The list may only SHRINK — adding an entry
requires the owner's explicit approval in that same session. An entry's remedy
is not always a split: a generated artifact stays whole by nature (documented
as such), and VENDORED third-party code's remedy is deletion/unvendoring —
name the actual remedy in the entry.

**`CONFIG_FILES` seeding:** genuinely config-centric modules only — a file
that is mostly algorithm with one small table stays OUT; when in doubt, keep
the seed narrow and record the judgment in the report/OPEN-QUESTIONS.

**Guard scope note:** `test_config_sections.py` checks MODULE-LEVEL statements
only. A config-like table living inside a class body is invisible to it — that
is itself a placement smell: lift it to a module-level config (a refactor
candidate), never force-add the file to `CONFIG_FILES` where the guard cannot
check anything.
`test_config_sections.py` carries the same mechanism (a `PATCHING_RATCHET`) for
legacy post-definition patching that cannot be folded in without behavior risk.

**Autonomous-session protocol:** a pre-authorized autonomous run that hits a
genuine violation it cannot safely fix MAY add a ratchet entry marked
`pending owner ratification`, and MUST surface it at the TOP of its final
report. The owner then ratifies it (entry stays, properly owed) or rejects it
(the next session fixes the violation). Silently leaving a guard red is never
an option; silently ratcheting without surfacing is a defect.

**`tests/run_guards.py`** — a small wrapper that runs the four tests via
`pytest.main`, prints failures to stderr, and exits **2** on failure (exit 2 is
what makes a hook BLOCKING). A project whose environment has no pytest may
call the guard functions directly instead — the contract (exit 2, stderr,
speed) is what matters, and the test files stay pytest-discoverable. It must stay fast (< ~2 s) and deterministic —
guards only, never the full app suite. When the project's own suite already
lives elsewhere (e.g. `support/tests/`), the guards still live in a root
`tests/` of their own — the hook contract and the speed budget demand it.

**Guard tree-scanning note:** when a project's guards scan `.py` sources, the
guard modules themselves (`tests/`) match — exclude the guards' own directory
in `iter_source_files()`/tier classification, or the suite flags itself.

**Guard self-test rule:** a newly installed or modified guard must be SHOWN
failing on a planted real violation and then passing after its removal — never
merely "installed". A guard that cannot even be collected reports success by
never running (a real, observed failure mode). **Plant-revert safety:** undo a
plant by removing exactly what you planted (or commit legitimate edits BEFORE
planting) — never `git checkout -- <file>` on a file carrying uncommitted real
work; it reverts to HEAD, not to "before the plant" (a real, observed
mistake).

**Claude Code hooks — `.claude/settings.json` in every project:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "python tests/run_guards.py --fast" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python tests/run_guards.py" }
        ]
      }
    ]
  }
}
```

- **PostToolUse** (`--fast`: structure + config-sections only) bites the moment
  a file is saved — the agent gets blocking feedback immediately, not at build
  time. The wrapper reads the hook JSON on stdin and **exits 0 immediately for
  non-source files** (docs edits must not pay the guard cost hundreds of times
  in a docs session).
- **Stop** runs all four guards — the agent literally cannot declare the work
  finished while a guard is red.
- Non-Python projects implement the same four guards in their own stack; the
  hook contract (fast, deterministic, exit 2 = block) is identical.

What the teeth CANNOT bite (honesty): "this logic semantically belongs in that
other module" is not machine-checkable. The guards catch the worst, most common
violations (end-of-file dumps, post-definition patches, god-files, missing/broken
docs). The rest is on the session's discipline — and the owner's review.

---

<a id="core-rules"></a>

## Core Code Rules

### No Error Masking

Errors MUST be visible. Never hide problems with silent fallbacks.

```python
# ❌ FORBIDDEN                       # ❌ FORBIDDEN — silent default
except Exception:                    except Exception:
    pass                                 result = default_value

# ✅ REQUIRED
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

Fallbacks are acceptable ONLY as explicitly documented behavior ("returns None
if not found") or retry logic with eventual escalation. GUI apps catch uncaught
exceptions at the top level and write them to the log — never silently swallow.

### No Hardcoded Values

All thresholds, dimensions, colors, paths and tunable values live in the
project's config file — no magic numbers in other files. Hardcode only what
NEVER changes (`PI`), enum values, loop counters. Unsure → ASK.

### No Duplicate Code

Before any new class/method ask: does similar functionality exist? Will more
classes like this come? Extract a base class or shared utility instead of
writing the same logic twice.

### No Backward Compatibility

When refactoring: Grep ALL callers → update EACH → DELETE the old path. Never
keep wrapper methods "for compatibility".

### No Defensive Programming for Impossible Scenarios

Trust initialization and internal guarantees; let impossible scenarios fail
loudly. Defensive code belongs ONLY at real boundaries: external input, file
I/O, network, database, OS APIs.

### Progress Logging for Long Tasks

Any long-running operation logs progress every N items: elapsed time,
processed/total, percentage, rate. Silent long loops are forbidden.

### Logging (scaled to the project)

Python: `logging` module, `logs/` folder, rotating handler. Every application
needs SOME error visibility; not every gadget needs a full log system.

---

<a id="compute"></a>

## Compute, Don't Generate (owner decree 2026-07-20)

The power of a program is that a small set of rules covers every situation —
chess is defined by movement rules, not by enumerating games. An asset is
GENERATED only when it is irreducibly artistic; every variant of it is COMPUTED.

Before ANY asset enters a prompt sheet, a generation queue, or the repo, answer
the **derivation check in writing**: can this be derived from ONE master + rules?
Tint/metal (recolor), lighting/shadow (angle math), phase/fraction (geometry),
orientation/position (transforms), size (scaling) — NEVER separate images. Only
the irreducible core (new scene, new figure, new composition) is generated; the
program derives the rest live, disk-cached. Legacy sheets are re-asked this
question BEFORE regenerating from them.

---

<a id="profiling"></a>

## Profiling — Python CPU (py-spy)

Sampling profiler, attaches to a running process (`pip install py-spy`).

1. **Find the PID:**
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, CommandLine | Format-List
   ```
2. **Live monitor:** `py-spy top --pid <PID> --rate 100` — wait for the state
   under investigation.
3. **Read:** `%Own` = time in the function itself; `%Total` = including callees;
   follow the chain bottom-up to the root caller.
4. **Flame graph:** `py-spy record --output profile.svg --pid <PID> --duration 30`.

`top` accumulates since process start — restart the app and measure a short,
focused window for clean results. Genuinely idle = all functions 0.00%.
