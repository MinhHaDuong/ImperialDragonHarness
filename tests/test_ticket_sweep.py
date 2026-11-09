"""Exercise scripts/ticket-sweep.sh: close, archive, prune, merged-probe."""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env


ROOT = Path(__file__).resolve().parent.parent
SWEEP = ROOT / "scripts/ticket-sweep.sh"
MOLT = ROOT / "skills/molt/SKILL.md"
YAWN = ROOT / "skills/yawn/SKILL.md"
OLD_ERG_REV = "51ee49c"

TICKET = (
    "%erg 0.1\nTitle: Probe\nCreated: 2026-09-10\nAuthor: test\n"
    "\n--- log ---\n2026-09-10T10:00Z test created\n\n--- body ---\n"
    "## Exit criteria\n- [ ] Done\n"
)


def run(*args, cwd, env=None):
    result = subprocess.run(
        args, cwd=cwd, env=env if env is not None else child_env(), text=True, capture_output=True
    )
    assert result.returncode == 0, f"{args}: {result.stdout}\n{result.stderr}"
    return result


def sweep(repo, *args, erg=None):
    env = child_env()
    env["MOLT_ERG"] = str(erg or ROOT / "tickets/erg")
    return subprocess.run(
        ["bash", str(SWEEP), *args], cwd=repo, env=env, text=True, capture_output=True
    )


def make_repo(tmp_path, ticket=True):
    repo = tmp_path / "repo"
    (repo / "tickets/closed").mkdir(parents=True)
    if ticket:
        (repo / "tickets/0001-probe.erg").write_text(TICKET)
    run("git", "init", "-q", "-b", "main", cwd=repo)
    run("git", "config", "user.name", "Test", cwd=repo)
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "add", "--", "tickets", cwd=repo)
    run("git", "commit", "-qm", "fixture", "--allow-empty", cwd=repo)
    return repo


def old_erg(tmp_path):
    old = tmp_path / "old-erg"
    old.write_bytes(subprocess.run(
        ["git", "show", f"{OLD_ERG_REV}:tickets/erg"], cwd=ROOT, check=True,
        capture_output=True, env=child_env(),
    ).stdout)
    old.chmod(0o755)
    return old


def branch_with_commit(repo, name):
    run("git", "switch", "-qc", name, cwd=repo)
    (repo / f"{name}.txt").write_text("x")
    run("git", "add", "--", f"{name}.txt", cwd=repo)
    run("git", "commit", "-qm", "wip", cwd=repo)
    run("git", "switch", "-q", "main", cwd=repo)


def closed_ticket(repo, num, closed_header):
    path = repo / f"tickets/closed/{num:04d}-thing.erg"
    path.write_text(TICKET.replace("Author: test\n", f"Author: test\nClosed: {closed_header}\n"))
    run("git", "add", "--", str(path.relative_to(repo)), cwd=repo)
    run("git", "commit", "-qm", f"ticket {num}", cwd=repo)


# --- merged-probe ---

@pytest.mark.integration
def test_probe_unmapped_branch_is_could_not_determine(tmp_path):
    repo = make_repo(tmp_path)
    branch_with_commit(repo, "feature-x")
    r = sweep(repo, "merged-probe", "feature-x")
    assert r.returncode == 2 and "could-not-determine" in r.stdout


@pytest.mark.integration
def test_probe_ancestor_is_merged(tmp_path):
    repo = make_repo(tmp_path)
    branch_with_commit(repo, "feature-x")
    run("git", "merge", "-q", "--no-ff", "-m", "merge", "feature-x", cwd=repo)
    assert sweep(repo, "merged-probe", "feature-x").returncode == 0


@pytest.mark.integration
def test_probe_squash_subject_is_merged(tmp_path):
    """Ancestry alone says no; the PR-subject signal must still say merged."""
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "autoclosed — PR #42")
    branch_with_commit(repo, "t0007-thing")
    run("git", "commit", "-q", "--allow-empty", "-m", "feat: thing (#42)", cwd=repo)
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", "t0007-thing", "main"], cwd=repo, env=child_env()
    )
    assert ancestor.returncode == 1
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 0


@pytest.mark.integration
def test_probe_mapped_not_merged(tmp_path):
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "autoclosed — PR #42")
    branch_with_commit(repo, "t0007-thing")
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 1


