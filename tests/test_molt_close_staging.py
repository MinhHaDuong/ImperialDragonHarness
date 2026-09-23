"""Exercise /molt's documented close/archive staging against both erg contracts."""

import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
MOLT = ROOT / "skills/molt/SKILL.md"


def run(*args, cwd, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    assert result.returncode == 0, f"{args}: {result.stdout}\n{result.stderr}"
    return result


def archive_commands():
    section = MOLT.read_text().split("2.6. **Archive closed tickets.**", 1)[1].split(
        "3. **Fix `fix-now` items.**", 1
    )[0]
    # The first shell fence is the archive/staging sequence. The second is
    # duplicate cleanup; run both as /molt instructs.
    return "\n".join(re.findall(r"```bash\n(.*?)\n\s*```", section, re.S))


@pytest.mark.integration
@pytest.mark.parametrize(
    ("old_binary", "recorded_close"),
    [(False, True), (True, True), (True, False)],
    ids=["current-erg", "old-erg", "old-erg-preclosed"],
)
def test_molt_closure_commit_tracks_archive_without_strays(tmp_path, old_binary, recorded_close):
    repo = tmp_path / "repo"
    repo.mkdir()
    tickets = repo / "tickets"
    tickets.mkdir()
    (tickets / "closed").mkdir()
    source = tickets / "0001-probe.erg"
    source.write_text(
        "%erg 0.1\nTitle: Probe\nCreated: 2026-09-10\nAuthor: test\n"
        "\n--- log ---\n2026-09-10T10:00Z test created\n\n--- body ---\n"
        "## Exit criteria\n- [ ] Done\n"
    )
    stray = tickets / "closed/stray.txt"
    stray.write_text("must stay untracked\n")
    run("git", "init", "-q", cwd=repo)
    run("git", "config", "user.name", "Test", cwd=repo)
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "add", "--", "tickets/0001-probe.erg", cwd=repo)
    run("git", "commit", "-qm", "fixture", cwd=repo)

    if old_binary:
        old = tmp_path / "old-erg"
        old.write_bytes(subprocess.run(
            ["git", "show", "51ee49c:tickets/erg"], cwd=ROOT, check=True, capture_output=True
        ).stdout)
        old.chmod(0o755)
        erg = old
    else:
        erg = ROOT / "tickets/erg"
    env = os.environ.copy()
    env["MOLT_ERG"] = str(erg)
    env["MOLT_CLOSED_TICKET_PATHS"] = "tickets/0001-probe.erg" if recorded_close else ""
    run(str(erg), "close", "0001", "already-done", "tickets/", cwd=repo)
    run("bash", "-e", "-c", archive_commands().replace("tickets/erg", '"$MOLT_ERG"'), cwd=repo, env=env)
    run("git", "commit", "-qm", "chore: housekeeping fixes (sweep)", cwd=repo)

    archived = "tickets/closed/0001-probe.erg"
    tracked = run("git", "ls-files", cwd=repo).stdout.splitlines()
    assert tracked == [archived]
    assert run("git", "status", "--porcelain", "--", archived, "tickets/0001-probe.erg", cwd=repo).stdout == ""
    assert run("git", "status", "--porcelain", "--untracked-files=all", cwd=repo).stdout == "?? tickets/closed/stray.txt\n"
    stray.unlink()
    assert run("git", "status", "--porcelain", cwd=repo).stdout == ""

    # A second sweep over the closed ticket has no tracked changes to commit.
    run("bash", "-e", "-c", archive_commands().replace("tickets/erg", '"$MOLT_ERG"'), cwd=repo, env=env)
    assert run("git", "diff", "--cached", "--name-only", cwd=repo).stdout == ""
