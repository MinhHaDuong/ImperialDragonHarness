"""Erg ID claims replace the cross-PR collision gate (ticket 1472).

Scratch store, vendored binary: two clones that each take the next ticket
number with `erg new` on their own branch conflict add/add on
tickets/.claims/NNNN when the second branch merges, offline, with no forge.
Two clones, not two branches of one clone: erg new already steps past a
number another local branch holds, so the collision that needs the claim is
the one between checkouts that cannot see each other.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parent.parent
ERG = ROOT / "tickets" / "erg"

pytestmark = pytest.mark.integration


def run(cwd, *args, check=True):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=child_env())
    if check:
        assert proc.returncode == 0, f"{args}: {proc.stdout}\n{proc.stderr}"
    return proc


def test_two_clones_taking_one_number_conflict_on_its_claim(tmp_path):
    repo = tmp_path / "repo"
    (repo / "tickets" / ".claims").mkdir(parents=True)
    (repo / "tickets" / ".claims" / ".keep").write_text("", encoding="utf-8")
    shutil.copy2(ERG, repo / "tickets" / "erg")
    run(repo, "git", "init", "-q", "-b", "main")
    run(repo, "git", "add", "-A")
    run(repo, "git", "-c", "user.email=t@example.com", "-c", "user.name=Test", "-c", "core.hooksPath=/dev/null",
        "commit", "-q", "-m", "claims store")

    other = tmp_path / "other"
    run(tmp_path, "git", "clone", "-q", str(repo), str(other))  # cloned before either number is taken
    for clone in (repo, other):
        for key, value in (("user.email", "t@example.com"), ("user.name", "Test"), ("core.hooksPath", "/dev/null")):
            run(clone, "git", "config", key, value)
    for clone, branch, title in ((repo, "a", "First take"), (other, "b", "Second take")):
        run(clone, "git", "switch", "-q", "-c", branch)
        run(clone, "tickets/erg", "new", title, "tickets", "--author", "test")
        run(clone, "git", "add", "tickets")
        run(clone, "git", "commit", "-q", "-m", title)
    run(repo, "git", "fetch", "-q", str(other), "b:b")
    claim_a = run(repo, "git", "show", "a:tickets/.claims/0001").stdout
    claim_b = run(repo, "git", "show", "b:tickets/.claims/0001").stdout
    assert claim_a != claim_b  # the nonce differs, so the same path cannot merge clean

    run(repo, "git", "switch", "-q", "main")
    run(repo, "git", "merge", "-q", "--no-ff", "a", "-m", "land a")
    second = run(repo, "git", "merge", "--no-ff", "b", "-m", "land b", check=False)
    assert second.returncode != 0, second.stdout
    assert "CONFLICT (add/add)" in second.stdout and "tickets/.claims/0001" in second.stdout, second.stdout
    unmerged = run(repo, "git", "diff", "--name-only", "--diff-filter=U").stdout.split()
    assert "tickets/.claims/0001" in unmerged
