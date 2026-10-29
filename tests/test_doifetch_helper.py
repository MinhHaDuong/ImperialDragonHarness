"""scripts/doifetch.sh runs DOIfetch on demand through uvx at a pinned ref (ticket 1343)."""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "scripts" / "doifetch.sh"


def _run(tmp_path, *args, uvx=True, fetch_rc=0, download_rc=0):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "uvx.log"
    if uvx:
        # The helper calls uvx twice: `doifetch --help` to get the tool, then the fetch.
        stub = path / "uvx"
        stub.write_text(
            "#!/bin/sh\n"
            f'[ "$5" = --help ] && [ "$#" -eq 5 ] && exit {download_rc}\n'
            f'printf "%s\\n" "$@" > "{log}"\nexit {fetch_rc}\n'
        )
        stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run(["bash", str(HELPER), *args], env=env, capture_output=True, text=True)
    return done, log


def test_helper_pins_a_commit_and_forwards_arguments(tmp_path):
    done, log = _run(tmp_path, "--doi", "10.1000/a b", "--title", "T")
    assert done.returncode == 0, done.stderr
    argv = log.read_text().splitlines()
    assert argv[:2] == ["-q", "--from"]
    assert re.fullmatch(r"git\+https://\S+/DOIfetch@(v\d+\.\d+\.\d+|[0-9a-f]{40})", argv[2]), argv[2]
    assert argv[3:] == ["doifetch", "--doi", "10.1000/a b", "--title", "T"]


def test_helper_without_uvx_names_the_prerequisite(tmp_path):
    done, _ = _run(tmp_path, "--help", uvx=False)
    assert done.returncode == 127
    assert "uvx not found" in done.stderr


def test_failed_download_is_69_not_a_fetch_failure(tmp_path):
    done, log = _run(tmp_path, "--doi", "10.1000/a", download_rc=1)
    assert done.returncode == 69
    assert "could not get DOIfetch" in done.stderr
    assert not log.exists()  # the fetch never ran


def test_fetch_failure_passes_through(tmp_path):
    done, log = _run(tmp_path, "--doi", "10.1000/a", fetch_rc=1)
    assert done.returncode == 1
    assert log.exists()
