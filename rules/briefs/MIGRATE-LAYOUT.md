# Migrate Layout — Task Brief

A **copy-paste task brief**: give an EXISTING GUI project the teeth of THE SPACE
& LEGIBILITY LAW (`rules/GUI.md`) — the static guard, the runtime layout audit,
and the fixes their first run demands.

**The runner is central now.** `rules/tools/uv.py` owns the screenshots, the
profiles and the ALG checks (`rules/templates/layout_checks_qt.py` / `_tk.py`);
a project only registers its windows in `.claude/uv_windows.py` (`TOOLKIT` +
`WINDOWS = {name: factory}`) and declares its mandatory `profiles:` in its
`CLAUDE.md`. So the steps below shrink to: static guard, window registry,
computed minimums, first-run fix list, wire `run_guards`.

## Table of Contents

- [Candidate Queue](#queue)
- [Step 1 — Static Guard](#step-1)
- [Step 2 — The Window Registry](#step-2)
- [Step 3 — Computed Minimums](#step-3)
- [Step 4 — First Run: the Fix List](#step-4)
- [Step 5 — Wire the Teeth](#step-5)
- [Hard Constraints](#constraints)
- [Definition of Done](#done)

---

<a id="queue"></a>

## Candidate Queue

Every project with a GUI is a candidate. Each waits for the owner's explicit go
— **nothing here starts on its own.**

| Project | Status |
|---------|--------|
| _(filled per owner go)_ | — |

---

<a id="step-1"></a>

## Step 1 — Static Guard (minutes)

Copy `rules/templates/test_layout_law.py` to the project's
`tests/test_layout_law.py` and set `GUI_DIRS` to the project's real GUI folders.

Run it. Every hit is a CAUSE of one of the two bugs — an elide call, a forced
scrollbar, a hard size on something that carries text. Fix what is fixable in
the session; what genuinely cannot be fixed now goes into `RATCHET` with the
file, the reason, and who owes the fix — the same discipline as the STRUCTURE
LAW ratchet ([Code Rules](../CODE.md) → Enforcement), and the list may only
shrink.

---

<a id="step-2"></a>

## Step 2 — The Window Registry (the real work)

Copy the runtime audit for the project's stack — `test_layout_audit_qt.py`
(PySide6/PyQt) or `LayoutAuditTests.cs` (C# + WPF) — and fill in its registry
with EVERY top-level window and dialog.

**A factory builds its window in the fullest realistic state it will ever
show** — longest real strings, most rows, every optional panel expanded. An
empty window passes any audit and proves nothing; the bug on the owner's
screenshot only appears with real content in it.

A window missing from the registry is a hole in the guard. List them from the
code (every `QDialog`/`QMainWindow` subclass, every `Window` in XAML) and say in
the report how many there are and how many are registered.

---

<a id="step-3"></a>

## Step 3 — Computed Minimums

The audit refuses a window with no declared minimum size, and that refusal is
the point: **the minimum is computed from measured content, never a guessed
round number.** For each window, derive it from the fullest state (the widest
real row, the tallest real content), set it (`setMinimumSize` / `MinWidth` +
`MinHeight`), and record the numbers in the component's docs — the next session
must be able to see where they came from.

---

<a id="step-4"></a>

## Step 4 — First Run: the Fix List

The first audit run produces the real work. Every failure is fixed in the
ladder's order — a later step is legal only when the earlier ones are exhausted:

```
1. TAKE THE FREE SPACE   the starving element gets the stretch; a spacer,
                         a filler or a trailing stretch NEVER outranks
                         content that does not fit
2. REFLOW                wrap the text, break the row into several rows,
                         make neighbours with slack give it up first
3. RAISE THE MINIMUM     computed, not guessed; the window can no longer
                         be shrunk below it
4. SCROLL                last, and only when the window is genuinely full
                         in that axis
```

Then the DESIGN REVIEW, on every window, in the same session: the audit writes
`.claude/shots/<Window>.png` at the minimum size — **open it with the Read tool,
look at it, and grade it 1–10 against [DESIGN.md](../../DESIGN.md).** Below 8/10 the
work is not done: fix what the picture shows, re-shoot, re-grade. The owner
pointing at a screenshot and saying "this is a 2 out of 5" is what this step
exists to prevent, and the Stop hook verifies the image was really opened.

**Suppressing a failure is not fixing it.** Widening a tolerance, dropping a
window from the registry, or ratcheting a runtime failure are all ways of
reporting a bug as solved — forbidden by FIXED = VERIFIED
([CLAUDE.md](../../CLAUDE.md) → The Laws). `RATCHET` exists for the STATIC guard's
legacy hits only; the runtime audit has no ratchet by design.

---

<a id="step-5"></a>

## Step 5 — Wire the Teeth

1. Add both tests to `tests/run_guards.py` — the static one to `--fast`
   (it is a grep, it costs nothing), the audit to the full Stop run.
2. Confirm the project's `.claude/settings.json` hooks run the wrapper
   ([Code Rules](../CODE.md) → Enforcement).
3. **Guard self-test** (mandatory, same rule as every other guard): plant a real
   violation — an elide call, or a scroll area next to a live spacer — SHOW the
   guard failing on it, remove the plant, show it passing. A guard that was
   never seen failing reports success by never running.

---

<a id="constraints"></a>

## Hard Constraints

- **The owner's explicit go, per project.** This brief never starts on its own.
- **No suppression** — see Step 4. Tolerances stay at the template's values
  unless the owner approves a change, in writing, with the reason.
- **The modern visual bar stays** ([DESIGN.md](../../DESIGN.md)). A window made ugly
  or empty to satisfy the audit has failed the task: the ladder's steps 1–3 are
  layout work, not design surrender.
- **Minimum sizes live in the docs**, with the content they were computed from.

---

<a id="done"></a>

## Definition of Done

A session under this brief ends in one honest state per FIXED = VERIFIED
([CLAUDE.md](../../CLAUDE.md) → The Laws): both guards installed and SHOWN failing on
a planted violation then passing, every window registered (or the unregistered
ones named with the reason), every audit failure fixed by the ladder, minimums
computed, fitting 1280×720 and documented, every window's screenshot opened and
graded ≥ 8/10, `.claude/layout-proof.md` written for the session, docs
of everything touched updated, and commits per the version system.
