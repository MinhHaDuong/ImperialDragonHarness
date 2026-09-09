"""The Claude Code adapter plugin (ticket 0887).

Three things can go silently wrong here, and each is a fail-open on the guard
layer, so each gets a test rather than a reading of the file:

1. the plugin's hooks drift from ``settings.shared.json`` while both exist;
2. ``bin/idh-hook`` resolves the harness root wrongly when the plugin is
   reached through a symlink -- the case that actually happens, since
   ``${CLAUDE_PLUGIN_ROOT}`` holds the *discovery* path, measured on 2.1.266;
3. a broken launcher exits 0 (indistinguishable from a correct silent hook) or
   exits 2 (Claude Code's "deny", which would block every matching tool call).
"""

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ADAPTER = REPO / "adapters" / "claude-code"
LAUNCHER = ADAPTER / "bin" / "idh-hook"
GENERATOR = REPO / "scripts" / "gen-claude-code-adapter-hooks.py"
ACTIVATOR = REPO / "scripts" / "adapter-claude-code-activate.sh"
LOADING_PROBE = REPO / "scripts" / "probe-plugin-hook-loading.sh"


def test_manifest_names_the_plugin():
    manifest = json.loads((ADAPTER / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "claude-code"


def test_hooks_are_in_sync_with_the_canonical_settings():
    """The generator's own derivation, re-run and compared.

    In-process on purpose: shelling out to `--check` would make this an
    integration test, and the drift guard belongs in the fast gate where a
    stale adapter is caught before it is pushed. The CLI path is exercised by
    `make check-adapter-hooks`.
    """
    spec = importlib.util.spec_from_file_location("gen_adapter_hooks", GENERATOR)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    shared = json.loads((REPO / "settings.shared.json").read_text())
    want = json.dumps(gen.derive(shared), indent=2, ensure_ascii=False) + "\n"

    assert (ADAPTER / "hooks" / "hooks.json").read_text() == want, (
        "adapters/claude-code/hooks/hooks.json is stale — run `make adapter-hooks`"
    )


def _commands():
    hooks = json.loads((ADAPTER / "hooks" / "hooks.json").read_text())["hooks"]
    return [
        hook["command"]
        for blocks in hooks.values()
        for block in blocks
        for hook in block.get("hooks", [])
        if "command" in hook
    ]


def test_no_command_names_the_home_path_the_adapter_exists_to_remove():
    assert [c for c in _commands() if "$HOME/.claude" in c] == []


def test_every_launched_script_exists():
    missing = []
    for command in _commands():
        if "idh-hook" not in command:
            continue  # e.g. `rtk hook claude`, which names no harness path
        name = command.split("idh-hook")[1].strip('" ').split()[0]
        if not (REPO / "scripts" / name).is_file():
            missing.append(name)
    assert missing == [], f"hooks.json launches scripts that do not exist: {missing}"


def test_the_hook_set_matches_the_canonical_one_entry_for_entry():
    """A hook must not be lost or gained in translation."""
    shared = json.loads((REPO / "settings.shared.json").read_text())["hooks"]
    derived = json.loads((ADAPTER / "hooks" / "hooks.json").read_text())["hooks"]
    assert sorted(shared) == sorted(derived)
    for event in shared:
        assert len(shared[event]) == len(derived[event])
        for a, b in zip(shared[event], derived[event]):
            assert a.get("matcher") == b.get("matcher")
            assert a.get("if") == b.get("if")
            assert len(a["hooks"]) == len(b["hooks"])


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
        argv, capture_output=True, text=True, cwd=root, env={**os.environ, "HOME": str(root)}
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
    """knowledge_hints.py is mode 644 in the repo; the launcher must still run it."""
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


def _activation_tree(tmp_path: Path) -> Path:
    root = tmp_path / "harness"
    (root / "adapters").mkdir(parents=True)
    shutil.copytree(ADAPTER, root / "adapters" / "claude-code")
    (root / "skills").mkdir()
    return root


def _run_activator(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(ACTIVATOR), *args],
        capture_output=True,
        text=True,
        cwd=root,
        env={**os.environ, "HARNESS_DIR": str(root)},
    )


def _write_canonical_settings(root: Path) -> dict:
    canonical = json.loads((REPO / "settings.shared.json").read_text())
    (root / "settings.shared.json").write_text(json.dumps(canonical))
    return canonical


@pytest.mark.integration
def test_activation_refuses_live_hooks_and_allows_known_absence(tmp_path):
    root = _activation_tree(tmp_path)
    live = root / "settings.json"
    link = root / "skills" / "claude-code"

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
    assert link.readlink() == Path("../adapters/claude-code")


@pytest.mark.integration
@pytest.mark.parametrize("contents", ["{ malformed", "[]", "42", "null", '"text"'])
def test_unknown_live_config_refuses_activation_and_status(tmp_path, contents):
    root = _activation_tree(tmp_path)
    (root / "settings.json").write_text(contents)

    activation = _run_activator(root, "activate")
    assert activation.returncode == 1
    assert "cannot determine whether" in activation.stderr
    assert not (root / "skills" / "claude-code").exists()

    status = _run_activator(root, "--status")
    assert status.returncode == 1
    assert "UNKNOWN" in status.stdout


@pytest.mark.integration
def test_unreadable_live_config_refuses_activation_and_status(tmp_path):
    """/proc/self/mem raises OSError on read even when pytest runs as root."""
    root = _activation_tree(tmp_path)
    (root / "settings.json").symlink_to("/proc/self/mem")

    activation = _run_activator(root, "activate")
    assert activation.returncode == 1
    assert "cannot determine whether" in activation.stderr
    assert not (root / "skills" / "claude-code").exists()

    status = _run_activator(root, "--status")
    assert status.returncode == 1
    assert "UNKNOWN" in status.stdout


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["directory", "dangling"])
def test_nonregular_live_config_is_unknown(tmp_path, kind):
    root = _activation_tree(tmp_path)
    live = root / "settings.json"
    if kind == "directory":
        live.mkdir()
    else:
        live.symlink_to(root / "missing-settings.json")

    activation = _run_activator(root, "activate")
    assert activation.returncode == 1
    assert "cannot determine whether" in activation.stderr
    assert not (root / "skills" / "claude-code").exists()

    status = _run_activator(root, "--status")
    assert status.returncode == 1
    assert "UNKNOWN" in status.stdout


