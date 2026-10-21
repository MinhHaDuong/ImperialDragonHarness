"""/merge refuses without a gate record on the candidate (ticket 1156).

Drives the real skills/merge/erg-pr-merge against a fixture repository with a
bare origin whose base carries `.merge-gate.json`, and a stub forge CLI that
logs merge calls. Negative control: no record, no merge call. Positive control:
after `merge-gate.py run`, the helper merges with the head pinned and without
arming forge auto-merge (which, with no required checks, would merge at once).
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
HELPER = ROOT / "skills" / "merge" / "erg-pr-merge"
GATE = ROOT / "scripts" / "merge-gate.py"
CONFIG = {"gate": "on", "scope": "fixture-set", "checks": [{"name": "always-pass", "argv": ["true"]}]}

GREEN = '[{"status":"COMPLETED","conclusion":"SUCCESS"}]'
TICKET = """%erg 0.1
Title: Fixture ticket
Created: 2026-10-21
Author: test

--- log ---
2026-10-21T00:00Z test created

--- body ---
## Context
Fixture.
"""

GH_STUB = r"""#!/usr/bin/env bash
set -euo pipefail
args="$*"
case "$1 $2" in
  "pr view")
    if [[ "$args" == *"--json autoMergeRequest"* ]]; then
      if [[ -n "${STUB_ARMED:-}" && ! -e "$STUB_DIR/disarmed" ]]; then echo yes; else echo no; fi; exit 0
    fi
    if [[ "$args" == *"autoMergeRequest"* ]]; then echo no; exit 0; fi
    if [[ "$args" == *"--jq"* && "$args" == *"state"* ]]; then echo "${STUB_STATE:-MERGED}"; exit 0; fi
    jq -n --arg h "$STUB_BRANCH" --arg body "${STUB_BODY:-Ticket: none}" --argjson r "${STUB_ROLLUP:-[]}" \
      '{number:42,headRefName:$h,baseRefName:"main",mergeable:"MERGEABLE",statusCheckRollup:$r,body:$body,isDraft:false,title:"fixture"}'
    exit 0 ;;
  "pr merge")
    if [[ "$args" == *"--disable-auto"* ]]; then
      echo "$args" >> "$STUB_DIR/disarm.log"
      [[ "${STUB_DISARM_FAILS:-0}" == 1 ]] && exit 1
      : > "$STUB_DIR/disarmed"; exit 0
    fi
    echo "$args" >> "$STUB_DIR/merge.log"; exit 0 ;;
  *) echo "stub gh: unexpected: $args" >&2; exit 1 ;;
