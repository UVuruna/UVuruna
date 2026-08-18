"""structure_guard: over-wall needs an entry; ratcheted files only shrink; stale entries fail."""
from pathlib import Path
import json
import structure_guard as sg


def _py(path: Path, lines: int) -> None:
    path.write_text("\n".join(f"x{i} = {i}" for i in range(lines)) + "\n", encoding="utf-8")


def test_over_wall_without_entry_fails(tmp_path):
    _py(tmp_path / "big.py", 30)
    problems = sg.check(tmp_path, tmp_path / "r.json", wall=20)
    assert any("OVER THE WALL" in p for p in problems)


def test_ratcheted_file_may_shrink_but_not_grow(tmp_path):
    big = tmp_path / "big.py"
    _py(big, 30)
    ratchet = tmp_path / "r.json"
    sg.write_ratchet(tmp_path, ratchet, wall=20)
    assert sg.check(tmp_path, ratchet, wall=20) == []
    _py(big, 28)                                   # shrinks: fine
    assert sg.check(tmp_path, ratchet, wall=20) == []
    _py(big, 35)                                   # grows: fails
    assert any("GREW" in p for p in sg.check(tmp_path, ratchet, wall=20))


def test_write_ratchet_never_raises_a_baseline(tmp_path):
    big = tmp_path / "big.py"
    _py(big, 30)
    ratchet = tmp_path / "r.json"
    sg.write_ratchet(tmp_path, ratchet, wall=20)
    _py(big, 40)
    sg.write_ratchet(tmp_path, ratchet, wall=20)
    assert json.loads(ratchet.read_text())["big.py"]["lines"] == 30


def test_stale_entry_fails(tmp_path):
    ratchet = tmp_path / "r.json"
    ratchet.write_text(json.dumps({"gone.py": {"lines": 50}}), encoding="utf-8")
    assert any("STALE" in p for p in sg.check(tmp_path, ratchet, wall=20))
