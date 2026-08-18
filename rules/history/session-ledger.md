# Deliverable line, session task list, REPEAT teeth, loud incompleteness, final report — the stories

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

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
  **And it carries its head (owner decree 2026-08-08):** the line names WHAT
  is being waited for (`WAITING_ON_OWNER: yes — <the awaited decision>`),
  and the turn's chat text actually ASKS it — a full question block, not two
  words. Born from his screenshot: *"vidim da si stao opet — zašto?"* — an
  agent that "waited" on him without a question he could answer.
- **A message the owner sends mid-session joins the list in the same turn
  (owner decree 2026-08-08).** The list is updated after EVERY owner
  message — new `- [ ]` tasks, changed statuses, or a restamped WAITING
  line. A list that froze at its opening state is how his instructions get
  lost in the scroll.
- The file is per project and per session: refreshed when the owner opens with
  a new list, removed (or fully checked) when the list is done. `.claude/` is
  excluded from the doc guards — this is harness state, not product docs.
- Class: **GATE** — machine-enforced by `rules/hooks/session_tasks_guard.py`
  (Stop hook, wired machine-wide in `~/.claude/settings.json`): ending a
  session with unchecked tasks and no `WAITING_ON_OWNER: yes` is blocked, with
  the open tasks fed back. Since 2026-08-08 the same hook also blocks: a
  `yes` with no reason on its line; a `yes` whose turn asked nothing (no
  question mark, or under the 700-char full-block minimum — fail-open when
  the harness has not flushed the turn's text yet); and a task list saved
  BEFORE the owner's last message (his words were not folded in).

### THE REPEAT LAW's teeth (owner decree 2026-08-07)

**A third checkbox exists, and it is the honest one:**

    - [ ] not done
    - [~] SHIPPED — gated, released, and HE has not seen it work yet
    - [x] done, on his confirmation or on evidence from HIS machine

**Why.** The owner spent a week being told ten tasks were done and finding
half of them unchanged. Nobody lied: "done" had drifted to mean *my own test
is green*, and a test written by the same reasoning that produced the bug
cannot falsify that reasoning. The record shows it plainly — one bug carried
four task numbers and four `[x]` across four rounds, and the guard that
"proved" the last one had **pinned the defect as the intended behaviour**.
One whole class of repeat was not a code bug at all: he was running a build
published before the fix, because the app asked GitHub once per start. Ten
green gates cannot beat an app he never installed.

- **A repeat is a PROCESS failure first.** When the owner reports something a
  previous round closed, the round's first deliverable is `PROCESS CAUSE:` —
  what was claimed, what the claim rested on, and why that evidence could be
  green while the app was broken. Then the code. — **LAW**
- **A REPEAT task may be `[x]` only with `OWNER CONFIRMED` or
  `HIS EVIDENCE:`** (his log, his installed binary, his screenshot, his word).
  Otherwise `[~]`, carried into the next round's report until he closes it.
  — **GATE**, enforced by the same hook, which blocks on a `REPEAT` block with
  no `PROCESS CAUSE:` and on a `[x]` REPEAT with no evidence of his.
- **`[~]` is not a demand that he test everything.** It applies to what he
  REPORTED and we claim to have fixed — nothing else. A round still ships,
  still closes, still releases; it simply stops calling a thing proven when
  the only witness is its own author.
- **Before believing a report is stale, check what he is RUNNING.** The
  installed binary's version against the latest release answers "is this a bug
  or an undelivered fix" in one command, and it is the cheapest question in
  this monorepo. — **LAW**

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
   and are never the report's source of truth. Since 2026-08-08 this has
   teeth: the session-tasks guard blocks a turn whose list is older than the
   owner's last message.
4. **The owner may demand the report AT ANY MOMENT mid-session (owner decree
   2026-08-08)** — "gde smo?", "šta je urađeno?" — and the answer is the
   SAME per-task shape (status + evidence per task, NOT DONE first),
   rendered in chat, without ending the session. A hook cannot recognize
   the demand in his words, so this half stays a LAW of conduct; the
   end-of-session half is machine-enforced above.

---

