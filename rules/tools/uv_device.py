"""`uv device` - the product on something that is not this machine.

Web: Chromium through Playwright with the profile's viewport, device pixel
ratio, CPU throttling and network conditions (CDP), a full-page screenshot and
two checks - horizontal scroll, and tap targets below 44 px. Android: `adb` on
a connected phone or emulator. A missing prerequisite is a `kind: unavailable`
row and a loud line on stderr, never a silent pass.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

from uv_core import (TAP_TARGET_PX, Context, command_line, import_from_path,
                     warn)

# --------------------------------------------------------------------------
# uv device - web (Playwright) and android (adb)
# --------------------------------------------------------------------------

_TAP_TARGET_JS = """
() => {
  const sel = 'a,button,input,select,textarea,summary,label,[role=button],' +
              '[role=link],[role=tab],[onclick],[tabindex]:not([tabindex="-1"])';
  const small = [];
  for (const el of document.querySelectorAll(sel)) {
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' ||
        style.pointerEvents === 'none') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (Math.min(r.width, r.height) < %d) {
      small.push(el.tagName.toLowerCase() +
        (el.id ? '#' + el.id : '') + ' ' +
        Math.round(r.width) + 'x' + Math.round(r.height));
    }
  }
  const doc = document.scrollingElement || document.documentElement;
  return {h_scroll: doc.scrollWidth > doc.clientWidth + 1,
          scroll_width: doc.scrollWidth, client_width: doc.clientWidth,
          small: small.slice(0, 25), small_total: small.length};
}
""" % TAP_TARGET_PX


def _ensure_playwright() -> str | None:
    """Returns None when Playwright + Chromium are usable, else the reason.
    One-time dev setup (pip install / browser download) is attempted once."""
    if importlib.util.find_spec("playwright") is None:
        warn("playwright not installed - installing (one-time dev setup)")
        if subprocess.run([sys.executable, "-m", "pip", "install",
                           "playwright"]).returncode != 0:
            return "playwright is not installed and pip install failed"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        return f"playwright import failed: {error}"
    with sync_playwright() as play:
        if Path(play.chromium.executable_path).exists():
            return None
    warn("chromium not downloaded - running `playwright install chromium`")
    if subprocess.run([sys.executable, "-m", "playwright", "install",
                       "chromium"]).returncode != 0:
        return "chromium browser is missing and `playwright install` failed"
    return None


def _device_web(args, ctx: Context, profile: dict, ident: str, cmd: str) -> int:
    reason = _ensure_playwright()
    if reason:
        ctx.ev.unavailable(ident, cmd, reason, profile=args.profile)
        return 3
    from playwright.sync_api import sync_playwright

    png = ctx.ev.dir / f"device-{ident[3:]}-{args.profile}.png"
    conditions = ctx.devices.get("network_conditions", {}).get(
        profile.get("network") or "", None)
    started = time.perf_counter()
    with sync_playwright() as play:
        browser = play.chromium.launch()
        context = browser.new_context(
            viewport={"width": profile["width"], "height": profile["height"]},
            device_scale_factor=profile.get("dpr", 1),
            is_mobile=bool(profile.get("mobile")),
            has_touch=bool(profile.get("mobile")))
        page = context.new_page()
        cdp = context.new_cdp_session(page)
        throttle = float(profile.get("cpu_throttle") or 1)
        if throttle > 1:
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": throttle})
        if conditions:
            cdp.send("Network.enable", {})
            cdp.send("Network.emulateNetworkConditions", {
                "offline": bool(conditions.get("offline")),
                "latency": conditions.get("latency", 0),
                "downloadThroughput": conditions.get("download", -1),
                "uploadThroughput": conditions.get("upload", -1)})
        try:
            page.goto(args.target, wait_until="load",
                      timeout=int(args.timeout * 1000))
            page.wait_for_timeout(500)
            if args.flow:
                _run_flow(Path(args.flow), page)
            checks = page.evaluate(_TAP_TARGET_JS)
            page.screenshot(path=str(png), full_page=True)
            error = None
        except Exception as failure:
            checks, error = {}, f"{type(failure).__name__}: {failure}"
        finally:
            context.close()
            browser.close()
    load_ms = round((time.perf_counter() - started) * 1000)
    if error:
        ctx.ev.unavailable(ident, cmd, f"{args.target}: {error}",
                           profile=args.profile)
        return 3
    row_checks = {"h_scroll": bool(checks["h_scroll"]),
                  "tap_targets_ok": checks["small_total"] == 0}
    rc = 0 if (not row_checks["h_scroll"] and row_checks["tap_targets_ok"]) else 1
    summary = (f"{args.profile} {profile['width']}x{profile['height']}@"
               f"{profile.get('dpr', 1)}x - "
               f"{'H-SCROLL ' + str(checks['scroll_width']) + '>' + str(checks['client_width']) if row_checks['h_scroll'] else 'no h-scroll'}"
               f", {checks['small_total']} tap targets < {TAP_TARGET_PX}px"
               f", load {load_ms} ms")
    if checks["small"]:
        summary += " | " + ", ".join(checks["small"][:4])
    ctx.ev.append(ident, "device", cmd, rc, summary, png,
                  profile=args.profile, checks=row_checks, start_ms=load_ms)
    return rc


def _run_flow(path: Path, page) -> None:
    """A project's own interaction script: a module with `def flow(page)`."""
    if not path.is_file():
        raise RuntimeError(f"flow script not found: {path}")
    module = import_from_path("_uv_flow", path)
    module.flow(page)


