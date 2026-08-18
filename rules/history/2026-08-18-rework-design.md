# Agent-work rework — design (owner verdict 2026-08-18)

Source of truth for the F1–F3 implementation. Written by the coordinating
session for the implementing sub-agents and for whoever writes rules later.
The ballot the owner accepted (all 16 options) is
`.claude/reports/agent-rework-2026-08-17.html`; its text is summarized here.

## 1. Principles

1. **Evidence is produced by a machine, timed by a hook, only looked at by the
   agent.** One runner (`rules/tools/uv.py`) writes one file per session,
   `<project>/.claude/evidence/<session_id>/evidence.jsonl`. Hooks accept only
   evidence rows that are NEWER than the last edit of a product file.
2. **The category chooses the rules and the tooth.** One line at session start
   (in the ledger): `kategorija: GUI + FEATURE · klasa: Standard · agenti: 1 sonnet`.
   Categories: `GUI FEATURE BUGFIX REFACTOR DOCS PLAN BUILD`. A session may
   carry several; each brings its tooth. No product-file edit without a
   category line (blocked at PreToolUse).
3. **Rules are checklists; stories go to `rules/history/`.** Constitution
   ≤ 6 KB, `rules/CODE.md` (shared by all code categories) ≤ 5 KB, each
   `rules/<CATEGORY>.md` ≤ 5 KB, every project `CLAUDE.md` ≤ 6 KB. Every rule
   line: WHAT · WHO CHECKS (hook / guard / runner / reviewer / nobody=STYLE) ·
   EVIDENCE.
4. **We build for others.** Device profiles in `rules/devices.json`; GUI and
   FEATURE teeth require at least one profile that is not the owner's PC.
5. **Build only on the owner's word.** Never automatic, never by a sub-agent.
   Session ends with the heading `## BUILD & RELEASE?` (question, not action).
6. **Sub-agents carry their own tooth.** A sub-agent that edited product
   files must have RUN something (uv/pytest/run_guards) after its last edit
   before it may finish; its final text carries the evidence lines. The
   coordinator's ledger references that evidence.
7. **The last text block of a turn is the whole message** (lesson from the
   Meta RayBan session 2f764c3a: the owner sees only the final block on his
   phone). Never end a turn with a one-liner after tool calls; every question
   the owner asked is answered in that final block; a turn that did work never
   ends without a message.

## 2. Files and layout (root)

```
CLAUDE.md                     constitution ≤ 6 KB
DESIGN.md                     unchanged (GUI category reads it)
rules/
  CODE.md                     shared code checklist ≤ 5 KB (read by GUI/FEATURE/BUGFIX/REFACTOR)
  GUI.md FEATURE.md BUGFIX.md REFACTOR.md DOCS.md PLAN.md BUILD.md   ≤ 5 KB each
  START.md                    kept (new project only), may stay long
  devices.json                device profiles (see §5)
  history/                    stories, decrees, this design; agents do not read
  howto/                      procedures (profiling, ship steps, ledger grammar, runner usage)
  briefs/                     MIGRATE-GUI.md MIGRATE-LAYOUT.md REFACTOR-GODFILES.md (moved from root)
  hooks/
    gate.py                   THE dispatcher: `gate.py prompt|pre|stop|subagent`
    gate/                     modules: transcript.py ledger.py language.py gui_api.py
                              build_guard.py ballot.py agents.py teeth.py evidence.py
    changed_files.py          kept (scope engine)
    (all other old *_guard.py deleted — history is git)
  tools/
    uv.py                     runner: shot | test | run | device   (F2)
    clone_guard.py            AST clone detector (used by projects' run_guards FULL)
    rules_size_guard.py       size limits for constitution / rules / project CLAUDE.md
    rename_project.py merge_session_history.py   kept
  templates/
    decision_page.html layout_checks_qt.py layout_checks_tk.py test_layout_audit_qt.py
    test_layout_law.py LayoutAuditTests.cs   kept
    ledger.md                 ledger skeleton
    project_CLAUDE.md         ≤ 6 KB project CLAUDE.md skeleton
    uv_windows.py             window registry skeleton for `uv shot`
    run_guards.py             project run_guards skeleton (changed_files gating + clone guard)
    settings.project.json     project .claude/settings.json skeleton
```

