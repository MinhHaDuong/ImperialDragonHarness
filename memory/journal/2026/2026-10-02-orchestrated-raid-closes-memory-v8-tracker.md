# Orchestrated raid closes the memory v8 tracker

Context: the author pointed an interactive session at tracker 0909 and asked
for autonomous execution. A raid ran the remaining train as six sequential
waves with detached executors, an internal standard review plus a decorrelated
external seat (openrouter-frontier) and a verify-gate before every merge.

Events and outcome: waves delivered PRs #1127 (0910 lair suggestion counting),
#1134 (0923 Vibe smoke), #1135 (0924 three-runtimes evidence), #1137 + #1142
(0918 predeclared protocol, then acceptance trials with verdict "No rollout"
— three of ten scenarios failed), and #1144 (0913 scoped out by author
decision; 0909 closed with the integration review). One executor died
mid-wave of a subagent runtime error (empty-message validation failure); its
worktree was clean at salvage and a relaunched finisher continued on the same
branch without redoing committed work. Both recorded rollout blockers were
then cleared on evidence: #1147 closed the codex contradictory-note channel
(user-level AGENTS.md in CODEX_HOME; rules/ proven not instruction-bearing on
codex-cli 0.159.3) and re-passed the cell; #1150 re-ran the pi cells on the
local llama.cpp server (padme, qwen3.8-27b) — all passed, and the original
plant's miss was explained: pi loads only the first of
AGENTS.override.md > AGENTS.md > AGENTS.MD > CLAUDE.md per directory.

Separately, the turn-ending stall the author observed across three detached
hunts was diagnosed in-session with a timed probe: blocking `agent.wait`
returns the runner's report; a client interrupt cancels the watch with
"Interrupted: client interrupt" while the runner survives; PR #1124 amended
hunt to block on the runner when the author is hands-off. The pi runtime's
standing default was reconfigured to the local server
(~/.pi/agent/settings.json: defaultProvider padme, defaultModel qwen3.8-27b),
verified from a pi session header; Hugging Face remains selectable.

Observations recorded as facts, with references: the predeclared protocol
caught a genuine codex behavior that post-hoc evaluation would have narrated
away; the relocated-clone link test caught directory-link errors in two
protocol documents before merge; the external seat's link-depth findings on
#1147 exposed that six archived v8 tickets carried `../docs/` links broken by
the archival move, repaired in this session's wrap-up. 0913 remains open as
the standing rollout workpackage with no recorded blocker; the metered
Kimi-K2.6 pi leg was never re-run.

Evidence: PRs #1127, #1134, #1135, #1137, #1142, #1144, #1147, #1150;
docs/memory-v8/evaluation-results.md; docs/memory-v8/integration-review.md;
tickets/closed/1019 and 1022 evidence documents.
