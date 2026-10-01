# Imperial Dragon Harness — State

Last updated: 2026-10-01T20:48Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-01T20:48Z · as of 9e89ba58 -->

**Tickets:** 21 ready · 21 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** 2 open PRs (1 draft), oldest #1091 0d · CI main: success
**Recent (first-parent):**
  9e89ba58 docs(memory): adopt Markdown-first v8 and replace the delivery train
  16b2bd70 Merge pull request #1090 from MinhHaDuong/docs-portable-agents
  9cff8d73 Merge pull request #1089 from MinhHaDuong/plan-portable-agents

## Resume point
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Ticket 0999 owns installation and runtime registration. The old relocation and cutover tickets 0978 and 0986 are closed WONTDO.
Academic skills are integrated: reading-note, critical-lit-review, slides, choose-venue, conference-submission-prep and message-framing. Claude.ai skill sync is off.
Planning landed in PR #1089; documentation is maintained in PR #1090. Portable loader/wiring implementation remains separate work under 0999. The planning PR's full gate passed 1289 tests with three skips.

## Next actions
See [ROADMAP.md](ROADMAP.md) for workstreams and `erg ready tickets/` for executable tickets.
Start with 0999 portability; keep runtime registration evidence distinct from the target design.
Memory v8 is drafted: repository Markdown, factual roar capture and weekly dreaming.
Start with 0911/0917, then pilot 0920; capture 0988 and prompt/timer 0916/0910 follow.
The old library/compiler/loader train is superseded; runtime behaviour is unchanged.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
