"""Ticket 1383: the transcript archive copies each aged file once and again when it grows."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transcript_archive.py"
NOW = 2_000_000_000.0
pytestmark = pytest.mark.integration


@pytest.fixture
def world(tmp_path):
    env = child_env()
    env.update(HOME=str(tmp_path / "home"), IDH_ARCHIVE_ROOT=str(tmp_path / "archive"))
    for key in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "PI_CODING_AGENT_DIR"):
        env.pop(key, None)
    home = tmp_path / "home"
    files = {
        "claude": home / ".claude/projects/-p/aaa.jsonl",
        "claude-sub": home / ".claude/projects/-p/aaa/subagents/agent-1.jsonl",
        "claude-tool": home / ".claude/projects/-p/aaa/tool-results/t.txt",
        "codex": home / ".codex/sessions/2026/10/31/rollout-1.jsonl",
        "pi": home / ".pi/agent/sessions/--p--/s.jsonl",
    }
    for name, path in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{name} line\n" * 50)
        os.utime(path, (NOW - 2 * 86400, NOW - 2 * 86400))
    host = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip().split(".")[0]
    spool = tmp_path / "archive/spool" / host / "vibe/20260101T000000Z-1/session/m.json"
    spool.parent.mkdir(parents=True)
    spool.write_text("vibe session\n")
    os.utime(spool, (NOW - 2 * 86400, NOW - 2 * 86400))
    files["vibe"] = spool
    return {"env": env, "files": files, "out": tmp_path / "archive/raw" / host, "home": home}


def archive(world, *extra, now=NOW):
    return subprocess.run([sys.executable, str(SCRIPT), "--now", str(now), *extra],
                          env=world["env"], capture_output=True, text=True, timeout=60)


def zstd_text(path):
    return subprocess.run(["zstd", "-dc", str(path)], capture_output=True, check=True).stdout


def target(world, runtime, rel):
    return world["out"] / runtime / (rel + ".zst")


def test_every_layout_is_archived_at_its_relative_path_byte_identical(world):
    result = archive(world)
    assert result.returncode == 0, result.stderr
    home = world["home"]
    expected = {
        "claude": ("claude", ".claude/projects", "claude"),
        "claude-sub": ("claude", ".claude/projects", "claude-sub"),
        "claude-tool": ("claude", ".claude/projects", "claude-tool"),
        "codex": ("codex", ".codex/sessions", "codex"),
        "pi": ("pi", ".pi/agent/sessions", "pi"),
    }
    for name, (runtime, live, key) in expected.items():
        source = world["files"][key]
        dest = target(world, runtime, str(source.relative_to(home / live)))
        assert dest.is_file(), name
        assert zstd_text(dest) == source.read_bytes(), name
        assert dest.stat().st_mtime_ns == source.stat().st_mtime_ns
        assert dest.stat().st_mode & 0o077 == 0  # as private as the live tree
    vibe = world["out"] / "vibe/20260101T000000Z-1/session/m.json.zst"
    assert zstd_text(vibe) == b"vibe session\n"


def test_unchanged_is_not_recopied_and_grown_is(world):
    archive(world)
    stable, grown = target(world, "codex", "2026/10/31/rollout-1.jsonl"), target(world, "claude", "-p/aaa.jsonl")
    before = {p: (p.stat().st_ino, p.stat().st_mtime_ns) for p in (stable, grown)}
    source = world["files"]["claude"]
    with source.open("a") as handle:
        handle.write("appended\n")
    os.utime(source, (NOW - 86400 - 60, NOW - 86400 - 60))
    result = archive(world)
    assert result.returncode == 0 and "copied: 1 files" in result.stdout, result.stdout
    assert (stable.stat().st_ino, stable.stat().st_mtime_ns) == before[stable]
    assert zstd_text(grown).endswith(b"appended\n")


def test_a_file_touched_within_the_day_is_skipped(world):
    source = world["files"]["pi"]
    os.utime(source, (NOW - 3600, NOW - 3600))
    archive(world)
    assert not target(world, "pi", "--p--/s.jsonl").exists()
    assert target(world, "codex", "2026/10/31/rollout-1.jsonl").exists()
    assert archive(world, now=NOW + 86400).returncode == 0
    assert target(world, "pi", "--p--/s.jsonl").exists()  # a day later it qualifies


def test_verify_prints_matching_counts_and_bytes_and_detects_a_missing_copy(world):
    result = archive(world, "--verify")
    assert result.returncode == 0, result.stdout
    size = sum(p.stat().st_size for p in world["files"].values())
    assert f"eligible: 6 files {size} bytes" in result.stdout
    assert f"archived: 6 files {size} bytes" in result.stdout
    # A half-written copy never stands in for the file: no stray .tmp after a run.
    assert not list(world["out"].rglob("*.tmp"))


def test_the_archive_never_writes_where_idh_archive_root_does_not_point(world, tmp_path):
    archive(world)
    assert not (world["home"] / "archive").exists()


def test_units_resolve_the_checkout_and_archive_from_the_home_of_the_running_user():
    unit = (ROOT / "scripts/systemd/transcript-archive.service").read_text()
    timer = (ROOT / "scripts/systemd/transcript-archive.timer").read_text()
    assert "ExecStart=/usr/bin/python3 %h/.agents/scripts/transcript_archive.py" in unit
    assert "/home/" not in unit + timer  # %h, so doudou installs the same files
    assert "Persistent=true" in timer and "Unit=transcript-archive.service" in timer


def _spool(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import transcript_spool as ts
    for key in ("IDH_ARCHIVE_ROOT", "DATASETS_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(ts, "ENV_FILE", tmp_path / "home/.config/environment.d/50-datasets.conf")
    return ts


def _declare(tmp_path, text):
    conf = tmp_path / "home/.config/environment.d/50-datasets.conf"
    conf.parent.mkdir(parents=True, exist_ok=True)
    conf.write_text(text)


def test_archive_root_override_wins_and_empty_counts_as_unset(tmp_path, monkeypatch):
    ts = _spool(tmp_path, monkeypatch)
    monkeypatch.setenv("DATASETS_DIR", str(tmp_path / "d"))
    monkeypatch.setenv("IDH_ARCHIVE_ROOT", str(tmp_path / "x"))
    assert ts.archive_root() == tmp_path / "x"
    monkeypatch.setenv("IDH_ARCHIVE_ROOT", "")
    assert ts.archive_root() == tmp_path / "d/ours/agent-sessions"


def test_archive_root_from_datasets_dir_ignores_directories_present(tmp_path, monkeypatch):
    ts = _spool(tmp_path, monkeypatch)
    (tmp_path / "home/data/datasets/ours").mkdir(parents=True)  # a probe would have chosen this
    monkeypatch.setenv("DATASETS_DIR", str(tmp_path / "d"))
    assert ts.archive_root() == tmp_path / "d/ours/agent-sessions"


def test_archive_root_file_fallback_without_environment(tmp_path, monkeypatch):
    ts = _spool(tmp_path, monkeypatch)
    _declare(tmp_path, f"# Host data locations\nMIRRORS_DIR=/m\nDATASETS_DIR={tmp_path / 'f'}\n")
    assert ts.archive_root() == tmp_path / "f/ours/agent-sessions"
    monkeypatch.setenv("DATASETS_DIR", "")  # empty environment value falls through to the file
    assert ts.archive_root() == tmp_path / "f/ours/agent-sessions"


def test_archive_root_unknown_is_a_clear_error(tmp_path, monkeypatch, capsys):
    ts = _spool(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="DATASETS_DIR"):
        ts.archive_root()
    _declare(tmp_path, "# nothing declared\nMIRRORS_DIR=/m\n")
    with pytest.raises(RuntimeError, match="IDH_ARCHIVE_ROOT"):
        ts.archive_root()
    assert ts.main(["root"]) == 1 and "DATASETS_DIR" in capsys.readouterr().err


def test_raw_dir_and_private_dirs_under_the_root(tmp_path, monkeypatch):
    ts = _spool(tmp_path, monkeypatch)
    monkeypatch.setenv("DATASETS_DIR", str(tmp_path / "ours0"))
    assert ts.raw_dir("h") == tmp_path / "ours0/ours/agent-sessions/raw/h"
    ts.mkdir_private(ts.raw_dir("h") / "claude")
    assert {oct(p.stat().st_mode & 0o777) for p in (ts.raw_dir("h"), ts.raw_dir("h") / "claude")} == {"0o700"}


def test_push_script_derives_both_ends_from_the_declared_root(tmp_path):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "ssh").write_text('#!/bin/sh\necho /remote/datasets/ours/agent-sessions\n')
    (bin_ / "rsync").write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$RSYNC_OUT"\n')
    for tool in bin_.iterdir():
        tool.chmod(0o755)
    home = tmp_path / "home"
    (home / ".agents/scripts").mkdir(parents=True)
    (home / ".agents/scripts/transcript_spool.py").symlink_to(ROOT / "scripts/transcript_spool.py")
    env = child_env()
    env.update(HOME=str(home), IDH_ARCHIVE_ROOT=str(tmp_path / "archive"), RSYNC_OUT=str(tmp_path / "out"),
               PATH=f"{bin_}:{env['PATH']}")
    subprocess.run([str(ROOT / "scripts/transcript-push-padme")], env=env, check=True)
    args = (tmp_path / "out").read_text().split()
    host = subprocess.check_output(["hostname", "-s"], text=True).strip()
    assert args[-2:] == [f"{tmp_path}/archive/raw/{host}/",
                         f"padme:/remote/datasets/ours/agent-sessions/raw/{host}/"]
    unit = (ROOT / "scripts/systemd/push-padme.conf").read_text()
    assert "/data/" not in unit and "ExecStartPost=-%h/.agents/scripts/transcript-push-padme" in unit
