# Personal data tiers — decided 2026-09-28

The harness is a PUBLIC repo. Personal information is managed in three tiers:

- **T1 — semi-public identifiers** (contact addresses, ORCID, homepage, public
  key IDs, institutional contacts of professional correspondents): allowed in
  the repo.
- **T2 — access topology and administrative references** (mail/IMAP/SMTP hosts
  and ports, login aliases, credential-file locations and inventories,
  keyring-extraction procedures, personal cloud endpoints, network/firewall
  posture of personal machines, FTP deploy credentials, local
  identity-document paths): never committed. Write them to
  `~/.config/harness/private/` (mode 700, outside the repo); the runtime
  discovers the private skills by symlink — repo files carry NO pointers to
  them, and .gitignore excludes the symlinks.
- **T2+ — financial and real-estate dossiers, third-party private identities**
  (property addresses, auction/bidding ceilings, personal amounts, and the
  names/addresses of private third parties — notaries, syndics, occupants,
  agents): never committed, not even as pointers. The private `directory`
  skill holds who-is-who data; in repo memory, redact such names as
  `[tiers — directory skill]` or drop the memory entirely.
- **T3 — secrets** (passwords, keys, tokens): never in the repo, never in
  agent-visible text; keystore only.

## Enforcement

- `scripts/check-personal-data.sh` blocks known T2 patterns (mail hosts,
  login aliases, keyring extraction); called by the pre-commit hook on staged
  files, by `make check-personal-data` (part of `make check`), and by the CI
  job `personal-data-guard`.
- The guard is a ratchet over known patterns, not an exhaustive scanner —
  apply the tiers by judgment too.
- This policy deliberately does NOT live in CLAUDE.md (resident context is
  budgeted; see `make resident-budget`). Pointers to it: the guard's error
  message and the pre-commit hook comment.

## History

History exposure of T2 facts is accepted (decided 2026-09-28): stop publishing
going forward, no history rewrite. Rationale: the committed content contained
no T3 secrets — only a reconnaissance profile (hosts, aliases, credential
locations); the marginal harm of residual history was judged lower than the
cost of a rewrite that invalidates every clone.
