# Raid 6958fe: four tickets, one composition refusal at the merge gate

2026-10-29. Team-lead raid on tickets 1337, 1339, 1340, 1341 (author-requested).
PRs 1967, 1968, 1969, 1970, all merged.

- PRs 1969 (ticket 1340) and 1970 (ticket 1341) each passed `make check` and
  verify-gate APPROVED on their own base. 1340 adds a sentence to
  `rules/claude-code.md`, 1341 a subsection to `rules/workflow.md`; both are
  resident rule files. After 1969 merged, `raid_land.py 1970` refused with
  "gate check answered 1": the composed resident set measured 18317 chars
  against the 18200 budget 1970 had set on the old base
  (`tests/test_rules_resident_budget.py`). Fix: rebase, budget 18350, gaze and
  gate round 2 on 0ac19d28, then merged.
- Gaze runs launched from a Sonnet subagent returned `seats: self-only` with
  `plan check: FAIL` on first attempt for PRs 1967 and 1970; the subagent
  rejected them and a second gaze run on the same head returned `seats: panel`
  with a codex (OpenAI) seat.
- PR 1969 was landed before writer lines were recorded on its review notes;
  `raid_land.py` printed `attribution: invalid ... (PR body: missing)` and
  merged anyway. Writer lines were recorded afterwards for the capture.
- Ticket 1341: `scripts/runtime_wake.py` `wake send` reaches a Codex thread by
  id (`codex queue`, queued only); on Pi it writes only the calling session's
  own `IDH_WAKE_INBOX`, so the rule states "ticket only" for Pi.
- After-merge record on 2df710ae (after 1967) passed pytest-guard, settling
  ticket 1337's third exit criterion.
