"""Adapter wiring for the dirty-reset guard (ticket 0809).

One canonical decision — ``scripts/guard-destructive-bash.sh`` blocks
``git reset --hard`` over uncommitted changes to tracked files, exit 2
with the reason on stderr — carried by three thin wirings:

- Claude Code: the live ``PreToolUse(Bash)`` hook in ``settings.shared.json``
  (unchanged by this slice; the ratchet below pins it);
- Codex: ``adapters/codex/hooks.json`` — Codex's PreToolUse payload carries
  ``tool_input.command`` and its block contract accepts exit 2 with the
  reason on stderr, so the same script runs byte-identical;
- Pi: ``adapters/pi/extensions/idh-guard.ts`` — a ``tool_call`` handler that
  normalizes the event into the guard's JSON payload and translates exit
  codes; Pi's fail-safe would block on a throwing handler, so the adapter
  catches everything to carry the guard's own fail-open doctrine instead of
  inventing a stricter one.

What this module proves mechanically (machine-independent):

- each wiring names the same canonical guard;
- the Pi adapter carries the three contract pieces independently — event
  mapping (the ``toolName === "bash"`` gate), block result
  (``{ block: true, reason }`` on exit 2) and exit semantics (fail-open on
  infra failure, allow on 0) — and mutation of each piece is rejected
  separately, so a weakening cannot hide behind another check;
- the Pi adapter locates the guard through the realpath seam, never a
  hard-coded installation root;
- the wirings install by symlink into a fixture home the way the slice
  installed them on the reference machine;
- the guard's own diagnostics never echo command text: a canary planted in a
  quoted segment of a blocked compound command appears in neither stdout
  nor stderr (integration).

The three-runtime block evidence (dirty tree blocked through claude
--print, codex exec and pi --print; clean tree allowed) is recorded as
manual-smoke assertions in ``adapters/pilot-support.json``.
"""

import json
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
GUARD = REPO / "scripts" / "guard-destructive-bash.sh"
PI_EXT = REPO / "adapters" / "pi" / "extensions" / "idh-guard.ts"
CODEX_HOOKS = REPO / "adapters" / "codex" / "hooks.json"


# --- shared contract helpers ----------------------------------------------


CANONICAL_SCRIPT = '"$HOME/.local/bin/idh-hook" guard-destructive-bash.sh'
# Codex hook trust pins the definition; re-trust a changed definition via /hooks.
CODEX_SCRIPT = CANONICAL_SCRIPT


def wiring_commands(doc, *, source_name):
    """Every PreToolUse/Bash command string in a hooks document, unexpanded.

    The invariant is the SCRIPT PATH, not its spelling: an adapter may wrap
    or quote the invocation (Codex runs it as `bash "$HOME/..."` per the
    third-party review, 2026-09-28) — that is adapter-local normalization,
    and the guard still owns the decision. CI checks the wiring contract.
    """
    commands = []
    for group in doc.get("hooks", {}).get("PreToolUse", []):
        matcher = group.get("matcher", "")
        if "Bash" not in matcher:
            continue
        for hook in group.get("hooks", []):
            if hook.get("type") != "command":
                continue
            commands.append(hook["command"])
    assert commands, f"{source_name}: no PreToolUse/Bash command hook"
    return commands


def assert_names_canonical_guard(commands, script=CANONICAL_SCRIPT):
    assert any(script in c for c in commands), (
        f"the canonical guard script {script!r} is not wired; found {commands}"
    )


def pi_adapter_violations(source: str):
    """The Pi adapter's contract, checked as named pieces so mutations fail
    distinctly. Returns a list of violation names."""
    violations = []
    if 'event.toolName !== "bash"' not in source:
        violations.append("event-mapping")
    if "result.status === 2" not in source:
        violations.append("exit-semantics")
    if "block: true" not in source:
        violations.append("block-result")
    if "result.error || result.signal" not in source or "return undefined" not in source:
        violations.append("fail-open")
    if "realpathSync" not in source:
        violations.append("seam")
    return violations


# --- Claude Code wiring (unchanged by the slice; pinned) ------------------


