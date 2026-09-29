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
    assert (home / ".bashrc.idh-bak").read_text() == before + stale + after

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
