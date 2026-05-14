# Imperial Dragon Harness

Never display API keys, tokens, passwords, or any credentials in chat text — not even partially, not even in "here's what I found" summaries.

Current status, blockers, next actions: `STATE.md`.

Tickets: `tickets/*.erg`. GitHub Issues are for cross-repo coordination only.

## Skills Catalog

The skills catalog in `README.md` is auto-generated from `skills/*/SKILL.md` frontmatter.

**When you add, rename, or remove a skill:**

```bash
make skills-catalog    # Regenerate README.md catalog
```

**To detect drift:**

```bash
make check-skills-drift  # Fails if README.md is out of sync
```

This check is run in CI to catch forgotten regeneration before merge.

@tickets/AGENTS.md
@RTK.md
