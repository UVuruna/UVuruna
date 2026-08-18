"""Self-test for the evidence runner (`rules/tools/uv.py`).

Run: `python -m pytest rules/tools/test_uv.py`

What is pinned here: ids are sequential and the file is append-only; `test`
counts a passing and a failing suite correctly; `run` measures start_ms under
a device profile; `shot` renders a synthetic Qt window and records the ALG
checks; a missing prerequisite becomes a `kind: unavailable` row, never a
silent pass.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import uv                                                      # noqa: E402
import uv_device                                               # noqa: E402

HAVE_QT = importlib.util.find_spec("PySide6") is not None


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    """A minimal project root: `.claude/` is what makes it one."""
    (tmp_path / ".claude").mkdir()
    return tmp_path


def run_uv(project: Path, *argv: str) -> int:
    return uv.main(["--project", str(project), "--session", "t", *argv])


def rows_of(project: Path) -> list[dict]:
    path = project / ".claude" / "evidence" / "t" / "evidence.jsonl"
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --- the evidence file itself ----------------------------------------------


def test_ids_are_sequential_and_the_file_is_append_only(project: Path):
    directory = project / ".claude" / "evidence" / "t"
    directory.mkdir(parents=True)
    evidence = uv.Evidence(project, "t", directory)
    for index in range(3):
        evidence.append(evidence.reserve(), "test", f"uv test {index}", 0,
                        f"row {index}")
    assert [row["id"] for row in rows_of(project)] == ["ev-0001", "ev-0002",
                                                       "ev-0003"]

    # A second runner in the same session continues the sequence and keeps
    # every earlier line byte for byte.
    before = (directory / "evidence.jsonl").read_text(encoding="utf-8")
    later = uv.Evidence(project, "t", directory)
    later.append(later.reserve(), "test", "uv test 3", 0, "row 3")
    after = (directory / "evidence.jsonl").read_text(encoding="utf-8")
    assert after.startswith(before)
    assert rows_of(project)[-1]["id"] == "ev-0004"


def test_a_reserved_id_is_not_handed_out_twice(project: Path):
    directory = project / ".claude" / "evidence" / "t"
    directory.mkdir(parents=True)
    evidence = uv.Evidence(project, "t", directory)
    assert evidence.reserve() != evidence.reserve()


def test_missing_current_falls_back_to_manual(project: Path, capsys):
    uv.main(["--project", str(project), "ls"])
    assert "manual" in capsys.readouterr().err
    assert (project / ".claude" / "evidence" / "manual").is_dir()


def test_session_id_comes_from_the_current_file(project: Path, capsys):
    evidence = project / ".claude" / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "current").write_text("s-42", encoding="utf-8")
    uv.main(["--project", str(project), "ls"])
    assert "session s-42" in capsys.readouterr().out


# --- uv test ----------------------------------------------------------------


def _write_suite(project: Path, name: str, body: str) -> Path:
    path = project / name
    path.write_text(body, encoding="utf-8")
    return path


def test_test_subcommand_records_a_passing_suite(project: Path):
    suite = _write_suite(project, "test_green.py",
                         "def test_one():\n    assert 1\n"
                         "def test_two():\n    assert 2\n")
    assert run_uv(project, "test", str(suite)) == 0
    row = rows_of(project)[-1]
    assert row["kind"] == "test" and row["rc"] == 0
    assert (row["passed"], row["failed"], row["total"]) == (2, 0, 2)
    assert row["summary"] == "2/2"
    assert row["artifact"].endswith(".xml") and row["sha256"]
    assert (project / row["artifact"]).is_file()


def test_test_subcommand_records_a_failing_suite(project: Path):
    suite = _write_suite(project, "test_red.py",
                         "def test_ok():\n    assert 1\n"
                         "def test_bad():\n    assert 0\n")
    assert run_uv(project, "test", str(suite)) != 0
    row = rows_of(project)[-1]
    assert row["kind"] == "test" and row["rc"] != 0
    assert (row["passed"], row["failed"], row["total"]) == (1, 1, 2)
    assert "1 failed" in row["summary"]


# --- uv run -----------------------------------------------------------------


def test_run_under_a_profile_measures_start_ms(project: Path):
    command = f'"{sys.executable}" -c "print(\'up\')"'
    assert run_uv(project, "run", command, "--profile", "pc-low",
                  "--timeout", "60") == 0
    row = rows_of(project)[-1]
    assert row["kind"] == "run" and row["profile"] == "pc-low"
    assert isinstance(row["start_ms"], int) and row["start_ms"] >= 0
    assert "start" in row["summary"]
    assert "up" in (project / row["artifact"]).read_text(encoding="utf-8")


def test_run_rejects_an_unknown_profile(project: Path):
    with pytest.raises(SystemExit):
        run_uv(project, "run", "echo hi", "--profile", "no-such-device")


# --- uv shot ----------------------------------------------------------------

_QT_REGISTRY = '''
TOOLKIT = "qt"
MANDATORY_PROFILES = ["pc-low"]


def _build(minimum):
    from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(QLabel("A synthetic window for the runner self-test"))
    layout.addWidget(QPushButton("Close"))
    window.setMinimumSize(*minimum)
    return window


def make_tiny():
    """A minimum that really holds the content - the ALG checks pass."""
    return _build((640, 160))


def make_cramped():
    """A minimum too small for its own label - CLIPPED, by construction."""
    return _build((120, 60))


WINDOWS = {"TinyWindow": make_tiny, "CrampedWindow": make_cramped}
'''


@pytest.mark.skipif(not HAVE_QT, reason="PySide6 is not installed")
def test_shot_renders_a_registered_qt_window(project: Path):
    (project / ".claude" / "uv_windows.py").write_text(_QT_REGISTRY,
                                                       encoding="utf-8")
    assert run_uv(project, "shot", "--window", "TinyWindow",
                  "--profile", "pc-low") == 0
    row = rows_of(project)[-1]
    assert row["kind"] == "shot"
    assert (row["window"], row["profile"]) == ("TinyWindow", "pc-low")
    assert row["checks"] == {"clipped": 0, "starved": 0, "min_fits": True}
    png = project / row["artifact"]
    assert png.is_file() and png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert row["sha256"] and len(row["sha256"]) == 64


@pytest.mark.skipif(not HAVE_QT, reason="PySide6 is not installed")
def test_shot_all_covers_every_window_and_fails_a_clipped_one(project: Path):
    (project / ".claude" / "uv_windows.py").write_text(_QT_REGISTRY,
                                                       encoding="utf-8")
    assert run_uv(project, "shot", "--all") == 1        # the cramped one fails
    rows = {row["window"]: row for row in rows_of(project)}
    assert set(rows) == {"TinyWindow", "CrampedWindow"}
    assert rows["TinyWindow"]["rc"] == 0
    cramped = rows["CrampedWindow"]
    assert cramped["rc"] == 1 and cramped["checks"]["clipped"] > 0
    assert "CLIPPED" in " ".join(cramped["faults"])


@pytest.mark.skipif(not HAVE_QT, reason="PySide6 is not installed")
def test_shot_of_an_unknown_window_is_unavailable(project: Path):
    (project / ".claude" / "uv_windows.py").write_text(_QT_REGISTRY,
                                                       encoding="utf-8")
    assert run_uv(project, "shot", "--window", "Ghost",
                  "--profile", "pc-low") == 3
    row = rows_of(project)[-1]
    assert row["kind"] == "unavailable" and row["rc"] == 3
    assert "not in WINDOWS" in row["summary"]


# --- missing prerequisites --------------------------------------------------


def test_shot_without_a_registry_is_unavailable(project: Path):
    assert run_uv(project, "shot", "--all") == 3
    row = rows_of(project)[-1]
    assert row["kind"] == "unavailable" and row["rc"] == 3
    assert "uv_windows.py" in row["summary"]
    assert row["artifact"] is None and row["sha256"] is None


def test_device_on_a_desktop_profile_is_unavailable(project: Path):
    assert run_uv(project, "device", "pc-low", "https://example.invalid") == 3
    row = rows_of(project)[-1]
    assert row["kind"] == "unavailable" and "web or android" in row["summary"]


def test_android_without_adb_is_unavailable(project: Path, monkeypatch):
    monkeypatch.setattr(uv_device, "_adb", lambda: None)
    assert run_uv(project, "device", "android-phone", "com.example.app") == 3
    row = rows_of(project)[-1]
    assert row["kind"] == "unavailable" and "adb" in row["summary"]


def test_android_without_device_or_avd_is_unavailable(project: Path,
                                                      monkeypatch):
    monkeypatch.setattr(uv_device, "_adb", lambda: "adb")
    monkeypatch.setattr(uv_device, "_adb_devices", lambda _adb: [])
    monkeypatch.setattr(uv_device, "_list_avds", lambda: [])
    assert run_uv(project, "device", "android-phone", "com.example.app") == 3
    assert "no Android device" in rows_of(project)[-1]["summary"]


# --- devices.json ------------------------------------------------------------


def test_every_profile_carries_the_fields_the_runner_reads():
    devices = uv.load_devices()
    assert devices["_doc"]
    for name, profile in devices["profiles"].items():
        assert profile["name"] == name
        assert profile["kind"] in ("desktop", "web", "android")
        for field in ("width", "height", "dpi_scale", "cores",
                      "affinity_mask", "priority", "cpu_throttle",
                      "network", "dpr", "checks", "budgets"):
            assert field in profile, f"{name} lacks {field}"
    assert devices["profiles"]["pc-owner"]["reference_only"] is True
