"""Tests for skills/roar/enumerate-merges.py (ticket 0331).

Roar's telemetry step must log one celebration per merged PR since the
roar-last-sha sentinel, not a single aggregate blob. This script enumerates
the merge commits in <since-sha>..HEAD and emits one JSON record per merge,
recovering the branch from the GitHub-shaped merge subject and the ticket from
the erg-pr-merge close commit inside the merge's second-parent range.

The load-bearing case is anti-tautological: a PR whose branch name carries no
ticket digits but whose range holds a close commit must still recover the
ticket. A branch-name-regex implementation fails it; the specified commit scan
passes.

Each test spawns real git via subprocess, so the module is integration-tier.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ENUMERATE = REPO_ROOT / "skills" / "roar" / "enumerate-merges.py"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("git") is None, reason="git required"),
]


def run(args, cwd=None, check=True):
    return subprocess.run(
        args, cwd=cwd, check=check, capture_output=True, text=True
    )


def git(repo, *args, check=True):
    return run(["git", "-C", str(repo), *args], check=check)


@pytest.fixture
def repo(tmp_path):
    """A real git repo on main with one initial commit."""
    r = tmp_path / "repo"
    run(["git", "init", "-b", "main", str(r)])
    git(r, "config", "user.email", "test@example.com")
    git(r, "config", "user.name", "Test")
    git(r, "config", "commit.gpgsign", "false")
    (r / "README").write_text("hi\n")
    git(r, "add", "-A")
    git(r, "commit", "-m", "init")
    return r


def merge_pr(repo, *, pr, owner_branch, feature_commits, subject=None):
    """Branch off main, add commits, and merge --no-ff back into main.

    owner_branch: the "owner/branch" string used to build a GitHub-shaped
    merge subject, or None (with an explicit ``subject``) for a non-PR merge.
    feature_commits: list of (filename, commit_message) tuples committed on the
    feature branch before the merge.
    """
    branch = f"feat-{pr}"
    git(repo, "switch", "-c", branch)
    for fname, msg in feature_commits:
        (repo / fname).write_text(f"{fname} content\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-m", msg)
    git(repo, "switch", "main")
    if subject is None and owner_branch is not None:
        subject = f"Merge pull request #{pr} from {owner_branch}"
    args = ["merge", "--no-ff", branch]
    if subject is not None:
        args += ["-m", subject]
    git(repo, *args)


def enumerate_merges(repo, since, project="testproj"):
    res = run(
        ["python3", str(ENUMERATE), since, "--project", project],
        cwd=str(repo),
    )
    records = [json.loads(ln) for ln in res.stdout.splitlines() if ln.strip()]
    return records, res


def head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def test_ticket_from_close_commit_not_branch_name(repo):
    """Anti-tautology: ticket comes from the close commit, not the branch name."""
    base = head(repo)
    # First PR: ordinary branch, no close commit -> ticket null.
    merge_pr(
        repo,
        pr=6,
        owner_branch="alice/add-feature",
        feature_commits=[("a.txt", "add feature")],
    )
    # Second PR: branch name has NO ticket digits, but the range carries an
    # erg-pr-merge close commit -> ticket must come from the commit scan.
    merge_pr(
        repo,
        pr=7,
        owner_branch="bob/fix-flaky-widget",
        feature_commits=[
            ("b.txt", "fix the widget"),
            ("dummy", "ticket(0042): close and archive — PR #7"),
        ],
    )
    records, res = enumerate_merges(repo, base)
    assert len(records) == 2, res.stderr
    assert records[0]["branch"] == "add-feature"
    assert records[0]["ticket"] is None
    assert records[1]["branch"] == "fix-flaky-widget"
    assert records[1]["ticket"] == 42


def test_empty_range_emits_nothing(repo):
    base = head(repo)
    records, res = enumerate_merges(repo, base)
    assert records == []
    assert res.returncode == 0
    assert res.stdout.strip() == ""


def test_multi_ticket_close_takes_first_id(repo):
    base = head(repo)
    merge_pr(
        repo,
        pr=8,
        owner_branch="carol/raid-wave",
        feature_commits=[
            ("c.txt", "raid work"),
            ("dummy", "ticket(0042, 0043): close and archive — PR #8"),
        ],
    )
    records, res = enumerate_merges(repo, base)
    assert len(records) == 1, res.stderr
    assert records[0]["ticket"] == 42


def test_filing_commit_not_mistaken_for_close(repo):
    """A ticket-FILING commit in a PR with no close commit must not attribute.

    Ordinary work commits also start "ticket(NNNN):" (the filing convention).
    A raid's per-PR roar logs ticket null for a PR that carried no erg-pr-merge
    close commit; the enumeration must match only the "close and archive — PR #"
    template, not any ticket(...) subject.
    """
    base = head(repo)
    merge_pr(
        repo,
        pr=11,
        owner_branch="erin/no-close",
        feature_commits=[
            ("g.txt", "ticket(0329): file the follow-up ticket"),
            ("h.txt", "wire up the follow-up"),
        ],
    )
    records, res = enumerate_merges(repo, base)
    assert len(records) == 1, res.stderr
    assert records[0]["ticket"] is None


def test_non_pr_merge_subject_branch_null_still_emitted(repo):
    base = head(repo)
    merge_pr(
        repo,
        pr=9,
        owner_branch=None,
        feature_commits=[("d.txt", "some work")],
        subject="Merge branch 'feat-9'",
    )
    records, res = enumerate_merges(repo, base)
    assert len(records) == 1, res.stderr
    assert records[0]["branch"] is None
    assert records[0]["ticket"] is None
    assert records[0]["project"] == "testproj"


def test_files_changed_excludes_interleaved_merges(repo):
    """files_changed counts only the PR's own diff, not intervening PRs.

    A batched session merges PRs cut from an older main. When PR-A is cut off
    C0, PR-B lands on main first, then PR-A is merged, a two-dot M^1..M^2 diff
    charges PR-A with PR-B's files as phantom changes. The PR's own diff (three
    dot, merge-base relative — what GitHub and a raid's per-PR roar record) must
    win.
    """
    base = head(repo)  # C0
    # Cut PR-A off C0, but do not merge it yet.
    git(repo, "switch", "-c", "feat-A")
    (repo / "a1.txt").write_text("a1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "A: one file")
    git(repo, "switch", "main")
    # PR-B lands on main first (three files), advancing main under PR-A.
    merge_pr(
        repo,
        pr=20,
        owner_branch="ben/three-files",
        feature_commits=[
            ("b1.txt", "b1"),
            ("b2.txt", "b2"),
            ("b3.txt", "b3"),
        ],
    )
    # Now merge PR-A off the advanced main.
    git(repo, "merge", "--no-ff", "feat-A", "-m",
        "Merge pull request #21 from ann/feat-A")
    records, res = enumerate_merges(repo, base)
    assert len(records) == 2, res.stderr
    # records[0] = PR-B (no interleaving), records[1] = PR-A (one own file).
    assert records[0]["branch"] == "three-files"
    assert records[0]["files_changed"] == 3
    assert records[1]["branch"] == "feat-A"
    assert records[1]["files_changed"] == 1
    assert records[1]["commits"] == 1


def test_octopus_merge_skipped_not_undercounted(repo):
    """An octopus (3+ parent) merge is skipped visibly, not silently reduced.

    build_records only reads parents[0]/parents[1], so an N-way merge would emit
    one plausible record while dropping every parent beyond the second (its
    commits, files, and close-commit ticket vanish). It must be skipped with a
    stderr note instead. Unreachable via the forge's 2-parent PR merge, but the
    script is a documented standalone CLI where octopus merges occur.
    """
    base = head(repo)
    # A normal PR that must still be emitted, to prove only the octopus is dropped.
    merge_pr(
        repo,
        pr=29,
        owner_branch="ivan/normal-pr",
        feature_commits=[("n.txt", "normal work")],
    )
    # Two feature branches off main, then a single 3-parent octopus merge.
    git(repo, "switch", "-c", "octo-1")
    (repo / "o1.txt").write_text("o1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "octo one")
    git(repo, "switch", "main")
    git(repo, "switch", "-c", "octo-2")
    (repo / "o2.txt").write_text("o2\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "octo two")
    git(repo, "switch", "main")
    git(repo, "merge", "--no-ff", "octo-1", "octo-2", "-m",
        "Merge pull request #30 from x/octo")
    octo_sha = head(repo)
    # Sanity: this really is a 3-parent merge.
    parents = git(repo, "rev-list", "--parents", "-n", "1", octo_sha).stdout.split()
    assert len(parents) == 4, parents  # commit + 3 parents

    records, res = enumerate_merges(repo, base)
    branches = [r["branch"] for r in records]
    assert branches == ["normal-pr"], res.stderr
    assert octo_sha[:12] in res.stderr


def test_commits_and_files_changed_counts(repo):
    base = head(repo)
    merge_pr(
        repo,
        pr=10,
        owner_branch="dan/two-commits",
        feature_commits=[("e.txt", "one"), ("f.txt", "two")],
    )
    records, res = enumerate_merges(repo, base)
    assert len(records) == 1, res.stderr
    assert records[0]["commits"] == 2
    assert records[0]["files_changed"] == 2
