"""Detectors of scripts/skill_text_lint.py, on fixtures only (ticket 1234).

The script is a doctor's instrument, never a gate: no test here runs it over
the live skills.
"""

import json
import subprocess
import sys

import pytest
from repo_sources import REPO

sys.path.insert(0, str(REPO / "scripts"))

import skill_text_lint as stl  # noqa: E402

FM = "---\nname: a\ndescription: \"x\"\n---\n"
FM_LINES = 4


def make(tmp_path, body, rel="skills/a/SKILL.md"):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(FM + body, encoding="utf-8")
    return path


def projects(tmp_path, names, fname="projects.json"):
    f = tmp_path / fname
    f.write_text(json.dumps([{"name": n, "path": "x"} for n in names]))
    return f


def run(tmp_path, names=("harness",)):
    return stl.lint(tmp_path, projects(tmp_path, names))["findings"]


def checks(findings, prefix):
    return [f for f in findings if f["check"].startswith(prefix)]


def fence(n):
    return "```bash\n" + "echo x\n" * n + "```\n"


def test_long_fence_flags_13_lines_not_12(tmp_path):
    make(tmp_path, fence(12) + fence(13))
    got = checks(run(tmp_path), "long_fence")
    assert len(got) == 1
    assert got[0]["line"] == FM_LINES + 15  # second fence's opening line


@pytest.mark.parametrize("n,flagged", [(150, False), (151, True)])
def test_body_lines_threshold(tmp_path, n, flagged):
    make(tmp_path, "word\n" * n)
    assert bool(checks(run(tmp_path), "body_lines")) is flagged


def test_heredoc_in_fence_only(tmp_path):
    make(tmp_path, "```bash\ncat <<'EOF'\nhi\nEOF\n```\n\na << b\n")
    got = checks(run(tmp_path), "heredoc")
    assert [f["line"] for f in got] == [FM_LINES + 2]


@pytest.mark.parametrize("text,flagged", [
    ("phase 2", True), ("phased rollout", False),
    ("since we met", True), ("since weeks", False),
    ("used to be", True), ("used to compute", True),  # known false positive
    ("formerly", True), ("form", False),
    ("2026-10-27", True), ("2026-10", True), ("2026-1", False),
    ("#1234", True), ("#12", False),
    ("ticket 1234", True), ("MR 7", True), ("ticket list", False),
])
def test_text_patterns(tmp_path, text, flagged):
    make(tmp_path, f"see {text} here\n")
    assert bool(run(tmp_path)) is flagged


def test_date_inside_fence_flagged(tmp_path):
    make(tmp_path, "```bash\nls 2026-10-27\n```\n")
    assert [f["line"] for f in checks(run(tmp_path), "date")] == [FM_LINES + 2]


def test_project_names_are_data(tmp_path):
    make(tmp_path, "zeta here\nzetas no\nharness skipped\nomega here\n")
    got = checks(run(tmp_path, ["zeta", "harness"]), "project")
    assert [f["line"] for f in got] == [FM_LINES + 1]
    got = checks(run(tmp_path, ["omega"]), "project")
    assert [f["line"] for f in got] == [FM_LINES + 4]


def test_glob_covers_references_not_other_dirs(tmp_path):
    make(tmp_path, "ticket 1234\n", "skills/a/references/x.md")
    make(tmp_path, "ticket 1234\n", "skills/a/notes/y.md")
    files = {f["file"] for f in run(tmp_path)}
    assert files == {"skills/a/references/x.md"}


@pytest.mark.integration
def test_cli_exits_zero_with_json(tmp_path):
    make(tmp_path, "ticket 1234\n")
    pf = projects(tmp_path, ["zeta"])
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "skill_text_lint.py"),
         "--root", str(tmp_path), "--projects", str(pf)],
        capture_output=True, text=True)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["files"] == 1 and out["summary"]["ticket_word"] == 1


def test_missing_script_flags_absent_harness_script_only(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/here.py").write_text("")
    make(tmp_path, "run `python3 \"$IDH_ROOT/scripts/here.py\"`.\n"
                   "run scripts/gone.py\n"
                   "run ${IDH_ROOT}/scripts/gone.sh\n"
                   "run skills/a/scripts/local.sh\n"
                   "run $HARNESS_DIR/scripts/gone.py\n"
                   "run $REPO/scripts/other.py\n")
    got = checks(run(tmp_path), "missing_script")
    assert [f["line"] for f in got] == [FM_LINES + 2, FM_LINES + 3,
                                        FM_LINES + 5]
