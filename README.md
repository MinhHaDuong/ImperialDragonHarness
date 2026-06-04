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

Skills are available as `/celebrate`, `/review-pr`, etc. Hooks fire automatically via `settings.json`.

## Skills Catalog

<!-- skills:begin -->

| Command | Description |
|---------|-------------|
| `/beat` | Trigger one beat cycle on the current project (housekeeping → pick-ticket → raid). |
| `/bib-merge` | Merge approved Bibliography entries from a related-work-note into the project's refs.bib. Dedupes, flags conflicts, appends new entries. Never rewrites existing entries. |
| `/celebrate` | Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches. |
| `/check-readiness` | Multi-repo pre-flight readiness check and interactive triage. Surfaces git hygiene, ticket health, configuration drift, and nightbeat risk signals. |
| `/dream` | Autonomous nightly memory consolidation for one project. |
| `/end-session` | End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session. |
| `/healthcheck` | Repo healthcheck — git hygiene, test status, and deep freshness verification of status/directive docs. Gracefully degrades when project-specific conventions (git-erg tickets, STATE.md, etc.) are absent. |
| `/housekeeping` | Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps. |
| `/memory` | Write, update, or sweep persistent memory. Enforces list caps, TTLs, and staleness criteria. |
| `/merge` | Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI). |
| `/nightbeat-report` | Morning review of autonomous nightbeat runs. Parses logs, narrates work done, and surfaces harness improvement opportunities. |
| `/nightbeat-supervisor` | Continuous autonomous supervisor for nightbeat. Watches beat outcomes, merges ready PRs, diagnoses and repairs failures, escalates when stuck. |
| `/perch` | Mid-session orientation — summarize what's done, surface unresolved points. Assesses clear-readiness and offers to do the work if conditions are right. |
| `/pick-ticket` | Pick the lowest-risk available ticket for an autonomous sweep run. Returns PICK:<id>, CLOSED:<id>, or IDLE. |
| `/raid` | Run an Imperial Dragon raid across multiple tickets. Picks targets, manages waves, enforces isolation. Merges APPROVED PRs after verify-gate clears. |
| `/related-work-note` | Author's due-diligence note for one cited paragraph of a manuscript. Covers relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/related-work-note-validate` | Re-resolve every DOI/URL/eprint in a related-work-note's Bibliography. Append a provenance line to Methods. One-line verdict to stdout (PASS / WARN / FAIL). |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/review-pr` | Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation. |
| `/review-pr-prose` | Simulated peer review panel for manuscript prose. Spins discipline-specific agents for multi-perspective review. |
| `/reviewers` | "Reviewer-management helper skill — list, request, harvest, scorecard" |
| `/skill-doctor` | Weekly failure-pattern analysis across journals, logs, and git history. Clusters recurring failures and opens tickets with proposed patches. Never auto-applies fixes. |
| `/smoke` | Agent environment smoke test — reports runtime identity, auth method, and harness context. |
| `/start-ticket` | Begin work on a ticket. Creates worktree, writes first test, transitions to Execute phase. |
| `/ticket-new` | Create a local %erg 0.1 file for agent coordination. |
| `/verify` | Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Never merges. |
| `/verify-adherence` | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. Emits suggested tests for any semantic finding so the LLM surface shrinks over time. |
| `/verify-gate` | Anti-rubber-stamp merge gate. Validates every ticket exit criterion and every review comment against the actual diff. Emits APPROVED / REROLL / ESCALATE with explicit evidence. Never merges. |
| `/zotero-import` | Import one or more PDFs into Zotero. Extracts metadata from the document, resolves identifiers online when available, checks for duplicates in the local Zotero library, writes a combined RIS file, and hands it to xdg-open so the user's environment decides what to do with it. |

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
