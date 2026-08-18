"""Blocks writing a non-English program file (ported from language_guard.py).

Same scope, same `lang-ok:` / `lang-ok-begin:`…`lang-ok-end` escapes and the
same `.claude/language-frame.json` declaration for product copy that is
legitimately written in another language.
"""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

FRAME_FILENAME = "language-frame.json"
MIN_REASON_CHARS = 20

CHECKED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".cs", ".vb", ".java", ".cpp",
    ".c", ".h", ".rs", ".go", ".html", ".htm", ".css", ".scss", ".qss",
    ".xaml", ".axaml", ".qml", ".xml", ".md", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".txt", ".svg",
    ".php", ".phtml", ".kt", ".kts", ".vue", ".svelte",
    ".ps1", ".psm1", ".sh", ".bat", ".sql",
}

# conversation state, the owner's inbox, and the rulebooks/tests/docs that
# QUOTE the patterns on purpose
SKIP_COMPONENTS = {
    ".claude", "uv", "scratchpad", "temp", "tmp", "node_modules",
    ".git", "__pycache__", "vendor", "rules", "tests", "test", "docs", "doc",
}
SKIP_FILENAMES = {"private.md"}

FOREIGN_RUNS = (
    (re.compile(r"[Ѐ-ԯ]{3,}"), "Cyrillic"),
    (re.compile(r"[Ͱ-Ͽἀ-῿]{3,}"), "Greek"),
    (re.compile(r"[一-鿿]{2,}"), "Chinese (CJK)"),
    (re.compile(r"[぀-ヿ]{3,}"), "Japanese kana"),
    (re.compile(r"[가-힯]{2,}"), "Korean hangul"),
    (re.compile(r"[؀-ۿ]{3,}"), "Arabic"),
    (re.compile(r"[֐-׿]{3,}"), "Hebrew"),
)

SERBIAN_DIACRITICS = re.compile(r"[čćšžđ"
                                r"ČĆŠŽĐ]")

SERBIAN_WORDS = re.compile(
    r"\b(nije|moze|treba|ovde|ovdje|zasto|dakle|umesto|umjesto|takodje"
    r"|koji|koja|koje|gdje|nesto|svaki|svaka|jeste|imamo|nemamo|uvek"
    r"|uvijek|posle|poslije|zatim|ovakav|ovoga|njega|njemu|veoma|vrlo"
    r"|takvo|prikaz|izbor|boje|slova)\b",
    re.IGNORECASE,
)
MIN_STOPWORD_HITS = 3

LANG_OK_RE = re.compile(r"lang-ok\s*[:(\-—]\s*\S{3,}")
LANG_OK_BEGIN_RE = re.compile(r"lang-ok-begin\s*[:(\-—]\s*\S{3,}")
LANG_OK_END_RE = re.compile(r"lang-ok-end\b")


def written_text(tool_input: dict) -> str:
    """Everything this call would put INTO the file."""
    parts = [tool_input.get("content"), tool_input.get("new_string"),
             tool_input.get("new_source")]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    return "\n".join(p for p in parts if isinstance(p, str))


def declared_content_path(path: str) -> bool:
    """True when the project declares THIS file as copy in another language.

    Fail-CLOSED on an unreadable frame: a malformed declaration frees nothing.
    """
    try:
        target = Path(path).resolve()
    except OSError:
        return False
    for directory in target.parents:
        frame = directory / ".claude" / FRAME_FILENAME
        if not frame.is_file():
            continue
        try:
            data = json.loads(frame.read_text(encoding="utf-8",
                                              errors="replace"))
        except (json.JSONDecodeError, ValueError, OSError):
            return False
        if len(str(data.get("reason") or "").strip()) < MIN_REASON_CHARS:
            return False
        patterns = data.get("content_paths") or []
        if not isinstance(patterns, list):
            return False
        try:
            relative = target.relative_to(directory).as_posix()
        except ValueError:
            return False
        for pattern in patterns:
            if isinstance(pattern, str) and (
                    fnmatch.fnmatch(relative, pattern)
                    or fnmatch.fnmatch(target.name, pattern)):
                return True
        return False
    return False


def in_scope(path: str) -> bool:
    if not path:
        return False
    components = [c.lower() for c in re.split(r"[\\/]+", path) if c]
    if any(c in SKIP_COMPONENTS for c in components):
        return False
    if components and components[-1] in SKIP_FILENAMES:
        return False
    if Path(path).suffix.lower() not in CHECKED_EXTENSIONS:
        return False
    return not declared_content_path(path)


def scan(text: str) -> list[str]:
    lines = text.splitlines()
    findings: list[str] = []
    stopword_hits: dict[str, int] = {}
    inside_block = False
    for number, line in enumerate(lines, start=1):
        if LANG_OK_BEGIN_RE.search(line):
            inside_block = True
            continue
        if LANG_OK_END_RE.search(line):
            inside_block = False
            continue
        if inside_block:
            continue
        previous = lines[number - 2] if number >= 2 else ""
        if LANG_OK_RE.search(line) or LANG_OK_RE.search(previous):
            continue
        flagged = None
        for pattern, script in FOREIGN_RUNS:
            match = pattern.search(line)
            if match:
                flagged = f"line {number}: {script} \"{match.group(0)[:30]}\""
                break
        if flagged is None and SERBIAN_DIACRITICS.search(line):
            flagged = f"line {number}: Serbian \"{line.strip()[:40]}\""
        if flagged:
            findings.append(flagged)
            continue
        for word in SERBIAN_WORDS.findall(line):
            stopword_hits.setdefault(word.lower(), number)
    if len(stopword_hits) >= MIN_STOPWORD_HITS:
        findings.append(f"line {min(stopword_hits.values())}: Serbian words "
                        f"({', '.join(sorted(stopword_hits))})")
    return findings


def check(tool_input: dict) -> list[str] | None:
    """Block lines, or None when the edit is fine."""
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not in_scope(path):
        return None
    text = written_text(tool_input)
    if not text:
        return None
    findings = scan(text)
    if not findings:
        return None
    return [
        f"Not English in {Path(path).name}: {'; '.join(findings[:2])}",
        "FIX: translate it; a legitimate exception is contested on its line "
        "with `lang-ok: <reason>` (block form: lang-ok-begin/lang-ok-end).",
        f"where: {path}",
    ]
