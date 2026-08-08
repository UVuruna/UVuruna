"""Check library - THE SPACE & LEGIBILITY LAW, runtime half, Qt (rules/GUI.md
-> Zubi v2). Companion to `test_layout_audit_qt.py`, the thin pytest entry
that imports this module - copy BOTH files together (the entry file's
docstring carries the template usage instructions and the full A/B/C +
ALG-1..ALG-9 rule list).
Every check degrades to an empty list on a window that has none of what it
looks for. No AI in the loop anywhere in this file - every finding is plain
code, and every finding names its rule and what to change.
"""

from __future__ import annotations
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontInfo, QImage
from PySide6.QtWidgets import (QAbstractScrollArea, QAbstractSlider,
                               QApplication, QCheckBox, QComboBox,
                               QDoubleSpinBox, QGroupBox, QLabel, QLayout,
                               QLineEdit, QPushButton, QRadioButton,
                               QScrollBar, QSpacerItem, QSpinBox, QToolButton,
                               QWidget)

# --- CONFIGURATION (thresholds - a project that must bend one bends it here,
# with the reason written beside it) ------------------------------------------
# The screen every window must survive. A declared minimum bigger than this is
# the absurd-minimum bug (a two-item menu demanding 6000px): REFLOW, never widen.
# Raising it needs `.claude/layout-frame.json` with a stated reason.
FLOOR_WIDTH, FLOOR_HEIGHT = 1280, 720
# px of slack tolerated before a spacer counts as "unused space"
SLACK_TOLERANCE = 24
# px of padding assumed between an element's frame and its text
TEXT_PADDING = 8

# --- ZUBI v2 thresholds (rules/GUI.md -> Zubi v2) ---------------------------
# These are the numbers of the rulebook, in ONE place: a project that must bend
# one bends it here, with the reason written beside it.
# ALG-4: the working width of a desktop settings page, and the ceiling that has
# no exception and no written excuse.
WORKING_WIDTH = 1600
ABSOLUTE_WIDTH, ABSOLUTE_HEIGHT = 2560, 1440
# ALG-2: WCAG 2.1 contrast floors. The large-text floor needs BOTH size and bold.
CONTRAST_MIN = 4.5
CONTRAST_MIN_LARGE = 3.0
LARGE_TEXT_PX = 18
# ALG-3: a plain-text tooltip longer than this renders as one unwrapped line.
TOOLTIP_MAX_CHARS = 72
# ALG-5: how far two same-kind siblings may differ before it reads as ragged.
SIBLING_TOLERANCE = 2
# ALG-1: a combo box with more items than this is not a "small enum" - walking
# 300 fonts would cost minutes and prove nothing new.
ENUM_STATE_LIMIT = 12
# ALG-1: px a child may leave the window rect by before it counts as outside
# (rounding in mapTo/frame geometry, not a layout fault).
GEOMETRY_TOLERANCE = 1
# ALG-7: band height, how empty a right half must be, and how many bands in a
# row are needed before the pattern counts. Deliberately conservative.
BAND_HEIGHT = 48
BAND_EMPTY_RATIO = 0.55
BAND_MIN_RUN = 2
BAND_CONTENT_RATIO = 0.03
BAND_COLOR_TOLERANCE = 12
# ALG-9: the concepts a section may be named for.
CONCEPT_WORDS = ("size", "width", "height", "color", "colour", "opacity",
                 "font")
# ALG-6: names that mark genuinely round content (exempt), and the comment a
# stylesheet rule can carry to say the same thing.
CIRCLE_CONTENT_RE = re.compile(r"swatch|avatar|circle|dot\b|orb|bullet",
                               re.IGNORECASE)
CIRCLE_CONTENT_MARKER = "radius-ok: circle content"
# ALG-8: the environment variable the live-profile copy is published under, for
# projects whose settings store already honours an env override.
PROFILE_ENV = "LAYOUT_AUDIT_PROFILE"
def walk(widget: QWidget):
    yield widget
    for child in widget.findChildren(QWidget):
        if child.isVisible():
            yield child
def settle(window: QWidget) -> None:
    """Two passes: the first installs the layout, the second lets scroll areas
    react to the geometry it produced."""
    instance = QApplication.instance()
    if instance is None:
        return
    instance.processEvents()
    instance.processEvents()

