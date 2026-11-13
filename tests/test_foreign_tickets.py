"""Foreign-ticket reports expose overdue requests and recognize owner pickup."""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "scripts/foreign_tickets.py"


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, env=child_env(), check=True,
        text=True, capture_output=True,
    )


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "receiver"
    (root / "tickets").mkdir(parents=True)
    git(root, "init", "-qb", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    for number, stamp, extra in [
        (1, "2026-11-10T12:00Z", ""),
        (2, "2026-11-12T12:00Z", ""),
        (3, "2026-11-10T12:00Z", "Closed: 2026-11-11\n"),
    ]:
        (root / f"tickets/{number:04d}-request.erg").write_text(
            f"%erg 0.1\nTitle: Request {number}\nCreated: 2026-11-10\n{extra}"
            f"\n--- log ---\n{stamp} test note filed from asker 0042\n"
            "\n--- body ---\nRequest body.\n"
        )
    (root / "tickets/0004-local.erg").write_text(
        "%erg 0.1\nTitle: Local\nCreated: 2026-11-10\n\n--- log ---\n"
        "2026-11-10T12:00Z test created\n\n--- body ---\nfiled from body 0001\n"
    )
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture")
    return root


def report(repo, *args):
    result = subprocess.run(
        ["python3", str(REPORT), "--repo", str(repo),
         "--now", "2026-11-13T12:00:00+00:00", *args],
        env=child_env(), text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.integration
@pytest.mark.parametrize("snapshot", [[], ["--ref", "main"]], ids=["molt", "dashboard"])
def test_overdue_foreign_ticket_disappears_after_branch_pickup(repo, snapshot):
    # Exactly one day old, closed, and local tickets are excluded.
    before = report(repo, *snapshot)
    assert "0001 | Request 1 | filed from asker 0042" in before
    assert all(f"{number:04d} |" not in before for number in (2, 3, 4))
    git(repo, "branch", "t00010-unrelated")
    assert "0001 |" in report(repo, *snapshot)
    git(repo, "branch", "t1-owner-pickup")
    assert report(repo, *snapshot) == ""


@pytest.mark.integration
def test_locked_worktree_ticket_name_suppresses_report(repo, tmp_path):
    worktree = tmp_path / "worker"
    git(repo, "worktree", "add", "--detach", str(worktree))
    git(repo, "worktree", "lock", "--reason", "hunt t1 (owner pid not visible)", str(worktree))
    assert report(repo) == ""


@pytest.mark.integration
def test_unavailable_snapshot_is_reported_as_error(repo):
    result = subprocess.run(
        ["python3", str(REPORT), "--repo", str(repo), "--ref", "missing"],
        env=child_env(), text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert result.stderr


@pytest.mark.integration
def test_dashboard_invokes_shared_report(repo, tmp_path):
    origin = tmp_path / "origin.git"
    git(repo, "clone", "--bare", str(repo), str(origin))
    git(repo, "remote", "add", "origin", str(origin))

    def dashboard():
        result = subprocess.run(
            ["bash", str(ROOT / "skills/dashboard/dashboard.sh")],
            cwd=repo, env=child_env(), text=True, capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.split("== unpicked foreign tickets (over one day)\n")[1].split("== remote branches")[0]

    assert "0001 | Request 1 | filed from asker 0042" in dashboard()
    git(repo, "branch", "t1-owner")
    assert "0001 |" not in dashboard()


@pytest.mark.integration
def test_lock_owner_pid_does_not_claim_unrelated_ticket(repo, tmp_path):
    worktree = tmp_path / "worker"
    git(repo, "worktree", "add", "--detach", str(worktree))
    git(repo, "worktree", "lock", "--reason", "hunt t99 (pid 1)", str(worktree))
    assert "0001 | Request 1" in report(repo)
