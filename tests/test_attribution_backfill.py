"""Real Git/CLI controls for conservative post-merge attribution backfill."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env
from run_checked import run_checked

CLI = Path(__file__).resolve().parents[1] / "scripts" / "attribution_backfill.py"
pytestmark = pytest.mark.integration
SPEC = importlib.util.spec_from_file_location("attribution_record", CLI.with_name("attribution_record.py"))
READER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READER)
parse_record = READER.parse_record


def git(repo, *args):
    return run_checked(["git", "-C", str(repo), *args]).stdout.strip()


def commit(repo, name):
    git(repo, "add", ".")
    git(repo, "commit", "-qm", name)
    return git(repo, "rev-parse", "HEAD")


def record(pr=12, anchor="source.py:2"):
    return ("kind: review-attribution\n"
            f"pr: {pr} · merged 2026-10-03 · project: fixture\n"
            "writer: runtime=fixture · model=example/writer-v1 · effort=standard\n"
            "reviewer: seat=first · runtime=fixture · model=example/reviewer-v1 · status: ran\n"
            f"  finding: verifiable · {anchor} · adopted: no\n"
            "reviewer: seat=second · runtime=fixture · model=example/reviewer-v1 · status: ran\n"
            f"  finding: consider · {anchor} · adopted: no\n"
            "Context: opaque reviewed revision claims are not coordinate evidence.\n")


@pytest.fixture
def project(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / "source.py").write_text("first\nbroken\nthird\n")
    reviewed = commit(tmp_path, "reviewed revision")
    journal = tmp_path / "memory/journal/2026"
    journal.mkdir(parents=True)
    entry = journal / "2026-10-03-review-attribution-pr12.md"
    entry.write_text(record())
    commit(tmp_path, "durable review record")
    (tmp_path / "source.py").write_text("first\nfixed\nthird\n")
    fix = commit(tmp_path, "commissioned defect fix")
    return tmp_path, entry, reviewed, fix


def run(project, *extra, evidence=True):
    repo, _, reviewed, fix = project
    args = [sys.executable, str(CLI), "--project", str(repo), "--fix-pr", "34",
            "--fix-commit", fix, "--defect-fix"]
    if evidence:
        args += ["--reviewed", f"12={reviewed}"]
    return subprocess.run(args + list(extra), capture_output=True, text=True, env=child_env())


def test_actual_cli_appends_only_event_and_shared_reader_labels(project):
    repo, entry, _, _ = project
    before = entry.read_bytes()
    result = run(project)
    assert result.returncode == 0, result.stderr
    assert entry.read_bytes() == before + b"defect-confirmed: source.py:2 \xc2\xb7 source: post-merge-fix \xc2\xb7 pr: 34\n"
    assert git(repo, "diff", "--name-only") == str(entry.relative_to(repo))
    assert git(repo, "diff", "--numstat").split("\t")[:2] == ["1", "0"]
    assert parse_record(entry.read_text())["defect_labels"] == ["source.py:2"]


def test_repeated_invocation_keeps_repeated_events(project):
    _, entry, _, _ = project
    assert run(project).returncode == 0
    assert run(project).returncode == 0
    assert len(parse_record(entry.read_text())["defect_confirmed"]) == 2


def test_second_fix_at_original_anchor_with_restored_base(project):
    repo, entry, reviewed, _ = project
    assert run(project).returncode == 0
    (repo / "source.py").write_text("first\nbroken\nthird\n")
    commit(repo, "independent reintroduction preserving reviewed coordinates")
    (repo / "source.py").write_text("first\nfixed again\nthird\n")
    fix = commit(repo, "second commissioned defect fix")
    assert run((repo, entry, reviewed, fix)).returncode == 0
    assert len(parse_record(entry.read_text())["defect_confirmed"]) == 2


@pytest.mark.parametrize("anchor", ["source.py:1", "source.py:3"])
def test_no_overlap_preserves_all_bytes(project, anchor):
    repo, entry, _, _ = project
    entry.write_text(record(anchor=anchor))
    commit(repo, "different anchor record")
    before = entry.read_bytes()
    result = run(project)
    assert result.returncode == 0 and "no-match=1" in result.stderr
    assert entry.read_bytes() == before
    assert git(repo, "status", "--porcelain") == ""


def test_insertion_does_not_cover_old_line(project):
    repo, entry, reviewed, _ = project
    git(repo, "reset", "--hard", "HEAD~1")
    (repo / "source.py").write_text("first\ninserted\nbroken\nthird\n")
    fix = commit(repo, "pure insertion before anchor")
    before = entry.read_bytes()
    result = run((repo, entry, reviewed, fix))
    assert "no-match=1" in result.stderr
    assert entry.read_bytes() == before


def test_old_coordinates_after_earlier_insertion(project):
    repo, entry, reviewed, _ = project
    git(repo, "reset", "--hard", "HEAD~1")
    (repo / "source.py").write_text("inserted\nfirst\nfixed\nthird\n")
    fix = commit(repo, "insertion plus modification shifts new coordinates")
    assert run((repo, entry, reviewed, fix)).returncode == 0
    assert parse_record(entry.read_text())["defect_labels"] == ["source.py:2"]


@pytest.mark.parametrize("change", ["elsewhere", "shift", "rename", "delete"])
def test_drift_rename_deletion_are_visible_and_leave_record_untouched(project, change):
    repo, entry, reviewed, _ = project
    git(repo, "reset", "--hard", "HEAD~1")
    if change in {"elsewhere", "shift"}:
        text = "different\nbroken\nthird\n" if change == "elsewhere" else "extra\nfirst\nbroken\nthird\n"
        (repo / "source.py").write_text(text)
        commit(repo, "file drift before fix")
        (repo / "source.py").write_text(text.replace("broken", "fixed"))
    elif change == "rename":
        git(repo, "mv", "source.py", "renamed.py")
    else:
        (repo / "source.py").unlink()
    fix = commit(repo, "commissioned fix with unresolved coordinates")
    before = entry.read_bytes()
    result = run((repo, entry, reviewed, fix))
    assert result.returncode == 0 and "WARN unresolved" in result.stderr
    assert entry.read_bytes() == before
    assert git(repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("evidence", [None, "0" * 40, "HEAD", "ambiguous"])
def test_missing_unknown_nonliteral_ambiguous_evidence_is_unresolved(project, evidence):
    _, entry, reviewed, fix = project
    before = entry.read_bytes()
    extra = [] if evidence is None else ["--reviewed", f"12={evidence}"]
    if evidence == "ambiguous":
        extra = ["--reviewed", f"12={reviewed}", "--reviewed", f"12={fix}"]
    result = run(project, *extra, evidence=False)
    assert result.returncode == 0 and "WARN unresolved" in result.stderr
    assert entry.read_bytes() == before


@pytest.mark.parametrize("bad", ["duplicate", "malformed", "encrypted", "opaque"])
def test_unresolved_records_do_not_mutate_while_other_pr_can_proceed(project, bad):
    repo, entry, reviewed, _ = project
    other = entry.with_name("2026-10-04-review-attribution-pr13.md")
    other.write_text(record(pr=13))
    if bad == "duplicate":
        entry.with_name("2026-10-04-review-attribution-pr12.md").write_text(record())
    elif bad == "malformed":
        entry.write_text(record() + "  finding: invalid\n")
    elif bad == "encrypted":
        entry.with_suffix(".md.age").write_bytes(b"age-encryption.org/v1\nfixture ciphertext\n")
    else:
        entry.write_text(record().replace("source.py:2", "source.py:99"))
    commit(repo, "mixed review records")
    before = entry.read_bytes()
    result = run(project, "--reviewed", f"13={reviewed}")
    assert result.returncode == 0 and "WARN unresolved" in result.stderr
    assert entry.read_bytes() == before
    assert parse_record(other.read_text())["defect_labels"] == ["source.py:2"]


def test_opaque_context_is_not_reviewed_coordinate_evidence(project):
    _, entry, reviewed, _ = project
    entry.write_text(record() + f"Context reviewed-SHA: {reviewed}\n")
    before = entry.read_bytes()
    result = run(project, evidence=False)
    assert "absent or ambiguous" in result.stderr
    assert entry.read_bytes() == before


def test_record_symlink_cannot_write_outside_project(project, tmp_path):
    repo, entry, _, _ = project
    outside = tmp_path.parent / (tmp_path.name + "-outside.md")
    outside.write_bytes(entry.read_bytes())
    entry.unlink()
    entry.symlink_to(outside)
    before = outside.read_bytes()
    result = run(project)
    assert "unsafe record path" in result.stderr
    assert outside.read_bytes() == before


def test_non_pr_uncommissioned_and_non_project_cli_rejected(project):
    repo, entry, _, _ = project
    before = entry.read_bytes()
    assert run(project, "--fix-pr", "0").returncode != 0
    assert run(project, "--project", str(repo / "memory")).returncode != 0
    result = subprocess.run([sys.executable, str(CLI), "--project", str(repo),
                             "--fix-pr", "34", "--fix-commit", project[3]],
                            capture_output=True, text=True, env=child_env())
    assert result.returncode != 0 and "--defect-fix" in result.stderr
    assert entry.read_bytes() == before


def test_mismatched_filename_reserves_both_pr_identities(project):
    _, entry, reviewed, _ = project
    other = entry.with_name("2026-10-04-review-attribution-pr12.md")
    other.write_text(record(pr=13))
    before = entry.read_bytes()
    result = run(project, "--reviewed", f"13={reviewed}")
    assert "record PR disagrees with filename" in result.stderr
    assert "duplicate attribution records" in result.stderr
    assert entry.read_bytes() == before


def test_no_final_newline_preserves_original_prefix(project):
    _, entry, _, _ = project
    entry.write_bytes(entry.read_bytes().rstrip(b"\n"))
    before = entry.read_bytes()
    assert run(project).returncode == 0
    assert entry.read_bytes() == before + b"\ndefect-confirmed: source.py:2 \xc2\xb7 source: post-merge-fix \xc2\xb7 pr: 34\n"


def test_reviewed_commit_from_other_history_is_unresolved(project):
    repo, entry, _, _ = project
    foreign = git(repo, "commit-tree", git(repo, "rev-parse", "HEAD^{tree}"), "-m", "unrelated root")
    before = entry.read_bytes()
    result = run(project, "--reviewed", f"12={foreign}", evidence=False)
    assert "WARN unresolved" in result.stderr
    assert entry.read_bytes() == before


@pytest.mark.parametrize("anchor,expected", [("source.py:3", 0), ("source.py:1", 1)])
def test_configured_interhunk_context_does_not_label_unchanged_middle(project, anchor, expected):
    repo, entry, _, _ = project
    git(repo, "reset", "--hard", "HEAD~1")
    (repo / "source.py").write_text("old1\nkeep2\nanchor3\nkeep4\nold5\n")
    entry.write_text(record(anchor=anchor))
    reviewed = commit(repo, "reviewed coordinates for separated edits")
    (repo / "source.py").write_text("new1\nkeep2\nanchor3\nkeep4\nnew5\n")
    fix = commit(repo, "separated commissioned changes")
    git(repo, "config", "diff.interHunkContext", "5")
    before = entry.read_bytes()
    result = run((repo, entry, reviewed, fix))
    assert result.returncode == 0, result.stderr
    events = parse_record(entry.read_text())["defect_confirmed"]
    assert len(events) == expected
    if expected:
        assert events[0]["anchor"] == anchor
        assert entry.read_bytes().startswith(before)
    else:
        assert entry.read_bytes() == before
        assert "no-match=1" in result.stderr


@pytest.fixture
def merged_wrap_project(project):
    repo, entry, reviewed, branch_tip = project
    git(repo, "branch", "fix-topic", branch_tip)
    git(repo, "checkout", "-qb", "integration", "HEAD~1")
    git(repo, "merge", "--no-ff", "-qm", "Merge commissioned fix PR 34", "fix-topic")
    merged = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/remotes/origin/main", merged)
    git(repo, "checkout", "-qb", "wrap-up", "fix-topic")
    assert git(repo, "rev-parse", "HEAD") == branch_tip
    return (repo, entry, reviewed, merged), merged, branch_tip


def test_wrap_branch_below_real_merge_accepts_proven_integration(merged_wrap_project):
    project, merged, branch_tip = merged_wrap_project
    repo, entry, _, _ = project
    before = entry.read_bytes()
    result = run(project, "--merged-through", merged)
    assert result.returncode == 0, result.stderr
    assert entry.read_bytes() == before + b"defect-confirmed: source.py:2 \xc2\xb7 source: post-merge-fix \xc2\xb7 pr: 34\n"
    assert git(repo, "rev-parse", "HEAD") == branch_tip
    assert git(repo, "diff", "--name-only") == str(entry.relative_to(repo))


def test_wrap_branch_without_integration_proof_still_rejects(merged_wrap_project):
    project, _, _ = merged_wrap_project
    before = project[1].read_bytes()
    result = run(project)
    assert result.returncode != 0
    assert project[1].read_bytes() == before


def test_unintegrated_merge_cannot_supply_tautological_proof(merged_wrap_project):
    project, merged, _ = merged_wrap_project
    repo, entry, _, _ = project
    git(repo, "update-ref", "refs/remotes/origin/main", git(repo, "rev-parse", merged + "^1"))
    before = entry.read_bytes()
    result = run(project, "--merged-through", merged)
    assert result.returncode != 0
    assert entry.read_bytes() == before


def test_integration_tip_without_fix_rejects(merged_wrap_project):
    project, merged, _ = merged_wrap_project
    repo, entry, _, _ = project
    before = entry.read_bytes()
    result = run(project, "--merged-through", git(repo, "rev-parse", merged + "^1"))
    assert result.returncode != 0
    assert entry.read_bytes() == before


@pytest.mark.parametrize("color_config", ["color.ui", "color.diff"])
def test_forced_git_color_still_appends_covered_event(project, color_config):
    repo, entry, _, _ = project
    git(repo, "config", color_config, "always")
    before = entry.read_bytes()
    result = run(project)
    assert result.returncode == 0, result.stderr
    assert entry.read_bytes() == before + b"defect-confirmed: source.py:2 \xc2\xb7 source: post-merge-fix \xc2\xb7 pr: 34\n"
    assert parse_record(entry.read_text())["defect_labels"] == ["source.py:2"]
    assert "appended=1" in result.stderr


@pytest.mark.parametrize("private_only", [True, False])
def test_actual_capture_age_name_is_unresolved_and_reserves_pr(project, private_only):
    repo, entry, _, _ = project
    # Exact suffix selected by memory-capture.sh for private capture.
    private = entry.with_suffix(".age")
    private.write_bytes(b"age-encryption.org/v1\nfixture ciphertext\n")
    before = entry.read_bytes()
    if private_only:
        entry.unlink()
    commit(repo, "actual private capture basename fixture")
    result = run(project)
    assert result.returncode == 0, result.stderr
    assert "WARN unresolved" in result.stderr and "encrypted record" in result.stderr
    assert "appended=0" in result.stderr
    if private_only:
        assert not entry.exists()
    else:
        assert "duplicate attribution records" in result.stderr
        assert entry.read_bytes() == before
    assert git(repo, "status", "--porcelain") == ""


def test_private_name_reserves_pr_without_reading_fake_plaintext_header(project):
    repo, entry, _, _ = project
    private = entry.with_suffix(".age")
    # Deliberately wrong header is an opaque stub, never evidence for PR 99.
    private.write_bytes(record(pr=99).encode("utf-8"))
    before = entry.read_bytes()
    commit(repo, "unreadable private fixture with misleading content")
    private.chmod(0)
    try:
        result = run(project)
        assert "encrypted record" in result.stderr
        assert "duplicate attribution records" in result.stderr
        assert "appended=0" in result.stderr
        assert entry.read_bytes() == before
    finally:
        private.chmod(0o600)


def test_invalid_private_basename_warns_without_header_salvage(project):
    repo, entry, _, _ = project
    entry.unlink()
    private = entry.with_name("2026-10-03-review-attribution-prINVALID.age")
    private.write_bytes(record().encode("utf-8"))
    commit(repo, "invalid private filename fixture")
    result = run(project)
    assert result.returncode == 0
    assert "encrypted record" in result.stderr and "WARN unresolved" in result.stderr
    assert "appended=0" in result.stderr
    assert not entry.exists()
    assert git(repo, "status", "--porcelain") == ""
