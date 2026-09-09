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
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ADAPTER = REPO / "adapters" / "claude-code"
LAUNCHER = ADAPTER / "bin" / "idh-hook"
GENERATOR = REPO / "scripts" / "gen-claude-code-adapter-hooks.py"


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
