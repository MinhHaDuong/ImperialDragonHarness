"""idh install prunes dangling links into .agents/skills, and only those (ticket 1128)."""

import importlib.util
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _module():
    spec = importlib.util.spec_from_file_location("lifecycle_prune", REPO / "adapters" / "lifecycle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lifecycle = _module()


def test_prune_dangling_keeps_live_and_foreign(tmp_path, capsys):
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    live_src = tmp_path / ".agents" / "skills" / "live"
    live_src.mkdir(parents=True)
    os.symlink(live_src, root / "live")
    os.symlink(tmp_path / ".agents" / "skills" / "gone", root / "gone")
    os.symlink(tmp_path / "code" / "arena" / "skills" / "arena", root / "arena")

    assert lifecycle.prune_dangling([root]) == 0

    out = capsys.readouterr().out.splitlines()
    assert len(out) == 1 and "gone" in out[0]
    assert not os.path.lexists(root / "gone")
    assert (root / "live").is_symlink()
    assert os.path.islink(root / "arena")


def test_prune_dangling_without_root(tmp_path):
    assert lifecycle.prune_dangling([tmp_path / "absent"]) == 0


def test_prune_dangling_requires_tail_shape(tmp_path):
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    agents = tmp_path / ".agents" / "skills"
    os.symlink(agents / "other", root / "renamed")  # name differs from target
    os.symlink(agents / "x" / "sub", root / "sub")  # deeper than .agents/skills/<name>

    assert lifecycle.prune_dangling([root]) == 0
    assert os.path.islink(root / "renamed") and os.path.islink(root / "sub")


def test_prune_dangling_oserror_is_reported_and_sweep_continues(tmp_path, monkeypatch, capsys):
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    for name in ("a", "b", "c"):
        os.symlink(tmp_path / ".agents" / "skills" / name, root / name)
    real = Path.unlink

    def flaky(self, *args, **kwargs):
        if self.name == "b":
            raise PermissionError(13, "Permission denied")
        real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", flaky)
    assert lifecycle.prune_dangling([root]) == 1
    captured = capsys.readouterr()
    assert "could not prune dangling link" in captured.err and "pruned dangling link" in captured.out
    assert not os.path.lexists(root / "a") and not os.path.lexists(root / "c")
    assert os.path.islink(root / "b")


def test_skill_roots_are_the_manifest_children_roots(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    roots = lifecycle.skill_roots()
    assert tmp_path / ".claude" / "skills" in roots
    assert all(r.name == "skills" for r in roots)
    assert tmp_path / ".pi" / "agent" / "skills" not in roots  # Pi reads ~/.agents/skills


def test_plain_install_runs_the_prune(monkeypatch, tmp_path):
    swept = []
    monkeypatch.setattr(lifecycle, "prune_dangling", lambda roots: swept.append(roots) or 0)
    monkeypatch.setattr(lifecycle, "entries", lambda runtime=None: [])
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("HOME", str(tmp_path))  # install_links also links bin/* under $HOME
    lifecycle.install_links()
    assert swept, "plain idh install must run the dangling-link sweep"


def test_prune_dangling_link_gone_meanwhile_is_not_a_refusal(tmp_path, monkeypatch, capsys):
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    os.symlink(tmp_path / ".agents" / "skills" / "gone", root / "gone")
    real = Path.unlink

    def vanish_first(self, *args, **kwargs):
        real(self, missing_ok=True)  # a concurrent install got there first
        real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", vanish_first)
    assert lifecycle.prune_dangling([root]) == 0
    assert "REFUSED" not in capsys.readouterr().err
