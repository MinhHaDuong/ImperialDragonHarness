"""Skill names embedded in scripts must survive skill directory renames."""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_script_skill_refs", ROOT / "scripts/check-script-skill-refs.py"
)


def guard():
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


def test_dangling_name_needs_a_local_historical_declaration(tmp_path):
    (tmp_path / "skills/current").mkdir(parents=True)
    (tmp_path / "skills/current/SKILL.md").write_text("current")
    script = tmp_path / "scripts/trace.py"
    script.parent.mkdir()
    script.write_text('MANDATED_SKILLS = {"current", "former"}\n')
    assert guard().check_script(script, tmp_path / "skills") == ["former"]

    script.write_text(
        '# historical-skill: former -> current\n'
        'MANDATED_SKILLS = {"current", "former"}\n'
    )
    assert guard().check_script(script, tmp_path / "skills") == []


def test_historical_declaration_must_point_to_live_skill(tmp_path):
    (tmp_path / "skills").mkdir()
    script = tmp_path / "trace.py"
    script.write_text(
        '# historical-skill: former -> missing\n'
        'MANDATED_SKILLS = {"former"}\n'
    )
    assert guard().check_script(script, tmp_path / "skills") == ["former"]


def test_regex_and_skill_path_references_are_guarded(tmp_path):
    (tmp_path / "skills/current").mkdir(parents=True)
    (tmp_path / "skills/current/SKILL.md").write_text("current")
    script = tmp_path / "trace.py"
    script.write_text(
        'import re\n'
        'SKILL = re.compile(rb\'"skill":\\\\s*"(current|former)"\')\n'
        'MERGE = "skills/deleted/SKILL.md"\n'
    )
    assert guard().check_script(script, tmp_path / "skills") == ["deleted", "former"]


def test_git_verb_and_cache_name_are_not_skill_references(tmp_path):
    (tmp_path / "skills").mkdir()
    script = tmp_path / "helper.py"
    script.write_text('GIT_MUTATIONS = {"merge"}\nINDEX_CACHE_DIR = "zotero-import"\n')
    assert guard().check_script(script, tmp_path / "skills") == []


@pytest.mark.adherence
def test_live_scripts_reference_current_or_declared_historical_skills():
    failures = guard().check_tree(ROOT)
    assert not failures, failures
