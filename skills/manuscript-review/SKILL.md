---
metadata:
  category: research
name: manuscript-review
description: "Review a manuscript with real literature retrieval, page evidence and a bounded check of major criticisms; preserve the original review and pending author decisions."
disable-model-invocation: false
user-invocable: true
argument-hint: "<manuscript.pdf> [annexes]"
---

# Manuscript review

One complete advisory review, then one source-aware verification pass. These
steps are **sequential-blocking**: verification needs the original review; author
decisions need both. Do not multiply readers before completing this cycle.
Independent-reader selection and synthesis belong to `external-peer-review`,
which reuses this protocol.

Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); seats that must be independent follow
`skills/route/references/decorrelation.md` ("The launch line").

1. Resolve the manuscript's project and permission to process its contents. Read
   project instructions, locate its R&R ledger and the exact manuscript revision.
   Inventory supplied and expected annexes, noting missing ones explicitly. Select
   the worker and effort through `/route` and record the routing reason.
   Uncleared content forces the local/private lane. This first runner supports
   only a hosted route and refuses uncleared fulltext before preparation. For
   that case use the local route from the session, and restrict any separate
   hosted searches to cleared citation metadata. Do not claim this runner
   completed a local review; it has no local backend.
2. Run `manuscript_review.py` from this skill's actual directory. Use a new
   project `release/<date>/review/<run-id>/` for each attempt. The script pins
   PDFs, hashes every input and per-page text/image, and renders **all** pages of
   the manuscript and annexes. Thin text layers are disclosed; the reader must
   inspect the image. Missing expected annexes remain a limitation, never an
   implied assessment. Refuse overwriting an existing attempt.
3. Read `references/reader-prompt.md` for provenance and the sourced adaptation
   of King–Worthington Appendix C. The runner launches one complete reviewer
   with reading and retrieval capabilities and then one bounded verifier.
   Native tool call/result events establish actual use; a claim that research
   occurred is insufficient. Both stages must read all text and images. The reader
   must search and fetch; the verifier retrieves each declared decisive source and
   searches when needed to locate evidence. Manuscript-only findings require no
   external retrieval during verification. Failed execution, missing terminal results, truncation,
   missing page coverage or missing major-finding evidence leave the run
   incomplete and return nonzero. This checks execution, not scientific truth.
   Markdown finding IDs and structured findings must cover each other; Key claims
   enumerates the major findings, or states exactly `No major findings.`. Each
   finding declares `decisive_urls` (empty only for manuscript-only criticism).
   Those URLs require observed retrieval attempts in the reader trace and matching
   verification sources for major findings; an unrelated fetch cannot substitute.
4. Inspect `status.json`, original `review.md`, `review.json`, `verify.json`,
   source traces and `ledger.jsonl`. Keep the review unchanged, show factual
   corrections alongside it, and preserve scientific disagreement. Each major
   finding has located manuscript evidence plus distinct factuality, severity
   and uncertainty judgments; each decisive external source has separate
   accessibility, identity, relevance and claim-support checks and a retrieved
   passage. Unavailable evidence needs an observed attempt and explicit reason;
   support stays unknown and the affected finding remains unverifiable. No scores, masks, artificial
   contradictions or comparative experiments belong in this production path.
   Passage matching checks returned fetch-tool text, which may be processed by a
   model; it does not establish a match against the original source bytes.
   Redirects count only when every hop has a matching observed fetch event.
5. Use the **existing** ingest-decision-letter ledger for author decisions and
   coverage. Exported rows carry `round`, `disposition: null`, `reason: ""`,
   `resolution: "open"`, and `evidence`; do not invent decisions or close work.
   The author accepts, contests, defers or records already satisfied remarks,
   supplying reasons and revision/ticket links through that workflow. Reuse
   Zotero for references; this runner's source evidence is not a second library.
   After a revision, run again with `--previous-run` and a new revision identifier,
   round and directory. History pins the preceding manifest; every attempt,
   including an incomplete one, remains intact. Stop after the decision round;
   another review requires a concrete revision or an explicit author request.

<!-- harness-extension-point -->
The supported native route is `claude -p --model <routed-token> --effort
<routed-effort>`, with stream JSON, read/search/fetch tools, safe/restricted mode,
no session persistence, no shell or write tools, and explicit turn/time bounds.
CLI authentication stays with the CLI. No credentials or provider API adapter
are implemented. Both passes use the explicit routed worker in fresh contexts;
the verifier is a check, not an independent-family review. Observed model names
come from CLI initialization/assistant metadata; absent identity stays absent.
A resumed run preserves the original reader route and records its new verifier separately.

Example, after routing and confirming the manuscript is public:

```bash
python3 /absolute/path/to/skills/manuscript-review/manuscript_review.py \
  --manuscript paper.pdf --annex supplement.pdf \
  --annex-inventory 'main paper and one supplement; none missing' \
  --revision '<commit-or-version>' --round round-1 \
  --run release/2026-10-23/review/attempt-1 \
  --clearance public --model '<routed-token>' --effort '<routed-effort>' \
  --route-reason '<route selection and why>' \
  --question 'What most needs correction before submission?'
```

PDFs, page text/images, prompts, raw streams and stderr are kept under ignored
`private/` in the run directory. Keep them locally for audit; exclusion avoids
accidental publication of manuscript fulltext. Durable manifests and hashes pin
those artifacts. Durable traces include reading paths and actual web tool results,
with raw stream line locators, while omitting manuscript Read returns. Original
reviews can quote a manuscript and web traces contain queries: inspect all durable
outputs before committing or publishing them. No artifact is automatically
committed, uploaded or imported. A nonzero run retains its status and partial
evidence; use a fresh attempt rather than editing it into apparent completeness.

For failed verification after a valid reader, use `--resume-review <attempt>`
with a fresh `--run` and the same inputs, revision, question, clearance and annex
inventory/limitations. This excludes `--previous-run`. The runner checks original
artifact hashes, revalidates the native reader stream at its original paths, and
matches its saved payload, Markdown and trace. It refuses sources with an existing
ledger. It copies the reader bundle unchanged and records `review.reuse.json`;
only the verifier runs again. The new cycle explicitly combines the old reader's
identity and evidence with a fresh verifier, preserving every earlier attempt.
Fetch prompts demand one contiguous verbatim excerpt, without joined quotations
or added ellipses; redirects without substantive content remain unavailable.
Passage checking follows only explicit native redirect receipts through URLs
actually fetched in that run, retaining their tool line locators. It rejects
cycles, ambiguous targets and chains longer than eight redirects, and never
substitutes an unrelated fetch or changes URL query parameters.
