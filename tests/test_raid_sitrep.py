"""Ticket 1246: the raid sitrep renders from durable state and never fakes an all-clear.

Fixture values are hand-written in tests/fixtures/raid_log_sample.log
(raid started 1700000000, now 1700001500 = 25 min, PR 12 at gate round 2,
a STALL before the last SITREP, a GATE_TIMEOUT after it).
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURE = Path(__file__).parent / "fixtures" / "raid_log_sample.log"
NOW = "1700001500"

sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("raid_sitrep", SCRIPTS / "raid-sitrep.py")
assert spec and spec.loader
sitrep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitrep)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=child_env())
    monkeypatch.chdir(root)
    return root


def stub_gh(tmp_path, monkeypatch, body):
    """A `gh` on PATH that runs `body`; the rest of PATH stays for git."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text("#!/bin/sh\n" + body + "\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")


def log_with(tmp_path, monkeypatch, text):
    path = tmp_path / "raid.log"
    path.write_text(text)
    monkeypatch.setenv("IDH_RAID_LOG", str(path))
    return path


def run(capsys, *extra):
    code = sitrep.main(["--now", NOW, "--no-mark", *extra])
    return code, capsys.readouterr().out


def test_unreadable_state_exits_nonzero(repo, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDH_RAID_LOG", str(tmp_path / "missing.log"))
    code, out = run(capsys, "--no-forge")
    assert code == 2
    assert "UNREADABLE log" in out
    assert "all clear" not in out.lower()
    assert "NEXT" not in out  # no next action from state it could not read


def test_readable_fixture_exits_zero_positive_control(repo, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("IDH_RAID_LOG", str(FIXTURE))
    code, out = run(capsys, "--no-forge")
    assert code == 0
    assert "UNREADABLE" not in out


def test_renders_fixture_values(repo, monkeypatch, capsys):
    monkeypatch.setenv("IDH_RAID_LOG", str(FIXTURE))
    code, out = run(capsys, "--no-forge")
    assert "elapsed 25m" in out
    assert "120m" in out  # budget: deadline minus start
    assert "wave 1" in out and "1246" in out
    assert "PR 12" in out and "gate_round_2" in out
    assert "PR 13" in out and "merged" in out
    assert "GATE_TIMEOUT" in out  # after the last SITREP
    assert "STALL" not in out  # before the last SITREP
    assert "NEXT wait" in out  # ticket 1246 still in flight


def test_garbled_line_is_unreadable(repo, tmp_path, monkeypatch, capsys):
    log_with(tmp_path, monkeypatch, FIXTURE.read_text() + "this is not an event\n")
    code, out = run(capsys, "--no-forge")
    assert code == 2
    assert "UNREADABLE log line 10" in out


def test_missing_queue_is_unreadable(repo, tmp_path, monkeypatch, capsys):
    text = "".join(ln for ln in FIXTURE.read_text().splitlines(True) if " QUEUE " not in ln)
    log_with(tmp_path, monkeypatch, text)
    code, out = run(capsys, "--no-forge")
    assert code == 2
    assert "UNREADABLE queue" in out


def done_log(queue):
    return (
        "1700000000 RAID_START deadline=1700007200 gate_max=1800\n"
        "1700000060 WAVE n=1 tickets=1246\n"
        "1700000200 PR n=13 ticket=1246 step=merged\n"
        f"1700001000 QUEUE n={queue}\n"
    )


def test_idle_with_queue_resumes(repo, tmp_path, monkeypatch, capsys):
    log_with(tmp_path, monkeypatch, done_log(2))
    code, out = run(capsys, "--no-forge")
    assert code == 0
    assert "NEXT resume wave" in out


def test_idle_with_empty_queue_wraps_up(repo, tmp_path, monkeypatch, capsys):
    log_with(tmp_path, monkeypatch, done_log(0))
    code, out = run(capsys, "--no-forge")
    assert code == 0
    assert "NEXT wrap-up" in out


def test_forge_failure_is_unreadable(repo, tmp_path, monkeypatch, capsys):
    log_with(tmp_path, monkeypatch, done_log(0))
    stub_gh(tmp_path, monkeypatch, "echo 'auth failed' >&2; exit 1")
    code, out = run(capsys)
    assert code == 2
    assert "UNREADABLE forge" in out


def test_forge_open_prs_listed(repo, tmp_path, monkeypatch, capsys):
    log_with(tmp_path, monkeypatch, done_log(0))
    stub_gh(tmp_path, monkeypatch,
            """echo '[{"number":77,"headRefName":"t9-x","title":"t"}]'""")
    code, out = run(capsys)
    assert code == 0
    assert "#77" in out


def test_mark_appends_sitrep_line(repo, tmp_path, monkeypatch, capsys):
    path = log_with(tmp_path, monkeypatch, done_log(0))
    assert sitrep.main(["--now", NOW, "--no-forge"]) == 0
    assert path.read_text().splitlines()[-1] == f"{NOW} SITREP"


def test_unreadable_run_does_not_mark(repo, tmp_path, monkeypatch, capsys):
    path = log_with(tmp_path, monkeypatch, done_log(0) + "garbage\n")
    before = path.read_text()
    assert sitrep.main(["--now", NOW, "--no-forge"]) == 2
    assert path.read_text() == before  # breakers stay unreported until a clean read


def test_raid_log_helper_roundtrip(tmp_path, monkeypatch):
    import raid_log
    path = tmp_path / "x" / "raid.log"
    raid_log.append("PR", {"n": "5", "step": "gaze"}, path, now=1700000000)
    events, bad = raid_log.parse(path.read_text())
    assert bad == [] and events == [(1700000000.0, "PR", {"n": "5", "step": "gaze"})]
    with pytest.raises(ValueError):
        raid_log.append("bad event", {}, path)


def test_skill_arms_and_disarms_cadence():
    text = (SCRIPTS.parent / "skills" / "raid" / "SKILL.md").read_text()
    arm = text.find("raid-sitrep.py")
    assert arm != -1
    section = text.find("## Sitrep cadence")
    wrap = text.find("## Wrap up")
    assert 0 < section < wrap
    assert "harness-extension-point" in text[section:wrap]
    assert "disarm" in text[wrap:].lower()
    assert 'scripts/raid-sitrep.py' not in text.replace('$IDH_ROOT/scripts/raid-sitrep.py', '')
