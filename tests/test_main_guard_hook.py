"""Main-update guard: the reference-transaction hook (ticket 1157, tracker 1045).

The hook journals every update of `refs/heads/main` and, only when
`git config idh.mainGuard` is `enforce`, refuses one that is not a gated
merge. Default `warn`: journal plus a stderr warning, exit 0.

Every case runs real git in a scratch clone whose `core.hooksPath=hooks`
points at a committed copy of the harness hook, as in the harness itself, so
a linked worktree reaches the hook through its own checkout of `hooks/`.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "reference-transaction"
SYNC = ROOT / "scripts" / "sync-local-main.sh"
GATE_NOTES_REF = "refs/notes/gate"


def _env():
    env = {k: v for k, v in child_env().items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_NAME="Fixture",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
        LC_ALL="C",
    )
    return env


def git(cwd, *args, check=True):
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, env=_env()
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {args} failed: {proc.stderr}")
    return proc


def rev(cwd, ref):
    return git(cwd, "rev-parse", ref).stdout.strip()


def journal(repo):
    common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    path = Path(common) / "idh" / "main-journal.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture
def repos(tmp_path):
    """origin (bare), work (clone, main checked out), wt2 (linked worktree)."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = tmp_path / "seed"
    git(tmp_path, "init", "-q", "-b", "main", str(seed))
    (seed / "hooks").mkdir()
    shutil.copy2(HOOK, seed / "hooks" / "reference-transaction")
    (seed / "README").write_text("seed\n")
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "seed with hook")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-q", "origin", "main")
    work = tmp_path / "work"
    git(tmp_path, "clone", "-q", str(origin), str(work))
    git(work, "config", "core.hooksPath", "hooks")
    wt2 = tmp_path / "wt2"
    git(work, "worktree", "add", "-q", "-b", "side", str(wt2), "main")
    return {"origin": origin, "seed": seed, "work": work, "wt2": wt2, "tmp": tmp_path}


def advance_origin(r, name="upstream"):
    """A commit lands on origin/main from elsewhere (the forge's merge)."""
    (r["seed"] / name).write_text(name + "\n")
    git(r["seed"], "add", "-A")
    git(r["seed"], "commit", "-q", "-m", name)
    git(r["seed"], "push", "-q", "origin", "main")
    return rev(r["seed"], "HEAD")


def local_commit(repo, name="local"):
    (Path(repo) / name).write_text(name + "\n")
    git(repo, "add", "-A")
    return git(repo, "commit", "-q", "-m", name, check=False)


def test_hook_is_installed_under_core_hooks_path(repos):
    assert HOOK.exists() and os.access(HOOK, os.X_OK)
    mode = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-s", "hooks/reference-transaction"],
        capture_output=True, text=True, env=_env(),
    ).stdout.split()
    assert mode and mode[0] == "100755"
    # Installation is verified, not assumed: git's own resolution of the hook
    # path lands on the committed file, in the clone and in a linked worktree.
    for repo in (repos["work"], repos["wt2"]):
        resolved = git(repo, "rev-parse", "--git-path", "hooks/reference-transaction").stdout.strip()
        resolved = (Path(repo) / resolved).resolve()
        assert resolved == (Path(repo) / "hooks" / "reference-transaction").resolve()
        assert resolved.read_bytes() == HOOK.read_bytes()


def test_warn_is_the_default_and_journals_the_actor(repos):
    work = repos["work"]
    before = rev(work, "main")
    proc = local_commit(work)
    assert proc.returncode == 0, proc.stderr
    assert rev(work, "main") != before
    assert "main-guard" in proc.stderr and "not a gated merge" in proc.stderr
    records = [r for r in journal(work) if r["phase"] == "prepared"]
    assert records, "no journal record"
    rec = records[-1]
    assert rec["ref"] == "refs/heads/main"
    assert rec["current"] == before and rec["new"] == rev(work, "main")
    assert rec["mode"] == "warn" and rec["action"] == "warned"
    assert rec["decision"] == "not-gated"
    assert rec["user"] and rec["host"] and rec["time"].endswith("Z")
    assert "fixture@example.invalid" in rec["git_ident"]
    cmds = " ".join(p["cmd"] for p in rec["procs"])
    assert "git" in cmds and "commit" in cmds
    assert any(r["phase"] == "committed" for r in journal(work))


def test_enforce_refuses_a_local_commit_on_main(repos):
    work = repos["work"]
    git(work, "config", "idh.mainGuard", "enforce")
    before = rev(work, "main")
    proc = local_commit(work)
    assert proc.returncode != 0
    assert rev(work, "main") == before
    assert "refused" in proc.stderr
    rec = [r for r in journal(work) if r["phase"] == "prepared"][-1]
    assert rec["action"] == "refused"


