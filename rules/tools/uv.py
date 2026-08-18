"""The evidence runner: the ONE program that writes
`<project>/.claude/evidence/<session>/evidence.jsonl`.

An agent never writes an evidence row by hand - it runs this and reads what
came back. Sub-commands:

    uv test <pytest args...>                     pytest + junit report -> row
    uv run "<command>" --profile <p>             run under a device profile -> row
    uv shot --window <Name> --profile <p> | --all   offscreen window PNG + checks -> row
    uv device <profile> <url|apk|package>        browser/Android emulation -> row
    uv ls                                        print this session's rows

Design: rules/history/2026-08-18-rework-design.md, sections 4, 5 and 7.
Device profiles: rules/devices.json. Usage: rules/howto/runner.md.
Stdlib first; `psutil` and `playwright` are optional and detected at runtime -
a missing prerequisite produces a `kind: unavailable` row (rc 3) and a loud
message on stderr, never a silent pass.

This file is the entry point and holds `test`, `run`, `ls` and the CLI. The
rest is beside it: `uv_core.py` (project root, session, the evidence file,
device profiles), `uv_shot.py`, `uv_device.py`.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

# Evidence and load_devices are re-exported: the self-test and any future
# caller reach them through `uv`, the name this tool is known by.
from uv_core import (Context, Evidence, command_line,      # noqa: F401
                     load_devices, warn)
from uv_device import cmd_device
from uv_shot import cmd_shot, cmd_shot_one

# --------------------------------------------------------------------------
# uv test
# --------------------------------------------------------------------------


def parse_junit(path: Path) -> dict:
    import xml.etree.ElementTree as ET

    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    total = failures = errors = skipped = 0
    for suite in suites:
        if suite.tag != "testsuite":
            continue
        total += int(suite.get("tests", 0))
        failures += int(suite.get("failures", 0))
        errors += int(suite.get("errors", 0))
        skipped += int(suite.get("skipped", 0))
    passed = total - failures - errors - skipped
    return {"total": total, "passed": passed,
            "failed": failures + errors, "skipped": skipped}


def cmd_test(args, ctx: Context) -> int:
    ident = ctx.ev.reserve()
    cmd = command_line(["test", *args.pytest_args]
                       + (["--label", args.label] if args.label else []))
    if importlib.util.find_spec("pytest") is None:
        ctx.ev.unavailable(ident, cmd, "pytest is not installed "
                                       "(pip install pytest)")
        return 3
    junit = ctx.ev.dir / f"junit-{ident[3:]}.xml"
    argv = [sys.executable, "-m", "pytest", *args.pytest_args,
            f"--junitxml={junit}", "-q", "--no-header",
            "-p", "no:cacheprovider"]
    proc = subprocess.run(argv, cwd=ctx.root, capture_output=True, text=True)
    tail = (proc.stdout or "").strip().splitlines()[-12:]
    print("\n".join(tail))
    if proc.stderr.strip():
        warn("pytest stderr: " + proc.stderr.strip().splitlines()[-1])
    if not junit.is_file():
        ctx.ev.unavailable(ident, cmd,
                           f"pytest produced no junit report (rc {proc.returncode})")
        return 3
    counts = parse_junit(junit)
    summary = f"{counts['passed']}/{counts['total']}"
    if counts["failed"]:
        summary += f" - {counts['failed']} failed"
    if counts["skipped"]:
        summary += f", {counts['skipped']} skipped"
    # A test file pytest COLLECTS NOTHING from is invisible to every count
    # (VibeCoder 2026-08-19: 30 script-style gates, 3 broken by a refactor,
    # every "N/N green" row silently excluded them). Name them in the row.
    invisible = _uncollected_test_files(ctx.root, args.pytest_args, junit)
    if invisible:
        counts["uncollected"] = len(invisible)
        summary += (f" | {len(invisible)} test file(s) pytest collected NOTHING "
                    f"from: {', '.join(invisible[:4])}"
                    + (" …" if len(invisible) > 4 else ""))
        warn(f"{len(invisible)} test file(s) yield no pytest tests - run them "
             "directly or wrap their main() in a test_* function")
    if args.label:
        summary = f"{args.label}: {summary}"
    ctx.ev.append(ident, "test", cmd, proc.returncode, summary, junit,
                  label=args.label, **counts)
    return proc.returncode


def _uncollected_test_files(root: Path, pytest_args: list[str],
                            junit: Path) -> list[str]:
    """`test_*.py` files under the pytest target paths that appear in NO
    junit testcase classname — pytest ran and found no test in them."""
    import xml.etree.ElementTree as ET
    targets = [root / a for a in pytest_args
               if not a.startswith("-") and (root / a).exists()]
    if not targets:
        return []
    files: set[Path] = set()
    for target in targets:
        if target.is_dir():
            files.update(target.rglob("test_*.py"))
        elif target.suffix == ".py":
            files.add(target)
    seen: set[str] = set()
    try:
        for case in ET.parse(junit).getroot().iter("testcase"):
            classname = case.get("classname") or ""
            seen.add(classname.split(".")[-1] if "." in classname else classname)
            for part in classname.split("."):
                seen.add(part)
    except ET.ParseError:
        return []
    return sorted(f.relative_to(root).as_posix() for f in files
                  if f.stem not in seen)


# --------------------------------------------------------------------------
# uv run
# --------------------------------------------------------------------------

_PSUTIL_PRIORITY = {
    "low": "IDLE_PRIORITY_CLASS",
    "belownormal": "BELOW_NORMAL_PRIORITY_CLASS",
    "normal": "NORMAL_PRIORITY_CLASS",
    "abovenormal": "ABOVE_NORMAL_PRIORITY_CLASS",
    "high": "HIGH_PRIORITY_CLASS",
}


def _apply_profile_limits(pid: int, profile: dict) -> str:
    """Affinity + priority through psutil. Returns a note for the summary."""
    try:
        import psutil
    except ImportError:
        return "psutil missing - no affinity/priority applied"
    notes = []
    try:
        process = psutil.Process(pid)
        mask = profile.get("affinity_mask")
        if mask:
            cpus = [i for i in range(mask.bit_length()) if mask >> i & 1]
            available = list(range(psutil.cpu_count() or len(cpus)))
            cpus = [c for c in cpus if c in available] or available[:1]
            process.cpu_affinity(cpus)
            notes.append(f"affinity {len(cpus)} cores")
        priority = profile.get("priority", "normal")
        constant = getattr(psutil, _PSUTIL_PRIORITY.get(priority, ""), None)
        if constant is not None:
            process.nice(constant)
            notes.append(priority)
        elif os.name != "nt":
            process.nice({"low": 15, "belownormal": 5}.get(priority, 0))
            notes.append(priority)
    except Exception as error:                       # process may have exited
        return f"limits not applied ({type(error).__name__}: {error})"
    return ", ".join(notes) or "no limits in profile"


def _run_with_cmd_start(command: str, profile: dict, log: Path,
                        cwd: Path, env: dict, timeout: float) -> int:
    """Windows fallback when psutil is absent: `start /wait /affinity`."""
    mask = profile.get("affinity_mask")
    priority = {"low": "LOW", "belownormal": "BELOWNORMAL",
                "normal": "NORMAL", "abovenormal": "ABOVENORMAL",
                "high": "HIGH"}.get(profile.get("priority", "normal"), "NORMAL")
    parts = ["start", '"uv"', "/wait", f"/{priority}"]
    if mask:
        parts += ["/affinity", format(int(mask), "x")]
    inner = f'{command} > "{log}" 2>&1'
    full = "cmd /c " + " ".join(parts) + f' cmd /c "{inner}"'
    warn("psutil not installed - using `cmd /c start /wait` "
         "(start_ms is total runtime, not first output)")
    return subprocess.run(full, shell=True, cwd=cwd, env=env,
                          timeout=timeout).returncode


def cmd_run(args, ctx: Context) -> int:
    profile = ctx.profile(args.profile)
    ident = ctx.ev.reserve()
    cmd = command_line(["run", args.command, "--profile", args.profile])
    log = ctx.ev.dir / f"run-{ident[3:]}.log"
    env = os.environ.copy()
    env.update({k: str(v) for k, v in (profile.get("env") or {}).items()})
    if profile.get("dpi_scale"):
        env.setdefault("QT_SCALE_FACTOR", str(profile["dpi_scale"]))

    started = time.perf_counter()
    first_output: list[float | None] = [None]
    lines: list[str] = []
    try:
        import psutil                                        # noqa: F401
        have_psutil = True
    except ImportError:
        have_psutil = False

    if not have_psutil and os.name == "nt":
        try:
            rc = _run_with_cmd_start(args.command, profile, log, ctx.root,
                                     env, args.timeout)
        except subprocess.TimeoutExpired:
            rc = 124
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        limits = "cmd start /affinity"
    else:
        proc = subprocess.Popen(args.command, shell=True, cwd=ctx.root,
                                env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                errors="replace", bufsize=1)
        limits = _apply_profile_limits(proc.pid, profile)

        def reader() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                if first_output[0] is None:
                    first_output[0] = time.perf_counter()
                lines.append(line)

        pump = threading.Thread(target=reader, daemon=True)
        pump.start()
        limit = args.smoke_seconds or args.timeout
        try:
            rc = proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            if args.smoke_seconds:
                rc = 0                       # survived the smoke window = pass
            else:
                rc = 124
                warn(f"timeout after {args.timeout}s - process killed")
        pump.join(timeout=2)
        log.write_text("".join(lines), encoding="utf-8")
        elapsed_ms = round(((first_output[0] or time.perf_counter())
                            - started) * 1000)

    if not log.is_file():
        log.write_text("", encoding="utf-8")
    budget = (profile.get("budgets") or {}).get("start_ms")
    summary = f"start {elapsed_ms} ms"
    if budget:
        summary += f" (budget {budget} ms, {'OK' if elapsed_ms <= budget else 'OVER'})"
    summary += f" - {args.profile}: {limits}"
    if args.smoke_seconds:
        summary += f", smoke {args.smoke_seconds}s"
    if profile.get("reference_only"):
        summary += f" - {REFERENCE_ONLY_NOTE}"
    ctx.ev.append(ident, "run", cmd, rc, summary, log,
                  profile=args.profile, start_ms=elapsed_ms)
    return rc


# --------------------------------------------------------------------------
# uv ls
# --------------------------------------------------------------------------


def cmd_ls(args, ctx: Context) -> int:
    rows = ctx.ev.rows()
    print(f"session {ctx.session} - {ctx.ev.path} ({len(rows)} rows)")
    for row in rows:
        print(f"{row.get('id'):8} {row.get('ts', ''):26} "
              f"{row.get('kind', ''):12} rc={row.get('rc')} "
              f"{row.get('summary', '')}")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uv", description="The UVuruna evidence runner "
                               "(rules/howto/runner.md).")
    parser.add_argument("--session", help="session id (default: "
                                          ".claude/evidence/current)")
    parser.add_argument("--project", help="project root (default: nearest "
                                          "ancestor with .claude/ or .git)")
    subs = parser.add_subparsers(dest="cmd", required=True)

    test = subs.add_parser("test", help="pytest run -> evidence row")
    test.add_argument("--label", help="short name for the summary")
    test.add_argument("pytest_args", nargs=argparse.REMAINDER)
    test.set_defaults(func=cmd_test)

    run = subs.add_parser("run", help="run a command under a device profile")
    run.add_argument("command")
    run.add_argument("--profile", required=True)
    run.add_argument("--timeout", type=float, default=120.0)
    run.add_argument("--smoke-seconds", type=float, default=None,
                     help="kill after N seconds and count survival as a pass")
    run.set_defaults(func=cmd_run)

    shot = subs.add_parser("shot", help="offscreen window PNG + layout checks")
    shot.add_argument("--window", help="registry name (default: all windows)")
    shot.add_argument("--profile", action="append",
                      help="device profile (repeatable)")
    shot.add_argument("--all", action="store_true",
                      help="every window x every mandatory profile")
    shot.set_defaults(func=cmd_shot)

    one = subs.add_parser("_shot-one", help=argparse.SUPPRESS)
    one.add_argument("--window", required=True)
    one.add_argument("--profile", required=True)
    one.add_argument("--out", required=True)
    one.add_argument("--result", required=True)
    one.set_defaults(func=cmd_shot_one)

    device = subs.add_parser("device", help="browser/Android device emulation")
    device.add_argument("profile")
    device.add_argument("target", nargs="?", help="url, .apk path or package")
    device.add_argument("--flow", help="python file with `def flow(page)`")
    device.add_argument("--package", help="Android package to launch")
    device.add_argument("--serial", help="adb device serial")
    device.add_argument("--start-emulator", action="store_true")
    device.add_argument("--timeout", type=float, default=30.0)
    device.set_defaults(func=cmd_device)

    listing = subs.add_parser("ls", help="print this session's evidence rows")
    listing.set_defaults(func=cmd_ls)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "pytest_args", None):
        args.pytest_args = [a for a in args.pytest_args if a != "--"]
    ctx = Context(args)
    return args.func(args, ctx)


if __name__ == "__main__":
    sys.exit(main())
