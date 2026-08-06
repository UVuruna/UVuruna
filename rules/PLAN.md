# PLAN — Brainstorming & Planning Rules

**Who reads this:** sessions that think WITH the owner — brainstorming, idea
shaping, direction choices, implementation planning. (Init/context-gathering
sessions too — see Read-Only on Init.)

## Table of Contents

- [Plans Are Discussions](#plans)
- [The Deliverable Line](#deliverable)
- [The Session Task List](#session-tasks)
- [Present Before Building](#present)
- [Communication with the Owner](#communication)
- [Constructive Disagreement](#disagreement)
- [Read-Only on Init](#init)
- [Rule Classes — Law / Gate / Style](#rule-classes)
- [Owner Guardrails](#guardrails)

---

<a id="plans"></a>

## Plans Are Discussions

- A plan explains WHAT will be done and WHICH files change — it is
  brainstorming, not a code preview
- Do NOT write full code blocks in plans that will later be copied into files
- Before starting any work: read the task carefully, identify ambiguities, read
  the relevant docs (`___folder.md`, `__about/`), ASK about everything unclear
  ("Should I modify X or create new?", "You said Y — did you mean Z?"), propose
  the approach, and START ONLY AFTER CONFIRMATION

---

<a id="deliverable"></a>

## The Deliverable Line (owner decree 2026-08-05)

**The FIRST line of every session names what the session ships.** It stands
beside the triage class, before any tool runs:

    ISPORUKA: kod = <what lands in the repository> · dokument = <what is written>

Either half may be `—`, and saying so is the point: a session that ships only a
document has declared that, and a session that ships code cannot quietly
substitute a document for it at the end.

**Why this rule exists.** A session was asked to design a registry — its shape
agreed in the same conversation, down to the package split and Python over JSON
— and to *describe it* on a rendered page once the design was settled. The agent
built the page, presented it as the deliverable, reported the work finished, and
when challenged called the gap a mutual misunderstanding. It was not: the agent
had taken the LAST artifact named in the request as the goal instead of the
FIRST, and the description of a thing is never the thing.

- **The line is written before the first tool call**, so it cannot be shaped
  after the fact by whatever was easiest to finish.
- **A document that describes the code is `dokument`, never `kod`.** A brief, a
  page, a diagram, a prompt sheet — none of them discharge a code deliverable.
- **Finishing means the declared line is true, both halves.** If one half turns
  out to be blocked, FIXED = VERIFIED applies to it by name: say which half, and
  why.
- Class: **GATE** — machine-enforced by `rules/hooks/communication_guard.py`,
  which blocks the first file-mutating tool call of a session until the line has
  been written.

---

<a id="session-tasks"></a>

## The Session Task List (owner decree 2026-08-05)

**When the owner opens a session with a defined task list, that list is pinned
in a file at the START and the session cannot end until it is finished.** The
agent writes the list to the project's `.claude/session-tasks.md` before any
other work:

    WAITING_ON_OWNER: yes|no
    - [ ] task as the owner defined it …
    - [x] finished task …

**Why this rule exists.** Sessions repeatedly drifted into pure conversation —
the owner opened with concrete tasks, the discussion ran long, and the agent
came to treat chatting as the job, losing the original list entirely. The owner
had to re-demand work he had already defined.

- **A task is checked ONLY when FIXED = VERIFIED** (root CLAUDE.md → The Laws):
  root cause named, fix landed, evidence shown. Never for a symptom patch or a
  promise.
- **`WAITING_ON_OWNER: yes` is legal only when the turn genuinely ends with
  questions or a presentation the owner must answer** — it goes back to `no`
  the moment work resumes. It is the ONLY way to end a turn with open tasks.
- The file is per project and per session: refreshed when the owner opens with
  a new list, removed (or fully checked) when the list is done. `.claude/` is
  excluded from the doc guards — this is harness state, not product docs.
- Class: **GATE** — machine-enforced by `rules/hooks/session_tasks_guard.py`
  (Stop hook, wired machine-wide in `~/.claude/settings.json`): ending a
  session with unchecked tasks and no `WAITING_ON_OWNER: yes` is blocked, with
  the open tasks fed back.

### Loud Incompleteness (owner decree 2026-08-05)

**Anything not fully done is announced LOUDLY, never slipped past in
mid-text.** Born from a real breakdown: a session reported a large rework as
finished and mentioned only in passing, deep inside the report, that two items
were "recorded as debt" — and both debt claims were WRONG (the agent had not
looked at the assets folder, and had misnamed an element that exists). The
owner reads reports diagonally; a quietly buried "nisam" is functionally a
lie.

1. **The final message of any working session OPENS with a section titled
   "NISAM URADIO" (or "NOT DONE")** listing every item that is unfinished,
   partial, deferred or reinterpreted — BEFORE any successes are described.
   No such items → the section says so in one line. — **LAW**
2. **Every debt, the moment it is recorded, is ALSO appended to
   `.claude/session-tasks.md` as an open `- [ ]` task** in the same commit
   that records it. The session-tasks guard then physically refuses to end
   the session silently — the owner sees the debt as an open task, not as a
   footnote. — **GATE** (rides the existing session-tasks teeth)
3. **A debt claim must name the EVIDENCE looked at** ("checked assets/x/, no
   art exists"; "grepped render/, no such element") — a debt without evidence
   is a guess, and a wrong guess about "impossible" is the costliest lie of
   all: it cancels planned work. Misunderstandings are asked about LOUDLY at
   the moment of doubt, never resolved silently into a debt.

### The Final Report (owner decree 2026-08-06)

**A session that delivered may not end until it has WALKED ITS OWN TASK LIST
in a report the owner can read diagonally** — per task: status + evidence,
then the release. Born the same day the session-tasks teeth already existed
and still failed him: the work was done, the tasks were checked, and the
closing message was so shapeless the owner could not tell WHAT had been done
at all ("nemam pojma ni dal si uradio ni šta si uradio"). Finishing the work
and saying what happened to each task are two different obligations; this one
gates the second.

1. **The final message of a delivering session IS the report**: the NOT DONE
   section first (Loud Incompleteness), then every task from
   `.claude/session-tasks.md` with its status — `DONE | PARTIAL | BLOCKED |
   NOT DONE` — and its evidence (commits, tests run and their results, files,
   measurements), then the release link when one shipped. Rendered readably
   (tables/sections), not as a raw file dump. — **LAW**
2. **The same report is mirrored to `.claude/session-report.md`**, stamped
   with the session id, before the session ends:

       SESSION: <session id>
       RELEASE: <release URL | none — why no release>
       - [x] <task text as in session-tasks.md> — DONE — <evidence>
       - [ ] <task text> — BLOCKED — <why + what would unblock>

   One line per task, the task text copied verbatim so the guard can match
   it; the evidence tail is NOT optional — FIXED = VERIFIED applies to a
   report line as to any claim of finished work. A fresh session writes a
   fresh report; an earlier session's file never carries over. — **GATE**,
   machine-enforced by `rules/hooks/report_guard.py` (Stop hook, wired
   machine-wide in `~/.claude/settings.json`): when every task is checked and
   the turn is not `WAITING_ON_OWNER: yes`, ending without a session-stamped
   report that covers every task with status + evidence + a RELEASE line is
   blocked, with what is missing fed back. While tasks are still open, the
   session-tasks guard is the wall — this gate takes over at the finish line.
3. **Tasks the owner adds mid-session join the list the moment they are
   given** — appended to `.claude/session-tasks.md` as `- [ ]` in the same
   turn, so the report at the end covers them exactly like the opening tasks.
   The session tracks the LIST; the owner's scratch files (`UV/`) are his own
   and are never the report's source of truth.

---

<a id="present"></a>

## Present Before Building (owner decree 2026-08-01)

Before implementing, the agent shows how it UNDERSTOOD the task. The obligation
scales with the triage class AUTOMATICALLY — the agent never asks whether a
sketch is wanted; the class decides:

| Task class | Before implementation |
|------------|----------------------|
| **Trivial** (small fix, mechanical change) | Nothing — one sentence of intent in the response |
| **Standard — new functionality / algorithm** | **Algorithm sketch**: VISUAL (box-drawing sketch in chat; rendered Artifact/HTML page when complex — see [Communication](#communication)) + detailed prose walkthrough + why this approach + how the instructions were understood + what is unclear → wait for the owner's yes |
| **Standard — new or changed GUI element** | **Layout sketch**: VISUAL wireframe (box-drawing in chat; rendered Artifact/HTML when complex) + prose explanation → wait. Mermaid source belongs only in `__flow/` doc files ([Docs Rules](DOCS.md)), never in chat |
| **Wide** (big task, many instructions) | **Echo-brief**: ALL instructions regrouped into cohesive wholes + "this is how I understood everything" + open questions → work starts only after confirmation |

- **The approved sketch is not throwaway work:** after implementation it seeds
  the file's `__flow/` doc — written once, used twice.
- This pairs with Owner Guardrail #5 (vocabulary mix-ups): the sketch is the
  mechanism that catches a misunderstanding at the cost of one message instead
  of one implementation.
- **Pre-authorized autonomous runs** cannot wait for a yes: the sketch /
  echo-brief goes into the final report instead (same precedent as the
  MIGRATE-DOCS target map).
- Class: **GATE** — a Definition-of-Done item in every task brief.

<a id="communication"></a>

## Communication with the Owner (owner decree 2026-08-02)

Born from a real breakdown: an agent pasted raw Mermaid into chat (the owner's
interface shows diagram source as unrendered garbage) and asked three one-line
questions with zero explanation — total mutual incomprehension, a session spent
on apologies instead of progress. Both patterns are now banned and enforced.

1. **A visual is OBLIGATORY, and it must render in the owner's eyes — LAW.**
   Presenting an algorithm, a GUI element, or a config-file structure ALWAYS
   carries a visual representation next to the detailed prose walkthrough
   (numbered steps, full sentences, in Serbian) — visuals are the default,
   never a rarity to be avoided. The MEDIUM scales with complexity:
   - **Simple** → a Unicode box-drawing / ASCII sketch directly in the chat
     message (plain text renders as-is in every interface — this is what
     "rendered normally" for the owner before).
   - **Complex** → a RENDERED page the owner opens: an Artifact or an HTML
     file — real diagram, not source.
   - **A rendered page commits to ONE explicit color scheme — LAW (owner
     2026-08-03).** Born from a real breakdown: a proposal page styled with
     adaptive light/dark theme tokens (`prefers-color-scheme` media queries /
     host theme stamping) rendered as white-on-white garbage in the artifact
     viewer — the host displayed the light palette inside a dark shell. A
     rendered page NEVER relies on the viewer's theme detection: it declares
     one scheme (dark, matching the owner's environment, unless he asks
     otherwise) and sets background AND text color together, explicitly, on
     the page body — never inheriting either half of the pair from the host.
   - **NEVER** Mermaid/graphviz source pasted into a chat message — the
     owner's interface shows it as raw code garbage. Diagram source lives only
     inside doc FILES (`__flow/`, per [Docs Rules](DOCS.md)), where viewers
     render it.
2. **Detailed questions only — LAW.** Every question to the owner is a full
   block: (a) context — what the agent is working on and where the decision
   arises, (b) the question itself in complete sentences, (c) why it matters
   and what depends on the answer, (d) the options with their concrete
   consequences, (e) the agent's recommendation. FORBIDDEN: enumerated
   one-liners — "(1) ok? (2) ok? (3) ok? — give me a YES". A question the owner
   cannot understand without asking back is a defect, not a question.
3. **Teeth:** `rules/hooks/communication_guard.py`, wired MACHINE-WIDE in
   `~/.claude/settings.json` (applies in every project, no per-project
   migration). The Stop hook blocks ending any turn whose chat text contains
   diagram source or a terse enumerated ask; the PreToolUse hook on
   AskUserQuestion blocks questions below minimum substance (question ≥ 100
   chars of context, every option description ≥ 40 chars of consequence); the
   PreToolUse hook on Artifact (added 2026-08-04, after the white-on-white
   law of 2026-08-03 was violated AGAIN by an agent following generic
   artifact styling guidance over this rulebook) blocks publishing any page
   whose stylesheet contains adaptive theme tokens (`prefers-color-scheme`,
   `data-theme`) or that never sets its own background — the page must carry
   ONE fixed explicit scheme.
   Honesty note: the hook measures substance by length — whether an
   explanation actually EXPLAINS stays on session discipline and the owner's
   review.

---

<a id="disagreement"></a>

## Constructive Disagreement

If a proposed approach is suboptimal, the agent MUST: (1) explain WHY with
concrete technical reasons, (2) propose an alternative, (3) ask for confirmation
after the trade-offs are understood. Blind acceptance is a defect:

```
❌ Owner: "Let's read the TOP 50 twice"  → Agent: "OK."
✅ Agent: "I see a problem: the list already contains all the data — reading it
   twice wastes resources. Proposal: read once. Agreed?"
```

Better a short pause for discussion than an inefficient build that must be
undone.

---

<a id="init"></a>

## Read-Only on Init

When a session starts in a project to gather context: READ the docs
(`CLAUDE.md`, `README.md`, relevant `___folder.md`) — do NOT propose
improvements, additions or modifications unprompted. Init is context gathering,
not a review.

---

<a id="rule-classes"></a>

## Rule Classes — Law / Gate / Style

Written rules that nothing enforces do not hold (proven repeatedly in this
monorepo). When the owner proposes a NEW rule, the planning agent asks:
**"What check guards it?"** and classifies it:

| Class | Meaning | Home |
|-------|---------|------|
| **LAW** | a guard test / hook fails the build or session on violation | guard tests + hooks ([CODE](CODE.md) → Enforcement) |
| **GATE** | checked at end of work (Stop hook, checklist, Definition of Done) | task briefs, hooks |
| **STYLE** | advisory; kept to ONE sentence | rules files |

A rule that cannot become a LAW or GATE is written as a single STYLE sentence —
or not at all.

---

<a id="guardrails"></a>

## Owner Guardrails (living list — owner decree 2026-08-01)

The owner explicitly asks to be PROTECTED from his own known mistakes. When a
planning session sees one of these patterns, it is the agent's DUTY to warn —
clearly, before work starts. Warning is not disobedience; silence is.

1. **GUI before functionality.** Visual polish requested before the logic is
   feature-complete → point to the Logic-Before-Looks law ([GUI](GUI.md)) and
   propose finishing functionality on the minimal GUI first.
2. **New project before the duplication check.** Founding a project without
   first checking whether an equivalent already exists — in the monorepo or as
   available software ([START](START.md) → Step 1).
3. **New project before the feasibility check.** Entering a build without
   naming the hard part and how it will be handled; when feasibility is
   unknown, the first milestone is a throwaway probe ([START](START.md) → Step 1).
4. **Tech insistence against engineering reality.** When the owner insists on a
   technology that is infeasible or clearly inferior for the task, the agent
   must lay out the technical reality and alternatives — NEVER silently accept.
   (Constructive Disagreement, escalated: here the agent warns even without
   being asked for an opinion.)
5. **Vocabulary mix-ups.** The owner's wording is sometimes imprecise; if a
   request contains an apparent illogic or contradiction, assume a possible
   word mix-up and ASK — "did you mean X?" — before acting on the literal
   reading.
6. **Generating what can be computed.** An asset request that skips the
   derivation check ([CODE](CODE.md) → Compute, Don't Generate).
7. **Rules without teeth.** A new rule proposed with no enforcement — apply
   [Rule Classes](#rule-classes).

The owner adds new guardrails as he identifies them; sessions may PROPOSE
candidates (at the end of work, never mid-task).
