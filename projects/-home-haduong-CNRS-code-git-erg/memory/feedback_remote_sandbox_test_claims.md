---
name: remote-sandbox-test-claims
description: "Cloud routine agents misreport sandbox-only test failures as \"pre-existing on main\" — verify locally before believing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7486d7d8-cc88-47ed-b071-07569335661d
---

The Anthropic cloud sandbox used by scheduled remote routines cannot run
`git worktree add` inside its checkout (exit 128). On 2026-06-05 the
remote agent for ticket 0237 (PR #285) hit this in test_install.sh's
linked-worktree test and reported "make check fails with a pre-existing
failure that reproduces on main" — false locally: 38/38 pass, exit 0,
CI green.

**Why:** the agent's claim was true *in its environment* but wrong as a
statement about the repo; accepting it would have spawned a phantom-bug
ticket (cf. [[observation-before-causal-verdict]]).

**How to apply:** when a remote/cloud agent claims a pre-existing test
failure, re-run that exact test locally on clean main before acting.
Worktree-dependent tests are the known offender class. The end-to-end
remote pipeline itself works: self-contained prompt → PR 13 min after
trigger → APPROVED r1; keep prompts warning that worktree-based tests
may fail in the sandbox.
