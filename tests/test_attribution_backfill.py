"""Real Git/CLI controls for conservative post-merge attribution backfill."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.attribution_record import parse_record

CLI = Path(__file__).resolve().parents[1] / "scripts" / "attribution_backfill.py"
pytestmark = pytest.mark.integration


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def commit(repo, name):
    git(repo, "add", ".")
    git(repo, "commit", "-qm", name)
    return git(repo, "rev-parse", "HEAD")


def record(pr=12, anchor="source.py:2"):
    return ("kind: review-attribution\n"
            f"pr: {pr} · merged 2026-10-03 · project: fixture\n"
            "writer: runtime=fixture · model=example/writer-v1 · effort=standard\n"
            "reviewer: seat=first · runtime=fixture · model=example/reviewer-v1 · status: ran\n"
            f"  finding: verifiable · {anchor} · adopted: no\n"
            "reviewer: seat=second · runtime=fixture · model=example/reviewer-v1 · status: ran\n"
            f"  finding: consider · {anchor} · adopted: no\n"
            "Context: opaque reviewed revision claims are not coordinate evidence.\n")


@pytest.fixture
def project(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / "source.py").write_text("first\nbroken\nthird\n")
    reviewed = commit(tmp_path, "reviewed revision")
    journal = tmp_path / "memory/journal/2026"
    journal.mkdir(parents=True)
    entry = journal / "2026-10-03-review-attribution-pr12.md"
    entry.write_text(record())
    commit(tmp_path, "durable review record")
    (tmp_path / "source.py").write_text("first\nfixed\nthird\n")
    fix = commit(tmp_path, "commissioned defect fix")
    return tmp_path, entry, reviewed, fix


def run(project, *extra, evidence=True):
    repo, _, reviewed, fix = project
    args = [sys.executable, str(CLI), "--project", str(repo), "--fix-pr", "34",
            "--fix-commit", fix, "--defect-fix"]
    if evidence:
        args += ["--reviewed", f"12={reviewed}"]
    return subprocess.run(args + list(extra), capture_output=True, text=True)


def test_actual_cli_appends_only_event_and_shared_reader_labels(project):
    repo, entry, _, _ = project
    before = entry.read_bytes()
    result = run(project)
    assert result.returncode == 0, result.stderr
    assert entry.read_bytes() == before + b"defect-confirmed: source.py:2 \xc2\xb7 source: post-merge-fix \xc2\xb7 pr: 34\n"
    assert git(repo, "diff", "--name-only") == str(entry.relative_to(repo))
    assert git(repo, "diff", "--numstat").split("\t")[:2] == ["1", "0"]
    assert parse_record(entry.read_text())["defect_labels"] == ["source.py:2"]