`~/.claude/settings.json` hooks after F1:

```
UserPromptSubmit  gate.py prompt          (+ VibeCoder ledger_hook prompt — product, phone)
PreToolUse        Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell|Artifact → gate.py pre
                  (+ VibeCoder agent_hook --asking on AskUserQuestion — product)
Stop              gate.py stop  (+ VibeCoder agent_hook, VibeCoder ledger_hook stop — product)
SubagentStop      gate.py subagent
Notification      VibeCoder agent_hook --asking (unchanged)
```

Project `.claude/settings.json`: PostToolUse `run_guards.py --fast`, Stop
`run_guards.py` (FULL, gated by changed_files inside the script). Nothing else.

## 3. Ledger — `.claude/sessions/<session_id>.md` (project-local, gitignored)

```
# <session title>
kategorija: GUI + FEATURE · klasa: Standard · agenti: 1 sonnet grader
- [x] T1 Card "Watch face" in Settings @fable
    ! ev-0003 shot SettingsDialog laptop-avg — looked — grade 9 (contrast ok, siblings ok, nothing clipped)
    ! ev-0004 test tests/test_settings_card.py 6/6
- [~] T2 New watch "Nautilus" @sonnet
    ! ev-0007 test 12/12 · matrix 5/6 (row phone-landscape: emulator unavailable)
- [?] T3 BUILD & RELEASE — waits for the owner's word
    ? build v0.0.288 with T1+T2? command: python setup/build.py
```

Grammar: states `[ ]` not started · `[>]` in progress · `[?]` waits for the
owner (needs a `?` line) · `[~]` done, unconfirmed/no machine evidence ·
`[x]` done WITH evidence (needs a `!` line). Indent 2 spaces per level.
`!` lines under GUI/FEATURE/BUGFIX/REFACTOR tasks reference at least one
`ev-NNNN` id from evidence.jsonl (or `commit <sha>` for pure moves);
DOCS/PLAN `!` lines are free text. Optional blocks:

```
matrica:                      (FEATURE — written BEFORE the first product edit)
| # | scenario | input/state | device | evidence |
| 1 | average device: laptop-avg start + main flow | fresh install | laptop-avg | ev-0009 |
| 2 | fresh install — no owner paths/hooks/rules used | — | pc-low | ev-0010 |
| 3 | old path removed (replacement) | grep old symbol | — | ev-0011 |
uzrok: <root cause>           (BUGFIX)
proces-uzrok: <why the previous claim was false>   (REPEAT)
```

`gate.py prompt` creates the file (from `rules/templates/ledger.md`) on the
first prompt of a session and prints its path + a 6-line grammar reminder;
later prompts print one line: `ledger: <path>`. It also writes
`.claude/evidence/current` = session_id (so `uv` knows the session).

## 4. Evidence — `.claude/evidence/<session_id>/evidence.jsonl`

One JSON object per line, written ONLY by `uv.py` (gate checks that no
Write/Edit in the transcript targeted this file):

