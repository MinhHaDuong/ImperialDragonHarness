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
├── adapters/               # Native glue for other harnesses (`adapters/README.md`)
├── memory/                 # Cross-project lessons, injected at session start
├── projects/<slug>/memory/ # Per-repo memory, written by /dream and /memory-sweep
├── bin/ hooks/             # PATH utilities, git hooks
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

The auto-loaded rules cost ~12 800 tokens per session, and they are one of five
resident channels: `CLAUDE.md` and its `@` imports, what the SessionStart hook
prints, the project memory index, and the frontmatter card of every skill and
subagent are all in front of the model before the first question too — about
28 000 tokens in all. `make resident-budget` reports the census;
`tests/test_resident_census.py` caps each channel and
`tests/test_rules_resident_budget.py` keeps the rules-specific rules. Trimming
a body lowers a cap, growing one has to argue for a raise.

At startup, a project with local `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`,
or project skills gets a short coherence prompt. The session checks applicable
local directives against harness rules and skill descriptions, then reports
concrete conflicts, repeated procedures, and stale references. Projects with
no local directives get no prompt.

A runtime without this auto-load — the Pi and Codex adapters — must inject that
set itself; that is the real work behind tickets 0800 and 0572.

The figures above are characters divided by 2.8, a ratio derived from
`/context`, not a token measurement: the arithmetic and its provenance are in
`scripts/resident_census.py`. The earlier ~8 800 recorded here came from
dividing by 4, which understated every channel by about 45%.

## Installation

Clone IDH into its own checkout:
```bash
git clone https://github.com/MinhHaDuong/ImperialDragonHarness.git ~/.idh
```

For an existing agent profile, follow the [additive installation strategy](docs/idh-install-strategy.md).
Register reviewed IDH skills through each runtime's native mechanism. Keep
existing `~/.claude`, `~/.agents`, and skills directories in place.

The current `idh install` is legacy all-runtime host setup, not a safe
skills-only install. It has no dry run or runtime selector. It sets up declared
links across runtimes, edits the shell loader, and enables a timer:

- the links: the harness pointer `~/.idh`, the Codex and Pi guard links, the
  shared skills, and `~/.local/bin/idh` itself;
- the loader block `scripts/bashrc-loader.sh`, written into `~/.bashrc`
  between its `>>>` and `<<<` marker lines. The previous file is kept as
  `~/.bashrc.idh-bak-<timestamp>`, and every byte outside the markers is verified
  unchanged. An old block without markers is refused with the manual step;
  zsh users copy the block into `~/.zshrc` by hand;
- the monthly audit timer, when `systemctl` is present.

It never overwrites: a real file or a foreign link where a link belongs is
named, left alone, and makes the run exit non-zero. Rerunning it is safe.
Day to day: `idh check [RUNTIME]` names each broken link with its repair,
`idh status` shows installed vs declared and the distance to origin, and
`idh sync` fast-forwards the checkout or names the files in the way.

Harness wiring (hooks, `BASH_ENV`, shell init, timers, the Codex and Pi
adapters) names the checkout as `~/.idh` (ticket 0982). Paths that are Claude
Code's own native root (`~/.claude/projects/`, `~/.claude/settings.json`) keep
their `~/.claude` spelling. The pointer lets the checkout later leave
`~/.claude` (tracker 0978) without chasing callers. Hooks and skills call
scripts by path, never through `idh`.

The loader sources `scripts/shell-init.sh`, which wraps `claude`, `codex` and `pi`: before each launch, `scripts/validate-projections.py` checks every link declared in `adapters/projections.json` and refuses to start, naming the culprit and its repair, when one is missing, dangling or foreign (ticket 0983). If the checkout itself is unreachable, the loader's stubs refuse instead of letting the runtimes start without their guards. The bypass is explicit and logged: `IDH_SKIP_VALIDATE=1 codex ...` appends to `~/.local/state/idh/validate-bypass.log`. The `claude` wrapper also skips permission prompts and auto-names each session after the current git repo. The wrappers live in the harness, so they update on every pull. They guard interactive shells only: systemd units, scripts and headless callers that exec a runtime by absolute path, through `env`, or from a non-interactive shell bypass them.

Two optional extras:

- API keys in `~/.idh/.env` (gitignored), one `NAME=value` line each, e.g.
  `ANTHROPIC_API_KEY=sk-...`.
- The dev dependencies (PyYAML for `make skills-catalog` and the pre-commit
  hook, pytest for every `make` test gate):
  `pip install --user -r ~/.idh/requirements-dev.txt`. On a PEP 668
  externally-managed Python (Debian 12+, Ubuntu 23.04+), use a venv or `pipx`.

Skills are available as `/roar`, `/gaze`, `/molt`, etc. Hooks fire automatically via `settings.json`.

### Monthly unused-skill audit

`idh install` enables the user timer when `systemctl` is present (first day of
each month, 08:00 local time, with up to five minutes of jitter). Rerun it
after changing the service or timer files: systemd uses installed copies. The
launcher is linked at `~/.local/bin/idh-mammoth-audit`, matching the service's
fixed executable path.

Run `bin/mammoth-audit` for an immediate census. The aggregate report is
`${XDG_STATE_HOME:-~/.local/state}/imperial-dragon-harness/mammoth-audit.json`;
`--output` selects another file. Only local Claude traces are observed. An
unused, unreferenced skill is a review candidate even after a recent edit;
missing traces produce an indeterminate result. References from unused skills
also protect their dependencies, conservatively. Nothing is removed by the audit.

Inspect scheduling with `systemctl --user list-timers idh-mammoth-audit.timer`
and failures with `journalctl --user -u idh-mammoth-audit.service`. Disable the
schedule with `systemctl --user disable --now idh-mammoth-audit.timer`.

## Skills Catalog

<!-- skills:begin -->

| Command | Description |
|---------|-------------|
| `/bib-merge` | Merge approved Bibliography entries from a related-work-note into the project's refs.bib. Dedupes, flags conflicts, appends new entries. Never rewrites existing entries. |
| `/biblio-saturation` | Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness. |
| `/choose-venue` | Choose where to submit a paper: shortlist journals, or conferences, by fit and diamond open access. |
| `/conference-submission-prep` | Prepare a humanities and social sciences conference submission from its call for papers. |
| `/critical-lit-review` | Critical literature review for history of economics and STS: scoping, consultation table, corpus analysis, report. |
| `/cut-prose` | Cut a document to a word or page budget by removing whole passages before condensing anything. Ranks the removable passages against the coverage ledger, cuts them entire, then condenses the survivors until the budget is met. Use for a manuscript trim, a reviewer-mandated length cut, or a slot-limited abstract. |
| `/dream` | Autonomous nightly memory consolidation for one project. |
| `/external-peer-review` | Send a manuscript PDF to external frontier models (OpenAI + Mistral via OpenRouter) for peer review; synthesize convergent findings into one verdict. |
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
| `/reading-note` | Academic reading note (note de lecture) from a DOI or citation, with Zotero RDF export. |
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
ExecStart=/usr/bin/git -C %h/.idh pull --ff-only --quiet
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

## Runtime support

IDH is personal configuration intended for a separate `~/.idh` checkout.
Native plugins and packages allow it to coexist with other configuration. The
[installation strategy](docs/idh-install-strategy.md) uses those mechanisms.
Portability is measured, not presumed: `adapters/` currently has pilot
evidence for two skills (`perch`, `healthcheck`) and one guard across Claude
Code, Codex and Pi. Mistral Vibe has a version and skill-path probe but no
behavioral port yet. See `adapters/pilot-support.json` and
`docs/adapter-operations.md` for the current evidence.
