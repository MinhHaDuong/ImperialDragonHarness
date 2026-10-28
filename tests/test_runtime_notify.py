"""runtime.py notify (ticket 1312): desktop popup via notify-send, alert file, rate limit per key."""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import runtime  # noqa: E402
import runtime_notify  # noqa: E402

STUB = f"""#!{sys.executable}
import json, os, sys
open(os.environ["STUB_LOG"], "a").write(json.dumps(sys.argv[1:]) + "\\n")
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Claude markers, PATH holding only a stub notify-send, alerts under tmp_path."""
    for key in ("CODEX_THREAD_ID", "PI_CODING_AGENT", "AI_AGENT", "CLAUDE_NIGHT_SWEEP"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("CLAUDECODE", "1")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "notify-send"
    stub.write_text(STUB)
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.setenv("STUB_LOG", str(tmp_path / "stub.log"))
    monkeypatch.setenv("IDH_ALERT_DIR", str(tmp_path / "alerts"))
    return tmp_path


def sent(tmp_path):
    log = tmp_path / "stub.log"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def notify(capsys, *extra):
    rc = runtime.main(["notify", "--key", "k1", "--title", "T", "--body", "B", *extra])
    return rc, capsys.readouterr().out.strip()


def test_second_call_within_repeat_does_not_call_notify_send(env, capsys):
    assert notify(capsys)[0] == 0
    rc, out = notify(capsys)
    assert rc == 0 and out == "SUPPRESSED k1"
    assert len(sent(env)) == 1


def test_first_call_passes_app_title_body_and_writes_alert_file(env, capsys):
    rc, out = notify(capsys)
    assert rc == 0 and out.startswith("NOTIFIED k1")
    assert sent(env) == [["-a", "idh", "T", "B"]]
    alert = json.loads((env / "alerts" / "k1.alert").read_text())
    assert alert["title"] == "T" and alert["body"] == "B"


def test_repeat_zero_never_suppresses(env, capsys):
    notify(capsys, "--repeat", "0")
    notify(capsys, "--repeat", "0")
    assert len(sent(env)) == 2


def test_other_key_is_not_suppressed(env, capsys):
    notify(capsys)
    rc = runtime.main(["notify", "--key", "k2", "--title", "T", "--body", "B"])
    assert rc == 0 and len(sent(env)) == 2


def test_expired_window_notifies_again(env, capsys):
    notify(capsys)
    state = env / "alerts" / "state.json"
    state.write_text(json.dumps({"k1": 1.0}))
    notify(capsys)
    assert len(sent(env)) == 2


def test_without_notify_send_writes_alert_file_only_and_says_so(env, monkeypatch, capsys):
    (env / "bin" / "notify-send").unlink()
    rc, out = notify(capsys)
    assert rc == 0 and "no notify-send" in out
    assert (env / "alerts" / "k1.alert").exists()


def test_failing_notify_send_still_writes_alert_and_exits_0(env, monkeypatch, capsys):
    (env / "bin" / "notify-send").write_text("#!/bin/sh\nexit 1\n")
    rc, out = notify(capsys)
    assert rc == 0 and "failed" in out and (env / "alerts" / "k1.alert").exists()


def test_key_cannot_escape_the_alert_dir(env, capsys):
    rc = runtime.main(["notify", "--key", "../x", "--title", "T", "--body", "B"])
    assert rc == 0
    assert not (env / "x.alert").exists()
    assert list((env / "alerts").glob("*.alert"))


def test_can_notify_is_yes_everywhere(env, capsys):
    assert runtime.main(["can", "notify"]) == 0


def test_notify_is_registered():
    assert runtime_notify in runtime.VERBS


def test_keys_that_sanitize_alike_keep_separate_alert_files():
    assert runtime_notify.safe_name("a/b") != runtime_notify.safe_name("a_b")
    assert runtime_notify.safe_name("k1") == "k1"
