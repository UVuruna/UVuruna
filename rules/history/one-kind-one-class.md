# One kind, one class — the probe behind the law (owner verdict 2026-08-18)

The owner's thesis: agents avoid OOP exactly where it is ideal — a card shown
in several panels, a watch, a theme, an encyclopedia page. A cheap reviewer was
sent into each of the four main projects to check that on the CODE, not on the
impression. The finding corrected him in part, and the law was written to match
what was actually found.

| Project | Grade | Found |
|---------|-------|-------|
| VibeCoder | 8 | real delegate hierarchy, one `card()/section()/row()` factory layer, no hardcoded colors outside `theme.py` — but `web.py` and `main_window.py` sit at EXACTLY 1000 lines, `web.py` cut three times "at the wall" |
| WatchAcademy | 7 | cards are ONE abstraction (`CardKind/OptionCard/CardGroup`), skins are a dataclass schema, 35 themes in one registry — but `settings_dialog/` builds `QGroupBox`+layout by hand ~6 times, the encyclopedia has 3 screens with no common base, and `app/controller.py` (4,483 lines), `render/compositor.py` (3,860) and `observatory.py` (1,697) are all ratcheted |
| PromptPainter | 8 | base classes exist (`ToolSettingsPanel` → 5 subclasses, `JobPanel` → 3, `PainterGui` over 6 mixins) — one literal duplication: a 3-line `Toplevel` setup repeated in 5 constructors; `painter/driver.py` 1,599 lines |
| Aviator | 7 | `BaseStatsWidget` → 3 subclasses, a real `components/` library, tabs via mixins (home 2321→420) — but 23 files over 800 lines, 8 ratcheted, and 5 tabs repeat the same `_init_ui` boilerplate with no `BaseTab` |

Conclusion: where a kind has ≥ 3 instances, a class or a registry usually DOES
exist. What actually repeats is small boilerplate (Toplevel setup ×5,
QGroupBox+layout ×6, tab `_init_ui` ×5); what actually hurts is STRUCTURE —
files of 1,000–4,483 lines that grow because nobody splits them BEFORE the
wall. So the teeth went on both: the clone guard for boilerplate, and the
sentence "split by responsibility before the wall reaches you" added to the
Structure Law.

The law itself (rule text in `rules/CODE.md`): when two or more things share
behaviour — cards, watches, themes, pages, panels, buttons of one kind — they
are instances of ONE class or entries of ONE registry; a new instance is a new
entry or subclass, never a copied block. Adding a watch, a theme, a card or an
encyclopedia page must be "add an object".

Teeth: `rules/tools/clone_guard.py` (AST fingerprint per function/method, names
normalised; two blocks of ≥ 8 statements with the same fingerprint in different
files fail, escape `clone-ok: <reason>`), run inside every project's
`run_guards.py` FULL. The first pass will find the existing clones — they go
into the RATCHET list exactly like the god-files, and it only shrinks.
A one-off OOP audit per main project (WatchAcademy first) stays a separate
session and is NOT part of this rework.
