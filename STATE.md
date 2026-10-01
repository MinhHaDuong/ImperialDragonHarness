# Imperial Dragon Harness — State

Last updated: 2026-10-01T19:52Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T19:52Z · as of 8fce5703 -->

**Tickets:** 22 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** 1 open PR, oldest #1090 0d · CI main: in progress
**Recent (first-parent):**
  8fce5703 docs: preserve checkout commands after guard test changes directory
  8c610d07 docs: simplify guides around portable agents checkout
  9cff8d73 Merge pull request #1089 from MinhHaDuong/plan-portable-agents

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Planning landed in PR #1089; documentation is maintained in PR #1090. Portable loader/wiring implementation remains separate work under 0999. The planning PR's full gate passed 1289 tests with three skips.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Start with 0999 portability; keep runtime registration evidence distinct from the target design.
Memory v7 starts with 0911 and 0917; 0920/0923 now use the portable root contract.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
