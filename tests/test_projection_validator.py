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
CLAUDE_LINKS = (
    "CLAUDE.md",
    "RTK.md",
    "rules",
    "agents",
    "commands",
    "tickets",
)


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
    ):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, root / rel)
    for skill in ("perch", "healthcheck"):
        (root / "skills" / skill).mkdir(parents=True)
    for name in CLAUDE_LINKS:  # the per-entry projections into ~/.claude (0986)
        if name.endswith(".md"):
            (root / name).write_text("")
        else:
            (root / name).mkdir(exist_ok=True)
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
    (home / ".idh").symlink_to(root, target_is_directory=True)
    # Post-cutover layout (0986): ~/.claude is Claude Code's own real root,
    # holding one link per harness entry. Memory links are optional entries.
    (home / ".claude").mkdir()
    for name in CLAUDE_LINKS:
        (home / ".claude" / name).symlink_to(home / ".idh" / name)
    (home / ".claude" / "skills").mkdir()
    for skill in ("perch", "healthcheck"):
        (home / ".claude" / "skills" / skill).symlink_to(
            home / ".idh" / "skills" / skill
        )
    for rel, target in (
        (".codex/hooks.json", "adapters/codex/hooks.json"),
        (".pi/agent/extensions/idh-guard.ts", "adapters/pi/extensions/idh-guard.ts"),
        (".agents/skills/perch", "skills/perch"),
    ):
        link = home / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(home / ".idh" / target)
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
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
            rc = VALIDATOR.main([runtime, "--root", str(world["home"] / ".idh")])
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


def test_manifest_declares_the_pointer_and_one_guard_per_runtime():
    required = {
        (e["path"], rt)
        for e in MANIFEST["entries"]
        if e["required"]
        for rt in e["runtimes"]
    }
    for rt in RUNTIMES:
        assert ("~/.idh", rt) in required
    # Post-cutover (0986): ~/.claude is Claude Code's own root, not the checkout;
    # the harness reaches it through one link per entry.
    assert ("~/.claude", "claude") not in required
    for n in CLAUDE_LINKS:
        assert (f"~/.claude/{n}", "claude") in required
    assert ("~/.claude/skills", "claude") not in required
    skill_entries = VALIDATOR.load_entries(REPO / "adapters" / "projections.json", "claude")
    assert any(e["path"] == "~/.claude/skills/perch" for e in skill_entries)
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
    assert not (world["home"] / ".local").exists()


def test_unset_home_refuses_with_a_message_not_a_traceback(world, monkeypatch):
    monkeypatch.delenv("HOME")
    r = validate(world, "codex")
    assert r.returncode == 1
    assert "HOME is unset" in r.stderr and "IDH_SKIP_VALIDATE=1 codex" in r.stderr


@pytest.mark.integration
def test_dangling_guard_link_names_culprit_and_a_working_repair(world):
    link = world["home"] / ".codex" / "hooks.json"
    link.unlink()
    link.symlink_to(world["tmp"] / "gone" / "hooks.json")
    r = validate(world, "codex")
    assert r.returncode == 1
    assert f"DANGLING: {link}" in r.stderr
    assert "IDH_SKIP_VALIDATE=1 codex" in r.stderr
    # The repair links through the pointer, as 0982 wired it, so it survives
    # the 0986 cutover instead of pinning today's resolved checkout.
    assert f"{world['home'] / '.idh'}/adapters/codex/hooks.json" in repair_command(
        r.stderr
    )
    # Scoped per runtime: Claude Code does not read the Codex hook.
    assert validate(world, "claude").returncode == 0
    run_repair(world, r.stderr)
    assert validate(world, "codex").returncode == 0


def test_foreign_link_is_refused(world):
    other = world["tmp"] / "other.ts"
    other.write_text("// not the guard\n")
    link = world["home"] / ".pi" / "agent" / "extensions" / "idh-guard.ts"
    link.unlink()
    link.symlink_to(other)
    r = validate(world, "pi")
    assert r.returncode == 1
    assert f"FOREIGN: {link} resolves to {other}" in r.stderr


@pytest.mark.integration
@pytest.mark.parametrize("runtime,rel", [("codex", ".codex"), ("pi", ".pi")])
def test_missing_guard_on_a_fresh_machine_gets_a_repair_that_works(world, runtime, rel):
    """No ~/.codex at all: a bare `ln -sfn` would fail, so the repair creates the parent."""
    shutil.rmtree(world["home"] / rel)
    r = validate(world, runtime)
    assert r.returncode == 1 and "MISSING:" in r.stderr
    assert "/bin/idh" in r.stderr  # the managed alternative: idh install
    run_repair(world, r.stderr)
    assert validate(world, runtime).returncode == 0


