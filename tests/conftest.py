"""Smart-cache declarations for inputs outside Python execution coverage.

Cost markers describe runtime; these declarations describe cache eligibility.
Normal pytest runs execute exactly the same tests with or without these marks.
"""
import pytest


MODULE_INPUTS = {
    'test_bash_suites.py': (
        'tests/*.sh', 'tests/fixtures/*', 'scripts/**/*', 'skills/**/*',
        'hooks/*', 'tickets/erg', 'tickets/.ergrc', 'rules/**/*',
        'commands/**/*', 'bin/*', 'README.md', 'STATE.md',
    ),
    'test_on_start_memory_injection.py': (
        'memory/MEMORY.md', 'scripts/on-start.sh', 'scripts/prompt-project-coherence.sh',
        'scripts/tmp_report.py', 'scripts/sync-local-main.sh',
    ),
    'test_project_coherence_prompt.py': (
        'scripts/on-start.sh', 'scripts/prompt-project-coherence.sh',
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
    ('test_ruff.py', 'test_ruff'): ('**/*.py', '.ruff.toml'),
    ('test_check_agnostic.py', 'test_real_skills_pass_agnostic_gate'): ('skills/**/*',),
    ('test_check_agnostic.py', 'test_real_scripts_dir_is_agnostic'): ('scripts/**/*',),
    ('test_zotero_rule.py', 'test_zotero_rule_file_exists'): ('rules/zotero.md',),
    ('test_agent_profiles.py', 'test_pi_translation_template_exists'): (
        'adapters/pi/agents/code-reviewer.md',
    ),
}
ALWAYS = {
    ('test_probe_memory_symlink.py', 'test_live_probe_control_fires'),
    ('test_local_ci_negative_controls.py', 'test_every_guard_catches_its_violation'),
    ('test_ruff.py', 'test_ruff_version_satisfies_pinned_range'),
    ('test_track_changes_pdf.py', 'test_render_end_to_end'),
    ('test_adapter_inventory.py', 'test_every_assertion_is_covered'),
    ('test_memory_v8_protocol.py', 'test_protocol_pins_historical_dream_prompt_blob'),
    *{('test_perch_discovery.py', name) for name in (
        'test_a_clean_codex_profile_gains_perch_only_after_install',
        'test_a_clean_pi_profile_gains_perch_only_after_install',
        'test_pi_reads_perch_through_the_neutral_home_symlink',
        'test_uninstall_takes_perch_back_out_of_a_pi_profile',
        'test_the_recorded_probe_command_is_the_one_that_ran',
    )},
}


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(items):
    for item in items:
        key = (item.path.name, getattr(item, 'originalname', item.name))
        inputs = MODULE_INPUTS.get(key[0], ()) + TEST_INPUTS.get(key, ())
        if inputs:
            item.add_marker(pytest.mark.smart_inputs(*inputs))
        script = getattr(item, 'callspec', None)
        script = script.params.get('script') if script else None
        git_case = script is not None and script.name in {
            'test_benchmark_board.sh', 'test_seat_runner.sh',
        }
        if key in ALWAYS or git_case:
            item.add_marker(pytest.mark.smart_always)
    yield
