# Skills catalog

<!-- Generated from skills/*/SKILL.md; run make skills-catalog. -->

## Generalist

### The build loop

| Command | Description |
|---------|-------------|
| [`/hunt`](skills/hunt/SKILL.md) | Work a ticket: plan, execute in its own worktree, verify adherence, ask /gaze to review, fix and open a merge request. Does not merge. |
| [`/verify-adherence`](skills/verify-adherence/SKILL.md) | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. |
| [`/gaze`](skills/gaze/SKILL.md) | Review one merge request: plan the checks that settle what the caller asks, run them once, check the plan against what ran, post one result: REVIEWED / FINDINGS / ESCALATE. Does not modify code. |
| [`/verify-gate`](skills/verify-gate/SKILL.md) | Anti-rubber-stamp merge gate: checks every ticket exit criterion and review comment against the diff. Emits APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR with evidence. Does not merge. |
| [`/merge`](skills/merge/SKILL.md) | Land a merge request: close its claimed ticket, check the gate record on a gated base, merge pinned to the reviewed head, read the result back, sync local main. Cleanup is left to /roar. |
| [`/roar`](skills/roar/SKILL.md) | Post-task wrap-up after one or more merge(s): clean task branches, reflect, capture significant facts, update state. |
| [`/raid`](skills/raid/SKILL.md) | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |

### The session loop

| Command | Description |
|---------|-------------|
| [`/yawn`](skills/yawn/SKILL.md) | Repo morning health check, read-only: git hygiene, test status, doc freshness; degrades without project conventions. Usually suggests /molt to fix findings. |
| [`/molt`](skills/molt/SKILL.md) | Repo housekeeping: git sync, yawn, fix-now repairs, tickets for findings. Safe interactively or in automated sweeps. Everything /roar missed. |
| [`/dashboard`](skills/dashboard/SKILL.md) | Ticket dashboard: open tickets, branches and merge requests; full state plus a delta led by the ticket count. Read-only. |
| [`/perch`](skills/perch/SKILL.md) | Mid-session orientation: summarize what's done, surface unresolved points, assess clear-readiness. Read-only. |
| [`/lair`](skills/lair/SKILL.md) | End-of-day wrap-up: housekeeping, push branches, run tests, refresh STATE. Run it last: parallel sessions are only partly protected. |

### Project maintenance

| Command | Description |
|---------|-------------|
| [`/test-doctor`](skills/test-doctor/SKILL.md) | Consulting doctor for a project's slow, flaky or stale test gates. Author-called. |
| [`/trace-doctor`](skills/trace-doctor/SKILL.md) | Surveying doctor of session-trace costs and waits over all sessions; refers cases to /test-doctor, /harness-doctor or tickets. Never auto-applies. |
| [`/harness-doctor`](skills/harness-doctor/SKILL.md) | Consulting doctor for harness skills and rules: contradiction, overlap, drift. Author-called, harness only. |

### Memory and learning

| Command | Description |
|---------|-------------|
| [`/hoard`](skills/hoard/SKILL.md) | Consolidate one project's repository memory, pruning stale or contradicted claims, without proposing rules. |
| [`/brood`](skills/brood/SKILL.md) | Turn accepted Hoard findings into project improvements and scoped harness nominations, on explicit request. |

### Runtime and review support

| Command | Description |
|---------|-------------|
| [`/reviewers`](skills/reviewers/SKILL.md) | Describe live independent review needs and let the active runtime discover and route optional reviewers, preserving findings and integrity evidence. |
| [`/route`](skills/route/SKILL.md) | Model routing: performance grid, route cache, triage, clusters. The single home for which model serves which work. |

## Research

### Research and bibliography

| Command | Description |
|---------|-------------|
| [`/biblio-saturation`](skills/biblio-saturation/SKILL.md) | Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness. |
| [`/critical-lit-review`](skills/critical-lit-review/SKILL.md) | Critical literature review (état de l'art) in history of economics and STS: object, actors, controversies. |
| [`/reading-note`](skills/reading-note/SKILL.md) | Critical reading note (note de lecture) on one article or book, filed in Zotero. |
| [`/related-work-note`](skills/related-work-note/SKILL.md) | Due-diligence note for one cited paragraph of a manuscript: relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| [`/zotero`](skills/zotero/SKILL.md) | Import PDFs or URLs into Zotero, suggest edits or attachments to existing items, check staged files against the library, or report duplicate files: extract metadata, resolve identifiers, create items with PDFs through the running Zotero's local API. |

### Reviewing

| Command | Description |
|---------|-------------|
| [`/external-peer-review`](skills/external-peer-review/SKILL.md) | Obtain independent AI peer reviews of a manuscript PDF; preserve dissent and synthesize verified findings. |
| [`/manuscript-review`](skills/manuscript-review/SKILL.md) | Review a manuscript with real literature retrieval, page evidence and a bounded check of major criticisms; preserve the original review and pending author decisions. |
| [`/ingest-decision-letter`](skills/ingest-decision-letter/SKILL.md) | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check mapping every remark to a ticket. Helps streamline Revise-and-Resubmit. |

### Writing and delivery

| Command | Description |
|---------|-------------|
| [`/message-framing`](skills/message-framing/SKILL.md) | Frame the central message of a talk, abstract or article before drafting it. |
| [`/cut-prose`](skills/cut-prose/SKILL.md) | Cut a document to a word or page budget by removing whole passages before condensing anything. Fights LLM hair shaving tendencies. |
| [`/pdf-finish`](skills/pdf-finish/SKILL.md) | Finishing pass on a PDF deliverable — journal submission, preprint deposit, personal page, report handoff. |
| [`/slides`](skills/slides/SKILL.md) | Make or review a talk's slide deck: build a beamer deck from a written text, or critique an existing deck with prioritized fixes. |
| [`/track-changes-pdf`](skills/track-changes-pdf/SKILL.md) | Render a revision-marked PDF of a LaTeX manuscript between two git refs, marking insertions and deletions via latexdiff. |

### Submission and publication

| Command | Description |
|---------|-------------|
| [`/aap-annonce`](skills/aap-annonce/SKILL.md) | Process a call-for-proposals announcement (AAP, appel à projets): file it, calendar deadlines, assess fit, propose three entry angles. |
| [`/choose-venue`](skills/choose-venue/SKILL.md) | Choose where to submit a paper: shortlist journals, or conferences, by fit and diamond open access. |
| [`/conference-submission-prep`](skills/conference-submission-prep/SKILL.md) | Prepare a humanities and social sciences conference submission from its call for papers. Use once venue is chosen and key messages are framed. |
| [`/release`](skills/release/SKILL.md) | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| [`/submission-event`](skills/submission-event/SKILL.md) | Classify a manuscript submission event (submitted, resubmitted, accepted, published) by its object's external register; propagate to the homepage publications list (works) or CNRS secretariat roadmap (work in progress), never both automatically. |
| [`/update-publist`](skills/update-publist/SKILL.md) | Add or update a publication on the author's personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
