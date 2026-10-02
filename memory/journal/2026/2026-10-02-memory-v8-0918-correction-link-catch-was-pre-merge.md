# Correction: the relocated-clone link catch happened pre-merge, on the PR's CI

Context: second correction entry for
[journal/2026/2026-10-02-memory-v8-0918-post-merge-link-catch.md](2026-10-02-memory-v8-0918-post-merge-link-catch.md),
which stays unchanged. The first withdrawal
([withdrawn-claim-local-gate-cause](2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md))
retired its wrong causal claim; this entry corrects its remaining framing
error, found while recording the trial's review facts.

Observation: the original entry describes "the freshly merged protocol"
containing the unresolved directory references. The pytest-guard failure
occurred on the merge request's own CI run, at PR head cf6c3f61, before
the merge: the protocol's directory links were present at
docs/memory-v8/evaluation-protocol.md:106, :193 and :197 at that head, the
CI check failed on them, the fix commit 3c7aa8cb landed on the same branch,
CI went green on the new head, and only then did the merge (be1ea2fc)
happen. Nothing defective ever reached main. The entry's own Evidence line
already said "PR #1137 review/CI history"; its framing words
("post-merge", "freshly merged") contradicted that and are retired here.

Consequence: the capture remains what its position was — a post-merge
capture (written on a closure branch after the real #1137 merge, bundled in
one PR) — but the event it records was a pre-merge CI catch. The trial's
S5.a cell and the trial results now describe it that way. The original
entry and the first withdrawal stand unchanged.

Evidence: PR #1137's check history (pytest-guard red at head cf6c3f61,
green at 3c7aa8cb), the merge commit be1ea2fc, and the directory-reference
line numbers at cf6c3f61 cited above, verifiable in any checkout.
