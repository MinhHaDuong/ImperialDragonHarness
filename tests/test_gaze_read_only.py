"""A gaze run leaves the merge request's branch tip and the caller's worktree unchanged (ticket 1225).

Runs gaze's setup and closing scripts (ticket 1227), around a
simulated review pass that writes its reports in the review worktree, and checks
that the branch, the caller's tree and the scratch all end as they began.
"""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
GAZE = ROOT / "skills" / "gaze"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repos(tmp_path):
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    for key, value in (("user.name", "t"), ("user.email", "t@example.org"), ("commit.gpgsign", "false")):
        git(seed, "config", key, value)
    (seed / "a.txt").write_text("a\n")
    git(seed, "add", "a.txt")
    git(seed, "commit", "-qm", "base")
    git(seed, "switch", "-qc", "feat")
    (seed / "b.txt").write_text("b\n")
    git(seed, "add", "b.txt")
    git(seed, "commit", "-qm", "feature")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-q", "origin", "main", "feat")
    primary = tmp_path / "primary"
    subprocess.run(["git", "clone", "-q", str(origin), str(primary)], check=True)
    caller = primary / ".claude" / "worktrees" / "caller"
    git(primary, "worktree", "add", "-q", "-b", "work", str(caller), "origin/main")
    (caller / "wip.txt").write_text("the caller's uncommitted work\n")
    return origin, primary, caller


def gh_env(tmp_path, primary, origin):
    import json
    import os
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    meta = {"headRefName": "feat", "headRefOid": git(origin, "rev-parse", "refs/heads/feat"),
            "baseRefName": "main", "state": "OPEN", "mergeable": "MERGEABLE", "body": "",
            "comments": [], "reviews": [], "statusCheckRollup": []}
    gh = bin_dir / "gh"
    gh.write_text(f"#!/bin/sh\ncase \"$2\" in view) cat <<'EOF'\n{json.dumps(meta)}\nEOF\n;; esac\n")
    gh.chmod(0o755)
    return {"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(primary.parent),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "s", "GIT_AUTHOR_EMAIL": "s@x",
            "GIT_COMMITTER_NAME": "s", "GIT_COMMITTER_EMAIL": "s@x"}


def run_gaze(tmp_path, repos, seat: str) -> subprocess.CompletedProcess:
    """gaze_setup.py, a simulated seat, then gaze_close.py."""
    origin, primary, caller = repos
    env = gh_env(tmp_path, primary, origin)
    script = (f'set -u\nsetup=$({sys.executable} "{ROOT}/scripts/gaze_setup.py" 7) || exit 1\n'
              'review_tree=$(echo "$setup" | sed -n "s/^review_tree=//p")\n' + seat +
              f'{sys.executable} "{ROOT}/scripts/gaze_close.py" 7 --branch feat\n')
    return subprocess.run(["bash", "-c", script], cwd=caller, capture_output=True, text=True, env=env)


@pytest.mark.parametrize("seat, removed", [
    ('git -C "$review_tree" commit -q --allow-empty -m "a seat that commits" && echo SEAT-COMMITTED\n', True),
    ('echo stray >> "$review_tree/a.txt"\n', False),
])
def test_a_seat_that_writes_cannot_move_the_branch_or_the_callers_tree(tmp_path, repos, seat, removed):
    """A seat that breaks its read-only rail still cannot reach the branch: the
    review tree is detached and gaze never pushes. Uncommitted writes make the
    cleanup refuse to remove the tree, so they are reported, never lost."""
    origin, primary, caller = repos
    tip, caller_status = git(origin, "rev-parse", "refs/heads/feat"), git(caller, "status", "--porcelain")
    run = run_gaze(tmp_path, repos, seat)
    assert (run.returncode == 0) is removed, run.stdout + run.stderr
    assert removed is ("SEAT-COMMITTED" in run.stdout), "the seat's write must have happened"
    assert git(origin, "rev-parse", "refs/heads/feat") == tip
    assert git(caller, "status", "--porcelain") == caller_status
    assert (primary / ".claude" / "worktrees" / "review-7").exists() is not removed


def test_a_gaze_run_leaves_the_branch_tip_and_the_callers_worktree_unchanged(tmp_path, repos):
    origin, primary, caller = repos
    tip = git(origin, "rev-parse", "refs/heads/feat")
    caller_head, caller_status = git(caller, "rev-parse", "HEAD"), git(caller, "status", "--porcelain")
    caller_branch = git(caller, "branch", "--show-current")
    review = (
        'mkdir -p "$review_tree/.panel/7"\n'
        'printf "# budget: 5m\\ncorrectness\\tm\\tanthropic\\tr\\n" > "$review_tree/.panel/7/manifest.txt"\n'
        'printf "worker: model=m · family=anthropic\\nverdict: clear\\n" > "$review_tree/.panel/7/correctness.md"\n'
    )
    run = run_gaze(tmp_path, repos, review)
    assert run.returncode == 0, run.stdout + run.stderr

    assert git(origin, "rev-parse", "refs/heads/feat") == tip
    assert git(caller, "rev-parse", "HEAD") == caller_head
    assert git(caller, "status", "--porcelain") == caller_status
    assert git(caller, "branch", "--show-current") == caller_branch
    review_tree = primary / ".claude" / "worktrees" / "review-7"
    assert not review_tree.exists()
    assert "review-7" not in git(primary, "worktree", "list")