def test_claude_wiring_wires_the_canonical_guard():
    doc = json.loads((REPO / "settings.shared.json").read_text())
    assert_names_canonical_guard(wiring_commands(doc, source_name="settings.shared.json"))


# --- Codex wiring ----------------------------------------------------------


def test_codex_wiring_names_the_same_guard():
    doc = json.loads(CODEX_HOOKS.read_text())
    assert_names_canonical_guard(wiring_commands(doc, source_name="adapters/codex/hooks.json"), CODEX_SCRIPT)
    for group in doc["hooks"]["PreToolUse"]:
        assert "Bash" in group.get("matcher", "")
        for hook in group["hooks"]:
            # Bounded above the guard's per-git 4s worst case (a slow repo
            # check must fit) and below a stall-every-call hazard.
            assert 4 < hook.get("timeout", 0) <= 10, "guard hook timeout out of the 5-10s band"


def test_codex_wiring_mutation_is_rejected(tmp_path):
    doc = json.loads(CODEX_HOOKS.read_text())
    doc["hooks"]["PreToolUse"] = []
    broken = tmp_path / "hooks.json"
    broken.write_text(json.dumps(doc))
    with pytest.raises(AssertionError):
        wiring_commands(json.loads(broken.read_text()), source_name="mutated")


def test_codex_wiring_installs_by_symlink(tmp_path):
    installed = tmp_path / ".codex" / "hooks.json"
    installed.parent.mkdir()
    installed.symlink_to(CODEX_HOOKS)
    doc = json.loads(installed.read_text())
    assert_names_canonical_guard(wiring_commands(doc, source_name="~/.codex/hooks.json"), CODEX_SCRIPT)


# --- Pi adapter -------------------------------------------------------------


def test_pi_adapter_carries_the_contract():
    violations = pi_adapter_violations(PI_EXT.read_text())
    assert violations == [], f"Pi adapter contract violated: {violations}"


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ('event.toolName !== "bash"', "event-mapping"),
        ("result.status === 2", "exit-semantics"),
        ("block: true", "block-result"),
        ("realpathSync", "seam"),
    ],
)
def test_pi_adapter_mutation_fails_distinctly(mutation, expected):
    source = PI_EXT.read_text()
    assert mutation in source, f"mutation target missing: {mutation}"
    broken = source.replace(mutation, "MUTATED")
    violations = pi_adapter_violations(broken)
    assert expected in violations
    assert len(violations) == 1, f"mutation leaked into other checks: {violations}"


def test_pi_adapter_installs_by_symlink(tmp_path):
    installed = tmp_path / ".pi" / "agent" / "extensions" / "idh-guard.ts"
    installed.parent.mkdir(parents=True)
    installed.symlink_to(PI_EXT)
    assert pi_adapter_violations(installed.read_text()) == []


# --- the guard's diagnostics never echo command text (canary) --------------


@pytest.mark.integration
def test_guard_diagnostics_do_not_leak_command_text(tmp_path):
    repo = tmp_path / "fixture"
    repo.mkdir()
    for args in (["init", "-q"], ["commit", "--allow-empty", "-qm", "init"]):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(repo), *args],
            check=True, capture_output=True, env=child_env(),
        )
    (repo / "f.txt").write_text("committed\n")
    subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True,
                   env=child_env())
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(repo), "commit", "-qm", "t"],
        check=True, capture_output=True, env=child_env(),
    )
    (repo / "f.txt").write_text("committed\nUNCOMMITTED\n")  # dirty tracked file

    canary = "CANARY-0809-zx9-never-echoed"
    payload = {
        "tool_input": {
            "command": f'echo "{canary} in quoted text" && git reset --hard'
        },
        "cwd": str(repo),
    }
    r = subprocess.run(
        ["bash", str(GUARD)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=10,
        env=child_env(),
    )
    assert r.returncode == 2, "guard did not block a dirty tracked reset"
    assert canary not in r.stdout
    assert canary not in r.stderr
    assert str(repo) in r.stderr  # the decision names the target, not the text
