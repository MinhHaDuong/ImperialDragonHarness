---
date: 2026-10-29
kind: episode
project: .agents
refs: [PR 2006, PR 2007, PR 2010, PR 2013, PR 2014, ticket 1348, ticket 1356, ticket 1357, ticket 1344, ticket 1359, ticket 1360]
---

# Raid 29bf18: gaze close anchors, the worktree deletion path, an after-merge red

Context: raid 29bf18 resumed raid b7c67c at Phase 5 (planning merged in PR 2005). Executors were Sonnet 5.5 coder subagents; the orchestrator was Opus 5.5.

Events:
- 1348 (PR 2006) and 1356 (PR 2007) each gated APPROVED in round 1. The 1356 executor's own gaze recorded `seats: self-only`; a gaze run from the orchestrating session then ran a headless codex seat and recorded `seats: panel`.
- 1357 (PR 2013): the executor's REVIEWED answer had a seat labelled `family=OpenAI` that ran as `runtime=claude-code, route=subagent, model=anthropic/gpt-6-luna`. verify-gate's `--require-cross-family` refused admission. This is the defect DOIfetch reported the same evening (ticket 1360).
- The four gaze rounds that followed on PR 2013, each with a headless codex `gpt-6.1-sol` red-team seat, each found a new deletion hole in `worktree_scrub`: a hand-made file inside an untracked `.venv`; hand-made files in `build/lib*`; any `*.py` or basename twin counted as build output; `git hash-object` applying `.gitattributes` clean filters. Rules adopted, in order: venv top-level allowlist; scrub only after a clean residue verdict; byte identity with a tracked blob or a `.pyc/.so/.pyd/.o` extension (advisor Fable 5.1 agreed); `--no-filters`. The third fix round went past the fix-and-regate two-round rule on the author's standing "don't wait"; it is recorded here as a departure.
- `git hash-object --stdin-paths` applied the filter for an absolute path when run with `-C <repo>` and a tracked `.gitattributes`; a `.git/info/attributes` file did not reproduce it inside the test fixture (cause not established).
- 1359: the after-merge red on main fc9014aa (pytest-guard, `test_negative_control_healthy_home_launches_unchanged[codex|pi]`) reproduced at 5b255399, before PR 2010. shell-init's disk-headroom probe wrote to stderr because /tmp (tmpfs, 32 GB) was 91% used, 28 GB of it by a live arena pilot run in another project. PR 2014 stubs the probe in the test's disposable checkout.
- 1344: the exit criterion was amended from a signed to an unsigned annotated tag `v0.2.0` after the author confirmed in this session; the request first came relayed by the DOIfetch session.

Outcome: PRs 2006, 2007, 2010, 2013, 2014 merged; tickets 1348, 1356, 1357, 1344, 1359 closed. Tickets 1360-1363 filed from the DOIfetch defect batch (PR 2012).
