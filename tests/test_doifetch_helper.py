"""scripts/doifetch.sh runs DOIfetch on demand through uvx at a pinned ref (ticket 1343)."""

import re
import subprocess
from pathlib import Path

import pytest

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
    done = subprocess.run(
        ["bash", str(HELPER), *args], env=env, capture_output=True, text=True
    )
    return done, log


def test_helper_pins_a_commit_and_forwards_arguments(tmp_path):
    done, log = _run(
        tmp_path, "--source", "crossref", "--doi", "10.1000/a b", "--title", "T"
    )
    assert done.returncode == 0, done.stderr
    argv = log.read_text().splitlines()
    assert argv[:2] == ["-q", "--from"]
    assert re.fullmatch(
        r"git\+https://\S+/DOIfetch@(v\d+\.\d+\.\d+|[0-9a-f]{40})", argv[2]
    ), argv[2]
    assert argv[3:] == [
        "doifetch",
        "--source",
        "crossref",
        "--doi",
        "10.1000/a b",
        "--title",
        "T",
    ]


def test_helper_without_uvx_names_the_prerequisite(tmp_path):
    done, _ = _run(tmp_path, "--help", uvx=False)
    assert done.returncode == 127
    assert "uvx not found" in done.stderr


def test_failed_download_is_69_not_a_fetch_failure(tmp_path):
    done, log = _run(
        tmp_path, "--source", "crossref", "--doi", "10.1000/a", download_rc=1
    )
    assert done.returncode == 69
    assert "could not get DOIfetch" in done.stderr
    assert not log.exists()  # the fetch never ran


def test_fetch_failure_passes_through(tmp_path):
    done, log = _run(tmp_path, "--source", "crossref", "--doi", "10.1000/a", fetch_rc=1)
    assert done.returncode == 1
    assert log.exists()


@pytest.mark.integration
def test_open_success_never_requires_shadow_extra(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "args"
    stub = path / "uvx"
    stub.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$3\" >> '{log}'\n"
        '[ "$5" = -c ] && exit 0\n'
        'printf \'%s\\n\' \'{"status":"success","source":"hal"}\'\n'
    )
    stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    result = subprocess.run(
        ["bash", str(HELPER), "--doi", "10.1000/example", "--title", "T"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert '"source":"hal"' in result.stdout
    assert all("[shadow]" not in line for line in log.read_text().splitlines())


@pytest.mark.integration
def test_missing_shadow_extra_reports_open_failure(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    stub = path / "uvx"
    stub.write_text(
        "#!/bin/sh\n"
        "case \"$3\" in *'[shadow]'*) exit 1;; esac\n"
        '[ "$5" = -c ] && exit 0\n'
        'printf \'%s\\n\' \'{"status":"failed","path":"/tmp/example.pdf"}\'\n'
        "exit 1\n"
    )
    stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    result = subprocess.run(
        ["bash", str(HELPER), "--doi", "10.1000/example", "--title", "T"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 69
    assert "open sources failed" in result.stderr
    assert "shadow extra" in result.stderr


@pytest.mark.integration
def test_shadow_fallback_preserves_target_and_follows_open_failure(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "args"
    stub = path / "uvx"
    stub.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
        '[ "$5" = -c ] && exit 0\n'
        '[ "$7" = open ] && { printf \'%s\\n\' \'{"status":"failed","path":"/tmp/book name.pdf"}\'; exit 1; }\n'
        'printf \'%s\\n\' \'{"status":"success","source":"scihub"}\'\n'
    )
    stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    result = subprocess.run(
        ["bash", str(HELPER), "--doi", "10.1000/a", "--title", "T"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert '"source":"scihub"' in result.stdout
    log_text = log.read_text()
    assert "--phase open" in log_text
    assert "--phase shadow --output-path /tmp/book name.pdf" in log_text
    assert log_text.index("--phase open") < log_text.index("[shadow]")


@pytest.mark.integration
def test_isbn_lookup_error_does_not_try_shadow(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "args"
    stub = path / "uvx"
    stub.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$3" >> "{log}"\n'
        '[ "$5" = -c ] && exit 0\n'
        'printf \'%s\\n\' \'{"status":"failed","error":"Crossref unavailable"}\'\n'
        "exit 3\n"
    )
    stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    result = subprocess.run(
        ["bash", str(HELPER), "--isbn", "9780674009691"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert "Crossref unavailable" in result.stdout
    assert "[shadow]" not in log.read_text()
