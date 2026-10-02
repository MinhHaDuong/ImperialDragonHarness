import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from child_env import child_env
from tracked_tree import tracked_checkout

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "mammoth_audit", SCRIPTS / "mammoth-audit.py"
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    for name in ("used", "dependency", "dead"):
        (repo / "skills" / name).mkdir(parents=True)
        (repo / "skills" / name / "SKILL.md").write_text(f"# {name}\n")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "consumer.py").write_text('SKILL = "dependency"\n')
    subprocess.run(["git", "init", "-q", str(repo)], check=True, env=child_env())
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, env=child_env())
    env = dict(
        child_env(),
        GIT_AUTHOR_NAME="Test",
        GIT_AUTHOR_EMAIL="test@example.org",
        GIT_COMMITTER_NAME="Test",
        GIT_COMMITTER_EMAIL="test@example.org",
        GIT_AUTHOR_DATE="2025-01-01T00:00:00Z",
        GIT_COMMITTER_DATE="2025-01-01T00:00:00Z",
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True, env=env
    )
    return repo


def write_trace(projects: Path) -> None:
    project = projects / "project"
    project.mkdir(parents=True)
    record = {
        "type": "assistant",
        "timestamp": "2026-09-01T10:00:00Z",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool-1",
                    "name": "Skill",
                    "input": {"skill": "used"},
                }
            ]
        },
    }
    (project / "private-session-id.jsonl").write_text(json.dumps(record) + "\n")


def test_report_classifies_without_leaking_trace_paths(tmp_path):
    repo = make_repo(tmp_path)
    projects = tmp_path / "private-traces"
    write_trace(projects)
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)

    report = audit.build_report(repo, projects, 180, now)
    rows = {row["skill"]: row for row in report["skills"]}

    assert rows["used"]["disposition"] == "keep-used"
    assert rows["dependency"]["disposition"] == "keep-dependency"
    assert rows["dead"]["disposition"] == "candidate-remove"
    serialized = json.dumps(report)
    assert "private-session-id" not in serialized
    assert str(projects) not in serialized


def test_absent_trace_corpus_never_recommends_removal(tmp_path):
    repo = make_repo(tmp_path)
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)

    report = audit.build_report(repo, tmp_path / "missing", 180, now)

    assert all(
        row["disposition"].startswith("indeterminate")
        or row["disposition"] == "keep-dependency"
        for row in report["skills"]
    )


@pytest.mark.integration
def test_housekeeping_edit_does_not_count_as_usage(tmp_path):
    repo = make_repo(tmp_path)
    projects = tmp_path / "traces"
    write_trace(projects)
    (repo / "skills" / "dead" / "SKILL.md").write_text("# dead\n\nReformatted.\n")
    env = {
        **child_env(),
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.org",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.org",
        "GIT_AUTHOR_DATE": "2026-09-06T00:00:00Z",
        "GIT_COMMITTER_DATE": "2026-09-06T00:00:00Z",
    }
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-qam", "housekeeping"], check=True, env=env
    )

    report = audit.build_report(
        repo, projects, 180, datetime(2026, 9, 7, tzinfo=timezone.utc)
    )
    dead = next(row for row in report["skills"] if row["skill"] == "dead")

    assert dead["last_change"].startswith("2026-09-06")
    assert dead["invocations"] == 0
    assert dead["disposition"] == "candidate-remove"


@pytest.mark.integration
def test_installed_audit_launcher_runs_without_scheduler(tmp_path):
    fake_home = tmp_path / "home"
    env = {
        **child_env(),
        "HOME": str(fake_home),
        "XDG_CONFIG_HOME": str(fake_home / "config"),
        "XDG_BIN_HOME": str(fake_home / "custom bin"),
    }
    # Run the installed audit command directly, without a scheduler.
    # Run from the tracked tree: untracked overlay links in this checkout would
    # make the install refuse on one machine only (ticket 0989).
    subprocess.run(
        [sys.executable, str(tracked_checkout() / "bin" / "idh"), "install"],
        check=True, env=env,
    )
    argv = [str(fake_home / ".local/bin/idh-mammoth-audit")]
    output = tmp_path / "report.json"
    result = subprocess.run(
        [
            *argv,
            "--projects-dir",
            str(tmp_path / "missing-traces"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report["coverage"]["trace_files_in_window"] == 0
    assert report["summary"].get("candidate-remove", 0) == 0
