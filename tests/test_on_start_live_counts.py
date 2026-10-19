"""Session start prints live ticket counts; STATE.md stores none (ticket 1121).

`scripts/on-start.sh` computes open and ready counts from the project's local
`tickets/erg` at read time and prints one declarative line. The project is
`CLAUDE_PROJECT_DIR`, else the working directory, so another runtime calling
the script gets the same line. It stays silent when the project has no
`tickets/erg` or when erg fails, and never fails startup.

The same module checks the portability guard: without `CLAUDE_PROJECT_DIR`
(another runtime, or a bare shell) the Claude-specific lines stay silent.
"""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "on-start.sh"

FAKE_ERG = """#!/bin/sh
case "$1" in
  ready) echo "erg: branch main (tickets)" >&2
         printf 'Ready tickets (2):\\n  0001     a\\n  0002     b\\n' ;;
  list)  printf 'Open tickets (5):\\n  0001     a\\n' ;;
  *) exit 2 ;;
esac
"""

FAILING_ERG = "#!/bin/sh\necho boom >&2\nexit 1\n"

EMPTY_ERG = """#!/bin/sh
case "$1" in
  ready) echo "No ready tickets found." ;;
  list)  echo "No open tickets found." ;;
esac
"""


def project(tmp_path: Path, erg: str | None) -> Path:
    proj = tmp_path / "project"
    (proj / "tickets").mkdir(parents=True)
    if erg is not None:
        path = proj / "tickets" / "erg"
        path.write_text(erg)
        path.chmod(0o755)
    return proj


def run(tmp_path: Path, cwd: Path, project_dir: Path | None):
    env = child_env()
    env["HOME"] = str(tmp_path / "home")
    env.pop("CLAUDE_NIGHT_SWEEP", None)
    if project_dir is None:
        env.pop("CLAUDE_PROJECT_DIR", None)
    else:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        ["bash", str(SCRIPT)], cwd=cwd, env=env,
        capture_output=True, text=True, input="{}",
    )


def counts_lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if "Live ticket counts" in line]


def test_counts_printed_for_claude_project_dir(tmp_path):
    proj = project(tmp_path, FAKE_ERG)
    r = run(tmp_path, tmp_path, proj)
    assert r.returncode == 0, r.stderr
    assert counts_lines(r.stdout) == [
        "Live ticket counts at session start: 5 open, 2 ready "
        "(`tickets/erg ready tickets/` lists the ready ones; "
        "STATE.md stores no counts)."
    ]


def test_counts_use_working_directory_without_project_dir(tmp_path):
    proj = project(tmp_path, FAKE_ERG)
    r = run(tmp_path, proj, None)
    assert r.returncode == 0, r.stderr
    assert "5 open, 2 ready" in r.stdout


def test_empty_corpus_reads_zero(tmp_path):
    proj = project(tmp_path, EMPTY_ERG)
    r = run(tmp_path, proj, None)
    assert "0 open, 0 ready" in r.stdout


@pytest.mark.parametrize("erg", [None, FAILING_ERG], ids=["no-erg", "erg-fails"])
def test_silent_without_a_working_erg(tmp_path, erg):
    proj = project(tmp_path, erg)
    r = run(tmp_path, proj, proj)
    assert r.returncode == 0, r.stderr
    assert counts_lines(r.stdout) == []


def test_silent_without_tickets_dir(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    r = run(tmp_path, plain, plain)
    assert r.returncode == 0, r.stderr
    assert counts_lines(r.stdout) == []


def test_claude_specific_lines_need_claude_project_dir(tmp_path):
    proj = project(tmp_path, None)
    other = run(tmp_path, proj, None).stdout
    assert "Worktree isolation is enabled" not in other
    assert "claude-code.md" not in other
    assert "effortLevel" not in other
    claude = run(tmp_path, proj, proj).stdout
    assert "Worktree isolation is enabled" in claude
    assert "effortLevel" in claude
