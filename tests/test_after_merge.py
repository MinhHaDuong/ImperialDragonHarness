"""After-merge runner: the full set on the newest main tip, in the background (ticket 1244).

`merge-gate.py run-after` takes a host-local flock, runs the declared checks
on the current origin tip, writes the record as a note on that tip under an
after-merge scope line, refetches and loops while main moves. On red it
prints the ticket text and exits 1; given a forge (`--open-ticket`, ticket
1251) it also opens and lands that ticket, deduped on the failing-check set.
`main_sweep.py --after` reports tips with no after-merge record and runs the
set on the latest one. Real git, real processes, a bare origin; the forge is
a stub that merges into that origin, and the lock is never mocked.
"""

import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "merge-gate.py"
SWEEP = ROOT / "scripts" / "main_sweep.py"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=child_env()
    ).stdout.strip()


def run_after(cwd, *args, **kw):
    return subprocess.Popen(
        [sys.executable, str(GATE), "run-after", "--ref", "main", *args],
        cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=child_env(), **kw,
    )


def finish(proc, timeout=60):
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


@pytest.fixture
def module():
    spec = importlib.util.spec_from_file_location("merge_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_repo(tmp_path, checks):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True, env=child_env())
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True, env=child_env())
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture"), ("commit.gpgsign", "false")):
        git(work, "config", key, value)
    config = {"gate": "on", "scope": "fixture-set", "checks": checks}
    (work / ".merge-gate.json").write_text(json.dumps(config), encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "base")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    return work


