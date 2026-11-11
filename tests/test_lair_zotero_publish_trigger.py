"""Lair offers `/zotero publish-notes` for drafts ahead of the local publish
record, from local files only (ticket 1527)."""
import hashlib
import json
import subprocess
from pathlib import Path

from child_env import child_env

ROOT = Path(__file__).resolve().parent.parent
TRIGGER = ROOT / "skills" / "lair" / "zotero-publish-trigger"
BODY = "<h1>Note</h1>\n<p>text</p>\n"


def draft(project: Path, rel: str, body: str = BODY, status: str = "draft") -> Path:
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\nzotero_item: "ABCD2345"\nstatus: {status}\n---\n{body}')
    return path


def record(state: Path, key: str, body: str = BODY) -> None:
    notes = json.loads(state.read_text())["notes"] if state.exists() else {}
    notes[key] = {"sha256": hashlib.sha256(body.encode()).hexdigest()}
    state.write_text(json.dumps({"notes": notes}))


def run(project: Path, state: Path) -> str:
    env = {**child_env(), "XDG_STATE_HOME": str(state)}
    out = subprocess.run([str(TRIGGER), str(project), "proj"], capture_output=True,
                         text=True, check=True, env=env)
    return out.stdout


def state_file(tmp_path: Path) -> Path:
    return tmp_path / "state" / "idh" / "zotero" / "publish-notes.json"


def test_no_state_file_counts_all_drafts(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/a.html")
    draft(proj, "wiki/references/b.html")
    draft(proj, "reading-notes/sub/c.html")
    out = run(proj, tmp_path / "state")
    assert out.count("\n") == 1
    assert "3 merged notes not yet published" in out
    assert "/zotero publish-notes" in out


def test_drafts_ahead_one_line(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/a.html")
    draft(proj, "wiki/works/b.html")
    st = state_file(tmp_path)
    st.parent.mkdir(parents=True)
    record(st, "proj/a")
    out = run(proj, tmp_path / "state")
    assert out.count("\n") == 1 and "1 merged note not yet published" in out


def test_in_step_is_silent(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/a.html")
    st = state_file(tmp_path)
    st.parent.mkdir(parents=True)
    record(st, "proj/a")
    assert run(proj, tmp_path / "state") == ""


def test_frontmatter_only_change_is_still_in_step(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/a.html", status="published")
    st = state_file(tmp_path)
    st.parent.mkdir(parents=True)
    record(st, "proj/a")
    assert run(proj, tmp_path / "state") == ""


def test_changed_body_is_ahead(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/a.html", body="<p>new</p>\n")
    st = state_file(tmp_path)
    st.parent.mkdir(parents=True)
    record(st, "proj/a")
    assert "1 merged note" in run(proj, tmp_path / "state")


def test_no_drafts_is_silent(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "README.md").write_text("x")
    assert run(proj, tmp_path / "state") == ""


def test_only_merged_drafts_count_in_a_git_repo(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/merged.html")
    draft(proj, "wiki/works/wip.html")
    git = ["git", "-C", str(proj), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True, env=child_env())
    subprocess.run([*git, "add", "wiki/works/merged.html"], check=True, env=child_env())
    subprocess.run([*git, "commit", "-qm", "m"], check=True, env=child_env())
    assert "1 merged note not yet published" in run(proj, tmp_path / "state")


def test_unreadable_state_counts_all(tmp_path):
    proj = tmp_path / "proj"
    draft(proj, "wiki/works/a.html")
    st = state_file(tmp_path)
    st.parent.mkdir(parents=True)
    st.write_text("not json")
    assert "1 merged note" in run(proj, tmp_path / "state")
