# Skills catalog

<!-- Generated from skills/*/SKILL.md; run make skills-catalog. -->

## Generalist

### Build and ship

| Command | Description |
|---------|-------------|
| `/gaze` | Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Does not merge — the merge decision belongs to the caller. |
| `/hunt` | Begin work on a ticket — creates a worktree and writes the first test. |
| `/merge` | Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI). |
| `/raid` | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |
| `/verify-gate` | Anti-rubber-stamp merge gate: checks every ticket exit criterion and review comment against the diff. Emits APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR with evidence. Does not merge. |

### Session and maintenance

| Command | Description |
|---------|-------------|
| `/dashboard` | Ticket dashboard: open tickets, branches and merge requests; full state plus a delta led by the ticket count. |
| `/lair` | End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session. |
| `/molt` | Repo housekeeping — git sync, yawn, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps. |
| `/perch` | Mid-session orientation — summarize what's done, surface unresolved points. Assesses clear-readiness and offers to do the work if conditions are right. |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/roar` | Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches. |
| `/yawn` | Repo healthcheck — git hygiene, test status, and deep freshness verification of status/directive docs. Gracefully degrades when project-specific conventions (git-erg tickets, STATE.md, etc.) are absent. |

### Memory and learning

| Command | Description |
|---------|-------------|
| `/brood` | Turn accepted Hoard findings into project improvements and scoped harness nominations, on explicit request. |
| `/coaching` | Replay the frozen, already merged PR benchmark board through a contained reviewer seat and report read-only ground-truth diagnostics. |
| `/hoard` | Consolidate one project's repository memory without proposing rules. |
| `/memory-sweep` | Review a project's repository memory for stale or contradictory claims. |
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
| `/bib-merge` | Merge approved Bibliography entries from a related-work-note into the project's refs.bib. Dedupes, flags conflicts, appends new entries. Never rewrites existing entries. |
| `/biblio-saturation` | Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness. |
| `/critical-lit-review` | Critical literature review (état de l'art) in history of economics and STS: object, actors, controversies. |
| `/reading-note` | Critical reading note (note de lecture) on one article or book, filed in Zotero. |
| `/related-work-note` | Due-diligence note for one cited paragraph of a manuscript: relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/related-work-note-validate` | Re-resolve every DOI/URL/eprint in a related-work-note's Bibliography. Append a provenance line to Methods. One-line verdict to stdout (PASS / WARN / FAIL). |
| `/zotero` | Import PDFs or URLs into Zotero, suggest edits or attachments to existing items, check staged files against the library, or report duplicate files: extract metadata, resolve identifiers, create items with PDFs through the running Zotero's local API. |

### Writing and presentation

| Command | Description |
|---------|-------------|
| `/cut-prose` | Cut a document to a word or page budget by removing whole passages before condensing anything. Use for a manuscript trim, a reviewer-mandated length cut, or a slot-limited abstract. |
| `/external-peer-review` | Obtain independent external frontier-class peer reviews of a manuscript PDF; synthesize convergent findings into one verdict. |
| `/message-framing` | Frame the central message of a talk, abstract or article before drafting it. |
| `/pdf-finish` | Finishing pass on a PDF deliverable before it leaves the workshop — journal submission, preprint deposit, personal page, report handoff. Keyword: finition. |
| `/slides` | Make or review a talk's slide deck: build a beamer deck from a written text, or critique an existing deck with prioritized fixes. Keywords: diaporama, présentation. |
| `/track-changes-pdf` | Render a revision-marked PDF of a LaTeX manuscript between two git refs, marking insertions and deletions via latexdiff. Closes the annotate-reply-apply loop of journal revise-and-resubmit rounds. |
| `/typography-finish` | Fine typography pass for a rendered text deliverable at finalization, after its wording is frozen. Handles French or English spacing by output format; never applies to drafts. |

### Submission and publication

| Command | Description |
|---------|-------------|
| `/aap-annonce` | Process a call-for-proposals announcement (AAP, appel à projets): file it, calendar deadlines, assess fit, propose three entry angles. |
| `/choose-venue` | Choose where to submit a paper: shortlist journals, or conferences, by fit and diamond open access. |
| `/conference-submission-prep` | Prepare a humanities and social sciences conference submission from its call for papers. |
| `/ingest-decision-letter` | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check mapping every remark to a ticket: one deterministic Revise-and-Resubmit intake pass. |
| `/submission-event` | Classify a manuscript submission event (submitted, resubmitted, accepted, published) by its object's external register; propagate to the homepage publications list (works) or CNRS secretariat roadmap (work in progress), never both automatically. |
| `/update-publist` | Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
