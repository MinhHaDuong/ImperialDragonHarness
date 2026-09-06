"""SessionEnd hook: remove this session's scratch dirs, never anyone else's.

Every session gets `<temp-root>/<cwd-key>/<session-id>/{scratchpad,tasks}` and
nothing ever removed it (ticket 0854): on a tmpfs `/tmp` under a per-user quota
the leftovers accumulate until the Bash tool dies with EDQUOT. `scripts/on-end.sh`
is wired as a `SessionEnd` hook and deletes exactly the directories whose
basename equals the session id in the hook's own JSON payload.

The suite spawns the hook as a REAL subprocess with a hermetic base env
(`rules/coding-bash.md`: a hook script is loaded by a fresh non-interactive
bash, and sourcing it into the test's own shell is blind to that path). The
fixture temp root is a `tmp_path` tree — never the machine's live temp root,
whose directories belong to live sessions.

Positive control (recorded 2026-09-07, ticket 0854): run against the tree
BEFORE `scripts/on-end.sh` existed, `test_removes_only_the_ending_session`
failed with `hook script missing` and the fixture directory was still on disk
— the assertion cannot pass without the fix.

The sibling assertion is the load-bearing one: a hook that removed the whole
temp root would satisfy "the target is gone" and destroy every live session's
scratchpad.
"""

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "on-end.sh"

TARGET_SID = "11111111-2222-3333-4444-555555555555"
SIBLING_SID = "99999999-8888-7777-6666-555555555555"


def _plant(root: Path, key: str, sid: str) -> Path:
    """Create one `<root>/<cwd-key>/<session-id>/` tree with content in it."""
    session_dir = root / key / sid
    (session_dir / "scratchpad").mkdir(parents=True)
    (session_dir / "tasks").mkdir()
    (session_dir / "scratchpad" / "payload.txt").write_text("x" * 128)
    return session_dir


def _fixture(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    """A temp root holding the ending session (two cwd keys) and a sibling."""
    root = tmp_path / "claude-fixture"
    dirs = {
        "target_a": _plant(root, "-key-a", TARGET_SID),
        "target_b": _plant(root, "-key-b", TARGET_SID),
        "sibling": _plant(root, "-key-a", SIBLING_SID),
    }
    return root, dirs


def _run_hook(root: Path, tmp_path: Path, payload, extra_env=None):
    """Spawn the hook the way the runtime does: fresh bash, JSON on stdin.

    The env is built from scratch (not inherited) so an ambient variable of the
    session running the test cannot mask a bug — in particular the harness's own
    BASH_ENV, which would re-enter the credential loader in the child.
    """
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "CLAUDE_SESSION_SCRATCH_ROOT": str(root),
    }
    if extra_env:
        env.update(extra_env)
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=stdin,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.integration
def test_removes_only_the_ending_session(tmp_path):
    """The payload's session id goes, under every cwd key; the sibling stays."""
    assert HOOK.is_file(), f"hook script missing: {HOOK}"
    root, dirs = _fixture(tmp_path)

    result = _run_hook(root, tmp_path, {"session_id": TARGET_SID, "reason": "exit"})

    assert result.returncode == 0, result.stderr
    assert not dirs["target_a"].exists(), "ending session's dir survived (key a)"
    assert not dirs["target_b"].exists(), "ending session's dir survived (key b)"
    # The load-bearing half: a hook that nukes the root would pass the two
    # assertions above and wipe every live session on the machine.
    assert dirs["sibling"].exists(), "a sibling session's dir was removed"
    assert (dirs["sibling"] / "scratchpad" / "payload.txt").read_text() == "x" * 128
    # A cwd key left with no sessions is pruned; one still holding a session is not.
    assert not (root / "-key-b").exists(), "emptied cwd-key dir was not pruned"
    assert (root / "-key-a").is_dir()


@pytest.mark.integration
def test_exits_zero_and_removes_nothing_without_a_session_id(tmp_path):
    """A payload with no session id is a no-op, not a wildcard sweep."""
    root, dirs = _fixture(tmp_path)

    result = _run_hook(root, tmp_path, {"reason": "exit"})

    assert result.returncode == 0, result.stderr
    for name, path in dirs.items():
        assert path.exists(), f"{name} removed on an id-less payload"


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    ["", "not json at all", '{"session_id": ""}'],
    ids=["empty-stdin", "garbage", "blank-id"],
)
def test_never_exits_non_zero_on_bad_input(tmp_path, payload):
    """Invariant: the hook never fails, whatever the runtime hands it."""
    root, dirs = _fixture(tmp_path)

    result = _run_hook(root, tmp_path, payload)

    assert result.returncode == 0, result.stderr
    for path in dirs.values():
        assert path.exists()