def merge_branch(work, name, files=None):
    """A --no-ff merge of a one-commit branch into main, pushed: one 'merge' on main."""
    git(work, "switch", "-q", "-c", name, "main")
    for path, text in (files or {name + ".txt": name}).items():
        (work / path).write_text(text + "\n", encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", name)
    git(work, "switch", "-q", "main")
    git(work, "merge", "-q", "--no-ff", name, "-m", f"Merge {name}")
    git(work, "push", "-q", "origin", "main")
    return git(work, "rev-parse", "HEAD")


def note(work, oid):
    proc = subprocess.run(
        ["git", "-C", str(work), "notes", "--ref=refs/notes/gate", "show", oid],
        capture_output=True, text=True, env=child_env(),
    )
    return proc.stdout if proc.returncode == 0 else ""


def wait_for_lines(path, n, proc, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists() and len(path.read_text().splitlines()) >= n:
            return
        if proc.poll() is not None:
            raise AssertionError(f"runner exited {proc.returncode} first: {proc.communicate()}")
        time.sleep(0.05)
    raise AssertionError(f"{path} never reached {n} line(s)")


def logging_checks(log, pause):
    return [{"name": "log-tip", "argv": ["sh", "-c", f"git rev-parse HEAD >> {log}; sleep {pause}"]}]


def test_three_quick_merges_run_at_most_twice(tmp_path, module):
    log = tmp_path / "runs.log"
    work = make_repo(tmp_path, logging_checks(log, 3))
    first = run_after(work)
    wait_for_lines(log, 1, first)  # run 1 holds the lock, on the first tip
    merge_branch(work, "two")
    second = run_after(work)
    merge_branch(work, "three")
    third = run_after(work)
    final = git(work, "rev-parse", "origin/main")
    for proc in (second, third):
        code, out, err = finish(proc)
        assert code == 0, err
        assert "busy" in out, out + err
    code, out, err = finish(first)
    assert code == 0, out + err
    runs = log.read_text().splitlines()
    assert len(runs) <= 2, runs
    assert runs[-1] == final
    git(work, "fetch", "-q", "origin", "+refs/notes/gate:refs/notes/gate")
    entries = module.parse_note(note(work, final))
    assert [e["result"] for e in entries] == ["pass"]
    assert entries[0]["scope"] == "fixture-set/after-merge: log-tip"
    assert f"tip={final}" in entries[0]["revision"]


def test_an_after_record_is_never_taken_for_a_before_merge_one(tmp_path, module):
    work = make_repo(tmp_path, [{"name": "ok", "argv": ["true"]}])
    git(work, "switch", "-q", "-c", "feature")
    (work / "f.txt").write_text("f\n", encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "feature")
    git(work, "switch", "-q", "main")
    tip = git(work, "rev-parse", "main")
    code, out, err = finish(run_after(work))
    assert code == 0, out + err
    entries = module.parse_note(note(work, tip))
    config = json.loads((work / ".merge-gate.json").read_text())
    # Even keyed on the very object `decide` is asked about, the after-record neither matches nor fits a scope.
    cwd = os.getcwd()
    os.chdir(work)
    try:
        module.candidate(tip, git(work, "rev-parse", "feature"))
        scopes = module.accepted_scopes(config)
    finally:
        os.chdir(cwd)
    assert module.decide(entries, tip, scopes)[0] == module.MISSING
    assert entries[0]["scope"] not in scopes


def test_a_killed_runner_leaves_no_lock_behind(tmp_path):
    log = tmp_path / "runs.log"
    work = make_repo(tmp_path, logging_checks(log, 60))
    holder = run_after(work, start_new_session=True)
    wait_for_lines(log, 1, holder)
    busy = finish(run_after(work))
    assert "busy" in busy[1], busy
    os.killpg(holder.pid, signal.SIGKILL)
    holder.wait(timeout=10)
    log.write_text("")
    (work / ".merge-gate.json").write_text(
        json.dumps({"gate": "on", "scope": "s", "checks": logging_checks(log, 0)}), encoding="utf-8"
    )
    git(work, "commit", "-q", "-am", "quick check")
    git(work, "push", "-q", "origin", "main")
    code, out, err = finish(run_after(work))
    assert code == 0, out + err
    assert "busy" not in out
    assert log.read_text().splitlines() == [git(work, "rev-parse", "origin/main")]


def test_a_red_run_prints_the_ticket_text_and_exits_non_zero(tmp_path, module):
    checks = [
        {"name": "always-pass", "argv": ["true"]},
        {"name": "marker-absent", "argv": ["sh", "-c", "! test -e BROKEN"]},
    ]
    work = make_repo(tmp_path, checks)
    green = git(work, "rev-parse", "main")
    assert finish(run_after(work))[0] == 0
    first = merge_branch(work, "harmless")
    tip = merge_branch(work, "breaker", {"BROKEN": "planted failure"})
    code, out, err = finish(run_after(work))
    assert code == 1, out + err
    report = out[out.index("Title:"):]
    assert tip in report
    assert "Failing checks: marker-absent" in report
    assert "always-pass" not in report.split("Failing checks:", 1)[1].split("\n", 1)[0]
    assert f"Last green after-merge tip: {green}" in report
    for merge in (first, tip):
        assert merge[:12] in report
    assert green[:12] not in report.split("Merges since", 1)[1]
    assert [e["result"] for e in module.parse_note(note(work, tip))] == ["fail"]
    remote_branches = git(work, "ls-remote", "origin", "refs/heads/*").splitlines()
    assert len(remote_branches) == 1  # no forge write: only main on origin


def audit(work, *args):
    return subprocess.run(
        [sys.executable, str(SWEEP), "--ref", "main", *args],
        cwd=work, capture_output=True, text=True, env=child_env(),
    )


def test_the_audit_lists_tips_without_an_after_record_and_runs_the_latest(tmp_path, module):
    work = make_repo(tmp_path, [{"name": "ok", "argv": ["true"]}])
    merge_branch(work, "covered")
    assert finish(run_after(work))[0] == 0
    covered = git(work, "rev-parse", "main")
    gap1 = merge_branch(work, "gap-one")
    gap2 = merge_branch(work, "gap-two")
    proc = audit(work, "--after")
    gaps = [line.split()[1] for line in proc.stdout.splitlines() if line.startswith("after-gap")]
    assert gaps == [gap2[:12], gap1[:12]], proc.stdout + proc.stderr
    assert covered[:12] not in gaps
    assert f"; ran on {gap2[:12]}: green" in proc.stdout
    git(work, "fetch", "-q", "origin", "+refs/notes/gate:refs/notes/gate")
    assert [e["result"] for e in module.parse_note(note(work, gap2))] == ["pass"]
    again = audit(work, "--after")
    assert not [line for line in again.stdout.splitlines() if line.startswith("after-gap")], again.stdout


def test_an_after_record_alone_does_not_vouch_for_a_direct_commit(tmp_path):
    work = make_repo(tmp_path, [{"name": "ok", "argv": ["true"]}])
    (work / "direct.txt").write_text("d\n", encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "direct")
    git(work, "push", "-q", "origin", "main")
    direct = git(work, "rev-parse", "main")
    assert finish(run_after(work))[0] == 0
    proc = audit(work)
    [line] = [x for x in proc.stdout.splitlines() if direct[:12] in x]
    assert line.startswith("finding"), proc.stdout


def test_the_audit_summary_with_after_stays_one_line_over_noisy_checks(tmp_path):
    work = make_repo(tmp_path, [{"name": "noisy", "argv": ["sh", "-c", "echo NOISY-OUT; echo NOISY-ERR >&2"]}])
    merge_branch(work, "gap")
    proc = audit(work, "--after", "--summary")
    assert "NOISY" not in proc.stdout + proc.stderr
    assert len(proc.stdout.splitlines()) == 1, proc.stdout
    assert "ran on" in proc.stdout


def step9_snippet():
    """The fenced bash of skills/merge/SKILL.md step 9, as the merging session runs it."""
    text = (ROOT / "skills" / "merge" / "SKILL.md").read_text(encoding="utf-8")
    step = text[text.index("9. **After-merge run"):]
    return step.split("```bash\n", 1)[1].split("```", 1)[0]


@pytest.mark.parametrize("layout", ["bare", "non-bare"])
def test_step9_starts_the_runner_from_a_linked_worktree(tmp_path, module, layout):
    seed = make_repo(tmp_path, [{"name": "ok", "argv": ["true"]}])
    origin = tmp_path / "origin.git"
    if layout == "bare":
        primary = tmp_path / "proj.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(origin), str(primary)], check=True, env=child_env())
    else:
        primary = seed
    linked = tmp_path / "request-wt"
    git(primary, "worktree", "add", "-q", "-b", "request", str(linked), "main")
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture")):
        git(primary, "config", key, value)
    env = {**child_env(), "IDH_ROOT": str(ROOT)}
    script = step9_snippet().replace("<base>", "main")
    subprocess.run(["bash", "-c", script], cwd=linked, check=True, env=env)
    common = Path(git(linked, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    log = common / "idh" / "after-merge.log"
    end = time.monotonic() + 30
    while time.monotonic() < end and "pass: after-merge record" not in (log.read_text() if log.exists() else ""):
        time.sleep(0.1)
    assert "pass: after-merge record" in log.read_text(), log.read_text()
    tip = git(primary, "rev-parse", "main")
    git(seed, "fetch", "-q", "origin", "+refs/notes/gate:refs/notes/gate")
    assert [e["result"] for e in module.parse_note(note(seed, tip))] == ["pass"]


# ── ticket 1251: a red after-merge record opens a ticket through a ticket-only PR ──

ERG = ROOT / "tickets" / "erg"
RED_CHECKS = [
    {"name": "always-pass", "argv": ["true"]},
    {"name": "marker-absent", "argv": ["sh", "-c", "! test -e BROKEN"]},
    {"name": "second-marker-absent", "argv": ["sh", "-c", "! test -e BROKEN2"]},
]


class MergingForge:
    """Stub forge: `create` opens a request on a pushed branch; `merge` merges it into the bare origin."""

    def __init__(self, origin, scratch, refuse=None):
        self.origin, self.scratch, self.refuse = origin, scratch, refuse
        self.prs, self.merged, self.calls = {}, set(), []

    def create(self, branch, base, title, body):
        number = str(len(self.prs) + 1)
        self.prs[number] = {"branch": branch, "base": base, "title": title, "body": body}
        self.calls.append(("create", branch))
        return number

    def _head(self, pr):
        refs = git(self.origin, "for-each-ref", "--format=%(objectname)", f"refs/heads/{self.prs[pr]['branch']}")
        return refs.strip()

    def resolve(self, pr):
        info = self.prs[pr]
        return {"state": "MERGED" if pr in self.merged else "OPEN", "isDraft": False,
                "headRefName": info["branch"], "baseRefName": info["base"],
                "headRefOid": self._head(pr), "body": info["body"]}

    def ready(self, pr):
        pass

    def auto_merge_armed(self, pr):
        return False

    def disarm(self, pr):
        pass

    def merge(self, pr, head, auto):
        self.calls.append(("merge", pr))
        if self.refuse:
            raise self.refuse("stub: merge refused")
        if not self.scratch.exists():
            subprocess.run(["git", "clone", "-q", str(self.origin), str(self.scratch)], check=True, env=child_env())
            for key, value in (("user.email", "f@example.com"), ("user.name", "Forge")):
                git(self.scratch, "config", key, value)
        git(self.scratch, "fetch", "-q", "origin")
        git(self.scratch, "checkout", "-q", "-B", "main", "origin/main")
        git(self.scratch, "merge", "-q", "--no-ff", head, "-m", f"Merge pull request #{pr}")
        git(self.scratch, "push", "-q", "origin", "main")
        self.merged.add(pr)

    def read_back(self, pr):
        state = "MERGED" if pr in self.merged else "OPEN"
        return f"{state} {self._head(pr)} -"

    def comment(self, pr, body):
        pass


@pytest.fixture
def red_repo(tmp_path, monkeypatch, module):
    """A gated temp main whose before set is cheap (ticket 1245); HOME is a temp dir."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    work = make_repo(tmp_path, RED_CHECKS)
    config = json.loads((work / ".merge-gate.json").read_text())
    config["before"] = ["always-pass"]
    (work / ".merge-gate.json").write_text(json.dumps(config), encoding="utf-8")
    git(work, "commit", "-q", "-am", "before set")
    git(work, "push", "-q", "origin", "main")
    monkeypatch.chdir(work)
    return work


def run_after_in_process(module, forge):
    return module.run_after("origin", "main", "runtime=fixture", "merge-gate run-after", forge=forge)


def red_tickets(work, ref="origin/main"):
    git(work, "fetch", "-q", "origin")
    names = git(work, "ls-tree", "--name-only", f"{ref}:tickets").splitlines() if ref else []
    return [n for n in names if "-after-merge-red-" in n]


def remote_red_branches(work):
    return [line.split()[1] for line in git(work, "ls-remote", "origin", "refs/heads/red-*").splitlines()]


def test_a_red_record_opens_one_ticket_and_a_second_red_run_opens_none(red_repo, module, tmp_path):
    work = red_repo
    green = git(work, "rev-parse", "main")
    assert run_after_in_process(module, None) == module.PASS
    first = merge_branch(work, "harmless")
    tip = merge_branch(work, "breaker", {"BROKEN": "planted failure"})
    forge = MergingForge(tmp_path / "origin.git", tmp_path / "forge-scratch")
    assert run_after_in_process(module, forge) == module.FAIL
    [name] = red_tickets(work)
    assert name.endswith(f"-after-merge-red-{tip[:12]}.erg"), name
    text = git(work, "show", f"origin/main:tickets/{name}")
    assert tip in text and "Failing checks: marker-absent\n" in text
    assert f"Last green after-merge tip: {green}" in text
    for merge in (first, tip):
        assert merge[:12] in text
    tree = tmp_path / "check-tree"
    git(work, "worktree", "add", "-q", "--detach", str(tree), "origin/main")
    proc = subprocess.run([str(ERG), "check", str(tree / "tickets")], capture_output=True, text=True,
                          env=child_env())
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert remote_red_branches(work) == []  # landed: the branch is gone, the open ticket carries the set
    # Second red run on the same failure: main moved (a harmless merge), the failing set did not.
    merge_branch(work, "unrelated")
    assert run_after_in_process(module, forge) == module.FAIL
    assert len(red_tickets(work)) == 1
    assert [c for c in forge.calls if c[0] == "create"] == [("create", f"red-{tip[:12]}")]


def test_an_unlanded_red_branch_dedupes_and_landing_is_bounded(red_repo, module, tmp_path):
    work = red_repo
    merge_branch(work, "breaker", {"BROKEN": "planted failure"})
    lander = module.raid_land()
    forge = MergingForge(tmp_path / "origin.git", tmp_path / "forge-scratch", refuse=lander.MergeRefused)
    assert run_after_in_process(module, forge) == module.FAIL
    merges = [c for c in forge.calls if c[0] == "merge"]
    assert 1 <= len(merges) <= module.RED_RETRIES, forge.calls
    assert len(remote_red_branches(work)) == 1  # left open for a human, carrying the set
    merge_branch(work, "unrelated")
    assert run_after_in_process(module, forge) == module.FAIL
    assert len([c for c in forge.calls if c[0] == "create"]) == 1, forge.calls


def test_a_different_failing_set_opens_its_own_ticket(red_repo, module, tmp_path):
    work = red_repo
    merge_branch(work, "breaker", {"BROKEN": "planted failure"})
    forge = MergingForge(tmp_path / "origin.git", tmp_path / "forge-scratch")
    assert run_after_in_process(module, forge) == module.FAIL
    assert len(red_tickets(work)) == 1
    git(work, "pull", "-q", "--ff-only", "origin", "main")
    merge_branch(work, "breaker2", {"BROKEN2": "second planted failure"})
    assert run_after_in_process(module, forge) == module.FAIL
    tickets = red_tickets(work)
    assert len(tickets) == 2, tickets
    texts = [git(work, "show", f"origin/main:tickets/{n}") for n in tickets]
    assert any("Failing checks: marker-absent, second-marker-absent\n" in t for t in texts)
