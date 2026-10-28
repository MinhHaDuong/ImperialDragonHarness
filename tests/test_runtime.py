"""Tickets 1309, 1311: scripts/runtime.py (selection, which, can, typed NOOP) and its wake verb,
with stubbed systemd-run and codex. Each backend has a positive and a negative control."""

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import runtime  # noqa: E402
import runtime_wake  # noqa: E402

MARKERS = ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID", "PI_CODING_AGENT", "AI_AGENT",
           "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_NIGHT_SWEEP", "IDH_WAKE_INBOX")
STUB = f"""#!{sys.executable}
import json, os, sys
open(os.environ["STUB_LOG"], "a").write(json.dumps([os.path.basename(sys.argv[0])] + sys.argv[1:]) + "\\n")
sys.exit(int(os.environ.get("STUB_RC", "0")))
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    """No runtime markers; PATH holds only the stub directory."""
    for key in MARKERS:
        monkeypatch.delenv(key, raising=False)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.setenv("STUB_LOG", str(tmp_path / "stub.log"))
    return bindir


def stub(bindir, *names):
    for name in names:
        path = bindir / name
        path.write_text(STUB)
        path.chmod(0o755)


def calls(tmp_path):
    log = tmp_path / "stub.log"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def cli(capsys, *argv):
    rc = runtime.main(list(argv))
    out = capsys.readouterr()
    return rc, out.out.strip(), out.err.strip()


# --- selection ------------------------------------------------------------------------------

def test_auto_without_markers_exits_3(env, capsys):
    rc, out, err = cli(capsys, "which")
    assert rc == 3 and out == "" and "no runtime markers" in err


def test_two_runtimes_markers_exit_3_never_first_wins(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-1")
    rc, out, err = cli(capsys, "which")
    assert rc == 3 and out == ""
    assert "claude and codex" in err


@pytest.mark.parametrize("key,value,rt", [
    ("CLAUDECODE", "1", "claude"),
    ("CLAUDE_CODE_SESSION_ID", "s-1", "claude"),
    ("CODEX_THREAD_ID", "t-1", "codex"),
    ("PI_CODING_AGENT", "true", "pi"),
    ("AI_AGENT", "pi", "pi"),
])
def test_each_marker_selects_its_runtime(env, monkeypatch, capsys, key, value, rt):
    monkeypatch.setenv(key, value)
    rc, out, _ = cli(capsys, "which")
    assert rc == 0 and out.startswith(f"runtime={rt} ")


def test_claude_ai_agent_value_is_not_a_pi_marker(env, monkeypatch):
    monkeypatch.setenv("AI_AGENT", "claude-code_2-1-312_agent")
    assert runtime.markers(os.environ) == []


def test_which_reports_session_and_headless(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s-9")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "sdk-cli")
    assert cli(capsys, "which")[1] == "runtime=claude session=s-9 headless=yes"


def test_explicit_flag_wins_over_markers_and_unknown_is_unreadable(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-1")
    assert cli(capsys, "--runtime", "codex", "which")[1].startswith("runtime=codex session=t-1")
    rc, _, err = cli(capsys, "--runtime", "vim", "which")
    assert rc == 3 and "unknown runtime" in err


# --- can and NOOP ---------------------------------------------------------------------------

def test_can_answers_yes_no_with_a_typed_noop_line(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    assert cli(capsys, "can", "wake")[:2] == (0, "YES wake claude")
    assert cli(capsys, "can", "wake.arm")[0] == 0
    rc, out, _ = cli(capsys, "can", "wake.send")
    assert rc == 1 and out.startswith("NOOP can wake.send claude: ")
    rc, out, _ = cli(capsys, "can", "teleport")
    assert rc == 1 and out.startswith("NOOP can teleport claude: no verb")


def test_can_without_markers_exits_3(env, capsys):
    assert cli(capsys, "can", "wake")[0] == 3


def test_verbs_are_an_explicit_list():
    assert runtime_wake in runtime.VERBS
    assert "import_module" not in (SCRIPTS / "runtime.py").read_text()


# --- Claude Code ----------------------------------------------------------------------------

def test_claude_arm_prints_the_background_command(env, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDECODE", "1")
    rc, out, _ = cli(capsys, "wake", "arm", "--after", "5", "--cmd", "echo WAKE-OK")
    assert rc == 0 and out.startswith("RUN-IN-BACKGROUND ")
    argv = shlex.split(out.removeprefix("RUN-IN-BACKGROUND "))
    assert argv[argv.index("--cmd") + 1] == "echo WAKE-OK"
    assert os.path.isabs(argv[0]) and os.path.isabs(argv[1])


@pytest.mark.integration
def test_claude_printed_command_runs_and_delivers(env, monkeypatch, capsys):
    """Positive control: the printed line, shlex-split and run with --after 0, prints the wake."""
    monkeypatch.setenv("CLAUDECODE", "1")
    out = cli(capsys, "wake", "arm", "--after", "0", "--cmd", "echo WAKE-OK; exit 4")[1]
    done = subprocess.run(shlex.split(out.removeprefix("RUN-IN-BACKGROUND ")), capture_output=True,
                          text=True, timeout=30)
    assert done.returncode == 0
    assert done.stdout.strip() == "echo WAKE-OK; exit 4 exited 4: WAKE-OK"


@pytest.mark.integration
def test_cmd_runs_under_bash_so_a_seconds_poll_waits(env, monkeypatch, capsys):
    """Gaze finding on PR 1890: under dash, merge's `$SECONDS` poll exited at once."""
    monkeypatch.setenv("PATH", f"{env}:/usr/bin:/bin")
    monkeypatch.setenv("CLAUDECODE", "1")
    poll = 'end=$((SECONDS + 1)); while [ "$SECONDS" -lt "$end" ]; do sleep 0.2; done; echo "polled ${BASH_VERSION:+bash}"'
    out = cli(capsys, "wake", "arm", "--after", "0", "--cmd", poll)[1]
    done = subprocess.run(shlex.split(out.removeprefix("RUN-IN-BACKGROUND ")), capture_output=True,
                          text=True, timeout=30)
    assert done.stdout.strip().endswith("exited 0: polled bash"), done.stdout


