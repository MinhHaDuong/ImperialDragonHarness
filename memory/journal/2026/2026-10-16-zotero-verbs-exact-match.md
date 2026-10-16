# Zotero helper: specific verbs and exact-identifier matching (ticket 1116)

Audience: public. 2026-10-16, padme, Claude Code session; PRs #1447 and #1448
(both merged), closing ticket 1116.

## Decisions made by the author

- Rename the subcommands to say what they do, no aliases; split `probe` into
  `extract-metadata` (format dependent, no Zotero) and `find-work` (local-API
  lookup): "Extracting is different than looking up."
- Eight cuts accepted ("oui à tout", "oui oui oui"), then three more after the
  writer's first pass left `scripts/zotero.py` at 3,005 lines ("Oui pour
  tout"): no hand-rolled match scoring (exact normalised identifier or PDF md5
  only; title hits are candidates), `check-staging` as the merged command name,
  Zotero item types instead of RIS codes.
- The 15-file /gaze breaker was waived per PR, verbatim: "Je lève le seuil des
  15 fichiers pour #1447" and "... pour #1448, et je garde les cinq choix."
  A waiver relayed by the orchestrator without the author's words was refused
  by /gaze on #1447.
- The re-measure of read timing on doudou was withdrawn: "On a plus besoin de
  remesurer".

## Observed events

- `scripts/zotero.py` line counts: 3,100 on main before 1116; 3,002 after
  #1447; 3,005 after the writer's first #1448 (lookup through Zotero search plus
  a hand-rolled scorer); 2,789 after the scorer cut.
- pdf2doi 1.7, run offline with network guarded, returned a DOI from a PDF's
  reference list where the document had none; rejected.
- #1447's own test `test_extract_metadata_never_contacts_zotero` passed locally
  and failed on CI because poppler is not installed there; found by a regression
  seat and the cross-family codex seat.
- The live Zotero tests skipped once because the shared /tmp tmpfs (32 GB) was
  full of other sessions' files, so Xvfb could not start.
- `erg-pr-merge` on #1448 aborted when its checks had not registered yet, after
  pushing the ticket close commit; a re-run armed auto-merge, the forge did not
  merge a CLEAN, all-green PR, and a second re-run merged it directly.

## References

PRs #1447, #1448; ticket `tickets/closed/1116-zotero-helper-specific-subcommand-names.erg`;
`memory/evidence/2026-10-16-review-identities-pr1447-1448.md`.
