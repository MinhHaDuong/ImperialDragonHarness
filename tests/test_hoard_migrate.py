"""Behavioral coverage of the project-local, one-way memory migration."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

SPEC = importlib.util.spec_from_file_location(
    "hoard_migrate", Path(__file__).resolve().parents[1] / "scripts/hoard_migrate.py"
)
migrate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migrate
SPEC.loader.exec_module(migrate)


def tree(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def project(tmp_path):
    (tmp_path / "memory/dreams").mkdir(parents=True)
    (tmp_path / "memory/topics").mkdir()
    (tmp_path / "memory/journal").mkdir()
    (tmp_path / "memory/DREAM.md").write_text(
        "# DREAM — prompt\nPrompt revision: v8-r1 (2026-10-02)\n"
        "Reports: memory/dreams/\n")
    (tmp_path / "memory/MEMORY.md").write_text("[report](dreams/old.md)\n")
    (tmp_path / "memory/topics/a.md").write_text("[report](../dreams/old.md)\n")
    (tmp_path / "memory/dreams/old.md").write_bytes(
        b"Prompt revision: v8-r1\n- memory/DREAM.md blob abc123\n\xff")
    (tmp_path / "memory/journal/old.md").write_bytes(b"memory/dreams/old.md\n")
    (tmp_path / "memory/journal/private.age").write_bytes(b"\x00\xffciphertext")
    return tmp_path


def test_migrate_preserves_evidence_and_is_repeatable(project):
    before = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    after = tree(project)
    assert after["memory/hoards/old.md"] == before["memory/dreams/old.md"]
    for name in ("memory/journal/old.md", "memory/journal/private.age"):
        assert after[name] == before[name]
    assert after["memory/MEMORY.md"] == b"[report](hoards/old.md)\n"
    assert after["memory/topics/a.md"] == b"[report](../hoards/old.md)\n"
    assert b"Prompt revision: v8-r2" in after["memory/HOARD.md"]
    assert not (project / "memory/DREAM.md").exists()
    assert not (project / "memory/dreams").exists()
    migrate.apply_migration(migrate.plan_migration(project))
    assert tree(project) == after


@pytest.mark.integration
def test_dry_run_and_explicit_reference(project):
    (project / "AGENTS.md").write_text("Read memory/DREAM.md and memory/dreams/\n")
    before = tree(project)
    result = subprocess.run([sys.executable, str(SPEC.origin), str(project),
                             "--dry-run", "--reference", "AGENTS.md"],
                            capture_output=True, text=True, env=child_env())
    assert result.returncode == 0, result.stderr
    assert tree(project) == before
    migrate.apply_migration(migrate.plan_migration(project, ["AGENTS.md"]))
    assert (project / "AGENTS.md").read_text() == "Read memory/HOARD.md and memory/hoards/\n"


@pytest.mark.parametrize("conflict", ["HOARD.md", "hoards"])
def test_coexistence_refused(project, conflict):
    path = project / "memory" / conflict
    path.mkdir() if conflict == "hoards" else path.write_text("existing")
    before = tree(project)
    with pytest.raises(migrate.MigrationError):
        migrate.plan_migration(project)
    assert tree(project) == before


@pytest.mark.parametrize("dangling", [True, False])
def test_symlinks_refused_without_external_writes(project, tmp_path, dangling):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.write_bytes(b"sentinel")
    (project / "memory/topics/link").symlink_to(
        outside.parent / "missing" if dangling else outside)
    before = tree(project)
    with pytest.raises(migrate.MigrationError):
        migrate.plan_migration(project)
    assert outside.read_bytes() == b"sentinel"
    assert tree(project) == before


def test_unreadable_real_io_boundary(project, monkeypatch):
    before = tree(project)
    read = Path.read_bytes

    def denied(path):
        if path.name == "old.md":
            raise PermissionError("simulated inaccessible input")
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", denied)
    with pytest.raises(migrate.MigrationError, match="inaccessible"):
        migrate.plan_migration(project)
    monkeypatch.undo()
    assert tree(project) == before


def test_intervening_change_refused(project):
    plan = migrate.plan_migration(project)
    (project / "memory/MEMORY.md").write_text("new author edit")
    before = tree(project)
    with pytest.raises(migrate.MigrationError, match="changed"):
        migrate.apply_migration(plan)
    assert tree(project) == before


def test_ordinary_write_failure_rolls_back(project, monkeypatch):
    before = tree(project)
    plan = migrate.plan_migration(project)
    replace = migrate.os.replace
    calls = 0

    def fail_once(src, dst):
        nonlocal calls
        calls += 1
        if calls == 6:
            raise OSError("injected write failure")
        return replace(src, dst)

    monkeypatch.setattr(migrate.os, "replace", fail_once)
    with pytest.raises(migrate.MigrationError, match="injected write failure"):
        migrate.apply_migration(plan)
    assert tree(project) == before
    assert not list(project.glob(".hoard-migrate-*"))


@pytest.mark.parametrize("reference", ["memory/journal/old.md", "memory/dreams/old.md", "../outside", ".git/HEAD"])
def test_immutable_or_escaping_reference_refused(project, reference):
    before = tree(project)
    with pytest.raises(migrate.MigrationError):
        migrate.plan_migration(project, [reference])
    assert tree(project) == before


def test_fresh_new_format_is_untouched(tmp_path):
    (tmp_path / "memory/hoards").mkdir(parents=True)
    (tmp_path / "memory/HOARD.md").write_bytes(b"Prompt revision: v8-r2\n")
    (tmp_path / "memory/hoards/new.md").write_bytes(b"provenance\x00\xff")
    before = tree(tmp_path)
    plan = migrate.plan_migration(tmp_path)
    assert not plan.moves and not plan.edits
    migrate.apply_migration(plan)
    assert tree(tmp_path) == before


def test_failed_rollback_retains_recovery_files(project, monkeypatch):
    plan = migrate.plan_migration(project)
    replace = migrate.os.replace
    calls = 0

    def fail_install_and_rollback(src, dst):
        nonlocal calls
        calls += 1
        if calls >= 4:
            raise OSError("persistent I/O failure")
        return replace(src, dst)

    monkeypatch.setattr(migrate.os, "replace", fail_install_and_rollback)
    with pytest.raises(migrate.MigrationError, match="residual recovery files"):
        migrate.apply_migration(plan)
    recovery = list(project.glob(".hoard-migrate-*"))
    assert len(recovery) == 1
    assert (recovery[0] / "backup-0").read_bytes() == plan.snapshot["memory/MEMORY.md"]


def test_missing_prompt_is_an_error_before_any_moves(tmp_path):
    (tmp_path / "memory/dreams").mkdir(parents=True)
    (tmp_path / "memory/dreams/report.md").write_bytes(b"retained provenance")
    before = tree(tmp_path)
    with pytest.raises(migrate.MigrationError, match="prompt"):
        migrate.plan_migration(tmp_path)
    assert tree(tmp_path) == before


def test_active_reference_tokens_have_path_boundaries(project):
    old = (
        "Run /dream, then read skills/dream/SKILL.md.\n"
        "[prompt](DREAM.md) [nested](../DREAM.md)\n"
        "[report](dreams/old.md) [nested](../dreams/old.md)\n"
        "Keep /dreamlike /dream-extra skills/dream-extra/SKILL.md "
        "daydreams/story.md OTHERDREAM.md DREAM.md.backup dreams-extra/file.md\n"
    )
    expected = (
        "Run /hoard, then read skills/hoard/SKILL.md.\n"
        "[prompt](HOARD.md) [nested](../HOARD.md)\n"
        "[report](hoards/old.md) [nested](../hoards/old.md)\n"
        "Keep /dreamlike /dream-extra skills/dream-extra/SKILL.md "
        "daydreams/story.md OTHERDREAM.md DREAM.md.backup dreams-extra/file.md\n"
    )
    (project / "memory/MEMORY.md").write_text(old)
    evidence = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    assert (project / "memory/MEMORY.md").read_text() == expected
    assert (project / "memory/hoards/old.md").read_bytes() == evidence["memory/dreams/old.md"]
    assert (project / "memory/journal/old.md").read_bytes() == evidence["memory/journal/old.md"]
    migrated = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    assert tree(project) == migrated
