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

## Personal data tiers

This harness is a PUBLIC repo. Personal information is managed in three tiers:

- **T1 — semi-public identifiers** (contact addresses, ORCID, homepage, public key IDs): allowed in the repo.
- **T2 — access topology and administrative references** (mail/IMAP/SMTP hosts and ports, login aliases, credential-file locations and inventories, keyring-extraction procedures, local identity-document paths): never committed. Write them to `~/.config/harness/private/` (mode 700, outside the repo) and reference that path.
- **T3 — secrets** (passwords, keys, tokens): never in the repo, never in agent-visible text; keystore only.

The pre-commit hook and `make check-personal-data` (CI: `scripts/check-personal-data.sh`) block known T2 patterns; the guard is a ratchet, not an exhaustive scanner — apply the tiers by judgment too. History exposure of T2 facts is accepted (decided 2026-09-28): stop publishing going forward, no history rewrite.

@tickets/AGENTS.md
@RTK.md
