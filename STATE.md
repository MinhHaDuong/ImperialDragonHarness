# Imperial Dragon Harness — State

Last updated: 2026-10-01T07:50Z

## North star
A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-10-01T07:51Z · as of d6cd5b85 -->

**Tickets:** 23 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  d6cd5b85 Merge pull request #1084 from MinhHaDuong/roar-skills-merge-wrapup
  b7e7a674 Merge pull request #1083 from MinhHaDuong/t0993-reading-note
  6e0c68d2 Merge pull request #1078 from MinhHaDuong/t0998-message-framing

## Resume point
**2026-10-01.** The eight academic skills uploaded to claude.ai are merged into the harness, which is now their single source of truth (PR #1075 import, tracker 0992 closed after integration review, PRs #1077-#1084). New or rewritten skills: `reading-note`, `critical-lit-review`, `slides` (absorbs text-to-slides and slides-review; beamer default), `choose-venue` (replaces choose-journal and conference-targeting), `conference-submission-prep`, `message-framing`; `/applied-econ-writing` retired into `rules/doctype/article.md`. claude.ai skill sync is off in Claude Code user settings (untracked). Imagine options now carry prices (#1076). The climate-finance-het memory pool was swept to 95 live notes (#1073, #1074); ticket 0991 asks `/dream` to purge tombstones and rank by reasoned EU.

**2026-09-30.** The live `~/.claude` move is retired; the direction is a separate `~/.idh` clone with additive registration through native runtime mechanisms (`docs/idh-install-strategy.md`).

Owed to the author, outside any diff:
- **ILaaS key**: cle consortium -> ~/.config/keys/ilaas.env, then models.json (0977 report).
- **Rotate** the six bash -x values and the Albert key (deferred to October 2026).

## Blockers
- **0986**: the old live-checkout move is retired. A fresh `~/.idh` clone needs additive runtime registration before it can replace the current symlink.

## Next actions
- **Relocation** (tracker 0978): keep `~/.claude` as Claude Code's profile; clone IDH separately into `~/.idh` and register reviewed skills natively. The current `idh install` is host setup, not the fresh-install command.
- **Harness defects**: 0988 (session memory lands uncommitted in the checkout and stalls host pulls), 0990 (raid Phase 6 cannot obtain a `/gaze` verdict from a background agent; see 0853), 0991 (`/dream` method).
- **Memory v7** (tracker 0909): foundations 0911, 0917 are ready. Re-read 0920/0923 before starting them; their premise changes with 0984's verdict.
- **Portable model policy** (tracker 0974): Phase 0 (0975) landed; Phase 1 child not yet filed.
- **Open defects worth a slot**: 0875 (hermeticity guard blind to script-path spawns), 0879 (gate writes malformed log lines), 0979 (Pi silent reroute to openrouter).
- **Watch**: re-open 0062 (Firecracker) when agents run against secret-bearing projects; lift the merge-review gate into the harness when a second consumer project grows one (0900).

## Backlog
- Merge REALF guidelines and business rules
