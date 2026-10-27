---
review-evidence: 1
kind: review
seat: doc-propagation
verdict: approve
family: anthropic
worker: claude-haiku-5-5
base: 837f99369eba180d3680a283a599b18ac974120b
head: 974a34d3cf1f5685702ca49d3cc4cf791446f6bc
patch-id: b1c61de53a1c79b91e8cd46fbe92c18b61011f8c+790dbfe803c22991252028a1dcc30192617752a5
criteria-hash: 16765aa9a3f14bad
policy-version: f78a1b40e2adb3e1
recorded: 2026-10-27T07:52:12Z
---

Re-recorded at the close head: the seat reviewed the PR content at the head named in its report; the only change since is commit 974a34d (ticket 1233 close and archive, merge-gate tier: bookkeeping, 2 ticket paths), which changed the patch-id. Verdict unchanged, not re-run.

Doc-propagation seat on PR #1699, range 40c2d9bdbbb3e58e1038eb5bf4bb310f0a25baae...HEAD, tickets/reviews excluded. Launched by the coder, read-only; worker self-reported as claude-haiku-5-5. Report verbatim:

Model: Claude Haiku 5.5 (claude-haiku-5-5), DOC-PROPAGATION seat, read-only. Worktree: the PR worktree. Diff base 40c2d9bd...HEAD, tickets/reviews excluded. Nothing written, no git write commands run.

Findings:
- nit: skills/harness-doctor/references/authoring-skills.md:6-8 says the rules are "enforced by tests/test_skill_descriptions.py and tests/test_skill_frontmatter.py", but the capability bullet is enforced by scripts/check-agnostic.sh (carried over from the original wording; the move did not change it).
- consider: rules/authoring-skills.md:1-4 keeps `paths:` so the stub loads on every skill edit, while the unenforced rules (declared concurrency, split by exclusivity, runtime-bound names, skill-not-command, test one before blasting) now have their content only in the reference, which loads only on a doctor run; the stub names them but does not carry them. Ticket 1233 (tickets/1233-harness-doctor-lints-harness-skills-and.erg:25) flagged this as a trade-off to settle in the PR, and the diff does not record a decision.
- consider: rules/README.md:38 dropped the summary terms "declared concurrency, skill-not-command, test one before blasting, naming" from the conditional-rule index row, so the index no longer advertises the unenforced rules that now live only in the reference; the stub body still lists them, so this is an index-summary choice, not a broken pointer.
- consider: tickets/1229-harness-doctor-and-project-coherence-tra.erg:29 still names rules/authoring-skills.md as the home of the split-by-exclusivity rule; this is an open ticket body, so the pointer is stale (the stub now points to the reference).
- nit: tickets/1222-skill-references-runtime-neutral-plain-n.erg:17 and :33 still read as the original plan; the retarget is recorded in the log at :8, so this is covered.
- nit: scripts/check-agnostic.sh:25 is about 106 characters after the path substitution; the comment could be reflowed.
- consider (unverifiable from the diff): tickets/1233-harness-doctor-lints-harness-skills-and.erg is not in the diff stat, so the PR may not carry a close claim for ticket 1233; check the PR body against /merge.

Checked and clean: live citers of the guide path all point at the reference; no live file cites rules/authoring-skills.md for a rule that exists only in the moved guide; the stub's bullets match the moved guide; the catalog row matches; README.md, AGENTS.md, CONTRIBUTING.md name no skill list needing /harness-doctor; rules/README.md row and its link resolve; referenced scripts and tests exist; remaining hits are in frozen docs, memory/ and tickets/closed/.

No blocking or verifiable findings.

VERDICT: approve