def test_absent_optional_entry_passes_but_a_dangling_one_does_not(world):
    link = world["home"] / ".agents" / "skills" / "perch"
    link.unlink()
    assert validate(world, "codex").returncode == 0
    link.symlink_to(world["tmp"] / "nowhere")
    r = validate(world, "codex")
    assert r.returncode == 1 and f"DANGLING: {link}" in r.stderr


def test_foreign_real_directory_is_never_overwritten_blind(world):
    (world["home"] / ".claude" / "rules").unlink()
    (world["home"] / ".claude" / "rules").mkdir()
    r = validate(world, "claude")
    assert r.returncode == 1
    assert "is a real directory" in r.stderr
    assert "mv " in r.stderr and ".pre-idh" in r.stderr


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
        ("claude", ".claude/rules"),
        ("codex", ".codex/hooks.json"),
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
    if init == "bashrc-loader.sh":
        (world["home"] / ".idh").unlink()
    (world["home"] / ".local").write_text("a file where the state dir should be\n")
    r = launch(world, "pi", init=init, IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0 and "LAUNCHED pi" in r.stdout
    assert "could not log to" in r.stderr and "(logged to" not in r.stderr


@pytest.mark.integration
@pytest.mark.parametrize("init", ["shell-init.sh", "bashrc-loader.sh"])
def test_a_newline_in_the_cwd_cannot_forge_a_log_line(world, init):
    if init == "bashrc-loader.sh":
        (world["home"] / ".idh").unlink()
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
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_pointer_removed_after_sourcing_still_refuses(world, runtime):
    """The wrapper outlives ~/.idh in a running shell and must not fall through."""
    script = (
        f'source "{world["home"]}/.idh/scripts/shell-init.sh"\n'
        f'rm "{world["home"]}/.idh"\n{runtime} --version'
    )
    r = subprocess.run(
        ["bash", "--norc", "-c", script],
        env=_env(world),
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout
    assert "restore the checkout at" in r.stderr
    assert str(world["home"] / ".idh") in r.stderr


@pytest.mark.integration
def test_bashrc_loader_sources_the_wrappers_when_reachable(world):
    r = launch(world, "pi", init="bashrc-loader.sh")
    assert r.returncode == 0 and "LAUNCHED pi" in r.stdout


@pytest.mark.integration
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_bashrc_loader_refuses_when_the_harness_is_unreachable(world, runtime):
    (world["home"] / ".idh").unlink()
    # Under `set -e` too: a refusal must print its message, never exit silently.
    r = launch(world, runtime, init="bashrc-loader.sh", pre="set -e")
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout
    assert "is unreachable" in r.stderr
    assert f"IDH_SKIP_VALIDATE=1 {runtime}" in r.stderr
    assert "restore the checkout at" in r.stderr
    assert str(world["home"] / ".idh") in r.stderr

    r = launch(world, runtime, init="bashrc-loader.sh", IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0 and f"LAUNCHED {runtime}" in r.stdout
    assert "(harness not loaded)" in bypass_log(world)


@pytest.mark.integration
@pytest.mark.parametrize("unreachable", [False, True])
def test_a_same_name_alias_neither_breaks_the_loader_nor_is_lost(world, unreachable):
    """An alias codex='codex --flag' defined before the loader (a real ~/.bash_aliases)
    once made `codex() {` a syntax error, leaving every runtime unwrapped."""
    if unreachable:
        (world["home"] / ".idh").unlink()
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
    # A pre-0983 copy: it defines claude without any check, and nothing else.
    "old copy": 'claude() {\n  command claude --dangerously-skip-permissions "$@"\n}\n',
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
    for tool in ("bash", "dirname", "basename"):
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
        '{"entries": [{"path": "~/.idh", "target": "$IDH_ROOT", "runtimes": ["codex"],'
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
    if init == "bashrc-loader.sh":
        (world["home"] / ".idh").unlink()
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
        (
            '[ -f "$HOME/.idh/scripts/shell-init.sh" ] && source "$HOME/.idh/scripts/shell-init.sh"\n',
            True,
        ),
        ((REPO / "scripts" / "bashrc-loader.sh").read_text(), False),
        (
            "_idh_unreachable() { :; }  # the round-1 block, until the post-merge refresh\n",
            False,
        ),
    ],
    ids=["none", "bare-source-line", "current-loader", "round-1-loader"],
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
