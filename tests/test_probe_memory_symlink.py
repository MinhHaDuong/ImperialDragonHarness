"""Tests for scripts/probe-memory-symlink.py (ticket 0984).

The offline half pins the pieces the live probe's verdict rests on: the
project-slug rule, the disposable-HOME rig, the refusal to build it over the
real HOME, and the sentinel detector. The live half runs the probe itself and
is skipped unless IDH_LIVE_PROBE=1 (network, Anthropic auth, a few haiku calls).
"""

import importlib.util
import os
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
    """A stand-in for the live HOME, holding a .claude.json to copy."""
    home = tmp_path / "live"
    home.mkdir()
    (home / ".claude.json").write_bytes(b'{"projects": {"/a": {}}}\n')
    return home


def _mem(rig):
    return rig.home / ".claude" / "projects" / pm.slug_for(rig.work) / "memory"


def test_build_rig_copies_claude_json_byte_identical(tmp_path, live):
    rig = pm.build_rig(tmp_path / "rig", "SENT-1", mode="real", live_home=live)
    assert (rig.home / ".claude.json").read_bytes() == (live / ".claude.json").read_bytes()


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


@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("IDH_LIVE_PROBE") != "1", reason="live probe: set IDH_LIVE_PROBE=1")
def test_live_probe_control_fires():
    report = pm.run_probe()
    assert report["control"] == "loaded", report
