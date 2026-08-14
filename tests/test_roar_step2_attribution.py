"""Class regression test for roar step 2's per-merge-request attribution (ticket 0500).

The invariant, not either symptom: **for an interval containing K merge-request
merges, roar step 2 writes K telemetry records — whatever the project name is,
and whatever reference the worktree happens to be sitting on.**

Two independent defects of `enumerate-merges.py` were found on the same day
(2026-08-14), both losing per-merge-request attribution *silently* by falling
back to the single aggregate record:

1. a project name beginning with `-` (every directory under `~/.claude/projects/`
   does) was read by argparse as an option, and step 2's `|| ROWS=""` swallowed
   the usage dump;
2. the enumeration ran to a hard-coded `HEAD`, while /roar normally runs from the
   worktree of the branch just merged — which sits on the branch tip, *below* the
   merge commit — so the merge being celebrated was missed.

Pinning either symptom leaves the other route open, so these tests drive roar's
step 2 snippet end to end (the real `enumerate-merges.py`, the real
`log-celebration`) and count the records that land in `celebrations.jsonl`.

**Positive control.** An interval with no merge-request merges makes a broken
enumerator and a correct one agree — both produce one aggregate record — so such
a test proves nothing. Every fixture here contains three known merge-request
merges and asserts three records; `test_fixture_is_a_positive_control` states
that requirement as its own check.

Note on counting: a raw merge-commit count is NOT the expected number. A
`main`→branch integration merge is legitimately skipped, because it does not sit
on the first-parent line of the default branch. The fixture below contains one
such merge on purpose: four merge commits are reachable, three are
merge-request merges.

Each test spawns real git and a real bash snippet, so the module is
integration-tier.
"""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ROAR_DIR = REPO_ROOT / "skills" / "roar"
SKILL_MD = ROAR_DIR / "SKILL.md"
ENUMERATE = ROAR_DIR / "enumerate-merges.py"
LOG_CELEBRATION = ROAR_DIR / "log-celebration"

# A real project directory name from ~/.claude/projects/. The leading dash is
# the actual directory name and stays in the record (ticket 0500 Invariants).
DASH_PROJECT = "-home-haduong--claude"

# Number of merge-request merges every fixture repo contains.
K_MERGES = 3

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(shutil.which("git") is None, reason="git required"),
]


def run(args, cwd=None, check=True, env=None):
    return subprocess.run(
        args, cwd=cwd, check=check, capture_output=True, text=True, env=env
    )


def git(repo, *args, check=True):
    return run(["git", "-C", str(repo), *args], check=check)


def head(repo, ref="HEAD"):
    return git(repo, "rev-parse", ref).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """A repo whose default branch carries K_MERGES merge-request merges.

    Layout (first-parent line of `main` reads left to right):

        C0 ──M1────────M2──────M3
              feat-1    feat-2  feat-3
                          └ carries a main→feat-2 integration merge

    feat-2 is cut before feat-1 lands, so merging main into it is a real merge
    commit rather than a fast-forward no-op.

    Reachable merge commits from main: 4. Merge-request merges: 3. The
    integration merge sits on feat-2's side, off main's first-parent line, and
    is correctly skipped — the same 16-vs-15 discrepancy observed on the real
    repo on 2026-08-14.

    An `origin` remote is wired up (bare push target) so `origin/main` exists,
    as it does in every real checkout.
    """
    r = tmp_path / "repo"
    run(["git", "init", "-b", "main", str(r)])
    git(r, "config", "user.email", "test@example.com")
    git(r, "config", "user.name", "Test")
    git(r, "config", "commit.gpgsign", "false")
    (r / "README").write_text("hi\n")
    git(r, "add", "-A")
    git(r, "commit", "-m", "init")

    def commit(name, msg):
        (r / name).write_text(f"{name}\n")
        git(r, "add", "-A")
        git(r, "commit", "-m", msg)

    # feat-2 is cut first, so that merging main into it later is a real merge.
    git(r, "switch", "-c", "feat-2")
    commit("b.txt", "work on two")

    # feat-1 — plain merge request; lands first and advances main under feat-2.
    git(r, "switch", "main")
    git(r, "switch", "-c", "feat-1")
    commit("a.txt", "work on one")
    git(r, "switch", "main")
    git(r, "merge", "--no-ff", "feat-1", "-m",
        "Merge pull request #1 from owner/feat-1")

    # feat-2 — merge request that first integrated main into itself.
    git(r, "switch", "feat-2")
    git(r, "merge", "--no-ff", "main", "-m", "Merge branch 'main' into feat-2")
    commit("b2.txt", "ticket(0500): close and archive — PR #2")
    git(r, "switch", "main")
    git(r, "merge", "--no-ff", "feat-2", "-m",
        "Merge pull request #2 from owner/feat-2")

    # feat-3 — plain merge request.
    git(r, "switch", "-c", "feat-3")
    commit("c.txt", "work on three")
    git(r, "switch", "main")
    git(r, "merge", "--no-ff", "feat-3", "-m",
        "Merge pull request #3 from owner/feat-3")

    remote = tmp_path / "remote.git"
    run(["git", "init", "--bare", "-b", "main", str(remote)])
    git(r, "remote", "add", "origin", str(remote))
    git(r, "push", "-q", "origin", "main")
    git(r, "fetch", "-q", "origin")
    return r


