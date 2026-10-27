"""The harness doctor is an author-called lint of the harness's own skills and rules.

Pinned here: a model cannot start it, it refuses outside the harness, it points
at its references and the lint script rather than restating them, and the
skill-writing guide moved under it while a path-scoped stub keeps the
edit-time prompt. The lint itself is never run over live skills here: the
script is an instrument, not a gate.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import skill_frontmatter as sf  # noqa: E402

DOCTOR = REPO / "skills" / "harness-doctor"
SKILL = DOCTOR / "SKILL.md"
HERE = REPO / "scripts" / "harness_here.sh"
STUB = REPO / "rules" / "authoring-skills.md"
POINTER = re.compile(r"`references/([\w.-]+\.md)`")


def test_the_doctor_cannot_be_invoked_by_a_model():
    meta = sf.load(SKILL)
    assert meta["disable-model-invocation"] is True
    assert meta["user-invocable"] is True
    assert meta["name"] == "harness-doctor"


def _here(cwd, env=None):
    return subprocess.run(["bash", str(HERE)], cwd=cwd, env=env,
                          capture_output=True, text=True)


@pytest.mark.integration
@pytest.mark.parametrize("repo", [True, False], ids=["foreign-repo", "no-repo"])
def test_refusal_outside_harness(tmp_path, repo):
    if repo:
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    out = _here(tmp_path)
    assert out.returncode == 1
    assert len(out.stderr.strip().splitlines()) == 1


@pytest.mark.integration
def test_refusal_ignores_an_exported_git_dir(tmp_path):
    """An exported GIT_DIR pointing at the harness must not admit a foreign cwd."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git_dir = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--path-format=absolute",
         "--git-common-dir"], capture_output=True, text=True, check=True).stdout.strip()
    out = _here(tmp_path, env={**os.environ, "GIT_DIR": git_dir})
    assert out.returncode == 1


@pytest.mark.integration
def test_the_harness_is_accepted():
    inside = _here(REPO / "skills")
    assert inside.returncode == 0, inside.stderr


def test_skill_names_its_references_and_script():
    body = SKILL.read_text(encoding="utf-8")
    assert set(POINTER.findall(body)) >= {
        "authoring-skills.md", "checklist.md", "evidence.md",
        "runtime-diagnostics.md"}
    assert '"$IDH_ROOT/scripts/skill_text_lint.py"' in body
    assert '"$IDH_ROOT/scripts/harness_here.sh"' in body


def test_stub_keeps_paths_and_points_to_reference():
    text = STUB.read_text(encoding="utf-8")
    meta = sf.load(STUB)
    assert set(meta["paths"]) == {"**/SKILL.md", "**/skills/**/*.md"}
    assert "skills/harness-doctor/references/authoring-skills.md" in text
    assert (DOCTOR / "references" / "authoring-skills.md").is_file()
