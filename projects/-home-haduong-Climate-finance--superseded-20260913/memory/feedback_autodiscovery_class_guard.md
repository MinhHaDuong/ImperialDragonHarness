---
name: feedback_autodiscovery_class_guard
description: Prefer Makefile/source-driven auto-discovery guards over hardcoded lists — they catch missed and rebased-in class members
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e941c29d-5c40-4794-8c38-de28cfeab946
  modified: 2026-07-27T19:03:33.426Z
---

For a "whole class of scripts must do X" guard (e.g. ticket 0233: every
`$(DERIVED)` producer must `os.makedirs` before `validate_io`), write the test
to **auto-discover** the class from the Makefile (or source), not from a
hardcoded script list.

**Why:** In 0233 the auto-discovering guard immediately caught 5 offenders the
ticket's manual sweep missed — `compute_lexical` (present at filing) plus 4
producers (`compute_analytical_null`, `compute_crossyear_zscore`,
`compute_sensitivity_grid`, `compute_venue_concentration`) that a mid-hunt
rebase brought in from parallel work. A hardcoded list would have silently left
all 5 unguarded.

**How to apply:**
- Discover by resolving Make variables (two-pass: collect vars expanding under
  the target dir, then scan target lines for a `scripts/*.py` prereq; join
  `\`-continuation lines first).
- Anchor the assertion tightly: check the *output-targeting* call
  (`os.makedirs(os.path.dirname(io_args.output)`) in the right lexical scope
  (between `parse_io_args()` and `validate_io`), so a decoy call elsewhere can't
  produce a false GREEN. Mutation-verify the teeth (delete a real fix → RED).
- Still pin the full known member set in a `_nonempty` sanity test so a
  discovery-scan regression that drops a producer fails loudly, not vacuously.
- Coverage boundary: a Makefile-driven scan only sees Make-wired producers; a
  script writing to the dir via a hardcoded default with no target is invisible
  (same limit as `test_phase_layout`). Accept it or add a source scan.

**Discover the class, but do not hand-roll the enumeration.** Auto-discovery
fixes the *list*; it does not stop the *walk* from drifting. This repo has one
sanctioned `scripts/` enumeration, `tests/_script_discovery.all_script_files()`
(ticket 0260), and the same defect keeps reappearing around it — 0248 for `.mk`
discovery, 0260 for `scripts/`, then 0346's own new guard shipping an
`os.walk(SCRIPTS_DIR)` that scanned the frozen `archive*/` trees. Three
occurrences, each caught by a human reading a diff, none by a test. The 0346
roar sweep then found two more live divergences (`test_script_hygiene.py:59`,
`test_import_path_model.py:148`) that test for the literal name `archive` while
the helper excludes anything `startswith("archive")` — so five
`archive_traditions/` scripts are enforced as active code, visible in every
`make lint` run. Filed as 0400, with a standing guard so the fourth occurrence
fails a test.

The rule: if the repo has a sanctioned enumeration for a file set, route
through it — a second walk is a second opinion about what the class contains,
and the two drift in whichever direction nobody is looking.

Related: [[feedback_scope_discipline]] [[feedback_lean_methods]]
