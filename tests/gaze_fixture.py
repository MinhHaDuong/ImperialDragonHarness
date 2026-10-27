"""Shared fixture for the gaze setup/close script tests (ticket 1227): a clone
with an origin carrying a PR branch, plus a `gh` PATH shim that answers
`pr view` from MOCK_PR_JSON and logs `pr comment` bodies."""

import json
import os
import subprocess
import sys
from pathlib import Path

from child_env import child_env
from run_checked import run_checked

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "scripts" / "gaze_setup.py"
CLOSE = ROOT / "scripts" / "gaze_close.py"


def git(cwd, *args):
    return run_checked(["git", "-C", str(cwd), *args]).stdout.strip()


def make_repo(tmp_path, body="Closes nothing"):
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    primary = tmp_path / "primary"
    run_checked(["git", "init", "--bare", "-b", "main", str(origin)])
    seed.mkdir()
    git(seed, "init", "-b", "main")
    git(seed, "config", "user.email", "t@example.com")
    git(seed, "config", "user.name", "T")
    (seed / "f.txt").write_text("base\n")
    git(seed, "add", "f.txt")
    git(seed, "commit", "-m", "base")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "origin", "main")
    git(seed, "switch", "-c", "feature")
    (seed / "f.txt").write_text("changed\n")
    git(seed, "commit", "-am", "change")
    git(seed, "push", "origin", "feature")
    run_checked(["git", "clone", str(origin), str(primary)])
    head = git(seed, "rev-parse", "HEAD")
    meta = {"number": 7, "headRefName": "feature", "headRefOid": head, "baseRefName": "main",
            "state": "OPEN", "mergeable": "MERGEABLE", "body": body,
            "comments": [{"author": {"login": "bob"}, "body": "looks odd"}],
            "reviews": [], "statusCheckRollup": [{"name": "ci", "conclusion": "SUCCESS"}]}
    shim = tmp_path / "bin" / "gh"
    shim.parent.mkdir()
    shim.write_text(
        "#!/bin/sh\n"
        'case "$2" in\n'
        '  view) printf \'%s\\n\' "$MOCK_PR_JSON" ;;\n'
        '  comment) printf \'%s\\n\' "$5" >> "$MOCK_GH_LOG" ;;\n'
        "esac\n")
    shim.chmod(0o755)
    env = dict(child_env(), PATH=f"{shim.parent}:{os.environ['PATH']}",
               MOCK_PR_JSON=json.dumps(meta), MOCK_GH_LOG=str(tmp_path / "gh.log"))
    return primary, env


def run(script, args, cwd, env):
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, env=env,
                          capture_output=True, text=True)


def fields(out):
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
