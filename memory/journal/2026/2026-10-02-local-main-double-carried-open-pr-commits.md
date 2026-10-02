# Local main carried SHA-identical copies of open PR #1143's commits into PR #1145

Context: harness steering session on 2026-10-02, primary checkout at
/home/haduong/.agents. Ticket steers for 1016 (option 1) and 1017 (seat
design) were committed on local main. A direct push of main was rejected
twice: first non-fast-forward (parallel raid history had landed on
origin/main), then by branch protection (7 required status checks on
main), so the accumulated local-main history went up as PR #1145 on
branch t1016-1017-seat-design-steers.

Observation: the CI check `cross-pr-ticket-collision`
(scripts/check-cross-pr-ticket-collision.sh) failed the PR with
"COLLISION: ticket ID 1018 is also added by open PR #1143". Cause: four
zotero commits sitting on local main (docs: zotero-integration
revision; rules: edm.md renamed zotero.md; tickets: close 0485;
tickets: file 1018 — c8c79118, 65737ba9, 741bc61e, b7e422f0) were
SHA-identical to the first four commits of open PR #1143's head branch
zotero-arch-close-0485, which a parallel session had created from the
same local history. PR #1145 therefore double-carried another open
PR's work, and the ticket-ID guard was the only merge-gate signal.

Consequence: the PR branch was rebuilt from origin/main with only the
five session commits (cherry-pick of 0e7ff520, ce29a26c, 4dd7c426,
78636d10, 82e4e44b), force-pushed with --force-with-lease; all 10
checks passed and erg-pr-merge merged PR #1145 (c7534e00, Ticket:
none). Local main remains diverged (ahead 10, behind 6): its unique
content is the four zotero commits (SHA-identical to #1143's open
branch), a merge commit of since-merged history, and five superseded
steer SHAs whose patches are upstream via #1145. Repair (reset local
main to origin/main) is pending the author's call; the duplicate SHAs
are preserved in #1143's branch either way.

Evidence: PR #1145 checks run 37002749862 (fail) and 37002948462
(pass); `git cherry origin/main` showing `+` only for the four zotero
commits; gh pr view 1143 commit list matching local SHAs.
