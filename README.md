# Imperial Dragon Harness

Casual people get shit done. Real humans ride the Imperial Dragon Harness.
They `/raid` tickets to bring back PR, they `/hunt` one down to the branch,
they `/perch` to orient midchat.

A personal harness for AI-assisted research across Claude Code, Codex and Pi.
The reference checkout is `~/.agents`; adapters connect each runtime to the
same skills, rules and tools. Portability work is tracked in ticket 0999.

## The Five Claws

Every task passes through five phases:

| Claw | Phase | Activity |
|------|-------|----------|
| 1 | **Imagine** | Explore, brainstorm, surface motivations |
| 2 | **Plan** | Design, write tickets with test specs |
| 3 | **Execute** | TDD red/green/refactor, open PR |
| 4 | **Verify** | Review PR, fix, iterate ≤3 cycles |
| 5 | **Celebrate** | Reflect, consolidate memory, dream forward |

## Structure

```
ImperialDragonHarness/          # reference clone: ~/.agents
├── rules/                  # Doctrine — loaded by the runtime itself, see below
├── skills/                 # Slash commands — auto-generated catalog below
├── scripts/                # Hook implementations, guards, shell init
├── tests/                  # The gates; `make check` runs them
├── tickets/                # git-erg ticket store (`tickets/AGENTS.md`)
├── adapters/               # Native glue for other harnesses (`adapters/README.md`)
├── memory/                 # Shared lessons in the current layout
├── projects/<slug>/memory/ # Per-repo memory, written by /dream and /memory-sweep
├── bin/ hooks/             # PATH utilities, git hooks
├── settings.shared.json    # Tracked config; the live settings.json is git-ignored
└── docs/                   # Reference material (not loaded)
```

See [ROADMAP.md](ROADMAP.md) for priorities and [STATE.md](STATE.md) for the
current resume point.

## Rules

Claude Code reads registered rules from `~/.claude/rules/**.md`. Its
frontmatter controls when they load:

| Frontmatter | Loading | What it costs |
|---|---|---|
| no `paths:` | in the system prompt of **every session, every project** | paid on every conversation |
| `paths: ["**/*.py"]` | only when the session touches a matching file | paid on use |

[rules/README.md](rules/README.md) indexes conditional rules and explains
loading. Each adapter must provide equivalent delivery or document its limits.

Run `make resident-budget` for the current startup-context census. The estimate
uses characters divided by 2.8; tests cap the resident channels. This avoids
keeping stale token totals in the README.

## Installation

Clone into an absent destination:

```bash
git clone https://github.com/MinhHaDuong/ImperialDragonHarness.git ~/.agents
cd ~/.agents
```

If `~/.agents` already exists, inspect it first. Other checkout locations are
supported by the portable registration contract: entry points resolve the
checkout from their real location or an explicit root argument. Dream/memory
helper portability remains separate work (1002); check its storage limitations
before consolidating independently owned runtime memory.

Follow the [installation guide](docs/idh-install-strategy.md) to register
reviewed resources with each runtime. It distinguishes current additive
registration from future native packaging and measured pilot support.

The current `./bin/idh install` creates manifest links, edits the shell loader
and enables an audit timer. It merges harness hooks into Claude/Codex settings
and links individual resources, preserving unrelated profile content. No
repository pointer or whole-profile alias is required. Same-name conflicts
are refused. Review these host-wide actions: there is no dry run or runtime
selector, and shell/timer integration is not opt-in. Tracker 0999 remains
open; 1001 owns registration and 1002 the separate memory-helper work.

For an existing installation:

- `./bin/idh check [RUNTIME]` reports broken manifest entries.
- `./bin/idh status` reports installation and repository state.
- `./bin/idh sync` fast-forwards or names the changes preventing it.

The [operations runbook](docs/adapter-operations.md) covers guard trust,
verification, removal and recovery. The [adapter reference](adapters/README.md)
records the loaded-skill path contract and measured runtime behavior.

## Development

Run checks from the checkout:

```bash
make check-fast       # fast development loop
make lint             # adherence checks
make check            # full gate
make resident-budget  # report startup context cost
```

Development dependencies are listed in `requirements-dev.txt`. Credentials
belong in the external keystore and are resolved by task-specific tools.

## Skills Catalog

<!-- skills:begin -->

