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
        "--output-dir",
        "docs",
    ]


@pytest.mark.parametrize(
    "args",
    [
        ("--source", "crossref", "--doi", "10.1000/a"),
        ("--url", "https://example.org/a.pdf", "--title", "T"),
        ("--title", "T", "--source", "all"),
        (),
    ],
)
def test_every_passthrough_mode_names_its_output_directory(tmp_path, args):
    done, log = _run(tmp_path, *args)
    assert done.returncode == 0, done.stderr
    argv = log.read_text().splitlines()
    assert argv.count("--output-dir") == 1
    assert argv[argv.index("--output-dir") + 1] == "docs"


@pytest.mark.parametrize(
    "given", [["--output-dir", "elsewhere"], ["--output-dir=elsewhere"]]
)
def test_a_callers_output_directory_is_kept_not_doubled(tmp_path, given):
    done, log = _run(tmp_path, "--url", "https://example.org/a.pdf", *given)
    assert done.returncode == 0, done.stderr
    argv = log.read_text().splitlines()
    assert [a for a in argv if a.startswith("--output-dir")] == given[:1]
    assert "docs" not in argv


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
def test_open_success_skips_shadow_phase(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "args"
    stub = path / "uvx"
    stub.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{log}'\n"
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
    assert "--phase shadow" not in log.read_text()


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
    assert log_text.index("--phase open") < log_text.index("--phase shadow")
    # One plain spec serves both phases: no extra is requested (DOIfetch 0.4.0).
    assert "[shadow]" not in log_text


@pytest.mark.integration
def test_shadow_failure_exit_code_passes_through(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    stub = path / "uvx"
    stub.write_text(
        "#!/bin/sh\n"
        '[ "$5" = -c ] && exit 0\n'
        '[ "$7" = open ] && { printf \'%s\\n\' \'{"status":"failed","path":"/tmp/a.pdf"}\'; exit 1; }\n'
        'printf \'%s\\n\' \'{"status":"failed","error":"no mirror"}\'\n'
        "exit 4\n"
    )
    stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    result = subprocess.run(
        ["bash", str(HELPER), "--doi", "10.1000/a", "--title", "T"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 4
    assert "no mirror" in result.stdout


@pytest.mark.integration
def test_isbn_lookup_error_does_not_try_shadow(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "args"
    stub = path / "uvx"
    stub.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
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
    assert "--phase shadow" not in log.read_text()


def _fulltext_run(tmp_path, *args):
    """Run the --doi/--isbn mode with uvx stubbed; the cascade's argv lines."""
    path = tmp_path / "bin"
    path.mkdir()
    log = tmp_path / "args"
    stub = path / "uvx"
    stub.write_text(
        "#!/bin/sh\n"
        '[ "$5" = -c ] && exit 0\n'
        f'printf "%s\\n" "$*" >> "{log}"\n'
        'printf \'%s\\n\' \'{"status":"success","source":"hal"}\'\n'
    )
    stub.chmod(0o755)
    env = {"PATH": f"{path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run(
        ["bash", str(HELPER), *args], env=env, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    return log.read_text().splitlines()


@pytest.mark.integration
@pytest.mark.parametrize("mode", [("--doi", "10.1000/a"), ("--isbn", "9780674009691")])
def test_the_cascade_is_launched_with_an_explicit_output_directory(tmp_path, mode):
    (line,) = _fulltext_run(tmp_path, *mode, "--title", "T")
    words = line.split()
    assert words[words.index("--output-dir") + 1] == "docs"


@pytest.mark.integration
def test_the_cascades_own_output_directory_wins(tmp_path):
    (line,) = _fulltext_run(tmp_path, "--doi", "10.1000/a", "--output-dir", "x")
    assert line.split().count("--output-dir") == 1
    assert "--output-dir x" in line


SHADOW_FORMS = [
    ("--doi", "10.1000/a", "--source", "scihub"),
    ("--doi", "10.1000/a", "--source=scihub"),
    ("--isbn", "9780000000002", "--source", "libgen"),
    ("--isbn", "9780000000002", "--source=libgen"),
    ("--source", "scihub", "--doi", "10.1000/a"),
    ("--source", "libgen"),
    ("--source=scihub",),
    ("--fulltext", "--doi", "10.1000/a", "--source", "scihub"),
    ("--doi", "10.1000/a", "--source", "crossref,scihub"),
]


@pytest.mark.parametrize("args", SHADOW_FORMS)
def test_a_named_shadow_source_is_refused_before_anything_runs(tmp_path, args):
    done, log = _run(tmp_path, *args)
    assert done.returncode == 2, done.stderr
    assert not log.exists(), "the refusal must not launch DOIfetch"
    assert "--doi <doi>" in done.stderr and "--isbn <isbn>" in done.stderr


def test_a_named_shadow_source_is_refused_even_without_uvx(tmp_path):
    done, _ = _run(tmp_path, "--doi", "10.1000/a", "--source", "scihub", uvx=False)
    assert done.returncode == 2, done.stderr


@pytest.mark.parametrize(
    "args",
    [
        ("--doi", "10.1000/a", "--source", "crossref"),
        ("--title", "T", "--source", "all"),
        ("--title", "scihub"),
        ("--version",),
    ],
)
def test_other_sources_and_informational_modes_still_pass_through(tmp_path, args):
    done, log = _run(tmp_path, *args)
    assert done.returncode == 0, done.stderr
    assert log.exists()