@pytest.mark.integration
def test_probe_mapped_without_pr_number_is_could_not_determine(tmp_path):
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "implemented in this PR")
    branch_with_commit(repo, "t0007-thing")
    r = sweep(repo, "merged-probe", "t0007-thing")
    assert r.returncode == 2 and "could-not-determine" in r.stdout


@pytest.mark.integration
@pytest.mark.parametrize("sub", [["merged-probe", "b"], ["archive"], ["close", "0001"]])
def test_no_erg_or_no_tickets_exits_2(tmp_path, sub):
    # No tickets/ directory at all (aedist-technical-report shape).
    bare = tmp_path / "bare"
    bare.mkdir()
    run("git", "init", "-q", "-b", "main", cwd=bare)
    assert sweep(bare, *sub).returncode == 2
    # tickets/ present but the erg binary is missing.
    repo = make_repo(tmp_path)
    assert sweep(repo, *sub, erg=tmp_path / "absent-erg").returncode == 2


# --- close ---

@pytest.mark.integration
def test_close_stages_moved_ticket(tmp_path):
    repo = make_repo(tmp_path)
    r = sweep(repo, "close", "0001")
    assert r.returncode == 0, r.stderr
    run("git", "commit", "-qm", "close", cwd=repo)
    assert run("git", "ls-files", cwd=repo).stdout.splitlines() == ["tickets/closed/0001-probe.erg"]


@pytest.mark.integration
def test_close_already_moved(tmp_path):
    """Ticket already archived: report and exit 1 without a git pathspec error."""
    repo = make_repo(tmp_path, ticket=False)
    closed_ticket(repo, 1, "already-done")
    r = sweep(repo, "close", "0001")
    assert r.returncode == 1
    assert "No open ticket file for 0001" in r.stderr
    assert "pathspec" not in r.stderr


@pytest.mark.integration
def test_close_aborts_on_collision(tmp_path):
    """A close error must stop before any git add."""
    repo = make_repo(tmp_path)
    collision = repo / "tickets/closed/0001-probe.erg"
    collision.write_text("pre-existing untracked file\n")
    r = sweep(repo, "close", "0001")
    assert r.returncode != 0
    assert run("git", "diff", "--cached", "--name-only", cwd=repo).stdout == ""
    assert run("git", "status", "--porcelain", "--untracked-files=all", cwd=repo).stdout == (
        " M tickets/0001-probe.erg\n"
        "?? tickets/closed/0001-probe.erg\n"
    )
    assert collision.read_text() == "pre-existing untracked file\n"


# --- archive ---

@pytest.mark.integration
@pytest.mark.parametrize(
    ("old_binary", "recorded_close"),
    [(False, True), (True, True), (True, False)],
    ids=["current-erg", "old-erg", "old-erg-preclosed"],
)
def test_archive_stages_only_reported(tmp_path, old_binary, recorded_close):
    repo = make_repo(tmp_path)
    stray = repo / "tickets/closed/stray.txt"
    stray.write_text("must stay untracked\n")
    erg = old_erg(tmp_path) if old_binary else ROOT / "tickets/erg"
    if recorded_close:
        assert sweep(repo, "close", "0001", erg=erg).returncode == 0
    else:
        run(str(erg), "close", "0001", "already-done", "tickets/", cwd=repo)
    r = sweep(repo, "archive", erg=erg)
    assert r.returncode == 0, r.stderr
    run("git", "commit", "-qm", "chore: housekeeping fixes (sweep)", cwd=repo)

    archived = "tickets/closed/0001-probe.erg"
    assert run("git", "ls-files", cwd=repo).stdout.splitlines() == [archived]
    assert run("git", "status", "--porcelain", "--", archived, "tickets/0001-probe.erg", cwd=repo).stdout == ""
    assert run("git", "status", "--porcelain", "--untracked-files=all", cwd=repo).stdout == "?? tickets/closed/stray.txt\n"
    stray.unlink()

    # A second sweep over the closed ticket has nothing to stage.
    assert sweep(repo, "archive", erg=erg).returncode == 0
    assert run("git", "diff", "--cached", "--name-only", cwd=repo).stdout == ""


