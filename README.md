# Imperial Dragon Harness

A personal harness for AI-assisted research integrity, excellence and openness.
Why a dragon, and why a harness: [AI is a dragon](https://realf.hypotheses.org/2).

Casual people get shit done. Real humans ride the Imperial Dragon Harness.
They `/yawn` at dawn, `/hunt` one ticket or `/raid` many in autonomous waves,
`/perch` to orient, `/roar` to celebrate and `/lair` at dusk.

**Browse the commands: [skills-catalog.md](skills-catalog.md).**

## Design case

- **Research.** The harness is specialized for academic research: Zotero library management, literature
  reviews, manuscripts, reviewer responses, slides and bibliographies, next to
  the code that supports them. Its author, [Minh Ha-Duong](https://minh.haduong.com),
  is a CNRS senior researcher in environment and development at
  [CIRED](https://www.centre-cired.fr/).
- **Linux first.** The harness targets Linux (systemd, `/proc`, GNU coreutils,
  `flock`, XDG paths). Some code paths will not work on macOS, Windows or
  WSL2, and we accept that. What to install, required and optional, is in
  [INSTALL.md § Dependencies](INSTALL.md#dependencies); the committed platform
  assumptions are in [§ Platform contract](INSTALL.md#platform-contract).
- **Forge optional, forge independent.** Everything works in a local
  repository with no remote. Issues live in `tickets/`
  ([git-erg](https://github.com/MinhHaDuong/git-erg)); review comments and
  verdicts live in git notes (`refs/notes/review`), and merge-gate records in
  `refs/notes/gate`. A forge, when present, is a transport and a merge
  button, not a store of record. A hardcoded dependency on GitHub is a bug:
  forge calls go through one adapter (`scripts/forge.py`).
- **Runtime and model independence.** This sentence was added using the
  Imperial Dragon Harness on Pi by Qwen 3.8 flash next, everything running
  locally on the author's workstation.

## The Five Claws

Every task passes through five phases:

1. Imagine   : Explore, brainstorm, surface motivations
2. Plan      : Design, write tickets with exit criteria and test specs
3. Execute   : TDD red/green/refactor, open PR
4. Verify    : Review PR, fix findings, validate exit criteria
5. Celebrate : Integrate, reflect, consolidate memory, look ahead

## Workflows

Each skill's `SKILL.md` is its procedure; `conception/` keeps the design
history behind it.

- **Day cycle**: `/yawn` (healthcheck) → `/molt` (housekeeping) → work → `/perch` (orient) → work → `/lair`
  (wrap-up: housekeeping, tests, STATE, suggestions).
- **Ticket loop**: `/hunt N` → `/merge` → `/roar`. Hunt works one ticket in
  its own worktree and branch, reviewed by `/gaze` and `/verify-gate`; merge
  lands it behind the merge gate. With an `origin` remote the forge merges
  the PR; without one the merge is local
  ([flows ruling](conception/2026-10-27-review-merge-flows.md)).
- **Autonomous work**: `/raid` picks several tickets and runs them in waves,
  merging as the gate approves, unattended for hours, asking an advisor model
  for decisions.
- **Research**: Skills and scripts to assist the complete ([research workflow](conception/research-workflow.md)),
  according to procedures described my book ([Research Excellence à la française](http://minh.haduong.com/realf.html)).

## Components

A harness has eight components. Here is where each one lives.

### 1. System prompt

`AGENTS.md` and the resident rules in `rules/` (`workflow.md`, `git.md`,
`guards.md`, plus `claude-code.md` for that runtime) are delivered into every
session. Scoped rules (`rules/prose/`, `rules/lang/`, `rules/doctype/`) load
only when a matching file is touched. [rules/README.md](rules/README.md)
explains the layout.

### 2. Guardrails

- `rules/guards.md`: guards for every agent role (no credentials in chat,
  skill loads are not write authorization, context ceiling).
- A destructive-command guard on every shell call (Claude Code `PreToolUse`,
  Codex hook, Pi extension): it refuses `git reset --hard` over uncommitted
  tracked changes, and a `pgrep -f`/`pkill -f` without `-A`, which would match
  or kill the calling shell.
- The main-update guard (`hooks/reference-transaction`): local `main` moves
  only to `origin/main` or onto a merge carrying a passing gate record.
- The merge gate (`.merge-gate.json`, `scripts/merge-gate.py`): checks run on
  the exact head, recorded in `refs/notes/gate`; the full suite runs again
  after merge.
- The tests (`make check`), which also lint the skills and rules.

### 3. Memory

> **Being reworked (2026-10-29).** The fifth consolidation was closed
> unmerged because topics had become accumulated incident logs. The redesign
> is ticketed: fixed departments with a 4 KB cap per page, the journal kept
> intact as the source with the pages as guides to it, and the runtimes'
> native memories (Claude Code, Codex) drained as inboxes. `/hoard` becomes
> `/smelt`, and a trial measures whether memory helps. See tickets 1346–1352
> and [the audit](conception/2026-10-29-memory-system-audit.md). Until then,
> the description below is the current mechanism.

Memory is layered, from raw to distilled. Project memory is written in each
project's own repository; the harness's memory is its own (`memory/`).

1. **Transcripts**: session logs written automatically by each runtime. Raw,
   never edited; read by surveys such as `/trace-doctor`.
2. **Events**: one Markdown file per significant fact in
   `memory/journal/YYYY/`, captured by `/roar`. Append-only. An entry not
   cleared for the repository's public audience is committed as age
   ciphertext, never as plaintext; what that needs (`age` and an `origin`
   remote; the key is created on first use) is in
   [INSTALL.md § Dependencies](INSTALL.md#dependencies).
3. **Topics**: consolidated Markdown files in `memory/topics/`. Their index,
   `memory/MEMORY.md`, is not injected: `AGENTS.md` asks each session to
   read it at task start, and subagents are pointed to it per section 7. `/hoard` turns
   events into topics; it runs on demand, and `/lair` suggests it when five
   or more events are not yet covered.
4. **Crystallisation**: `/brood` proposes improvements to rules and skills
   from accepted hoard findings, on explicit request only.

### 4. Skills

`skills/<name>/SKILL.md`, one directory per slash command, in portable
Markdown. **[skills-catalog.md](skills-catalog.md)** lists them all by
category; it is generated from the skills' frontmatter (`make
skills-catalog`). `bin/idh install skill <name>` registers a skill with
Claude Code, Codex and Pi.

### 5. Tool guidance

How agents should use the tools around them: [RTK.md](RTK.md) (the
token-saving command proxy), [tickets/AGENTS.md](tickets/AGENTS.md) (erg),
`rules/zotero.md` (the bibliography), `rules/coding-bash.md`,
`rules/coding-python.md` and `rules/make.md`.

### 6. Scripts

Deterministic helpers the skills call, so judgment stays with the model and
mechanics stay testable: `scripts/` (gate, forge adapter, review notes,
worktree GC, reports), `bin/` (the `idh` installer and utilities), and the
`Makefile` targets.

### 7. Subagents

The session runs in N+2 mode: the author talks with an orchestrator, which
delegates to team leads (`agents/team-lead.md`), which manage workers:
`coder`, `code-reviewer`, `gate-seat`, `prose-reviewer` (`agents/`, with
their contracts in `profiles/`). `/route` assigns each task a model from
benchmark evidence. The benchmarks come from **Arena**, an independent
repository ([integration contract](conception/arena-integration.md)).

Subagents start without the session's memory. Each worker profile tells its
worker to read the project's `memory/MEMORY.md` index at task start, and a
brief names the topics relevant to its task as paths (memory layer 3). Plain
text in profiles and rules, so Claude Code, Codex and Pi get it alike.

### 8. Middleware plugin

`adapters/claude-code/` packages the hooks as a Claude Code plugin:
`SessionStart` (start context, local main sync), `SessionEnd` (scratch
cleanup) and `PreToolUse` (destructive-command guard, RTK rewrite). Codex and
Pi are launched through wrappers in `scripts/shell-init.sh`;
[adapters/README.md](adapters/README.md) covers what each runtime supports.

## Repository layout

```
ImperialDragonHarness/      # reference clone: ~/.agents
├── AGENTS.md  rules/       # System prompt and guardrails
├── memory/                 # The harness's own memory (journal, topics, hoards)
├── skills/                 # Slash commands — see skills-catalog.md
├── RTK.md                  # Tool guidance (with tickets/AGENTS.md, rules/)
├── scripts/  bin/          # Deterministic helpers, installer
├── agents/  profiles/      # Subagent definitions and contracts
├── adapters/  hooks/       # Runtime plugin, git hooks
├── tests/                  # The gates; `make check` runs them
├── tickets/                # git-erg ticket store
├── projects/<slug>/memory/ # Legacy project memories; migration tracked per project
├── settings.shared.json    # Tracked config; the live settings.json is git-ignored
├── conception/             # Design history: memos, audits, reviews (not loaded)
└── docs/                   # Staging for external documents, git-ignored (Zotero is the record)
```

- [STATE.md](STATE.md): current resume point.
- [ROADMAP.md](ROADMAP.md): development priorities.
- [INSTALL.md](INSTALL.md): setup, platform contract, runtime support.
- [CONTRIBUTING.md](CONTRIBUTING.md): development setup, checks and ticket workflow.
