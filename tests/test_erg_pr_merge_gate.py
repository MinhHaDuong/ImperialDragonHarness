"""/merge refuses without a gate record on the candidate (ticket 1156).

Drives the real skills/merge/erg-pr-merge against a fixture repository with a
bare origin whose base carries `.merge-gate.json`, and a stub forge CLI that
logs merge calls. Negative control: no record, no merge call. Positive control:
after `merge-gate.py run`, the helper merges with the head pinned and without
arming forge auto-merge (which, with no required checks, would merge at once).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills" / "merge" / "erg-pr-merge"
GATE = ROOT / "scripts" / "merge-gate.py"
CONFIG = {"gate": "on", "scope": "fixture-set", "checks": [{"name": "always-pass", "argv": ["true"]}]}

GH_STUB = r"""#!/usr/bin/env bash
set -euo pipefail
args="$*"
case "$1 $2" in
  "pr view")
    if [[ "$args" == *"headRefOid,statusCheckRollup"* ]]; then
      n=$(cat "$STUB_DIR/reads" 2>/dev/null || echo 0); echo $((n + 1)) > "$STUB_DIR/reads"
      if (( n < ${STUB_PENDING_READS:-0} )); then roll='[{"status":"IN_PROGRESS","conclusion":null}]'
      else roll="${STUB_ROLLUP:-[]}"; fi
      jq -n --arg h "$STUB_HEAD" --argjson r "$roll" '{headRefOid:$h,statusCheckRollup:$r}'; exit 0
    fi
    if [[ "$args" == *"autoMergeRequest"* ]]; then echo no; exit 0; fi
    if [[ "$args" == *"--jq"* && "$args" == *"state"* ]]; then echo MERGED; exit 0; fi
    jq -n --arg h "$STUB_BRANCH" --arg body "Ticket: none" --argjson r "${STUB_ROLLUP:-[]}" \
      '{number:42,headRefName:$h,baseRefName:"main",mergeable:"MERGEABLE",statusCheckRollup:$r,body:$body,isDraft:false,title:"fixture"}'
    exit 0 ;;
  "pr merge") echo "$args" >> "$STUB_DIR/merge.log"; exit 0 ;;
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
    assert result.returncode != 0
    assert "no gate record" in result.stderr
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


def test_pending_forge_checks_without_wait_do_not_merge(fixture):
    work, stub = fixture
    record(work)
    result = merge(work, stub, STUB_PENDING_READS="5")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "pending" in result.stdout
    assert merge_log(stub) == ""


def test_rerun_merges_once_forge_checks_complete(fixture):
    work, stub = fixture
    record(work)
    done = '[{"status":"COMPLETED","conclusion":"SUCCESS"}]'
    first = merge(work, stub, STUB_PENDING_READS="1", STUB_ROLLUP=done)
    assert first.returncode == 2, first.stdout + first.stderr
    assert merge_log(stub) == ""
    second = merge(work, stub, STUB_PENDING_READS="1", STUB_ROLLUP=done)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "--match-head-commit" in merge_log(stub)


def test_failing_forge_check_refuses(fixture):
    work, stub = fixture
    record(work)
    result = merge(work, stub, STUB_ROLLUP='[{"status":"COMPLETED","conclusion":"FAILURE"}]')
    assert result.returncode == 1
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
    assert result.returncode != 0
    assert "no gate record" in result.stderr
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