@pytest.mark.integration
@pytest.mark.parametrize(
    "sid",
    ["../-key-a", "-key-a/" + SIBLING_SID, "*", "."],
    ids=["parent", "slash", "glob", "dot"],
)
def test_rejects_a_session_id_that_is_not_a_plain_name(tmp_path, sid):
    """A path or a glob in the id must never widen the deletion."""
    root, dirs = _fixture(tmp_path)

    result = _run_hook(root, tmp_path, {"session_id": sid})

    assert result.returncode == 0, result.stderr
    for name, path in dirs.items():
        assert path.exists(), f"{name} removed by session id {sid!r}"
    assert root.exists()


@pytest.mark.integration
def test_missing_temp_root_is_a_silent_no_op(tmp_path):
    """A machine whose temp root was already cleared must not error."""
    root = tmp_path / "absent"

    result = _run_hook(root, tmp_path, {"session_id": TARGET_SID})

    assert result.returncode == 0, result.stderr
    assert not root.exists()


@pytest.mark.integration
def test_subagent_session_leaves_the_shared_dir_alone(tmp_path):
    """A subagent shares the parent session's scratch dir — never delete it.

    Measured on this host 2026-09-07: a subagent's environment carries the
    parent's session id and a child-session marker, and its scratchpad path is
    the parent's directory. If a child ever fires SessionEnd, honouring it would
    delete a live session's scratchpad out from under it.
    """
    root, dirs = _fixture(tmp_path)

    result = _run_hook(
        root,
        tmp_path,
        {"session_id": TARGET_SID},
        extra_env={"CLAUDE_CODE_CHILD_SESSION": "1"},
    )

    assert result.returncode == 0, result.stderr
    for name, path in dirs.items():
        assert path.exists(), f"{name} removed from a child session's hook"


@pytest.mark.integration
def test_a_removal_that_fails_still_exits_zero(tmp_path):
    """The invariant holds when the filesystem says no, not only on bad input.

    `set -e` plus the EXIT trap is what makes this pass: a read-only cwd-key
    directory makes the removal fail, and the hook must still finish quietly.
    """
    root, dirs = _fixture(tmp_path)
    key = root / "-key-b"
    key.chmod(0o500)  # readable, not writable: the removal cannot succeed
    try:
        result = _run_hook(root, tmp_path, {"session_id": TARGET_SID})

        assert result.returncode == 0, result.stderr
        assert dirs["target_b"].exists(), "fixture is void — the removal succeeded"
        assert not dirs["target_a"].exists(), "the removable one was not removed"
    finally:
        key.chmod(0o700)


@pytest.mark.integration
def test_hook_is_wired_as_a_session_end_hook():
    """The canonical settings file runs this script on SessionEnd."""
    settings = json.loads((REPO_ROOT / "settings.shared.json").read_text())
    commands = [
        hook.get("command", "")
        for entry in settings.get("hooks", {}).get("SessionEnd", [])
        for hook in entry.get("hooks", [])
    ]
    assert any("on-end.sh" in c for c in commands), (
        f"no SessionEnd hook runs on-end.sh; found {commands}"
    )


@pytest.mark.integration
def test_hook_does_not_need_jq(tmp_path, monkeypatch):
    """Payload parsing must survive a PATH without jq (fallback extractor)."""
    root, dirs = _fixture(tmp_path)
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    for tool in ("bash", "cat", "tr", "head", "sed", "rm", "rmdir", "id"):
        found = shutil.which(tool)
        if found:
            (bindir / tool).symlink_to(found)
    assert not (bindir / "jq").exists()

    result = _run_hook(
        root, tmp_path, {"session_id": TARGET_SID}, extra_env={"PATH": str(bindir)}
    )

    assert result.returncode == 0, result.stderr
    assert not dirs["target_a"].exists(), "removal failed without jq on PATH"
    assert dirs["sibling"].exists()


def test_fixture_ids_are_not_a_live_session():
    """Guard: the fixtures must never collide with a real session id."""
    live_root = Path(f"/tmp/claude-{os.getuid()}")
    for sid in (TARGET_SID, SIBLING_SID):
        uuid.UUID(sid)  # well-formed, so a collision would be meaningful
        assert not list(live_root.glob(f"*/{sid}")), (
            f"fixture id {sid} exists under the live temp root"
        )
