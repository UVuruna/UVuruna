# Delegation, agents are not daemons, the solo-work guard — the stories

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="delegation"></a>

## Delegation Is Not a Question (owner decree 2026-08-06)

**Once a round's verdicts are settled, starting the approved work is the
agent's job, not the owner's.** A big task is EXECUTED BY AGENTS — each job
its own agent session, the weakest capable tier — while the session only
coordinates and reports. The coordinator designs the roster (job, tier,
exact files, structured deliverable), presents it, and LAUNCHES the first
wave in the same message. Ending a turn by asking the owner "do I start
now, or in a fresh session?" is the exact drift this rule exists to stop —
it happened the very day the verdicts of a Wide round were fully settled,
and a memory note recording the same lesson had already failed to hold.

- A genuine CONTENT question (a verdict the owner truly owns) still ends a
  turn lawfully with `WAITING_ON_OWNER: yes`. A SCHEDULING question never
  does — that flag is for decisions only the owner can make, and the
  calendar is not one of them.
- Class: **GATE** — machine-enforced by `rules/hooks/delegation_guard.py`
  (Stop hook, wired machine-wide in `~/.claude/settings.json`): ending a
  turn whose chat text asks whether/when to start while open tasks remain
  in `.claude/session-tasks.md` is blocked, in either language.

<a id="agents-not-daemons"></a>

## Agents Are Not Daemons (owner decree 2026-08-06)

**The session that launches agents OWNS them** — months of established
practice, broken the very evening the delegation rule landed: a coordinator
fired background agents per project and moved on; nobody could say which
agents ran, what they were doing or when they finished, and the owner
learned of them from windows flashing over his work and from phone
notifications he could not attribute.

1. **A visible roster before launch** — who (tier), what job, which files —
   per [Delegation Is Not a Question](#delegation); launching is the
   coordinator's job, but launching UNTRACKED is abandonment, not delegation.
2. **A ledger while they run** — `.claude/agents-ledger.md`, one line per
   agent: `- [ ] <tier> - <job> - RUNNING - started <when>`, flipped to
   `DONE - <evidence>` when its result is COLLECTED and verified, or to
   `HANDED OVER - <exact state + where + how the owner checks>` when the
   owner explicitly takes it.
3. **No ending with a running agent.** Wait and collect, or hand over
   loudly. Every agent inherits [Silent Audits](../GUI.md#silent-audits) — an
   agent that flashes windows over the owner's desk is a defect of its
   COORDINATOR.
- Class: **GATE** — machine-enforced by `rules/hooks/agents_guard.py`
  (Stop hook, machine-wide): a session whose transcript launched subagents
  cannot end unless the ledger names the session, accounts for every
  launched agent, and holds no RUNNING line.

---

### THE SOLO-WORK GUARD (GATE, owner decree 2026-08-09)

A ten-hour session opened with one instruction — *lead the work, engage other
agents, verify them* — and ran to its end without launching a single one. It
was reported to him as an observation, ten hours late, after the application
had been degraded to the point of being unusable. His ruling:

> *"ako sam ti rekao da angažuješ agente, ni slučajno ne smiješ da radiš sam i
> 1 zadatak koji uradiš sam"*

**Two guards already looked like this one and neither owned the question.**
`agents_guard.py` blocks a session from ENDING while agents it launched are
still running — it guards agents that EXIST. `delegation_guard.py` blocks a
turn that asks the owner WHEN to start approved work — it guards one question.
A session that quietly does everything itself, launches nothing and asks
nothing, passes both. That gap is the whole reason this gate exists, and it is
worth remembering as a shape: *a rule can have two guards and still have none.*

`rules/hooks/solo_work_guard.py` (Stop, machine-wide) blocks a turn that WROTE
product files and launched NO agent, in any project carrying
`.claude/delegation-required`. Reading, measuring, running gates, the task
list, the proofs and the reports are always free — those are the coordinator's
own job and delegating them would delegate the thing he asked for personally.

Self-tested against eight cases, including the two that must NOT block (an
agent was launched; only bookkeeping was written) — a gate that cannot pass is
as useless as one that cannot fail.
