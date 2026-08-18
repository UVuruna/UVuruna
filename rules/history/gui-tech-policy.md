# GUI stack policy — the story

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="stack"></a>

## Stack Choice for GUIs

The design LANGUAGE in DESIGN.md (dark-first, tokens, soft depth, typography)
is **stack-agnostic** — it does not mandate any library. For NEW projects the
stack comes from the default decision tree in [START](../START.md) → Technology
Selection (C# + WPF front by default; Python only as worker processes behind
IPC) — departures need the written justification there. DESIGN.md carries
recipes for stacks already in use (Qt, web); a new stack gets its recipe
section on first use.

---


---

## The decree behind it (owner decree 2026-08-04)

C# + WPF is the default FRONT for NEW projects; Python survives only as worker
processes behind IPC. Existing Python GUIs migrate only on the owner's explicit
go, project by project — the queue named that day was PromptPainter, Watch
Academy, Aviator, RHMH — through the four phases of
`rules/briefs/MIGRATE-GUI.md`, whose first phase (responsiveness verification)
is worth running even when no migration follows.
