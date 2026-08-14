# Imperial Dragon Harness

Casual people get shit done. Real humans ride the Imperial Dragon Harness.
They `/raid` tickets to bring back PR, they `/beat` their wings autonomously,
they `/perch` to orient midchat.

A Claude Code harness for Minh Ha-Duong's research workflow. Lives as `~/.claude`.

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
ImperialDragonHarness/
├── rules/                  # Rule index (README.md) injected at SessionStart; bodies read on demand
│   ├── README.md           # One-screen index: filename, scope, summary
│   ├── workflow.md         # Session start, escalation, worktree
│   ├── git.md              # Branch, commit, PR discipline
│   ├── coding-python.md    # Python style, testing, Make (load when Python project)
│   ├── state.md            # STATE.md format spec
│   └── tickets.md          # Ticket log verbs including bump categories
├── skills/                 # Slash commands — auto-generated catalog below
├── scripts/                # Hook implementations + shell init
│   ├── shell-init.sh           # Source from ~/.bashrc — claude wrapper
│   ├── on-start.sh             # Session start: env loading, worktree gate
│   ├── guard-destructive-bash.sh
│   ├── guard-commit-on-main.sh
│   ├── block-pr-merge-in-worktree.sh
│   ├── lint-on-edit.sh
│   ├── warn-stale-rules.sh
│   └── gen-skills-catalog.sh   # Generate skills catalog from SKILL.md frontmatter
├── commands/               # Guidance documents
│   └── choose-journal.md
├── bin/                    # Utilities (added to PATH)
│   ├── usage-report
│   ├── snapshot
│   └── install-cron
├── settings.json           # Hooks, permissions, env vars
└── docs/                   # Reference material (not loaded)
```

## Installation

1. Clone the repo as your `~/.claude` directory:
   ```bash
   git clone https://github.com/MinhHaDuong/ImperialDragonHarness.git ~/.claude
   ```

2. Create `~/.claude/.env` with your API keys (this file is gitignored):
   ```
   ANTHROPIC_API_KEY=sk-...
   OPENAI_API_KEY=sk-...
   ```

3. Add one line to your `~/.bashrc` (or `~/.zshrc`) to source the harness shell init:
   ```bash
   [ -f "$HOME/.claude/scripts/shell-init.sh" ] && source "$HOME/.claude/scripts/shell-init.sh"
   ```
   This installs a `claude` wrapper that skips permission prompts and auto-names each session after the current git repo. The script lives in the harness, so it updates on every pull.

Skills are available as `/roar`, `/gaze`, `/molt`, etc. Hooks fire automatically via `settings.json`.

## Skills Catalog

<!-- skills:begin -->

| Command | Description |
|---------|-------------|
| `/beat` | Run one autonomous work cycle on the current project — housekeeping, then pick a ticket, then execute it (housekeeping → pick-ticket → raid). |
| `/bib-merge` | Merge approved Bibliography entries from a related-work-note into the project's refs.bib. Dedupes, flags conflicts, appends new entries. Never rewrites existing entries. |
| `/biblio-saturation` | Saturation bibliographic search by independent web-search subagents — adjudicate factual register lines and adversarially stress a novelty claim until every search angle runs dry. Fleets of finders on disjoint angles (fields, languages, gray literature, citation graph, lateral vocabularies), adversarial judging of every candidate, completeness critic before declaring saturation. |
| `/celebrate` | Deprecated — renamed to /roar. Warns, then delegates to the new name. |
| `/check-readiness` | Alias of /scry — multi-repo pre-flight readiness check and interactive triage. |
| `/dream` | Autonomous nightly memory consolidation for one project. |
| `/end-session` | Deprecated — renamed to /lair. Warns, then delegates to the new name. |
| `/external-peer-review` | Send a manuscript PDF to external frontier models (OpenAI + Mistral via OpenRouter) for peer review; synthesize convergent findings into one verdict. |
| `/gaze` | Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Does not merge — the merge decision belongs to the caller. |
| `/healthcheck` | Repo healthcheck — git hygiene, test status, and deep freshness verification of status/directive docs. Gracefully degrades when project-specific conventions (git-erg tickets, STATE.md, etc.) are absent. |
| `/housekeeping` | Alias of /molt — repo housekeeping with git sync, healthcheck, and eager fix-now repairs. |
| `/hunt` | Begin work on a ticket — creates a worktree and writes the first test. |
| `/index-source` | Index/catalogue a document from a URL into Zotero with the right item type and clean metadata. Fetches the page, stages it locally, scrapes author/date/title/identifiers/pagination from meta tags (JSON-LD, citation_*, Dublin Core, OpenGraph) and DOI/arXiv APIs, classifies the Zotero type with judgment, dedupes, and hands a RIS + attachment to Zotero. URL sibling of zotero-import; implements the EDM workflow (docs/ staging → Zotero). |
| `/ingest-decision-letter` | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check that maps every remark to a ticket. Turns Revise-and-Resubmit intake into one deterministic pass instead of a manual re-count. |
| `/lair` | End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session. |
| `/maw-audit` | Mutation-testing audit of test-suite quality — verifies each test detects defects, tolerates safe refactors, and guards the whole defect class. EXPENSIVE — invoke deliberately. Auto-discovers config. |
| `/memory` | Write, update, or sweep persistent memory. Enforces list caps, TTLs, and staleness criteria. |
| `/merge` | Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI). |
| `/molt` | Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps. |
| `/nightbeat-report` | Review what the overnight autonomous pipeline (nightbeat) did each morning: parse logs, narrate work done, surface harness improvement opportunities. |
| `/nightbeat-supervisor` | Supervise an overnight autonomous work run: keep the authorized ticket queue moving, integrate verified work, diagnose and repair failures, and deliver a self-contained morning report. |
| `/perch` | Mid-session orientation — summarize what's done, surface unresolved points. Assesses clear-readiness and offers to do the work if conditions are right. |
| `/pick-ticket` | Pick the lowest-risk available ticket for an autonomous run. |
| `/raid` | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |
| `/related-work-note` | Author's due-diligence note for one cited paragraph of a manuscript. Covers relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/related-work-note-validate` | Re-resolve every DOI/URL/eprint in a related-work-note's Bibliography. Append a provenance line to Methods. One-line verdict to stdout (PASS / WARN / FAIL). |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/review-pr` | Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation. |
| `/review-pr-prose` | Simulated peer review panel for manuscript prose. Spins discipline-specific agents for multi-perspective review. |
| `/reviewers` | Reviewer-panel management for /gaze — list, request, harvest, scorecard, scores, audition, and help reviewer seats. |
| `/roar` | Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches. |
| `/scry` | Multi-repo pre-flight readiness check and interactive triage. Surfaces git hygiene, ticket health, configuration drift, and nightbeat risk signals. |
| `/skill-doctor` | Weekly failure-pattern analysis across journals, logs, and git history. Clusters recurring failures and opens tickets with proposed patches. Never auto-applies fixes. |
| `/smoke` | Agent environment smoke test — reports runtime identity, auth method, and harness context. |
| `/test-audit-llm` | Read-and-judge audit of test quality across four lenses: faithfulness, intent legibility, negative-space coverage, change-detector smell. Runs nothing — advisory only; findings feed ticket creation. |
| `/trace-doctor` | Monthly survey of Claude Code session-trace economics — cost census, hypothesis statistics, and a ranked cost-saving recommendation report, cross-referenced against tickets. Never auto-applies changes; files tickets for actionable findings. |
| `/track-changes-pdf` | Render a revision-marked PDF of a LaTeX manuscript between two git refs, highlighting insertions and deletions via latexdiff. Closes the annotate-reply-apply loop for journal revise-and-resubmit rounds. |
| `/update-publist` | Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
| `/verify` | Deprecated — renamed to /gaze. Warns, then delegates to the new name. |
| `/verify-adherence` | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. |
| `/verify-gate` | Anti-rubber-stamp merge gate. Validates every ticket exit criterion and every review comment against the actual diff. Emits APPROVED / REROLL / ESCALATE with explicit evidence. Does not merge — the merge decision belongs to the caller. |
| `/zotero-import` | Import one or more PDFs into Zotero — extract metadata, resolve identifiers online, dedupe against the local library, and inject items with their PDFs through the Zotero Web API (RIS file as fallback). |

