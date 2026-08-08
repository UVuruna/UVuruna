#!/usr/bin/env python3
"""Language guard — owner decree 2026-08-08.

Enforces the LANGUAGE LAW (root CLAUDE.md -> Universal Conduct: "English in
all code, comments, docs and commit messages") across ALL sessions on this
machine (wired in ~/.claude/settings.json):

  PreToolUse (Write|Edit|NotebookEdit)
      Blocks writing product text that is not English: Serbian in Latin
      script (diacritics, or a density of common Serbian words), and any RUN
      of a foreign script — Cyrillic (Serbian or Russian), Greek, CJK,
      Arabic, Hebrew. Born from a real shipped violation: the Loading Cube
      demo page reached its repository with its whole visible UI in Serbian,
      straight through four guard tests, a visual proof and a commit — the
      rule existed only as one sentence in the constitution, and the
      constitution itself records that rules hold only when a check
      enforces them.

WHAT IS EXEMPT, by design (the owner's own carve-outs, 2026-08-08):

  * Conversation-with-the-owner state: `.claude/` files (session tasks and
    reports are written in Serbian by law), his `UV/` inboxes, PRIVATE.md,
    scratchpad/temp paths. The law governs the PRODUCT, not the chat.
  * Single foreign SYMBOLS (Ω, π, Δ, 中 as an isolated glyph) — a symbol is
    not a language. Only a run of foreign-script letters counts as WRITING
    in that script.
  * A line the agent CONTESTS with its head on: `lang-ok: <reason>` on that
    line (or the line directly above). This is for the owner's named
    exceptions — a quotation, a local pronunciation in parentheses beside
    the English name, an i18n string bundle. An exemption without a reason
    does not count, and a false reason is a capacity lie (CLAUDE.md ->
    Universal Conduct).
  * PRODUCT CONTENT IN ANOTHER LANGUAGE, declared per project in
    `.claude/language-frame.json` (owner ruling 2026-08-08). Three of the
    monorepo's websites sell to Serbian customers, so their customer-facing
    COPY is legitimately Serbian — the law was always about the PROGRAM
    (code, comments, identifiers, docs, developer-facing UI), never about
    the words a product says to its own audience. The declaration:

        {"content_language": "sr",
         "reason": "<why this product's copy is not English>",
         "content_paths": ["public/**", "*.php", "content/**"]}

    Only the listed paths are freed, `reason` is mandatory (< 20 chars does
    not count, exactly like the layout floor override), and code files
    outside those paths are still English-only — a Serbian shop still has
    English variable names.

Contract: exit 2 = BLOCK (stderr is fed back to the agent); exit 0 = pass.
Fail-open on any parse error — a broken guard must never brick a session.
"""

import fnmatch
import json
import re
import sys
from pathlib import Path

FRAME_FILENAME = "language-frame.json"
MIN_REASON_CHARS = 20

# ═══════════════════════════ SCOPE ═══════════════════════════

CHECKED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".cs", ".vb", ".java", ".cpp",
    ".c", ".h", ".rs", ".go", ".html", ".htm", ".css", ".scss", ".qss",
    ".xaml", ".axaml", ".qml", ".xml", ".md", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".txt", ".svg",
    # The stacks this monorepo actually ships, added 2026-08-08 after a live
    # check found .php missing — the language of three of the websites, so
    # the guard had been passing them in silence.
    ".php", ".phtml", ".kt", ".kts", ".vue", ".svelte",
    ".ps1", ".psm1", ".sh", ".bat", ".sql",
}

# path components that mark agent/owner conversation state, not product —
# plus "rules"/"tests"/"docs", following layout_guard's precedent: the
# rulebooks QUOTE the owner's Serbian decrees on purpose, and the guards
# themselves name the patterns they hunt
SKIP_COMPONENTS = {
    ".claude", "uv", "scratchpad", "temp", "tmp", "node_modules",
    ".git", "__pycache__", "vendor", "rules", "tests", "test", "docs", "doc",
}
SKIP_FILENAMES = {"private.md"}

# ═══════════════════════════ DETECTION ═══════════════════════════

# a run of letters from a foreign script is WRITING in it; a lone glyph is a
# symbol and legal (Ω on a dial, π in a formula)
FOREIGN_RUNS = (
    (re.compile(r"[Ѐ-ԯ]{3,}"), "Cyrillic (Serbian or Russian)"),
    (re.compile(r"[Ͱ-Ͽἀ-῿]{3,}"), "Greek"),
    (re.compile(r"[一-鿿]{2,}"), "Chinese (CJK)"),
    (re.compile(r"[぀-ヿ]{3,}"), "Japanese kana"),
    (re.compile(r"[가-힯]{2,}"), "Korean hangul"),
    (re.compile(r"[؀-ۿ]{3,}"), "Arabic"),
    (re.compile(r"[֐-׿]{3,}"), "Hebrew"),
)