esac
"""


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=child_env()
    ).stdout.strip()


@pytest.fixture
def fixture(tmp_path):
    origin, work, stub = tmp_path / "origin.git", tmp_path / "work", tmp_path / "bin"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, env=child_env())
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True, env=child_env())
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture"), ("commit.gpgsign", "false")):
        git(work, "config", key, value)
    (work / ".merge-gate.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    (work / "tickets").mkdir()
    shutil.copy(ROOT / "tickets" / "erg", work / "tickets" / "erg")
    (work / "tickets" / "0001-fixture.erg").write_text(TICKET, encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "base")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-q", "-c", "feature")
    (work / "b.txt").write_text("b\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "feature")
    git(work, "push", "-q", "-u", "origin", "feature")
    stub.mkdir()
    (stub / "gh").write_text(GH_STUB, encoding="utf-8")
    (stub / "gh").chmod(0o755)
    return work, stub


def merge(work, stub, *args, **env):
    full = {
        **child_env(),
        "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}",
        "STUB_DIR": str(stub),
        "STUB_BRANCH": "feature",
        "STUB_HEAD": git(work, "rev-parse", "feature"),
        "ERG_PR_MERGE_SYNC": "/bin/true",
        "ERG": str(work / "tickets" / "erg"),
        "STUB_ROLLUP": GREEN,
        **env,
    }
    return subprocess.run(["bash", str(HELPER), *args, "42"], cwd=work, capture_output=True, text=True, env=full)


def merge_log(stub):
    log = stub / "merge.log"
    return log.read_text(encoding="utf-8") if log.exists() else ""


def record(work):
    proc = subprocess.run(
        ["python3", str(GATE), "run", "--base", "origin/main", "--head", "HEAD"],
        cwd=work,
        capture_output=True,
        text=True,
        env=child_env(),
    )
    assert proc.returncode == 0, proc.stderr


def test_refuses_without_a_record(fixture):
    work, stub = fixture
    result = merge(work, stub)
    assert result.returncode == 2
    assert "No gate record" in result.stderr
    assert merge_log(stub) == ""


def test_positive_control_merges_with_pinned_head_and_no_auto(fixture):
    work, stub = fixture
    record(work)
    head = git(work, "rev-parse", "HEAD")
    result = merge(work, stub)
    assert result.returncode == 0, result.stdout + result.stderr
    log = merge_log(stub)
    assert f"--match-head-commit {head}" in log
    assert "--auto" not in log


def test_failing_latest_entry_refuses(fixture):
    work, stub = fixture
    record(work)
    base, head = git(work, "rev-parse", "origin/main"), git(work, "rev-parse", "HEAD")
    candidate = subprocess.run(
        ["python3", str(GATE), "candidate", "--base", base, "--head", head],
        cwd=work, capture_output=True, text=True, env=child_env(),
    ).stdout.strip()
    note = git(work, "notes", "--ref=gate", "show", candidate).replace("result: pass", "result: fail")
    git(work, "notes", "--ref=gate", "append", "-m", note, candidate)
    git(work, "push", "-q", "origin", "refs/notes/gate")
    result = merge(work, stub)
    assert result.returncode != 0
    assert merge_log(stub) == ""


def test_base_moved_after_gating_refuses(fixture):
    work, stub = fixture
    record(work)
    git(work, "switch", "-q", "main")
    (work / "c.txt").write_text("c\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "main moved")
    git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-q", "feature")
    result = merge(work, stub)
    assert result.returncode == 2
    assert "No gate record" in result.stderr
    assert merge_log(stub) == ""


def test_gate_off_base_keeps_forge_auto_merge(fixture):
    work, stub = fixture
    git(work, "switch", "-q", "main")
    git(work, "rm", "-q", ".merge-gate.json")
    git(work, "commit", "-q", "-m", "gate off")
    git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-q", "feature")
    result = merge(work, stub)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--auto" in merge_log(stub)


def test_inspection_failure_is_not_absence(fixture):
    work, stub = fixture
    record(work)
    shim = stub / "git"
    real = shutil.which("git")
    shim.write_text(f'#!/usr/bin/env bash\n[[ "$1" == ls-tree ]] && exit 128\nexec {real} "$@"\n', encoding="utf-8")
    shim.chmod(0o755)
    result = merge(work, stub)
    assert result.returncode == 1
    assert "could not inspect" in result.stderr
    assert merge_log(stub) == ""


def test_close_at_merge_time_needs_a_gate_run_on_the_close_commit(fixture):
    work, stub = fixture
    record(work)
    body = "**Ticket:** tickets/0001-fixture.erg"
    first = merge(work, stub, STUB_BODY=body)
    assert first.returncode == 2, first.stdout + first.stderr
    assert "Close commit" in first.stderr
    assert merge_log(stub) == ""
    assert (work / "tickets" / "closed" / "0001-fixture.erg").exists()
    assert git(work, "rev-parse", "HEAD") == git(work, "rev-parse", "origin/feature")
    record(work)
    second = merge(work, stub, STUB_BODY=body)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "--match-head-commit" in merge_log(stub)
    assert git(work, "log", "--oneline", "-3", "feature").count("close and archive") == 1


def test_ticket_closed_before_gating_merges_in_one_run(fixture):
    work, stub = fixture
    erg = str(work / "tickets" / "erg")
    subprocess.run([erg, "close", "0001", "done"], cwd=work, check=True, capture_output=True, env=child_env())
    git(work, "add", "-A", "tickets")
    git(work, "commit", "-q", "-m", "close 0001")
    git(work, "push", "-q", "origin", "feature")
    record(work)
    result = merge(work, stub, STUB_BODY="**Ticket:** tickets/closed/0001-fixture.erg")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--match-head-commit" in merge_log(stub)


@pytest.mark.parametrize(
    "rollup",
    [
        '[{"status":"COMPLETED","conclusion":"FAILURE"}]',
        '[{"status":"IN_PROGRESS","conclusion":null}]',
        "[]",
        "null",
    ],
)
def test_forge_conclusions_are_information_only_on_a_gated_base(fixture, rollup):
    work, stub = fixture
    record(work)
    result = merge(work, stub, STUB_ROLLUP=rollup)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--match-head-commit" in merge_log(stub)


def test_armed_auto_merge_is_disarmed_before_the_pinned_merge(fixture):
    work, stub = fixture
    record(work)
    result = merge(work, stub, STUB_ARMED="1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--disable-auto" in (stub / "disarm.log").read_text(encoding="utf-8")
    assert "--match-head-commit" in merge_log(stub)


def test_armed_auto_merge_that_cannot_be_disarmed_refuses(fixture):
    work, stub = fixture
    record(work)
    result = merge(work, stub, STUB_ARMED="1", STUB_DISARM_FAILS="1")
    assert result.returncode == 1
    assert merge_log(stub) == ""


def test_success_means_merged_not_armed(fixture):
    work, stub = fixture
    record(work)
    result = merge(work, stub, STUB_STATE="OPEN")
    assert result.returncode == 1
    assert "not MERGED" in result.stderr
