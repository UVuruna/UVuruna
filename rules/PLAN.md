# PLAN — thinking with the owner

Brainstorming, direction choices, implementation planning, research, init.
A PLAN session is READ-ONLY on product code.

## Plans are discussions

- A plan explains WHAT will be done and WHICH files change — never a code
  preview; no full code blocks that will later be copied into files. · STYLE.
- Before any work: read the task, name the ambiguities, read the relevant docs
  (`___folder.md`, `__about/`), ASK about everything unclear, propose the
  approach, and start only after confirmation. · conduct.
- **Read-only on init** — a session gathering context reads `CLAUDE.md`,
  `README.md` and folder docs and does NOT propose improvements unprompted.

## Communication with the owner

1. **A visual is OBLIGATORY** whenever an algorithm, a GUI element or a config
   structure is presented: simple → Unicode box-drawing sketch in the chat
   message; complex → a RENDERED page (Artifact/HTML) he opens. · `gate.py stop`.
2. **NEVER Mermaid or graphviz source in a chat message** — his interface shows
   it as garbage. Diagram source lives only in `__flow/` doc files. · `gate.py stop`.
3. **A rendered page commits to ONE explicit color scheme** — dark by default,
   background AND text set together on the body; never `prefers-color-scheme` or
   host-theme tokens. · `gate.py pre` on Artifact.
4. **A page that PROPOSES is a BALLOT** — a tick box per option (grouped when
   the options exclude each other, freely multi-selected when they combine), a
   comment field under EVERY option, and a closing block with a free-text
   instruction field, a **Copy verdict** button and a plain-text verdict box;
   selections survive a reload. Reference: `rules/templates/decision_page.html`
   — keep the `data-option` / `data-group` / `#ballot` contract. · `gate.py pre`.
5. **Questions are fully explained blocks** — context, the question in complete
   sentences, why it matters, the options with their concrete consequences, the
   recommendation. Never enumerated one-liners. · conduct (no length rule).
6. **Pictures arrive as LINKS, grouped by topic** — every image name is a
   clickable link, the message also links the FOLDER; targets are paths from the
   monorepo root (forward slashes, outside backticks) VERIFIED to exist on disk.
   · `gate.py stop`.

History → `history/communication-law.md`.

## Constructive disagreement

A suboptimal approach must be met with: (1) WHY, in concrete technical terms,
(2) an alternative, (3) a request for confirmation. Blind acceptance is a defect.

## Rule classes

| Class | Meaning | Home |
|-------|---------|------|
| LAW | a guard test or hook fails the build/session | guards + hooks |
| GATE | checked at the end of work | ledger, hooks, definition of done |
| STYLE | advisory, kept to ONE sentence | the rulebooks |

A new rule enters the books only with its class declared, and the planning agent
asks first: "what check guards it?". A rule that can be neither LAW nor GATE is
one STYLE sentence — or nothing.

## Owner guardrails — warn him, always

1. **GUI before functionality** — logic first, minimal GUI (`GUI.md`).
2. **New project before the duplication check** — does it already exist, here or
   as software he could install? (`START.md`)
3. **New project before the feasibility check** — name the hard part; unknown
   feasibility means a throwaway probe first.
4. **Tech insistence against engineering reality** — lay out the reality and the
   alternatives even when no opinion was asked for.
5. **Vocabulary mix-ups** — an apparent illogic is probably a word mix-up: ask
   "did you mean X?" before acting on the literal reading.
6. **Generating what can be computed** — the derivation check (`CODE.md`).
7. **Rules without teeth** — apply the rule classes above.

He adds guardrails as he finds them; sessions may PROPOSE candidates at the end
of work, never mid-task.

## Agents

- **Delegation is not a question** — once the verdicts are settled, starting the
  approved work is the agent's job; never end a turn asking whether to begin. A
  genuine CONTENT question still ends a turn lawfully as a `[?]` task.
- **Agents are not daemons** — the session that launches agents OWNS them: a
  visible roster before launch (who, tier, job, files), the `agenti:` line in
  the ledger, and no ending while one still runs. · `gate.py stop`.
- **The solo-work guard is OPT-IN** — a project carrying `.claude/delegation-required`
  blocks a turn that wrote product files and launched no agent. It stays off
  unless he asks for it in that session.

History → `history/delegation-and-agents.md`, `history/session-ledger.md`.
