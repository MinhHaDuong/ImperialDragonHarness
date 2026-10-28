# 2026-10-28 — Raid f7fa41: forge-leak tracker 1317 (PRs #1904, #1906, #1911, #1912, #1915, #1916)

Session: Claude Code team lead, claude-opus-5-5, host padme; executors and gate runners claude-sonnet-5-5, one claude-haiku-5-5 (1321).

- Children 1318-1321 filed and merged in two waves; tracker 1317 closed after its integration review (main 21e9bb9a: 3009 passed, 4 skipped). Residue with reasons is listed in the tracker body.
- Blind-Spot pass found that `forge.get_forge(ref="")` returned the none backend even with gh installed (an empty ref is not numeric); 1318 added `get_forge_listing` and the exit 0/2/3 contract (no origin → 3, origin without a readable gh → 2).
- Gaze run from a nested general-purpose subagent recorded `seats: self-only` three times on PR #1915 (plans declared only `self`; one run's cross-family spend was refused). A seat run outside gaze's plan was not recorded. The fourth run, told to put a correctness seat in its plan per `skills/gaze/references/plan.md` lines 38-47, recorded `seats: panel`.
- A sitrep wake started by `runtime.py wake fire` from a worktree that was removed before it fired printed `UNREADABLE log/git/forge` (cwd gone); re-armed with `cd <primary> &&` in `--cmd`, it read normally.
- verify-gate round 1 on #1912 REROLLed: `tests/test_close_claim_grammar.sh` built detector dirs with no git repo, so the ported check-close-claims answered exit 3; the round-2 fix gave the fixture an origin remote.
- Direct `pytest tests/test_attribution_record.py` errors (ModuleNotFoundError: forge) on main too; `make check` passes it.
