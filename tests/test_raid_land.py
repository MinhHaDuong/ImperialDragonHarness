"""Ticket 1255: raid_land.py lands one request by /merge's recipe, behind a stubbed forge."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("raid_land", SCRIPTS / "raid_land.py")
assert spec and spec.loader
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)


def sh(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True,
                          text=True, env=child_env()).stdout.strip()


class StubForge:
    def __init__(self, head, body="", readback=None, armed=False, state="OPEN"):
        self.head, self.body, self.armed, self.state = head, body, armed, state
        self.readback = readback if readback is not None else f"MERGED {head} -"
        self.calls = []

    def resolve(self, pr):
        return {"state": self.state, "isDraft": False, "headRefName": "feat", "baseRefName": "main",
                "headRefOid": self.head, "body": self.body}

    def ready(self, pr): self.calls.append("ready")

    def auto_merge_armed(self, pr): return self.armed

    def disarm(self, pr): self.calls.append("disarm")

    def merge(self, pr, head, auto): self.calls.append(("merge", head, auto))

    def read_back(self, pr): return self.readback

    def comment(self, pr, body): self.calls.append("comment")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    sh(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    sh(tmp_path, "clone", "-q", str(origin), str(work))
    sh(work, "config", "user.email", "t@example.org")
    sh(work, "config", "user.name", "t")
    (work / "a.txt").write_text("a\n")
    sh(work, "add", "a.txt")
    sh(work, "commit", "-qm", "base")
    sh(work, "push", "-q", "origin", "HEAD:main")
    sh(work, "switch", "-qc", "feat")
    (work / "b.txt").write_text("b\n")
    sh(work, "add", "b.txt")
    sh(work, "commit", "-qm", "feat")
    sh(work, "push", "-q", "origin", "feat")
    monkeypatch.setattr(rl, "sync", lambda primary, base: ["sync-local-main: main fast-forwarded"])
    return work


def head(repo):
    return sh(repo, "rev-parse", "HEAD")


def land(repo, forge, ruled, **kw):
    out = []
    code = rl.land(forge, "7", ruled, "main", repo, out=out.append, **kw)
    return code, out


def merged_calls(forge):
    return [c for c in forge.calls if isinstance(c, tuple)]


def test_head_not_the_ruled_tip_refuses_and_never_merges(repo):
    forge = StubForge(head(repo))
    with pytest.raises(rl.Refusal, match="ruled tip"):
        land(repo, forge, "0" * 40)
    assert merged_calls(forge) == []


def test_second_stale_record_refuses(repo, monkeypatch):
    forge = StubForge(head(repo))
    monkeypatch.setattr(rl, "gate", lambda cwd, *a: 0 if a[0] == "enabled" else 2)
    with pytest.raises(rl.Refusal, match="stale twice"):
        land(repo, forge, head(repo))
    assert merged_calls(forge) == []


def test_moved_base_rerecords_once_then_merges_pinned(repo, monkeypatch):
    forge = StubForge(head(repo))
    seen = []
    checks = iter([2, 0])

    def gate(cwd, *a):
        seen.append(a[0])
        return 0 if a[0] in ("enabled", "run") else next(checks)

    monkeypatch.setattr(rl, "gate", gate)
    code, out = land(repo, forge, head(repo))
    assert code == 0 and seen == ["enabled", "check", "run", "check"]
    assert merged_calls(forge) == [("merge", head(repo), False)]


def test_armed_auto_merge_still_armed_refuses(repo, monkeypatch):
    forge = StubForge(head(repo), armed=True)
    monkeypatch.setattr(rl, "gate", lambda cwd, *a: 0)
    with pytest.raises(rl.Refusal, match="still armed"):
        land(repo, forge, head(repo))
    assert "disarm" in forge.calls and merged_calls(forge) == []


@pytest.mark.parametrize("back", [None, "MERGED " + "f" * 40 + " -", "CLOSED x -"])
def test_bad_read_back_refuses_and_merges_once(repo, back):
    forge = StubForge(head(repo), readback=back if back else None)
    if back is None:
        forge.readback = None
    with pytest.raises(rl.Refusal):
        land(repo, forge, "-")
    assert len(merged_calls(forge)) == 1


def test_happy_path_prints_one_row_and_syncs(repo):
    forge = StubForge(head(repo))
    code, out = land(repo, forge, head(repo))
    rows = [line.split() for line in out if " merge " in line]
    assert code == 0 and len(rows) == 1 and rows[0][:2] == ["7", "merge"]
    assert int(rows[0][3]) >= int(rows[0][2])
    assert merged_calls(forge) == [("merge", head(repo), True)]
    assert out[-1].startswith("sync-local-main")


def test_unsynced_main_exits_4_without_remerge(repo, monkeypatch):
    monkeypatch.setattr(rl, "sync", lambda p, b: ["sync-local-main: local main diverged — left untouched"])
    forge = StubForge(head(repo))
    code, out = land(repo, forge, "-")
    assert code == rl.UNSYNCED and len(merged_calls(forge)) == 1


def test_close_claims_ignore_fences_and_refs():
    body = "**Ticket:** tickets/0123-x.erg\nTicket-ref: tickets/0999-y.erg\n```\nTicket: tickets/0555-z.erg\n```\nTicket: none\n"
    assert rl.close_claims(body) == ["0123"]
    with pytest.raises(rl.Refusal):
        rl.close_claims("Ticket: 0123\n")
