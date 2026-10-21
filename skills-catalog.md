# Skills catalog

<!-- Generated from skills/*/SKILL.md; run make skills-catalog. -->

## Generalist

### Build and ship

| Command | Description |
|---------|-------------|
| `/gaze` | Review one merge request: adherence check, code or prose review panel, simplify. Returns REVIEWED / FINDINGS / ESCALATE and never APPROVED; the merge gate is /verify-gate, run by the caller. Does not merge. |
| `/hunt` | Begin work on a ticket — creates a worktree and writes the first test. |
| `/merge` | Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI). |
| `/raid` | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |
| `/verify-gate` | Anti-rubber-stamp merge gate: checks every ticket exit criterion and review comment against the diff. Emits APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR with evidence. Does not merge. |

### Session and maintenance

| Command | Description |
|---------|-------------|
| `/dashboard` | Ticket dashboard: open tickets, branches and merge requests; full state plus a delta led by the ticket count. |
| `/lair` | End-of-day wrap-up: housekeeping, push branches, run tests, refresh STATE, offer an autonomous session. Not for one merged task (/roar) or a mid-session check (/perch). |
| `/molt` | Repo housekeeping that acts: git sync, yawn, fix-now repairs, tickets for findings. Safe interactively or in automated sweeps. Not for a plain check (/yawn). |
| `/perch` | Mid-session orientation: summarize what's done, surface unresolved points, assess clear-readiness. Not for end-of-day (/lair) or post-merge (/roar) wrap-up. |
| `/pulse` | Testing expert for slow, flaky or stale test gates; author-called only. |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/roar` | Post-task wrap-up after a merge: reflect, capture significant facts, update state, clean task branches. Not for consolidating or auditing memory (/hoard) or ending the day (/lair). |
| `/yawn` | Repo healthcheck, reports first, fixes on request: git hygiene, test status, doc freshness; degrades without project conventions. Not for unprompted fixes (/molt). |

### Memory and learning

| Command | Description |
|---------|-------------|
| `/brood` | Turn accepted Hoard findings into project improvements and scoped harness nominations, on explicit request. |
| `/hoard` | Consolidate one project's repository memory, pruning stale or contradicted claims, without proposing rules. Use to tidy accumulated memory; not for new facts (/roar). |
| `/trace-doctor` | Monthly survey of Claude Code session-trace economics: cost census, hypothesis statistics, ranked cost-saving report cross-referenced to tickets. Never auto-applies; files tickets for findings. |

### Runtime and review support

| Command | Description |
|---------|-------------|
| `/review-pr` | Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation. |
| `/review-pr-prose` | Simulated peer review panel for manuscript prose. Spins discipline-specific agents for multi-perspective review. |
| `/reviewers` | Describe live independent review needs and let the active runtime discover and route optional reviewers, preserving findings and integrity evidence. |
| `/route` | Model routing: performance grid, route cache, triage, clusters. The single home for which model serves which work. |
| `/verify-adherence` | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. |

## Research

### Research and bibliography

| Command | Description |
|---------|-------------|
| `/biblio-saturation` | Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness. |
| `/critical-lit-review` | Critical literature review (état de l'art) in history of economics and STS: object, actors, controversies. |
| `/reading-note` | Critical reading note (note de lecture) on one article or book, filed in Zotero. |
| `/related-work-note` | Due-diligence note for one cited paragraph of a manuscript: relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/zotero` | Import PDFs or URLs into Zotero, suggest edits or attachments to existing items, check staged files against the library, or report duplicate files: extract metadata, resolve identifiers, create items with PDFs through the running Zotero's local API. |

### Writing and presentation

| Command | Description |
|---------|-------------|
| `/cut-prose` | Cut a document to a word or page budget by removing whole passages before condensing anything. Use for a manuscript trim, a reviewer-mandated length cut, or a slot-limited abstract. |
| `/external-peer-review` | Obtain independent external frontier-class peer reviews of a manuscript PDF; synthesize convergent findings into one verdict. |
| `/message-framing` | Frame the central message of a talk, abstract or article before drafting it. Not for cutting a text (/cut-prose) or building a deck (/slides). |
| `/pdf-finish` | Finishing pass on a PDF deliverable before it leaves the workshop — journal submission, preprint deposit, personal page, report handoff. Keyword: finition. |
| `/slides` | Make or review a talk's slide deck: build a beamer deck from a written text, or critique an existing deck with prioritized fixes. Keywords: diaporama, présentation. |
| `/track-changes-pdf` | Render a revision-marked PDF of a LaTeX manuscript between two git refs, marking insertions and deletions via latexdiff. Closes the annotate-reply-apply loop of journal revise-and-resubmit rounds. |

### Submission and publication

| Command | Description |
|---------|-------------|
| `/aap-annonce` | Process a call-for-proposals announcement (AAP, appel à projets): file it, calendar deadlines, assess fit, propose three entry angles. |
| `/choose-venue` | Choose where to submit a paper: shortlist journals, or conferences, by fit and diamond open access. |
| `/conference-submission-prep` | Prepare a humanities and social sciences conference submission from its call for papers. Use once venue and message are set; not for those (/choose-venue, /message-framing). |
| `/ingest-decision-letter` | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check mapping every remark to a ticket: one deterministic Revise-and-Resubmit intake pass. |
| `/submission-event` | Classify a manuscript submission event (submitted, resubmitted, accepted, published) by its object's external register; propagate to the homepage publications list (works) or CNRS secretariat roadmap (work in progress), never both automatically. |
| `/update-publist` | Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
