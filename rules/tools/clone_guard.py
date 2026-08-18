"""AST clone detector — rules/history/2026-08-18-rework-design.md ch.8.

Fingerprints every function/method BODY under a root: identifiers
(Name/arg/Attribute) are renamed to positional placeholders in
encounter order, constants are folded to a `<type>` placeholder,
leading docstrings are dropped, then the normalized body is
`ast.dump`-ed and hashed. Two bodies of >= --min-statements statements
(counted recursively, nested blocks included) that produce the same
fingerprint in DIFFERENT files are a clone group and FAIL. The same
fingerprint repeated inside one file is a WARN only — it never fails
the run.

Escapes:
  * a `clone-ok: <reason>` comment (first source line of the body) or
    docstring exempts the whole group a function belongs to. Reason is
    mandatory — a bare `clone-ok:` with nothing after it does not count.
  * `--ratchet <file>` — a JSON list of known clone groups (each a
    sorted list of "path::qualname" member ids), adopted at the time
    they were first found. A ratcheted group does not fail. The
    ratchet may only SHRINK: an id in the ratchet that the current
    code no longer produces is STALE and fails the run so it gets
    removed by hand.

CLI:
    python clone_guard.py <root> [--ratchet FILE] [--min-statements 8]
                           [--include-tests] [--write-ratchet] [--json]

Importable API: find_clones(root, min_statements) -> list[CloneGroup];
run(argv) -> int.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".git", ".claude", "__pycache__", "venv", ".venv", "build",
             "dist", "node_modules"}


@dataclass(frozen=True)
class FuncInfo:
    path: str          # posix path relative to root
    qualname: str
    lineno: int
    stmt_count: int
    exempt: bool
    reason: str

    @property
    def member_id(self) -> str:
        return f"{self.path}::{self.qualname}"

    @property
    def location(self) -> str:
        return f"{self.path}:{self.lineno} {self.qualname} ({self.stmt_count} stmts)"


@dataclass
class CloneGroup:
    fingerprint: str
    funcs: list = field(default_factory=list)

    @property
    def files(self) -> set:
        return {f.path for f in self.funcs}

    @property
    def cross_file(self) -> bool:
        return len(self.files) > 1

    @property
    def exempt(self) -> bool:
        return any(f.exempt for f in self.funcs)

    def member_ids(self) -> list:
        return sorted(f.member_id for f in self.funcs)


def _is_test_path(rel_parts: tuple) -> bool:
    if "tests" in rel_parts[:-1]:
        return True
    name = rel_parts[-1]
    return name.startswith("test_") or name.endswith("_test.py")


def _iter_py_files(root: Path, include_tests: bool):
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        parts = rel.parts
        if any(p in SKIP_DIRS for p in parts[:-1]):
            continue
        if not include_tests and _is_test_path(parts):
            continue
        yield path, rel


class _Normalizer(ast.NodeTransformer):
    """Renames identifiers to positional placeholders, folds constants."""

    def __init__(self):
        self._map = {}
        self._n = 0

    def _id(self, name: str) -> str:
        if name not in self._map:
            self._n += 1
            self._map[name] = f"ID{self._n}"
        return self._map[name]

    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id=self._id(node.id), ctx=ast.Load()), node)

    def visit_arg(self, node):
        node.arg = self._id(node.arg)
        node.annotation = None
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = self._id(node.attr)
        return node

    def visit_Constant(self, node):
        return ast.copy_location(
            ast.Constant(value=f"<{type(node.value).__name__}>"), node
        )


def _strip_docstring(body: list) -> tuple:
    """Returns (body_without_docstring, docstring_text_or_None)."""
    if body and isinstance(body[0], ast.Expr) and isinstance(
        body[0].value, ast.Constant
    ) and isinstance(body[0].value.value, str):
        return body[1:], body[0].value.value
    return body, None


def _count_statements(body: list) -> int:
    count = 0
    for node in body:
        for n in ast.walk(node):
            if isinstance(n, ast.stmt):
                count += 1
    return count


def _fingerprint_body(body: list) -> str:
    norm = _Normalizer()
    dumped = [ast.dump(norm.visit(n), annotate_fields=False) for n in body]
    return "|".join(dumped)


def _clone_ok_reason(source_lines: list, def_lineno: int, first_body_lineno: int,
                      docstring: str | None) -> tuple:
    if docstring and "clone-ok:" in docstring:
        reason = docstring.split("clone-ok:", 1)[1].strip().splitlines()[0].strip()
        return bool(reason), reason
    start = max(def_lineno - 1, 0)
    end = min(first_body_lineno, len(source_lines))
    for line in source_lines[start:end]:
        if "clone-ok:" in line and "#" in line.split("clone-ok:", 1)[0]:
            reason = line.split("clone-ok:", 1)[1].strip()
            return bool(reason), reason
    return False, ""


class _FuncWalker(ast.NodeVisitor):
    def __init__(self, source_lines: list):
        self.source_lines = source_lines
        self.scope = []
        self.found = []  # list of (qualname, node, body, docstring)

    def _visit_func(self, node):
        self.scope.append(node.name)
        qualname = ".".join(self.scope)
        body, docstring = _strip_docstring(node.body)
        self.found.append((qualname, node, body, docstring))
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node)

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()


def find_clones(root, min_statements: int = 8, include_tests: bool = False):
    root = Path(root).resolve()
    by_fingerprint = {}
    for path, rel in _iter_py_files(root, include_tests):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        lines = source.splitlines()
        walker = _FuncWalker(lines)
        walker.visit(tree)
        for qualname, node, body, docstring in walker.found:
            stmt_count = _count_statements(body)
            if stmt_count < min_statements:
                continue
            first_body_lineno = body[0].lineno if body else node.lineno
            exempt, reason = _clone_ok_reason(
                lines, node.lineno, first_body_lineno, docstring
            )
            fingerprint = _fingerprint_body(body)
            info = FuncInfo(
                path=rel.as_posix(), qualname=qualname, lineno=node.lineno,
                stmt_count=stmt_count, exempt=exempt, reason=reason,
            )
            by_fingerprint.setdefault(fingerprint, CloneGroup(fingerprint)).funcs.append(info)

    return [g for g in by_fingerprint.values() if len(g.funcs) > 1]


def _load_ratchet(path: Path):
    if not path or not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [tuple(sorted(members)) for members in data]


def _write_ratchet(path: Path, groups: list):
    data = [g.member_ids() for g in groups]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--ratchet", default=None)
    parser.add_argument("--min-statements", type=int, default=8)
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--write-ratchet", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def run(argv) -> int:
    args = build_parser().parse_args(argv)
    groups = find_clones(args.root, args.min_statements, args.include_tests)
    cross = [g for g in groups if g.cross_file]
    same_file = [g for g in groups if not g.cross_file]

    ratchet_path = Path(args.ratchet) if args.ratchet else None

    if args.write_ratchet:
        if ratchet_path is None:
            print("clone_guard: --write-ratchet needs --ratchet <file>", file=sys.stderr)
            return 2
        _write_ratchet(ratchet_path, cross)
        print(f"clone_guard: wrote {len(cross)} group(s) to {ratchet_path}")
        return 0

    ratchet_keys = set(_load_ratchet(ratchet_path)) if ratchet_path else set()
    seen_keys = set()
    failing = []
    for g in cross:
        key = tuple(g.member_ids())
        seen_keys.add(key)
        if key in ratchet_keys or g.exempt:
            continue
        failing.append(g)
    stale = sorted(ratchet_keys - seen_keys)

    for g in same_file:
        locs = " / ".join(f.location for f in g.funcs)
        print(f"WARN same-file clone: {locs}")

    if args.json:
        payload = {
            "failing": [[f.location for f in g.funcs] for g in failing],
            "stale_ratchet_ids": [list(k) for k in stale],
            "same_file_warnings": len(same_file),
        }
        print(json.dumps(payload, indent=2))
    else:
        for g in failing:
            locs = " / ".join(f.location for f in g.funcs)
            print(f"CLONE: {locs}")
        for key in stale:
            print(f"STALE RATCHET ID (no longer produced): {list(key)}")

    if failing or stale:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
