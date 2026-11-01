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

Ticket 1324 adds one clause: a `pgrep -f`/`pkill -f` search lacking `-A` or a
bracketed pattern matches its own calling shell, so it is refused.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "scripts" / "guard-destructive-bash.sh"

pytestmark = pytest.mark.integration


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null",
         "-C", str(cwd), *args],
        check=True, capture_output=True, env=child_env(),
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


def _run(command: str, cwd: Path | str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    return subprocess.run(
        ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
        cwd=REPO, timeout=30, env={**child_env(), **(extra_env or {})},
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
    res = subprocess.run(["bash", str(HOOK)], input=stdin, capture_output=True,
                         text=True, env=child_env())
    assert res.returncode == 0


def test_non_repo_target_allows(tmp_path):
    """git cannot read the tree, so the reset would fail on its own."""
    # The ceiling keeps the tool from discovering an enclosing repo when TMPDIR
    # itself sits inside one (e.g. under ~/.claude/jobs/...).
    ceiling = {"GIT_CEILING_DIRECTORIES": str(tmp_path.parent)}
    assert _run("git reset --hard", tmp_path, ceiling).returncode == 0


@pytest.mark.parametrize("command", [
    "pgrep -f foo",
    "pgrep -af foo",
    "pgrep --full foo",
    "pgrep -u root -f foo",
    "pkill -9 -f foo",
    "pkill -ALRM -f foo",  # a signal name holding an A is not -A
    "/usr/bin/pgrep -f foo",
    "rtk pgrep -lf foo",
    "grep -q x <<<word\npgrep -f foo\nword",  # a here-string is no heredoc
    "timeout 5 pkill -f foo",
    "while pgrep -f job >/dev/null; do :; done",
    "cd /tmp && pgrep -f foo",
    "pgrep --ful foo",  # getopt_long prefix of --full
])
def test_self_matching_pgrep_is_blocked(tmp_path, command):
    res = _run(command, tmp_path)
    assert res.returncode == 2, (command, res.stderr)
    assert "-A" in res.stderr and "[p]attern" in res.stderr and "tail --pid" in res.stderr


@pytest.mark.parametrize("command", [
    "pgrep -fA foo",
    "pgrep -A -f foo",
    "pgrep --full --ignore-ancestors foo",
    "pgrep -f '[f]oo'",
    "pgrep foo",
    "pgrep -P 12 sh",
    "pgrep -uf foo",  # -u takes the value f: no -f flag
    "pkill -x sleep",
    'echo "pgrep -f foo"',
    "cat <<'EOF'\npgrep -f foo\nEOF",
    "cat <<'END-OF-TEXT'\npgrep -f job\nEND-OF-TEXT",  # gaze rv-20261028-pr-1914-c770
    "pgrep --full --ignore-anc foo",
])
def test_safe_pgrep_is_allowed(tmp_path, command):
    res = _run(command, tmp_path)
    assert res.returncode == 0, (command, res.stderr)


def _procps_major():
    out = subprocess.run(["pgrep", "--version"], capture_output=True, text=True).stdout
    m = re.search(r"procps-ng\s+(\d+)", out)
    return int(m.group(1)) if m else 0


@pytest.mark.skipif(_procps_major() < 4, reason="-A needs procps-ng >= 4.0")
def test_refused_form_really_matches_its_shell():
    """Positive control: the refused form self-matches, the allowed ones do not."""
    mark = "idhmarker1324x"
    script = f"pgrep -f {mark} >/dev/null; a=$?; pgrep -A -f {mark} >/dev/null; echo $a $?"
    r = subprocess.run(["sh", "-c", script], capture_output=True, text=True, env=child_env())
    assert r.stdout.split() == ["0", "1"], r
    # The bracket holds only while the plain word is absent from the caller's line.
    r = subprocess.run(["sh", "-c", "pgrep -f '[i]dhmarker1324x' >/dev/null; echo $?"],
                       capture_output=True, text=True, env=child_env())
    assert r.stdout.split() == ["1"], r


@pytest.mark.parametrize("command", [
    "pi --print 'hello'",
    "pi -p hello",
    "rtk pi -p hello",
    "FOO=1 pi --print hello",
    "timeout 60 pi -p hello",
    "cd /tmp && pi -p hello",
    "pi -p hello | tail -3",  # stdin of the first command is still open
    "pi -p hello > out.txt 2>&1",
    "codex exec 'say ok'",
    "codex exec --skip-git-repo-check 'say ok'",
])
def test_open_stdin_cli_is_blocked(tmp_path, command):
    res = _run(command, tmp_path)
    assert res.returncode == 2, (command, res.stderr)
    assert "</dev/null" in res.stderr and "coding-bash.md" in res.stderr


@pytest.mark.parametrize("command", [
    "pi --print hello </dev/null",
    "pi -p hello < prompt.txt",
    "pi -p <<< 'hello'",
    "pi -p <<EOF\nhello\nEOF",
    "echo hello | pi -p",
    "cat prompt.txt | pi --print",
    "codex exec 'say ok' </dev/null",
    "pi --help",
    "pi",
    "pi chat",
    "codex --help",
    "codex login",
    'echo "pi -p hello"',
    "grep 'pi --print' notes.md",
    "# pi -p hello",
    "command -v pi",
    "git log -p",
    "cat <<'EOF'\npi -p hello\nEOF",
])
def test_closed_stdin_or_other_cli_is_allowed(tmp_path, command):
    res = _run(command, tmp_path)
    assert res.returncode == 0, (command, res.stderr)
