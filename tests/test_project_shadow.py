"""project_shadow.py: a project's directives that collide with the harness's
(ticket 1230). Fixture projects are non-git tmp dirs run against the real
harness checkout; the positive control is a local skill named like a harness
skill, the negative twin a skill that is not."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/project_shadow.py"


def run(project: Path, tmp_path: Path) -> list[dict]:
    env = child_env()
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path.parent)
    out = subprocess.run([sys.executable, str(SCRIPT), str(project)],
                         capture_output=True, text=True, env=env, check=True)
    return [json.loads(line) for line in out.stdout.splitlines() if line]


def skill(project: Path, rel: str, name: str, body: str = "") -> Path:
    path = project / rel / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\nname: {name}\ndescription: local {name}\n---\n{body}\n")
    return path


def test_name_collision_is_found(tmp_path):
    skill(tmp_path, ".claude/skills", "yawn")
    skill(tmp_path, ".claude/skills", "mine")
    (rec,) = run(tmp_path, tmp_path)
    assert rec["kind"] == "shadowing"
    assert rec["local_file"].endswith(".claude/skills/yawn/SKILL.md")
    assert rec["harness_file"].endswith("skills/yawn/SKILL.md")
    assert rec["verdict"] == "warn"
    assert rec["destination"] == "project"
    assert rec["disposition"] is None
    assert rec["instruction"]
    assert "mine" not in json.dumps(rec)


def test_no_collision_is_quiet(tmp_path):
    skill(tmp_path, ".claude/skills", "mine")
    assert run(tmp_path, tmp_path) == []


@pytest.mark.parametrize("rel", [".vibe/skills", ".pi/skills", ".agents/skills",
                                 "skills"])
def test_runtime_roots_and_toplevel_skills_are_scanned(tmp_path, rel):
    skill(tmp_path, rel, "yawn")
    (rec,) = run(tmp_path, tmp_path)
    assert rec["local_file"].endswith(f"{rel}/yawn/SKILL.md")


def test_rule_name_collision(tmp_path):
    rules = tmp_path / ".claude/rules"
    rules.mkdir(parents=True)
    (rules / "git.md").write_text("local git rule\n")
    (rec,) = run(tmp_path, tmp_path)
    assert rec["harness_file"].endswith("rules/git.md")
    assert rec["local_file"].endswith(".claude/rules/git.md")


def test_reason_in_place_is_ok(tmp_path):
    path = skill(tmp_path, ".claude/skills", "merge",
                 "Replaces the harness merge because this repo has no forge.")
    (rec,) = run(tmp_path, tmp_path)
    assert rec["verdict"] == "ok"
    assert "no forge" in rec["reason"]
    assert rec["local_file"] == str(path)


def test_malformed_local_skill_is_a_record_not_a_crash(tmp_path):
    path = tmp_path / ".claude/skills/yawn/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("no frontmatter\n")
    (rec,) = run(tmp_path, tmp_path)
    assert rec["kind"] == "shadowing" and rec["verdict"] == "warn"


def test_no_directives_skips_with_reason(tmp_path):
    (rec,) = run(tmp_path, tmp_path)
    assert rec["status"] == "skip" and rec["reason"]


def test_harness_and_its_worktree_skip():
    (rec,) = run(ROOT, ROOT.parent)
    assert rec["status"] == "skip" and "harness" in rec["reason"]


def test_is_harness_exit_codes(tmp_path):
    env = child_env()
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path.parent)
    def code(p):
        return subprocess.run([sys.executable, str(SCRIPT), "--is-harness",
                               str(p)], env=env).returncode
    assert code(ROOT) == 0
    assert code(tmp_path) == 1


def test_yawn_check_calls_the_script_through_the_seam():
    text = (ROOT / "skills/yawn/SKILL.md").read_text()
    assert 'python3 "$IDH_ROOT/scripts/project_shadow.py"' in text
    assert "ok (reasoned)" in text


def test_every_runtime_declares_project_skill_roots():
    data = json.loads((ROOT / "adapters/pilot-support.json").read_text())
    roots = {v["harness"]: v["project_skill_roots"] for v in data["versions"]}
    assert ".vibe/skills" in roots["vibe"] and ".pi/skills" in roots["pi"]
    assert ".claude/skills" in roots["claude"]


def test_undecodable_skill_and_broken_rule_link_are_records(tmp_path):
    bad = tmp_path / ".claude/skills/yawn/SKILL.md"
    bad.parent.mkdir(parents=True)
    bad.write_bytes(b"\xff\xfe\x00bad")
    rules = tmp_path / ".claude/rules"
    rules.mkdir(parents=True)
    (rules / "git.md").symlink_to("/nonexistent")
    recs = run(tmp_path, tmp_path)
    assert len(recs) == 1 or len(recs) == 2
    assert {r["verdict"] for r in recs} == {"warn"}


def test_frontmatter_words_are_not_a_reason(tmp_path):
    path = tmp_path / ".claude/skills/yawn/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: yawn\ndescription: Runs since midnight\n---\nbody\n")
    (rec,) = run(tmp_path, tmp_path)
    assert rec["verdict"] == "warn"


def test_symlinked_roots_yield_one_record(tmp_path):
    skill(tmp_path, ".agents/skills", "yawn")
    (tmp_path / ".pi").mkdir()
    (tmp_path / ".pi/skills").symlink_to(tmp_path / ".agents/skills")
    assert len(run(tmp_path, tmp_path)) == 1
