"""trace_merge_path classes each merging session by the gate seen before it.

The probe answers "did a gate run before this merge?", so its two failure
modes both matter: a gated merge read as ungated sends the doctor chasing a
non-defect, and an ungated one read as gated hides a skipped gate. These
tests are its positive control: a raid session gated inside a subagent, a
bookkeeping merge, an ungated merge, a verify-gate load without `repo=`, and a
grep that only mentions `gh pr merge`.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import trace_merge_path as tmp_  # noqa: E402

STAMP = "2026-10-27T10:{:02d}:00.000Z"


def _skill(minute: int, skill: str, args: str = "") -> dict:
    return {"type": "assistant", "timestamp": STAMP.format(minute), "message": {"content": [
        {"type": "tool_use", "id": f"s{minute}", "name": "Skill", "input": {"skill": skill, "args": args}}]}}


def _bash(minute: int, command: str, result: str = "") -> list[dict]:
    use = {"type": "assistant", "timestamp": STAMP.format(minute), "message": {"content": [
        {"type": "tool_use", "id": f"b{minute}", "name": "Bash", "input": {"command": command}}]}}
    answer = {"type": "user", "timestamp": STAMP.format(minute), "message": {"content": [
        {"type": "tool_result", "tool_use_id": f"b{minute}", "content": result}]}}
    return [use, answer]


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def _fixture(root: Path) -> None:
    project = root / "-home-user-repo"
    # Raid: the gate runs in a subagent, the merge in the main session.
    _write(project / "aaaaaaaa-raid.jsonl", [_skill(1, "raid"), *_bash(9, "python3 scripts/raid_land.py 12 --ruled-head x")])
    _write(project / "aaaaaaaa-raid" / "subagents" / "agent-1.jsonl",
           [_skill(5, "verify-gate", "12 repo=/w session=u")])
    # Bookkeeping: a tier answer, no gate.
    _write(project / "bbbbbbbb-book.jsonl", [
        *_bash(1, 'python3 "$IDH_ROOT/scripts/merge-gate.py" tier --base origin/main --head HEAD',
               "bookkeeping: 1 path(s) changed"),
        *_bash(2, "gh pr merge 13 --merge --match-head-commit abc")])
    # Ungated: the only gate load lacks repo=, so it stopped; then a merge.
    _write(project / "cccccccc-skip.jsonl", [
        _skill(1, "merge"), _skill(2, "verify-gate", "14"),
        *_bash(3, "cd /w && gh pr merge 14 --merge")])
    # A grep that names the merge command merges nothing.
    _write(project / "dddddddd-grep.jsonl", [*_bash(1, "grep -n 'gh pr merge' skills/merge/SKILL.md")])
    # Before the window.
    _write(project / "eeeeeeee-old.jsonl", [
        {"type": "assistant", "timestamp": "2026-09-01T00:00:00.000Z", "message": {"content": [
            {"type": "tool_use", "id": "o", "name": "Bash", "input": {"command": "gh pr merge 1"}}]}}])


def test_classes_each_merging_session(tmp_path):
    _fixture(tmp_path)
    report = tmp_.survey(tmp_path, "2026-10-21")
    classes = {s["session"]: s["class"] for s in report["sessions"]}
    assert classes == {"aaaaaaaa": "gated", "bbbbbbbb": "bookkeeping", "cccccccc": "no gate seen"}
    assert (report["gate_loads"], report["gate_loads_norepo"]) == (2, 1)


def test_render_lists_only_unexplained_sessions(tmp_path):
    _fixture(tmp_path)
    text = tmp_.render(tmp_.survey(tmp_path, "2026-10-21"))
    assert "gated 1, bookkeeping 1, no gate seen 1" in text
    assert "cccccccc" in text and "aaaaaaaa" not in text


def test_disable_auto_is_not_a_merge():
    assert not tmp_.MERGE_RE.search("gh pr merge 12 --disable-auto")
    assert tmp_.MERGE_RE.search("cd /w && gh pr merge 12 --merge")
    assert tmp_.MERGE_RE.search("git fetch origin\ngh pr merge 12 --merge --match-head-commit abc")
