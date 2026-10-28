# Skills catalog

<!-- Generated from skills/*/SKILL.md; run make skills-catalog. -->

## Generalist

### The build loop

| Command | Description |
|---------|-------------|
| `/hunt` | Work a ticket: plan, execute in its own worktree, verify adherence, ask /gaze to review, fix and open a merge request. Does not merge. |
| `/verify-adherence` | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. |
| `/gaze` | Review one merge request: plan the checks that settle what the caller asks, run them once, check the plan against what ran, post one result: REVIEWED / FINDINGS / ESCALATE. Does not modify code. |
| `/verify-gate` | Anti-rubber-stamp merge gate: checks every ticket exit criterion and review comment against the diff. Emits APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR with evidence. Does not merge. |
| `/merge` | Land a merge request: close its claimed ticket, check the gate record on a gated base, merge pinned to the reviewed head, read the result back, sync local main. Cleanup is left to /roar. |
| `/roar` | Post-task wrap-up after one or more merge(s): clean task branches, reflect, capture significant facts, update state. |
| `/raid` | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |

### The session loop

| Command | Description |
|---------|-------------|
| `/yawn` | Repo morning health check, read-only: git hygiene, test status, doc freshness; degrades without project conventions. Usually suggests /molt to fix findings. |
| `/molt` | Repo housekeeping: git sync, yawn, fix-now repairs, tickets for findings. Safe interactively or in automated sweeps. Everything /roar missed. |
| `/dashboard` | Ticket dashboard: open tickets, branches and merge requests; full state plus a delta led by the ticket count. Read-only. |
| `/perch` | Mid-session orientation: summarize what's done, surface unresolved points, assess clear-readiness. Read-only. |
| `/lair` | End-of-day wrap-up: housekeeping, push branches, run tests, refresh STATE. Run it last: parallel sessions are only partly protected. |

### Project maintenance

| Command | Description |
|---------|-------------|
| `/test-doctor` | Consulting doctor for a project's slow, flaky or stale test gates. Author-called. |
| `/trace-doctor` | Surveying doctor of session-trace costs and waits over all sessions; refers cases to /test-doctor, /harness-doctor or tickets. Never auto-applies. |
| `/harness-doctor` | Consulting doctor for harness skills and rules: contradiction, overlap, drift. Author-called, harness only. |

### Memory and learning

| Command | Description |
|---------|-------------|
| `/hoard` | Consolidate one project's repository memory, pruning stale or contradicted claims, without proposing rules. |
| `/brood` | Turn accepted Hoard findings into project improvements and scoped harness nominations, on explicit request. |

### Runtime and review support

| Command | Description |
|---------|-------------|
| `/reviewers` | Describe live independent review needs and let the active runtime discover and route optional reviewers, preserving findings and integrity evidence. |
| `/route` | Model routing: performance grid, route cache, triage, clusters. The single home for which model serves which work. |

## Research

### Research and bibliography

| Command | Description |
|---------|-------------|
| `/biblio-saturation` | Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness. |
| `/critical-lit-review` | Critical literature review (état de l'art) in history of economics and STS: object, actors, controversies. |
| `/reading-note` | Critical reading note (note de lecture) on one article or book, filed in Zotero. |
| `/related-work-note` | Due-diligence note for one cited paragraph of a manuscript: relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/zotero` | Import PDFs or URLs into Zotero, suggest edits or attachments to existing items, check staged files against the library, or report duplicate files: extract metadata, resolve identifiers, create items with PDFs through the running Zotero's local API. |

### Reviewing

| Command | Description |
|---------|-------------|
| `/external-peer-review` | Obtain independent AI peer reviews of a manuscript PDF; preserve dissent and synthesize verified findings. |
| `/manuscript-review` | Review a manuscript with real literature retrieval, page evidence and a bounded check of major criticisms; preserve the original review and pending author decisions. |
| `/ingest-decision-letter` | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check mapping every remark to a ticket. Helps streamline Revise-and-Resubmit. |

### Writing and delivery

| Command | Description |
|---------|-------------|
| `/message-framing` | Frame the central message of a talk, abstract or article before drafting it. |
| `/cut-prose` | Cut a document to a word or page budget by removing whole passages before condensing anything. Fights LLM hair shaving tendencies. |
| `/pdf-finish` | Finishing pass on a PDF deliverable — journal submission, preprint deposit, personal page, report handoff. |
| `/slides` | Make or review a talk's slide deck: build a beamer deck from a written text, or critique an existing deck with prioritized fixes. |
| `/track-changes-pdf` | Render a revision-marked PDF of a LaTeX manuscript between two git refs, marking insertions and deletions via latexdiff. |

### Submission and publication

| Command | Description |
|---------|-------------|
| `/aap-annonce` | Process a call-for-proposals announcement (AAP, appel à projets): file it, calendar deadlines, assess fit, propose three entry angles. |
| `/choose-venue` | Choose where to submit a paper: shortlist journals, or conferences, by fit and diamond open access. |
| `/conference-submission-prep` | Prepare a humanities and social sciences conference submission from its call for papers. Use once venue is chosen and key messages are framed. |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/submission-event` | Classify a manuscript submission event (submitted, resubmitted, accepted, published) by its object's external register; propagate to the homepage publications list (works) or CNRS secretariat roadmap (work in progress), never both automatically. |
| `/update-publist` | Add or update a publication on the author's personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
