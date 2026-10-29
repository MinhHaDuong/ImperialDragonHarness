"""scripts/doifetch.sh runs DOIfetch on demand through uvx at a pinned ref (ticket 1343)."""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "scripts" / "doifetch.sh"


def _run(tmp_path, *args, uvx=True):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "uvx.log"
    if uvx:
        stub = path / "uvx"
        stub.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{log}"\n')
        stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run(["bash", str(HELPER), *args], env=env, capture_output=True, text=True)
    return done, log


def test_helper_pins_a_commit_and_forwards_arguments(tmp_path):
    done, log = _run(tmp_path, "--doi", "10.1000/a b", "--title", "T")
    assert done.returncode == 0, done.stderr
    argv = log.read_text().splitlines()
    assert argv[0] == "--from"
    assert re.fullmatch(r"git\+https://\S+/DOIfetch@[0-9a-f]{40}", argv[1]), argv[1]
    assert argv[2:] == ["doifetch", "--doi", "10.1000/a b", "--title", "T"]


def test_helper_without_uvx_names_the_prerequisite(tmp_path):
    done, _ = _run(tmp_path, "--help", uvx=False)
    assert done.returncode == 127
    assert "uvx not found" in done.stderr
