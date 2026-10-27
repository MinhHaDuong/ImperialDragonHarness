---
review-evidence: 1
kind: review
seat: correctness
verdict: approve
family: anthropic
worker: sonnet-route-model-id-not-observed
base: 837f99369eba180d3680a283a599b18ac974120b
head: 974a34d3cf1f5685702ca49d3cc4cf791446f6bc
patch-id: b1c61de53a1c79b91e8cd46fbe92c18b61011f8c+790dbfe803c22991252028a1dcc30192617752a5
criteria-hash: 16765aa9a3f14bad
policy-version: f78a1b40e2adb3e1
recorded: 2026-10-27T07:52:11Z
---

Re-recorded at the close head: the seat reviewed the PR content at the head named in its report; the only change since is commit 974a34d (ticket 1233 close and archive, merge-gate tier: bookkeeping, 2 ticket paths), which changed the patch-id. Verdict unchanged, not re-run.

Gaze round 5 seat report, transcribed verbatim from https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1699#pullrequestreview-5663690972 (head 586fa3f6d4a380ed5510ed3ebd59c11f215a7ce4).

**correctness: clear.** The round-4 verifiable at runtime-diagnostics.md:70 is closed: `pi mcp list` is now labelled author, with its reason, and is limited to the plain form. `pi list --no-approve` exists in pi 1.4.0: `pi list --help` prints "-na, --no-approve  Ignore project-local files for this command", which matches the new text. The cheapest-first order holds. Targeted tests (test_harness_doctor_skill, test_skill_frontmatter, test_skill_descriptions, test_check_agnostic): 49 passed. nofollow: the author-labelled line sits between a no-user line and a spends line; no test enforces the order.
