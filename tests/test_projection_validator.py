"""Launch-time projection validator and its shell wrappers (ticket 0983).

Every test runs in a disposable HOME against a disposable checkout that copies
the real validator, wrappers and manifest, so the host's own links (the
private skill overlay in the primary checkout, say) never leak in.
"""

import contextlib
import importlib.util
import io
import json
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
    ):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, root / rel)
    for skill in ("perch", "healthcheck"):
        (root / "skills" / skill).mkdir(parents=True)
    return root


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A healthy install: HOME whose projections all resolve into the checkout."""
    root = _checkout(tmp_path / "checkout")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    (home / ".idh").symlink_to(root, target_is_directory=True)
    (home / ".claude").symlink_to(root, target_is_directory=True)
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


def test_manifest_declares_the_pointer_and_one_guard_per_runtime():
    required = {
        (e["path"], rt)
        for e in MANIFEST["entries"]
        if e["required"]
        for rt in e["runtimes"]
    }
    for rt in RUNTIMES:
        assert ("~/.idh", rt) in required
    assert ("~/.claude", "claude") in required
    assert ("~/.codex/hooks.json", "codex") in required
    assert ("~/.pi/agent/extensions/idh-guard.ts", "pi") in required


def test_manifest_entries_are_well_formed():
    for e in MANIFEST["entries"]:
        assert set(e) == {"path", "target", "runtimes", "required", "why"}, e
        for spec in (e["path"], e["target"]):
            assert spec.startswith(("~/", "$IDH_ROOT")), spec
        assert set(e["runtimes"]) <= set(RUNTIMES)


# --- the validator -------------------------------------------------------


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_healthy_home_validates(world, runtime):
    r = validate(world, runtime)
    assert (r.returncode, r.stderr) == (0, "")


def test_success_records_the_checkout_for_later_repairs(world):
    assert validate(world, "claude").returncode == 0
    recorded = world["home"] / ".local" / "state" / "idh" / "last-good-root"
    assert recorded.read_text().strip() == str(world["root"].resolve())


def test_dangling_guard_link_names_culprit_and_repair(world):
    link = world["home"] / ".codex" / "hooks.json"
    link.unlink()
    link.symlink_to(world["tmp"] / "gone" / "hooks.json")
    r = validate(world, "codex")
    assert r.returncode == 1
    assert f"DANGLING: {link}" in r.stderr
    # The repair links through the pointer, as 0982 wired it, so it survives
    # the 0986 cutover instead of pinning today's resolved checkout.
    idh = world["home"] / ".idh"
    assert f"repair: ln -sfn {idh}/adapters/codex/hooks.json {link}" in r.stderr
    assert "IDH_SKIP_VALIDATE=1 codex" in r.stderr
    # Scoped per runtime: Claude Code does not read the Codex hook.
    assert validate(world, "claude").returncode == 0


def test_foreign_link_is_refused(world):
    other = world["tmp"] / "other.ts"
    other.write_text("// not the guard\n")
    link = world["home"] / ".pi" / "agent" / "extensions" / "idh-guard.ts"
    link.unlink()
    link.symlink_to(other)
    r = validate(world, "pi")
    assert r.returncode == 1
    assert f"FOREIGN: {link} resolves to {other}" in r.stderr


def test_missing_required_entry_is_refused(world):
    (world["home"] / ".pi" / "agent" / "extensions" / "idh-guard.ts").unlink()
    r = validate(world, "pi")
    assert r.returncode == 1
    assert "MISSING:" in r.stderr and "idh-guard.ts" in r.stderr


def test_absent_optional_entry_passes_but_a_dangling_one_does_not(world):
    link = world["home"] / ".agents" / "skills" / "perch"
    link.unlink()
    assert validate(world, "codex").returncode == 0
    link.symlink_to(world["tmp"] / "nowhere")
    r = validate(world, "codex")
    assert r.returncode == 1 and f"DANGLING: {link}" in r.stderr


def test_foreign_real_directory_is_never_overwritten_blind(world):
    (world["home"] / ".claude").unlink()
    (world["home"] / ".claude").mkdir()
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


def launch(world, runtime, init="shell-init.sh", **extra):
    script = f'source "{world["root"]}/scripts/{init}"\n{runtime} --version'
    return subprocess.run(
        ["bash", "--norc", "-c", script],
        env=_env(world, **extra),
        cwd=world["tmp"],
        capture_output=True,
        text=True,
    )


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
        ("claude", ".claude"),
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
    assert "IDH_SKIP_VALIDATE=1" in r.stderr
    log = (
        world["home"] / ".local" / "state" / "idh" / "validate-bypass.log"
    ).read_text()
    assert " codex bypass cwd=" in log
    # Any other value is not a bypass.
    r = launch(world, "codex", IDH_SKIP_VALIDATE="yes")
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout


@pytest.mark.integration
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_pointer_removed_after_sourcing_still_refuses(world, runtime):
    """The wrapper outlives ~/.idh in a running shell and must not fall through."""
    assert validate(world, runtime).returncode == 0  # records last-good-root
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
    assert f"repair: ln -sfn {world['root'].resolve()} {world['home']}/.idh" in r.stderr


@pytest.mark.integration
def test_bashrc_loader_sources_the_wrappers_when_reachable(world):
    r = launch(world, "pi", init="bashrc-loader.sh")
    assert r.returncode == 0 and "LAUNCHED pi" in r.stdout


@pytest.mark.integration
@pytest.mark.parametrize("runtime", RUNTIMES)
def test_bashrc_loader_refuses_when_the_harness_is_unreachable(world, runtime):
    assert validate(world, runtime).returncode == 0  # records last-good-root
    (world["home"] / ".idh").unlink()
    r = launch(world, runtime, init="bashrc-loader.sh")
    assert r.returncode != 0 and "LAUNCHED" not in r.stdout
    assert f"repair: ln -sfn {world['root'].resolve()} {world['home']}/.idh" in r.stderr
    assert f"IDH_SKIP_VALIDATE=1 {runtime}" in r.stderr

    r = launch(world, runtime, init="bashrc-loader.sh", IDH_SKIP_VALIDATE="1")
    assert r.returncode == 0 and f"LAUNCHED {runtime}" in r.stdout
    log = (
        world["home"] / ".local" / "state" / "idh" / "validate-bypass.log"
    ).read_text()
    assert "(harness unreachable)" in log
