# 2026-10-27 — raid: forge-less review chain, guard in enforce, narrow agent token

Session raid-116623 (padme), orchestrator Opus 5.5; coders Sonnet 5.5 and Opus 5.5; OpenAI review seats via codex.

Facts:
- 25 PRs merged, including tickets 1180, 1196, 1227, 1249, 1262, 1266, 1267, 1268, 1271-1276, 1279-1281 closed.
- idh.mainGuard is enforce on padme and doudou since 16:20Z (1268 whitelists pack-refs).
- Agent sessions (Claude Code shells) use a fine-grained PAT via GH_CONFIG_DIR=~/.config/gh-agent (1196); Codex and Pi shells do not yet.
- Cross-family review consent on padme: OpenAI, Mistral (~/.config/harness/gaze-seats.json); vibe became a working read-only seat (1279).
- Author's flows ruling: F1 default (notes review + forge PR merge); F2 (local gated merge) only with no origin remote; no setting.
- Main went red after PR #1799: callers outside the moved set (merge-gate.py) and integration-tier tests were not run by any review or gate; fixed forward in PR #1811.
- Gaze run from inside a coder came back self-only in all five wave-1 runs; explicit panel briefs fixed it.
- git push over https failed once each in two places and succeeded on retry; cause not established.
