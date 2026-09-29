"""Tests for scripts/probe-memory-symlink.py (ticket 0984).

The offline half pins the pieces the live probe's verdict rests on: the
project-slug rule, the disposable-HOME rig, the refusal to build it over the
real HOME, the sentinel detector, the launch-failure and retry rules, and the
secret hygiene of the API key. The live half runs the probe itself and is
skipped unless IDH_LIVE_PROBE=1 (network, Anthropic auth, a few haiku calls).
"""

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "probe-memory-symlink.py"
spec = importlib.util.spec_from_file_location("probe_memory_symlink", SCRIPT)
pm = importlib.util.module_from_spec(spec)
sys.modules["probe_memory_symlink"] = pm
spec.loader.exec_module(pm)


@pytest.mark.parametrize(
    "path, slug",
    [
        ("/srv/x/.claude", "-srv-x--claude"),
        # A "/"-only replacement fails here: the dot must become a dash too.
        ("/tmp/a.b/c", "-tmp-a-b-c"),
    ],
)
def test_slug_for(path, slug):
    assert pm.slug_for(Path(path)) == slug


@pytest.fixture
def live(tmp_path):
    """A stand-in for the live HOME, holding a .claude.json the rig must NOT copy."""
    home = tmp_path / "live"
    home.mkdir()
    (home / ".claude.json").write_text(
        '{"projects": {"/a": {}}, "mcpServers": {"x": {}}}\n'
    )
    return home


def _mem(rig):
    return rig.home / ".claude" / "projects" / pm.slug_for(rig.work) / "memory"


def test_build_rig_writes_a_minimal_private_claude_json(tmp_path, live):
    rig = pm.build_rig(tmp_path / "rig", "SENT-1", mode="real", live_home=live)
    cj = rig.home / ".claude.json"
    assert cj.read_text().strip() == '{"projects": {}}'
    assert stat.S_IMODE(cj.stat().st_mode) == 0o600


def test_build_rig_real_mode_writes_sentinel_in_a_real_file(tmp_path, live):
    rig = pm.build_rig(tmp_path / "rig", "SENT-2", mode="real", live_home=live)
    mem = _mem(rig)
    assert not mem.is_symlink()
    assert "SENT-2" in (mem / "MEMORY.md").read_text()
    # The work dir is its own git root, so memory keys on it and not an ancestor.
    assert (rig.work / ".git").is_dir()


def test_build_rig_symlink_mode_links_memory_to_the_sentinel(tmp_path, live):
    rig = pm.build_rig(tmp_path / "rig", "SENT-3", mode="symlink", live_home=live)
    mem = _mem(rig)
    assert mem.is_symlink()
    target = mem.resolve()
    assert target != mem.absolute()
    assert "SENT-3" in (target / "MEMORY.md").read_text()


def test_build_rig_refuses_the_real_home(live):
    with pytest.raises(ValueError):
        pm.build_rig(live, "SENT-4", mode="real", live_home=live)


def test_build_rig_refuses_a_path_inside_the_real_home(live):
    with pytest.raises(ValueError):
        pm.build_rig(live / "sub", "SENT-5", mode="real", live_home=live)


def test_detect_loaded_true_on_sentinel():
    assert pm.detect_loaded("The codeword is SENT-6.\n", "SENT-6")


def test_detect_loaded_false_without_sentinel():
    assert not pm.detect_loaded("NONE\n", "SENT-7")


def test_detect_loaded_false_on_echoed_prompt():
    assert not pm.detect_loaded(pm.PROMPT + "\nNONE\n", "SENT-8")


@pytest.mark.parametrize(
    "launch, expected",
    [
        (pm.Launch("", "timeout"), "could not look (timeout)"),
        (pm.Launch("SENT-9\n", "exit 1"), "could not look (exit 1)"),
        (pm.Launch("", "exit 0"), "could not look (exit 0)"),
        (pm.Launch("NONE\n", "exit 0"), "not loaded"),
        (pm.Launch("SENT-9\n", "exit 0"), "loaded"),
    ],
)
def test_verdict_separates_a_failed_launch_from_a_negative(launch, expected):
    # A timeout or rate limit must not read as "links are not followed".
    assert pm.verdict(launch, "SENT-9") == expected


@pytest.mark.parametrize(
    "results, expected",
    [
        (["loaded"], "loaded"),
        (["not loaded", "not loaded"], "not loaded (retry agrees)"),
        (["not loaded", "loaded"], "inconclusive (retry: loaded)"),
        (["could not look (timeout)"], "could not look (timeout)"),
    ],
)
def test_a_negative_needs_a_retry_that_agrees(results, expected):
    it = iter(results)
    assert pm.confirm_negative(lambda: next(it)) == expected


def test_bad_timeout_env_does_not_break_import(monkeypatch):
    monkeypatch.setenv("PROBE_TIMEOUT", "soon")
    assert pm._timeout() == 150


# --- API key hygiene -------------------------------------------------------

KEY_SENTINEL = (
    "sk-probe-test KEYSENTINEL-5e1f"  # a space: a hand-rolled parse truncates it
)


