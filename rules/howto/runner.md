# The evidence runner — `rules/tools/uv.py`

Evidence is produced by a machine and only LOOKED AT by the agent. This is the
only writer of `<project>/.claude/evidence/<session>/evidence.jsonl`; a
hand-written row is a forged row. Run it from inside the project:

```
python u:/Coding/UVuruna/rules/tools/uv.py <cmd> …     # or `uv <cmd>` with rules/tools on PATH
```

Session id: `.claude/evidence/current` (written by `gate.py prompt`) or
`--session <id>`; without either it says so on stderr and uses `manual`.
Project root = nearest ancestor of the cwd with `.claude/` or `.git`
(`--project` overrides).

## Commands

| Command | Does | Row |
|---------|------|-----|
| `uv test <pytest args…> [--label X]` | pytest with `--junitxml` into the evidence dir | `kind:test` + `passed/failed/skipped/total` |
| `uv run "<cmd>" --profile <p> [--timeout S] [--smoke-seconds N]` | runs it under the profile's affinity, priority and env; log captured | `kind:run` + `start_ms` |
| `uv shot [--window N] [--profile P …] [--all]` | builds a registered window offscreen at the profile screen AND at its minimum, PNG + ALG checks | `kind:shot` + `checks` |
| `uv device <profile> <url\|apk\|package> [--flow f.py]` | Chromium emulation (viewport, DPR, CPU throttle, network) or `adb` on a phone | `kind:device` + `checks` |
| `uv ls` | prints this session's rows | — |

Exit codes: `0` clean · `1` the checks found something · `3` a prerequisite
missing (row `kind: unavailable`, which satisfies NO tooth). `--smoke-seconds`
makes surviving N seconds the pass (a GUI that never exits).

## A row

```json
{"id":"ev-0003","ts":"2026-08-18T20:20:34+02:00","kind":"shot",
 "cmd":"uv shot --window SettingsDialog --profile laptop-avg","rc":0,
 "profile":"laptop-avg","window":"SettingsDialog","sha256":"3f9a…",
 "artifact":".claude/evidence/s-1/SettingsDialog-laptop-avg.png",
 "checks":{"clipped":0,"starved":0,"min_fits":true},"summary":"ALG ok…"}
```

`id` is sequential per session, `sha256` is the artifact's hash (a regenerated
file is a NEW row). Append-only, never hand-edited — the gate blocks that.

## Registering windows

Copy `rules/templates/uv_windows.py` to `<project>/.claude/uv_windows.py`:

```python
TOOLKIT = "qt"                                 # "qt" (PySide6) or "tk"
MANDATORY_PROFILES = ["laptop-avg", "pc-low"]  # from rules/devices.json
def prepare(): ...                             # optional: fonts, sys.path
WINDOWS = {"SettingsDialog": make_settings_dialog}
```

Each factory returns a window in its FULLEST realistic state — an empty window
passes everything and proves nothing. Keep toolkit imports inside the factories
(the file is imported before the offscreen env is set). Each (window, profile)
runs in its own process, so a crashing factory costs one `unavailable` row, not
the run. A project with a pytest layout audit points at its builders instead of
writing them twice — see `Applications/WatchAcademy/.claude/uv_windows.py`.

## Device profiles

`rules/devices.json` holds them all, each with its own `_doc`. A project names
its mandatory ones in its `CLAUDE.md`: `profiles: laptop-avg, pc-low`.
**`pc-owner` is reference only** — its rows say so and satisfy no tooth. We
build for others.

## Prerequisites, and what a missing one does

| Needed for | Missing → |
|------------|-----------|
| `pytest` (`uv test`) | `unavailable`: "pytest is not installed" |
| `psutil` (`uv run`) | falls back to `cmd /c start /wait /affinity`, loudly; `start_ms` becomes total runtime |
| `PySide6` / Tk + Pillow (`uv shot`) | `unavailable` with the import error |
| `.claude/uv_windows.py` | `unavailable`: "no window registry at …" |
| `playwright` + Chromium (`uv device` web) | installed once automatically; on failure `unavailable` with the reason |
| `adb` + device or AVD (`uv device` android) | `unavailable`: no adb / no device and no AVD / AVD exists → add `--start-emulator` |

Nothing is silent: a missing prerequisite is a loud stderr line AND a row that
cannot be mistaken for proof.

Self-test: `pytest rules/tools/test_uv.py`
