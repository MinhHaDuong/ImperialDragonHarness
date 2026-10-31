"""Hermetic managed and npm Pi extension linking regressions (ticket 1089)."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.integration


@pytest.fixture
def fixture(tmp_path):
    utilities = tmp_path / "utilities"
    utilities.mkdir()
    for name in ("bash", "tr", "readlink", "dirname", "mkdir", "ln", "rm"):
        target = shutil.which(name)
        assert target
        (utilities / name).symlink_to(target)
    env = child_env()
    env.update(PI_HOME=str(tmp_path / "agent"), PATH=str(utilities),
               HOME=str(tmp_path / "home"), IDH_ARCHIVE_ROOT=str(tmp_path / "archive"), HOSTNAME="fixturehost.lan")
    return tmp_path, utilities, env


def modules(package):
    source = package / "examples/extensions/subagent"
    source.mkdir(parents=True)
    for name in ("index.ts", "agents.ts"):
        (source / name).write_text('// fixture\nconst args: string[] = ["--mode", "json", "-p", "--no-session"];\n')
    return source


def npm_install(fixture):
    base, utilities, _ = fixture
    package = base / "global/node_modules/@earendil-works/pi-coding-agent"
    source = modules(package)
    executable = package / "dist/cli.js"
    executable.parent.mkdir()
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    (utilities / "pi").symlink_to(executable)
    return source


def run_helper(fixture):
    return subprocess.run(
        ["/bin/bash", str(ROOT / "scripts/pi-subagent-link")],
        env=fixture[2], capture_output=True, text=True, check=False,
    )


def assert_links(fixture, source):
    dest = Path(fixture[2]["PI_HOME"]) / "extensions/subagent"
    assert (dest / "agents.ts").is_symlink()
    assert (dest / "agents.ts").resolve() == source / "agents.ts"
    patched = dest / "index.ts"  # a copy, never a link: the release file must stay untouched
    assert not patched.is_symlink()
    spool = Path(fixture[2]["IDH_ARCHIVE_ROOT"]) / "spool/fixturehost/pi"
    assert spool.is_dir()
    text = patched.read_text()
    assert f'"-p", "--session-dir", "{spool}"];' in text and '"--no-session"' not in text
    assert '"--no-session"' in (source / "index.ts").read_text()


def test_npm_global_links_and_is_idempotent(fixture):
    source = npm_install(fixture)
    for _ in range(2):
        result = run_helper(fixture)
        assert result.returncode == 0, result.stderr
        assert_links(fixture, source)


@pytest.mark.parametrize("broken", [False, True])
def test_managed_preferred_or_falls_back(fixture, broken):
    npm_source = npm_install(fixture)
    home = Path(fixture[2]["PI_HOME"])
    marker = home / "install/current-version"
    marker.parent.mkdir(parents=True)
    marker.write_text("v1\n")
    package = home / "install/releases/v1/node_modules/@earendil-works/pi-coding-agent"
    managed = modules(package)
    if broken:
        (managed / "agents.ts").unlink()
    result = run_helper(fixture)
    assert result.returncode == 0, result.stderr
    assert_links(fixture, npm_source if broken else managed)


def test_managed_without_executable(fixture):
    home = Path(fixture[2]["PI_HOME"])
    marker = home / "install/current-version"
    marker.parent.mkdir(parents=True)
    marker.write_text("v1\n")
    source = modules(home / "install/releases/v1/node_modules/@earendil-works/pi-coding-agent")
    result = run_helper(fixture)
    assert result.returncode == 0, result.stderr
    assert_links(fixture, source)


@pytest.mark.parametrize("incomplete", [False, True])
def test_failure_names_both_attempts_without_dangling_links(fixture, incomplete):
    if incomplete:
        source = npm_install(fixture)
        (source / "agents.ts").unlink()
    result = run_helper(fixture)
    assert result.returncode != 0
    assert f'{fixture[2]["PI_HOME"]}/install/current-version' in result.stderr
    assert "PATH" in result.stderr
    if incomplete:
        assert str(fixture[1] / "pi") in result.stderr
    assert not (Path(fixture[2]["PI_HOME"]) / "extensions").exists()


def test_wrapper_preserves_diagnostic_arguments_and_pi_status(fixture):
    base, utilities, env = fixture
    keyfile = base / "synthetic.env"
    keyfile.write_text("ANTHROPIC_API_KEY=synthetic-fixture-value\n")
    wrapper = (ROOT / "scripts/pi-haiku").read_text()
    assignment = 'keyfile="$HOME/.config/keys/anthropic.env"'
    assert wrapper.count(assignment) == 1
    wrapper = wrapper.replace(assignment, f'keyfile="{keyfile}"')
    copied = base / "pi-haiku"
    copied.write_text(wrapper)
    shutil.copy2(ROOT / "scripts/pi-subagent-link", base / "pi-subagent-link")
    argv = base / "argv.json"
    pi = utilities / "pi"
    pi.write_text(
        f'#!{shutil.which("python3")}\nimport json, sys\n'
        f'with open({str(argv)!r}, "w") as f: json.dump(sys.argv[1:], f)\n'
        'sys.exit(23)\n'
    )
    pi.chmod(0o755)
    result = subprocess.run(
        ["/bin/bash", str(copied), "--print", "hello world"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert "pi-subagent-link:" in result.stderr
    assert result.returncode == 23
    assert json.loads(argv.read_text()) == [
        "--provider", "anthropic", "--model", "claude-haiku-5-5",
        "--models", "anthropic/claude-haiku-5-5", "--print", "hello world",
    ]


def test_unpatchable_release_warns_keeps_a_link_and_fails(fixture):
    source = npm_install(fixture)
    (source / "index.ts").write_text("// upstream renamed the flag\n")
    result = run_helper(fixture)
    assert result.returncode != 0 and "keep no session file" in result.stderr
    assert (Path(fixture[2]["PI_HOME"]) / "extensions/subagent/index.ts").is_symlink()


def test_relinking_over_an_old_symlink_leaves_the_release_file_alone(fixture):
    source = npm_install(fixture)
    dest = Path(fixture[2]["PI_HOME"]) / "extensions/subagent"
    dest.mkdir(parents=True)
    (dest / "index.ts").symlink_to(source / "index.ts")  # what the previous version of the helper left
    original = (source / "index.ts").read_text()
    assert run_helper(fixture).returncode == 0
    assert (source / "index.ts").read_text() == original
