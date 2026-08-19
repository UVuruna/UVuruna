"""Shared machinery of the evidence runner: project root, session, the
append-only `evidence.jsonl` and the device profiles.

Imported by `uv.py` (the CLI entry, plus `test`/`run`/`ls`), `uv_shot.py`
(window screenshots + layout checks) and `uv_device.py` (browser and Android
emulation). The whole runner is documented in rules/howto/runner.md.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parents[1]
DEVICES_FILE = RULES_DIR / "devices.json"
TEMPLATES_DIR = RULES_DIR / "templates"

#: The screen every desktop window must survive (THE SPACE & LEGIBILITY LAW).
FLOOR_WIDTH, FLOOR_HEIGHT = 1280, 720
#: Minimum edge of an interactive element on a touch device.
TAP_TARGET_PX = 44
#: Profiles that are the owner's own machine never satisfy a tooth.
REFERENCE_ONLY_NOTE = "pc-owner is REFERENCE ONLY - this row satisfies no tooth"


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def warn(message: str) -> None:
    """Everything the runner cannot do is said out loud, on stderr."""
    print(f"uv: {message}", file=sys.stderr)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_project_root(start: Path | None = None) -> Path:
    """Nearest ancestor holding `.claude/` or `.git` — ONE implementation,
    shared with the gate (rules/hooks/gate/paths.py)."""
    hooks_dir = str(Path(__file__).resolve().parents[1] / "hooks")
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)
    from gate import paths as gate_paths
    return gate_paths.project_root(Path(start or Path.cwd()).resolve())


def load_devices() -> dict:
    if not DEVICES_FILE.is_file():
        raise SystemExit(f"uv: missing device profiles: {DEVICES_FILE}")
    return json.loads(DEVICES_FILE.read_text(encoding="utf-8"))


def import_from_path(name: str, path: Path):
    """Import a file by path under a private module name (avoids colliding
    with a project's own module of the same basename)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# evidence file
# --------------------------------------------------------------------------


class Evidence:
    """Append-only `evidence.jsonl` with sequential `ev-NNNN` ids."""

    def __init__(self, root: Path, session: str, directory: Path):
        self.root = root
        self.session = session
        self.dir = directory
        self.path = directory / "evidence.jsonl"
        self._reserved: set[int] = set()

    # -- reading ------------------------------------------------------------

    def rows(self) -> list[dict]:
        if not self.path.is_file():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                warn(f"unreadable evidence line skipped: {line[:60]}")
        return out

    def _used_numbers(self) -> set[int]:
        numbers = set(self._reserved)
        for row in self.rows():
            ident = str(row.get("id", ""))
            if ident.startswith("ev-") and ident[3:].isdigit():
                numbers.add(int(ident[3:]))
        return numbers

    def reserve(self) -> str:
        """Claim the next id. The artifact is named after it, so it must be
        known before the work runs."""
        used = self._used_numbers()
        number = max(used) + 1 if used else 1
        self._reserved.add(number)
        return f"ev-{number:04d}"

    # -- writing ------------------------------------------------------------

    def append(self, ident: str, kind: str, cmd: str, rc: int,
               summary: str, artifact: Path | None = None, **extra) -> dict:
        row: dict = {"id": ident, "ts": now_iso(), "kind": kind,
                     "cmd": cmd, "rc": int(rc)}
        row.update({k: v for k, v in extra.items() if v is not None})
        if artifact is not None and Path(artifact).is_file():
            artifact = Path(artifact)
            try:
                relative = artifact.resolve().relative_to(self.root).as_posix()
            except ValueError:
                relative = artifact.as_posix()
            row["artifact"] = relative
            row["sha256"] = sha256_of(artifact)
        else:
            if artifact is not None:
                warn(f"artifact was not produced: {artifact}")
            row["artifact"] = None
            row["sha256"] = None
        row["summary"] = summary
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['id']} {row['kind']} rc={row['rc']} {row['summary']}")
        return row

    def unavailable(self, ident: str, cmd: str, reason: str, **extra) -> dict:
        warn(f"UNAVAILABLE: {reason}")
        return self.append(ident, "unavailable", cmd, 3, reason, **extra)


class Context:
    """Everything a sub-command needs: project root, session, devices."""

    def __init__(self, args):
        self.root = find_project_root(Path(args.project) if args.project
                                      else None)
        self.devices = load_devices()
        evidence_dir = self.root / ".claude" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        self.session = self._session_id(evidence_dir, args.session)
        session_dir = evidence_dir / self.session
        session_dir.mkdir(parents=True, exist_ok=True)
        self.ev = Evidence(self.root, self.session, session_dir)

    @staticmethod
    def _session_id(evidence_dir: Path, explicit: str | None) -> str:
        if explicit:
            return explicit
        current = evidence_dir / "current"
        if current.is_file():
            text = current.read_text(encoding="utf-8").strip()
            if text:
                return text
        warn(f"no session id in {current} - falling back to session 'manual'")
        return "manual"

    def profile(self, name: str) -> dict:
        profiles = self.devices["profiles"]
        if name not in profiles:
            raise SystemExit(
                f"uv: unknown profile {name!r}; known: "
                + ", ".join(sorted(profiles)))
        return profiles[name]


def command_line(argv: list[str]) -> str:
    return "uv " + " ".join(shlex.quote(a) for a in argv)


