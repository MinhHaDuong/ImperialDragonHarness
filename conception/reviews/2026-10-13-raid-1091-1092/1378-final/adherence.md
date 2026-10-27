python3 -m pytest tests/ -m adherence
============================= test session starts ==============================
platform linux -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/haduong/.agents/.claude/worktrees/t1091-census-overlay
configfile: pytest.ini
plugins: xdist-3.8.0, cov-7.1.0, anyio-4.15.1
collected 1610 items / 1425 deselected / 185 selected

tests/test_adherence_project_runner.py ...                               [  1%]
tests/test_agent_profiles.py ......................                      [ 13%]
tests/test_check_agnostic.py .............                               [ 20%]
tests/test_deps_declared.py ...                                          [ 22%]
tests/test_gaze_breaker_counting.py ...                                  [ 23%]
tests/test_gaze_prose_routing.py ........                                [ 28%]
tests/test_guards_rule.py ...                                            [ 29%]
tests/test_legacy_memory_retired.py ..                                   [ 30%]
tests/test_pi_provider_assertion_rule.py ...                             [ 32%]
tests/test_project_census.py ........                                    [ 36%]
tests/test_prose_cutting_rule.py ...                                     [ 38%]
tests/test_python_tests_are_hermetic.py ................................ [ 55%]
..                                                                       [ 56%]
tests/test_resident_census.py ........                                   [ 61%]
tests/test_review_detached_seat_pattern.py ...                           [ 62%]
tests/test_review_first_round_width.py ...                               [ 64%]
tests/test_review_round_scoping.py .....                                 [ 67%]
tests/test_roar_armed_exit.py ....                                       [ 69%]
tests/test_roar_clear_verdict.py ....                                    [ 71%]
tests/test_root_cause_taxonomy.py ....                                   [ 73%]
tests/test_ruff.py ...                                                   [ 75%]
tests/test_rules_resident_budget.py ....                                 [ 77%]
tests/test_skill_frontmatter.py ......                                   [ 80%]
tests/test_skill_reference_pointers.py ...............                   [ 88%]
tests/test_stale_idh_layout.py ...                                       [ 90%]
tests/test_worktree_predicate_ratchet.py ...........                     [ 96%]
tests/test_zotero_backend_name.py .......                                [100%]

==================== 185 passed, 1425 deselected in 20.72s =====================
