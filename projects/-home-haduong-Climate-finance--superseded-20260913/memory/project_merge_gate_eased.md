---
name: merge-gate-eased-expost
description: PR gate is check-fast + lint since 2026-07-28; full make check runs ex post (lair step 9) and pre-PR only for pipeline-surface diffs
metadata: 
  node_type: memory
  type: project
  originSessionId: 1b0d238d-3cde-4140-ad66-b4efd28aabaa
  modified: 2026-07-28T09:10:47.443Z
---

The per-PR merge gate is `make check-fast` + `make lint` (~40 s), decided 2026-07-28 (PR #1261; IDH #690 carries the global-rule deferral). The full `make check` runs ex post — `/lair` step 9 on main, new failures ticketed — and pre-PR only when the diff touches the pipeline surface (`scripts/`, `libs/`, `dvc.yaml`, Makefiles, slow/integration tests). AGENTS.md § Execute is the contract.

**Why:** an 18-day transcript census (2026-07-10 → 07-28) found 67 full-suite gate runs at 4–10 min each (~1.3 per merged PR, ~4.5 h total) with zero gate-time catches beyond the fast tiers — every observed failure was environmental (corpus-less worktree `test_corpus_acceptance`) or fast/adherence-tier. Census method: pair Bash tool_use/tool_result timestamps in session `.jsonl`, tally in Python (rtk rewrites grep output).

**How to apply:** don't demand "make check passes" as a per-PR exit criterion for non-pipeline diffs; cite the eased gate. A parked follow-up design exists for a roar-signaled ex-post runner: serialized systemd user oneshot on padme, SHA-addressed (verify head of origin/main, catch-up pass if main advanced mid-run, flock), verified-SHA marker answering "is main green?" — build it if the lair cadence proves too slow. See [[no-ci-local-merge-gate]].
