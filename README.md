# Imperial Dragon Harness

A personal harness for AI-assisted research across Claude Code, Codex and Pi.

Casual people get shit done. Real humans ride the Imperial Dragon Harness.
They `/yawn` at dawn, `/hunt` one ticket or `/raid` many in autonomous waves,
`/perch` to orient, `/roar` to celebrate and `/lair` at dusk.

## The Five Claws

Every task passes through five phases:

1. Imagine   : Explore, brainstorm, surface motivations
2. Plan      : Design, write tickets with exit criteria and test specs
3. Execute   : TDD red/green/refactor, open PR
4. Verify    : Review PR, fix findings, validate exit criteria
5. Celebrate : Integrate, reflect, consolidate memory, look ahead

## Structure

```
ImperialDragonHarness/      # reference clone: ~/.agents
├── rules/                  # Doctrine — delivered by runtime adapters
├── skills/                 # Slash commands — see skills-catalog.md
├── scripts/                # Hook implementations, guards, shell init
├── tests/                  # The gates; `make check` runs them
├── tickets/                # git-erg ticket store (`tickets/AGENTS.md`)
├── adapters/               # Native glue for other harnesses (`adapters/README.md`)
├── memory/                 # The harness's own v8 memory (journal, topics, hoards)
├── projects/<slug>/memory/ # Legacy project memories; migration tracked per project
├── bin/ hooks/             # PATH utilities, git hooks
├── settings.shared.json    # Tracked config; the live settings.json is git-ignored
└── docs/                   # Reference material (not loaded)
```

- [ROADMAP.md](ROADMAP.md) : development priorities.
- [STATE.md](STATE.md) : current resume point.
- [skills-catalog.md](skills-catalog.md) : for humans browsing, runtimes discover registered skills directly.
- [Research workflow](docs/research-workflow.md) : choose the skills for literature, manuscript review, author decisions and PDF delivery.
- [INSTALL.md](INSTALL.md) : setup, maintenance commands and runtime support.
- [CONTRIBUTING.md](CONTRIBUTING.md) : development setup, checks and ticket workflow.

## Memory

Project memory is written in each project’s own repository, the harness's memory are its own.

1. Roar captures facts and experiences.
2. Hoard consolidates them in topics.
3. Brood crystallises in rules and skills.

Issues are tracked in the `tickets/` folder using the [git-erg](https://github.com/MinhHaDuong/git-erg) portable, forge-independent system.

## Model routing

To enable long-running tasks, IDH starts in N+2 mode:

- User talks with a general orchestrator agent.
- MOE spawns team-lead orchestrators.
- Team leads manage coder/reviewer workers.

The harness uses `/route` to assign each task to a model based on benchmark evidence.

## Benchmarking arena

Benchmarks are produced by **Arena**, an independent repository, owning the protocol, tournament runner, analysis and reports.
See the [Arena integration contract](docs/arena-integration.md) for the repository location, report paths and evidence-refresh procedure.
Benchmark coverage and provisional results remain explicit when routing is updated.
