# Fable : avis de conception KISS

Révision examinée : `1206b23e`.

[→ Verify] · read-only design review of commit 1206b23e, no edits made.

**Overall verdict.** The audit's diagnosis holds and the seven-step protocol is the right shape. Two decisions are missing before the engine lot can start, and both change what gets built: where the reader prompt comes from, and how a reader gets real tools. Everything else is small corrections to existing helpers.

## Material findings

1. **The reader prompt does not exist in the repo.** Ticket 1199 line 15 requires a sourced King–Worthington prompt. Grep finds the name only in the audit and the ticket. The executor will reconstruct it from memory. Correction: before 1199 starts, stage the paper through the zotero skill and commit `references/reader-prompt.md` with the citation, the verbatim core, and each adaptation marked.

2. **"Search tools actually used" is unobservable through a chat-completion call.** The old helper at `skills/external-peer-review/peer_review.py:284` sends one message and gets text back. Only the headless launch doors in `skills/route/routes.json:72-110` give a reader tools and a transcript that proves tool use. Correction: the engine is an orchestrator around one headless reader run plus a file contract on the run directory, not an HTTP client. This also removes all credential code from the new script, since each CLI manages its own.

3. **Private manuscripts and real retrieval conflict.** The route skill forces uncleared content to local models, which have no web access. Ticket 1205 line 17 starts with a public manuscript, which is right, but no ticket says what the private path is. Correction: state in the engine SKILL that for uncleared text the reader runs locally and the verification searches run from the session with citation metadata only.

4. **The decisions step depends on 1202, and the two tickets are parallel.** Ticket 1199 line 18 wants author decisions linked to revisions and reuse of the R&R ledger. The ledger schema at `skills/ingest-decision-letter/ingest_letter.py:58-68` has no disposition field yet. Correction: fix the field names now in 1202's exit criteria so 1199 consumes them without drift: `disposition` in {accepted, contested, deferred, already_satisfied, null}, `rationale`, `resolution` as a commit or path. The engine emits a review text that `segment` ingests under a reviewer label, and stops there.

5. **The four source-check statuses are in 1200 but not in 1199.** Ticket 1200 line 16 separates accessibility from identity and support. The engine's verifier needs the same vocabulary or two incompatible records appear. Correction: add one line to 1199 naming the four statuses accessible, identity, relevant, supports-claim for each decisive attribution.

6. **Run evidence under `docs/` would be gitignored.** Paper repos ignore `docs/**` including Markdown. Correction: the run directory lives under `release/<date>/review/<run-id>/`, beside the R&R archive, with manifest, text, findings and verification committed and the PDF pinned by hash and git ref only.

7. **New skill name and location.** Putting the script inside external-peer-review inherits a description promising frontier-class multi-reviewer synthesis, a test at `tests/test_external_peer_review_skill.py:33-38` requiring the word "frontier", and the "3 of 4 outranks" rule at `references/openrouter.md:70-72`. Correction: a new skill directory with a plain name. Avoid `review`, which Claude Code binds. Regenerate the catalog in the same PR.

8. **Truncation check pattern already exists.** `scripts/coaching/seat-runner/direct-client.py:83-91` rejects a non-stop finish reason and empty content. For a headless reader the equivalent is structural: exit status, required sections present, every major finding carrying a page that exists in the manifest, a non-empty search log when retrieval was required. Missing any of these writes status incomplete and exits non-zero.

## Smallest corrections for the other lots

- **F2.** `scripts/validate-refs.py:66-80` keeps a regex splitter while `scripts/bib-merge.py:149-190` has a working parser. Hyphenated filenames prevent import, so move the parser into an importable `scripts/bibtex_parse.py` and use it in both. At `validate-refs.py:193-195`, report entries seen versus parsed instead of "0 of 0". In `bib-merge.py:228-233`, read `date[:4]` when `year` is absent, and check a DOI index before the author-year bucket at line 326.
- **F4.** At `ingest_letter.py:396-405`, use `--tickets-dir` only to validate unknown references and build the orphan universe from `--tickets`. At lines 174-177, read and extend the existing manifest instead of overwriting it.
- **F5.** After each compile in `track_changes_pdf.py:197-209`, read the log for the summary lines named in `rules/manuscript-build.md:42-45` and fail on them. When only pdflatex is available and the source names a bibliography resource, refuse with a message rather than run two passes. After extraction, check that every `\addbibresource` or `\bibliography` target exists and name the missing file. In `skills/pdf-finish/SKILL.md:51`, narrow the anonymity grep to the author's own identifiers; at lines 59-64, render variants in an isolated copy at a pinned commit.
- **F3.** `skills/zotero/references/import.md:100` tells the user to import a duplicate when the hit has no file; `references/backfill.md:128-137` forbids exactly that. Replace the exception with `suggest-attachments --edit`. `skills/related-work-note/SKILL.md:49-50` defers import to submission; align with intake. Verify that the attach path in `scripts/zotero.py` accepts a Markdown file before promising a note receipt in `reading-note` step 4.
- **F6.** `skills/biblio-saturation/SKILL.md:37-46` and 106-110 name a workflow tool, a batch size and tool names, which `rules/authoring-skills.md` already forbids. Add `unresolved` and `angle_blocked` to the outputs at lines 116-125 and exclude blocked rounds from the dryness test at 89-91.

## Suggested architecture

One skill directory, one argparse script of pure I/O in the style of `ingest_letter.py`, three subcommands. `prepare` hashes the PDF, extracts text per page and renders every page, flags thin text layers, and refuses an existing run directory. `brief` writes the reader brief from the committed prompt, the manifest facts, the author's question and the output contract. `check` validates completeness as in finding 8, captures the model identity from the raw launch output when present and records it as unverified otherwise, and writes a status file. The verification pass is a second brief and a second `check`, producing one record per major finding with confirmed, not found, misread or unverifiable, plus the four source statuses. Decisions go through the ledger of 1202.

Production review is one reader, one verification pass, one report, one decision round. The A/B comparisons, relevance masks, order permutations and scores of the paper belong to a later experiment mode. Ticket 1205 line 27 already excludes them from the trial, so v1 needs no flag for them.

Reviewer identity for the Astra and Fable passes should come from launch metadata, as 1205 line 21 requires, and the two seats are from different families, which satisfies the decorrelation rule. The repo has no scoped check file, so each wave-1 PR runs the full gate.