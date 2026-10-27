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
REAL_SYNC = rl.sync


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

    def read_back(self, pr):
        self.reads = getattr(self, "reads", 0) + 1
        return self.readback

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
    monkeypatch.setattr(rl, "sync", lambda primary, base: (True, ["sync-local-main: main fast-forwarded"]))
    return work


def head(repo):
    return sh(repo, "rev-parse", "HEAD")


def land(repo, forge, ruled, **kw):
    out = []
    kw.setdefault("ruled_claims", [])
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
        land(repo, forge, head(repo))
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
    monkeypatch.setattr(rl, "sync", lambda p, b: (False, ["sync-local-main: local main diverged — left untouched"]))
    forge = StubForge(head(repo))
    code, out = land(repo, forge, head(repo))
    assert code == rl.UNSYNCED and len(merged_calls(forge)) == 1


def test_close_claims_ignore_fences_and_refs():
    body = "**Ticket:** tickets/0123-x.erg\nTicket-ref: tickets/0999-y.erg\n```\nTicket: tickets/0555-z.erg\n```\nTicket: none\n"
    assert rl.close_claims(body) == ["0123"]
    with pytest.raises(rl.Refusal):
        rl.close_claims("Ticket: 0123\n")


def test_body_claims_differing_from_ruled_set_refuse(repo):
    forge = StubForge(head(repo), body="**Ticket:** tickets/0123-x.erg\n")
    with pytest.raises(rl.Refusal, match="close claims"):
        land(repo, forge, head(repo), ruled_claims=["0999"])
    assert merged_calls(forge) == []


def test_body_edited_between_reads_refuses(repo):
    forge = StubForge(head(repo))
    reads = [""]
    orig = forge.resolve

    def resolve(pr):
        info = orig(pr)
        info["body"] = "".join(reads)
        reads[:] = ["**Ticket:** tickets/0123-x.erg\n"]
        return info

    forge.resolve = resolve
    with pytest.raises(rl.Refusal, match="close claims"):
        land(repo, forge, head(repo))
    assert merged_calls(forge) == []


def test_dash_ruled_head_still_requires_bookkeeping_tier(repo, monkeypatch):
    forge = StubForge(head(repo))
    monkeypatch.setattr(rl, "gate", lambda cwd, *a: 1 if a[0] == "tier" else 0)
    with pytest.raises(rl.Refusal, match="not bookkeeping"):
        land(repo, forge, "-")
    assert merged_calls(forge) == []


def test_attribution_warning_surfaced_never_refuses(repo, monkeypatch):
    monkeypatch.setattr(rl, "attribution", lambda body: "missing")
    forge = StubForge(head(repo))
    code, out = land(repo, forge, head(repo))
    assert code == 0 and any("attribution: missing" in line for line in out)


def test_duration_comment_posted_after_merge(repo):
    forge = StubForge(head(repo))
    forge.comment = lambda pr, body: forge.calls.append(("comment", body))
    land(repo, forge, head(repo))
    comments = [c for c in forge.calls if c[0] == "comment"]
    assert len(comments) == 1 and f"merge {head(repo)}: duration: " in comments[0][1]


def test_exception_after_merge_is_outcome_unknown_code_6(repo):
    forge = StubForge(head(repo))
    forge.read_back = lambda pr: (_ for _ in ()).throw(OSError("boom"))
    out = []
    code = rl.main_land(forge, "7", head(repo), [], "main", repo, out.append)
    assert code == rl.UNKNOWN and len(merged_calls(forge)) == 1
    assert any("outcome unknown" in line for line in out)
    assert any(line.startswith("read-back now: unreadable") for line in out)


def test_bad_read_back_is_code_6_not_1(repo):
    forge = StubForge(head(repo), readback="CLOSED x -")
    out = []
    assert rl.main_land(forge, "7", head(repo), [], "main", repo, out.append) == rl.UNKNOWN
    assert forge.reads == 2 and "read-back now: CLOSED x -" in out


def test_missing_sync_script_after_merge_is_code_4(repo, monkeypatch):
    monkeypatch.setattr(rl, "sync", REAL_SYNC)
    monkeypatch.setattr(rl, "SYNC", Path("/nonexistent/sync.sh"))
    forge = StubForge(head(repo))
    code, out = land(repo, forge, head(repo))
    assert code == rl.UNSYNCED


@pytest.mark.parametrize("stdout,rc,want", [
    ("sync-local-main: main fast-forwarded at /x (a -> b)\n", 0, True),
    ("sync-local-main: main updated by ref a -> b\n", 0, True),
    ("", 0, False),
    ("something odd\n", 0, False),
    ("sync-local-main: main fast-forwarded at /x (a -> b)\n", 2, False),
])
def test_sync_result_needs_known_success_line(tmp_path, monkeypatch, stdout, rc, want):
    script = tmp_path / "s.sh"
    script.write_text(f"#!/bin/sh\nprintf '%s' '{stdout}'\nexit {rc}\n".replace("\\n", "\n"))
    script.chmod(0o755)
    monkeypatch.setattr(rl, "SYNC", script)
    assert REAL_SYNC(tmp_path, "main")[0] is want


def refused_merge(forge):
    def merge(pr, h, auto):
        forge.calls.append(("merge", h, auto))
        raise rl.MergeRefused("head moved")
    forge.merge = merge


def test_forge_refused_merge_with_open_read_back_at_same_head_is_definite_refusal(repo):
    forge = StubForge(head(repo), readback=f"OPEN {head(repo)} -")
    refused_merge(forge)
    out = []
    assert rl.main_land(forge, "7", head(repo), [], "main", repo, out.append) == rl.REFUSED
    assert not any("outcome unknown" in line for line in out)


def test_forge_refused_merge_with_other_read_back_stays_unknown(repo):
    forge = StubForge(head(repo), readback="MERGED " + "f" * 40 + " -")
    refused_merge(forge)
    assert rl.main_land(forge, "7", head(repo), [], "main", repo, [].append) == rl.UNKNOWN


def test_usage_line_names_ruled_claims():
    assert "--ruled-claims" in rl.__doc__.splitlines()[2]


def test_create_returns_the_request_number_and_refuses_without_one(monkeypatch):
    """Ticket 1251: GhForge.create, the red ticket's request, parsed from gh's URL; gh itself is stubbed."""
    forge = rl.GhForge()
    seen = []

    def fake(*args, out="https://github.com/o/r/pull/42\n", code=0):
        seen.append(args)
        return subprocess.CompletedProcess(args, code, out, "")

    monkeypatch.setattr(forge, "_gh", fake)
    assert forge.create("red-abc", "main", "t", "b") == "42"
    assert seen[0][:6] == ("pr", "create", "--head", "red-abc", "--base", "main")
    monkeypatch.setattr(forge, "_gh", lambda *a: subprocess.CompletedProcess(a, 1, "", "denied"))
    with pytest.raises(rl.Refusal):
        forge.create("red-abc", "main", "t", "b")