SERBIAN_DIACRITICS = re.compile(r"[čćšžđČĆŠŽĐ]")

# conservative word list — each is a common Serbian word that is not an
# English word; ≥ MIN_STOPWORD_HITS DISTINCT hits flag the text, so a lone
# name or coincidence never trips it
SERBIAN_WORDS = re.compile(
    r"\b(nije|moze|treba|ovde|ovdje|zasto|dakle|umesto|umjesto|takodje"
    r"|koji|koja|koje|gdje|nesto|svaki|svaka|jeste|imamo|nemamo|uvek"
    r"|uvijek|posle|poslije|zatim|ovakav|ovoga|njega|njemu|veoma|vrlo"
    r"|takvo|bilo\s+koje|prikaz|izbor|boje|slova|veličina|velicina)\b",
    re.IGNORECASE,
)
MIN_STOPWORD_HITS = 3

# the contest marker: lang-ok: <reason> on the flagged line or the line above
LANG_OK_RE = re.compile(r"lang-ok\s*[:(\-—]\s*\S{3,}")
# ...and its block form, for a RUN of foreign text inside an English file —
# a translation table, a quoted passage, a roster of local names. One reason
# for the whole block instead of a marker per line (owner ruling 2026-08-08:
# the backend stays English, so a data table must be markable without
# freeing the file it lives in).
LANG_OK_BEGIN_RE = re.compile(r"lang-ok-begin\s*[:(\-—]\s*\S{3,}")
LANG_OK_END_RE = re.compile(r"lang-ok-end\b")

BLOCK = (
    "THE LANGUAGE LAW (root CLAUDE.md -> Universal Conduct, teeth of "
    "2026-08-08): every program is written in ENGLISH — code, comments, "
    "docs, UI strings, commit messages. Serbian belongs in the chat with "
    "the owner, never in the product. This edit to {path} writes another "
    "language:\n{findings}\n"
    "This law grew teeth because a whole demo page shipped with its UI in "
    "Serbian through every existing gate. Fix: TRANSLATE the flagged text "
    "to English. If a line is a LEGITIMATE exception — a quotation, a "
    "local pronunciation in parentheses beside the English name, an i18n "
    "bundle entry — contest it ON THAT LINE (or the line above) with: "
    "lang-ok: <the reason>. An exemption without a reason does not count, "
    "and a false reason is a capacity lie."
)


def written_text(tool_input: dict) -> str:
    """Everything this call would put INTO the file."""
    parts = [
        tool_input.get("content"),
        tool_input.get("new_string"),
        tool_input.get("new_source"),
    ]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    return "\n".join(p for p in parts if isinstance(p, str))


def declared_content_path(path: str) -> bool:
    """True when the project declares THIS file as product copy written in
    another language (`.claude/language-frame.json`). A declaration without
    a real reason does not count — same rule as the layout floor override.
    Fail-CLOSED on an unreadable frame: a broken declaration frees nothing,
    because 'the file was malformed' must never become a way to smuggle
    Serbian into a program."""
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
            if not isinstance(pattern, str):
                continue
            if fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(
                    target.name, pattern):
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


def scan(text: str) -> list:
    lines = text.splitlines()
    findings = []
    stopword_hits: dict = {}
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
                flagged = f"{script} text: \"{match.group(0)[:40]}\""
                break
        if flagged is None and SERBIAN_DIACRITICS.search(line):
            flagged = f"Serbian diacritics: \"{line.strip()[:60]}\""
        if flagged:
            findings.append(f"  line {number}: {flagged}")
            continue
        for word in SERBIAN_WORDS.findall(line):
            stopword_hits.setdefault(word.lower(), number)
    if len(stopword_hits) >= MIN_STOPWORD_HITS:
        words = ", ".join(sorted(stopword_hits))
        first = min(stopword_hits.values())
        findings.append(
            f"  from line {first}: Serbian written in Latin script "
            f"(common words found: {words})")
    return findings


def check_pre_tool_use(payload: dict) -> None:
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not in_scope(path):
        return
    text = written_text(tool_input)
    if not text:
        return
    findings = scan(text)
    if not findings:
        return
    print(BLOCK.format(path=path, findings="\n".join(findings)),
          file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    try:
        if payload.get("hook_event_name", "") == "PreToolUse" and \
                payload.get("tool_name") in ("Write", "Edit", "NotebookEdit"):
            check_pre_tool_use(payload)
    except SystemExit:
        raise
    except Exception:  # a broken guard must never brick a session
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
