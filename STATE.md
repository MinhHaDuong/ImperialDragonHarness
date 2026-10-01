# Imperial Dragon Harness — State

Last updated: 2026-10-01T19:10Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T19:10Z · as of a5abd4bd -->

**Tickets:** 22 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**Recent (first-parent):**
  a5abd4bd Merge pull request #1088 from MinhHaDuong/reading-note-industrial
  4a6919f3 Merge pull request #1087 from MinhHaDuong/fix-skill-seam-locale
  10719602 Merge pull request #1086 from MinhHaDuong/dream-consolidate-2026-10-01-harness

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Current local work includes portable loader/wiring changes, the ticket sweep and documentation updates; these are uncommitted. The last fast gate passed 853 tests with one skip.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Start with 0999 portability; keep runtime registration evidence distinct from the target design.
Memory v7 starts with 0911 and 0917; 0920/0923 now use the portable root contract.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