| Command | Description |
|---------|-------------|
| `/bib-merge` | Merge approved Bibliography entries from a related-work-note into the project's refs.bib. Dedupes, flags conflicts, appends new entries. Never rewrites existing entries. |
| `/biblio-saturation` | Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness. |
| `/choose-venue` | Choose where to submit a paper: shortlist journals, or conferences, by fit and diamond open access. |
| `/conference-submission-prep` | Prepare a humanities and social sciences conference submission from its call for papers. |
| `/critical-lit-review` | Critical literature review (état de l'art) in history of economics and STS: object, actors, controversies. |
| `/cut-prose` | Cut a document to a word or page budget by removing whole passages before condensing anything. Ranks the removable passages against the coverage ledger, cuts them entire, then condenses the survivors until the budget is met. Use for a manuscript trim, a reviewer-mandated length cut, or a slot-limited abstract. |
| `/dream` | Autonomous nightly memory consolidation for one project. |
| `/external-peer-review` | Obtain independent external frontier-class peer reviews of a manuscript PDF; synthesize convergent findings into one verdict. |
| `/gaze` | Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Does not merge — the merge decision belongs to the caller. |
| `/healthcheck` | Repo healthcheck — git hygiene, test status, and deep freshness verification of status/directive docs. Gracefully degrades when project-specific conventions (git-erg tickets, STATE.md, etc.) are absent. |
| `/hunt` | Begin work on a ticket — creates a worktree and writes the first test. |
| `/index-source` | Import a document from a URL into Zotero: verify metadata and item type, deduplicate, and attach the source file. URL counterpart to zotero-import in the EDM workflow. |
| `/ingest-decision-letter` | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check that maps every remark to a ticket. Turns Revise-and-Resubmit intake into one deterministic pass instead of a manual re-count. |
| `/lair` | End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session. |
| `/memory-sweep` | Write, update, or sweep persistent memory. Enforces list caps, TTLs, and staleness criteria. |
| `/merge` | Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI). |
| `/message-framing` | Frame the central message of a talk, abstract or article before drafting it. |
| `/molt` | Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps. |
| `/pdf-finish` | Finishing pass on a PDF deliverable before it leaves the workshop — journal submission, preprint deposit, personal page, report handoff. Automates pagination through header knobs, verifies the result with a scripted text sweep rather than by eye, and treats each named variant as a reproducible transform layer. Keyword: finition. |
| `/perch` | Mid-session orientation — summarize what's done, surface unresolved points. Assesses clear-readiness and offers to do the work if conditions are right. |
| `/raid` | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |
| `/reading-note` | Critical reading note (note de lecture) on one article or book, filed in Zotero. |
| `/related-work-note` | Author's due-diligence note for one cited paragraph of a manuscript. Covers relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/related-work-note-validate` | Re-resolve every DOI/URL/eprint in a related-work-note's Bibliography. Append a provenance line to Methods. One-line verdict to stdout (PASS / WARN / FAIL). |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/review-pr` | Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation. |
| `/review-pr-prose` | Simulated peer review panel for manuscript prose. Spins discipline-specific agents for multi-perspective review. |
| `/reviewers` | Reviewer-panel management for /gaze — list, request, harvest, scorecard, scores, audition, and help reviewer seats. |
| `/roar` | Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches. |
| `/slides` | Make or review a talk's slide deck: build a beamer deck from a written text, or critique an existing deck with prioritized fixes. Keywords: diaporama, présentation. |
| `/submission-event` | Classify a manuscript submission event — submitted, resubmitted, accepted, published — by which external register its object belongs in, then propagate it to the homepage publications list and/or the CNRS secretariat roadmap. The roadmap tracks work in progress; the publications list tracks works, so never update both automatically. |
| `/trace-doctor` | Monthly survey of Claude Code session-trace economics — cost census, hypothesis statistics, and a ranked cost-saving recommendation report, cross-referenced against tickets. Never auto-applies changes; files tickets for actionable findings. |
| `/track-changes-pdf` | Render a revision-marked PDF of a LaTeX manuscript between two git refs, highlighting insertions and deletions via latexdiff. Closes the annotate-reply-apply loop for journal revise-and-resubmit rounds. |
| `/typography-finish` | Fine typography pass for a rendered text deliverable at finalization, after its wording is frozen. Handles French or English spacing by output format; never applies to drafts. |
| `/update-publist` | Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
| `/verify-adherence` | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. |
| `/verify-gate` | Anti-rubber-stamp merge gate. Validates every ticket exit criterion and every review comment against the actual diff. Emits APPROVED / REROLL / ESCALATE with explicit evidence. Does not merge — the merge decision belongs to the caller. |
| `/zotero-import` | Import one or more PDFs into Zotero, or backfill a whole staging directory — extract metadata, resolve identifiers online, dedupe against the library (desktop database or a cached Web API index), and inject items with their PDFs through the Zotero Web API (RIS file as fallback). |

<!-- skills:end -->

## Ticket management

The preferred ticket system is [git-erg](https://github.com/MinhHaDuong/git-erg), an offline `tickets/` directory that lives inside each project's git repo. Install it per-project following its README. When git-erg is available, use it. Fall back to GitHub issues or any other forge when needed (e.g., for cross-team coordination).

## Runtime support

The reference clone lives at `~/.agents`. The installation strategy uses
native registration to coexist with runtime-owned configuration.
Portability is measured, not presumed: `adapters/` currently has pilot
evidence for two skills (`perch`, `healthcheck`) and one guard across Claude
Code, Codex and Pi. Mistral Vibe has a version and skill-path probe but no
behavioral port yet. See `adapters/pilot-support.json` and
`docs/adapter-operations.md` for the current evidence.
