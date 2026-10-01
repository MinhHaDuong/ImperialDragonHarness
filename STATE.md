# Imperial Dragon Harness — State

Last updated: 2026-10-01T22:07Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T22:07Z · as of bfade35d -->

**Tickets:** 18 ready · 21 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**Recent (first-parent):**
  bfade35d Merge pull request #1104 from MinhHaDuong/close-0999-integration
  3d796179 Merge pull request #1103 from MinhHaDuong/roar-1101
  6c2fa0ef Merge pull request #1101 from MinhHaDuong/retire-0934

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Planning and documentation landed in PRs #1089/#1090. Runtime registration, launch guards and safe operator docs landed in PR #1091 (child 1003). Child 1002 was closed WONTDO in #1099; its extracted legacy helper patch remains historical and unapproved. PR #1101 retired obsolete 0934 provenance machinery while preserving memory data and source history. Parent 0999's integration review is complete and it closed in #1104; the memory v8 pilot is downstream, not a prerequisite.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Continue the memory v8 session on 0911/0917; pilot 0920 is now unblocked and next. Then address 0988 integration and 0916/0910 prompt/follow-up work; 0913 retains rollout.
Memory v8 is drafted: repository Markdown, factual roar capture and dream suggested by lair after five new experiences. Native packaging and opt-in shell integration remain follow-on design; scheduling is external.
The old library/compiler/loader train is superseded; runtime behaviour is unchanged.

The primary `docs-portable-agents-plan` checkout has 85 unreconciled local changes and is 56 commits behind main. Do not publish that branch wholesale: it contains stale ticket/helper/test changes; reconcile it separately before reuse.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
