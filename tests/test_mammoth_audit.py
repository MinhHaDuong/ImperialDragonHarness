import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

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
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    env = dict(
        os.environ,
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
