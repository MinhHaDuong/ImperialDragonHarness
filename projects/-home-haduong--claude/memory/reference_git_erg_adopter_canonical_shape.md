---
name: reference_git_erg_adopter_canonical_shape
description: Canonical git-erg adopter shape is CLAUDE.md = `@tickets/AGENTS.md`; detect stale pre-0013 erg-init footprints by orphan .claude/skills/ticket-* + `--- git-erg ---` block
metadata:
  type: reference
---

When a tooling repo migrates, **adopter repos silently lag** — they keep the old
installed footprint until someone re-syncs. git-erg dropped the `.wip`
claim/release machinery and the local `ticket-*` wrapper skills in its own ticket
0013 (2026-05-02) and moved to a `tickets/AGENTS.md` + `tickets/.ergrc` model
(`erg init` now writes only those two files — no `.claude` skills, no CLAUDE.md
block). But several adopter repos still carried the **stale pre-0013 footprint**.

**Canonical adopter shape** (cf. `chemin-de-voix`, `git-erg`, `.claude`):
- `CLAUDE.md` (or `.claude/CLAUDE.md`) is just `@tickets/AGENTS.md` — no inline
  `--- git-erg ---` block.
- No `.claude/skills/ticket-*` (erg provides `new`/`close`/`ready`/`list`/`archive`
  as subcommands; `claim`/`release` describe machinery `%erg v1` removed).
- No hand-maintained `.claude/rules/tickets.md` (it described a legacy `%ticket`
  `Status:`-header model the binary no longer implements; `erg spec` is authoritative
  — v1 has **no `Status:` header**, closed-ness is path- or `Closed:`-header-based).

**Detection (cheap grep across the fleet):**
- orphan skills: `find .claude/skills -name 'ticket-claim' -o -name 'ticket-release'`
  (the claim/release pair is the surest smoking gun of a pre-0013 footprint)
- stale block: `grep -l 'git-erg --- begin' .claude/CLAUDE.md CLAUDE.md`
- stale paths: `grep -rn 'tickets/tools/go' .claude` (old build path → vendored `tickets/erg`)

**Caveats learned the hard way (2026-06-08 scry sweep):**
- A repo can be *substantively* migrated (accurate erg-verb CLAUDE.md, no skills)
  yet still carry the `--- git-erg ---` marker — that block is not necessarily stale.
  Read the content before reducing; don't strip accurate, project-specific docs for
  cosmetic marker-uniformity unless asked.
- File **mtimes mislead**: dirty working-tree edits with old mtimes were actually
  migration-in-progress content (more correct than HEAD). Verify by content/intent,
  not timestamps.
- `.claude/CLAUDE.md` may be **gitignored** in a repo (e.g. Climate_finance whitelists
  only `.claude/rules|skills|hooks|settings.json`) — its reduction is then local-only,
  not part of the PR.

Sweep PRs (2026-06-08): fuzzy-corpus #60, Climate_finance #794, aedist #783, padme #19.
cadens deferred (149-file untracked `.claude/` scaffold). See [[project_git_erg_migration_next]].