def test_claude_negative_controls(env, monkeypatch, capsys):
    """Headless has no session to wake; send and disarm are typed NOOPs."""
    monkeypatch.setenv("CLAUDECODE", "1")
    rc, out, _ = cli(capsys, "wake", "send", "--session", "x", "--message", "hi")
    assert rc == 1 and out.startswith("NOOP wake send claude: ")
    assert cli(capsys, "wake", "disarm")[0] == 1
    monkeypatch.setenv("CLAUDE_NIGHT_SWEEP", "1")
    rc, out, _ = cli(capsys, "wake", "arm", "--after", "0", "--cmd", "true")
    assert rc == 1 and "headless" in out


# --- Codex ----------------------------------------------------------------------------------

def unit_command(argv):
    """The command a systemd-run call runs: everything after its own options."""
    i = 1
    while argv[i].startswith("--"):
        i += 1
    return argv[i:]


@pytest.mark.integration
def test_codex_arm_queues_cmd_output_through_the_unit(env, tmp_path, monkeypatch, capsys):
    """Positive control: re-run the logged unit command; codex is called with queue --thread."""
    stub(env, "systemd-run", "codex")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-42")
    rc, out, _ = cli(capsys, "wake", "arm", "--after", "30", "--cmd", "echo hi")
    assert rc == 0 and out.startswith("ARMED codex idh-wake-") and "thread=t-42" in out
    (systemd,) = calls(tmp_path)
    assert "--user" in systemd and "--on-active=30" in systemd
    assert f"--setenv=PATH={env}" in systemd
    assert "--expand-environment=no" in systemd
    command = unit_command(systemd)
    assert os.path.isabs(command[0]) and os.path.isabs(command[1])
    assert command[command.index("--codex") + 1] == str(env / "codex")
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0 and done.stdout.strip() == "QUEUED codex t-42"
    assert "DELIVERED" not in done.stdout
    assert calls(tmp_path)[1] == ["codex", "queue", "--thread", "t-42", "--message", "echo hi exited 0: hi"]


def test_codex_arm_without_systemd_run_is_noop(env, tmp_path, monkeypatch, capsys):
    """Negative control: no systemd-run (CI) answers NOOP, and nothing is called."""
    stub(env, "codex")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-42")
    rc, out, _ = cli(capsys, "wake", "arm", "--after", "1", "--cmd", "true")
    assert rc == 1 and out.startswith("NOOP wake arm codex: ") and "systemd-run" in out
    assert cli(capsys, "can", "wake.arm")[0] == 1
    assert calls(tmp_path) == []