def base_sha(repo):
    """The initial commit — the sentinel value for an interval covering all merges."""
    return git(repo, "rev-list", "--max-parents=0", "HEAD").stdout.strip()


def write_sentinel(repo, sha, cwd=None):
    """Write the sentinel where the snippet looks for it, from the given tree.

    `--git-common-dir` must be resolved from the tree the snippet will run in: a
    linked worktree shares the main checkout's common dir, and resolving it from
    the main tree instead yields a path relative to the wrong root.
    """
    where = Path(cwd or repo)
    common = git(where, "rev-parse", "--git-common-dir").stdout.strip()
    path = (where / common).resolve() / "roar-last-sha"
    path.write_text(sha + "\n")
    return path


def step2_snippet() -> str:
    """The bash block roar's step 2 tells the agent to run."""
    blocks = re.findall(r"```bash\n(.*?)```", SKILL_MD.read_text(), re.S)
    hits = [b for b in blocks if "enumerate-merges.py" in b]
    assert len(hits) == 1, (
        f"expected exactly one step-2 telemetry snippet in {SKILL_MD}, found {len(hits)}"
    )
    return hits[0]


def render_snippet(project=DASH_PROJECT, enumerate_cmd=None) -> str:
    """Substitute the snippet's placeholders the way a running agent does."""
    s = step2_snippet()
    s = s.replace(
        "~/.claude/skills/roar/enumerate-merges.py",
        enumerate_cmd or f"{sys.executable} {ENUMERATE}",
    )
    s = s.replace("~/.claude/skills/roar/log-celebration", str(LOG_CELEBRATION))
    s = s.replace("<name>", project)
    s = s.replace("<branch>", "aggregate")
    s = s.replace("<n>", "0")
    s = s.replace("<number|null>", "null")
    assert "~/.claude" not in s, "an unsubstituted harness path would escape the fixture"
    leftover = re.findall(r"<[a-z][a-z0-9|_ -]*>", s)
    assert not leftover, f"unsubstituted placeholders: {leftover}"
    return s


def run_step2(cwd, telemetry_dir, project=DASH_PROJECT, enumerate_cmd=None):
    env = dict(os.environ)
    env["CLAUDE_TELEMETRY_DIR"] = str(telemetry_dir)
    return run(
        ["bash", "-c", render_snippet(project=project, enumerate_cmd=enumerate_cmd)],
        cwd=str(cwd),
        check=False,
        env=env,
    )


def records(telemetry_dir):
    path = Path(telemetry_dir) / "celebrations.jsonl"
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


# ── the invariant ──────────────────────────────────────────────────────────────


def test_fixture_is_a_positive_control(repo):
    """The interval must actually contain merges, or the other tests prove nothing.

    A broken enumerator and a correct one agree on an empty interval — both emit
    one aggregate record. This check is what keeps the tests below honest, and it
    also pins the counting rule: 4 merge commits are reachable, 3 of them are
    merge-request merges (the main→feat-2 integration merge is not one).
    """
    base = base_sha(repo)
    reachable = git(repo, "rev-list", "--merges", f"{base}..main").stdout.split()
    first_parent = git(
        repo, "rev-list", "--merges", "--first-parent", f"{base}..main"
    ).stdout.split()
    assert len(reachable) == K_MERGES + 1, "fixture lost its integration merge"
    assert len(first_parent) == K_MERGES, "fixture lost a merge-request merge"


