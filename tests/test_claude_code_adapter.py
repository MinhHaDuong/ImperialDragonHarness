"""The Claude Code adapter plugin (ticket 0887).

Three things can go silently wrong here, and each is a fail-open on the guard
layer, so each gets a test rather than a reading of the file:

1. the hooks creep back into ``settings.shared.json`` now that the plugin is
   the single hook source — every guard would then fire twice;
2. ``bin/idh-hook`` resolves the harness root wrongly when the plugin is
   reached through a symlink -- the case that actually happens, since
   ``${CLAUDE_PLUGIN_ROOT}`` holds the *discovery* path, measured on 2.1.266;
3. a broken launcher exits 0 (indistinguishable from a correct silent hook) or
   exits 2 (Claude Code's "deny", which would block every matching tool call).
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parent.parent
ADAPTER = REPO / "adapters" / "claude-code"
LAUNCHER = ADAPTER / "bin" / "idh-hook"
ACTIVATOR = REPO / "scripts" / "adapter-claude-code-activate.sh"
LOADING_PROBE = REPO / "scripts" / "probe-plugin-hook-loading.sh"


def test_manifest_names_the_plugin():
    manifest = json.loads((ADAPTER / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "claude-code"


def test_the_canonical_settings_carry_no_hooks():
    """The plugin is the single hook source (ticket 0887, activation).

    While both sources carried the hooks, a guard fired twice per call. The
    canonical settings dropped their ``hooks`` key at activation; a hook added
    back there would double-fire every guard, so the key is ratcheted out.
    """
    shared = json.loads((REPO / "settings.shared.json").read_text())
    assert "hooks" not in shared, (
        "settings.shared.json carries a hooks key — the adapter plugin is "
        "the single hook source; a second source double-fires every guard"
    )


def test_the_plugin_wires_the_three_hook_events():
    """The single hook source must actually carry the guard layer."""
    hooks = json.loads((ADAPTER / "hooks" / "hooks.json").read_text())["hooks"]
    assert {"SessionStart", "SessionEnd", "PreToolUse"} <= set(hooks)


def _commands():
    hooks = json.loads((ADAPTER / "hooks" / "hooks.json").read_text())["hooks"]
    return [
        hook["command"]
        for blocks in hooks.values()
        for block in blocks
        for hook in block.get("hooks", [])
        if "command" in hook
    ]



def test_every_launched_script_exists():
    missing = []
    for command in _commands():
        if "idh-hook" not in command:
            continue  # e.g. `rtk hook claude`, which names no harness path
        name = command.split("idh-hook")[1].strip('" ').split()[0]
        if not (REPO / "scripts" / name).is_file():
            missing.append(name)
    assert missing == [], f"hooks.json launches scripts that do not exist: {missing}"


# --- the optional rtk hook -------------------------------------------------


def _rtk_command() -> str:
    found = [c for c in _commands() if "rtk hook claude" in c]
    assert len(found) == 1
    return found[0]


@pytest.mark.integration
def test_rtk_hook_is_silent_and_harmless_when_rtk_is_absent(tmp_path):
    """rtk is an optional compactor: off PATH, the hook must not error."""
    (tmp_path / "sh").symlink_to("/bin/sh")  # the only thing on PATH: no rtk
    r = subprocess.run(
        ["/bin/sh", "-c", _rtk_command()],
        input="{}", capture_output=True, text=True,
        env={"PATH": str(tmp_path)},
    )
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")


@pytest.mark.integration
def test_rtk_hook_execs_rtk_with_its_args_and_stdin_when_present(tmp_path):
    """Positive control for the test above: a stub rtk really is reached."""
    stub = tmp_path / "rtk"
    stub.write_text('#!/bin/sh\necho "argv=$*"; cat\n')
    stub.chmod(0o755)
    payload = '{"tool_input":{"command":"ls"}}'
    r = subprocess.run(
        ["/bin/sh", "-c", _rtk_command()],
        input=payload, capture_output=True, text=True,
        env={"PATH": f"{tmp_path}:/usr/bin:/bin"},
    )
    assert r.returncode == 0
    assert r.stdout == f"argv=hook claude\n{payload}"


# --- the launcher ----------------------------------------------------------


def _tree(tmp_path: Path, marker: str) -> Path:
    """A throwaway harness: root/scripts/probe.sh plus the real launcher."""
    root = tmp_path / "harness"
    (root / "adapters" / "claude-code" / "bin").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "skills").mkdir()
    launcher = root / "adapters" / "claude-code" / "bin" / "idh-hook"
    launcher.write_bytes(LAUNCHER.read_bytes())
    launcher.chmod(0o755)
    probe = root / "scripts" / "probe.sh"
    probe.write_text(f"#!/bin/sh\necho {marker}\n")
    probe.chmod(0o755)
    return root


def _run(argv, root):
    return subprocess.run(
        argv, capture_output=True, text=True, cwd=root, env={**child_env(), "HOME": str(root)}
    )


@pytest.mark.parametrize("through_symlink", [False, True])
def test_launcher_resolves_the_harness_root(tmp_path, through_symlink):
    """The load-bearing invariant: the same launcher, reached either way.

    This is the positive control for the symlink design. If it ever regresses,
    the hooks point at a path that does not exist and every guard stops.
    """
    root = _tree(tmp_path, "PROBE-RAN")
    if through_symlink:
        (root / "skills" / "claude-code").symlink_to("../adapters/claude-code")
        entry = root / "skills" / "claude-code" / "bin" / "idh-hook"
    else:
        entry = root / "adapters" / "claude-code" / "bin" / "idh-hook"

    result = _run([str(entry), "probe.sh"], root)

    assert result.returncode == 0, result.stderr
    assert "PROBE-RAN" in result.stdout


def test_a_missing_target_is_loud_and_never_denies(tmp_path):
    """Exit 1: visible. Not 0 (silent no-op), not 2 (deny every tool call)."""
    root = _tree(tmp_path, "unused")

    result = _run(
        [str(root / "adapters" / "claude-code" / "bin" / "idh-hook"), "absent.sh"], root
    )

    assert result.returncode == 1, f"exit {result.returncode} — 2 would deny, 0 would hide"
    assert "absent.sh" in result.stderr


def test_a_python_target_needs_no_execute_bit(tmp_path):
    """A Python hook target may be mode 644 in the repo; the launcher must still run it."""
    root = _tree(tmp_path, "unused")
    script = root / "scripts" / "probe.py"
    script.write_text("print('PY-RAN')\n")
    script.chmod(0o644)

    result = _run(
        [str(root / "adapters" / "claude-code" / "bin" / "idh-hook"), "probe.py"], root
    )

    assert result.returncode == 0, result.stderr
    assert "PY-RAN" in result.stdout


# --- activation ------------------------------------------------------------


def _profile(root):
    return root.parent / "runtime-home/.claude"


def _activation_tree(tmp_path: Path) -> Path:
    root = tmp_path / "harness"
    (root / "adapters").mkdir(parents=True)
    shutil.copytree(ADAPTER, root / "adapters" / "claude-code")
    (_profile(root) / "skills").mkdir(parents=True)
    return root


def _run_activator(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(ACTIVATOR), *args],
        capture_output=True,
        text=True,
        cwd=root,
        env={**child_env(), "HARNESS_DIR": str(root), "HOME": str(root.parent / "runtime-home")},
    )


@pytest.mark.integration
def test_activation_refuses_live_hooks_and_allows_known_absence(tmp_path):
    root = _activation_tree(tmp_path)
    live = _profile(root) / "settings.json"
    link = _profile(root) / "skills" / "claude-code"

    live.write_text('{"hooks": {"PreToolUse": []}}')
    status = _run_activator(root, "--status")
    assert status.returncode == 0
    assert "carries a hooks block" in status.stdout

    present = _run_activator(root, "activate")
    assert present.returncode == 1
    assert "still carries a hooks block" in present.stderr
    assert not link.exists()

    live.write_text('{"permissions": {}}')
    status = _run_activator(root, "--status")
    assert status.returncode == 0
    assert "no hooks block" in status.stdout

    absent = _run_activator(root, "activate")
    assert absent.returncode == 0, absent.stderr
    assert link.is_symlink()
    assert link.resolve() == root / "adapters/claude-code"


@pytest.mark.integration
@pytest.mark.parametrize("contents", ["{ malformed", "[]", "42", "null", '"text"'])
def test_unknown_live_config_refuses_activation_and_status(tmp_path, contents):
    root = _activation_tree(tmp_path)
    (_profile(root) / "settings.json").write_text(contents)

    activation = _run_activator(root, "activate")
    assert activation.returncode == 1
    assert "cannot determine whether" in activation.stderr
    assert not (_profile(root) / "skills" / "claude-code").exists()

    status = _run_activator(root, "--status")
    assert status.returncode == 1
    assert "UNKNOWN" in status.stdout


@pytest.mark.integration
def test_unreadable_live_config_refuses_activation_and_status(tmp_path):
    """/proc/self/mem raises OSError on read even when pytest runs as root."""
    root = _activation_tree(tmp_path)
    (_profile(root) / "settings.json").symlink_to("/proc/self/mem")

    activation = _run_activator(root, "activate")
    assert activation.returncode == 1
    assert "cannot determine whether" in activation.stderr
    assert not (_profile(root) / "skills" / "claude-code").exists()

    status = _run_activator(root, "--status")
    assert status.returncode == 1
    assert "UNKNOWN" in status.stdout


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["directory", "dangling"])
def test_nonregular_live_config_is_unknown(tmp_path, kind):
    root = _activation_tree(tmp_path)
    live = _profile(root) / "settings.json"
    if kind == "directory":
        live.mkdir()
    else:
        live.symlink_to(root / "missing-settings.json")

    activation = _run_activator(root, "activate")
    assert activation.returncode == 1
    assert "cannot determine whether" in activation.stderr
    assert not (_profile(root) / "skills" / "claude-code").exists()

    status = _run_activator(root, "--status")
    assert status.returncode == 1
    assert "UNKNOWN" in status.stdout


@pytest.mark.integration
def test_revert_removes_the_link_and_warns_when_no_hooks_remain(tmp_path):
    """The canonical settings carry no hooks, so revert cannot wait for them.

    Reverting means the guards stop until a hooks block is restored; the
    switch must allow that rollback and say so loudly instead of refusing
    forever against a precondition the endgame removed.
    """
    root = _activation_tree(tmp_path)
    live = _profile(root) / "settings.json"
    link = _profile(root) / "skills" / "claude-code"
    live.write_text("{}")

    activated = _run_activator(root, "activate")
    assert activated.returncode == 0, activated.stderr

    reverted = _run_activator(root, "--revert")
    assert reverted.returncode == 0, reverted.stderr
    assert not link.exists()
    assert "no hooks" in (reverted.stdout + reverted.stderr).lower()
    assert "restore" in (reverted.stdout + reverted.stderr).lower()


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["foreign", "dangling", "directory"])
def test_adapter_commands_refuse_unmanaged_link_paths(tmp_path, kind):
    root = _activation_tree(tmp_path)
    link = _profile(root) / "skills" / "claude-code"
    if kind == "foreign":
        foreign = root / "foreign-plugin"
        foreign.mkdir()
        link.symlink_to(foreign)
    elif kind == "dangling":
        link.symlink_to(root / "missing-plugin")
    else:
        link.mkdir()

    for argument in ("--status", "activate", "--revert"):
        result = _run_activator(root, argument)
        assert result.returncode == 1
        assert "refusing" in (result.stdout + result.stderr)
        assert link.is_symlink() if kind != "directory" else link.is_dir()


REQUIRED_ADAPTER_COMPONENTS = [
    ".claude-plugin/plugin.json",
    "hooks/hooks.json",
    "bin/idh-hook",
]


def _remove_adapter_component(root: Path, component: str) -> None:
    target = root / "adapters" / "claude-code"
    if component == "target":
        shutil.rmtree(target)
    else:
        (target / component).unlink()


@pytest.mark.integration
@pytest.mark.parametrize("component", ["target", *REQUIRED_ADAPTER_COMPONENTS])
def test_activation_refuses_an_incomplete_adapter_payload(tmp_path, component):
    root = _activation_tree(tmp_path)
    (_profile(root) / "settings.json").write_text("{}")
    _remove_adapter_component(root, component)

    result = _run_activator(root, "activate")

    assert result.returncode == 1
    assert "adapter payload is incomplete" in result.stderr
    assert not (_profile(root) / "skills" / "claude-code").is_symlink()


@pytest.mark.integration
@pytest.mark.parametrize("component", ["target", *REQUIRED_ADAPTER_COMPONENTS])
def test_missing_adapter_payload_makes_an_existing_link_unknown(tmp_path, component):
    root = _activation_tree(tmp_path)
    link = _profile(root) / "skills" / "claude-code"
    (_profile(root) / "settings.json").write_text("{}")
    assert _run_activator(root, "activate").returncode == 0
    _remove_adapter_component(root, component)

    for argument in ("--status", "activate", "--revert"):
        result = _run_activator(root, argument)
        assert result.returncode == 1
        assert "refusing" in (result.stdout + result.stderr)
        assert link.is_symlink()


# --- loading probe ---------------------------------------------------------


def _probe_stub(tmp_path: Path) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    claude = bindir / "claude"
    claude.write_text(
        """#!/usr/bin/env bash
