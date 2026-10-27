"""The harness doctor is an author-called visit to the harness's own skills and rules.

Pinned here: a model cannot start it, it refuses outside the harness, it points
at its references and the lint script rather than restating them, and the
skill-writing guide moved under it while a path-scoped stub keeps the
edit-time prompt. The doctor runs as a visit: the refusal precedes the probe
menu, the menu is a table, the frozen control fixture keeps firing, the empty
revisit is stated and no retirement clause survives. The lint runs here only
on the doctor's own skill and its control, never as a gate over live skills.
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import skill_frontmatter as sf  # noqa: E402
import skill_text_lint as stl  # noqa: E402

DOCTOR = REPO / "skills" / "harness-doctor"
SKILL = DOCTOR / "SKILL.md"
HERE = REPO / "scripts" / "harness_here.sh"
STUB = REPO / "rules" / "authoring-skills.md"
POINTER = re.compile(r"`references/([\w.-]+\.md)`")
CONTROL = REPO / "tests" / "fixtures" / "harness-doctor" / "trace-doctor-SKILL.md"
# The control is frozen: a copy edited or swapped for a weaker file could still
# raise the four checks yet stop being the case the doctor's report names.
CONTROL_SHA256 = "445e4276f655e2d38fff918d78dcba890d829347651a6efa26baec7318aa6e7a"
CONTROL_CHECKS = {"body_lines", "date", "history_phase", "long_fence"}


def _sections(text):
    """Map each `## ` heading to (start offset, body up to the next heading)."""
    heads = [(m.start(), m.group(1).strip())
             for m in re.finditer(r"^## (.+)$", text, re.MULTILINE)]
    out = {}
    for i, (start, title) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        out[title] = (start, text[start:end])
    return out


def _section(text, prefix):
    hits = [v for k, v in _sections(text).items() if k.startswith(prefix)]
    assert len(hits) == 1, f"expected one section starting {prefix!r}"
    return hits[0]


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
@pytest.mark.parametrize("var", ["GIT_DIR", "GIT_COMMON_DIR"])
def test_refusal_ignores_an_exported_git_dir(tmp_path, var):
    """An exported repository override pointing at the harness must not admit a foreign cwd."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git_dir = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--path-format=absolute",
         "--git-common-dir"], capture_output=True, text=True, check=True).stdout.strip()
    out = _here(tmp_path, env={**os.environ, var: git_dir})
    assert out.returncode == 1


@pytest.mark.integration
def test_refusal_ignores_an_exported_work_tree(tmp_path):
    """GIT_WORK_TREE plus GIT_DIR at the harness must not admit a foreign cwd either."""
    git_dir = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-dir"],
        capture_output=True, text=True, check=True).stdout.strip()
    env = {**os.environ, "GIT_DIR": git_dir, "GIT_WORK_TREE": str(REPO)}
    assert _here(tmp_path, env=env).returncode == 1


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
    assert "skills/test-doctor/SKILL.md" in body
    assert (REPO / "skills" / "test-doctor" / "SKILL.md").is_file()


def test_stub_keeps_paths_and_points_to_reference():
    text = STUB.read_text(encoding="utf-8")
    meta = sf.load(STUB)
    assert set(meta["paths"]) == {"**/SKILL.md", "**/skills/**/*.md"}
    assert "skills/harness-doctor/references/authoring-skills.md" in text
    assert (DOCTOR / "references" / "authoring-skills.md").is_file()


def test_control_fixture_fires_every_listed_check():
    """The frozen control must keep firing: a silent control means a blind probe."""
    assert hashlib.sha256(CONTROL.read_bytes()).hexdigest() == CONTROL_SHA256
    result = stl.lint(REPO, stl.DEFAULT_PROJECTS, [CONTROL])
    assert set(result["summary"]) >= CONTROL_CHECKS


def test_skill_names_the_control_fixture():
    body = SKILL.read_text(encoding="utf-8")
    cited = re.findall(r'"\$IDH_ROOT/(tests/fixtures/harness-doctor/[\w.-]+)"', body)
    assert cited, "SKILL.md must cite the control fixture"
    assert all((REPO / c).is_file() for c in cited)
    control_section = _section(body, "Positive control")[1]
    assert all(c in control_section for c in CONTROL_CHECKS)
    assert "control" in control_section and "fired" in control_section
    assert "skills/test-doctor/SKILL.md" in control_section, "reading-probe control"


def test_refusal_precedes_the_menu():
    body = SKILL.read_text(encoding="utf-8")
    probes_start, probes = _section(body, "Probes")
    pre_start, pre = _section(body, "Precondition")
    assert pre_start < probes_start
    assert "harness_here.sh" in pre and "stop" in pre
    assert "harness_here" not in probes


def test_menu_is_a_table_not_a_sequence():
    _, probes = _section(SKILL.read_text(encoding="utf-8"), "Probes")
    rows = [ln for ln in probes.splitlines() if ln.startswith("|")]
    assert len(rows) >= 2 + 5, "header, rule, five probes"
    assert all(r.count("|") == 4 for r in rows), "probe | answers | cost"
    for r in rows[2:]:
        assert all(c.strip() for c in r.strip().strip("|").split("|")), r
    assert not re.search(r"^\s*\d+\.", probes, re.MULTILINE)


def test_no_retirement_text():
    files = [SKILL, *sorted((DOCTOR / "references").glob("*.md"))]
    for f in files:
        text = f.read_text(encoding="utf-8").lower()
        assert "retire" not in text, f
        assert "three consecutive" not in text, f
        assert "delete this skill" not in text, f


def test_revisit_empty_case_is_stated():
    _, journal = _section(SKILL.read_text(encoding="utf-8"), "Journal")
    assert "no prior visit" in journal
    assert 'never "fixed"' in journal
    assert "revisit condition" in journal
    assert "-harness-doctor-" in journal


def test_proposals_are_priced_with_one_recommended():
    _, report = _section(SKILL.read_text(encoding="utf-8"), "Findings")
    for word in ("price", "author-hours", "agent cost", "odds", "recommend"):
        assert word in report, word


def test_visit_forms_hypotheses_before_probes():
    body = SKILL.read_text(encoding="utf-8")
    visit_start, visit = _section(body, "The visit")
    assert visit_start < _section(body, "Probes")[0]
    assert "Hypotheses" in visit and "prior" in visit


def test_skill_under_150_lines():
    assert len(SKILL.read_text(encoding="utf-8").splitlines()) < 150


def test_lint_reports_nothing_on_skill():
    result = stl.lint(REPO, stl.DEFAULT_PROJECTS, [SKILL])
    assert result["findings"] == [], result["findings"]
