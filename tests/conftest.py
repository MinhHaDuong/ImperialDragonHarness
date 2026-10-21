"""Smart-cache declarations for inputs outside Python execution coverage.

Cost markers describe runtime; these declarations describe cache eligibility.
Normal pytest runs execute exactly the same tests with or without these marks.
"""
import json
import re
from pathlib import Path

import pytest

from repo_sources import SCAN_DIRS


MODULE_INPUTS = {
    'test_perch_discovery.py': (
        'version:claude', 'version:codex', 'version:pi',
        'version:$PERCH_CLAUDE_BIN', 'version:$PERCH_CODEX_BIN', 'version:$PERCH_PI_BIN',
        'adapters/perch.py', 'adapters/pilot-support.json',
        'scripts/skill_frontmatter.py', 'skills/perch/SKILL.md', 'tests/child_env.py',
    ),
    'test_bash_suites.py': (
        'tests/*.sh', 'tests/fixtures/*', 'scripts/**/*', 'skills/**/*',
        'hooks/*', 'tickets/erg', 'tickets/.ergrc', 'rules/**/*',
        'commands/**/*', 'bin/*', 'README.md', 'STATE.md',
    ),
    'test_on_start_memory_injection.py': (
        'memory/MEMORY.md', 'scripts/on-start-context.sh', 'scripts/prompt-project-coherence.sh',
        'scripts/tmp_report.py', 'scripts/sync-local-main.sh',
    ),
    'test_project_coherence_prompt.py': (
        'scripts/on-start-context.sh', 'scripts/prompt-project-coherence.sh',
        'scripts/tmp_report.py', 'scripts/sync-local-main.sh',
    ),
    'test_hook_launchers.py': (
        'adapters/claude-code/bin/idh-hook', 'scripts/guard-destructive-bash.sh',
    ),
    'test_skill_reference_pointers.py': ('skills/*/references/*',),
    'test_dream_v8.py': ('memory/**/*',),
    'test_memory_v8_protocol.py': ('docs/**/*', 'memory/**/*', 'skills/**/*'),
}
TEST_INPUTS = {
    # source_texts() is shared and memoized: audit reads reach only its first
    # caller, so each guard must declare the inventory it actually consumes.
    ('test_deps_declared.py', 'test_third_party_imports_are_declared'): tuple(
        f'{directory}/**/*' for directory in SCAN_DIRS),
    ('test_skill_frontmatter.py', 'test_frontmatter_regex_has_single_definition'): tuple(
        f'{directory}/**/*' for directory in SCAN_DIRS),
    ('test_ruff.py', 'test_ruff'): ('**/*.py', '.ruff.toml'),
    ('test_check_agnostic.py', 'test_real_skills_pass_agnostic_gate'): ('skills/**/*',),
    ('test_check_agnostic.py', 'test_real_scripts_dir_is_agnostic'): ('scripts/**/*',),
    ('test_zotero_rule.py', 'test_zotero_rule_file_exists'): ('rules/zotero.md',),
    ('test_agent_profiles.py', 'test_pi_translation_template_exists'): (
        'adapters/pi/agents/code-reviewer.md',
    ),
    ('test_lair_state_via_pr.py', 'test_step_10_regenerates_nothing'): (
        'scripts/refresh-STATE.py',
    ),
}
ALWAYS = {
    ('test_probe_memory_symlink.py', 'test_live_probe_control_fires'),
    ('test_local_ci_negative_controls.py', 'test_every_guard_catches_its_violation'),
    ('test_ruff.py', 'test_ruff_version_satisfies_pinned_range'),
    ('test_track_changes_pdf.py', 'test_render_end_to_end'),
    ('test_memory_v8_protocol.py', 'test_protocol_pins_historical_dream_prompt_blob'),
}


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(items):
    for item in items:
        key = (item.path.name, getattr(item, 'originalname', item.name))
        inputs = MODULE_INPUTS.get(key[0], ()) + TEST_INPUTS.get(key, ())
        if key == ('test_adapter_inventory.py', 'test_every_assertion_is_covered'):
            inventory = 'adapters/pilot-support.json'
            doc = json.loads((item.config.rootpath / inventory).read_text())
            inputs += (inventory, 'tests/child_env.py', 'tests/tracked_tree.py',
                       'adapters/perch.py',
                       'scripts/skill_frontmatter.py', *doc['canonical_sources'].values(),
                       *{entry['test'].split('::', 1)[0] for entry in doc['assertions']
                         if entry['evidence_kind'] in ('static-test', 'local-probe')})
        section = getattr(item, 'callspec', None)
        section = section.params.get('section') if section else None
        if key[0] == 'test_bash_suites.py' and section == 'deterministic':
            inputs = ('tests/test_seat_runner.sh', 'scripts/coaching/seat-runner.sh',
                      'scripts/coaching/seat-runner/**/*')
        if inputs:
            item.add_marker(pytest.mark.smart_inputs(*inputs))
        script = getattr(item, 'callspec', None)
        script = script.params.get('script') if script else None
        git_case = script is not None and (
            script.name == 'test_benchmark_board.sh'
            or (script.name == 'test_seat_runner.sh' and section != 'deterministic')
        )
        if key in ALWAYS or git_case:
            item.add_marker(pytest.mark.smart_always)
    yield


# --- split-skill contract view ------------------------------------------------
# skills/gaze/SKILL.md (ticket 1153) and skills/raid/SKILL.md (ticket 1131) are
# a core plus references/*.md. The tests pin the *contract*, not its file
# layout, so reading either SKILL.md through Path.read_text returns the
# contract with every `<!-- inline: references/x.md -->` marker replaced by
# that reference's body (its H1 and intro line dropped). Only these paths are
# affected; layout tests read the files directly through other means
# (test_skill_reference_pointers.py walks the directory).
_SKILLS = Path(__file__).resolve().parents[1] / "skills"
_SPLIT_SKILLS = {_SKILLS / name / "SKILL.md" for name in ("gaze", "raid")}
_INLINE = re.compile(r"<!-- inline: (references/[\w.-]+\.md) -->")
_read_text = Path.read_text


def _split_contract_read_text(self, *args, **kwargs):
    text = _read_text(self, *args, **kwargs)
    skill = self.resolve()
    if skill not in _SPLIT_SKILLS:
        return text

    def body(match: re.Match) -> str:
        ref = _read_text(skill.parent / match.group(1), encoding="utf-8")
        return ref.split("\n\n", 2)[2]

    return _INLINE.sub(body, text)


Path.read_text = _split_contract_read_text