@pytest.fixture
def key_file(tmp_path):
    f = tmp_path / "keys" / "anthropic.env"
    f.parent.mkdir()
    f.write_text(f'# test provider\nANTHROPIC_API_KEY="{KEY_SENTINEL}"\n')
    return f


def test_resolve_api_key_reads_the_sourced_value(key_file):
    assert pm.resolve_api_key(key_file) == KEY_SENTINEL


@pytest.mark.parametrize("content", [None, "OTHER_KEY=x\n"])
def test_no_key_refuses_without_launching_or_copying(
    tmp_path, live, monkeypatch, content
):
    kf = tmp_path / "missing.env"
    if content is not None:
        kf.write_text(content)
    monkeypatch.setattr(
        pm, "_launch", lambda *a, **k: pytest.fail("launched without a key")
    )
    before = sorted(p.name for p in live.rglob("*"))
    r = pm.run_probe(live_home=live, key_file=kf)
    assert r["control"] == "could not look: no API key"
    assert sorted(p.name for p in live.rglob("*")) == before


@pytest.mark.integration
def test_key_reaches_the_child_env_only_never_output(
    tmp_path, key_file, monkeypatch, capsys
):
    """Whole probe against a fake `claude`: it answers with whichever memory its
    physical cwd keys to, and records the env and argv it was handed."""
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    rigs = tmp_path / "rigs"
    rigs.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr(pm, "KEY_FILE", key_file)
    monkeypatch.setattr(pm.shutil, "which", lambda name: "/fake/claude")
    monkeypatch.setattr(pm.tempfile, "tempdir", str(rigs))
    real_run = subprocess.run
    calls = []

    def fake_run(cmd, *a, **kw):
        if cmd[0] == "claude":
            return subprocess.CompletedProcess(cmd, 0, "0.0.0 (fake)\n", "")
        return real_run(cmd, *a, **kw)

    class FakePopen:
        def __init__(self, cmd, **kw):
            calls.append((list(cmd), dict(kw["env"])))
            cwd = Path(kw["cwd"]).resolve()
            home = Path(kw["env"]["HOME"])
            mem = (
                home
                / ".claude"
                / "projects"
                / pm.slug_for(cwd)
                / "memory"
                / "MEMORY.md"
            )
            self.out = mem.read_text() if mem.exists() else "NONE\n"
            self.returncode = 0
            self.pid = -1

        def communicate(self, timeout=None):
            return self.out, ""

    real_popen = subprocess.Popen

    def fake_popen(cmd, *a, **kw):
        # Only `claude` is faked; bash (the keystore reader) and git run for real.
        if cmd[0] == "claude":
            return FakePopen(cmd, **kw)
        return real_popen(cmd, *a, **kw)

    monkeypatch.setattr(pm.subprocess, "run", fake_run)
    monkeypatch.setattr(pm.subprocess, "Popen", fake_popen)
    assert pm.main([]) == 0
    out, err = capsys.readouterr()
    assert calls, "the fake claude was never launched"
    for argv, env in calls:
        assert env["ANTHROPIC_API_KEY"] == KEY_SENTINEL
        assert not any("KEYSENTINEL" in a for a in argv)
    assert "KEYSENTINEL" not in out + err
    assert "control   memory in a real file    loaded" in out
    assert "symlink   memory dir is a link     loaded" in out
    assert out.count("memory=slug(target)") == 2
    last = out.strip().splitlines()[-1].split()
    assert last[:4] == ["live", "HOME", "tagged", "entries"] and last[-1] == "none"
    assert not list(rigs.iterdir()), "the rig outlived the run"


def test_rig_is_removed_when_a_case_raises(tmp_path, key_file, live, monkeypatch):
    rigs = tmp_path / "rigs"
    rigs.mkdir()
    monkeypatch.setattr(pm.tempfile, "tempdir", str(rigs))
    monkeypatch.setattr(pm, "_version", lambda: "fake")

    def boom(*a, **k):
        raise SystemExit(143)  # what the SIGTERM handler raises

    monkeypatch.setattr(pm, "_memory_case", boom)
    with pytest.raises(SystemExit):
        pm.run_probe(live_home=live, key_file=key_file)
    assert not list(rigs.iterdir())


@pytest.mark.parametrize(
    "second, expected",
    [
        (["none"], ["none (retry agrees)"]),
        (["slug(target)"], ["inconclusive (retry: slug(target))"]),
    ],
)
def test_cwd_key_none_needs_a_retry_that_agrees(
    tmp_path, live, monkeypatch, second, expected
):
    results = iter([{"memory": ["none"]}, {"memory": second}])
    monkeypatch.setattr(pm, "_cwd_key_case", lambda *a, **k: next(results))
    assert pm._cwd_key_confirmed(tmp_path, live, True, "k")["memory"] == expected


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("IDH_LIVE_PROBE") != "1", reason="live probe: set IDH_LIVE_PROBE=1"
)
def test_live_probe_control_fires():
    report = pm.run_probe()
    assert report["control"] == "loaded", report
