"""Periodic sweep of main (ticket 1157, tracker 1045).

Each commit that entered main must be a gated merge: either it carries a gate
record (ticket 1156's note in refs/notes/gate), or it is the merge commit of a
PR whose required checks were green on the forge. The sweep reports both
facts for every commit and flags the rest. The forge is faked here; the git
side is a real scratch repository.
"""

import importlib.util
import json
import os
import re
import shutil
import sys
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "main_sweep.py"
HOOK = ROOT / "hooks" / "reference-transaction"


@pytest.fixture(scope="module")
def sweep():
    spec = importlib.util.spec_from_file_location("main_sweep", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _env():
    env = {k: v for k, v in child_env().items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="F", GIT_AUTHOR_EMAIL="f@example.invalid",
        GIT_COMMITTER_NAME="F", GIT_COMMITTER_EMAIL="f@example.invalid",
    )
    return env


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True,
        env=_env(), check=True,
    ).stdout.strip()


class FakeForge:
    def __init__(self, pulls=None, checks=None, required=(), fail=()):
        self.pulls = pulls or {}      # merge sha -> (number, head sha)
        self.checks = checks or {}    # head sha -> {name: conclusion}
        self.required = list(required)
        self.fail = set(fail)

    def merged_pull(self, sha):
        if sha in self.fail:
            raise self.error("forge unreachable")
        if sha in self.pulls:
            number, head = self.pulls[sha]
            return {"number": number, "head_sha": head}, []
        return None, []

    def check_conclusions(self, head_sha):
        return dict(self.checks.get(head_sha, {}))

    def required_checks(self):
        return self.required, "fixture"


@pytest.fixture
def repo(tmp_path, sweep):
    FakeForge.error = sweep.ForgeError
    r = tmp_path / "r"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    shas = {}
    for name in ("base", "gated", "green", "red", "direct", "unknown"):
        git(r, "commit", "-q", "--allow-empty", "-m", name)
        shas[name] = git(r, "rev-parse", "HEAD")
    return r, shas


def _forge(shas):
    return FakeForge(
        pulls={
            shas["green"]: (11, "h-green"),
            shas["red"]: (12, "h-red"),
        },
        checks={
            "h-green": {"pytest-guard": "success", "validate-tickets": "success"},
            "h-red": {"pytest-guard": "failure", "validate-tickets": "success"},
        },
        required=["pytest-guard", "validate-tickets"],
        fail=[shas["unknown"]],
    )


def test_gate_notes_ref_is_shared_with_the_hook(sweep):
    hook_ref = re.search(r"^GATE_NOTES_REF=(\S+)", HOOK.read_text(), re.M).group(1)
    assert sweep.GATE_NOTES_REF == hook_ref == "refs/notes/gate"


def test_each_commit_is_classified_and_both_facts_reported(repo, sweep):
    r, shas = repo
    # Fixture stand-in for ticket 1156's record writer.
    git(r, "notes", f"--ref={sweep.GATE_NOTES_REF}", "add", "-m", "fixture record", shas["gated"])
    results = {res["subject"]: res for res in sweep.sweep(
        r, sweep.first_parent_commits(r, "main", max_count=5), _forge(shas))}
    assert set(results) == {"gated", "green", "red", "direct", "unknown"}
    assert results["gated"]["status"] == "ok" and results["gated"]["gate_record"]
    assert results["green"]["status"] == "ok" and results["green"]["pr"] == 11
    assert results["green"]["gate_record"] is False
    assert results["green"]["checks"] == "green"
    assert results["red"]["status"] == "finding"
    assert "pytest-guard" in results["red"]["reason"]
    assert results["direct"]["status"] == "finding"
    assert "no merged PR" in results["direct"]["reason"]
    assert results["unknown"]["status"] == "unknown"


def test_a_gate_record_stands_even_when_the_forge_cannot_be_read(repo, sweep):
    r, shas = repo
    git(r, "notes", f"--ref={sweep.GATE_NOTES_REF}", "add", "-m", "fixture", shas["unknown"])
    [res] = sweep.sweep(r, [shas["unknown"]], _forge(shas))
    assert res["status"] == "ok" and res["gate_record"]
    assert res["checks"] == "unknown"


def test_a_missing_required_check_is_not_green(repo, sweep):
    r, shas = repo
    forge = _forge(shas)
    forge.checks["h-green"].pop("validate-tickets")
    [res] = sweep.sweep(r, [shas["green"]], forge)
    assert res["status"] == "finding" and "validate-tickets" in res["reason"]


def test_without_a_required_list_every_run_must_pass(repo, sweep):
    r, shas = repo
    forge = _forge(shas)
    forge.required = []
    [green] = sweep.sweep(r, [shas["green"]], forge)
    [red] = sweep.sweep(r, [shas["red"]], forge)
    assert green["status"] == "ok" and red["status"] == "finding"


def test_exit_code_separates_findings_from_could_not_look(sweep):
    assert sweep.exit_code([{"status": "ok"}]) == 0
    assert sweep.exit_code([{"status": "ok"}, {"status": "unknown"}]) == 2
    assert sweep.exit_code([{"status": "unknown"}, {"status": "finding"}]) == 1
    assert sweep.exit_code([]) == 2  # an empty sweep looked at nothing
    assert sweep.exit_code([{"status": "ok"}], ["range cut"]) == 2
    assert sweep.exit_code([{"status": "finding"}], ["range cut"]) == 1


def test_report_names_every_finding(repo, sweep):
    r, shas = repo
    results = sweep.sweep(r, [shas["red"], shas["direct"]], _forge(shas))
    text = sweep.render(results, "fixture")
    assert shas["red"][:12] in text and shas["direct"][:12] in text
    assert json.loads(sweep.render(results, "fixture", as_json=True))["results"]


def _cli(repo, *args, path=None):
    env = _env()
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
        capture_output=True, text=True, env=env,
    )


def test_no_tools_on_path_is_could_not_look(repo):
    r, _ = repo
    proc = _cli(r, "--ref", "main", path="")
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_an_unknown_ref_is_could_not_look(repo):
    r, _ = repo
    proc = _cli(r, "--ref", "origin/main", "--required", "x")
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_a_failed_fetch_is_could_not_look(repo):
    r, _ = repo  # no origin remote: the fetch fails
    proc = _cli(r, "--fetch", "--ref", "main", "--required", "x")
    assert proc.returncode == 2
    assert "fetch" in proc.stderr


def test_malformed_forge_output_is_could_not_look(repo, tmp_path):
    r, _ = repo
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "gh"
    fake.write_text("#!/bin/sh\necho 'not json'\n")
    fake.chmod(0o755)
    gitdir = str(Path(shutil.which("git")).parent)
    proc = _cli(r, "--ref", "main", "--max-count", "3", path=f"{bindir}:{gitdir}")
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "finding " not in proc.stdout


def test_a_range_cut_by_max_count_is_not_an_all_clear(repo, sweep):
    r, shas = repo
    green = {sha: (n, "h-green") for n, sha in enumerate(shas.values())}
    forge = FakeForge(pulls=green, checks={"h-green": {"c": "success"}}, required=["c"])
    args = sweep.parse_args(["--repo", str(r), "--ref", "main", "--max-count", "3"])
    assert sweep.run(args, forge) == 2
    args = sweep.parse_args(["--repo", str(r), "--ref", "main", "--max-count", "50"])
    assert sweep.run(args, forge) == 0
