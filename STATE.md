# Imperial Dragon Harness — State

Last updated: 2026-04-17

## Status

Level 4 (Hooks) + orchestrator + `/verify` loop + git-erg tickets + bibliography pipeline all shipped. Skills slimmed to non-obvious constraints only (916→325 lines across 5 skills).

## Open tickets (2)

- 0013 — bib-to-zotero (push refs.bib to Zotero via API at submission)
- 0015 — add CI (validator + skill sanity on PR/push)

## Blockers

None

## Next actions

- **CI batch**: 0015 here + git-erg 0003 + AEDIST 0111 + Climate-finance 0081. Once green, enable branch protection.
- Build 0013 (bib-to-zotero) when a manuscript reaches submission.
- Merge REALF guidelines and business rules.

## North star

A reusable, science-backed harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Backlog

- Streamline settings.json hook configuration (#23)
- Multi-machine sync (doudou ↔ padme)
- Second project onboarding (CIRED.digital or activity reports)
- Measure compliance rates (context hygiene, review quality, token economy)
