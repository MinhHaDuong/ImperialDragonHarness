# Imperial Dragon Harness

Casual people get shit done. Real humans ride the Imperial Dragon Harness.
They `/raid` tickets to bring back PR, they `/hunt` one down to the branch,
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
ImperialDragonHarness/          # cloned as ~/.claude
├── rules/                  # Doctrine — loaded by the runtime itself, see below
├── skills/                 # Slash commands — auto-generated catalog below
├── scripts/                # Hook implementations, guards, shell init
├── tests/                  # The gates; `make check` runs them
├── tickets/                # git-erg ticket store (`tickets/AGENTS.md`)
├── memory/                 # Cross-project lessons, injected at session start
├── projects/<slug>/memory/ # Per-repo memory, written by /dream and /memory
├── commands/ bin/ hooks/   # Guidance docs, PATH utilities, git hooks
├── settings.shared.json    # Tracked config; the live settings.json is git-ignored
└── docs/                   # Reference material (not loaded)
```

Directory contents are not enumerated here: `ls` answers that, and a hand-kept
listing drifts — this one claimed five rule files when there were nineteen, and
named one that no longer exists.

## Rules

`~/.claude/rules/**.md` is read by the runtime, not by a hook, and the
frontmatter decides how:

| Frontmatter | Loading | What it costs |
|---|---|---|
| no `paths:` | in the system prompt of **every session, every project** | paid on every conversation |
| `paths: ["**/*.py"]` | only when the session touches a matching file | paid on use |

So a rule needs no description anywhere: an unscoped one is already in front of
the reader, and a scoped one is named in [`rules/README.md`](rules/README.md)
precisely because it is not. That index is one screen, and it is the single
source of truth on when each conditional rule applies.

The resident set costs ~21 600 tokens per session (measured 2026-09-09;
`workflow.md` and `git.md` are two thirds of it). `tests/test_rules_resident_budget.py`
caps it: trimming a body lowers the cap, growing one has to argue for a raise.
A runtime without this auto-load — the Pi and Codex adapters — must inject that
set itself; that is the real work behind tickets 0800 and 0572.

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

3. Install the dev dependencies (PyYAML is needed by `make skills-catalog` and the pre-commit hook, pytest by every `make` test gate):
   ```bash
   pip install --user -r ~/.claude/requirements-dev.txt
   ```
   On a PEP 668 externally-managed Python (Debian 12+, Ubuntu 23.04+), install into a venv or via `pipx` instead.

4. Add one line to your `~/.bashrc` (or `~/.zshrc`) to source the harness shell init:
   ```bash
   [ -f "$HOME/.claude/scripts/shell-init.sh" ] && source "$HOME/.claude/scripts/shell-init.sh"
   ```
   This installs a `claude` wrapper that skips permission prompts and auto-names each session after the current git repo. The script lives in the harness, so it updates on every pull.

Skills are available as `/roar`, `/gaze`, `/molt`, etc. Hooks fire automatically via `settings.json`.

## Skills Catalog

<!-- skills:begin -->

| Command | Description |
|---------|-------------|
| `/bib-merge` | Merge approved Bibliography entries from a related-work-note into the project's refs.bib. Dedupes, flags conflicts, appends new entries. Never rewrites existing entries. |
| `/biblio-saturation` | Saturation bibliographic search by independent web-search subagents — adjudicate factual register lines and adversarially stress a novelty claim until every search angle runs dry. Fleets of finders on disjoint angles (fields, languages, gray literature, citation graph, lateral vocabularies), adversarial judging of every candidate, completeness critic before declaring saturation. |
| `/dream` | Autonomous nightly memory consolidation for one project. |
| `/external-peer-review` | Send a manuscript PDF to external frontier models (OpenAI + Mistral via OpenRouter) for peer review; synthesize convergent findings into one verdict. |
| `/gaze` | Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Does not merge — the merge decision belongs to the caller. |
| `/healthcheck` | Repo healthcheck — git hygiene, test status, and deep freshness verification of status/directive docs. Gracefully degrades when project-specific conventions (git-erg tickets, STATE.md, etc.) are absent. |
| `/hunt` | Begin work on a ticket — creates a worktree and writes the first test. |
| `/index-source` | Index/catalogue a document from a URL into Zotero with the right item type and clean metadata. Fetches the page, stages it locally, scrapes author/date/title/identifiers/pagination from meta tags (JSON-LD, citation_*, Dublin Core, OpenGraph) and DOI/arXiv APIs, classifies the Zotero type with judgment, dedupes, and hands a RIS + attachment to Zotero. URL sibling of zotero-import; implements the EDM workflow (docs/ staging → Zotero). |
| `/ingest-decision-letter` | Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check that maps every remark to a ticket. Turns Revise-and-Resubmit intake into one deterministic pass instead of a manual re-count. |
| `/lair` | End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session. |
| `/memory` | Write, update, or sweep persistent memory. Enforces list caps, TTLs, and staleness criteria. |
| `/merge` | Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI). |
| `/molt` | Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps. |
| `/perch` | Mid-session orientation — summarize what's done, surface unresolved points. Assesses clear-readiness and offers to do the work if conditions are right. |
| `/raid` | Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears. |
| `/related-work-note` | Author's due-diligence note for one cited paragraph of a manuscript. Covers relevance, history, cited works (detailed), related-but-not-cited (justified), methods, verification checklist, bibliography with DOI/URL. |
| `/related-work-note-validate` | Re-resolve every DOI/URL/eprint in a related-work-note's Bibliography. Append a provenance line to Methods. One-line verdict to stdout (PASS / WARN / FAIL). |
| `/release` | Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step. |
| `/review-pr` | Multi-perspective code review with parallel agents. Covers correctness, consistency, scope, red team, and doc propagation. |
| `/review-pr-prose` | Simulated peer review panel for manuscript prose. Spins discipline-specific agents for multi-perspective review. |
| `/reviewers` | Reviewer-panel management for /gaze — list, request, harvest, scorecard, scores, audition, and help reviewer seats. |
| `/roar` | Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches. |
| `/trace-doctor` | Monthly survey of Claude Code session-trace economics — cost census, hypothesis statistics, and a ranked cost-saving recommendation report, cross-referenced against tickets. Never auto-applies changes; files tickets for actionable findings. |
| `/track-changes-pdf` | Render a revision-marked PDF of a LaTeX manuscript between two git refs, highlighting insertions and deletions via latexdiff. Closes the annotate-reply-apply loop for journal revise-and-resubmit rounds. |
| `/update-publist` | Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call. |
| `/verify-adherence` | Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM. |
| `/verify-gate` | Anti-rubber-stamp merge gate. Validates every ticket exit criterion and every review comment against the actual diff. Emits APPROVED / REROLL / ESCALATE with explicit evidence. Does not merge — the merge decision belongs to the caller. |
| `/zotero-import` | Import one or more PDFs into Zotero, or backfill a whole staging directory — extract metadata, resolve identifiers online, dedupe against the library (desktop database or a cached Web API index), and inject items with their PDFs through the Zotero Web API (RIS file as fallback). |

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

Run `/fewer-permission-prompts` to propose an allowlist diff per project. Diffs are never auto-applied; review them at `~/.claude/telemetry/permission-diffs/`. A weekly run and a morning report used to drive this from the nightbeat, removed in ticket 0882 — the proposal is now something you ask for.

## Why not a plugin?

Because it's **my** harness. IDH is my personal Claude config, cloned to `~/.claude` on every machine I use. The plugin system exists for shareable, redistributable tooling — that's not this. Fork the repo if you want your own.
