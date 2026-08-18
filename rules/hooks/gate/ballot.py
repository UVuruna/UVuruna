"""Artifact pages: a proposal page must be a ballot, and its colours are fixed.

Ported from communication_guard.py (Artifact half only): the ballot contract,
the fixed-colour-scheme rule, and image links that must resolve on disk.
"""

from __future__ import annotations

import re
from pathlib import Path

PROPOSAL_RE = re.compile(
    r"data-option|our pick|recommend(ed|ation)|\boption\s*[ab1-9]\b", re.I)
BALLOT_RE = re.compile(r"ballot-copy|id=[\"']ballot[\"']", re.I)
SELECTABLE_RE = re.compile(r"type=[\"'](checkbox|radio)[\"']", re.I)
TEXTAREA_RE = re.compile(r"<textarea", re.I)
VERDICT_RE = re.compile(r"id=[\"']verdict[\"']", re.I)

ADAPTIVE_THEME_RE = re.compile(
    r"prefers-color-scheme|\[\s*data-theme|data-theme\s*=", re.I)
BACKGROUND_RE = re.compile(r"background(-color)?\s*:", re.I)

IMG_SRC_RE = re.compile(r"<img[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.I)
MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^()\s]+)\)")


def _local_images(page: str) -> list[str]:
    targets = IMG_SRC_RE.findall(page) + MD_IMG_RE.findall(page)
    return [t for t in targets
            if not re.match(r"^(https?:|data:|//|#)", t.strip(), re.I)]


def check(file_path: str, page: str, roots: list[Path]) -> list[str] | None:
    """Block lines, or None when the page may be published."""
    if not page:
        return None
    if ADAPTIVE_THEME_RE.search(page):
        return [
            "This page adapts to the viewer's theme (prefers-color-scheme / "
            "data-theme) — in the owner's viewer that renders white on white.",
            "FIX: commit to ONE fixed scheme — explicit hex background AND "
            "text colour on the body, no media queries, no data-theme.",
            f"where: {file_path}",
        ]
    if "<style" in page.lower() and not BACKGROUND_RE.search(page):
        return [
            "This page never sets its own background colour, so it inherits "
            "the host shell's.",
            "FIX: set an explicit fixed background and text colour on the body.",
            f"where: {file_path}",
        ]
    if PROPOSAL_RE.search(page) and not (
            BALLOT_RE.search(page) and SELECTABLE_RE.search(page)
            and TEXTAREA_RE.search(page)):
        return [
            "This page proposes options but the owner cannot answer inside it "
            "(missing tick boxes / per-option comment / ballot block).",
            "FIX: copy rules/templates/decision_page.html and replace only the "
            "content — data-option cards, a textarea per option, #ballot-copy, "
            "#verdict.",
            f"where: {file_path}",
        ]
    dead = []
    for target in _local_images(page):
        raw = target.split("#", 1)[0].replace("%20", " ")
        candidate = Path(raw)
        if candidate.is_absolute() or re.match(r"^[A-Za-z]:", raw):
            alive = candidate.exists()
        else:
            alive = any((root / raw).exists() for root in roots)
        if not alive:
            dead.append(raw)
    if dead:
        return [
            f"Image link(s) in the page do not resolve: {', '.join(dead[:3])}",
            "FIX: embed the image as a data: URI (the artifact CSP blocks "
            "external hosts) or point at a file that exists.",
            f"where: {file_path}",
        ]
    return None
