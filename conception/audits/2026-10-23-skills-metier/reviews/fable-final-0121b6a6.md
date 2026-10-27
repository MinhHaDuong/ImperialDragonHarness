Reading done. The find-work `--pdf` flag computes a content hash from any file path, so the Markdown note receipt path in the Zotero import reference is supported by the backend as described. I have what I need; here is the validation.

`[→ Verify] · Fable 5.1 · read-only final validation of 0121b6a6, no edits, no git, no subagents.`

## Verdict

**Validated with explicit limits, not a merge approval.** The changed skills implement the agreed protocol in KISS form: one tool-backed reader, one bounded verifier, immutable per-attempt evidence, decisions exported into the existing R&R ledger with the agreed field names. The engine is a single argparse script with no framework, no provider adapter, no credential handling. The old helper is untouched. Two material findings remain, both one-sentence fixes. Several things I could not inspect are listed as such.

## Material findings

1. **The "retrieved passage" check verifies the passage against the fetch tool's output, not against the source.** `skills/manuscript-review/manuscript_review.py:198-205` requires the verifier's `passage` to appear in a matching WebFetch result. In this runtime the web-fetch capability returns a model-processed rendering of the page, not its bytes. So the check proves "the passage appeared in what the fetch tool returned", which is weaker than SKILL.md line 50 ("a retrieved passage") and reader-prompt line 25 imply. Minimal fix: one sentence in SKILL.md and one entry in the `limitations` list at line 340 saying the fetched text is tool output and may be processed; in the verifier brief at line 261, ask that each fetch request verbatim quotation. No code change.

2. **The F3 import-timing contradiction the audit named is still in one runbook.** `skills/conference-submission-prep/runbooks/bib-merge.md:27-29` says the author imports refs.bib into Zotero "at manuscript submission". `rules/zotero.md`, `related-work-note/SKILL.md:50-53` and the Zotero import reference now say intake. Ticket 1200 forbade touching other lots' skills and ticket 1201 said to coordinate rather than edit these runbooks, so the line fell between the two. Minimal fix: replace those three lines with "Zotero is the system of record from intake; this script merges a citation view only."

## Checked and holding

- **Engine executability.** The launch at `manuscript_review.py:274-279` is a native CLI call with stream-JSON, read and web tools only, no shell or write tools, bounded turns and timeout, authentication left to the CLI. The trace parser accepts only a successful terminal event and requires a matching non-error tool result per call. Truncation, refusal, context overflow, non-zero exit, partial reads with offset or limit, missing page coverage, missing search or fetch, finding text absent from the Markdown review, and evidence pointing at an unknown page each leave the run incomplete and non-zero. The integration test exercises the full cycle with real poppler extraction and a fake CLI, including a truncated verifier and a refused re-run.
- **Same-family verifier.** SKILL.md lines 69-70 say the verifier is a check, not an independent-family review. Observed model names come from init and assistant metadata, and the full terminal event with `modelUsage` is kept in the durable trace. Nothing claims provider attestation.
- **R&R integration.** `ledger_records` at lines 222-231 emits exactly the agreed fields: `disposition: null`, `reason: ""`, `resolution: "open"`, `evidence` as reference strings, `round`. The ingest helper's `_normalize_record` and `coverage` accept them; a fresh engine ledger is reported uncovered until the author decides, which is the intended behavior. Cumulative archive manifest and round-scoped universe are implemented and tested.
- **Evidence preservation and recovery.** Each attempt is its own directory, refused if it exists; PDFs, page text and images, prompts, raw streams and stderr sit under a gitignored `private/` with hashes pinned in durable manifests. A timeout or interrupt writes the termination record and keeps partial evidence. Durable traces drop manuscript Read returns and keep web results. The SKILL discloses that reviews can quote the manuscript and that web queries may carry it.
- **Privacy boundary.** `--clearance uncleared` is refused before any preparation; the SKILL names the local lane for that case and restricts hosted searches to cleared metadata, and says this runner has no local backend.
- **Bibliography lot.** Both scripts use bibtexparser with a declared-versus-parsed count guard that aborts before any fetch or append; DOI deduplication is global and `date` is read when `year` is absent. Validator and runbooks state the four separate checks. Track-changes compile rejects a log with undefined citations or references, matching the summary lines in `rules/manuscript-build.md:42-45`, refuses the pdflatex fallback when a bibliography processor is needed, checks declared `.bib` resources exist inside the pinned tree, and takes pinned supplementary inputs. pdf-finish narrows anonymity to author identifiers and renders variants in isolated copies.
- **Zotero and research skills.** Import's duplicate handling now attaches via `suggest-attachments`, consistent with backfill. The Markdown note path is concrete and the backend's `attach_file` infers MIME from the filename, with `find-work --pdf` hashing any file. biblio-saturation names capabilities, drops tool names and batch sizes, and adds `unresolved` and `angle_blocked`; critical-lit-review states the handoff into saturation. Catalog lists both review skills; the old skill's "frontier" test is untouched.

## Could not inspect

- The reader-prompt provenance: the SHA-256 and Zotero key at `references/reader-prompt.md:6-12`, and the fidelity of the paraphrase to Appendix C. No Zotero or file access here.
- Whether every CLI flag at `manuscript_review.py:274-279` is accepted by the installed CLI. The repo shows prior real runs with `--effort`, `--safe-mode`, `--no-session-persistence`, `--strict-mcp-config` and `--tools ''`; I found no observed run using `--restricted`, `--disable-slash-commands` or a `--tools` list. The fake CLI in the test ignores flags. An unknown flag fails safe as a non-zero exit, and the running public trial is the check that settles it.
- No test execution and no gate run; the counts in the ticket logs are the executors' reports.

## Optional simplifications, separate from the findings

- Ledger id uses `round-1-R1-01` while the ingest convention is `r1:R1-01`. Use the colon form for consistency.
- `category` receives the severity at line 224; the ingest schema reserves it for framing, method, data and so on. Leave it empty and let severity stay in `verify.json`.
- `history.json` and the durable traces record absolute host paths. Relativize to the run directory before these artifacts are committed in a paper repo.
- The verifier must search and fetch even when every source list is empty. Require it only when a source is listed.
- Default `--reader-turns 60` may be low for a long manuscript read page by page. Note it in the SKILL rather than raising the default.
