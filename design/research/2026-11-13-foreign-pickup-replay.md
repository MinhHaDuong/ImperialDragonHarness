# Foreign-ticket pickup replay

Ticket 1546; performed 2026-11-13. This is a retrospective replay of the
four pickup checks, with outcomes visible. It tests whether the procedure
names the recorded corrections; it does not estimate a blind triage benefit.

## G2: git-erg 0243

Facts against framing: the filed report at git-erg `2807b8e16574` asks
`erg update` to prune old installed skills. Reading
`2807b8e16574^:src/go/update.go` shows update replaces the binary and
explicitly leaves embedded assets to separate commands. The observed stale
skills are credible; making update their cleanup command contradicts its
contract. Correction: target the migration/legacy-layout cleanup path.

Duplicates and overlap: the report itself names AEDIST 0355 and 0526 as
source and related stale-hook work. Treat them as evidence for one receiving
request rather than independent new defects. Ownership: git-erg owns the
migration behavior; adopters own installing its result. Standing rulings:
preserve update's binary-only contract; a contrary author instruction would
be a question, not an automatic refusal. Owner outcome `6fd3851fd5f9`
retargeted 0243 to `erg migrate`, matching this correction. The earlier blind
trial's `erg init` guess is not adopted.

## H3: harness 1492

Facts against framing: the filed report at `a7b3c098f26a` correctly observes
self-closing close claims but presumes an automated ticket-filing flow.
Reading the receiving merge skill at its parent finds the close-claim
consumer, without such a filing generator. The pre-filing journal
`memory/journal/2026/2026-11-09-native-store-prune-1481.md` lists six PRs,
including climate-finance-het #2050, and already records AEDIST's next-id scan
timeout. Corrections: address the landing-side claim interpretation, include
the sixth affected PR, and distinguish allocation timeout from unproved
failure to allocate an ID.

Duplicates and overlap: these are follow-through on rollout 1481 and its
six adoption records; search those rather than file six unrelated repairs.
Ownership: the harness owns the merge convention; each adopter owns review
and repair of its own PR. Standing rulings: ticket-only status cannot waive
receiver authorization, and a proposed guard must preserve legitimate
file-and-close work. The owner's subsequent Verify/Imagine record and
`memory/journal/2026/2026-11-09-raid-4afdb3-post-skill-gaze-close.md` identify
the same four corrections. The latter also records that the broad proposed
guard would reject legitimate file-and-close PRs. No new guard is warranted.
