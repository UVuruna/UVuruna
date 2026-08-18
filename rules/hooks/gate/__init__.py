"""Gate modules — the checks `gate.py` dispatches to.

One module per subject: transcript parsing, ledger grammar, evidence rows,
language, GUI APIs, build permission, ballot pages, running agents, category
teeth, and the four event handlers (prompt/pre/stop/subagent).
"""

import sys as _sys
from pathlib import Path as _Path

# `changed_files` is the scope engine and lives beside gate.py, one level up
_HOOKS = str(_Path(__file__).resolve().parent.parent)
if _HOOKS not in _sys.path:
    _sys.path.insert(0, _HOOKS)
