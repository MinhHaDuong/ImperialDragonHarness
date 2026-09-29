"""`idh install | check` on a disposable HOME (ticket 0987).

The expected link set comes from adapters/projections.json, never from what
install happened to create, so an entry install forgets is a failure here.
Every run uses a fixture HOME and a PATH whose `systemctl` is a stub that logs
its argv: nothing touches the developer's HOME, ~/.bashrc or systemd.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
IDH = REPO / "bin" / "idh"
MANIFEST = json.loads((REPO / "adapters" / "projections.json").read_text())["entries"]

pytestmark = pytest.mark.integration


def expand(spec: str, home: Path) -> Path:
    if spec.startswith("$IDH_ROOT"):
        return Path(str(REPO) + spec[len("$IDH_ROOT"):])
    return Path(str(home) + spec[1:])


@pytest.fixture
def machine(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "systemctl.log"
    stub = bin_dir / "systemctl"
    stub.write_text(f'#!/bin/sh\necho "$*" >> "{log}"\n')
    stub.chmod(0o755)
    env = {"HOME": str(home), "PATH": f"{bin_dir}:/usr/bin:/bin"}

    def idh(*args):
        return subprocess.run(
            [sys.executable, str(IDH), *args], env=env, capture_output=True, text=True, timeout=60
        )

    return {"home": home, "idh": idh, "log": log, "env": env}


def test_install_then_check_round_trip_and_planted_break(machine):
    home, idh = machine["home"], machine["idh"]
    r = idh("install")
    assert r.returncode == 0, r.stdout + r.stderr

    r = idh("check")  # positive control
    assert r.returncode == 0, r.stdout + r.stderr

    for entry in MANIFEST:
        if not entry["required"]:
            continue
        path = expand(entry["path"], home)
        target = expand(entry["target"], home)
        assert path.resolve() == target.resolve(), (path, target)
    assert (home / ".local" / "bin" / "idh").resolve() == IDH.resolve()
    assert "--user enable --now idh-mammoth-audit.timer" in machine["log"].read_text()
    assert (home / ".bashrc").read_text() == (REPO / "scripts" / "bashrc-loader.sh").read_text()

    # Negative control: one planted broken link, one named culprit.
    hooks = home / ".codex" / "hooks.json"
    hooks.unlink()
    hooks.symlink_to("/nonexistent")
    r = idh("check")
    assert r.returncode == 1
    culprits = [
        line for line in (r.stdout + r.stderr).splitlines()
        if line.lstrip().startswith(("MISSING:", "DANGLING:", "FOREIGN:"))
    ]
    assert culprits == [f"  DANGLING: {hooks} -> /nonexistent resolves to nothing"], culprits


def test_install_is_idempotent_and_refuses_foreign_files(machine):
    home, idh = machine["home"], machine["idh"]
    hooks = home / ".codex" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text('{"mine": true}')
    r = idh("install")
    assert r.returncode == 1
    assert f"FOREIGN: {hooks} is a real file" in r.stdout + r.stderr
    assert hooks.read_text() == '{"mine": true}', "the only copy was overwritten"
    # The other entries still installed.
    assert (home / ".pi" / "agent" / "extensions" / "idh-guard.ts").is_symlink()

    hooks.unlink()
    assert idh("install").returncode == 0
    r = idh("install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "installed:" not in r.stdout


def test_skill_subcommands_still_reach_perch(machine):
    r = machine["idh"]("check", "harness", "pi", "--version", "0.99.0")
    assert "pi:" in r.stdout + r.stderr


LOADER = (REPO / "scripts" / "bashrc-loader.sh").read_text()


def test_loader_file_is_delimited_by_its_markers():
    lines = LOADER.splitlines()
    assert lines[0].startswith("# >>> Imperial Dragon Harness loader")
    assert lines[-1].startswith("# <<< Imperial Dragon Harness loader")


def test_loader_splice_keeps_every_user_line(machine):
    """The padme case: a user alias AFTER the block must survive the update."""
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    stale = LOADER.replace("_idh_stubs\n", "_idh_stubs  # stale\n", 1)
    before, after = "export EDITOR=vi\n", "alias zotero='zotero --no-remote'\n"
    bashrc.write_text(before + stale + after)
    r = idh("install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert bashrc.read_text() == before + LOADER + after
    (backup,) = home.glob(".bashrc.idh-bak-*")
    assert backup.read_text() == before + stale + after

    snapshot = bashrc.stat().st_mtime_ns
    assert idh("install").returncode == 0
    assert bashrc.stat().st_mtime_ns == snapshot, "a rerun rewrote ~/.bashrc"


def test_loader_is_appended_when_absent(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    bashrc.write_text("alias ll='ls -l'")  # no final newline
    assert idh("install").returncode == 0
    assert bashrc.read_text() == "alias ll='ls -l'\n" + LOADER


@pytest.mark.parametrize(
    "legacy",
    [LOADER.split("\n", 1)[1].rsplit("# <<<", 1)[0],  # pre-marker block
     LOADER.rsplit("# <<<", 1)[0]],  # begin marker, end marker lost
    ids=["pre-marker", "no-end-marker"],
)
def test_legacy_loader_is_refused_not_guessed(machine, legacy):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    bashrc.write_text(legacy + "alias zotero=z\n")
    r = idh("install")
    assert r.returncode == 1
    assert "remove the old harness loader block" in r.stderr
    assert bashrc.read_text() == legacy + "alias zotero=z\n"


def test_status_reports_installed_vs_declared(machine):
    home, idh = machine["home"], machine["idh"]
    assert idh("install").returncode == 0
    r = idh("status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"declared {len(MANIFEST)}, ok " in r.stdout
    assert f"ok       {home / '.codex' / 'hooks.json'} -> " in r.stdout
    assert "timer    idh-mammoth-audit.timer:" in r.stdout
    assert "origin   " in r.stdout

    hooks = home / ".codex" / "hooks.json"
    hooks.unlink()
    r = idh("status")
    assert r.returncode == 1
    assert f"MISSING  {hooks} -> " in r.stdout
    assert "broken 1" in r.stdout


SYNC_FILES = (
    "bin/idh",
    "adapters/lifecycle.py",
    "adapters/projections.json",
    "scripts/validate-projections.py",
    "scripts/sync-local-main.sh",
)


def _git(cwd, *args):
    subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t",
         "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
        check=True, capture_output=True, text=True,
    )


def test_sync_fast_forwards_or_names_the_blocking_file(tmp_path, machine):
    """The padme case: an untracked file where an incoming one lands."""
    origin, upstream, local = tmp_path / "origin.git", tmp_path / "up", tmp_path / "local"
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(upstream))
    for rel in SYNC_FILES:
        (upstream / rel).parent.mkdir(parents=True, exist_ok=True)
        (upstream / rel).write_bytes((REPO / rel).read_bytes())
        (upstream / rel).chmod((REPO / rel).stat().st_mode)
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-qm", "base")
    _git(upstream, "push", "-q", "origin", "HEAD:main")
    _git(tmp_path, "clone", "-q", str(origin), str(local))

    (upstream / "notes.md").write_text("incoming\n")
    _git(upstream, "add", "notes.md")
    _git(upstream, "commit", "-qm", "notes")
    _git(upstream, "push", "-q", "origin", "HEAD:main")
    (local / "notes.md").write_text("mine, untracked\n")

    def sync():
        return subprocess.run(
            [sys.executable, str(local / "bin" / "idh"), "sync"],
            env=machine["env"], capture_output=True, text=True, timeout=60,
        )

    r = sync()
    assert r.returncode == 1
    assert "notes.md" in r.stdout
    assert "not synced" in r.stderr
    assert (local / "notes.md").read_text() == "mine, untracked\n"

    (local / "notes.md").unlink()  # positive control: the blocker gone, sync lands
    r = sync()
    assert r.returncode == 0, r.stdout + r.stderr
    assert (local / "notes.md").read_text() == "incoming\n"

    origin.rename(tmp_path / "gone.git")  # offline: a skipped sync is not a success
    r = sync()
    assert r.returncode == 1
    assert "not synced" in r.stderr


def test_loader_splice_keeps_crlf_and_non_utf8_bytes(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    before, after = b"export A=1\r\n# caf\xe9 latin-1\r\n", b"alias z=zotero\r\n"
    bashrc.write_bytes(before + after)
    assert idh("install").returncode == 0
    assert bashrc.read_bytes() == before + after + LOADER.encode()
    stale = bashrc.read_bytes().replace(b"_idh_stubs\n", b"_idh_stubs  # stale\n", 1)
    bashrc.write_bytes(stale)
    assert idh("install").returncode == 0
    assert bashrc.read_bytes() == before + after + LOADER.encode()


def test_two_loader_blocks_are_refused(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    bashrc.write_text(LOADER + "alias a=b\n" + LOADER)
    r = idh("install")
    assert r.returncode == 1
    assert "more than one loader block" in r.stderr
    assert bashrc.read_text() == LOADER + "alias a=b\n" + LOADER


def test_links_go_through_the_pointer_and_a_blocked_parent_is_named(machine):
    home, idh = machine["home"], machine["idh"]
    (home / ".pi").write_text("a file where a directory belongs\n")
    r = idh("install")
    assert r.returncode == 1
    assert f"REFUSED: {home / '.pi' / 'agent' / 'extensions' / 'idh-guard.ts'}" in r.stderr
    # The run went on: the loader and the other links are in place.
    assert (home / ".bashrc").read_text() == LOADER
    hooks = home / ".codex" / "hooks.json"
    assert str(hooks.readlink()).startswith(str(home / ".idh")), hooks.readlink()
