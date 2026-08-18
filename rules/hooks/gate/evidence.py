"""Reads `.claude/evidence/<sid>/evidence.jsonl` — rows written only by uv.py.

A row satisfies a tooth only when it succeeded (`rc == 0`), is not
`kind: unavailable`, and is NEWER than the edit it is supposed to prove.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .transcript import parse_ts


@dataclass(slots=True)
class Row:
    id: str
    kind: str
    ts: datetime | None
    rc: int
    profile: str
    window: str
    artifact: str
    summary: str
    data: dict

    @property
    def usable(self) -> bool:
        return self.kind != "unavailable" and self.rc == 0

    def newer_than(self, when: datetime | None) -> bool:
        if when is None:
            return True
        return self.ts is not None and self.ts > when

    @property
    def artifact_name(self) -> str:
        return Path(self.artifact).name.lower() if self.artifact else ""

    def number(self, key: str) -> int | None:
        value = self.data.get(key)
        return value if isinstance(value, int) else None


@dataclass
class Evidence:
    path: Path
    exists: bool = False
    rows: list[Row] = field(default_factory=list)

    def by_id(self, ident: str) -> Row | None:
        for row in self.rows:
            if row.id == ident:
                return row
        return None

    def of_kind(self, kind: str) -> list[Row]:
        return [r for r in self.rows if r.kind == kind]

    def usable_of_kind(self, kind: str, after: datetime | None = None) -> list[Row]:
        return [r for r in self.of_kind(kind)
                if r.usable and r.newer_than(after)]


def load(path: Path) -> Evidence:
    path = Path(path)
    evidence = Evidence(path=path)
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return evidence
    evidence.exists = True
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        rc = data.get("rc")
        evidence.rows.append(Row(
            id=str(data.get("id") or ""),
            kind=str(data.get("kind") or ""),
            ts=parse_ts(data.get("ts")),
            rc=rc if isinstance(rc, int) else 1,
            profile=str(data.get("profile") or ""),
            window=str(data.get("window") or ""),
            artifact=str(data.get("artifact") or ""),
            summary=str(data.get("summary") or ""),
            data=data,
        ))
    return evidence
