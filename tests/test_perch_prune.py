"""idh install prunes dangling links into .agents/skills, and only those (ticket 1128)."""

import importlib.util
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _module():
    spec = importlib.util.spec_from_file_location("perch_prune", REPO / "adapters" / "perch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


perch = _module()


def test_prune_dangling_keeps_live_and_foreign(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    live_src = tmp_path / ".agents" / "skills" / "live"
    live_src.mkdir(parents=True)
    os.symlink(live_src, root / "live")
    os.symlink(tmp_path / ".agents" / "skills" / "gone", root / "gone")
    os.symlink(tmp_path / "code" / "arena" / "skills" / "arena", root / "arena")

    messages = perch.prune_dangling("claude")

    assert len(messages) == 1 and "gone" in messages[0]
    assert not os.path.lexists(root / "gone")
    assert (root / "live").is_symlink()
    assert os.path.islink(root / "arena")


def test_prune_dangling_without_root(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert perch.prune_dangling("claude") == []
