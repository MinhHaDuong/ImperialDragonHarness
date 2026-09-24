"""guard-destructive-bash blocks `git reset --hard` on a dirty tree, only (ticket 0976).

The 2026-09-24 audit kept one clause of the former catch-all guard: its only
firing that prevented real damage was a hard reset over a primary checkout
holding uncommitted work. These tests pin the narrowed contract through the
real hook invocation (a subprocess fed a PreToolUse payload on stdin):

- dirty target tree -> blocked (exit 2), wherever the target is named from:
  the payload cwd, `git -C DIR`, or a leading `cd DIR &&`;
- clean target tree -> allowed, even when the session cwd is dirty;
- every former pattern (recursive rm, force push, clean, sudo rm, DROP) -> allowed;
- "reset --hard" as text (quoted, commit message, heredoc body) -> allowed.
"""

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "scripts" / "guard-destructive-bash.sh"

pytestmark = pytest.mark.integration


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null",
         "-C", str(cwd), *args],
        check=True, capture_output=True,
    )


def _repo(root: Path, name: str, *, dirty: bool = False, untracked: bool = False) -> Path:
    repo = root / name
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "f.txt").write_text("committed\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-q", "-m", "init")
    if dirty:
        (repo / "f.txt").write_text("uncommitted\n")
    if untracked:
        (repo / "new.txt").write_text("untracked\n")
    return repo


def _run(command: str, cwd: Path | str) -> subprocess.CompletedProcess:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    return subprocess.run(
        ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
        cwd=REPO, timeout=30,
    )


@pytest.fixture
def trees(tmp_path):
    return {
        "dirty": _repo(tmp_path, "dirty", dirty=True),
        "clean": _repo(tmp_path, "clean"),
        "untracked": _repo(tmp_path, "untracked", untracked=True),
    }


def test_dirty_tree_is_blocked(trees):
    res = _run("git reset --hard HEAD~0", trees["dirty"])
    assert res.returncode == 2, res.stderr
    assert "uncommitted changes" in res.stderr
    assert str(trees["dirty"]) in res.stderr


def test_clean_tree_is_allowed(trees):
    res = _run("git reset --hard HEAD", trees["clean"])
    assert res.returncode == 0, res.stderr
    assert res.stderr == ""


def test_untracked_only_is_allowed(trees):
    """reset --hard leaves untracked files alone; nothing is at risk."""
    assert _run("git reset --hard", trees["untracked"]).returncode == 0


@pytest.mark.parametrize("form", [
    "git -C {dirty} reset --hard",
    "cd {dirty} && git reset --hard",
    "cd {dirty}; git status; git reset --hard origin/main",
    "rtk git -C {dirty} reset --hard",
    "GIT_TRACE=0 git -C {dirty} reset --hard",
])
def test_target_named_in_the_command_is_the_one_checked(trees, form):
    res = _run(form.format(dirty=trees["dirty"]), trees["clean"])
    assert res.returncode == 2, (form, res.stderr)


@pytest.mark.parametrize("form", [
    "git -C {clean} reset --hard",
    "cd {clean} && git reset --hard",
])
def test_clean_target_allowed_from_a_dirty_cwd(trees, form):
    res = _run(form.format(clean=trees["clean"]), trees["dirty"])
    assert res.returncode == 0, (form, res.stderr)


@pytest.mark.parametrize("command", [
    "rm -rf build",
    "rm -fr build",
    "rm --force important.txt",
    "sudo rm /etc/hosts",
    "git push --force origin main",
    "git push -f origin main",
    "git clean -fd",
    "psql -c 'DROP TABLE users'",
    "git reset --soft HEAD~1",
    "git reset HEAD f.txt",
])
def test_former_patterns_are_allowed(trees, command):
    """Run from the dirty tree: only a hard reset may ever be refused there."""
    res = _run(command, trees["dirty"])
    assert res.returncode == 0, (command, res.stderr)


@pytest.mark.parametrize("command", [
    'echo "never run git reset --hard on a dirty tree"',
    "git commit -m 'explain why git reset --hard is refused'",
    "grep -n 'reset --hard' scripts/guard-destructive-bash.sh",
    "cat > note.md <<'EOF'\ngit reset --hard\nEOF\necho done",
    "cat <<EOF | wc -l\ncd /tmp && git reset --hard\nEOF",
])
def test_text_mentioning_reset_hard_is_allowed(trees, command):
    res = _run(command, trees["dirty"])
    assert res.returncode == 0, (command, res.stderr)


def test_command_after_heredoc_is_still_checked(trees):
    """Dropping a heredoc body must not drop the command that follows it."""
    command = "cat > note.md <<'EOF'\nnothing here\nEOF\ngit reset --hard"
    assert _run(command, trees["dirty"]).returncode == 2


@pytest.mark.parametrize("stdin", ["not json{", "{}", '{"tool_input": {}}'])
def test_unreadable_payload_allows(stdin):
    res = subprocess.run(["bash", str(HOOK)], input=stdin, capture_output=True, text=True)
    assert res.returncode == 0


def test_non_repo_target_allows(tmp_path):
    """git cannot read the tree, so the reset would fail on its own."""
    assert _run("git reset --hard", tmp_path).returncode == 0
