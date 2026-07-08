# Memory index — polycentric_activity

## Key insights

- The author's communication norms are strict and specific — no irony or authorial winks, musical/structure terms only in their exact sense, one shared refs.bib per project — hold manuscript prose to those standards, not generic academic defaults.
- Uncommitted or untracked files demand inspection before you act on them: they may be generated (filecontents), stale duplicates of a tracked file, or partial WIP — diff and check provenance before committing, discarding, or assuming a live conflict.
- Tooling has level-specific behaviour: `erg validate` differs at file vs corpus level, `delete_branch_on_merge` is false here (merged PRs leave remote branches) — verify at the exact level the operation runs, never assume.
- Instruction order carries design intent — a later instruction that changes the toolchain redefines the design space of an earlier one; execute sequentially and re-derive earlier parts against the new world.
- Data-source limits are real and worth remembering: OpenAlex can't reconstruct pre-1970 works' outgoing references, so reference-overlap/indirect analysis over mid-century sources is a structural null — hand-curation beats a database crawl there.

## Entries

- [Raid for proofs](feedback_raid_for_proofs.md) — reviewers must re-derive; notation-collision check at integration; shared files excluded from agents. No-remote fallback only after re-verifying.
- [Verify uncommitted files before acting](feedback_verify_uncommitted_files_before_acting.md) — an untracked file a tracked file depends on may be generated (filecontents), not forgotten; check before committing it as source.
- [erg validate vs. closed-ticket Blocked-by](feedback_erg_validate_closed_ticket_blocked_by.md) — per-file `erg validate` on `tickets/closed/*.erg` can't resolve Blocked-by refs to open siblings even though corpus-level `erg check` passes.
- [Diverging uncommitted copies may be stale, not conflicting](feedback_diverging_uncommitted_copies_may_be_stale_not_conflicting.md) — diff before assuming two uncommitted copies are a live conflict; one may just be a stale duplicate of the other.
- [polycentric_activity: delete_branch_on_merge=false](project_delete_branch_on_merge_false.md) — every merged PR leaves its remote branch behind; delete manually (`git push origin --delete`) as part of hygiene.
- [Frais réels 2026](frais-reels-2026.md) — compta impôts dans perso/comptes/impots/déclaration 2027/frais réels/ (registre+PJ) ; y ranger les factures d'abonnements pro au fil de l'eau.
- [Dépôt HAL par SWORD](hal-sword-deposit.md) — recette API (clés hal.env, AOfr, ref fichier obligatoire sinon notice sans fichier, statuts accept/verify/update), pièges vécus.
- [No irony](user_no_irony.md) — author firmly proscribes irony; reflexive facts stated flat, no winks/litotes, in manuscripts and in my summaries.
- [Musical terms need precision](user_musical_terms_precision.md) — author is a trumpeter; "coda" mid-paper rejected (a coda TERMINATES). Name sections by function, not musical/literary structure words.
- [Single bib database preference](user_single_bib_database_preference.md) — one refs.bib per project, no per-manuscript bib files or filecontents embedding; twin identities (original vs reprint) coexist under distinct keys with cross-notes.
- [Sequential instructions: order matters](feedback_sequential_instructions_order_matters.md) — a later instruction that changes the toolchain redefines the design space of an earlier one; execute in order and re-derive earlier parts against the new world.
- [OpenAlex pre-1970 citations](reference_openalex_pre1970_citations.md) — OpenAlex has no outgoing references for old works; incoming citations reliable, reference-overlap/2-hop analysis is a structural null. Hand-transcribe bibliographies instead.
