---
name: Verify sibling PRs jointly, not just individually
description: two PRs can each be internally clean yet assert opposite facts; check the pair before merging both
metadata:
  type: feedback
---

When asked to verify and merge more than one PR, check the claims they make
*against each other*, not only each against the code. Two PRs can both be
mechanically clean — green CI, current base, uncontested ticket seat — and
still land a claim and its refutation in the repo on the same day.

Seen 2026-07-27 on harness PRs #680 and #681. #680 rewrote the
`update-publist` credential paragraph to end "`~/.claude/.env` does, which
covers a run from anywhere"; #681 filed ticket 0360 documenting that a project
`KEYS=` *replaces* the harness selection, which makes that sentence false from
any cwd carrying its own `KEYS=` line. Both were 9/9 green. A per-PR gate
passes both by construction — the contradiction exists only in the union.

**Why:** the harness's mechanical gates (`/gaze`, CI, verify-gate) are scoped
to one diff. Nothing in the per-PR path compares PR A's assertions to PR B's.
Consistency across a merge batch is the reviewer's job, and it is the one
check that scales with the number of PRs rather than their size.

**How to apply:** before merging a batch, list the factual claims each PR
makes about shared mechanisms and look for pairs that talk about the same
thing. When one PR *documents* behaviour and a sibling *files a bug against*
that same behaviour, read the doc sentence against the ticket body — that
pairing is the high-yield case. Test the claim rather than reasoning about it:
here a hermetic `env -i` subprocess probe from three startup cwds settled it in
one call (see [[project_bash_env_secret_loading]] and
[[feedback_bash_env_tests_real_invocation_path]]). Fix the wrong sentence
inline in its own PR before merging — a tooling-repo finding below the
merge-blocking bar is fixed in the current change, not ticketed
([[feedback_harness_cooldown_stop_second_order_tooling]]).