```
{"id":"ev-0003","ts":"2026-08-18T15:02:11+02:00","kind":"shot","cmd":"uv shot --window SettingsDialog --profile laptop-avg",
 "rc":0,"profile":"laptop-avg","window":"SettingsDialog","artifact":".claude/evidence/<sid>/SettingsDialog-laptop-avg.png",
 "sha256":"3f9a…","checks":{"clipped":0,"starved":0,"min_fits":true},"summary":"ALG ok 0 clipped"}
{"id":"ev-0004","ts":"…","kind":"test","cmd":"uv test tests/test_settings_card.py","rc":0,"passed":6,"failed":0,"total":6,
 "artifact":".claude/evidence/<sid>/junit-0004.xml","sha256":"…","summary":"6/6"}
{"id":"ev-0005","ts":"…","kind":"run","cmd":"…","rc":0,"profile":"pc-low","start_ms":1840,"artifact":"…log","sha256":"…","summary":"…"}
{"id":"ev-0006","ts":"…","kind":"device","cmd":"…","rc":0,"profile":"phone-portrait","artifact":"….png","sha256":"…",
 "checks":{"h_scroll":false,"tap_targets_ok":true},"summary":"…"}
{"id":"ev-0007","ts":"…","kind":"unavailable","cmd":"uv device phone-portrait …","rc":3,"summary":"no AVD"}
```

Rules: `id` sequential per session; `ts` ISO with offset; a `kind:
unavailable` row never satisfies a tooth. `sha256` = artifact hash so a
regenerated file is a new row.

## 5. Device profiles — `rules/devices.json`

```
laptop-avg      1536x864 @125% (alt 1366x768 @100%), 4 cores → affinity 0xF, belownormal; start ≤ 3 s
pc-low          1280x720 @100%, 2 cores → affinity 0x3, low priority, software backend where it applies; start ≤ 5 s
pc-owner        no limits — reference only, never satisfies a tooth
phone-portrait  360x800 DPR 3, CPU 4x slower, Fast 3G (Playwright device emulation; APK: adb emulator screencap)
phone-landscape 800x360 same
tablet-landscape 1280x800 DPR 2
web-desktop     1366x768 and 1920x1080 (Playwright)
```

Each profile: `name, kind (desktop|web|android), width, height, dpi_scale,
cores, affinity_mask, priority, cpu_throttle, network, dpr, checks[]`.
Project `CLAUDE.md` declares its mandatory profiles in one line:
`profiles: laptop-avg, pc-low` (VibeCoder: + phone-portrait, phone-landscape, tablet-landscape).

## 6. gate.py — events and checks

Common: parse the transcript ONCE (`gate/transcript.py`) into: user
messages with timestamps, assistant text blocks per turn, tool_use records
(name, input, ts), tool_results, Read'ed image paths, launched agents +
completions. Project root = nearest ancestor of cwd with `.claude/` or
`.git`. Product file = inside the project root, not under `.claude/`,
`.git/`, `UV/`, scratchpad, and not the ledger/evidence. GUI file =
`changed_files.is_gui_path`.

Block = exit 2, stderr ≤ 3 lines: WHAT is wrong · the exact FIX · (optional)
where. Never lecture. Fail-open only on gate crash (print a one-line
warning to stderr, exit 0).

`prompt` (UserPromptSubmit): ensure `.claude/sessions/`, `.claude/evidence/<sid>/`,
`.claude/evidence/current`; create ledger from template if missing → print
path + grammar reminder (≤ 8 lines); else print `ledger: <path>`. Never
blocks.

`pre` (PreToolUse):
- Write/Edit/MultiEdit/NotebookEdit on a product file: ledger exists and has
  a `kategorija:` line with ≥ 1 valid category → else block:
  `No category. Write <ledger path> with 'kategorija: GUI|FEATURE|BUGFIX|REFACTOR|DOCS|PLAN|BUILD …' first.`
- FEATURE category + first product edit of the session + no `matrica:`
  block in ledger → block (Standard/Wide only; class `Trivial` skips).
- Write/Edit on `.claude/evidence/**` → block (machine-written).
- language check (module ported from language_guard.py — same behaviour,
  same `lang-ok` escapes, same language-frame.json).
- GUI file: forbidden GUI APIs (module ported from layout_guard.py
  PreToolUse part — same list, same `layout-ok` escape).
