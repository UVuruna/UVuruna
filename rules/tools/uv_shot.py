"""`uv shot` - a registered window built offscreen, measured and photographed.

Parent side: the window x profile matrix, one child process per pair (a
factory that crashes costs one `unavailable` row, never the run). Child side:
the toolkit work itself, in a process whose environment already carries the
profile's platform, scaling and backend. The checks are the ALG library in
rules/templates/layout_checks_qt.py / _tk.py - clipped, starved, min_fits.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from uv_core import (FLOOR_HEIGHT, FLOOR_WIDTH, REFERENCE_ONLY_NOTE,
                     TEMPLATES_DIR, Context, command_line, import_from_path,
                     warn)

#: The CLI entry - a shot child is `uv.py _shot-one`, not this module.
ENTRY = Path(__file__).resolve().parent / "uv.py"

# --------------------------------------------------------------------------
# uv shot - parent side (one child process per window x profile)
# --------------------------------------------------------------------------


def load_registry(root: Path):
    path = root / ".claude" / "uv_windows.py"
    if not path.is_file():
        return None, path
    sys.path.insert(0, str(root))
    return import_from_path("_uv_windows", path), path


def shot_matrix(registry, args) -> list[tuple[str, str]]:
    windows = list(registry.WINDOWS)
    mandatory = list(getattr(registry, "MANDATORY_PROFILES",
                             ["laptop-avg", "pc-low"]))
    if args.all:
        return [(w, p) for w in windows for p in mandatory]
    names = [args.window] if args.window else windows
    profiles = args.profile or mandatory
    return [(w, p) for w in names for p in profiles]


def cmd_shot(args, ctx: Context) -> int:
    registry, registry_path = load_registry(ctx.root)
    if registry is None:
        ident = ctx.ev.reserve()
        ctx.ev.unavailable(ident, command_line(["shot"]),
                           f"no window registry at {registry_path} "
                           "(copy rules/templates/uv_windows.py)")
        return 3
    toolkit = getattr(registry, "TOOLKIT", "qt")
    pairs = shot_matrix(registry, args)
    if not pairs:
        warn("nothing to shoot - registry WINDOWS is empty")
        return 3
    worst = 0
    for window, profile_name in pairs:
        worst = max(worst, _shot_one(ctx, toolkit, window, profile_name))
    return worst


def _shot_one(ctx: Context, toolkit: str, window: str, profile_name: str) -> int:
    profile = ctx.profile(profile_name)
    ident = ctx.ev.reserve()
    cmd = command_line(["shot", "--window", window, "--profile", profile_name])
    png = ctx.ev.dir / f"{window}-{profile_name}.png"
    env = os.environ.copy()
    env.update({k: str(v) for k, v in (profile.get("env") or {}).items()})
    if toolkit == "qt":
        env["QT_QPA_PLATFORM"] = "offscreen"
        env["QT_SCALE_FACTOR"] = str(profile.get("dpi_scale", 1))
        env["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    result_file = ctx.ev.dir / f".shot-{ident[3:]}.json"
    argv = [sys.executable, str(ENTRY),
            "--project", str(ctx.root), "--session", ctx.session, "_shot-one",
            "--window", window, "--profile", profile_name,
            "--out", str(png), "--result", str(result_file)]
    proc = subprocess.run(argv, cwd=ctx.root, env=env,
                          capture_output=True, text=True)
    if proc.stderr.strip():
        for line in proc.stderr.strip().splitlines()[-6:]:
            warn(f"[{window}/{profile_name}] {line}")
    result = {}
    if result_file.is_file():
        result = json.loads(result_file.read_text(encoding="utf-8"))
        result_file.unlink()
    if not result.get("ok"):
        reason = result.get("error") or f"shot child failed (rc {proc.returncode})"
        ctx.ev.unavailable(ident, cmd, f"{window}/{profile_name}: {reason}",
                           profile=profile_name, window=window)
        return 3
    checks = result["checks"]
    faults = result.get("faults") or []
    rc = 0 if (checks["clipped"] == 0 and checks["starved"] == 0
               and checks["min_fits"]) else 1
    summary = (f"ALG {'ok' if rc == 0 else 'FAIL'} - {checks['clipped']} clipped,"
               f" {checks['starved']} starved, min {result['min'][0]}x"
               f"{result['min'][1]} "
               f"{'fits' if checks['min_fits'] else 'DOES NOT FIT'} "
               f"{FLOOR_WIDTH}x{FLOOR_HEIGHT}")
    if faults:
        summary += " | " + faults[0][:140]
    if profile.get("reference_only"):
        summary += f" | {REFERENCE_ONLY_NOTE}"
    ctx.ev.append(ident, "shot", cmd, rc, summary, png,
                  profile=profile_name, window=window, checks=checks,
                  faults=faults or None)
    return rc


# --------------------------------------------------------------------------
# uv shot - child side (one process = one toolkit env = one profile)
# --------------------------------------------------------------------------


def _qt_checks_module():
    return import_from_path("_uv_layout_checks_qt",
                            TEMPLATES_DIR / "layout_checks_qt.py")


def _shot_qt(registry, window_name: str, profile: dict, out: Path) -> dict:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    checks_module = _qt_checks_module()
    app = QApplication.instance() or QApplication([])
    prepare = getattr(registry, "prepare", None)
    if callable(prepare):
        prepare()

    def pump() -> None:
        for _ in range(3):
            app.processEvents()

    window = registry.WINDOWS[window_name]()
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.show()
    pump()

    minimum = window.minimumSize()
    if minimum.width() > 0 and minimum.height() > 0:
        min_w, min_h = minimum.width(), minimum.height()
    else:
        hint = window.minimumSizeHint()
        min_w, min_h = max(hint.width(), 1), max(hint.height(), 1)
    min_fits = min_w <= FLOOR_WIDTH and min_h <= FLOOR_HEIGHT

    def audit(label: str) -> tuple[list[str], list[str]]:
        pump()
        clipped = [f"[{label}] {f}" for f in checks_module.check_clipping(window)]
        starved = [f"[{label}] {f}"
                   for f in checks_module.check_scroll_with_free_space(window)]
        return clipped, starved

    # Pass A - the declared minimum, the state the law is hardest on.
    window.resize(min_w, min_h)
    clipped, starved = audit("min")

    # Pass B - the profile's own screen (logical pixels), which is what the
    # PNG shows: a window never bigger than the screen it must live on.
    scale = float(profile.get("dpi_scale") or 1)
    screen_w = int(profile["width"] / scale)
    screen_h = int(profile["height"] / scale)
    hint = window.sizeHint()
    target_w = max(min_w, min(screen_w, max(hint.width(), min_w)))
    target_h = max(min_h, min(screen_h, max(hint.height(), min_h)))
    window.resize(target_w, target_h)
    more_clipped, more_starved = audit("screen")
    clipped += more_clipped
    starved += more_starved

    pump()
    if not window.grab().save(str(out), "PNG"):
        raise RuntimeError(f"QWidget.grab().save() failed for {out}")
    return {
        "ok": True,
        "min": [min_w, min_h],
        "size": [target_w, target_h],
        "checks": {"clipped": len(clipped), "starved": len(starved),
                   "min_fits": bool(min_fits)},
        "faults": clipped + starved
                  + ([] if min_fits else
                     [f"ABSURD MINIMUM {min_w}x{min_h} does not fit "
                      f"{FLOOR_WIDTH}x{FLOOR_HEIGHT} - REFLOW, never widen"]),
    }


def _shot_tk(registry, window_name: str, profile: dict, out: Path) -> dict:
    """Tk has no offscreen platform and no widget-level grab: the window is
    built for real, placed off the visible desktop, measured, and captured
    with Pillow's ImageGrab (which needs it on-screen, so it is moved to the
    corner for the single grab)."""
    import tkinter as tk

    checks_module = import_from_path("_uv_layout_checks_tk",
                                     TEMPLATES_DIR / "layout_checks_tk.py")
    root = tk._default_root or tk.Tk()                       # noqa: SLF001
    root.withdraw()
    prepare = getattr(registry, "prepare", None)
    if callable(prepare):
        prepare()
    window = registry.WINDOWS[window_name]()
    scale = float(profile.get("dpi_scale") or 1)
    screen_w = int(profile["width"] / scale)
    screen_h = int(profile["height"] / scale)
    window.update_idletasks()
    min_w, min_h = window.winfo_reqwidth(), window.winfo_reqheight()
    try:
        declared = window.minsize()
        if declared and declared[0] > 1:
            min_w, min_h = int(declared[0]), int(declared[1])
    except Exception:
        pass
    min_fits = min_w <= FLOOR_WIDTH and min_h <= FLOOR_HEIGHT

    faults: list[str] = []
    for label, (w, h) in (("min", (min_w, min_h)),
                          ("screen", (min(screen_w, max(min_w, screen_w)),
                                      min(screen_h, max(min_h, screen_h))))):
        window.geometry(f"{w}x{h}+0+0")
        window.update_idletasks()
        window.update()
        faults += [f"[{label}] {f}"
                   for f in checks_module.run_zubi(window, window_name)]

    window.deiconify()
    window.lift()
    window.update()
    try:
        from PIL import ImageGrab
    except ImportError as error:
        raise RuntimeError("Tk screenshots need Pillow (pip install pillow)"
                           ) from error
    box = (window.winfo_rootx(), window.winfo_rooty(),
           window.winfo_rootx() + window.winfo_width(),
           window.winfo_rooty() + window.winfo_height())
    ImageGrab.grab(bbox=box).save(out, "PNG")
    starved = [f for f in faults if "EMPTY BAND" in f]
    return {
        "ok": True,
        "min": [min_w, min_h],
        "size": [screen_w, screen_h],
        # Tk exposes no per-widget minimum, so `clipped` counts what the Tk
        # check library CAN measure; the gap is documented in the template.
        "checks": {"clipped": len(faults) - len(starved),
                   "starved": len(starved), "min_fits": bool(min_fits)},
        "faults": faults,
    }


def cmd_shot_one(args, ctx: Context) -> int:
    """Hidden: one window, one profile, in this process's own env."""
    registry, registry_path = load_registry(ctx.root)
    out = Path(args.out)
    result_file = Path(args.result)
    try:
        if registry is None:
            raise RuntimeError(f"no registry at {registry_path}")
        if args.window not in registry.WINDOWS:
            raise RuntimeError(f"window {args.window!r} not in WINDOWS "
                               f"({', '.join(registry.WINDOWS)})")
        profile = ctx.profile(args.profile)
        toolkit = getattr(registry, "TOOLKIT", "qt").lower()
        if toolkit == "qt":
            result = _shot_qt(registry, args.window, profile, out)
        elif toolkit == "tk":
            result = _shot_tk(registry, args.window, profile, out)
        else:
            raise RuntimeError(f"unknown TOOLKIT {toolkit!r} (qt|tk)")
    except BaseException as error:                # a factory may raise anything
        import traceback

        traceback.print_exc()
        result = {"ok": False,
                  "error": f"{type(error).__name__}: {error}"}
    result_file.write_text(json.dumps(result), encoding="utf-8")
    return 0 if result.get("ok") else 1


