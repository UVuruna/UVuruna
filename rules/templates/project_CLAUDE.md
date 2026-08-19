# <Project Name>

<One paragraph: what this app does, for whom, on what platform.>

This file inherits the monorepo constitution (`CLAUDE.md` at the root) and may
only ADD or TIGHTEN its rules — never loosen them. Keep it under 6,000 bytes:
everything longer lives in `docs/`.

profiles: laptop-avg, pc-low
installable: yes

<!-- profiles: the device profiles from rules/devices.json that this project's
     GUI/FEATURE teeth must satisfy; at least one is never pc-owner.
     installable: yes when the project ships an installer (then BUILD.md
     applies on his word), no otherwise. -->

## Stack

- Language / runtime: <Python 3.12 · C# .NET 8 · Kotlin …>
- GUI: <PySide6 · WPF · web>
- Key libraries: <one line each, why it is here>
- Data / storage: <files, SQLite, none>

## How to run

```
<python main.py>
<python main.py --smoke>          smoke run used by `uv run`
```

## How to test

```
python -m pytest                  full suite
python tests/run_guards.py        guards, FULL (Stop hook)
python tests/run_guards.py --fast guards, fast (PostToolUse hook)
python rules/tools/uv.py shot --all   screenshots for every window × profile
```

## Entry points

| Path | Role |
|------|------|
| `main.py` | process entry, wiring |
| `<pkg>/app/controller.py` | orchestration |
| `<pkg>/gui/main_window.py` | main window |
| `.claude/uv_windows.py` | window registry for `uv shot` (GUI projects) |

## Project laws

<Only what is TIGHTER or EXTRA compared to the constitution. Examples:>

- <Every new watch is a row in `registry/…`, never a new module.>
- <Rendering never touches the config file directly.>
- RATCHET (files allowed over the structure wall, shrinking only):
  `<path>` — <why it stays whole> — <who owes the split>.

## Docs

- `README.md` — what it is, the name story, the navigation chain root
- `docs/<AREA>.md` — <protocol / decisions / canon; read only when touching it>
- Folder docs: `<pkg>/___<pkg>.md` → `__about/`, `__flow/`

## Open items

- <carried `[~]` items and known debts, one line each>
