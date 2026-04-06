# Plugin Architecture Feasibility: Imperial Dragon Harness

## Verdict: Yes, with one structural caveat

The harness maps cleanly onto the official Claude Code plugin system. Every
component has a direct equivalent. The one caveat is **rules/** — the official
plugin spec has no `rules/` directory. Rules must stay in `~/.claude/rules/`
or project `.claude/rules/`, outside the plugin.

## Official plugin spec (April 2026)

Source: [code.claude.com/docs/en/plugins-reference](https://code.claude.com/docs/en/plugins-reference)

Claude Code ships a built-in plugin system with:
- CLI: `claude plugin install|uninstall|enable|disable|update`
- In-session: `/plugin` command, `/reload-plugins`
- Loading: `claude --plugin-dir ./path` for development
- Distribution: marketplace repos, official Anthropic marketplace
- Namespaced skills: `/imperial-dragon:review-pr`

## Component mapping

| Harness component | Plugin equivalent | Notes |
|---|---|---|
| `skills/*/SKILL.md` | `skills/*/SKILL.md` | Identical format. Namespaced as `/imperial-dragon:skill-name` |
| `hooks/*.sh` | `scripts/*.sh` + `hooks/hooks.json` | Hooks declared in JSON, scripts use `${CLAUDE_PLUGIN_ROOT}` |
| `rules/*.md` | **No equivalent** | Must stay in `~/.claude/rules/`. See caveat below |
| `commands/*.md` | `commands/*.md` | Identical. Legacy but supported |
| `commands/gsd/*.md` | `commands/gsd/*.md` | Same |
| `bin/*` | `bin/*` | Official: added to Bash PATH when plugin enabled |
| `settings.json` | `settings.json` at plugin root | Only `agent` key currently supported by plugins |
| `docs/*` | Stays as documentation, not loaded | Same |

## Plugin directory layout

```
imperial-dragon/
├── .claude-plugin/
│   └── plugin.json           # name, version, description, author
├── skills/                   # 8 skills, identical SKILL.md format
│   ├── new-ticket/SKILL.md
│   ├── start-ticket/SKILL.md
│   ├── review-pr/SKILL.md
│   ├── review-pr-prose/SKILL.md
│   ├── celebrate/
│   │   ├── SKILL.md
│   │   └── log-celebration   # companion script
│   ├── end-session/
│   │   ├── SKILL.md
│   │   └── log-agent-metrics
│   ├── memory/SKILL.md
│   └── autonomous/SKILL.md
├── commands/                 # guidance documents
│   ├── choose-journal.md
│   └── gsd/                  # 33 research workflow commands
├── hooks/
│   └── hooks.json            # declares all hook events + matchers
├── scripts/                  # hook implementations
│   ├── on-start.sh
│   ├── guard-destructive-bash.sh
│   ├── guard-commit-on-main.sh
│   ├── block-pr-merge-in-worktree.sh
│   ├── lint-on-edit.sh
│   ├── check-tests-on-stop.sh
│   └── warn-stale-rules.sh
├── bin/                      # utilities on PATH
│   ├── usage-report
│   ├── snapshot
│   └── install-cron
└── docs/                     # not loaded by plugin system
```

## The rules/ caveat

The official plugin system does **not** support bundling rules. Rules are
loaded from:
- `~/.claude/rules/*.md` (user scope)
- `.claude/rules/*.md` (project scope)
- Managed policy locations

### Workaround options

1. **SessionStart hook** — print rules content to stdout; Claude sees it as
   session context. Lightweight, no file management needed.
2. **Companion install script** — `bin/install-rules` symlinks rule files
   into `~/.claude/rules/`. Run once after plugin install.
3. **CLAUDE.md import** — use `@path/to/file` imports in CLAUDE.md to
   reference rule files inside the plugin directory (if path is stable).
4. **Accept the split** — keep rules in `~/.claude/rules/` as user config,
   treat the plugin as providing skills/hooks/commands only.

**Recommendation**: Option 4 (accept the split). Rules are personal
behavioral constraints that should be version-controlled separately from
distributable tooling. The harness already separates "how I want Claude to
behave" (rules) from "what Claude can do" (skills/hooks). A plugin is the
right vehicle for the latter.

## Migration effort

| Task | Size | Notes |
|---|---|---|
| Create `.claude-plugin/plugin.json` | Trivial | Just metadata |
| Move `hooks/*.sh` to `scripts/` | Trivial | Rename directory |
| Create `hooks/hooks.json` | Small | Translate settings.json hooks format |
| Update hook paths to use `${CLAUDE_PLUGIN_ROOT}` | Small | Search-replace |
| Test with `claude --plugin-dir` | Small | Verify all components load |
| Namespace skill invocations in docs | Small | `/review-pr` becomes `/imperial-dragon:review-pr` |
| Keep rules in `~/.claude/rules/` | Zero | Already there |

**Total**: ~2 hours of mechanical work. No design changes needed.

## What we gain

- **`claude plugin install`** — standard install, no custom scripts
- **`/reload-plugins`** — hot-reload during development
- **Marketplace distribution** — share via Git repo or official marketplace
- **Namespacing** — no skill name collisions with other plugins
- **`${CLAUDE_PLUGIN_ROOT}`** — portable paths, no hardcoded `$HOME/.claude`
- **Enable/disable** — toggle without uninstalling
- **Version updates** — `claude plugin update` with semver tracking

## What we lose

Nothing functional. The custom `bin/plugin-*` scripts we prototyped are
strictly inferior to the built-in CLI. The only real delta is that rules
stay outside the plugin, which is architecturally appropriate.

## Decision

Restructure the harness as an official Claude Code plugin. Keep rules in
`~/.claude/rules/` as a separate concern. No custom plugin management
tooling needed — the built-in system covers all use cases.