@pytest.mark.integration
def test_prune_duplicates(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "tickets/closed/0001-probe.erg").write_text(TICKET)
    run("git", "add", "--", "tickets", cwd=repo)
    run("git", "commit", "-qm", "duplicate", cwd=repo)
    assert len(run("git", "ls-files", cwd=repo).stdout.splitlines()) == 2
    assert sweep(repo, "archive").returncode == 0
    assert run("git", "ls-files", cwd=repo).stdout.splitlines() == ["tickets/closed/0001-probe.erg"]
    assert not (repo / "tickets/0001-probe.erg").exists()


# --- SKILL.md call sites ---

def test_skills_call_the_script():
    molt = MOLT.read_text()
    for sub in ("close <id>", "archive", "merged-probe <branch>"):
        assert f'ticket-sweep.sh" {sub}' in molt, sub
    assert "ticket-sweep.sh" in YAWN.read_text()
    assert "grep -oP" not in molt + YAWN.read_text()


@pytest.mark.integration
def test_probe_missing_branch_is_could_not_determine(tmp_path):
    """A git error (no such branch) is not 'not merged' and not a crash."""
    repo = make_repo(tmp_path)
    r = sweep(repo, "merged-probe", "t0009-nope")
    assert r.returncode == 2 and "could-not-determine" in r.stdout


@pytest.mark.integration
def test_probe_first_pr_number_wins(tmp_path):
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "autoclosed — PR #42, followup of #12")
    branch_with_commit(repo, "t0007-thing")
    run("git", "commit", "-q", "--allow-empty", "-m", "feat: thing (#42)", cwd=repo)
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 0


@pytest.mark.integration
def test_prune_skips_untracked_duplicate(tmp_path):
    repo = make_repo(tmp_path, ticket=False)
    (repo / "tickets/0001-probe.erg").write_text(TICKET)
    (repo / "tickets/closed/0001-probe.erg").write_text(TICKET)
    r = sweep(repo, "archive")
    assert r.returncode == 0 and "untracked duplicate" in r.stderr
    assert (repo / "tickets/0001-probe.erg").exists()


@pytest.mark.integration
def test_probe_ignores_pr_subject_older_than_the_fork(tmp_path):
    """A historical main commit citing the same PR number is not a merge of this branch."""
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "autoclosed — PR #42")
    run("git", "commit", "-q", "--allow-empty", "-m", "old unrelated work (#42)", cwd=repo)
    branch_with_commit(repo, "t0007-thing")
    run("git", "commit", "-q", "--allow-empty", "-m", "later work", cwd=repo)
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 1


@pytest.mark.integration
def test_archive_failure_is_reported_and_stops_the_prune(tmp_path):
    repo = make_repo(tmp_path, ticket=False)
    (repo / "tickets/closed/0001-probe.erg").write_text(TICKET)
    run("git", "add", "--", "tickets", cwd=repo)
    (repo / "tickets/0001-probe.erg").write_text(TICKET)
    run("git", "add", "--", "tickets", cwd=repo)
    run("git", "commit", "-qm", "duplicate", cwd=repo)
    bad = tmp_path / "bad-erg"
    bad.write_text("#!/bin/sh\necho 'archive: boom' >&2\nexit 1\n")
    bad.chmod(0o755)
    r = sweep(repo, "archive", erg=bad)
    assert r.returncode != 0
    assert "boom" in r.stderr
    assert (repo / "tickets/0001-probe.erg").exists()


def test_run_helper_strips_bash_env(tmp_path, monkeypatch):
    marker = tmp_path / "loaded"
    loader = tmp_path / "loader.sh"
    loader.write_text(f"touch {marker}\n")
    monkeypatch.setenv("BASH_ENV", str(loader))
    run("bash", "-c", "true", cwd=tmp_path)
    assert not marker.exists()


def test_molt_writes_no_state_stamp():
    """Ticket 1138: molt stamps nothing in STATE.md; its PR exists only when
    the run produced commits."""
    skill = (Path(__file__).resolve().parents[1] / "skills" / "molt" / "SKILL.md").read_text()
    assert "**Timestamp.**" not in skill
    assert "STATE timestamp" not in skill
    assert "6.5" not in skill
    assert "**Open merge request.** If any commits were created" in skill


