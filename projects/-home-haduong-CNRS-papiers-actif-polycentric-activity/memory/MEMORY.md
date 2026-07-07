# Memory index — polycentric_activity

## Key insights

- Never trust a prior "no remote exists" (or similar environment) determination without re-verifying in the current working tree — state can be stale, wrong, or scoped to a different worktree, and the cost of acting on it wrong (a day of un-pushed work) is high.
- An untracked file a tracked file depends on is not automatically forgotten WIP — check for codegen markers (filecontents, generated-by comments) before committing it as source.
- Tool-level sanity checks that pass at the corpus/whole-repo level (`erg check`) don't guarantee the same operation passes at the single-file level a git hook actually runs (`erg validate <one file>`) — a clean corpus check is not a green light to skip testing the exact commit that's about to happen.
- The raid workflow (execute → adversarial re-derive → integration notation-collision check) is validated across multiple proof tickets and transfers well to mathematical research generally.
- When restructuring a paper (splitting a manuscript, moving a workpackage directory), grep exhaustively for every `\ref`/`\citep` into the moved content before deleting it — LaTeX won't warn about a reference to a definition that used to exist two sections up.
- Diverging uncommitted copies of the same file across two checkouts aren't automatically a live parallel-session conflict — diff them; one may be a strict, dated superset of the other, resolved by picking the newer copy, no merge needed.

## Entries

- [Raid for proofs](feedback_raid_for_proofs.md) — reviewers must re-derive; notation-collision check at integration; shared files excluded from agents. Corrected 2026-07-07: no-remote fallback only after re-verifying, not by default.
- [Verify uncommitted files before acting](feedback_verify_uncommitted_files_before_acting.md) — an untracked file a tracked file depends on may be generated (filecontents), not forgotten; check before committing it as source.
- [erg validate vs. closed-ticket Blocked-by](feedback_erg_validate_closed_ticket_blocked_by.md) — per-file `erg validate` on a `tickets/closed/*.erg` can't resolve Blocked-by refs to open siblings even though corpus-level `erg check` passes; strip Blocked-by lines when closing a ticket whose blockers are still open in substance.
- [Diverging uncommitted copies may be stale, not conflicting](feedback_diverging_uncommitted_copies_may_be_stale_not_conflicting.md) — diff before assuming two uncommitted copies are a live conflict; one may just be a stale duplicate of the other.
- [polycentric_activity: delete_branch_on_merge=false](project_delete_branch_on_merge_false.md) — every merged PR leaves its remote branch behind; delete manually (`git push origin --delete`) as part of hygiene.
- [Frais réels 2026](frais-reels-2026.md) — compta impôts dans perso/comptes/impots/déclaration 2027/frais réels/ (registre+PJ) ; y ranger les factures d'abonnements pro au fil de l'eau.
- [Dépôt HAL par SWORD](hal-sword-deposit.md) — recette API (clés hal.env, AOfr, ref fichier obligatoire sinon notice sans fichier, statuts accept/verify/update), pièges vécus.
