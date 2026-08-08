"""Guard test - THE SPACE & LEGIBILITY LAW, runtime half, Qt (rules/GUI.md).

TEMPLATE for PySide6/PyQt projects. Copy BOTH this file and its companion
`layout_checks_qt.py` (the check library - all check_* functions, thresholds
and the ALG-8 live-profile plumbing live there) to `tests/`, then fill in the
WINDOWS registry below - nothing else should need editing (ALG-8's
live_profile_source() is the one optional override, imported straight from
the library).

It opens every window OFFSCREEN - and with WA_DontShowOnScreen, so a guard run
never flashes a window across the owner's desktop (rules/GUI.md -> LAW Silent
Audits) - at its declared minimum size and at a larger size, walks the whole
widget tree via `layout_checks_qt.audit()`, and fails on exactly the three
things the owner keeps reporting by hand (CLIPPED / ELIDED / SCROLL+SLACK),
the declared-minimum precondition, and every Zubi v2 ALG-1..ALG-9 finding
(rules/GUI.md -> Zubi v2) - see that module's docstring for the full list.

Runs headless (QT_QPA_PLATFORM=offscreen), so it belongs in CI and in the Stop
hook like any other guard.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from layout_checks_qt import (_window_image, check_contrast,
                              check_declared_minimum, check_radius,
                              check_row_occupancy, check_space_ceiling,
                              check_tooltips, check_uniform_siblings,
                              check_extreme_states, live_profile_copy,
                              live_profile_source, settle, state_invariants)

# --- CONFIGURATION (per project) -------------------------------------------

# Every top-level window and dialog of the project, as (name, factory).
# A window missing from this list is a hole in the guard - keep it complete.
#
#   from gui.sets_dialog import SetsDialog
#   WINDOWS = [("SetsDialog", lambda: SetsDialog(config=demo_config()))]
#
# Factories must build the window in its FULLEST realistic state (longest real
# strings, most rows) - an empty window proves nothing.
WINDOWS: list[tuple[str, object]] = []

# Screenshots the agent must OPEN and grade (>= 8/10) before the session may
# end - the Stop half of rules/hooks/layout_guard.py checks both.
SHOT_DIR = Path(__file__).resolve().parents[1] / ".claude" / "shots"


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def capture(window: QWidget, name: str) -> Path:
    """The screenshot the agent must OPEN and grade. A GUI nobody looked at is
    a GUI nobody checked."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SHOT_DIR / f"{name}.png"
    window.grab().save(str(path), "PNG")
    return path


def audit(window: QWidget, label: str, at_minimum: bool = False) -> list[str]:
    """Every check, in one pass over one state of one window.

    `at_minimum` adds the checks the rulebook defines AT the minimum size
    (ALG-7 reads the pixels of a window that has no room to spare)."""
    image = _window_image(window)
    problems = (state_invariants(window)
                + check_contrast(window, image)
                + check_tooltips(window)
                + check_space_ceiling(window)
                + check_uniform_siblings(window)
                + check_radius(window))
    if at_minimum:
        problems += check_row_occupancy(window, image)
    problems += check_extreme_states(window)
    return [f"[{label}] {problem}" for problem in problems]


# --- the walk ---------------------------------------------------------------


def audit_window(app: QApplication, name: str, factory,
                 profile: str = "") -> list[str]:
    """Build one window, audit it at its minimum and at +50%, screenshot it.

    Silent by law (rules/GUI.md -> LAW Silent Audits): WA_DontShowOnScreen is
    set BEFORE the first show(), on top of the offscreen platform."""
    window: QWidget = factory()
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.show()
    app.processEvents()

    tag = f"{name} ({profile})" if profile else name
    problems = [f"[{tag}] {problem}"
                for problem in check_declared_minimum(window)]
    minimum = window.minimumSize()
    sizes = [("minimum", minimum.width(), minimum.height()),
             ("minimum+50%", int(minimum.width() * 1.5),
              int(minimum.height() * 1.5))]
    for label, width, height in sizes:
        if width <= 0 or height <= 0:
            continue
        window.resize(width, height)
        settle(window)
        problems += audit(window, f"{tag} @ {label} {width}x{height}",
                          at_minimum=(label == "minimum"))
        if label == "minimum":
            shot = capture(window, name if not profile else f"{name}-live")
            print(f"SHOT {shot} - MIN {width}x{height} - now OPEN it and "
                  f"GRADE it (>= 8/10) in .claude/layout-proof.md")

    window.close()
    return problems


@pytest.mark.skipif(not WINDOWS, reason="WINDOWS registry is empty - fill it")
@pytest.mark.parametrize("name,factory", WINDOWS, ids=lambda v: getattr(v, "__name__", str(v)))
def test_layout_audit(app: QApplication, name: str, factory) -> None:
    problems = audit_window(app, name, factory)

    # ALG-8: the same walk again, on a copy of the owner's real settings.
    source = live_profile_source()
    if source is not None:
        if not Path(source).is_file():
            problems.append(
                f"[{name}] ALG-8 LIVE PROFILE (rules/GUI.md -> Zubi v2): "
                f"live_profile_source() points at {source}, which does not "
                "exist - return None when the owner's profile is absent, or "
                "fix the path; a silently skipped live pass is the hole this "
                "rule closes")
        else:
            with live_profile_copy() as copy:
                problems += audit_window(app, name, factory,
                                         profile=f"live profile {copy.name}")

    assert not problems, (
        "THE SPACE & LEGIBILITY LAW (rules/GUI.md) - runtime audit failed:\n  "
        + "\n  ".join(problems)
        + "\nLadder: (1) the starving element takes the free space, "
          "(2) reflow into more rows, (3) raise the window minimum, "
          "(4) scroll only when the window is genuinely full."
          "\nZubi v2 (rules/GUI.md -> Zubi v2): an ALG- finding is measured, "
          "not felt - the message says what to change."
    )
