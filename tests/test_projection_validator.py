"""Launch-time projection validator and its shell wrappers (ticket 0983).

Every test runs in a disposable HOME against a disposable checkout that copies
the real validator, wrappers and manifest, so the host's own links (the
private skill overlay in the primary checkout, say) never leak in.
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((REPO / "adapters" / "projections.json").read_text())
RUNTIMES = ("claude", "codex", "pi")


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_projections", REPO / "scripts" / "validate-projections.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _checkout(root: Path) -> Path:
    for rel in (
        "scripts/validate-projections.py",
        "scripts/shell-init.sh",
        "scripts/bashrc-loader.sh",
        "adapters/projections.json",
        "adapters/codex/hooks.json",
        "adapters/pi/extensions/idh-guard.ts",
        "adapters/claude-code/bin/idh-hook",
        "scripts/bash-env.sh",
        "AGENTS.md",
        "RTK.md",
        "tickets/AGENTS.md",
        "settings.shared.json",
        "bin/idh",
        "adapters/lifecycle.py",
    ):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, root / rel)
    (root / "rules").mkdir()
    (root / "rules/workflow.md").write_text("rules")
    (root / "agents").mkdir()
    (root / "agents/helper.md").write_text("agent")
    for skill in ("perch", "healthcheck"):
        (root / "skills" / skill).mkdir(parents=True)
    return root


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A healthy install: HOME whose projections all resolve into the checkout."""
    root = _checkout(tmp_path / "checkout")
    # A space in HOME: every printed repair must survive being pasted.
    home = tmp_path / "my home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    for entry in VALIDATOR.load_entries(root / "adapters/projections.json", None):
        if not entry["required"] and not VALIDATOR.expand(entry["target"], root).exists():
            continue
        link = VALIDATOR.expand(entry["path"], root)
        target = VALIDATOR.expand(entry["target"], root)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture")
            if entry["path"].startswith("~/.local/bin/"):
                target.chmod(0o755)
        if link == target:
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        if entry.get("registration"):
            link.write_text(json.dumps(VALIDATOR.merge_hooks({}, json.loads(target.read_text()))))
        elif not link.exists():
            link.symlink_to(target)
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    (fakebin / "systemctl").write_text("#!/bin/sh\nexit 0\n")
    (fakebin / "systemctl").chmod(0o755)
    for rt in RUNTIMES:
        exe = fakebin / rt
        exe.write_text(f'#!/bin/sh\necho "LAUNCHED {rt} $*"\n')
        exe.chmod(0o755)
    return {"root": root, "home": home, "fakebin": fakebin, "tmp": tmp_path}


def _env(world, **extra):
    env = {"HOME": str(world["home"]), "PATH": f"{world['fakebin']}:/usr/bin:/bin"}
    env.update(extra)
    return env


class Result:
    def __init__(self, returncode, stderr):
        self.returncode, self.stderr = returncode, stderr


def validate(world, runtime):
    """Run the validator in-process against the disposable checkout and HOME."""
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        try:
            rc = VALIDATOR.main([runtime, "--root", str(world["root"])])
        except SystemExit as exc:
            print(exc, file=err)
            rc = 2
    return Result(rc, err.getvalue())


# --- the manifest --------------------------------------------------------


def repair_command(stderr: str, n: int = 0) -> str:
    """The n-th printed repair, as the author would paste it."""
    lines = [
        ln.split("repair: ", 1)[1] for ln in stderr.splitlines() if "repair: " in ln
    ]
    return lines[n].split("   (", 1)[0]