def _sdk_tool(name: str, *rel: str) -> str | None:
    """`adb`/`emulator` from PATH, else from the Android SDK the OS knows —
    `ANDROID_HOME` / `ANDROID_SDK_ROOT`, then the SDK's default install
    folder under the CURRENT user's profile. Never the owner's path."""
    import os
    from shutil import which
    found = which(name)
    if found:
        return found
    roots = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk"),
             os.path.expanduser("~/Android/Sdk"),
             os.path.expanduser("~/Library/Android/sdk")]
    for root in roots:
        if not root:
            continue
        candidate = Path(root).joinpath(*rel)
        if candidate.is_file():
            return str(candidate)
    return None


def _adb() -> str | None:
    return _sdk_tool("adb", "platform-tools", "adb.exe")


def _adb_devices(adb: str) -> list[str]:
    out = subprocess.run([adb, "devices"], capture_output=True, text=True).stdout
    return [line.split("\t")[0] for line in out.splitlines()[1:]
            if line.strip().endswith("device")]


def _list_avds() -> list[str]:
    emulator = _sdk_tool("emulator", "emulator", "emulator.exe")
    if not emulator:
        return []
    out = subprocess.run([emulator, "-list-avds"],
                         capture_output=True, text=True).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def _device_android(args, ctx: Context, profile: dict,
                    ident: str, cmd: str) -> int:
    adb = _adb()
    if adb is None:
        ctx.ev.unavailable(ident, cmd, "adb not found (Android SDK "
                                       "platform-tools not installed)",
                           profile=args.profile)
        return 3
    serials = _adb_devices(adb)
    if not serials:
        avds = _list_avds()
        if not avds:
            ctx.ev.unavailable(ident, cmd, "no Android device or emulator "
                                           "connected and no AVD exists",
                               profile=args.profile)
            return 3
        if not args.start_emulator:
            ctx.ev.unavailable(ident, cmd, f"no device connected; AVD(s) "
                               f"available ({', '.join(avds)}) - rerun with "
                               "--start-emulator to boot one",
                               profile=args.profile)
            return 3
        emulator = _sdk_tool("emulator", "emulator", "emulator.exe")
        warn(f"booting AVD {avds[0]} headless and silent - this takes a minute")
        # HEADLESS AND SILENT, always: a virtual device is the agent's eye,
        # never a window or a sound on the owner's desk (owner decree
        # 2026-08-18). Screenshots come from `adb exec-out screencap`.
        subprocess.Popen([emulator, "-avd", avds[0], "-no-snapshot-save",
                          "-no-window", "-no-audio", "-no-boot-anim",
                          "-gpu", "swiftshader_indirect"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([adb, "wait-for-device"], timeout=args.timeout * 4)
        serials = _adb_devices(adb)
        if not serials:
            ctx.ev.unavailable(ident, cmd, f"AVD {avds[0]} did not come up",
                               profile=args.profile)
            return 3
    serial = args.serial or serials[0]
    shell = [adb, "-s", serial]
    started = time.perf_counter()
    package = args.package
    target = args.target or ""
    if target.endswith(".apk"):
        install = subprocess.run(shell + ["install", "-r", target],
                                 capture_output=True, text=True)
        if install.returncode != 0:
            ctx.ev.unavailable(ident, cmd,
                               f"adb install failed: {install.stdout.strip()[:200]}",
                               profile=args.profile)
            return 3
    elif target:
        package = package or target
    orientation = (profile.get("android") or {}).get("orientation", "portrait")
    subprocess.run(shell + ["shell", "settings", "put", "system",
                            "accelerometer_rotation", "0"],
                   capture_output=True)
    subprocess.run(shell + ["shell", "settings", "put", "system",
                            "user_rotation",
                            "1" if orientation == "landscape" else "0"],
                   capture_output=True)
    if package:
        subprocess.run(shell + ["shell", "monkey", "-p", package,
                                "-c", "android.intent.category.LAUNCHER", "1"],
                       capture_output=True, text=True)
        time.sleep(min(args.timeout, 6))
    png = ctx.ev.dir / f"device-{ident[3:]}-{args.profile}.png"
    grab = subprocess.run(shell + ["exec-out", "screencap", "-p"],
                          capture_output=True)
    if grab.returncode != 0 or not grab.stdout:
        ctx.ev.unavailable(ident, cmd, "adb screencap produced nothing",
                           profile=args.profile)
        return 3
    png.write_bytes(grab.stdout.replace(b"\r\n", b"\n")
                    if grab.stdout[:8] != b"\x89PNG\r\n\x1a\n" else grab.stdout)
    elapsed = round((time.perf_counter() - started) * 1000)
    summary = (f"{args.profile} on {serial} ({orientation})"
               f"{' - ' + package if package else ''}, screencap in {elapsed} ms")
    ctx.ev.append(ident, "device", cmd, 0, summary, png,
                  profile=args.profile, checks={"screencap": True},
                  start_ms=elapsed)
    return 0


def cmd_device(args, ctx: Context) -> int:
    profile = ctx.profile(args.profile)
    ident = ctx.ev.reserve()
    cmd = command_line(["device", args.profile, args.target or ""])
    kind = profile.get("kind")
    if kind == "web" and not (args.target or "").startswith(("http", "file:")):
        kind = "android"                # an apk/package on a phone profile
    if kind == "android":
        return _device_android(args, ctx, profile, ident, cmd)
    if kind != "web":
        ctx.ev.unavailable(ident, cmd,
                           f"profile {args.profile} is kind {profile.get('kind')} "
                           "- `uv device` needs a web or android profile",
                           profile=args.profile)
        return 3
    return _device_web(args, ctx, profile, ident, cmd)


