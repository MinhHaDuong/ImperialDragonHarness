# /pulse renamed /test-doctor; trace-doctor hands slow gates to it (PR 1689, ticket 1228)

Date: 2026-10-27
Project: ImperialDragonHarness

**Context.** The author asked how /pulse and trace-doctor split their roles. A read of both skills found trace-doctor's velocity section ranks the slow Bash tail (mostly test gates) but could only open tickets, with no route to the testing consultation. The session also stated that runtime hook guards had an owner with no method.

**Measurement before the decision.** At the author's request, `trace-friction.py --json` (28 d, padme, 37 s): 3,391 worktree-guard denials, 93 write-outside-worktree, 2 unattributed. Daily series: ~750/day on 2026-09-30/10-01, ~240/day 10-05 to 10-11, 184 on 10-14, 8 in total 10-15 to 10-27, 0 in the last 3 days. The drop matches commit edd139bd (2026-10-14, sessions enter worktrees with plain git), a timing match, not an isolated cause. Same scan: sleep_poll_to_cap 268 calls / 103 sessions, 145,251-155,068 s bounds; pgrep_self_match 496 calls / 184 sessions, ~29,570 s.

**Correction.** The "guards without an owner" claim was wrong: closed ticket 1218 had routed the live PreToolUse guard (guard-destructive-bash.sh) to /pulse, and the syndromes define a guard as any test or check guarding a rule. The planned narrowing of rules/workflow.md to "test guards" was dropped.

**Decision.** The author found "pulse" broader than the task and chose `/test-doctor` (singular, pairing with `/trace-doctor`), waiving the themed name because the skill is meta. The author's own directive of 2026-10-21 (memory note on second-order guards) had already said "test doctor (pulse)". Scripts were renamed by function (`gate_traces.py`, `gate_profile.py`) because `scripts/test_doctor_*.py` would match pytest's default collection pattern. Closed tickets and journal entries keep "pulse"; chart history reads both slugs.

**Review path.** /gaze round 1 REVIEWED ad1d3b4b with two consider findings on the same lines; adopting them as commit a45854fa moved the head, and /verify-gate refused ("no completed review": full tier since the reviewed head). /gaze round 2 REVIEWED a45854fa (3m14s); /verify-gate round 1 APPROVED. Before the gate, the PR-body attribution block failed `attribution_record.py --pr-body`: no `writer` line, the writer needed `route` and `independence` and a provider-qualified model id, and gaze round 2 had written two findings as `nit`, outside the `verifiable|consider` grammar (recorded as consider). A first `/verify-gate` call without `repo=` returned ESCALATE without spending a round.

**Outcome.** PR 1689 merged at a0b9c3d7 (gate record on padme, pytest 67.9 s; merge recipe 111 s). Runtime links `~/.claude/skills/test-doctor` and `~/.pi/agent/skills/test-doctor` re-pointed by hand; the Pi skills directory is a per-skill link farm, which the author attributed to another session's work.