def check_declared_minimum(window: QWidget) -> list[str]:
    minimum = window.minimumSize()
    if minimum.width() <= 0 or minimum.height() <= 0:
        return ["no declared minimum size - the law requires one, COMPUTED "
                "from the longest real content (setMinimumSize)"]
    if minimum.width() > FLOOR_WIDTH or minimum.height() > FLOOR_HEIGHT:
        return [f"ABSURD MINIMUM {minimum.width()}x{minimum.height()} - it does "
                f"not fit the screen floor {FLOOR_WIDTH}x{FLOOR_HEIGHT}, so "
                "the window demands a screen the user does not have. REFLOW "
                "it (ladder step 2); widening your way out is the bug itself"]
    return []
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
        # A QLabel paints straight into its contentsRect; framed controls
        # lose their frame plus padding.
        padding = 0 if isinstance(widget, QLabel) else TEXT_PADDING
        available = widget.contentsRect().width() - padding
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
def ancestor_spacer_slack(widget: QWidget, window: QWidget,
                          vertical: bool) -> list[str]:
    """Spacers between `widget` and `window` handed real space IN THE
    SCROLLING AXIS - a 328x0 stretch holds no vertical space and must
    not convict a legitimately scrolling list (Aviator, 2026-08-06)."""
    slack = []
    node = widget.parentWidget()
    while node is not None:
        layout = node.layout()
        if layout is not None:
            for index in range(layout.count()):
                item = layout.itemAt(index)
                if isinstance(item, QSpacerItem):
                    geometry = item.geometry()
                    extent = (geometry.height() if vertical
                              else geometry.width())
                    if extent > SLACK_TOLERANCE:
                        slack.append(
                            f"{node.__class__.__name__}"
                            f"'{node.objectName() or '-'}' holds a spacer of "
                            f"{geometry.width()}x{geometry.height()}px")
        if node is window:
            break
        node = node.parentWidget()
    return slack
def check_scroll_with_free_space(window: QWidget) -> list[str]:
    """C. SCROLL+SLACK, and ALG-4's half of the same subject: a page that
    scrolls HORIZONTALLY fails at every step of the ladder, slack or no
    slack (rules/GUI.md -> Zubi v2, ALG-4)."""
    problems = []
    for widget in walk(window):
        if not isinstance(widget, QAbstractScrollArea):
            continue
        for name, bar in (("vertically", widget.verticalScrollBar()),
                          ("horizontally", widget.horizontalScrollBar())):
            if bar is None or bar.maximum() <= 0:
                continue
            if name == "horizontally":
                problems.append(
                    f"ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2) "
                    f"{widget.__class__.__name__} "
                    f"'{widget.objectName() or '-'}' scrolls HORIZONTALLY "
                    f"({bar.maximum()}px past its viewport) - horizontal "
                    "scroll on a settings page fails at every step of the "
                    "ladder, with or without free space. REFLOW the row into "
                    "columns/rows (ladder step 2); a wider window is not the "
                    "answer either")
            slack = ancestor_spacer_slack(
                widget, window, vertical=(name == "vertically"))
            if slack:
                problems.append(
                    f"SCROLL+SLACK {widget.__class__.__name__} "
                    f"'{widget.objectName() or '-'}' scrolls {name} while the "
                    f"same window holds unused space: " + "; ".join(slack)
                    + " - ladder step 1: the starving element takes the free "
                      "space before any scrollbar appears")
    return problems

# --- shared plumbing for the ZUBI v2 checks ---------------------------------
def _ancestors(widget: QWidget, window: QWidget) -> list[QWidget] | None:
    """The chain from `widget` up to (not including) `window`, or None when
    the widget is not rooted in the window at all - a popup, a menu, a
    torn-off tool window. Coordinates of those cannot be mapped, so every
    geometric check skips them rather than inventing a number."""
    chain: list[QWidget] = []
    node = widget.parentWidget()
    while node is not None and node is not window:
        chain.append(node)
        node = node.parentWidget()
    if node is None:
        return None
    return chain
def _rect_in_window(widget: QWidget, window: QWidget) -> QRect | None:
    try:
        top_left: QPoint = widget.mapTo(window, QPoint(0, 0))
    except (RuntimeError, TypeError):
        return None
    return QRect(top_left, widget.size())
def _window_image(window: QWidget) -> QImage | None:
    pixmap = window.grab()
    if pixmap.isNull():
        return None
    return pixmap.toImage()
def _image_point(image: QImage, x: int, y: int) -> QColor | None:
    if x < 0 or y < 0 or x >= image.width() or y >= image.height():
        return None
    return QColor.fromRgb(image.pixel(x, y))
