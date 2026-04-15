# Imperial Dragon Harness

A Claude Code plugin for Minh Ha-Duong's research workflow.

Install with `claude --plugin-dir /path/to/ImperialDragonHarness` or via a plugin marketplace.

## The Five Claws

Every task passes through five phases:

| Claw | Phase | Activity |
|------|-------|----------|
| 1 | **Imagine** | Explore, brainstorm, surface motivations |
| 2 | **Plan** | Design, write tickets with test specs |
| 3 | **Execute** | TDD red/green/refactor, open PR |
| 4 | **Verify** | Review PR, fix, iterate ≤3 cycles |
| 5 | **Celebrate** | Reflect, consolidate memory, dream forward |

## Plugin structure

```
ImperialDragonHarness/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest (name, version, author)
├── skills/                 # Slash commands: /idh:<skill>
│   ├── harness-rules/      # Auto-invoked rules (companion .md files)
│   │   ├── SKILL.md
│   │   ├── workflow.md         # Session start, escalation, worktree
│   │   ├── git.md              # Branch, commit, PR discipline
│   │   ├── coding.md           # Python style, testing, Make
│   │   └── state.md            # STATE.md format spec
│   ├── new-ticket/         # GitHub issue template
│   ├── start-ticket/       # Begin work on issue (TDD)
│   ├── review-pr/          # Multi-agent code review
│   ├── review-pr-prose/    # Peer review panel for prose
│   ├── celebrate/          # Post-task wrap-up
│   ├── end-session/        # Day wrap-up
│   ├── memory/             # Persistent memory management
│   └── autonomous/         # Unsupervised exploration session
├── hooks/
│   └── hooks.json          # Lifecycle event handlers
├── scripts/                # Hook implementations
│   ├── on-start.sh             # Session start: identity, env, hooks
│   ├── guard-destructive-bash.sh
│   ├── guard-commit-on-main.sh
│   ├── block-pr-merge-in-worktree.sh
│   ├── lint-on-edit.sh
│   ├── check-tests-on-stop.sh
│   └── warn-stale-rules.sh
├── commands/               # Guidance documents
│   ├── choose-journal.md
│   └── gsd/                    # 33 research workflow commands
├── bin/                    # Utilities (added to PATH)
│   ├── usage-report
│   ├── snapshot
│   └── install-cron
├── settings.json           # Default settings when plugin enabled
└── docs/                   # Reference material (not loaded)
```

## Installation

Load the plugin with:

```bash
claude --plugin-dir ./ImperialDragonHarness
```

Skills are namespaced as `/idh:<skill>`. Hooks fire automatically via `hooks/hooks.json`. Rules are delivered as companion files in the auto-invoked `harness-rules` skill.

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

## Backed by

https://github.com/MinhHaDuong/ImperialDragonHarness
