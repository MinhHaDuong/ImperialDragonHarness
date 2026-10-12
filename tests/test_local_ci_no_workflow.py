"""Local-CI setup distinguishes an intentional no-CI repo from broken setup."""

import subprocess
from pathlib import Path

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "local-ci.sh"


def _repo(tmp_path: Path, *, workflow: bool) -> Path:
    repo = tmp_path / ("with-workflow" if workflow else "without-workflow")
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "-b", "main", str(repo)], check=True, env=child_env()
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"],
        check=True,
        env=child_env(),
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
        env=child_env(),
    )
    (repo / "fixture.txt").write_text("fixture\n")
    if workflow:
        path = repo / ".github" / "workflows" / "CI.yml"
        path.parent.mkdir(parents=True)
        path.write_text("name: CI\n")
    subprocess.run(
        ["git", "-C", str(repo), "add", "."], check=True, env=child_env()
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "--quiet", "-m", "fixture"],
        check=True,
        env=child_env(),
    )
    return repo


def _run(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RUNNER)],
        cwd=repo,
        capture_output=True,
        text=True,
        env=child_env(),
        check=False,
    )


def test_no_workflow_is_a_successful_skip_before_local_helpers(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path, workflow=False))

    assert result.returncode == 3, result.stdout + result.stderr
    assert "SKIP" in result.stdout
    assert "no .github/workflows/CI.yml" in result.stdout
    assert "no CI checks were run" in result.stdout


def test_workflow_without_local_helpers_is_a_setup_error(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path, workflow=True))

    assert result.returncode == 2
    assert "ci-local/common.sh is missing" in result.stderr
