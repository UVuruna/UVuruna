"""Planted cases for gate.py: one PASS and one BLOCK per event, at least.

Every case builds a synthetic project in tmp_path — transcript JSONL, ledger,
evidence.jsonl — and runs `gate.py <event>` as a real subprocess with the hook
payload on stdin, so the exit-code contract is tested and not simulated.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parent / "gate.py"
T0 = datetime(2026, 8, 18, 10, 0, tzinfo=timezone.utc)


def at(minutes: int) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


# ═══════════════════════════ builders ═══════════════════════════

def user(text: str, minutes: int) -> dict:
    return {"type": "user", "timestamp": at(minutes),
            "message": {"role": "user", "content": text}}


def assistant(text: str, minutes: int) -> dict:
    return {"type": "assistant", "timestamp": at(minutes),
            "message": {"role": "assistant",
                        "content": [{"type": "text", "text": text}]}}


def tool_use(name: str, tool_input: dict, minutes: int, ident: str) -> dict:
    return {"type": "assistant", "timestamp": at(minutes),
            "message": {"role": "assistant",
                        "content": [{"type": "tool_use", "id": ident,
                                     "name": name, "input": tool_input}]}}


def tool_result(ident: str, text: str, minutes: int) -> dict:
    return {"type": "user", "timestamp": at(minutes),
            "message": {"role": "user",
                        "content": [{"type": "tool_result",
                                     "tool_use_id": ident, "content": text}]}}


def write_transcript(directory: Path, records, name="session.jsonl") -> Path:
    path = directory / name
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n",
                    encoding="utf-8")
    return path


def project(tmp_path: Path, session="s1") -> Path:
    root = tmp_path / "proj"
    (root / ".claude" / "sessions").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "evidence" / session).mkdir(parents=True,
                                                    exist_ok=True)
    (root / "gui").mkdir(exist_ok=True)
    (root / "src").mkdir(exist_ok=True)
    return root


def ledger(root: Path, body: str, session="s1") -> Path:
    path = root / ".claude" / "sessions" / f"{session}.md"
    path.write_text(body, encoding="utf-8")
    return path


def evidence(root: Path, rows, session="s1") -> Path:
    path = root / ".claude" / "evidence" / session / "evidence.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                    encoding="utf-8")
    return path


def run_gate(event: str, root: Path, transcript: Path, session="s1",
             tool_name=None, tool_input=None):
    payload = {"session_id": session, "transcript_path": str(transcript),
               "cwd": str(root), "hook_event_name": event}
    if tool_name:
        payload["tool_name"] = tool_name
        payload["tool_input"] = tool_input or {}
    done = subprocess.run([sys.executable, str(GATE), event],
                          input=json.dumps(payload), text=True,
                          capture_output=True, timeout=300)
    return done


def shot_row(ident, minutes, profile, artifact, rc=0, kind="shot"):
    return {"id": ident, "ts": at(minutes), "kind": kind, "cmd": "uv shot",
            "rc": rc, "profile": profile, "window": "MainWindow",
            "artifact": artifact, "sha256": "x", "summary": "ok"}


def ev_test_row(ident, minutes, rc=0, total=12):
    return {"id": ident, "ts": at(minutes), "kind": "test", "cmd": "uv test",
            "rc": rc, "passed": total if rc == 0 else 0,
            "failed": 0 if rc == 0 else 1, "total": total,
            "artifact": "junit.xml", "sha256": "x",
            "summary": f"{total if rc == 0 else 0}/{total}"}


LONG = "This is the full report. " * 40          # > 600 chars
GOOD_FINAL = ("Done: the card landed in Settings, both profiles were shot and "
              "graded 9, the regression test is green, and nothing else was "
              "touched. Next: your word on the build.")


# ═══════════════════════════ pre ═══════════════════════════

def test_pre_blocks_product_edit_without_category(tmp_path):
    root = project(tmp_path)
    ledger(root, "# no header here\n\n- [ ] T1 do the thing\n")
    transcript = write_transcript(tmp_path, [user("uradi", 0)])
    done = run_gate("pre", root, transcript, tool_name="Write",
                    tool_input={"file_path": str(root / "src" / "a.py"),
                                "content": "x = 1\n"})
    assert done.returncode == 2, done.stderr
    assert "category" in done.stderr.lower()
    assert len(done.stderr.strip().splitlines()) <= 3


def test_pre_passes_with_category(tmp_path):
    root = project(tmp_path)
    ledger(root, "# work\nkategorija: BUGFIX · klasa: Trivial\n\n- [ ] T1\n")
    transcript = write_transcript(tmp_path, [user("uradi", 0)])
    done = run_gate("pre", root, transcript, tool_name="Write",
                    tool_input={"file_path": str(root / "src" / "a.py"),
                                "content": "x = 1\n"})
    assert done.returncode == 0, done.stderr


def test_pre_blocks_editing_evidence_file(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: FEATURE · klasa: Trivial\n")
    transcript = write_transcript(tmp_path, [user("uradi", 0)])
    target = root / ".claude" / "evidence" / "s1" / "evidence.jsonl"
    done = run_gate("pre", root, transcript, tool_name="Write",
                    tool_input={"file_path": str(target),
                                "content": '{"id":"ev-0001"}\n'})
    assert done.returncode == 2, done.stderr
    assert "machine" in done.stderr.lower()


def test_pre_blocks_forbidden_gui_api(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: GUI · klasa: Standard\n")
    transcript = write_transcript(tmp_path, [user("uradi", 0)])
    done = run_gate("pre", root, transcript, tool_name="Edit",
                    tool_input={"file_path": str(root / "gui" / "panel.py"),
                                "new_string": "label.setFixedWidth(120)\n"})
    assert done.returncode == 2, done.stderr
    assert "setFixedWidth" in done.stderr


def test_pre_blocks_feature_without_matrix(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: FEATURE · klasa: Standard\n\n- [ ] T1\n")
    transcript = write_transcript(tmp_path, [user("dodaj feature", 0)])
    done = run_gate("pre", root, transcript, tool_name="Write",
                    tool_input={"file_path": str(root / "src" / "a.py"),
                                "content": "x = 1\n"})
    assert done.returncode == 2, done.stderr
    assert "matrica" in done.stderr.lower()


def test_pre_blocks_build_without_owner_word(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: BUILD · klasa: Standard\n")
    transcript = write_transcript(tmp_path, [user("sredi ovaj bag", 0)])
    done = run_gate("pre", root, transcript, tool_name="Bash",
                    tool_input={"command": "python setup/build.py"})
    assert done.returncode == 2, done.stderr
    assert "owner" in done.stderr.lower()


def test_pre_allows_build_on_owner_word(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: BUILD · klasa: Standard\n")
    transcript = write_transcript(tmp_path, [user("hajde izbilduj i objavi", 0)])
    done = run_gate("pre", root, transcript, tool_name="Bash",
                    tool_input={"command": "python setup/build.py"})
    assert done.returncode == 0, done.stderr


def test_pre_blocks_build_in_subagent(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: BUILD · klasa: Standard\n")
    sub = tmp_path / "s1" / "subagents"
    sub.mkdir(parents=True)
    transcript = write_transcript(sub, [user("izbilduj sve", 0)],
                                  name="agent-7.jsonl")
    done = run_gate("pre", root, transcript, tool_name="Bash",
                    tool_input={"command": "gh release create v1"})
    assert done.returncode == 2, done.stderr
    assert "sub-agent" in done.stderr.lower()


# ═══════════════════════════ prompt ═══════════════════════════

def test_prompt_creates_ledger_and_never_blocks(tmp_path):
    root = project(tmp_path, session="fresh")
    transcript = write_transcript(tmp_path, [user("zdravo", 0)])
    done = run_gate("prompt", root, transcript, session="fresh")
    assert done.returncode == 0, done.stderr
    created = root / ".claude" / "sessions" / "fresh.md"
    assert created.is_file()
    assert "kategorija" in done.stdout
    assert (root / ".claude" / "evidence" / "current").read_text().strip() \
        == "fresh"


# ═══════════════════════════ stop ═══════════════════════════

def test_stop_blocks_while_agents_run(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: DOCS · klasa: Standard\n\n- [x] T1 done\n"
                 "    ! wrote the docs\n")
    records = [user("kreni", 0),
               tool_use("Agent", {"description": "grader"}, 1, "t1"),
               tool_result("t1", "Async agent launched\nagentId: aaa111", 2)]
    records += [assistant("still working", 3 + i) for i in range(5)]
    transcript = write_transcript(tmp_path, records)
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "running" in done.stderr.lower()


def test_stop_blocks_open_task_without_question(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: DOCS · klasa: Standard\n\n"
                 "- [x] T1 done\n    ! wrote it\n- [ ] T2 not started\n")
    transcript = write_transcript(tmp_path, [
        user("kreni", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        assistant(GOOD_FINAL, 2)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "[?]" in done.stderr


def test_stop_blocks_done_task_without_evidence_line(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: DOCS · klasa: Standard\n\n- [x] T1 done\n")
    transcript = write_transcript(tmp_path, [
        user("kreni", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        assistant(GOOD_FINAL, 2)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "!" in done.stderr


def test_stop_gui_passes_with_two_fresh_graded_shots(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: GUI · klasa: Trivial\n\n"
                 "- [x] T1 panel\n"
                 "    ! ev-0001 shot MainWindow laptop-avg - looked - grade 9\n"
                 "    ! ev-0002 shot MainWindow pc-low - looked - grade 8\n")
    evidence(root, [shot_row("ev-0001", 5, "laptop-avg", "a.png"),
                    shot_row("ev-0002", 6, "pc-low", "b.png")])
    transcript = write_transcript(tmp_path, [
        user("popravi panel", 0),
        tool_use("Edit", {"file_path": str(root / "gui" / "panel.py"),
                          "new_string": "pass\n"}, 1, "t1"),
        tool_use("Read", {"file_path": str(root / "a.png")}, 7, "t2"),
        tool_use("Read", {"file_path": str(root / "b.png")}, 8, "t3"),
        assistant(GOOD_FINAL, 9)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 0, done.stderr


def test_stop_gui_blocks_stale_shot(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: GUI · klasa: Trivial\n\n"
                 "- [x] T1 panel\n"
                 "    ! ev-0001 shot MainWindow laptop-avg - grade 9\n"
                 "    ! ev-0002 shot MainWindow pc-low - grade 9\n")
    # both shots were taken BEFORE the GUI edit
    evidence(root, [shot_row("ev-0001", 0, "laptop-avg", "a.png"),
                    shot_row("ev-0002", 0, "pc-low", "b.png")])
    transcript = write_transcript(tmp_path, [
        user("popravi panel", 0),
        tool_use("Edit", {"file_path": str(root / "gui" / "panel.py"),
                          "new_string": "pass\n"}, 5, "t1"),
        tool_use("Read", {"file_path": str(root / "a.png")}, 6, "t2"),
        assistant(GOOD_FINAL, 7)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "shot" in done.stderr.lower()


def test_stop_feature_blocks_matrix_row_without_evidence(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: FEATURE · klasa: Standard\n\n"
                 "- [x] T1 new card\n    ! ev-0001 test 12/12\n\n"
                 "matrica:\n"
                 "| # | scenario | input | device | evidence |\n"
                 "| 1 | average device: main flow | fresh | laptop-avg | - |\n"
                 "| 2 | fresh install, no owner paths | - | pc-low | ev-0001 |\n")
    evidence(root, [ev_test_row("ev-0001", 9)])
    transcript = write_transcript(tmp_path, [
        user("dodaj karticu", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        assistant(GOOD_FINAL, 10)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "evidence" in done.stderr.lower()


def test_stop_bugfix_passes_red_before_green_after(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: BUGFIX · klasa: Standard\n"
                 "uzrok: the path was resolved against cwd, not the root\n\n"
                 "- [x] T1 fix\n    ! ev-0002 test 12/12\n")
    evidence(root, [ev_test_row("ev-0001", 0, rc=1),
                    ev_test_row("ev-0002", 9)])
    transcript = write_transcript(tmp_path, [
        user("puca kad se otvori", 0),
        tool_use("Edit", {"file_path": str(root / "src" / "a.py"),
                          "new_string": "pass\n"}, 5, "t1"),
        assistant(GOOD_FINAL, 10)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 0, done.stderr


def test_stop_bugfix_blocks_repeat_without_process_cause(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: BUGFIX · klasa: Standard\n"
                 "uzrok: the path was wrong\n\n"
                 "- [x] T1 fix\n    ! ev-0002 test 12/12\n")
    evidence(root, [ev_test_row("ev-0001", 0, rc=1), ev_test_row("ev-0002", 9)])
    transcript = write_transcript(tmp_path, [
        user("opet puca isto kao prosli put", 0),
        tool_use("Edit", {"file_path": str(root / "src" / "a.py"),
                          "new_string": "pass\n"}, 5, "t1"),
        assistant(GOOD_FINAL, 10)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "proces-uzrok" in done.stderr.lower()


def test_stop_blocks_final_one_liner_after_long_block(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: DOCS · klasa: Standard\n\n"
                 "- [x] T1 done\n    ! wrote the docs\n")
    transcript = write_transcript(tmp_path, [
        user("kreni", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.md"),
                           "content": "hello\n"}, 1, "t1"),
        assistant(LONG, 2),
        assistant("Gotovo.", 3)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "last block" in done.stderr.lower()


def test_stop_conversation_only_session_passes(tmp_path):
    root = project(tmp_path)   # no ledger at all, no edits
    transcript = write_transcript(tmp_path, [
        user("sta mislis o ovome", 0),
        assistant("Mislim da je bolje prvo izmeriti; evo zasto i sta predlazem "
                  "kao sledeci korak, sa posledicama svake opcije.", 1)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 0, done.stderr


def test_stop_blocks_agent_written_evidence(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: DOCS · klasa: Standard\n\n"
                 "- [x] T1 done\n    ! wrote it\n")
    evidence(root, [ev_test_row("ev-0001", 9)])
    transcript = write_transcript(tmp_path, [
        user("kreni", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        tool_use("Edit", {"file_path": str(root / ".claude" / "evidence"
                                           / "s1" / "evidence.jsonl"),
                          "new_string": '{"id":"ev-0009"}'}, 2, "t2"),
        assistant(GOOD_FINAL, 3)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "evidence" in done.stderr.lower()


def test_stop_installable_project_must_ask_for_build(tmp_path):
    root = project(tmp_path)
    (root / "CLAUDE.md").write_text("# proj\ninstallable: yes\n",
                                    encoding="utf-8")
    ledger(root, "# w\nkategorija: DOCS · klasa: Standard\n\n"
                 "- [x] T1 done\n    ! wrote it\n")
    transcript = write_transcript(tmp_path, [
        user("kreni", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        assistant(GOOD_FINAL, 2)])
    done = run_gate("stop", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "build" in done.stderr.lower()


# ═══════════════════════════ subagent ═══════════════════════════

def test_subagent_blocks_edit_without_run(tmp_path):
    root = project(tmp_path)
    sub = tmp_path / "s1" / "subagents"
    sub.mkdir(parents=True)
    transcript = write_transcript(sub, [
        user("sredi modul", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        assistant("Sredio sam modul.", 2)], name="agent-3.jsonl")
    done = run_gate("subagent", root, transcript)
    assert done.returncode == 2, done.stderr
    assert "ran nothing" in done.stderr.lower()


def test_subagent_passes_with_run_and_bang_line(tmp_path):
    root = project(tmp_path)
    sub = tmp_path / "s1" / "subagents"
    sub.mkdir(parents=True)
    transcript = write_transcript(sub, [
        user("sredi modul", 0),
        tool_use("Write", {"file_path": str(root / "src" / "a.py"),
                           "content": "x = 1\n"}, 1, "t1"),
        tool_use("Bash", {"command": "python rules/tools/uv.py test tests"},
                 2, "t2"),
        assistant("Report\n! ev-0004 test tests/test_a.py 6/6", 3)],
        name="agent-3.jsonl")
    done = run_gate("subagent", root, transcript)
    assert done.returncode == 0, done.stderr


# ═══════════════════════════ contract ═══════════════════════════

def test_gate_fails_open_on_broken_payload(tmp_path):
    done = subprocess.run([sys.executable, str(GATE), "stop"],
                          input="not json at all", text=True,
                          capture_output=True, timeout=60)
    assert done.returncode == 0


@pytest.mark.parametrize("event", ["prompt", "pre", "stop", "subagent"])
def test_gate_survives_missing_transcript(tmp_path, event):
    root = project(tmp_path)
    done = run_gate(event, root, tmp_path / "nope.jsonl", tool_name="Read",
                    tool_input={"file_path": str(root / "src" / "a.py")})
    assert done.returncode in (0, 2)


# ═══════════════════════════ scratch ═══════════════════════════

def test_pre_blocks_shell_write_to_drive_root(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: GUI · klasa: Trivial\n")
    transcript = write_transcript(tmp_path, [user("crop the shot", 0)])
    cmd = "cd proj && cat > " + "/tmp" + "_crop.py << 'PY'\nprint(1)\nPY"
    done = run_gate("pre", root, transcript, tool_name="Bash",
                    tool_input={"command": cmd})
    assert done.returncode == 2, done.stderr
    assert "leaves the project" in done.stderr


def test_pre_allows_shell_write_inside_project(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: GUI · klasa: Trivial\n")
    transcript = write_transcript(tmp_path, [user("crop the shot", 0)])
    done = run_gate("pre", root, transcript, tool_name="Bash",
                    tool_input={"command": "python x.py > .claude/tmp/out.txt 2>&1"})
    assert done.returncode == 0, done.stderr


def test_pre_blocks_write_tool_outside_project(tmp_path):
    root = project(tmp_path)
    ledger(root, "# w\nkategorija: GUI · klasa: Trivial\n")
    transcript = write_transcript(tmp_path, [user("note", 0)])
    outside = Path(root.anchor) / "tmp_notes.txt"   # the drive root, never written
    done = run_gate("pre", root, transcript, tool_name="Write",
                    tool_input={"file_path": str(outside), "content": "x"})
    assert done.returncode == 2, done.stderr
    assert "outside the project" in done.stderr


# ═══════════════════════════ artifact: seen before publish ═══════════════════════════

BALLOT_HTML = (
    "<title>t</title><style>body{background:#000;color:#fff}</style>"
    "<div class='option' data-option='a'><input type='checkbox' id='a'>"
    "<label for='a'>A</label><textarea></textarea></div>"
    "<div id='ballot'><textarea id='ballot-note'></textarea>"
    "<button id='ballot-copy'></button><textarea id='verdict'></textarea></div>"
)


def _device_row(ident, minutes, cmd, artifact):
    return {"id": ident, "ts": at(minutes), "kind": "device", "cmd": cmd,
            "rc": 0, "profile": "web-desktop", "artifact": artifact,
            "sha256": "x", "summary": "ok"}


def test_artifact_blocks_page_nobody_rendered(tmp_path):
    root = project(tmp_path)
    page = root / "page.html"
    page.write_text(BALLOT_HTML, encoding="utf-8")
    transcript = write_transcript(tmp_path, [user("napravi listić", 0)])
    done = run_gate("pre", root, transcript, tool_name="Artifact",
                    tool_input={"file_path": str(page), "favicon": "x"})
    assert done.returncode == 2, done.stderr
    assert "rendered" in done.stderr


def test_artifact_blocks_render_nobody_looked_at(tmp_path):
    root = project(tmp_path)
    page = root / "page.html"
    page.write_text(BALLOT_HTML, encoding="utf-8")
    evidence(root, [_device_row("ev-0001", 600, f"uv device web-desktop file:///{page.as_posix()}",
                                "device-0001-web-desktop.png")])
    transcript = write_transcript(tmp_path, [user("napravi listić", 0)])
    done = run_gate("pre", root, transcript, tool_name="Artifact",
                    tool_input={"file_path": str(page), "favicon": "x"})
    assert done.returncode == 2, done.stderr
    assert "LOOKED" in done.stderr


def test_artifact_passes_rendered_and_seen(tmp_path):
    root = project(tmp_path)
    page = root / "page.html"
    page.write_text(BALLOT_HTML, encoding="utf-8")
    evidence(root, [_device_row("ev-0001", 600, f"uv device web-desktop file:///{page.as_posix()}",
                                "device-0001-web-desktop.png")])
    transcript = write_transcript(tmp_path, [
        user("napravi listić", 0),
        tool_use("Read", {"file_path": str(root / ".claude" / "evidence" / "s1" /
                                           "device-0001-web-desktop.png")}, 601, "r1"),
        tool_result("r1", "image", 601),
    ])
    done = run_gate("pre", root, transcript, tool_name="Artifact",
                    tool_input={"file_path": str(page), "favicon": "x"})
    assert done.returncode == 0, done.stderr