@pytest.mark.integration
def test_revert_waits_for_live_hooks_to_be_restored(tmp_path):
    root = _activation_tree(tmp_path)
    canonical = _write_canonical_settings(root)
    live = root / "settings.json"
    link = root / "skills" / "claude-code"
    live.write_text("{}")

    activated = _run_activator(root, "activate")
    assert activated.returncode == 0, activated.stderr
    assert link.is_symlink()

    unsafe = _run_activator(root, "--revert")
    assert unsafe.returncode == 1
    assert "restore the canonical hooks" in unsafe.stderr
    assert link.is_symlink()

    canonical["hooks"]["SessionStart"].append(
        {"matcher": "", "hooks": [{"type": "command", "command": "custom-hook"}]}
    )
    live.write_text(json.dumps(canonical))
    reverted = _run_activator(root, "--revert")
    assert reverted.returncode == 0, reverted.stderr
    assert not link.exists()
    assert "live hooks block is restored" in reverted.stdout


@pytest.mark.integration
@pytest.mark.parametrize(
    "live_config",
    [
        {},
        {"hooks": {}},
        {"hooks": {"PreToolUse": []}},
        {"hooks": {"Custom": [{"matcher": "", "hooks": []}]}},
    ],
)
def test_revert_refuses_incomplete_live_hook_sets(tmp_path, live_config):
    root = _activation_tree(tmp_path)
    _write_canonical_settings(root)
    live = root / "settings.json"
    link = root / "skills" / "claude-code"
    live.write_text("{}")
    assert _run_activator(root, "activate").returncode == 0

    live.write_text(json.dumps(live_config))
    result = _run_activator(root, "--revert")

    assert result.returncode == 1
    assert "canonical hooks" in result.stderr
    assert link.is_symlink()


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["foreign", "dangling", "directory"])
def test_adapter_commands_refuse_unmanaged_link_paths(tmp_path, kind):
    root = _activation_tree(tmp_path)
    link = root / "skills" / "claude-code"
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
    (root / "settings.json").write_text("{}")
    _remove_adapter_component(root, component)

    result = _run_activator(root, "activate")

    assert result.returncode == 1
    assert "adapter payload is incomplete" in result.stderr
    assert not (root / "skills" / "claude-code").is_symlink()


@pytest.mark.integration
@pytest.mark.parametrize("component", ["target", *REQUIRED_ADAPTER_COMPONENTS])
def test_missing_adapter_payload_makes_an_existing_link_unknown(tmp_path, component):
    root = _activation_tree(tmp_path)
    link = root / "skills" / "claude-code"
    (root / "settings.json").write_text("{}")
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
            **os.environ,
            "PATH": f"{bindir}:{os.environ['PATH']}",
            "PROBE_TIMEOUT": "5",
            **extra_env,
        },
    )


@pytest.mark.integration
def test_loading_probe_accepts_its_expected_three_cases(tmp_path):
    result = _run_loading_probe(tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.integration
@pytest.mark.parametrize(
    ("extra_env", "failed_case"),
    [({"STUB_SKIP_B": "1"}, "case B"), ({"STUB_FIRE_C": "1"}, "case C")],
)
def test_loading_probe_rejects_unexpected_symlink_or_project_results(
    tmp_path, extra_env, failed_case
):
    result = _run_loading_probe(tmp_path, **extra_env)
    assert result.returncode == 1
    assert failed_case in result.stderr
