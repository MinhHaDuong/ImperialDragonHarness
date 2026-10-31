"""Ticket 1314: the `session` verb of scripts/runtime.py (`session id`, `session headless`)."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import runtime  # noqa: E402
import runtime_session  # noqa: E402

MARKERS = ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID", "PI_CODING_AGENT", "AI_AGENT",
           "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_NIGHT_SWEEP", "CLAUDE_CODE_CHILD_SESSION")


@pytest.fixture
def env(monkeypatch):
    for key in MARKERS:
        monkeypatch.delenv(key, raising=False)


def cli(capsys, *argv):
    rc = runtime.main(list(argv))
    out = capsys.readouterr()
    return rc, out.out.strip(), out.err.strip()


def test_registered():
    assert runtime_session in runtime.VERBS


def test_pi_session_id_comes_from_the_adapter_export(env, monkeypatch, capsys):
    monkeypatch.setenv("IDH_PI_SESSION_ID", "pi-3")  # exported by idh-wake.ts (ticket 1384)
    assert cli(capsys, "--runtime", "pi", "session", "id")[:2] == (0, "pi-3")


def test_pi_without_the_export_exits_3_not_an_empty_line(env, capsys):
    rc, out, err = cli(capsys, "--runtime", "pi", "session", "id")
    assert rc == 3 and out == "" and "IDH_PI_SESSION_ID unset" in err


def test_claude_session_id(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s-1")
    assert cli(capsys, "session", "id")[:2] == (0, "s-1")


def test_codex_session_id(env, monkeypatch, capsys):
    monkeypatch.setenv("CODEX_THREAD_ID", "th-2")
    assert cli(capsys, "session", "id")[:2] == (0, "th-2")


def test_claude_without_session_id_exits_3(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    rc, out, err = cli(capsys, "session", "id")
    assert rc == 3 and out == "" and err


def test_codex_explicit_without_thread_exits_3(env, capsys):
    rc, out, _ = cli(capsys, "--runtime", "codex", "session", "id")
    assert rc == 3 and out == ""


def test_headless_no_by_default(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    assert cli(capsys, "session", "headless")[:2] == (0, "no")


@pytest.mark.parametrize("key,val", [("CLAUDE_CODE_ENTRYPOINT", "sdk-cli"), ("CLAUDE_NIGHT_SWEEP", "1")])
def test_headless_markers(env, monkeypatch, capsys, key, val):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv(key, val)
    assert cli(capsys, "session", "headless")[:2] == (0, "yes")


def test_child_session_marker_is_not_headless_and_wake_works(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CLAUDE_CODE_CHILD_SESSION", "1")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    assert cli(capsys, "session", "headless")[:2] == (0, "no")
    assert cli(capsys, "can", "wake")[:2] == (0, "YES wake claude")


def test_headless_entrypoint_cli_is_interactive(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    assert cli(capsys, "session", "headless")[:2] == (0, "no")


def test_which_goes_through_the_verb_helpers(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s-9")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "sdk-cli")
    assert cli(capsys, "which")[1] == "runtime=claude session=s-9 headless=yes"
    assert runtime.headless is not None and runtime.session_id("claude", {"CLAUDE_CODE_SESSION_ID": "x"}) == "x"


def test_can_session(env, capsys):
    assert cli(capsys, "--runtime", "claude", "can", "session.id")[0] == 0
    assert cli(capsys, "--runtime", "pi", "can", "session.id")[0] == 0
    assert cli(capsys, "--runtime", "pi", "can", "session.headless")[0] == 0
