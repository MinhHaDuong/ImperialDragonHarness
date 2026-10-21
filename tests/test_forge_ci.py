"""The forge's check conclusion spares a full run only when green for the exact head.

Ticket 1172: /gaze and /verify-gate read the forge's conclusion for the head
they review. Green for that head means a targeted run; anything else (older
head, pending, failed, missing, unreadable) means the full run, never a skip.
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "forge_ci.py"
SPEC = importlib.util.spec_from_file_location("forge_ci", SCRIPT)
fc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fc)

HEAD = "a" * 40
OLDER = "b" * 40
WF = ".github/workflows/CI.yml"


def run(head=HEAD, status="completed", conclusion="success", path=WF, rid=1,
        created="2026-10-21T10:00:00Z"):
    return {"id": rid, "head_sha": head, "status": status, "conclusion": conclusion,
            "path": path, "created_at": created}


def verdict(*runs):
    return fc.classify({"workflow_runs": list(runs)}, HEAD, WF)


def test_positive_control_green_for_this_head():
    assert verdict(run())[0] == "green"


@pytest.mark.parametrize("runs, why", [
    ([run(head=OLDER)], "missing"),                       # green, but for an older head
    ([run(status="in_progress", conclusion=None)], "pending"),
    ([run(status="queued", conclusion=None)], "pending"),
    ([run(conclusion="failure")], "failure"),
    ([run(conclusion="cancelled")], "cancelled"),
    ([], "missing"),
    ([run(path=".github/workflows/other.yml")], "missing"),  # another workflow only
])
def test_negative_controls_are_not_green(runs, why):
    assert verdict(*runs)[:2] == ("not-green", why)


def test_latest_run_for_the_head_decides():
    old_green = run(rid=1, created="2026-10-21T10:00:00Z")
    new_pending = run(rid=2, status="in_progress", conclusion=None,
                      created="2026-10-21T11:00:00Z")
    assert verdict(old_green, new_pending)[0] == "not-green"
    assert verdict(new_pending | {"status": "completed", "conclusion": "success"},
                   run(rid=1, conclusion="failure"))[0] == "green"


def test_unreadable_payload_is_not_green():
    assert fc.classify({"nope": []}, HEAD, WF)[:2] == ("not-green", "unreadable")


def _fake_forge(tmp_path, stdout, code=0):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "gh"
    fake.write_text(f"#!/bin/sh\ncat <<'EOF'\n{stdout}\nEOF\nexit {code}\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = child_env()
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    return env


def _status(env, head=HEAD):
    return subprocess.run([sys.executable, str(SCRIPT), "status", "o/n", head,
                           "--workflow", WF], capture_output=True, text=True, env=env)


@pytest.mark.integration
def test_cli_reports_what_it_read(tmp_path):
    out = _status(_fake_forge(tmp_path, json.dumps({"workflow_runs": [run(rid=7)]})))
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == f"forge_ci: green workflow={WF} head={HEAD} conclusion=success run=7"


@pytest.mark.integration
def test_cli_failed_read_is_not_green(tmp_path):
    out = _status(_fake_forge(tmp_path, "", code=1))
    assert out.returncode == 1
    assert "not-green" in out.stdout and "conclusion=unreadable" in out.stdout


@pytest.mark.integration
def test_cli_refuses_an_abbreviated_head(tmp_path):
    out = _status(_fake_forge(tmp_path, json.dumps({"workflow_runs": [run()]})), head="a" * 12)
    assert out.returncode == 2


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env=child_env())


@pytest.mark.integration
def test_targets_lists_tests_naming_a_changed_path(tmp_path):
    repo = tmp_path / "r"
    (repo / "tests").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "skills" / "gaze").mkdir(parents=True)
    (repo / "scripts" / "tool.py").write_text("x = 1\n")
    (repo / "skills" / "gaze" / "SKILL.md").write_text("gaze\n")
    (repo / "tests" / "test_tool.py").write_text("# exercises scripts/tool.py\n")
    (repo / "tests" / "test_gaze.py").write_text("P = ROOT / 'skills' / 'gaze'\n")
    (repo / "tests" / "test_other.py").write_text("# unrelated\n")
    (repo / "tests" / "helper.py").write_text("# names tool.py but is no test\n")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base",
         "--allow-empty")
    base = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True, env=child_env()).stdout.strip()
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "change")
    out = subprocess.run([sys.executable, str(SCRIPT), "targets", base, "--repo-dir", str(repo)],
                         capture_output=True, text=True, env=child_env())
    assert out.returncode == 0, out.stderr
    picked = out.stdout.split()
    assert "tests/test_tool.py" in picked and "tests/test_gaze.py" in picked
    assert "tests/test_other.py" in picked  # a changed test file runs itself
    assert "tests/helper.py" not in picked



def test_skills_route_the_full_run_through_the_helper():
    """The rule lives once, in review-pr's run-tests step; gaze and gate point to it."""
    review = (ROOT / "skills/review-pr/SKILL.md").read_text()
    assert "forge_ci.py\" status" in review and "forge_ci.py\" targets" in review
    for rel in ("skills/verify-gate/SKILL.md", "skills/gaze/references/setup-and-breaker.md"):
        text = (ROOT / rel).read_text()
        assert "review-pr` § Synthesis step 4" in text, rel
        assert "forge_ci.py\" status" not in text, f"{rel} restates the rule"
    for rel in ("skills/gaze/SKILL.md", "skills/gaze/references/output.md",
                "skills/verify-gate/SKILL.md"):
        assert "forge_ci:" in (ROOT / rel).read_text(), f"{rel} does not report what it read"
