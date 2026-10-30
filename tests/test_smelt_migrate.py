"""Behavioral coverage of the project-local, one-way memory migration."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

SPEC = importlib.util.spec_from_file_location(
    "smelt_migrate", Path(__file__).resolve().parents[1] / "scripts/smelt_migrate.py"
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
    assert after["memory/smelts/old.md"] == before["memory/dreams/old.md"]
    for name in ("memory/journal/old.md", "memory/journal/private.age"):
        assert after[name] == before[name]
    assert after["memory/MEMORY.md"] == b"[report](smelts/old.md)\n"
    assert after["memory/topics/a.md"] == b"[report](../smelts/old.md)\n"
    assert b"Prompt revision: v8-r2" in after["memory/SMELT.md"]
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
    assert (project / "AGENTS.md").read_text() == "Read memory/SMELT.md and memory/smelts/\n"


@pytest.mark.parametrize("conflict", ["SMELT.md", "smelts"])
def test_coexistence_refused(project, conflict):
    path = project / "memory" / conflict
    path.mkdir() if conflict == "smelts" else path.write_text("existing")
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
    assert not list(project.glob(".smelt-migrate-*"))


@pytest.mark.parametrize("reference", ["memory/journal/old.md", "memory/dreams/old.md", "../outside", ".git/HEAD"])
def test_immutable_or_escaping_reference_refused(project, reference):
    before = tree(project)
    with pytest.raises(migrate.MigrationError):
        migrate.plan_migration(project, [reference])
    assert tree(project) == before


def test_fresh_new_format_is_untouched(tmp_path):
    (tmp_path / "memory/smelts").mkdir(parents=True)
    (tmp_path / "memory/SMELT.md").write_bytes(b"Prompt revision: v8-r2\n")
    (tmp_path / "memory/smelts/new.md").write_bytes(b"provenance\x00\xff")
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
    recovery = list(project.glob(".smelt-migrate-*"))
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
        "Run /smelt, then read skills/smelt/SKILL.md.\n"
        "[prompt](SMELT.md) [nested](../DREAM.md)\n"
        "[report](smelts/old.md) [nested](../dreams/old.md)\n"
        "Keep /dreamlike /dream-extra skills/dream-extra/SKILL.md "
        "daydreams/story.md OTHERDREAM.md DREAM.md.backup dreams-extra/file.md\n"
    )
    (project / "memory/MEMORY.md").write_text(old)
    evidence = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    assert (project / "memory/MEMORY.md").read_text() == expected
    assert (project / "memory/smelts/old.md").read_bytes() == evidence["memory/dreams/old.md"]
    assert (project / "memory/journal/old.md").read_bytes() == evidence["memory/journal/old.md"]
    migrated = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    assert tree(project) == migrated


def test_unrelated_paths_and_urls_are_preserved(project):
    (project / "docs/dreams").mkdir(parents=True)
    (project / "docs/dreams/retained.md").write_text("retained")
    (project / "docs/DREAM.md").write_text("unrelated prompt")
    (project / "docs/memory/dreams").mkdir(parents=True)
    (project / "docs/memory/dreams/retained.md").write_text("nested unrelated")
    (project / "docs/active.md").write_text(
        "[unrelated](memory/dreams/retained.md) [moved](../memory/dreams/old.md)\n")
    references = (
        "[other](../docs/dreams/retained.md) [prompt](../docs/DREAM.md)\n"
        "[remote](https://example.org/memory/dreams/retained.md)\n"
        "[actual](dreams/old.md)\n"
    )
    (project / "memory/MEMORY.md").write_text(references)
    (project / "memory/topics/a.md").write_text(
        "[prompt](../DREAM.md) [report](../dreams/old.md)\n")
    before = tree(project)
    migrate.apply_migration(migrate.plan_migration(project, ["docs/active.md"]))
    assert (project / "docs/active.md").read_text() == (
        "[unrelated](memory/dreams/retained.md) [moved](../memory/smelts/old.md)\n")
    assert (project / "memory/MEMORY.md").read_text() == references.replace(
        "(dreams/old.md)", "(smelts/old.md)")
    assert (project / "memory/topics/a.md").read_text() == (
        "[prompt](../SMELT.md) [report](../smelts/old.md)\n")
    for name in ("docs/DREAM.md", "docs/dreams/retained.md"):
        assert (project / name).read_bytes() == before[name]


def test_retired_helpers_preserve_their_historical_identity(project):
    # A real topic naming the retired helpers, as it stood before the fifth smelt merged it.
    actual_topic = subprocess.run(
        ["git", "-C", str(Path(SPEC.origin).parents[1]), "show",
         "0cad157b8e42dca534139a80f7a7933c8be04975:memory/topics/memory-v8-acceptance-trial.md"],
        check=True, capture_output=True, env=child_env(),
    ).stdout
    (project / "memory/topics/history.md").write_bytes(actual_topic)
    (project / "AGENTS.md").write_text(
        "Use /dream and skills/dream/SKILL.md. Retired: "
        "skills/dream/read-index.py skills/dream/commit.py skills/dream/provenance.py\n")
    migrate.apply_migration(migrate.plan_migration(project, ["AGENTS.md"]))
    assert (project / "memory/topics/history.md").read_bytes() == actual_topic
    assert (project / "AGENTS.md").read_text() == (
        "Use /smelt and skills/smelt/SKILL.md. Retired: "
        "skills/dream/read-index.py skills/dream/commit.py skills/dream/provenance.py\n")


def test_stage_directory_failure_is_reported_without_writes(project, monkeypatch):
    before = tree(project)
    plan = migrate.plan_migration(project)

    def denied(**kwargs):
        raise OSError("stage denied")

    monkeypatch.setattr(migrate.tempfile, "mkdtemp", denied)
    with pytest.raises(migrate.MigrationError, match="stage denied"):
        migrate.apply_migration(plan)
    assert tree(project) == before
    assert not list(project.glob(".smelt-migrate-*"))


def test_relative_skill_entrypoints_and_directory_targets(project):
    (project / "skills/dream").mkdir(parents=True)
    (project / "skills/dream/SKILL.md").write_text("canonical skill")
    old = (
        "[skill](../skills/dream/SKILL.md) [directory](../skills/dream/)\n"
        "Root /skills/dream/ and skills/dream/ and skills/dream.\n"
        "Retired ../skills/dream/read-index.py skills/dream/commit.py\n"
        "Near skills/dreamish ../skills/dreamish/SKILL.md\n"
        "[other](../docs/dreams/retained.md)\n"
        "[remote](https://example.org/skills/dream/SKILL.md)\n"
        "[remote dir](https://example.org/skills/dream/)\n"
    )
    expected = (
        "[skill](../skills/smelt/SKILL.md) [directory](../skills/smelt/)\n"
        "Root /skills/smelt/ and skills/smelt/ and skills/smelt.\n"
        "Retired ../skills/dream/read-index.py skills/dream/commit.py\n"
        "Near skills/dreamish ../skills/dreamish/SKILL.md\n"
        "[other](../docs/dreams/retained.md)\n"
        "[remote](https://example.org/skills/dream/SKILL.md)\n"
        "[remote dir](https://example.org/skills/dream/)\n"
    )
    (project / "memory/MEMORY.md").write_text(old)
    migrate.apply_migration(migrate.plan_migration(project))
    assert (project / "memory/MEMORY.md").read_text() == expected
    assert (project / "skills/dream/SKILL.md").read_text() == "canonical skill"


@pytest.mark.parametrize("swap_ancestor", [False, True])
def test_replaced_project_root_or_ancestor_refuses_outside_writes(project, swap_ancestor):
    selected = project / "scope/selected"
    selected.mkdir(parents=True)
    migrate.shutil.copytree(project / "memory", selected / "memory")
    plan = migrate.plan_migration(selected)
    source = selected.parent if swap_ancestor else selected
    outside = project / "outside"
    original = project / "original"
    migrate.shutil.copytree(source, outside)
    source.rename(original)
    source.symlink_to(outside, target_is_directory=True)
    original_before = tree(original)
    outside_before = tree(outside)
    with pytest.raises(migrate.MigrationError, match="symlink"):
        migrate.apply_migration(plan)
    assert tree(original) == original_before
    assert tree(outside) == outside_before
    assert not list(outside.rglob(".smelt-migrate-*"))
    assert not list(original.rglob(".smelt-migrate-*"))


@pytest.mark.parametrize("new_prompt", [True, False])
def test_mixed_prompt_and_report_layout_is_refused_without_writes(project, new_prompt):
    if new_prompt:
        (project / "memory/DREAM.md").rename(project / "memory/SMELT.md")
    else:
        (project / "memory/dreams").rename(project / "memory/smelts")
    before = tree(project)
    with pytest.raises(migrate.MigrationError, match="Mixed old/new"):
        migrate.plan_migration(project)
    assert tree(project) == before
    assert not list(project.glob(".smelt-migrate-*"))


def test_old_prompt_without_reports_can_migrate(project):
    migrate.shutil.rmtree(project / "memory/dreams")
    before = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    assert b"memory/smelts/" in (project / "memory/SMELT.md").read_bytes()
    assert not (project / "memory/DREAM.md").exists()
    assert not (project / "memory/smelts").exists()
    for name in ("memory/journal/old.md", "memory/journal/private.age"):
        assert (project / name).read_bytes() == before[name]
    after = tree(project)
    migrate.apply_migration(migrate.plan_migration(project))
    assert tree(project) == after


def test_legacy_hoard_layout_migrates_to_smelt(tmp_path):
    (tmp_path / "memory/hoards").mkdir(parents=True)
    (tmp_path / "memory/HOARD.md").write_text(
        "# HOARD — prompt\nPrompt revision: v8-r2 (2026-10-15)\nReports: memory/hoards/\n")
    (tmp_path / "memory/hoards/old.md").write_bytes(b"report memory/HOARD.md\xff")
    (tmp_path / "memory/MEMORY.md").write_text("[report](hoards/old.md) /hoard\n")
    migrate.apply_migration(migrate.plan_migration(tmp_path))
    assert (tmp_path / "memory/hoards").exists() is False
    assert not (tmp_path / "memory/HOARD.md").exists()
    assert (tmp_path / "memory/smelts/old.md").read_bytes() == b"report memory/HOARD.md\xff"
    prompt = (tmp_path / "memory/SMELT.md").read_text()
    assert prompt.startswith("# SMELT") and "Prompt revision: v8-r3" in prompt
    assert "memory/smelts/" in prompt
    assert (tmp_path / "memory/MEMORY.md").read_text() == "[report](smelts/old.md) /smelt\n"
