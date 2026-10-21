"""Forge CI triggers (ticket 1174).

The full workflow runs on push to main (the ex-post record) and by hand
(workflow_dispatch), never on pull_request. The one PR-only job, the cross-PR
ticket-ID collision check, lives in its own small workflow triggered by
pull_request. The local runners must invoke each workflow through a trigger it
still accepts, which `act -l` checks without a container.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from child_env import child_env

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
CI = WORKFLOWS / "CI.yml"
COLLISION = WORKFLOWS / "ticket-collision.yml"


def _load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text())
    # PyYAML reads the bare key `on` as the boolean True.
    doc["on"] = doc.pop(True, doc.get("on"))
    return doc


def test_full_workflow_runs_on_push_to_main_and_by_hand_only():
    on = _load(CI)["on"]
    assert set(on) == {"push", "workflow_dispatch"}, on
    assert on["push"] == {"branches": ["main"]}


def test_full_workflow_has_no_pull_request_only_job():
    jobs = _load(CI)["jobs"]
    assert "cross-pr-ticket-collision" not in jobs
    assert "pull_request" not in CI.read_text().split("jobs:", 1)[1]


def test_collision_check_runs_on_pull_requests_in_its_own_workflow():
    doc = _load(COLLISION)
    assert set(doc["on"]) == {"pull_request"}
    assert list(doc["jobs"]) == ["cross-pr-ticket-collision"]
    steps = doc["jobs"]["cross-pr-ticket-collision"]["steps"]
    assert any("check-cross-pr-ticket-collision.sh" in s.get("run", "") for s in steps)


@pytest.mark.parametrize(
    "runner", ["scripts/local-ci.sh", "scripts/local-ci-negative-controls.sh"]
)
def test_local_runners_never_send_a_pull_request_to_the_full_workflow(runner):
    # The full workflow is run under workflow_dispatch; a pull_request event
    # would now select none of its jobs.
    text = (ROOT / runner).read_text()
    assert "workflow_dispatch" in text


@pytest.mark.integration
@pytest.mark.skipif(not shutil.which("act"), reason="act is required")
@pytest.mark.parametrize(
    ("workflow", "event", "expected"),
    [
        (CI, "workflow_dispatch", None),
        (CI, "pull_request", set()),
        (COLLISION, "pull_request", {"cross-pr-ticket-collision"}),
    ],
)
def test_act_selects_the_jobs_each_trigger_should(workflow, event, expected):
    out = subprocess.run(
        ["act", event, "-l", "-W", str(workflow)],
        capture_output=True, text=True, cwd=ROOT, check=True, env=child_env(),
    ).stdout
    listed = {line.split()[1] for line in out.splitlines()[1:] if line.split()}
    if expected is None:
        expected = set(_load(workflow)["jobs"])
    assert listed == expected, out