def test_enforce_allows_fast_forward_to_origin_main(repos):
    work = repos["work"]
    git(work, "config", "idh.mainGuard", "enforce")
    tip = advance_origin(repos)
    git(work, "fetch", "-q", "origin")
    proc = git(work, "merge", "--ff-only", "-q", "origin/main", check=False)
    assert proc.returncode == 0, proc.stderr
    assert rev(work, "main") == tip
    assert "main-guard" not in proc.stderr


@pytest.mark.parametrize("atomic", [False, True])
def test_enforce_allows_fetching_origin_main_into_main(repos, atomic):
    """`fetch origin main:main` moves main before origin/main (own transaction);
    `--atomic` moves both in one. Both are the forge's main coming home."""
    wt2 = repos["wt2"]
    work = repos["work"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")  # main checked out nowhere
    tip = advance_origin(repos)
    flags = ["--atomic"] if atomic else []
    proc = git(wt2, "fetch", "-q", *flags, "origin", "main:main", check=False)
    assert proc.returncode == 0, proc.stderr
    assert rev(wt2, "main") == tip


def test_enforce_refuses_fetching_another_remotes_main_into_main(repos, tmp_path):
    wt2, work = repos["wt2"], repos["work"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")
    fork = tmp_path / "fork"
    git(tmp_path, "clone", "-q", str(repos["origin"]), str(fork))
    local_commit(fork, "forked")
    git(work, "remote", "add", "fork", str(fork))
    before = rev(wt2, "main")
    proc = git(wt2, "fetch", "-q", "fork", "main:main", check=False)
    assert proc.returncode != 0
    assert rev(wt2, "main") == before


@pytest.mark.parametrize("checked_out", [True, False])
def test_sync_local_main_still_works_in_enforce_mode(repos, checked_out):
    work = repos["work"]
    git(work, "config", "idh.mainGuard", "enforce")
    if not checked_out:
        git(work, "switch", "-q", "--detach")
    tip = advance_origin(repos)
    proc = subprocess.run(
        ["bash", str(SYNC), str(repos["wt2"]), "main"],
        capture_output=True, text=True, env=_env(),
    )
    assert proc.returncode == 0
    assert rev(work, "main") == tip, proc.stdout + proc.stderr
    assert "main-guard" not in proc.stderr


@pytest.mark.parametrize("mode,allowed", [("enforce", False), ("warn", True)])
def test_second_worktree_behaves_the_same(repos, mode, allowed):
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", mode)
    (wt2 / "side").write_text("side\n")
    git(wt2, "add", "-A")
    git(wt2, "commit", "-q", "-m", "side")
    side = rev(wt2, "HEAD")
    before = rev(wt2, "main")
    proc = git(wt2, "update-ref", "refs/heads/main", side, check=False)
    assert (proc.returncode == 0) is allowed, proc.stderr
    assert rev(work, "main") == (side if allowed else before)
    rec = [r for r in journal(wt2) if r["phase"] == "prepared"][-1]
    assert rec["action"] == ("warned" if allowed else "refused")
    assert rec["cwd"] == str(wt2)


def _candidate(repo, parent_branch="side"):
    """A --no-ff merge of a branch into main, built without moving main."""
    tree = rev(repo, f"{parent_branch}^{{tree}}")
    main = rev(repo, "main")
    side = rev(repo, parent_branch)
    return git(repo, "commit-tree", tree, "-p", main, "-p", side, "-m", "Merge side").stdout.strip()


@pytest.mark.parametrize("with_note", [True, False])
def test_enforce_accepts_a_gated_merge_only_with_its_record(repos, with_note):
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")
    (wt2 / "feature").write_text("feature\n")
    git(wt2, "add", "-A")
    git(wt2, "commit", "-q", "-m", "feature")
    cand = _candidate(wt2)
    if with_note:  # fixture stand-in for ticket 1156's record writer
        git(wt2, "notes", f"--ref={GATE_NOTES_REF}", "add", "-m", "fixture gate record", cand)
    old = rev(wt2, "main")
    proc = git(wt2, "update-ref", "refs/heads/main", cand, old, check=False)
    assert (proc.returncode == 0) is with_note, proc.stderr
    if with_note:
        rec = [r for r in journal(wt2) if r["phase"] == "prepared"][-1]
        assert rec["decision"] == "gate-record" and rec["action"] == "allowed"


def test_a_record_on_a_stale_candidate_does_not_pass(repos):
    """The record must sit on a merge whose first parent is the current main."""
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    (wt2 / "feature").write_text("feature\n")
    git(wt2, "add", "-A")
    git(wt2, "commit", "-q", "-m", "feature")
    tree = rev(wt2, "HEAD^{tree}")
    stale = git(wt2, "commit-tree", tree, "-p", rev(wt2, "HEAD"), "-m", "not on main").stdout.strip()
    git(wt2, "notes", f"--ref={GATE_NOTES_REF}", "add", "-m", "fixture", stale)
    proc = git(wt2, "update-ref", "refs/heads/main", stale, check=False)
    assert proc.returncode != 0


def test_enforce_refuses_deleting_main(repos):
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")
    proc = git(wt2, "update-ref", "-d", "refs/heads/main", check=False)
    assert proc.returncode != 0
    assert git(wt2, "rev-parse", "-q", "--verify", "refs/heads/main", check=False).returncode == 0


def test_a_journal_failure_never_blocks_nor_shouts(repos):
    work = repos["work"]
    common = Path(git(work, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    (common / "idh").write_text("a file where the journal directory should be\n")
    git(work, "config", "idh.mainGuard", "off")
    tip = advance_origin(repos)
    git(work, "fetch", "-q", "origin")
    proc = git(work, "merge", "--ff-only", "-q", "origin/main", check=False)
    assert proc.returncode == 0
    assert rev(work, "main") == tip
    assert proc.stderr.strip() == ""


def test_off_mode_journals_without_warning(repos):
    work = repos["work"]
    git(work, "config", "idh.mainGuard", "off")
    proc = local_commit(work)
    assert proc.returncode == 0
    assert "main-guard" not in proc.stderr
    rec = [r for r in journal(work) if r["phase"] == "prepared"][-1]
    assert rec["action"] == "allowed" and rec["decision"] == "not-gated"


def test_other_refs_are_ignored(repos):
    wt2 = repos["wt2"]
    (wt2 / "x").write_text("x\n")
    git(wt2, "add", "-A")
    proc = git(wt2, "commit", "-q", "-m", "x")
    assert "main-guard" not in proc.stderr
    assert journal(wt2) == []


def _stdin(repo, script, check=False):
    return subprocess.run(
        ["git", "-C", str(repo), "update-ref", "--stdin"], input=script,
        capture_output=True, text=True, env=_env(), check=check,
    )


@pytest.mark.parametrize("mode", ["enforce", "warn"])
def test_a_verify_of_main_is_not_an_update(repos, mode):
    """`verify main <old>` reaches the hook as "<old> <zero>", like a delete."""
    wt2 = repos["wt2"]
    git(wt2, "config", "idh.mainGuard", mode)
    main = rev(wt2, "main")
    proc = _stdin(wt2, f"verify refs/heads/main {main}\ncreate refs/heads/other {main}\n")
    assert proc.returncode == 0, proc.stderr
    assert rev(wt2, "other") == main and rev(wt2, "main") == main
    assert "main-guard" not in proc.stderr
    assert journal(wt2) == []


def test_a_stdin_delete_of_main_is_journaled_and_warned(repos):
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")
    main = rev(wt2, "main")
    proc = _stdin(wt2, f"delete refs/heads/main {main}\n")
    assert "deleted" in proc.stderr
    assert git(wt2, "rev-parse", "-q", "--verify", "refs/heads/main", check=False).returncode != 0
    rec = journal(wt2)[-1]
    assert rec["decision"] == "deleted-unrefusable" and rec["phase"] == "committed"


@pytest.mark.parametrize("how", ["update-ref", "branch"])
def test_enforce_refuses_a_deletion_with_an_expected_old_value(repos, how):
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")
    main = rev(wt2, "main")
    if how == "update-ref":
        proc = git(wt2, "update-ref", "-d", "refs/heads/main", main, check=False)
    else:
        proc = git(wt2, "branch", "-D", "main", check=False)
    assert proc.returncode != 0
    assert rev(wt2, "main") == main


def test_moving_origin_main_alongside_main_is_not_a_pass(repos):
    """Only a fetch may vouch for main with an origin/main of the same transaction."""
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    (wt2 / "sneak").write_text("sneak\n")
    git(wt2, "add", "-A")
    git(wt2, "commit", "-q", "-m", "sneak")
    sneak = rev(wt2, "HEAD")
    before = rev(wt2, "main")
    proc = _stdin(wt2, f"update refs/remotes/origin/main {sneak}\nupdate refs/heads/main {sneak}\n")
    assert proc.returncode != 0
    assert rev(wt2, "main") == before


def test_a_record_on_a_single_parent_commit_does_not_pass(repos):
    work, wt2 = repos["work"], repos["wt2"]
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "switch", "-q", "--detach")
    tree = rev(wt2, "HEAD^{tree}")
    main = rev(wt2, "main")
    single = git(wt2, "commit-tree", tree, "-p", main, "-m", "not a merge").stdout.strip()
    git(wt2, "notes", f"--ref={GATE_NOTES_REF}", "add", "-m", "fixture", single)
    proc = git(wt2, "update-ref", "refs/heads/main", single, main, check=False)
    assert proc.returncode != 0
