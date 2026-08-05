"""Guard test - THE SPACE & LEGIBILITY LAW, runtime half, Qt (rules/GUI.md).

TEMPLATE for PySide6/PyQt projects. Copy to `tests/test_layout_audit.py` and
fill in the WINDOWS registry - nothing else should need editing.

It opens every window OFFSCREEN at its declared minimum size and at a larger
size, walks the whole widget tree, and fails on exactly the three things the
owner keeps reporting by hand:

  A. CLIPPED      - a widget got less room than it minimally needs
  B. ELIDED       - text does not fit its own element ("shift+tab" -> "ift+tab")
  C. SCROLL+SLACK - something scrolls while a spacer in the same window holds
                    unused space (the 300-px-empty-dialog screenshot)

plus the precondition the law puts on every window: a DECLARED MINIMUM SIZE.

Runs headless (QT_QPA_PLATFORM=offscreen), so it belongs in CI and in the Stop
hook like any other guard.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QCheckBox,
                               QLabel, QLineEdit, QPushButton, QSpacerItem,
                               QWidget)

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

# px of slack tolerated before a spacer counts as "unused space"
SLACK_TOLERANCE = 24

# px of padding assumed between an element's frame and its text
TEXT_PADDING = 8


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def walk(widget: QWidget):
    yield widget
    for child in widget.findChildren(QWidget):
        if child.isVisible():
            yield child


def check_declared_minimum(window: QWidget) -> list[str]:
    minimum = window.minimumSize()
    if minimum.width() > 0 and minimum.height() > 0:
        return []
    return ["no declared minimum size - the law requires one, COMPUTED from "
            "the longest real content (setMinimumSize / setMinimumWidth)"]


def check_clipping(window: QWidget) -> list[str]:
    problems = []
    for widget in walk(window):
        need: QSize = widget.minimumSizeHint()
        if need.width() > widget.width() or need.height() > widget.height():
            problems.append(
                f"CLIPPED {widget.__class__.__name__} "
                f"'{widget.objectName() or '-'}': has "
                f"{widget.width()}x{widget.height()}, needs at least "
                f"{need.width()}x{need.height()}")
    return problems


def visible_text(widget: QWidget) -> str:
    if isinstance(widget, (QLabel, QPushButton, QCheckBox)):
        return widget.text()
    if isinstance(widget, QLineEdit):
        return widget.text() or widget.placeholderText()
    return ""


def check_elision(window: QWidget) -> list[str]:
    problems = []
    for widget in walk(window):
        text = visible_text(widget)
        if not text:
            continue
        metrics = widget.fontMetrics()
        available = widget.contentsRect().width() - TEXT_PADDING
        if isinstance(widget, QLabel) and widget.wordWrap():
            wanted = metrics.boundingRect(
                0, 0, max(available, 1), 10_000, 0x1000, text).height()
            if wanted > widget.contentsRect().height():
                problems.append(
                    f"ELIDED (wrapped text taller than its element) "
                    f"{widget.__class__.__name__} '{text[:40]}': needs "
                    f"{wanted}px height, has {widget.contentsRect().height()}")
            continue
        wanted = metrics.horizontalAdvance(text)
        if wanted > available:
            problems.append(
                f"ELIDED {widget.__class__.__name__} '{text[:40]}': text needs "
                f"{wanted}px, element offers {available}px")
    return problems


def ancestor_spacer_slack(widget: QWidget, window: QWidget) -> list[str]:
    """Spacers between `widget` and `window` that were handed real space."""
    slack = []
    node = widget.parentWidget()
    while node is not None:
        layout = node.layout()
        if layout is not None:
            for index in range(layout.count()):
                item = layout.itemAt(index)
                if isinstance(item, QSpacerItem):
                    geometry = item.geometry()
                    if max(geometry.width(), geometry.height()) > SLACK_TOLERANCE:
                        slack.append(
                            f"{node.__class__.__name__}"
                            f"'{node.objectName() or '-'}' holds a spacer of "
                            f"{geometry.width()}x{geometry.height()}px")
        if node is window:
            break
        node = node.parentWidget()
    return slack


def check_scroll_with_free_space(window: QWidget) -> list[str]:
    problems = []
    for widget in walk(window):
        if not isinstance(widget, QAbstractScrollArea):
            continue
        for name, bar in (("vertically", widget.verticalScrollBar()),
                          ("horizontally", widget.horizontalScrollBar())):
            if bar is None or bar.maximum() <= 0:
                continue
            slack = ancestor_spacer_slack(widget, window)
            if slack:
                problems.append(
                    f"SCROLL+SLACK {widget.__class__.__name__} "
                    f"'{widget.objectName() or '-'}' scrolls {name} while the "
                    f"same window holds unused space: " + "; ".join(slack)
                    + " - ladder step 1: the starving element takes the free "
                      "space before any scrollbar appears")
    return problems


def audit(window: QWidget, label: str) -> list[str]:
    return [f"[{label}] {problem}" for problem in (
        check_clipping(window)
        + check_elision(window)
        + check_scroll_with_free_space(window))]


@pytest.mark.skipif(not WINDOWS, reason="WINDOWS registry is empty - fill it")
@pytest.mark.parametrize("name,factory", WINDOWS, ids=lambda v: getattr(v, "__name__", str(v)))
def test_layout_audit(app: QApplication, name: str, factory) -> None:
    window: QWidget = factory()
    window.show()
    app.processEvents()

    problems = [f"[{name}] {p}" for p in check_declared_minimum(window)]
    minimum = window.minimumSize()
    sizes = [("minimum", minimum.width(), minimum.height()),
             ("minimum+50%", int(minimum.width() * 1.5),
              int(minimum.height() * 1.5))]
    for label, width, height in sizes:
        if width <= 0 or height <= 0:
            continue
        window.resize(width, height)
        app.processEvents()
        problems += audit(window, f"{name} @ {label} {width}x{height}")

    window.close()
    assert not problems, (
        "THE SPACE & LEGIBILITY LAW (rules/GUI.md) - runtime audit failed:\n  "
        + "\n  ".join(problems)
        + "\nLadder: (1) the starving element takes the free space, "
          "(2) reflow into more rows, (3) raise the window minimum, "
          "(4) scroll only when the window is genuinely full."
    )
