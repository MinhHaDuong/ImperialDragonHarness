"""`idh install | check` on a disposable HOME (ticket 0987).

The expected link set comes from adapters/projections.json, never from what
install happened to create, so an entry install forgets is a failure here.
Every run uses a fixture HOME and a PATH whose `systemctl` is a stub that logs
its argv: nothing touches the developer's HOME, ~/.bashrc or systemd.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from tracked_tree import tracked_checkout

# The tracked tree, not this checkout: untracked links here (the private
# overlay) would reach $IDH_ROOT and fail the run on one machine only (0989).
REPO = tracked_checkout()
IDH = REPO / "bin" / "idh"
spec = importlib.util.spec_from_file_location("projections", REPO / "scripts/validate-projections.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
MANIFEST = validator.load_entries(REPO / "adapters/projections.json", None)

pytestmark = pytest.mark.integration


def expand(spec: str, home: Path) -> Path:
    if spec.startswith("$IDH_ROOT"):
        return Path(str(REPO) + spec[len("$IDH_ROOT"):])
    return Path(str(home) + spec[1:])


@pytest.fixture
def machine(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "systemctl.log"
    stub = bin_dir / "systemctl"
    stub.write_text(f'#!/bin/sh\necho "$*" >> "{log}"\n')
    stub.chmod(0o755)
    env = {"HOME": str(home), "PATH": f"{bin_dir}:/usr/bin:/bin"}

    def idh(*args):
        return subprocess.run(
            [sys.executable, str(IDH), *args], env=env, capture_output=True, text=True, timeout=60
        )

    return {"home": home, "idh": idh, "log": log, "env": env}


def test_install_then_check_round_trip_and_planted_break(machine):
    home, idh = machine["home"], machine["idh"]
    r = idh("install")
    assert r.returncode == 0, r.stdout + r.stderr

    r = idh("check")  # positive control
    assert r.returncode == 0, r.stdout + r.stderr

    for entry in MANIFEST:
        if not entry["required"]:
            continue
        path = expand(entry["path"], home)
        target = expand(entry["target"], home)
        if entry.get("registration"):
            actual = json.loads(path.read_text())
            wanted = json.loads(target.read_text())
            assert validator.merge_hooks(json.loads(json.dumps(actual)), wanted) == actual
        else:
            assert path.resolve() == target.resolve(), (path, target)
    assert (home / ".local" / "bin" / "idh").resolve() == IDH.resolve()
    assert "--user enable --now idh-mammoth-audit.timer" in machine["log"].read_text()
    assert (home / ".bashrc").read_text() == (REPO / "scripts" / "bashrc-loader.sh").read_text()

    # Negative control: one planted broken link, one named culprit.
    hooks = home / ".codex" / "hooks.json"
    hooks.unlink()
    hooks.symlink_to("/nonexistent")
    r = idh("check")
    assert r.returncode == 1
    culprits = [
        line for line in (r.stdout + r.stderr).splitlines()
        if line.lstrip().startswith(("MISSING:", "DANGLING:", "FOREIGN:"))
    ]
    assert len(culprits) == 1 and str(hooks) in culprits[0], culprits


def test_install_is_idempotent_and_refuses_foreign_files(machine):
    home, idh = machine["home"], machine["idh"]
    hooks = home / ".codex" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text('{not-json')
    r = idh("install")
    assert r.returncode == 1
    assert f"REFUSED: {hooks}" in r.stdout + r.stderr
    assert hooks.read_text() == '{not-json', "the only copy was overwritten"
    # The other entries still installed.
    assert (home / ".pi" / "agent" / "extensions" / "idh-guard.ts").is_symlink()

    hooks.unlink()
    assert idh("install").returncode == 0
    r = idh("install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "installed:" not in r.stdout


def test_skill_subcommands_still_reach_perch(machine):
    r = machine["idh"]("check", "harness", "pi", "--version", "0.99.0")
    assert "pi:" in r.stdout + r.stderr


LOADER = (REPO / "scripts" / "bashrc-loader.sh").read_text()


def test_loader_file_is_delimited_by_its_markers():
    lines = LOADER.splitlines()
    assert lines[0].startswith("# >>> Imperial Dragon Harness loader")
    assert lines[-1].startswith("# <<< Imperial Dragon Harness loader")


def test_loader_splice_keeps_every_user_line(machine):
    """The padme case: a user alias AFTER the block must survive the update."""
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    stale = LOADER.replace("_idh_stubs\n", "_idh_stubs  # stale\n", 1)
    before, after = "export EDITOR=vi\n", "alias zotero='zotero --no-remote'\n"
    bashrc.write_text(before + stale + after)
    r = idh("install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert bashrc.read_text() == before + LOADER + after
    (backup,) = home.glob(".bashrc.idh-bak-*")
    assert backup.read_text() == before + stale + after

    snapshot = bashrc.stat().st_mtime_ns
    assert idh("install").returncode == 0
    assert bashrc.stat().st_mtime_ns == snapshot, "a rerun rewrote ~/.bashrc"


def test_loader_is_appended_when_absent(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    bashrc.write_text("alias ll='ls -l'")  # no final newline
    assert idh("install").returncode == 0
    assert bashrc.read_text() == "alias ll='ls -l'\n" + LOADER


def test_status_reports_installed_vs_declared(machine):
    home, idh = machine["home"], machine["idh"]
    assert idh("install").returncode == 0
    r = idh("status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"declared {len(MANIFEST)}, ok " in r.stdout
    assert f"ok       {home / '.codex' / 'hooks.json'} -> " in r.stdout
    assert "timer    idh-mammoth-audit.timer:" in r.stdout
    assert "origin   " in r.stdout

    hooks = home / ".codex" / "hooks.json"
    hooks.unlink()
    r = idh("status")
    assert r.returncode == 1
    assert f"MISSING  {hooks} -> " in r.stdout
    assert "broken 1" in r.stdout


SYNC_FILES = (
    "bin/idh",
    "adapters/lifecycle.py",
    "adapters/projections.json",
    "scripts/validate-projections.py",
    "scripts/sync-local-main.sh",
)


def _git(cwd, *args):
    subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t",
         "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
        check=True, capture_output=True, text=True,
    )


def test_sync_fast_forwards_or_names_the_blocking_file(tmp_path, machine):
    """The padme case: an untracked file where an incoming one lands."""
    origin, upstream, local = tmp_path / "origin.git", tmp_path / "up", tmp_path / "local"
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(upstream))
    for rel in SYNC_FILES:
        (upstream / rel).parent.mkdir(parents=True, exist_ok=True)
        (upstream / rel).write_bytes((REPO / rel).read_bytes())
        (upstream / rel).chmod((REPO / rel).stat().st_mode)
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-qm", "base")
    _git(upstream, "push", "-q", "origin", "HEAD:main")
    _git(tmp_path, "clone", "-q", str(origin), str(local))

    (upstream / "notes.md").write_text("incoming\n")
    _git(upstream, "add", "notes.md")
    _git(upstream, "commit", "-qm", "notes")
    _git(upstream, "push", "-q", "origin", "HEAD:main")
    (local / "notes.md").write_text("mine, untracked\n")

    def sync():
        return subprocess.run(
            [sys.executable, str(local / "bin" / "idh"), "sync"],
            env=machine["env"], capture_output=True, text=True, timeout=60,
        )

    r = sync()
    assert r.returncode == 1
    assert "notes.md" in r.stdout
    assert "not synced" in r.stderr
    assert (local / "notes.md").read_text() == "mine, untracked\n"

    (local / "notes.md").unlink()  # positive control: the blocker gone, sync lands
    r = sync()
    assert r.returncode == 0, r.stdout + r.stderr
    assert (local / "notes.md").read_text() == "incoming\n"

    # HEAD on another branch, origin/HEAD unset: the script moves main by ref,
    # and success is judged on main, the branch it syncs.
    _git(local, "switch", "-q", "-c", "side")
    _git(local, "remote", "set-head", "origin", "--delete")
    (upstream / "more.md").write_text("more\n")
    _git(upstream, "add", "more.md")
    _git(upstream, "commit", "-qm", "more")
    _git(upstream, "push", "-q", "origin", "HEAD:main")
    r = sync()
    assert r.returncode == 0, r.stdout + r.stderr
    main = subprocess.run(["git", "-C", str(local), "rev-parse", "main", "origin/main"],
                          capture_output=True, text=True, check=True).stdout.split()
    assert main[0] == main[1]

    script = local / "scripts" / "sync-local-main.sh"
    script.chmod(0o644)  # not executable: a named error, not a traceback
    r = sync()
    assert r.returncode == 1
    assert "idh sync: cannot run" in r.stderr and "Traceback" not in r.stderr
    script.chmod(0o755)

    origin.rename(tmp_path / "gone.git")  # offline: a skipped sync is not a success
    r = sync()
    assert r.returncode == 1
    assert "not synced" in r.stderr


def test_loader_splice_keeps_crlf_and_non_utf8_bytes(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    before, after = b"export A=1\r\n# caf\xe9 latin-1\r\n", b"alias z=zotero\r\n"
    bashrc.write_bytes(before + after)
    assert idh("install").returncode == 0
    assert bashrc.read_bytes() == before + after + LOADER.encode()
    stale = bashrc.read_bytes().replace(b"_idh_stubs\n", b"_idh_stubs  # stale\n", 1)
    bashrc.write_bytes(stale)
    assert idh("install").returncode == 0
    assert bashrc.read_bytes() == before + after + LOADER.encode()


def test_two_loader_blocks_are_refused(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    bashrc.write_text(LOADER + "alias a=b\n" + LOADER)
    r = idh("install")
    assert r.returncode == 1
    assert "more than one loader block" in r.stderr
    assert bashrc.read_text() == LOADER + "alias a=b\n" + LOADER


def test_links_target_the_checkout_and_a_blocked_parent_is_named(machine):
    home, idh = machine["home"], machine["idh"]
    (home / ".pi").write_text("a file where a directory belongs\n")
    r = idh("install")
    assert r.returncode == 1
    assert f"REFUSED: {home / '.pi' / 'agent' / 'extensions' / 'idh-guard.ts'}" in r.stderr
    # The run went on: the loader and the other links are in place.
    assert (home / ".bashrc").read_text() == LOADER
    hooks = home / ".codex" / "hooks.json"
    assert json.loads(hooks.read_text())["hooks"] == json.loads((REPO / "adapters/codex/hooks.json").read_text())["hooks"]


def _lifecycle(monkeypatch, home):
    import importlib.util

    monkeypatch.setenv("HOME", str(home))
    spec = importlib.util.spec_from_file_location("lifecycle", REPO / "adapters" / "lifecycle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_backup_keeps_a_private_mode_and_never_collides(machine):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    bashrc.write_text("export TOKEN_FILE=~/.secret\n")
    bashrc.chmod(0o600)
    assert idh("install").returncode == 0
    bashrc.write_text(bashrc.read_text().replace("_idh_stubs\n", "_idh_stubs #\n", 1))
    assert idh("install").returncode == 0  # a second changing install, same second
    backups = sorted(home.glob(".bashrc.idh-bak-*"))
    assert len(backups) == 2, backups
    assert backups[0].read_text() == "export TOKEN_FILE=~/.secret\n", "first backup overwritten"
    for path in (*backups, bashrc):
        assert path.stat().st_mode & 0o777 == 0o600, path


def test_failed_replace_leaves_bashrc_byte_identical(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    home.mkdir()
    bashrc = home / ".bashrc"
    bashrc.write_bytes(b"alias keep=me\r\n")
    lifecycle = _lifecycle(monkeypatch, home)

    def boom(src, dst):
        raise OSError("simulated crash before the rename")

    monkeypatch.setattr(lifecycle.os, "replace", boom)
    assert lifecycle.install_loader() == 1
    assert "simulated crash" in capsys.readouterr().err
    assert bashrc.read_bytes() == b"alias keep=me\r\n"
    assert not list(home.glob("*idh-tmp-*")), "temp file left behind"


@pytest.mark.parametrize("shape", ["read-only", "directory"])
def test_unusable_bashrc_is_named_and_the_rest_still_runs(machine, shape):
    home, idh = machine["home"], machine["idh"]
    bashrc = home / ".bashrc"
    if shape == "directory":
        bashrc.mkdir()
    else:
        bashrc.write_text("alias a=b\n")
        bashrc.chmod(0o444)
    r = idh("install")
    assert r.returncode == 1
    assert "idh: loader NOT installed:" in r.stderr and "Traceback" not in r.stderr
    assert (home / ".codex" / "hooks.json").is_file()
    assert "enable --now" in machine["log"].read_text()
    if shape == "read-only":
        assert bashrc.read_text() == "alias a=b\n"


def test_failing_systemctl_is_named_not_a_traceback(machine):
    stub = Path(machine["env"]["PATH"].split(":")[0]) / "systemctl"
    stub.write_text("#!/bin/sh\necho 'Failed to connect to bus' >&2\nexit 1\n")
    r = machine["idh"]("install")
    assert r.returncode == 1
    assert "idh: timer NOT enabled: systemctl --user daemon-reload failed" in r.stderr
    assert "Traceback" not in r.stderr
    assert (machine["home"] / ".bashrc").read_text() == LOADER


def test_unknown_command_never_installs(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    home.mkdir()
    lifecycle = _lifecycle(monkeypatch, home)
    for argv in (["instal"], ["install", "extra"], []):
        assert lifecycle.main(argv) == 2
    assert "unknown command" in capsys.readouterr().err
    assert not any(home.iterdir()), "an unknown command installed something"


def test_backup_names_in_the_same_second_get_a_counter(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    lifecycle = _lifecycle(monkeypatch, home)
    monkeypatch.setattr(lifecycle.time, "strftime", lambda fmt: "20260929T120000")
    dest = home / ".bashrc"
    first = lifecycle._backup(dest, b"original\n", 0o600)
    second = lifecycle._backup(dest, b"later\n", 0o600)
    assert first != second and second.name.endswith(".1")
    assert first.read_bytes() == b"original\n"


def test_symlinked_bashrc_is_rewritten_at_its_target(machine):
    home, idh = machine["home"], machine["idh"]
    real = home / "dotfiles" / "bashrc"
    real.parent.mkdir()
    real.write_text("alias a=b\n")
    (home / ".bashrc").symlink_to(real)
    assert idh("install").returncode == 0
    assert (home / ".bashrc").is_symlink()
    assert real.read_text() == "alias a=b\n" + LOADER


@pytest.mark.parametrize("failing_call", [1, 2], ids=["backup-fsync", "temp-fsync"])
def test_failed_write_leaves_no_copy_of_bashrc(tmp_path, monkeypatch, failing_call):
    """A partial copy of ~/.bashrc may hold secrets: nothing is left behind."""
    home = tmp_path / "home"
    home.mkdir()
    bashrc = home / ".bashrc"
    bashrc.write_bytes(b"export SECRET=x\n")
    lifecycle = _lifecycle(monkeypatch, home)
    real_fsync, calls = lifecycle.os.fsync, []

    def fsync(fd):
        calls.append(fd)
        if len(calls) == failing_call:
            raise OSError("simulated disk error")
        return real_fsync(fd)

    monkeypatch.setattr(lifecycle.os, "fsync", fsync)
    assert lifecycle.install_loader() == 1
    assert bashrc.read_bytes() == b"export SECRET=x\n"
    assert not list(home.glob("*idh-tmp-*"))
    if failing_call == 1:
        assert not list(home.glob(".bashrc.idh-bak-*")), "partial backup left"


def test_short_writes_still_yield_complete_files(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    bashrc = home / ".bashrc"
    bashrc.write_bytes(b"alias keep=me\n")
    lifecycle = _lifecycle(monkeypatch, home)
    real_write = lifecycle.os.write
    monkeypatch.setattr(lifecycle.os, "write", lambda fd, data: real_write(fd, bytes(data[:10])))
    assert lifecycle.install_loader() == 0
    monkeypatch.undo()
    assert bashrc.read_text() == "alias keep=me\n" + LOADER
    (backup,) = home.glob(".bashrc.idh-bak-*")
    assert backup.read_bytes() == b"alias keep=me\n"


@pytest.mark.parametrize("location", ["default", "arbitrary"])
def test_independent_profiles_survive_install_and_relocation(tmp_path, location):
    import shutil

    home = tmp_path / "home"
    home.mkdir()
    checkout = home / ".agents" if location == "default" else tmp_path / "a different checkout"
    shutil.copytree(REPO, checkout, symlinks=True)
    native = home / ".claude"
    native.mkdir()
    original = {"theme": "mine", "env": {"USER_FLAG": "kept"},
                "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                    {"type": "command", "command": "echo USER-HOOK"}]}]}}
    settings = native / "settings.json"
    settings.write_text(json.dumps(original))
    for rel in (".claude/rules/mine.md", ".claude/skills/custom/SKILL.md",
                ".codex/notes", ".pi/agent/extensions/custom.ts", ".claude/rules/doctype/user.md"):
        dest = home / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("user-owned")
    codex = home / ".codex/hooks.json"
    codex.write_text(json.dumps({"description": "my hooks", "hooks": original["hooks"]}))
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    for name in ("systemctl", "claude", "codex", "pi"):
        script = fakebin / name
        script.write_text(f'#!/bin/sh\necho "RUNTIME {name}"\n')
        script.chmod(0o755)
    env = {"HOME": str(home), "PATH": f"{home}/.local/bin:{fakebin}:/usr/bin:/bin"}

    def run(*args):
        return subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)

    result = run(sys.executable, str(checkout / "bin/idh"), "install")
    assert result.returncode == 0, result.stdout + result.stderr
    assert native.is_dir() and not native.is_symlink()
    merged = json.loads(settings.read_text())
    assert merged["theme"] == "mine" and merged["env"]["USER_FLAG"] == "kept"
    assert original["hooks"]["PreToolUse"][0] in merged["hooks"]["PreToolUse"]
    assert json.loads(codex.read_text())["description"] == "my hooks"
    before = settings.read_bytes(), codex.read_bytes()
    assert run("idh", "install").returncode == 0
    assert before == (settings.read_bytes(), codex.read_bytes())

    moved = tmp_path / "deeper" / "relocated harness"
    moved.parent.mkdir()
    checkout.rename(moved)
    # A move changes path topology; reinstall refreshes only recorded links.
    result = run(sys.executable, str(moved / "bin/idh"), "install")
    assert result.returncode == 0, result.stdout + result.stderr
    assert run("idh", "check").returncode == 0
    for runtime in ("claude", "codex", "pi"):
        result = run("bash", "--norc", "-c", f'source "$HOME/.bashrc"; {runtime} --version')
        assert result.returncode == 0 and f"RUNTIME {runtime}" in result.stdout, result.stderr
    for rel in (".claude/rules/mine.md", ".claude/skills/custom/SKILL.md",
                ".codex/notes", ".pi/agent/extensions/custom.ts", ".claude/rules/doctype/user.md"):
        assert (home / rel).read_text() == "user-owned"
    assert before == (settings.read_bytes(), codex.read_bytes())


def test_relocation_does_not_replace_a_modified_registered_link(machine):
    home, idh = machine["home"], machine["idh"]
    assert idh("install").returncode == 0
    link = home / ".pi/agent/extensions/idh-guard.ts"
    link.unlink()
    foreign = home / "foreign.ts"
    foreign.write_text("user-owned")
    link.symlink_to(foreign)
    result = idh("install")
    assert result.returncode == 1 and "FOREIGN:" in result.stderr
    assert link.resolve() == foreign