@pytest.mark.integration
def test_codex_send_queues_and_a_failed_queue_exits_2(env, tmp_path, monkeypatch, capsys):
    stub(env, "codex")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-1")
    rc, out, _ = cli(capsys, "wake", "send", "--session", "t-7", "--message", "go")
    assert (rc, out) == (0, "QUEUED codex t-7")
    assert calls(tmp_path) == [["codex", "queue", "--thread", "t-7", "--message", "go"]]
    monkeypatch.setenv("STUB_RC", "1")
    assert cli(capsys, "wake", "send", "--session", "t-7", "--message", "go")[0] == 2


@pytest.mark.integration
def test_codex_disarm_stops_only_this_threads_units(env, tmp_path, monkeypatch, capsys):
    """Two Codex sessions on one user bus never cancel each other's wakes."""
    stub(env, "systemd-run", "systemctl", "codex")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-a")
    out = cli(capsys, "wake", "arm", "--after", "5", "--cmd", "true")[1]
    unit = out.split()[2]
    assert unit.startswith("idh-wake-t-a-")
    assert cli(capsys, "wake", "disarm")[:2] == (0, "DISARMED codex")
    stop = calls(tmp_path)[-1]
    assert stop == ["systemctl", "--user", "stop", "idh-wake-t-a-*.timer", "idh-wake-t-a-*.service"]


@pytest.mark.integration
def test_codex_failed_systemd_run_exits_2(env, monkeypatch, capsys):
    stub(env, "systemd-run", "codex")
    monkeypatch.setenv("CODEX_THREAD_ID", "t-1")
    monkeypatch.setenv("STUB_RC", "1")
    assert cli(capsys, "wake", "arm", "--after", "1", "--cmd", "true")[0] == 2


# --- Pi (writer side only; the reader extension is ticket 1316) -----------------------------

def test_pi_without_inbox_is_noop(env, monkeypatch, capsys):
    """Negative control: no extension loaded, every mode answers NOOP."""
    monkeypatch.setenv("AI_AGENT", "pi")
    for argv in (("arm", "--after", "0", "--cmd", "true"), ("send", "--session", "s", "--message", "m"),
                 ("disarm",)):
        rc, out, _ = cli(capsys, "wake", *argv)
        assert rc == 1 and "extension not loaded" in out


def test_pi_send_writes_one_message_file(env, tmp_path, monkeypatch, capsys):
    inbox = tmp_path / "inbox"
    monkeypatch.setenv("AI_AGENT", "pi")
    monkeypatch.setenv("IDH_WAKE_INBOX", str(inbox))
    rc, out, _ = cli(capsys, "wake", "send", "--session", "s", "--message", "hello")
    (msg,) = inbox.glob("*.msg")
    assert rc == 0 and out == f"QUEUED pi {msg}"
    assert msg.read_text() == "hello\n"


@pytest.mark.integration
def test_pi_arm_delivers_into_the_inbox(env, tmp_path, monkeypatch, capsys):
    """Positive control: the detached fire process writes the wake message and clears its pid."""
    inbox = tmp_path / "inbox"
    monkeypatch.setenv("AI_AGENT", "pi")
    monkeypatch.setenv("IDH_WAKE_INBOX", str(inbox))
    rc, out, _ = cli(capsys, "wake", "arm", "--after", "0", "--cmd", "echo PI-OK")
    assert rc == 0 and out.startswith("ARMED pi pid=")
    deadline = time.time() + 20
    while not list(inbox.glob("*.msg")) and time.time() < deadline:
        time.sleep(0.1)
    (msg,) = inbox.glob("*.msg")
    assert msg.read_text() == "echo PI-OK exited 0: PI-OK\n"
    while list((inbox / ".armed").glob("*.pid")) and time.time() < deadline:
        time.sleep(0.1)
    assert list((inbox / ".armed").glob("*.pid")) == []


@pytest.mark.integration
def test_pi_disarm_stops_a_pending_arm(env, tmp_path, monkeypatch, capsys):
    inbox = tmp_path / "inbox"
    monkeypatch.setenv("AI_AGENT", "pi")
    monkeypatch.setenv("IDH_WAKE_INBOX", str(inbox))
    cli(capsys, "wake", "arm", "--after", "60", "--cmd", "echo LATE")
    assert cli(capsys, "wake", "disarm")[:2] == (0, "DISARMED pi 1")
    assert list((inbox / ".armed").glob("*.pid")) == []


def test_wake_message_truncates_long_output():
    text = runtime_wake.message("c", 0, "x" * 5000)
    assert text.startswith("c exited 0: ...") and len(text) < 2100
    assert runtime_wake.message("c", 1, "  ") == "c exited 1: (no output)"
