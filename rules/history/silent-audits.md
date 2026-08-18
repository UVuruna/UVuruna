# Silent Audits — the story

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="silent-audits"></a>

## LAW — Silent Audits (owner decree 2026-08-06)

**No window an audit, guard run or agent builds may ever reach the owner's
screen or take his focus.** Born live, the same day the design-review teeth
landed: an audit's factories called `show()` before `WA_DontShowOnScreen`,
so every guard run flashed the real main window across the owner's desktop
and broke his typing mid-sentence, repeatedly, while background agents ran.

- **Qt:** `setAttribute(WA_DontShowOnScreen, True)` BEFORE every `show()` —
  including shows inside window factories — or the offscreen platform.
- **Tk:** `withdraw()` / off-screen geometry AND `attributes("-alpha", 0)`
  before the first `update()`; every `Toplevel` pinned the instant it is born.
- **WPF:** render to `RenderTargetBitmap`, never `Show()`.

Class: **LAW** — `rules/hooks/layout_guard.py` (PreToolUse, machine-wide)
refuses to write any `test_layout_audit*` file that builds windows without a
silencing mechanism. The order of calls inside stays on session discipline —
the hook catches the missing mechanism, the reviewer catches the wrong order.

---