def run_repair(world, stderr: str, n: int = 0):
    """Paste the printed repair into a plain shell; it must succeed as printed."""
    r = subprocess.run(
        ["bash", "--norc", "-c", repair_command(stderr, n)],
        env=_env(world),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (repair_command(stderr, n), r.stderr)


# --- the manifest --------------------------------------------------------


def test_manifest_declares_one_guard_per_runtime():
    required = {
        (e["path"], rt)
        for e in MANIFEST["entries"]
        if e["required"]
        for rt in e["runtimes"]
    }
    assert ("~/.claude/CLAUDE.md", "claude") in required
    assert ("~/.codex/hooks.json", "codex") in required
    assert ("~/.pi/agent/extensions/idh-guard.ts", "pi") in required


def test_manifest_entries_are_well_formed():
    for e in MANIFEST["entries"]:
        assert {"path", "target", "runtimes", "required", "why"} <= set(e), e
        assert set(e) <= {
            "path",
            "target",
            "runtimes",
            "required",
            "why",
            "installer",
            "children",
            "registration",
        }, e
        for spec in (e["path"], e["target"]):
            assert spec.startswith(("~/", "$IDH_ROOT")), spec
        assert set(e["runtimes"]) <= set(RUNTIMES)


# --- the validator -------------------------------------------------------


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_healthy_home_validates(world, runtime):
    r = validate(world, runtime)
    assert (r.returncode, r.stderr) == (0, "")


def test_validation_writes_no_state(world):
    """No state file: nothing a later launch could trip on (dropped last-good-root)."""
    assert validate(world, "claude").returncode == 0
    assert not (world["home"] / ".local/state").exists()


def test_unset_home_refuses_with_a_message_not_a_traceback(world, monkeypatch):
    monkeypatch.delenv("HOME")
    r = validate(world, "codex")
    assert r.returncode == 1
    assert "HOME is unset" in r.stderr and "IDH_SKIP_VALIDATE=1 codex" in r.stderr


@pytest.mark.integration
def test_dangling_guard_link_names_culprit_without_overwriting_it(world):
    link = world["home"] / ".local/bin/idh-hook"
    link.unlink()
    link.symlink_to(world["tmp"] / "gone" / "idh-hook")
    r = validate(world, "codex")
    assert r.returncode == 1
    assert f"DANGLING: {link}" in r.stderr
    assert "IDH_SKIP_VALIDATE=1 codex" in r.stderr
    assert "inspect " in repair_command(r.stderr)
    assert "ln -sf" not in repair_command(r.stderr)
    assert link.readlink() == world["tmp"] / "gone" / "idh-hook"
    # Scoped per runtime: Claude Code does not read the Codex hook.
    assert validate(world, "pi").returncode == 0


def test_foreign_link_is_refused(world):
    other = world["tmp"] / "other.ts"
    other.write_text("// not the guard\n")
    link = world["home"] / ".pi" / "agent" / "extensions" / "idh-guard.ts"
    link.unlink()
    link.symlink_to(other)
    r = validate(world, "pi")
    assert r.returncode == 1
    assert f"FOREIGN: {link} resolves to {other}" in r.stderr
    assert "inspect " in repair_command(r.stderr) and "ln -sf" not in r.stderr
    assert link.readlink() == other


def test_non_executable_installed_launcher_is_reported(world):
    target = world["root"] / "adapters/claude-code/bin/idh-hook"
    target.chmod(0o644)
    r = validate(world, "codex")
    assert r.returncode == 1 and "UNUSABLE:" in r.stderr
    assert "not executable" in r.stderr


@pytest.mark.integration
@pytest.mark.parametrize("runtime,rel", [("codex", ".codex"), ("pi", ".pi")])
def test_missing_guard_on_a_fresh_machine_gets_a_repair_that_works(world, runtime, rel):
    """Fresh registration creates missing parent directories without replacing links."""
    shutil.rmtree(world["home"] / rel)
    r = validate(world, runtime)
    assert r.returncode == 1 and "MISSING:" in r.stderr
    assert "/bin/idh" in r.stderr  # the managed alternative: idh install
    for n in range(r.stderr.count("    repair:")):
        run_repair(world, r.stderr, n)
    assert validate(world, runtime).returncode == 0


def test_absent_optional_entry_passes_but_a_dangling_one_does_not(world):
    link = world["home"] / ".agents" / "skills" / "perch"
    # A required canonical skill must remain registered.
    link.unlink()
    assert validate(world, "codex").returncode == 1
    link.symlink_to(world["tmp"] / "nowhere")
    r = validate(world, "codex")
    assert r.returncode == 1 and f"DANGLING: {link}" in r.stderr


def test_foreign_real_directory_is_never_overwritten_blind(world):
    (world["home"] / ".claude/CLAUDE.md").unlink()
    (world["home"] / ".claude/CLAUDE.md").mkdir()
    r = validate(world, "claude")
    assert r.returncode == 1
    assert "is a real directory" in r.stderr
    assert "inspect " in r.stderr and "mv " not in r.stderr


def test_unlisted_links_are_not_consulted(world):
    """The manifest is the whole contract: nothing is globbed."""
    (world["home"] / ".agents" / "skills" / "stray").symlink_to(
        world["tmp"] / "nowhere"
    )
    assert validate(world, "codex").returncode == 0


def test_unknown_runtime_is_a_usage_error(world):
    r = validate(world, "vibe")
    assert r.returncode != 0 and "unknown runtime" in r.stderr


# --- the shell wrappers --------------------------------------------------


def launch(world, runtime, init="shell-init.sh", pre="", cwd=None, env=None, **extra):
    script = f'{pre}\nsource "{world["root"]}/scripts/{init}"\n{runtime} --version'
    return subprocess.run(
        ["bash", "--norc", "-c", script],
        env=env if env is not None else _env(world, **extra),
        cwd=cwd or world["tmp"],
        capture_output=True,
        text=True,
    )


def bypass_log(world) -> str:
    return (
        world["home"] / ".local" / "state" / "idh" / "validate-bypass.log"
    ).read_text()


@pytest.mark.integration
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_negative_control_healthy_home_launches_unchanged(world, runtime):
    r = launch(world, runtime)
    assert r.returncode == 0, r.stderr
    assert f"LAUNCHED {runtime}" in r.stdout and "--version" in r.stdout
    assert r.stderr == ""


@pytest.mark.integration
@pytest.mark.parametrize(
    "runtime,rel",
    [
        ("claude", ".claude/CLAUDE.md"),
        ("codex", ".local/bin/idh-hook"),
        ("pi", ".pi/agent/extensions/idh-guard.ts"),
    ],
)
def test_positive_control_planted_broken_link_blocks_the_launch(world, runtime, rel):
    link = world["home"] / rel
    link.unlink()
    link.symlink_to(world["tmp"] / "planted-dangling")
    r = launch(world, runtime)
    assert r.returncode != 0
    assert "LAUNCHED" not in r.stdout
    assert f"DANGLING: {link}" in r.stderr and "repair:" in r.stderr


@pytest.mark.integration
def test_bypass_is_explicit_and_logged(world):
    (world["home"] / ".codex" / "hooks.json").unlink()
    r = launch(world, "codex", IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0 and "LAUNCHED codex" in r.stdout
    assert "IDH_SKIP_VALIDATE=1" in r.stderr and "(logged to " in r.stderr
    assert " codex bypass cwd=" in bypass_log(world)
    # Any other value is not a bypass.
    r = launch(world, "codex", IDH_SKIP_VALIDATE="yes")
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout


@pytest.mark.integration
@pytest.mark.parametrize("init", ["shell-init.sh", "bashrc-loader.sh"])
def test_an_unwritable_bypass_log_is_reported_not_claimed(world, init):
    (world["home"] / ".local/state").write_text("a file where the state dir should be\n")
    r = launch(world, "pi", init=init, IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0 and "LAUNCHED pi" in r.stdout
    assert "could not log to" in r.stderr and "(logged to" not in r.stderr


@pytest.mark.integration
@pytest.mark.parametrize("init", ["shell-init.sh", "bashrc-loader.sh"])
def test_a_newline_in_the_cwd_cannot_forge_a_log_line(world, init):
    evil = world["tmp"] / "x\n2026-01-01T00:00Z claude bypass cwd=forged"
    evil.mkdir()
    r = launch(world, "pi", init=init, cwd=evil, IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0
    lines = bypass_log(world).splitlines()
    assert len(lines) == 1 and "\\n2026-01-01" in lines[0]


@pytest.mark.integration
def test_unset_home_in_the_wrapper_refuses_with_a_message(world):
    env = {"PATH": f"{world['fakebin']}:/usr/bin:/bin"}
    r = launch(world, "codex", pre="unset HOME", env=env)
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout
    assert "HOME is unset" in r.stderr


@pytest.mark.integration
def test_bashrc_loader_sources_the_wrappers_when_reachable(world):
    r = launch(world, "pi", init="bashrc-loader.sh")
    assert r.returncode == 0 and "LAUNCHED pi" in r.stdout


@pytest.mark.integration
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_bashrc_loader_direct_source_works_under_errexit(world, runtime):
    # Directly sourced from the checkout, including under `set -e`.
    r = launch(world, runtime, init="bashrc-loader.sh", pre="set -e")
    assert r.returncode == 0 and f"LAUNCHED {runtime}" in r.stdout


@pytest.mark.integration
def test_a_same_name_alias_neither_breaks_the_loader_nor_is_lost(world):
    """An alias codex='codex --flag' defined before the loader (a real ~/.bash_aliases)
    once made `codex() {` a syntax error, leaving every runtime unwrapped."""
    script = (
        "shopt -s expand_aliases\n"
        "alias codex='codex --approve-for-me'\n"
        f'source "{world["root"]}/scripts/bashrc-loader.sh"\n'
        "type -t claude\n"
        "codex --version\n"
    )
    r = subprocess.run(
        ["bash", "--norc", "-c", script],
        env=_env(world, IDH_SKIP_VALIDATE="1"),
        cwd=world["tmp"],
        capture_output=True,
        text=True,
    )
    assert "syntax error" not in r.stderr, r.stderr
    assert r.stdout.startswith("function\n"), r.stdout
    assert "LAUNCHED codex --approve-for-me --version" in r.stdout


BROKEN_INIT = {
    "empty": "",
    "syntax error": 'function codex {\n  command codex "$@"\n\nif then fi\n',
    # Incomplete wrappers must not leave any runtime unprotected.
    "incomplete wrappers": 'claude() {\n  command claude --dangerously-skip-permissions "$@"\n}\n',
}


@pytest.mark.integration
@pytest.mark.parametrize("interactive", [False, True])
@pytest.mark.parametrize("case", [*BROKEN_INIT, "syntax error mid-file", "unreadable"])
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_loader_fails_closed_on_a_broken_shell_init(world, case, runtime, interactive):
    """Round-2 red team: `[ -f init ] && source init` launched codex bare (rc 0)."""
    init = world["root"] / "scripts" / "shell-init.sh"
    if case == "unreadable":
        init.chmod(0o000)
        if os.access(init, os.R_OK):
            pytest.skip("running as a user who can read mode-000 files")
    elif case == "syntax error mid-file":
        # The real file with one broken line in the middle: bash may carry on
        # past it and still reach the _IDH_WRAPPERS marker on the last line.
        text = init.read_text()
        cut = text.index("_idh_preflight() {")
        init.write_text(
            text[:cut]
            + "if then fi\n"
            + text[cut:].replace("_idh_preflight() {", "_idh_preflight() { (", 1)
        )
    else:
        init.write_text(BROKEN_INIT[case])
    flags = ["--norc", "-i"] if interactive else ["--norc"]
    script = f'source "{world["root"]}/scripts/bashrc-loader.sh"\n{runtime} --version'
    r = subprocess.run(
        ["bash", *flags, "-c", script],
        env=_env(world),
        cwd=world["tmp"],
        capture_output=True,
        text=True,
    )
    init.chmod(0o644)
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout, (r.stdout, r.stderr)
    assert f"refusing to launch {runtime}" in r.stderr
    assert "repair: " in r.stderr


@pytest.mark.integration
def test_missing_python3_refuses_with_a_repair(world):
    bare = world["tmp"] / "bare-bin"
    bare.mkdir()
    for tool in ("bash", "dirname", "basename", "readlink"):
        (bare / tool).symlink_to(shutil.which(tool))
    env = {"HOME": str(world["home"]), "PATH": f"{world['fakebin']}:{bare}"}
    r = launch(world, "codex", env=env)
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout
    assert "python3 is not on PATH" in r.stderr
    assert "repair: install python3" in r.stderr


@pytest.mark.parametrize(
    "corrupt",
    [
        "{not json",
        '{"entries": 3}',
        '{"entries": [{"path": "~/.local/bin/idh", "target": "$IDH_ROOT", "runtimes": ["codex"],'
        ' "why": "no required key"}]}',
    ],
)
def test_corrupt_manifest_is_a_one_line_refusal(world, corrupt):
    (world["root"] / "adapters" / "projections.json").write_text(corrupt)
    r = validate(world, "codex")
    assert r.returncode == 1
    assert len(r.stderr.strip().splitlines()) == 1, r.stderr
    assert "unusable" in r.stderr and "repair:" in r.stderr


@pytest.mark.integration
@pytest.mark.parametrize("init", ["shell-init.sh", "bashrc-loader.sh"])
def test_control_characters_in_the_cwd_never_reach_the_log_raw(world, init):
    odd = world["tmp"] / "a\rb\x1b[31mc\x07d"
    odd.mkdir()
    r = launch(world, "pi", init=init, cwd=odd, IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0
    log = bypass_log(world)
    assert not any(ch in log for ch in "\r\x1b\x07"), repr(log)
    assert len(log.splitlines()) == 1


@pytest.mark.integration
def test_an_unreadable_shell_init_gets_the_chmod_repair_not_ln(world):
    init = world["root"] / "scripts" / "shell-init.sh"
    init.chmod(0o000)
    try:
        if os.access(init, os.R_OK):
            pytest.skip("running as a user who can read mode-000 files")
        r = launch(world, "codex", init="bashrc-loader.sh")
    finally:
        init.chmod(0o644)
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout
    assert "exists but is unreadable" in r.stderr
    assert "repair: chmod u+r" in r.stderr and "ln -sfn" not in r.stderr


@pytest.mark.integration
@pytest.mark.parametrize(
    "bashrc,reminded",
    [
        ("", True),
        ((REPO / "scripts" / "bashrc-loader.sh").read_text(), False),
    ],
    ids=["none", "current-loader"],
)
def test_session_start_reminds_only_when_the_loader_is_absent(
    tmp_path, bashrc, reminded
):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").write_text(bashrc)
    r = subprocess.run(
        ["bash", str(REPO / "scripts" / "on-start.sh")],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="{}",
    )
    assert ("harness loader is not in your shell config" in r.stdout) is reminded, (
        r.stdout
    )
