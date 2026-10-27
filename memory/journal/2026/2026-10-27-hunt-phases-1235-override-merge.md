# Hunt rewritten as phases; merged on author override after five gaze rounds (ticket 1235, PR 1704)

Context: the author asked (2026-10-27) to reword `skills/hunt/SKILL.md` from eleven numbered steps into Plan / Execute / Verify / Celebrate, with no forge and no code assumed. Filed as ticket 1235, landed as PR #1704; follow-ups filed as ticket 1241 (PR #1713).

Events:
- The session's cwd was the arena repository (no remote). The first `/gaze 1704` launched from it resolved no PR and stopped at setup; later rounds succeeded only with the harness worktree path and `--repo` named in the arguments.
- Gaze rounds 1-4 each returned FINDINGS on a new head; each set was fixed. Round 2's blocker came from a design change the author steered mid-review (a hunt returns a monster ticket to its caller instead of splitting); the ticket's exit criterion had not followed it.
- A resident-budget overrun (skills channel 6209/6200) passed a pre-rebase `make lint` and was caught by gaze round 3 after the base grew.
- The author stopped round 5 ("ENOUGH") and ordered the merge by override. Round 5's correctness seat later reported no blocking findings.
- The gate record failed twice: first on two `test_harness_doctor_skill.py` refusal tests that fail only with `TMPDIR` inside the worktree (hunt's own advice) and pass with the default; then on a merge conflict after main took gaze-by-intention (ticket 1225), which rewrote hunt's Review step. Resolved by merging main into the branch; the third record passed.
- `erg next-id` proposed 1236 for the follow-up ticket while an open PR already added 1236; the cross-PR scan caught it and the ticket became 1241.
- A full-suite run once failed `tests/test_zotero_import.py::test_item_fields_lists_every_field_the_type_owns`; it passed alone and in the next full run. Cause not established.

Outcome: PR #1704 merged at b243f22b on 2026-10-27 (ticket 1235 closed, override logged in the ticket); PR #1713 merged at 70034bd2 (ticket 1241 open, ten items).
