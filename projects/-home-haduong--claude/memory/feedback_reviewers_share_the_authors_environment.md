---
name: feedback_reviewers_share_the_authors_environment
description: "A review panel is decorrelated by model and by angle but not by environment — every agent works in the author's worktree, so a defect the machine hides is hidden from all of them at once"
metadata:
  type: feedback
---

Raid on tracker 0942, 2026-09-16. Twenty-one review agents ran over two PRs:
adherence, scope, consistency, doc-propagation, correctness and red-team
batteries, across three rounds, one of them doing genuine mutation testing.

Between them they found a keystore-redirection hole that let an untrusted
project `.env` point the resolver at an attacker file, a decoy test that could
never fail, a newline injection into a live authenticated request, a missing
size cap, and a dormant `repr()` disclosure. Not one of those five was predicted
by any exit criterion. The battery paid for itself.

**The defect that would actually have shipped escaped all twenty-one.** A
module-level `from openai import …` made `peer_review.py` unimportable wherever
the SDK is absent. Seven credential-resolution tests passed locally — `make
check` reported 994 — and failed in CI. Every reviewer worked inside the author's
worktree, on the author's machine, where `openai` is installed.

**Why:** the harness decorrelates reviewers along two axes, model and angle of
attack, and `rules/workflow.md` § Delegation names both. It does not decorrelate
them by *environment*. A shared environment does not produce N independent
misses; it produces one miss shared N times, and the agreement between agents
reads as confirmation. The more reviewers pass, the more confident the wrong
conclusion looks.

**How to apply:** treat CI as a panel member rather than a final gate — it was
the only participant not sharing the environment, and it was the one that found
this. Where a wave is worth a full battery, give at least one reviewer a clean
checkout rather than the author's tree. And when a test needs the developer's
machine to pass, that is a property of the test, not a convenience: the fix here
was to make the credential half of the module import nothing third-party, not to
install the SDK in CI (buys a large dependency for a guard) and not to skip the
tests when it is missing (the green-while-testing-nothing this very wave spent
three rounds eliminating).

The general shape: **agreement among probes that share a blind spot is not
evidence.** Related: [[feedback_positive_control_validates_the_detector_not_the_enumerator]]
(a fired control says you can recognise a hit, not that you looked at every
candidate), [[feedback_adversarial_pair_verification]].
