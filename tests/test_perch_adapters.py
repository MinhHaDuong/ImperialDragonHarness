"""Contract tests for the hand-ported perch pilot (ticket 0802)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).parent.parent
ADAPTER = REPO / "adapters" / "perch.py"
CANONICAL = REPO / "skills" / "perch" / "SKILL.md"
INVENTORY = REPO / "adapters" / "pilot-support.json"
SCHEMA = REPO / "adapters" / "pilot-support.schema.json"


def _fake_cli(tmp_path: Path, name: str, output: str) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    cli = bindir / name
    cli.write_text(f"#!/bin/sh\nprintf '%s\\n' '{output}'\n")
    cli.chmod(0o755)
    return cli


def _run(
    home: Path,
    *args: str,
    cli_name: str | None = None,
    cli_output: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    if cli_name and cli_output:
        cli = _fake_cli(home.parent, cli_name, cli_output)
        env[f"{cli_name.upper()}_BIN"] = str(cli)
    return subprocess.run(
        [sys.executable, str(ADAPTER), *args],
        env=env,
        capture_output=True,
        text=True,
    )


def test_agents_home_is_native_source_for_codex_and_pi(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    installed = home / ".agents" / "skills" / "perch"
    installed.parent.mkdir(parents=True)
    installed.symlink_to(CANONICAL.parent, target_is_directory=True)

    assert installed.is_symlink()
    assert installed.resolve() == CANONICAL.parent.resolve()
    assert (installed / "SKILL.md").read_text() == CANONICAL.read_text()


def test_clean_profile_gains_only_claude_projection(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    installed = home / ".claude" / "skills" / "perch"
    assert not installed.exists()  # red-state positive control

    result = _run(
        home,
        "install",
        "claude",
        cli_name="claude",
        cli_output="claude 2.1.250",
    )

    assert result.returncode == 0, result.stderr
    assert installed.is_symlink()
    assert installed.resolve() == CANONICAL.parent.resolve()
    assert (installed / "SKILL.md").read_text() == CANONICAL.read_text()


@pytest.mark.parametrize(
    ("harness", "minimum", "current"),
    [
        ("claude", "2.1.232", "2.1.250"),
        ("codex", "0.150.0", "0.150.1"),
        ("pi", "0.84.2", "0.84.3"),
    ],
)
def test_declared_minimum_and_current_versions_are_accepted(
    tmp_path, harness, minimum, current
):
    home = tmp_path / "home"
    home.mkdir()
    for version in (minimum, current):
        result = _run(home, "check-version", harness, "--version", version)
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("harness", ["claude", "codex", "pi"])
@pytest.mark.parametrize("version", ["unknown", "99.0.0"])
def test_unknown_versions_refuse_activation(tmp_path, harness, version):
    home = tmp_path / "home"
    home.mkdir()
    result = _run(home, "check-version", harness, "--version", version)
    assert result.returncode != 0
    assert "refusing support check" in result.stderr


def test_install_refuses_to_overwrite_an_unmanaged_entry(tmp_path):
    home = tmp_path / "home"
    target = home / ".claude" / "skills" / "perch"
    target.mkdir(parents=True)
    sentinel = target / "keep"
    sentinel.write_text("mine")

    result = _run(
        home,
        "install",
        "claude",
        cli_name="claude",
        cli_output="claude 2.1.250",
    )

    assert result.returncode != 0
    assert sentinel.read_text() == "mine"
    assert "refusing to replace" in result.stderr


def test_uninstall_removes_only_the_managed_claude_symlink(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert _run(
        home,
        "install",
        "claude",
        cli_name="claude",
        cli_output="claude 2.1.250",
    ).returncode == 0

    result = _run(home, "uninstall", "claude")

    assert result.returncode == 0, result.stderr
    assert not (home / ".claude" / "skills" / "perch").exists()
    assert CANONICAL.exists()


@pytest.mark.parametrize("harness", ["codex", "pi"])
def test_native_consumers_refuse_adapter_mutation(tmp_path, harness):
    home = tmp_path / "home"
    home.mkdir()

    result = _run(home, "uninstall", harness)

    assert result.returncode != 0
    assert "canonical skill is not removed" in result.stderr


def test_canonical_contract_has_stable_shape_and_is_read_only():
    text = CANONICAL.read_text()
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "perch"
    assert frontmatter["user-invocable"] is True
    for heading in ("## Done", "## Open", "## Drift", "**Stance:**"):
        assert heading in text
    assert "Read-only report" in text
    assert not any(token in text for token in ("Write(", "Edit(", "Bash("))


def test_inventory_covers_three_harnesses_with_stable_ids():
    inventory = json.loads(INVENTORY.read_text())
    assert inventory["slice"] == "perch"
    assert {entry["harness"] for entry in inventory["versions"]} == {
        "claude",
        "codex",
        "pi",
    }
    ids = [assertion["id"] for assertion in inventory["assertions"]]
    assert len(ids) == len(set(ids))
    assert any(
        assertion["evidence_kind"] == "manual-smoke"
        for assertion in inventory["assertions"]
    )


def test_inventory_validates_against_its_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text())
    inventory = json.loads(INVENTORY.read_text())
    jsonschema.validate(inventory, schema)