case "$HOME" in
  */a/home) : > "${HOME%/home}/marker" ;;
  */b/home) [ "${STUB_SKIP_B:-0}" = 1 ] || : > "${HOME%/home}/marker" ;;
  */c/home) [ "${STUB_FIRE_C:-0}" = 1 ] && : > "${HOME%/home}/marker" ;;
  */d/home) [ "${STUB_FIRE_D:-0}" = 1 ] && : > "${HOME%/home}/marker" ;;
esac
exit 0
"""
    )
    claude.chmod(0o755)
    return bindir


def _run_loading_probe(tmp_path: Path, **extra_env: str) -> subprocess.CompletedProcess:
    bindir = _probe_stub(tmp_path)
    return subprocess.run(
        [str(LOADING_PROBE)],
        capture_output=True,
        text=True,
        env={
            **child_env(),
            "PATH": f"{bindir}:{os.environ['PATH']}",
            "PROBE_TIMEOUT": "5",
            **extra_env,
        },
    )


@pytest.mark.integration
def test_loading_probe_accepts_its_expected_four_cases(tmp_path):
    result = _run_loading_probe(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "broken symlink" in result.stdout


@pytest.mark.integration
@pytest.mark.parametrize(
    ("extra_env", "failed_case"),
    [
        ({"STUB_SKIP_B": "1"}, "case B"),
        ({"STUB_FIRE_C": "1"}, "case C"),
        ({"STUB_FIRE_D": "1"}, "case D"),
    ],
)
def test_loading_probe_rejects_an_unexpected_result(tmp_path, extra_env, failed_case):
    result = _run_loading_probe(tmp_path, **extra_env)
    assert result.returncode == 1
    assert failed_case in result.stderr
