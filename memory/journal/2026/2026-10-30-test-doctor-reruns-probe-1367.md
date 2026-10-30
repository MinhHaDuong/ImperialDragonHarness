---
date: 2026-10-30
kind: episode
project: .agents
refs: [PR 2032, ticket 1367, padme PR 161, padme ticket 0080, padme ticket 0081]
---

# Test doctor gains a reruns probe; the first metric was not the bound it claimed

Context: the author asked how projects manage `.pytest_cache`, then ruled that runner-cache management is the test doctor's on-demand knowledge, backed by evidence from repeated runs, not a pin in agent briefs. The session worked ticket 1367 directly (no hunt or raid), so no `writer:` line was on notes until roar recorded it.

Events:
- The primary checkout's `.pytest_cache/v/cache/lastfailed` (2026-10-29) named four tests; none exists on main at f7c64e93 (`tests/test_model_policy.py` deleted in 455ac217, the fourth renamed in d21281a7).
- Positive control before building: 3377 of 6536 test/gate results in 28 d of harness traces carried a pytest summary line.
- First version (d8d0abb6) reported 81.8 min of `make check` rerun time "spent on previously passing tests", labelled an upper bound. Gaze round 1 (codex gpt-6.1-sol seat and self, independently) found it count-weighted and counting the green rerun the remedy keeps; a replay of the remedy showed no change in the figure.
- Fix 2fdb0a77 counts only full reruns that came back red: 17 reruns, 24.6 min on the same traces; quiet-summary parsing raised outcome reads from 1293 to 2963 of 4477 runs; flip candidates on `make check` fell from 24 to 9.
- Gaze round 2: both seats reproduced a fix-on-fix regression (segments after the gate, `| tee log`, counted as edits). Fix 6e495df2; round 3 REVIEWED; verify-gate APPROVED round 1. One below-bar consider left: `SELECTED` regex trailing `\b` matches before a hyphen.
- The first verify-gate call refused without spending a round: the only gaze answer covered d8d0abb6, and the fix was full tier.
- Same session, padme and doudou: padme syncs no files; doudou's Nextcloud client syncs `~/CNRS` and still syncs `node_modules` (1.4 GiB) and `.ruff_cache`; ~5.4 GiB of `.venv`/`.mypy_cache`/`.git` entries predate its 2026-06-18 exclude list. Filed as padme tickets 0080 (restic `--exclude-caches`) and 0081 (doudou), padme PR 161.

Outcome: PR 2032 merged at 2a1aba02, ticket 1367 closed; padme PR 161 merged.
