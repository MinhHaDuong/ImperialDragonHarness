# Withdrawn claim: why the local gate missed the protocol's directory links

Context: withdrawal entry for
[journal/2026/2026-10-02-memory-v8-0918-post-merge-link-catch.md](2026-10-02-memory-v8-0918-post-merge-link-catch.md),
which stays unchanged per the append-only convention. That entry explained
its Observation with the claim that "the protocol file did not yet exist on
main when the pilot test's clone was taken in earlier rounds". This entry
withdraws that causal claim and records what the session record establishes
instead.

Observation (established): in the STEP A session the full pre-PR gate
(`make check` through `scripts/raid-gate.py`) ran BEFORE the protocol,
test and ticket commits were made — the three files existed only as
untracked working-tree files at gate time. The relocated-clone proof
clones the repository's committed HEAD, so an untracked file is invisible
to the proof no matter what branch or round the clone is taken in. CI ran
against the pushed branch, where the protocol was committed, and caught the
links. The cause is commit-ordering between the gate and the document, not
the document's absence from main "in earlier rounds".

Consequence: the withdrawn phrasing is retired from consolidated memory;
the established cause above replaces it. The entry's remaining claims
(CI caught the defect, the fix pointed the references at concrete files,
all ten checks green on the new head) stand. The authority boundary of
this withdrawal: it corrects a factual attribution in project memory
only, derives no rule, and touches no file outside memory/ on this branch.

Evidence: the STEP A session record (gate run preceding the three commits
in the same session, PR #1137), the proof's mechanism
(tests/test_memory_v8_pilot.py: `git clone` of the checkout, then
`unresolved_links` over the moved clone), and the merged protocol at
be1ea2fc. The correction was prompted by the 0918 protocol's S8 trial
(withdrawal of a claim traceable to its original entry); the grounds are
the session record, not the trial.