def test_step2_writes_one_record_per_merge_request(repo, tmp_path):
    """Route 1: a leading-dash project name must not collapse K records into 1."""
    telemetry = tmp_path / "telemetry"
    write_sentinel(repo, base_sha(repo))
    res = run_step2(repo, telemetry)
    got = records(telemetry)
    assert len(got) == K_MERGES, f"{res.stdout}\n{res.stderr}"
    assert {r["branch"] for r in got} == {"feat-1", "feat-2", "feat-3"}
    assert {r["project"] for r in got} == {DASH_PROJECT}, "project name mangled"
    assert [r for r in got if r["ticket"] == 500], "ticket attribution lost"


def test_step2_from_a_branch_worktree_still_writes_one_record_per_merge(
    repo, tmp_path
):
    """Route 2: /roar runs from the merged branch's worktree, below the merge commit.

    The branch tip contains none of main's merge-request merges, so an
    enumeration hard-coded to HEAD returns nothing (or, here, the branch's own
    integration merge) and step 2 degrades to a single aggregate record. The
    count must be K regardless of where the worktree stands.
    """
    telemetry = tmp_path / "telemetry"
    wt = tmp_path / "branch-worktree"
    git(repo, "worktree", "add", str(wt), "feat-2")
    assert head(wt) != head(repo), "worktree must sit below the merge commit"
    write_sentinel(repo, base_sha(repo), cwd=wt)
    res = run_step2(wt, telemetry)
    got = records(telemetry)
    assert len(got) == K_MERGES, f"{res.stdout}\n{res.stderr}"
    assert {r["branch"] for r in got} == {"feat-1", "feat-2", "feat-3"}
    assert {r["project"] for r in got} == {DASH_PROJECT}


def test_step2_reports_which_reference_it_enumerated(repo, tmp_path):
    """A short enumeration must not be indistinguishable from a correct one."""
    telemetry = tmp_path / "telemetry"
    wt = tmp_path / "branch-worktree"
    git(repo, "worktree", "add", str(wt), "feat-2")
    write_sentinel(repo, base_sha(repo), cwd=wt)
    res = run_step2(wt, telemetry)
    combined = res.stdout + res.stderr
    assert "origin/main" in combined, "step 2 does not say which reference it used"


# ── the swallowed failure ──────────────────────────────────────────────────────


# Marker step 2 must print when it degrades to the single aggregate record, and
# the reason keyword that follows it. FAILED is upper-case on purpose: a lowercase
# "fail" would also match unrelated noise, and an argparse usage dump already
# contains the word "merge" — an assertion loose enough to match either would
# pass against the very defect it guards.
FALLBACK_MARKER = "aggregate fallback"
FAILED_MARKER = "FAILED"


def test_failed_enumeration_is_not_a_silent_fallback(repo, tmp_path):
    """`|| ROWS=""` must distinguish 'nothing to enumerate' from 'the call failed'.

    The legitimate fallback and the swallowed failure produce the same single
    aggregate record, so the record alone cannot tell them apart — only the
    reason step 2 prints can.
    """
    telemetry = tmp_path / "telemetry"
    write_sentinel(repo, base_sha(repo))
    stub = tmp_path / "broken-enumerate"
    stub.write_text("#!/usr/bin/env bash\necho boom >&2\nexit 1\n")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    res = run_step2(repo, telemetry, enumerate_cmd=str(stub))
    assert len(records(telemetry)) == 1, "expected the aggregate fallback"
    combined = res.stdout + res.stderr
    assert FALLBACK_MARKER in combined, "the fallback did not announce itself"
    assert FAILED_MARKER in combined, "the fallback did not say the call failed"


def test_legitimate_fallback_is_not_reported_as_a_failure(repo, tmp_path):
    """An empty interval is a legitimate fallback — and must say so, not cry failure."""
    telemetry = tmp_path / "telemetry"
    write_sentinel(repo, head(repo))  # sentinel at HEAD: nothing merged since
    res = run_step2(repo, telemetry)
    assert len(records(telemetry)) == 1
    combined = res.stdout + res.stderr
    assert FALLBACK_MARKER in combined, "the fallback did not announce itself"
    assert FAILED_MARKER not in combined, "a legitimate fallback cried failure"
    assert "no merge commits" in combined, "the fallback did not name its reason"


def test_missing_sentinel_fallback_names_its_reason(repo, tmp_path):
    """First roar in a checkout: no sentinel — a third, distinct reason."""
    telemetry = tmp_path / "telemetry"
    res = run_step2(repo, telemetry)
    assert len(records(telemetry)) == 1
    combined = res.stdout + res.stderr
    assert FALLBACK_MARKER in combined, "the fallback did not announce itself"
    assert "no sentinel" in combined, "the fallback did not name its reason"
    assert FAILED_MARKER not in combined