# --- merged-probe: default branch and patch-id evidence ---

def master_repo(tmp_path, set_head=True):
    """A repo whose default branch is master, with a bare origin."""
    repo = make_repo(tmp_path)
    run("git", "branch", "-qm", "master", cwd=repo)
    origin = tmp_path / "origin.git"
    run("git", "init", "-q", "--bare", str(origin), cwd=tmp_path)
    run("git", "remote", "add", "origin", str(origin), cwd=repo)
    run("git", "push", "-q", "origin", "master", cwd=repo)
    run("git", "fetch", "-q", "origin", cwd=repo)
    if set_head:
        run("git", "remote", "set-head", "origin", "master", cwd=repo)
    return repo


def switch_branch(repo, name, *, create=False):
    run("git", "switch", "-q", *(["-c"] if create else []), name, cwd=repo)


@pytest.mark.integration
def test_probe_master_default_ancestor_is_merged(tmp_path):
    repo = master_repo(tmp_path)
    run("git", "switch", "-q", "master", cwd=repo)
    switch_branch(repo, "feature-x", create=True)
    (repo / "x.txt").write_text("x")
    run("git", "add", "--", "x.txt", cwd=repo)
    run("git", "commit", "-qm", "wip", cwd=repo)
    switch_branch(repo, "master")
    run("git", "merge", "-q", "--ff-only", "feature-x", cwd=repo)
    assert sweep(repo, "merged-probe", "feature-x").returncode == 0


@pytest.mark.integration
def test_probe_master_default_via_origin_head_only(tmp_path):
    """origin/HEAD names master and no local main exists; unmerged stays 1."""
    repo = master_repo(tmp_path)
    run("git", "switch", "-q", "master", cwd=repo)
    closed_ticket(repo, 7, "autoclosed — PR #42")
    switch_branch(repo, "t0007-thing", create=True)
    (repo / "t.txt").write_text("t")
    run("git", "add", "--", "t.txt", cwd=repo)
    run("git", "commit", "-qm", "wip", cwd=repo)
    switch_branch(repo, "master")
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 1


@pytest.mark.integration
def test_probe_no_default_branch_is_could_not_determine(tmp_path):
    repo = make_repo(tmp_path)
    run("git", "branch", "-qm", "trunk", cwd=repo)
    r = sweep(repo, "merged-probe", "trunk")
    assert r.returncode == 2 and "no default branch" in r.stderr


def cherry_picked(repo, name, files=1):
    """Branch with commits that main then gained by cherry-pick (no ancestry)."""
    switch_branch(repo, name, create=True)
    for i in range(files):
        (repo / f"{name}-{i}.txt").write_text(str(i))
        run("git", "add", "--", f"{name}-{i}.txt", cwd=repo)
        run("git", "commit", "-qm", f"wip {i}", cwd=repo)
    switch_branch(repo, "main")
    return name


@pytest.mark.integration
def test_probe_cherry_picked_branch_is_merged_without_pr_number(tmp_path):
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "implemented in this PR")
    cherry_picked(repo, "t0007-thing")
    run("git", "cherry-pick", "t0007-thing", cwd=repo)
    run("git", "commit", "-q", "--allow-empty", "-m", "unrelated", cwd=repo)
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 0


@pytest.mark.integration
def test_probe_partially_landed_branch_is_not_merged(tmp_path):
    """One '+' in git cherry: the squash dropped a change, so not merged (exit 1)."""
    repo = make_repo(tmp_path)
    closed_ticket(repo, 7, "autoclosed — PR #42")
    cherry_picked(repo, "t0007-thing", files=2)
    run("git", "cherry-pick", "t0007-thing~1", cwd=repo)
    assert sweep(repo, "merged-probe", "t0007-thing").returncode == 1


@pytest.mark.integration
def test_probe_partially_landed_unmapped_branch_is_could_not_determine(tmp_path):
    repo = make_repo(tmp_path)
    cherry_picked(repo, "feature-x", files=2)
    run("git", "cherry-pick", "feature-x~1", cwd=repo)
    r = sweep(repo, "merged-probe", "feature-x")
    assert r.returncode == 2 and "could-not-determine" in r.stdout