- Bash/PowerShell: build/release command patterns (`build.py`, `pyinstaller`,
  `makensis`, `gradlew assemble|bundle`, `gh release`, `git tag v`,
  `msbuild … /t:Publish`, `dotnet publish`) → allowed only if (a) transcript is
  the MAIN session (path not under `/subagents/`) AND (b) the owner's LAST
  message matches `\b(build|release|bild|bildu?j|rilis|objavi|izbilduj)\w*` (case-insensitive).
  Else block: `Build/release needs the owner's word in his last message; sub-agents never build. Ask with '## BUILD & RELEASE?'.`
- Artifact (publish): ballot contract check ported from communication_guard
  (`.option[data-option]`, textarea per option, `#ballot`, `#ballot-copy`,
  `#verdict`, no `prefers-color-scheme`/`data-theme`) when the page proposes
  options; image links exist. Serbian pages under scratchpad are exempt from
  language.

`stop` (Stop) — order matters, first block wins:
1. agents still running (port agents_guard mechanic verbatim) → block.
2. If NO product file was edited this session AND ledger has no open task →
   only checks 7–8 run (a conversation is not taxed).
3. Ledger exists, was modified after the owner's last message; every `[x]`
   has `!`; every `[?]` has `?`; `[ ]`/`[>]` present and no `[?]` → block
   `Open tasks without a [?] — mark [?] with a ? question, or [~], or finish.`
4. Category teeth (`gate/teeth.py`), per category present in the ledger:
   - GUI: for each GUI file edited, at least 2 `shot` rows with distinct
     profiles (one of them not `pc-owner`) newer than the last GUI edit; each
     shot's artifact was Read in the transcript after its `ts`; ledger has
     `grade N` ≥ 8 (or `ocena N`) per shot line. Class Standard/Wide: an
     `Agent` launch whose prompt contains `grader` (independent grader) exists
     after the shots.
   - FEATURE: `matrica:` table exists; every row's `evidence` column names an
     `ev-` id that exists, is not `unavailable`, and is newer than the last
     product edit — OR the task is `[~]`/`[ ]` (honest incompleteness);
     mandatory rows by keyword: `average device|prosečan`, `fresh install|sveža
     instalacija`; when the ledger says `zamena|replacement`: `old path|stari put`.
   - BUGFIX: a `test` row with rc≠0 BEFORE the first product edit and a
     `test` row rc=0 AFTER the last edit; ledger has `uzrok:`; if the owner's
     first message contains `opet|ponovo|again|still|i dalje` → `proces-uzrok:`
     line must exist.
   - REFACTOR: `test` rows before first edit and after last edit with equal
     `total` and both rc=0; project run_guards FULL exit 0 (gate runs it if
     the project has one) — includes clone guard.
   - DOCS/PLAN/BUILD: none here.