<!-- skills:end -->

## Ticket management

The preferred ticket system is [git-erg](https://github.com/MinhHaDuong/git-erg), an offline `tickets/` directory that lives inside each project's git repo. Install it per-project following its README. When git-erg is available, use it. Fall back to GitHub issues or any other forge when needed (e.g., for cross-team coordination).

### Optional: daily auto-update via systemd

To keep the harness up to date without a network hit on every session start:

```bash
# Create the service and timer
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/claude-harness-pull.service << 'EOF'
[Unit]
Description=Pull ImperialDragonHarness updates

[Service]
Type=oneshot
ExecStart=/usr/bin/git -C %h/.claude pull --ff-only --quiet
EOF

cat > ~/.config/systemd/user/claude-harness-pull.timer << 'EOF'
[Unit]
Description=Daily pull of ImperialDragonHarness

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now claude-harness-pull.timer
```

## Permissions

The nightbeat folds in a weekly run of `/fewer-permission-prompts` (Sundays) that proposes an allowlist diff per project. Diffs are never auto-applied; review them at `~/.claude/telemetry/permission-diffs/` — `nightbeat-report` surfaces unreviewed entries each morning.

## Why not a plugin?

Because it's **my** harness. IDH is my personal Claude config, cloned to `~/.claude` on every machine I use. The plugin system exists for shareable, redistributable tooling — that's not this. Fork the repo if you want your own.
