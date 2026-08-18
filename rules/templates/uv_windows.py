"""SKELETON - copy to `<project>/.claude/uv_windows.py` and fill in.

The window registry `uv shot` imports (rules/tools/uv.py, rules/howto/runner.md).
It answers three questions and nothing else:

    TOOLKIT             "qt" or "tk"
    WINDOWS             {name: factory}, factory() -> a top-level window
    MANDATORY_PROFILES  the profiles every window must survive

Rules for this file:

* It is imported in the PARENT process before any toolkit env is set, so keep
  the module level free of toolkit imports - import inside each factory.
* A factory builds its window in the FULLEST realistic state it will ever show.
  An empty window passes every check and proves nothing.
* One process per (window, profile) - a factory that crashes costs one row
  (`kind: unavailable`), never the whole run.
* `prepare()` is optional and runs once per child process after the toolkit
  application exists: use it for fonts, sys.path or test data.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Where the application package lives, if it is not the project root.
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


# --- which toolkit the windows are built with ------------------------------
TOOLKIT = "qt"                                    # "qt" (PySide6) or "tk"

# --- profiles from rules/devices.json that every window must survive --------
# At least one must NOT be pc-owner - we build for others.
MANDATORY_PROFILES = ["laptop-avg", "pc-low"]


def prepare() -> None:
    """Optional, runs once per shot process after the app object exists.

    Qt offscreen starts with an EMPTY font database, which renders every
    label as tofu boxes and measures a window nobody will ever see. If the
    project has a font-provisioning helper, call it here."""
    try:
        from tests.offscreen_fonts import provision
    except ImportError:
        return
    provision()


# --- Qt example -------------------------------------------------------------


def make_main_window():
    """A Qt top-level widget in its fullest realistic state."""
    from app.main_window import MainWindow          # import INSIDE the factory
    from app.settings_store import Settings

    return MainWindow(Settings())


def make_settings_dialog():
    from app.settings_dialog import SettingsDialog
    from app.settings_store import Settings

    dialog = SettingsDialog(Settings())
    dialog.select_section("Appearance")             # the fullest page
    return dialog


# --- Tk example (delete the Qt block above and set TOOLKIT = "tk") ----------
#
# def make_main_window():
#     import customtkinter as ctk
#
#     from app.ui.main import MainWindow
#
#     root = ctk.CTk()                # the factory owns its own root/Toplevel
#     window = MainWindow(root)
#     window.load_demo_project()      # fullest realistic state
#     return root


WINDOWS = {
    "MainWindow": make_main_window,
    "SettingsDialog": make_settings_dialog,
}