5. Evidence integrity: no Write/Edit targeted evidence.jsonl.
6. Rules-size guard when any of CLAUDE.md / rules/*.md / project CLAUDE.md
   was edited this session.
7. Communication: no ```mermaid``` fenced block in the final assistant text;
   local image links in the final text exist. Final block rule (§1.7): turn
   ended with no text block → block; last text block < 120 chars while an
   earlier text block of the same turn > 600 chars → block
   `Final message must stand alone — the owner sees only the last block.`
8. Installable project (project CLAUDE.md line `installable: yes` or a
   `setup/build.py`/`build.py` exists) + product edit this session + no build
   ran this session → final text must contain `## BUILD & RELEASE?` and the
   ledger a `[?]` BUILD task.

`subagent` (SubagentStop): transcript is the agent's own; if it edited a
product file, require a run tool call (Bash/PowerShell whose command contains
`uv.py`, `pytest`, `run_guards`, or `python -m`) AFTER the last product edit,
and its final text to contain at least one `! ` evidence line → else block
`Sub-agent edited files but ran nothing after the last edit — run uv test/shot/run_guards and report ! lines.`
Sub-agents never see build permission (pre check).

Self-test: `rules/hooks/test_gate.py` — ≥ 12 planted transcripts/ledgers
(pass and fail for each event) runnable with `python -m pytest rules/hooks`.

## 7. Runner — `rules/tools/uv.py` (F2)

`python rules/tools/uv.py <cmd>`; a `uv.cmd`/`uv` shim in `rules/tools/`
optional. Reads `.claude/evidence/current` for the session id (or
`--session`). Sub-commands:

- `test <pytest args…>` → `pytest --junitxml` into the evidence dir; row
  kind=test with passed/failed/total; `--label` optional.
- `run "<command>" --profile <p> [--timeout s] [--smoke-seconds n]` → runs
  under the profile's affinity/priority (Windows: `psutil` if present else
  `cmd /c start /wait /affinity …`; env `QT_SCALE_FACTOR`, `QT_QUICK_BACKEND`
  from profile), captures stdout/stderr to a log, measures start_ms (first
  output or window) → row kind=run.
- `shot --window <Name> --profile <p> [--all]` → imports the project's
  `.claude/uv_windows.py` (registry: `TOOLKIT = "qt"|"tk"`, `WINDOWS =
  {name: factory}` returning a top-level widget), sets offscreen platform,
  logical size + DPI from the profile, resizes to the profile screen (and to
  the window's declared minimum), grabs a PNG, runs the ALG checks from
  `rules/templates/layout_checks_qt.py`/`_tk.py` (clipped / starved / min
  fits 1280×720), writes PNG + row kind=shot with checks. `--all` = every
  registered window × every mandatory profile.
- `device <profile> <url|apk-path> [--flow script.py]` → web: Playwright
  Chromium with device emulation + CPU throttling, screenshot full page,
  checks h_scroll / tap targets ≥ 44 px; android: `adb` on a running
  emulator (`emulator -avd` if none and one exists), install apk, launch,
  `screencap`, rotate for landscape → row kind=device. Missing prerequisite →
  row kind=unavailable, rc=3, clear stderr message.
- `ls` → prints the session's evidence rows (id, ts, kind, summary).

Every row: id, ts, kind, cmd, rc, artifact, sha256, summary. Never
overwrite; append only. Errors are loud, never silent.

## 8. Project migration (F3) — per main project

1. `CLAUDE.md` ≤ 6 KB: stack, how to run/test, entry points, project laws,
   `profiles:` line, `installable: yes|no`, pointers to docs. Everything else
   → `docs/` (VibeCoder protocol → `docs/PROTOCOL.md`, decisions →
   `docs/DECISIONS.md`) or deleted if it repeats the constitution.
2. `tests/run_guards.py` (or `desktop/tests/…`): `--fast` on PostToolUse;
   FULL runs only when `changed_files.touched_anything()`; FULL includes
   `rules/tools/clone_guard.py` (ratchet list of known clones allowed,
   shrinking only) and the layout audit only for touched windows.
3. `.claude/uv_windows.py` registry (GUI projects).
4. `.claude/settings.json`: only the two run_guards hooks; permissions
   cleaned (stale paths out); no `delegation-required`.
5. `.claude/` cleanup: session-tasks.md, session-report.md, agents-ledger.md,
   layout-proof*.md, visual-proof*.json, ledger-plan.md, reports/, shots/
   (except topic folders the owner asked to keep) → Recycle Bin.
   `.gitignore` gets `.claude/sessions/` and `.claude/evidence/`.
6. Root-of-project stale briefs per the ballot chapter 9 (archive with `git mv`,
   delete via Recycle Bin).
7. Verification: `run_guards.py` FULL green; `rules_size_guard.py` green;
   `uv shot --all` produces PNGs for at least one window (GUI projects);
   commit per project.

## 9. What is NOT in this rework

- F4 (OOP audit + refactor plans) — separate sessions, WatchAcademy first.
- Application code of any project (only rules, hooks, docs, tests, .claude/).
- Any build or release.
