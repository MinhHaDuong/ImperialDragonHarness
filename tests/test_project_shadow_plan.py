"""project_shadow.py --plan: routes 1230 finding records into molt's action
plan (ticket 1231). The model performs the edits; this decides which ones.
Each test pairs a record with a neighbour that would flip the routing."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration
SCRIPT = Path(__file__).resolve().parents[1] / "scripts/project_shadow.py"


def rec(local, verdict, disposition, destination="project"):
    return {"kind": "shadowing", "local_file": local, "harness_file": "h/x",
            "instruction": "i", "verdict": verdict, "reason": None,
            "disposition": disposition, "destination": destination}


def plan(records, *flags, raw=None):
    text = raw if raw is not None else "".join(
        json.dumps(r) + "\n" for r in records)
    return subprocess.run([sys.executable, str(SCRIPT), "--plan", *flags],
                          input=text, capture_output=True, text=True)


def test_ok_reasoned_finding_yields_no_entry():
    out = plan([rec("ok-file", "ok", "delete-local"),
                rec("warn-file", "warn", "annotate")])
    assert out.returncode == 0
    lines = out.stdout.splitlines()
    assert len(lines) == 1 and "warn-file" in lines[0]
    assert "ok-file" not in out.stdout
    assert plan([rec("ok-file", "ok", "delete-local")]).stdout == ""


def test_dispositions_route_distinctly():
    d = plan([rec("a", "warn", "delete-local")]).stdout
    n = plan([rec("a", "warn", "annotate")]).stdout
    t = plan([rec("a", "warn", "harness-ticket", "harness")]).stdout
    assert d.startswith("fix-now") and "delete" in d
    assert n.startswith("fix-now") and "reason" in n and n != d
    assert t.startswith("open-ticket") and "harness" in t


def test_auto_never_files_into_harness():
    r = rec("a", "warn", "harness-ticket", "harness")
    out = plan([r], "--auto").stdout
    assert not out.startswith("open-ticket") and out.startswith("report")
    # project-bound work is unaffected by --auto
    assert plan([rec("a", "warn", "delete-local")], "--auto"
                ).stdout.startswith("fix-now")


def test_null_disposition_and_skip_lines_become_skip():
    assert plan([rec("a", "warn", None)]).stdout.startswith("skip")
    out = plan([], raw='{"status": "skip", "reason": "harness itself"}\n')
    assert out.returncode == 0 and out.stdout.startswith("skip")
    assert "harness itself" in out.stdout


def test_malformed_line_fails_and_empty_is_empty():
    assert plan([], raw="not json\n").returncode != 0
    out = plan([], raw="")
    assert out.returncode == 0 and out.stdout == ""


def test_display_string_ok_reasoned_is_also_left_alone():
    assert plan([rec("a", "ok (reasoned)", "delete-local")]).stdout == ""


def test_bad_shapes_fail_and_destination_harness_wins():
    assert plan([], raw="[1]\n").returncode == 1
    assert plan([], raw='{"verdict": "warn", "disposition": "annotate"}\n'
                ).returncode == 1
    out = plan([rec("a", "warn", "delete-local", "harness")]).stdout
    assert out.startswith("open-ticket")
    assert plan([rec("a", "warn", "x", "project")]).stdout.startswith("skip")
    assert plan([rec("a", "okay", "delete-local")]).stdout.startswith("fix-now")
