# Raid af737d: Zotero as the record for reading notes (tracker 1522)

Date: 2026-11-11 · host: padme · orchestrator anthropic/claude-opus-5-5 ·
coders anthropic/claude-sonnet-5-5 (1524, 1526, 1527) and
anthropic/claude-opus-5-5 (1525)

## Context

Ticket 1522 was filed on 2026-11-10 by a climate-finance-het coding agent from
author decisions recorded in that project's journal
(2026-11-10-rel-pr-adjudication-roar.md). It chose the Zotero web API with the
read-write key.

## Events

- Imagine found the web-API choice contradicted the author rulings of
  2026-10-15/16 (local API only; memory/topics/host-environment.md). The
  Blind-Spot pass found the local API already writes child notes
  (tests/zotero_live.py) and that the climate-finance-het journal recorded the
  storage decision, not the transport.
- One question to the author: transport for publish and pull. Answer: local
  API for both; the 2026-10-16 ruling stands.
- 1522 decomposed (PR 2451) into 1524 rule and skills, 1525 publish-notes,
  1526 pull-notes, 1527 lair offer. Climate-finance-het's live session logged
  the transport change on its ticket 3019.
- Orchestrator design calls: tag-keyed idempotence `wiki:<project>/<slug>`;
  in-place update only for harness-created notes behind a version guard; lair
  offer reads a local state file only; word caps per project.
- 1525's gaze considers 1 (record matched on library and item) and 2 (paging
  past 100 children) were ruled in and fixed before merge with live tests.
- PR 2454's gaze answer carried no attribution (script item plus self);
  `attribution_query.py --missing-attribution`, merged earlier the same day,
  listed it (32 units). Cause not examined.
- Writer lines were recorded for every PR right after landing.

## Outcome

PRs 2451-2455 merged; 1524-1527 closed; every gate round 1 APPROVED. Tracker
1522 stays open on its last criterion, climate-finance-het 3019 consuming the
verbs. Live tests ran by hand with DISPLAY=:0 on the throwaway profile; the
author's library was not written.

## References

- tickets/1522-zotero-is-the-record-for-reading-notes-t.erg
- reviews rv-20261111-pr-2452-bf1f, -2453-71a5, -2454-b3cf, -2455-e614