def _dominant_color(image: QImage, rect: QRect) -> QColor | None:
    """The background REALLY painted under `rect` - the whole point of ALG-2:
    what the pixels say, not what the palette claims (a stylesheet, a parent's
    gradient or a chip behind the label all change the answer).

    Two refinements the naive "most common pixel" needed, both found on real
    widgets: the rect is INSET by a few px so a 1px frame cannot out-vote the
    fill on a short control, and colours are counted in BUCKETS of 16 per
    channel so a vertical gradient (every row a different shade) still adds up
    to one background instead of losing to the border or to the text ink."""
    ratio = image.devicePixelRatio() or 1.0
    left, top = int(rect.left() * ratio), int(rect.top() * ratio)
    right, bottom = int(rect.right() * ratio), int(rect.bottom() * ratio)
    inset = min(3, (right - left) // 4, (bottom - top) // 4)
    left, top, right, bottom = (left + inset, top + inset,
                                right - inset, bottom - inset)
    if right < left or bottom < top:
        return None
    step_x = max(1, (right - left) // 48)
    step_y = max(1, (bottom - top) // 48)
    buckets: dict[tuple[int, int, int], list[int]] = {}
    for y in range(top, bottom + 1, step_y):
        for x in range(left, right + 1, step_x):
            if x < 0 or y < 0 or x >= image.width() or y >= image.height():
                continue
            color = QColor.fromRgb(image.pixel(x, y))
            key = (color.red() >> 4, color.green() >> 4, color.blue() >> 4)
            totals = buckets.setdefault(key, [0, 0, 0, 0])
            totals[0] += color.red()
            totals[1] += color.green()
            totals[2] += color.blue()
            totals[3] += 1
    if not buckets:
        return None
    totals = max(buckets.values(), key=lambda entry: entry[3])
    count = totals[3]
    return QColor(totals[0] // count, totals[1] // count, totals[2] // count)
def _relative_luminance(color: QColor) -> float:
    channels = []
    for value in (color.redF(), color.greenF(), color.blueF()):
        channels.append(value / 12.92 if value <= 0.03928
                        else ((value + 0.055) / 1.055) ** 2.4)
    return (0.2126 * channels[0] + 0.7152 * channels[1]
            + 0.0722 * channels[2])
def contrast_ratio(one: QColor, other: QColor) -> float:
    """WCAG 2.1 contrast ratio, 1.0 (invisible) to 21.0 (black on white)."""
    first, second = _relative_luminance(one), _relative_luminance(other)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)
_RULE_RE = re.compile(
    r"(?P<lead>(?:/\*.*?\*/\s*)*)(?P<selectors>[^{}/]+)\{(?P<body>[^{}]*)\}",
    re.DOTALL)
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
def _declarations(body: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for piece in _COMMENT_RE.sub(" ", body).split(";"):
        if ":" not in piece:
            continue
        key, _, value = piece.partition(":")
        found[key.strip().lower()] = value.strip()
    return found
def _parse_sheet(sheet: str) -> tuple[dict[str, str], list[tuple]]:
    """(declarations written without a selector, [(selectors, decls, raw)]).

    A BEST-EFFORT STATIC PARSE, and it must be read as one: it ignores Qt's
    specificity ordering, descendant combinators (only the last simple
    selector is matched), pseudo-states and attribute selectors, and it never
    sees a stylesheet applied from C++/QSS files at runtime. That is why every
    finding quotes the declaration it read - a wrong parse is then visible in
    the message instead of hiding inside a verdict."""
    if not sheet or not sheet.strip():
        return {}, []
    rules = []
    for match in _RULE_RE.finditer(sheet):
        selectors = [part.strip()
                     for part in match.group("selectors").split(",")
                     if part.strip()]
        raw = match.group("lead") + match.group(0)
        rules.append((selectors, _declarations(match.group("body")), raw))
    bare = {}
    if "{" not in sheet:
        bare = _declarations(sheet)
    return bare, rules
def _selector_matches(selector: str, widget: QWidget) -> bool:
    simple = selector.strip().split()[-1] if selector.strip() else ""
    simple = simple.split("::")[0].split(":")[0]
    simple = re.sub(r"\[[^\]]*\]", "", simple).strip()
    if simple in ("", "*"):
        return True
    name = None
    if "#" in simple:
        simple, _, name = simple.partition("#")
    if name and widget.objectName() != name:
        return False
    simple = simple.lstrip(".")
    if simple:
        classes = {klass.__name__ for klass in type(widget).__mro__}
        if simple not in classes:
            return False
    return True
def effective_style(widget: QWidget, window: QWidget) -> tuple[dict, str]:
    """(declarations in force on `widget`, the raw text they came from).

    Cascade order, weakest first: the application sheet, the window's, every
    ancestor's, then the widget's own. Best-effort - see _parse_sheet."""
    sheets = []
    instance = QApplication.instance()
    if instance is not None:
        sheets.append(instance.styleSheet())
    chain = _ancestors(widget, window)
    nodes = [window] + list(reversed(chain or [])) + [widget]
    for node in nodes:
        try:
            sheets.append(node.styleSheet())
        except RuntimeError:
            continue
    merged: dict[str, str] = {}
    raw_parts: list[str] = []
    for sheet in sheets:
        bare, rules = _parse_sheet(sheet or "")
        for selectors, decls, raw in rules:
            if any(_selector_matches(one, widget) for one in selectors):
                merged.update(decls)
                raw_parts.append(raw)
        if bare:
            merged.update(bare)
            raw_parts.append(sheet)
    return merged, "\n".join(raw_parts)
def _parse_color(text: str) -> QColor | None:
    text = text.strip().rstrip(";").strip()
    match = re.match(r"rgba?\s*\(([^)]*)\)", text, re.IGNORECASE)
    if match:
        parts = [piece.strip() for piece in match.group(1).split(",")]
        try:
            values = [int(round(float(piece.rstrip("%")))) for piece in parts]
        except ValueError:
            return None
        if len(values) >= 3:
            return QColor(values[0], values[1], values[2])
        return None
    color = QColor(text)
    return color if color.isValid() else None
def _length_px(token: str, widget: QWidget) -> float | None:
    match = re.match(r"^([0-9]*\.?[0-9]+)(px|pt|em|ex|%)?$", token.strip(),
                     re.IGNORECASE)
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "px").lower()
    if unit == "px":
        return number
    if unit == "pt":
        return number * 96.0 / 72.0
    if unit in ("em", "ex"):
        size = max(QFontInfo(widget.font()).pixelSize(), 1)
        return number * size * (1.0 if unit == "em" else 0.5)
    return number / 100.0 * max(widget.height(), 1)

# --- ALG-1  EXTREME STATE MATRIX --------------------------------------------
def check_outside_window(window: QWidget) -> list[str]:
    """Nothing paints outside the window rect. The ALG-1 invariant that a
    default-state audit can never see: a control's own extreme is what pushes
    a child over the edge."""
    problems = []
    frame = window.rect()
    for widget in walk(window):
        if widget is window or widget.isWindow():
            continue
        chain = _ancestors(widget, window)
        if chain is None:
            continue
        if any(isinstance(node, QAbstractScrollArea) for node in chain):
            continue        # a viewport clips by design; the scroll checks own it
        rect = _rect_in_window(widget, window)
        if rect is None or rect.isEmpty():
            continue
        over = (rect.left() < frame.left() - GEOMETRY_TOLERANCE
                or rect.top() < frame.top() - GEOMETRY_TOLERANCE
                or rect.right() > frame.right() + GEOMETRY_TOLERANCE
                or rect.bottom() > frame.bottom() + GEOMETRY_TOLERANCE)
        if over:
            problems.append(
                f"OUTSIDE WINDOW (rules/GUI.md -> Zubi v2, ALG-1) "
                f"{widget.__class__.__name__} "
                f"'{widget.objectName() or '-'}': sits at "
                f"{rect.left()},{rect.top()} {rect.width()}x{rect.height()} "
                f"which leaves the window rect {frame.width()}x"
                f"{frame.height()} - the user cannot see it. Put it back in "
                "the layout (a hand-placed child does not reflow), or grow "
                "the window minimum (ladder step 3)")
    return problems
def state_invariants(window: QWidget) -> list[str]:
    """What must hold in EVERY state - the default one and every extreme
    ALG-1 drives the window through."""
    return (check_clipping(window)
            + check_elision(window)
            + check_scroll_with_free_space(window)
            + check_outside_window(window))
def control_states(widget: QWidget):
    """(kind, values to visit, value to restore, setter) or None.

    QScrollBar is deliberately excluded: it is a subclass of QAbstractSlider
    but it is VIEW state, not a setting the user configures - driving it to
    its maximum only scrolls the view the scroll checks are already judging."""
    if isinstance(widget, QScrollBar):
        return None
    if isinstance(widget, (QAbstractSlider, QSpinBox, QDoubleSpinBox)):
        return ("value",
                [widget.minimum(), widget.value(), widget.maximum()],
                widget.value(), widget.setValue)
    if isinstance(widget, QCheckBox):
        return ("checked", [False, True], widget.isChecked(),
                widget.setChecked)
    if isinstance(widget, QComboBox) and 0 < widget.count() <= ENUM_STATE_LIMIT:
        return ("item", list(range(widget.count())), widget.currentIndex(),
                widget.setCurrentIndex)
    return None

def check_extreme_states(window: QWidget, invariants=None) -> list[str]:
    """ALG-1 - "tested" without extremes is not tested.

    Every numeric control is visited at minimum / current / maximum, every
    check box in both states, every small enum through all its items; after
    each change the window is re-settled (processEvents twice, so a signal
    handler's own layout work lands) and the invariants are re-run. Original
    values are restored afterwards, even when a handler raises.

    Only breakage the DEFAULT state does not already show is reported - the
    baseline belongs to the plain audit, and repeating it once per slider
    position would bury the new finding."""
    invariants = state_invariants if invariants is None else invariants
    baseline = set(invariants(window))
    problems: list[str] = []
    seen: set[tuple[str, str]] = set()
    for widget in list(walk(window)):
        try:
            plan = control_states(widget)
        except RuntimeError:
            continue
        if plan is None:
            continue
        kind, values, original, apply_value = plan
        label = (f"{widget.__class__.__name__} "
                 f"'{widget.objectName() or widget.accessibleName() or '-'}'")
        try:
            for value in values:
                try:
                    apply_value(value)
                except (RuntimeError, TypeError):
                    break
                settle(window)
                for problem in invariants(window):
                    if problem in baseline:
                        continue
                    key = (label, problem)
                    if key in seen:
                        continue
                    seen.add(key)
                    problems.append(
                        f"ALG-1 EXTREME STATE MATRIX (rules/GUI.md -> Zubi v2) "
                        f"{label} at {kind}={value}: {problem} - a state the "
                        "user can reach must satisfy the same rules as the "
                        "default one; fix the layout for the extreme, or "
                        "narrow the control's range")
        finally:
            try:
                apply_value(original)
                settle(window)
            except (RuntimeError, TypeError):
                pass
    return problems

# --- ALG-2  CONTRAST --------------------------------------------------------
TEXT_WIDGETS = (QLabel, QPushButton, QCheckBox, QRadioButton, QGroupBox)
_RICH_TEXT_RE = re.compile(
    r"<\s*(?:html|body|p|br|b|i|u|s|em|strong|span|div|table|tr|td|ul|ol|li"
    r"|font|code|pre|h[1-6])\b[^>]*>", re.IGNORECASE)
def is_rich_text(text: str) -> bool:
    checker = getattr(Qt, "mightBeRichText", None)
    if callable(checker):
        try:
            return bool(checker(text))
        except Exception:       # a Qt build without the QtGui namespace helper
            pass
    return bool(_RICH_TEXT_RE.search(text))
def widget_text(widget: QWidget) -> str:
    if isinstance(widget, QGroupBox):
        return widget.title()
    if isinstance(widget, (QLabel, QPushButton, QCheckBox, QRadioButton)):
        return widget.text()
    return ""
def font_pixel_size(widget: QWidget) -> int:
    """The rendered size of the widget's text, in px.

    QFontInfo answers -1 on a platform with no real font database (the
    offscreen plugin does exactly that), which would silently hand every
    element the strict 4.5:1 floor and make the large-text exemption
    unreachable. Fall back through point size and, last, the line height."""
    info = QFontInfo(widget.font())
    font = widget.font()
    for candidate in (info.pixelSize(), font.pixelSize()):
        if candidate > 0:
            return int(candidate)
    dpi = max(widget.logicalDpiY(), 72)
    for points in (info.pointSizeF(), font.pointSizeF()):
        if points > 0:
            return int(round(points * dpi / 72.0))
    return max(widget.fontMetrics().height(), 1)
def effective_foreground(widget: QWidget, window: QWidget) -> QColor:
    declarations, _ = effective_style(widget, window)
    declared = declarations.get("color")
    if declared:
        parsed = _parse_color(declared)
        if parsed is not None:
            return parsed
    return widget.palette().color(widget.foregroundRole())
def check_contrast(window: QWidget, image: QImage | None = None) -> list[str]:
    """ALG-2 - foreground against the background REALLY rendered under it.

    The background is sampled from window.grab() (see _dominant_color): what
    was really painted inside the widget's own rect. That is what catches
    white-on-light chips where the palette says the window is dark. Rich-text
    labels are skipped (their colours live in the markup, per-run, and a single
    foreground would be a guess); disabled widgets are skipped by rule.

    NOT covered: hover and pressed states. The rulebook asks for them, and a
    widget-tree walk cannot render them - reaching them needs synthetic mouse
    events per widget, which is a separate tooth. Until it exists, hover
    contrast stays with the grader's checklist (GRD-1)."""
    image = _window_image(window) if image is None else image
    if image is None or image.isNull():
        return []
    problems = []
    for widget in walk(window):
        if not isinstance(widget, TEXT_WIDGETS) or not widget.isEnabled():
            continue
        text = widget_text(widget).strip()
        if not text or is_rich_text(text):
            continue
        if _ancestors(widget, window) is None:
            continue
        rect = _rect_in_window(widget, window)
        if rect is None:
            continue
        rect = rect.intersected(window.rect())
        if isinstance(widget, QGroupBox):
            # Only the title band - the box's body is other widgets' business.
            rect = QRect(rect.left(), rect.top(), rect.width(),
                         min(rect.height(),
                             widget.fontMetrics().height() + TEXT_PADDING))
        if rect.width() < 4 or rect.height() < 4:
            continue
        foreground = effective_foreground(widget, window)
        background = _dominant_color(image, rect)
        if background is None or not foreground.isValid():
            continue
        pixels = font_pixel_size(widget)
        bold = QFontInfo(widget.font()).bold() or widget.font().bold()
        floor = (CONTRAST_MIN_LARGE if pixels >= LARGE_TEXT_PX and bold
                 else CONTRAST_MIN)
        ratio = contrast_ratio(foreground, background)
        if ratio < floor:
            problems.append(
                f"ALG-2 CONTRAST (rules/GUI.md -> Zubi v2) "
                f"{widget.__class__.__name__} "
                f"'{widget.objectName() or '-'}' '{text[:40]}': "
                f"{foreground.name()} on the rendered background "
                f"{background.name()} is {ratio:.2f}:1, below the "
                f"{floor}:1 floor for this text "
                f"({pixels}px{', bold' if bold else ''}) - "
                "darken the background or lighten the text until the ratio "
                f"reaches {floor}:1 (or make the text >= {LARGE_TEXT_PX}px AND "
                "bold, which lowers the floor to 3.0:1)")
    return problems

# --- ALG-3  HOVER GEOMETRY ---------------------------------------------------
def check_tooltips(window: QWidget) -> list[str]:
    """ALG-3 - a PLAIN QToolTip does not wrap. Qt word-wraps rich text only,
    so a long plain tooltip renders as ONE line as wide as its text: that is
    how a tooltip once drew wider than a 3840px screen. The widget-tree walk
    never sees the popup itself, so the length of the string is the measurable
    proxy."""
    problems = []
    for widget in walk(window):
        try:
            tip = (widget.toolTip() or "").strip()
        except RuntimeError:
            continue
        if not tip or is_rich_text(tip):
            continue
        if len(tip) > TOOLTIP_MAX_CHARS:
            problems.append(
                f"ALG-3 HOVER GEOMETRY (rules/GUI.md -> Zubi v2) "
                f"{widget.__class__.__name__} "
                f"'{widget.objectName() or '-'}': plain-text tooltip of "
                f"{len(tip)} chars ('{tip[:48]}...') - plain tooltips are NOT "
                "wrapped by Qt, so this renders as one line far wider than "
                f"the window. Wrap it: make it rich text ('<p>{tip[:24]}...'"
                "</p>' or '<br>' between clauses, which Qt wraps), or cut it "
                f"under {TOOLTIP_MAX_CHARS} characters")
    return problems

# --- ALG-4  SPACE CEILING ---------------------------------------------------
def natural_size(window: QWidget) -> QSize:
    """What the window ASKS for in logical px - the largest of its size hint,
    its minimum hint and its declared minimum. Logical, because that is the
    unit layouts are written in; a 4K screen is not a licence."""
    hint = window.sizeHint()
    minimum_hint = window.minimumSizeHint()
    declared = window.minimumSize()
    return QSize(max(hint.width(), minimum_hint.width(), declared.width()),
                 max(hint.height(), minimum_hint.height(), declared.height()))
def check_space_ceiling(window: QWidget) -> list[str]:
    """ALG-4 - the width ladder. The horizontal-scroll half of this rule lives
    in check_scroll_with_free_space, beside the logic it extends."""
    natural = natural_size(window)
    width, height = natural.width(), natural.height()
    if width > ABSOLUTE_WIDTH or height > ABSOLUTE_HEIGHT:
        return [f"ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): natural size "
                f"{width}x{height} logical px passes the ABSOLUTE ceiling "
                f"{ABSOLUTE_WIDTH}x{ABSOLUTE_HEIGHT} - no exception, no "
                "written excuse; a window this size is a fullscreen demand. "
                "REFLOW into columns, tabs or pages (ladder step 2) until it "
                f"fits under {WORKING_WIDTH}px wide"]
    if width > WORKING_WIDTH:
        return [f"ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): natural width "
                f"{width} logical px exceeds the {WORKING_WIDTH}px working "
                "width of a desktop settings page. Reflow the widest row into "
                "columns or a second page (ladder step 2); a step up the "
                "ladder is legal only when reflow is exhausted AND the reason "
                "is written down"]
    return []

# --- ALG-5  UNIFORM SIBLINGS ------------------------------------------------
UNIFORM_ROLES = (QPushButton, QToolButton, QRadioButton)
def _sub_layouts(layout: QLayout):
    yield layout
    for index in range(layout.count()):
        item = layout.itemAt(index)
        child = item.layout() if item is not None else None
        if child is not None:
            yield from _sub_layouts(child)
def check_uniform_siblings(window: QWidget) -> list[str]:
    """ALG-5 - a control's size must never depend on the length of its own
    text. Grouped by EXACT class, so a styled subclass beside a plain button
    is not convicted of being a different size on purpose."""
    problems = []
    for container in walk(window):
        layout = container.layout()
        if layout is None:
            continue
        for sub in _sub_layouts(layout):
            groups: dict[str, list[QWidget]] = {}
            for index in range(sub.count()):
                item = sub.itemAt(index)
                widget = item.widget() if item is not None else None
                if widget is None or not widget.isVisible():
                    continue
                if not isinstance(widget, UNIFORM_ROLES):
                    continue
                groups.setdefault(type(widget).__name__, []).append(widget)
            for role, members in groups.items():
                if len(members) < 2:
                    continue
                widths = [member.width() for member in members]
                heights = [member.height() for member in members]
                if (max(widths) - min(widths) <= SIBLING_TOLERANCE
                        and max(heights) - min(heights) <= SIBLING_TOLERANCE):
                    continue
                sizes = ", ".join(
                    f"'{widget_text(member)[:24] or member.objectName() or '-'}'"
                    f" {member.width()}x{member.height()}"
                    for member in members)
                problems.append(
                    f"ALG-5 UNIFORM SIBLINGS (rules/GUI.md -> Zubi v2) "
                    f"{role} row in {container.__class__.__name__} "
                    f"'{container.objectName() or '-'}': {sizes} - same-kind "
                    f"controls in one container must share their size within "
                    f"{SIBLING_TOLERANCE}px. Let the WIDEST content decide and "
                    "give every one of them that minimum (or lay them out in "
                    "a grid with equal columns)")
    return problems

# --- ALG-6  RADIUS BY ASPECT RATIO ------------------------------------------
RADIUS_PROPERTIES = ("border-radius", "border-top-left-radius",
                     "border-top-right-radius", "border-bottom-left-radius",
                     "border-bottom-right-radius")
def _declared_radius(declarations: dict[str, str],
                     widget: QWidget) -> tuple[float, str] | None:
    best: tuple[float, str] | None = None
    for name in RADIUS_PROPERTIES:
        value = declarations.get(name)
        if not value:
            continue
        for token in value.split():
            pixels = _length_px(token, widget)
            if pixels is None:
                continue
            if best is None or pixels > best[0]:
                best = (pixels, f"{name}: {value.strip()}")
    return best
def check_radius(window: QWidget) -> list[str]:
    """ALG-6 - a pill is legitimate on a WIDE element and nowhere else.

    The radius comes from a best-effort STATIC parse of the stylesheets in
    force (see _parse_sheet): a radius painted by a custom paintEvent, a QSS
    file loaded by the platform style, or a proxy style is invisible here.
    Every finding quotes the declaration it read, so a misparse shows itself.

    NOT covered: the second half of ALG-6, "inner text/image inset >= 0.3*r".
    Qt's padding lives partly in the same stylesheet and partly in the style's
    own margins, so a number measured here would be a guess dressed as a
    measurement; the inset stays with the grader's checklist (GRD-1)."""
    problems = []
    for widget in walk(window):
        width, height = widget.width(), widget.height()
        if width <= 0 or height <= 0:
            continue
        declarations, raw = effective_style(widget, window)
        radius = _declared_radius(declarations, widget)
        if radius is None:
            continue
        if (CIRCLE_CONTENT_RE.search(widget.objectName() or "")
                or CIRCLE_CONTENT_MARKER in raw):
            continue        # true-circle content (swatch, avatar) is exempt
        aspect = width / height
        if aspect >= 2:
            allowed, rule = 0.50 * height, "AR >= 2 allows 50% of the height"
        elif aspect >= 1.4:
            allowed, rule = 0.30 * height, "1.4 <= AR < 2 allows 30% of the height"
        else:
            allowed, rule = (0.15 * min(width, height),
                             "AR < 1.4 allows 15% of the shorter side")
        if radius[0] > allowed + 0.5:
            problems.append(
                f"ALG-6 RADIUS BY ASPECT RATIO (rules/GUI.md -> Zubi v2) "
                f"{widget.__class__.__name__} "
                f"'{widget.objectName() or '-'}': {width}x{height} px "
                f"(AR {aspect:.2f}) carries {radius[0]:.0f}px from "
                f"'{radius[1]}', but {rule} = {allowed:.0f}px. Lower the "
                f"radius to {allowed:.0f}px or less, or widen the element to "
                "AR >= 2 if a pill is what you want. Genuinely round content "
                "is exempt: name it (swatch/avatar/circle) or mark the rule "
                f"with a '/* {CIRCLE_CONTENT_MARKER} */' comment")
    return problems

# --- ALG-7  ROW OCCUPANCY ---------------------------------------------------
def _colors_close(one: QColor, other: QColor,
                  tolerance: int = BAND_COLOR_TOLERANCE) -> bool:
    return (abs(one.red() - other.red()) <= tolerance
            and abs(one.green() - other.green()) <= tolerance
            and abs(one.blue() - other.blue()) <= tolerance)
def _edge_background(image: QImage) -> QColor | None:
    """The most common pixel on the four edges - the window's own background
    in every layout that does not bleed art to the border. A HEURISTIC, and
    the finding says so."""
    counts: dict[int, int] = {}
    width, height = image.width(), image.height()
    step_x, step_y = max(1, width // 64), max(1, height // 64)
    for x in range(0, width, step_x):
        for y in (0, height - 1):
            counts[image.pixel(x, y)] = counts.get(image.pixel(x, y), 0) + 1
    for y in range(0, height, step_y):
        for x in (0, width - 1):
            counts[image.pixel(x, y)] = counts.get(image.pixel(x, y), 0) + 1
    if not counts:
        return None
    return QColor.fromRgb(max(counts.items(), key=lambda pair: pair[1])[0])
def check_row_occupancy(window: QWidget,
                        image: QImage | None = None) -> list[str]:
    """ALG-7 - the measurable form of "nothing starves beside empty space".

    The grabbed window is cut into ~48px bands; a band whose RIGHT half is
    more than 55% background while its LEFT half carries content is a
    "right-empty" band. Two or more of those in a row, with content still
    coming BELOW them, is the stacking-instead-of-reflowing pattern.

    Heuristic, deliberately conservative, and it can be fooled: background is
    the most common EDGE pixel, so a window with a full-bleed image border
    measures nothing; a column of left-aligned prose above a footer is the
    known false positive, which is why the rule is a GATE and why a run of two
    consecutive bands is required."""
    image = _window_image(window) if image is None else image
    if image is None or image.isNull():
        return []
    width, height = image.width(), image.height()
    ratio = image.devicePixelRatio() or 1.0
    band_px = max(8, int(BAND_HEIGHT * ratio))
    if width < 80 or height < band_px * 2:
        return []
    background = _edge_background(image)
    if background is None:
        return []
    middle = width // 2
    bands = []
    for top in range(0, height, band_px):
        bottom = min(top + band_px, height)
        step_y = max(1, (bottom - top) // 12)
        step_x = max(1, width // 80)
        totals = [0, 0]
        content = [0, 0]
        for y in range(top, bottom, step_y):
            for x in range(0, width, step_x):
                side = 0 if x < middle else 1
                totals[side] += 1
                pixel = _image_point(image, x, y)
                if pixel is not None and not _colors_close(pixel, background):
                    content[side] += 1
        if not totals[0] or not totals[1]:
            continue
        left_ratio = content[0] / totals[0]
        right_ratio = content[1] / totals[1]
        overall = (content[0] + content[1]) / (totals[0] + totals[1])
        bands.append({
            "top": int(top / ratio), "bottom": int(bottom / ratio),
            "content": overall >= BAND_CONTENT_RATIO,
            "right_empty": (left_ratio >= BAND_CONTENT_RATIO
                            and (1.0 - right_ratio) > BAND_EMPTY_RATIO),
            "right_ratio": right_ratio,
        })

    problems = []
    index = 0
    while index < len(bands):
        if not bands[index]["right_empty"]:
            index += 1
            continue
        end = index
        while end + 1 < len(bands) and bands[end + 1]["right_empty"]:
            end += 1
        run = end - index + 1
        below = [band for band in bands[end + 1:] if band["content"]]
        if run >= BAND_MIN_RUN and below:
            empty = 100.0 * (1.0 - min(band["right_ratio"]
                                       for band in bands[index:end + 1]))
            problems.append(
                f"ALG-7 ROW OCCUPANCY (rules/GUI.md -> Zubi v2): rows "
                f"y={bands[index]['top']}-{bands[end]['bottom']} px leave "
                f"their right half up to {empty:.0f}% empty while content "
                f"continues BELOW them (y={below[0]['top']} px) - reflow "
                "those rows into columns before stacking them into height "
                "(ladder step 2). Heuristic: background taken as the most "
                f"common edge pixel {background.name()}, bands of "
                f"{BAND_HEIGHT}px, {BAND_MIN_RUN} consecutive bands required")
        index = end + 1
    return problems

# --- ALG-8  LIVE PROFILE ----------------------------------------------------
_ACTIVE_PROFILE: Path | None = None

def live_profile_source() -> Path | None:
    """ALG-8 - THE ONE FUNCTION A PROJECT OVERRIDES.

    Return the path of the owner's REAL settings file and every window in
    WINDOWS is audited a second time, built from a COPY of it:

        def live_profile_source() -> Path | None:
            path = Path.home() / "AppData/Roaming/MyApp/settings.json"
            return path if path.is_file() else None

    The original is only ever READ - the audit copies it into a temp folder,
    publishes the copy through the LAYOUT_AUDIT_PROFILE environment variable
    AND through active_profile(), and deletes the folder afterwards. A settings
    store that already honours an env override then needs nothing else; one
    that does not, reads active_profile() in its factory:

        def make_main_window():
            return MainWindow(Settings.load(active_profile() or DEFAULT_PATH))

    "That is the environment, not this change" is not a legal sentence in any
    proof file: a failure under the owner's real profile is this session's."""
    return None
def active_profile() -> Path | None:
    """The read-only copy currently in force, or None during the default
    pass. Factories read this to build from the owner's real settings."""
    return _ACTIVE_PROFILE
@contextmanager
def live_profile_copy():
    """Copy live_profile_source() to a temp folder, publish it, clean up.

    The COPY is what the app may open, scribble on and rewrite; the owner's
    original file is opened once, for reading, and never written to."""
    global _ACTIVE_PROFILE
    source = live_profile_source()
    if source is None or not Path(source).is_file():
        yield None
        return
    source = Path(source)
    folder = Path(tempfile.mkdtemp(prefix="layout-audit-profile-"))
    copy = folder / source.name
    shutil.copyfile(source, copy)
    previous_env = os.environ.get(PROFILE_ENV)
    previous_active = _ACTIVE_PROFILE
    _ACTIVE_PROFILE = copy
    os.environ[PROFILE_ENV] = str(copy)
    try:
        yield copy
    finally:
        _ACTIVE_PROFILE = previous_active
        if previous_env is None:
            os.environ.pop(PROFILE_ENV, None)
        else:
            os.environ[PROFILE_ENV] = previous_env
        shutil.rmtree(folder, ignore_errors=True)

# --- ALG-9  SECTION TAXONOMY ------------------------------------------------
def _concepts(text: str) -> set[str]:
    found = set()
    lowered = text.lower()
    for word in CONCEPT_WORDS:
        if re.search(rf"\b{word}s?\b", lowered):
            found.add("color" if word == "colour" else word)
    return found
def check_section_taxonomy(sections: dict[str, list[str]]) -> list[str]:
    """ALG-9 - a concept that owns a section owns every control of that
    concept.

    Not wired into the generic walk: only the project knows which list widget
    is its nav and which page belongs to which entry. A project feeds it from
    its own structure, in its own test:

        def test_section_taxonomy(app):
            window = make_settings_dialog()
            window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
            window.show()
            sections = {}
            for row in range(window.nav.count()):
                window.nav.setCurrentRow(row)
                QApplication.processEvents()
                page = window.stack.currentWidget()
                sections[window.nav.item(row).text()] = [
                    label.text() for label in page.findChildren(QLabel)
                    if label.text().strip()]
            window.close()
            assert not check_section_taxonomy(sections)

    A deliberate exception stays legal - the rulebook asks for a written
    reason beside it, which in practice means renaming the label or the
    section so the taxonomy reads true."""
    homes: dict[str, list[str]] = {}
    for title in sections:
        for concept in _concepts(title):
            homes.setdefault(concept, []).append(title)
    problems = []
    for title, labels in sections.items():
        owned = _concepts(title)
        for label in labels:
            for concept in sorted(_concepts(label) - owned):
                home = homes.get(concept)
                if not home:
                    continue
                problems.append(
                    f"ALG-9 SECTION TAXONOMY (rules/GUI.md -> Zubi v2): "
                    f"'{label}' sits in section '{title}' while '{concept}' "
                    f"has a section of its own ({', '.join(home)}) - move the "
                    f"control into {home[0]}, or rename it so it no longer "
                    "claims a concept that lives elsewhere")
    return problems
