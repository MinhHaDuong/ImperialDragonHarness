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


def test_prune_dangling_requires_tail_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    agents = tmp_path / ".agents" / "skills"
    os.symlink(agents / "other", root / "renamed")  # name differs from target
    os.symlink(agents / "x" / "sub", root / "sub")  # deeper than .agents/skills/<name>

    assert perch.prune_dangling("claude") == []
    assert os.path.islink(root / "renamed") and os.path.islink(root / "sub")


def test_prune_dangling_oserror_is_a_refusal_and_sweep_continues(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    for name in ("a", "b", "c"):
        os.symlink(tmp_path / ".agents" / "skills" / name, root / name)
    real = perch._unlink

    def flaky(entry):
        if entry.name == "b":
            raise PermissionError(13, "Permission denied")
        real(entry)

    monkeypatch.setattr(perch, "_unlink", flaky)
    try:
        perch.prune_dangling("claude")
    except perch.Refusal as exc:
        text = str(exc)
    else:
        raise AssertionError("expected Refusal")
    assert "could not prune dangling link" in text and "pruned dangling link" in text
    assert not os.path.lexists(root / "a") and not os.path.lexists(root / "c")
    assert os.path.islink(root / "b")


def test_main_install_reports_prune_failure_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(perch, "check_version", lambda *a, **k: "1.0.0")
    monkeypatch.setattr(perch, "install", lambda *a, **k: "ok")
    monkeypatch.setattr(perch, "prune_dangling", lambda h: (_ for _ in ()).throw(perch.Refusal("boom")))
    assert perch.main(["install", "skill", "perch"]) == 2
    assert "idh: boom" in capsys.readouterr().err


def test_main_install_sweeps_shared_root_once(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(perch, "check_version", lambda *a, **k: "1.0.0")
    monkeypatch.setattr(perch, "install", lambda *a, **k: "ok")
    swept = []
    monkeypatch.setattr(perch, "prune_dangling", lambda h: swept.append(h) or [])
    assert perch.main(["install", "skill", "perch"]) == 0
    roots = {perch.target_path(h, "x").parent for h in swept}
    assert len(swept) == len(roots)
    assert "codex" not in swept or "pi" not in swept
