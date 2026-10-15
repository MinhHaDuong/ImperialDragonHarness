"""Exercise skills/molt/ticket-sweep.sh: close, archive, prune, merged-probe."""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env


ROOT = Path(__file__).resolve().parent.parent
SWEEP = ROOT / "skills/molt/ticket-sweep.sh"
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
def test_reconcile_path_is_per_run(tmp_path):
    """Run molt step 1.8 twice with a stub zotero.py; the --out paths must differ."""
    import re

    section = MOLT.read_text().split("1.8. **Reconcile", 1)[1].split("2. **Yawn.**", 1)[0]
    block = re.findall(r"```bash\n(.*?)\n\s*```", section, re.S)[0]
    root = tmp_path / "idh"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts/zotero.py").write_text(
        "import sys, pathlib\n"
        "args = sys.argv\n"
        "pathlib.Path(sys.argv[0]).with_name('seen.txt').open('a').write(args[args.index('--out') + 1] + '\\n')\n"
    )
    proj = tmp_path / "proj"
    (proj / "docs").mkdir(parents=True)
    env = child_env()
    env["IDH_ROOT"] = str(root)
    env["TMPDIR"] = str(tmp_path)
    for _ in range(2):
        run("bash", "-c", block, cwd=proj, env=env)
    seen = (root / "scripts/seen.txt").read_text().split()
    assert len(seen) == 2 and seen[0] != seen[1]


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


def reconcile_block():
    section = MOLT.read_text().split("1.8. **Reconcile", 1)[1].split("2. **Yawn.**", 1)[0]
    return reconcile_blocks(section)[0]


def reconcile_blocks(text):
    import re

    return re.findall(r"```bash\n(.*?)\n\s*```", text, re.S)


def stub_zotero(tmp_path, status):
    root = tmp_path / "idh"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts/zotero.py").write_text(f"import sys\nsys.exit({status})\n")
    shim = tmp_path / "bin/zotero.py"
    shim.parent.mkdir(parents=True)
    shim.write_text(f"#!/bin/sh\nexit {status}\n")
    shim.chmod(0o755)
    proj = tmp_path / "proj"
    (proj / "docs").mkdir(parents=True)
    env = child_env()
    env["IDH_ROOT"] = str(root)
    env["TMPDIR"] = str(tmp_path)
    env["PATH"] = f"{shim.parent}:{env['PATH']}"
    return proj, env


@pytest.mark.integration
@pytest.mark.parametrize("which", ["molt", "backfill"])
def test_reconcile_failure_propagates_and_path_announced(tmp_path, which):
    """A failing reconcile must fail the block, and the report path is still named."""
    if which == "molt":
        block = reconcile_block()
    else:
        text = (ROOT / "skills/zotero/references/backfill.md").read_text()
        block = next(b for b in reconcile_blocks(text) if "reconcile . --out" in b)
    proj, env = stub_zotero(tmp_path, 7)
    r = subprocess.run(["bash", "-c", block], cwd=proj, env=env, text=True, capture_output=True)
    assert r.returncode != 0, (r.returncode, r.stdout, r.stderr)
    assert "reconcile report: " in r.stdout and "(exit 7)" in r.stdout
    okdir = tmp_path / "ok"
    okdir.mkdir()
    proj2, env2 = stub_zotero(okdir, 0)
    assert subprocess.run(["bash", "-c", block], cwd=proj2, env=env2).returncode == 0


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
