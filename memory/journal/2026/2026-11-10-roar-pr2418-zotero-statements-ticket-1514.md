# Roar PR 2418: two statements corrected in the Zotero helper (ticket 1514)

Date: 2026-11-10. Project: ImperialDragonHarness. Follows raid 13f6d8
(tickets 1510 and 1511, PRs 2414 and 2413).

## Context

The author answered the raid's report with "Fix minors". The two minors:
the docstring of `licenses_attach` named a caller it does not have, and,
since 1511, a miss on an embedded title under a skipped hash index reads
`unidentified` where it read `unchecked`.

## Events

- The session first leaned to a behaviour change for the second minor:
  test the skipped index before the hint rule, so every miss reads
  `unchecked`. It put the call to an advisor seat (claude-opus-5-5).
- The advisor picked a third option: keep the behaviour, correct the text.
  It cited `skills/zotero/references/backfill.md` ("a file that would read
  `absent` reads `unchecked`") and `helper-script.md`, which already stated
  the narrow rule the code applies; only the docstring of
  `_staging_verdict` and the `unchecked` row of the verdict table said
  more. It also showed the every-miss rule would not be uniform: a file
  with no key at all reads `unidentified` through an earlier branch.
- The session built that option locally, pushed nothing, and asked the
  author, who answered "D".
- Gaze compared the syntax tree of `scripts/zotero.py` on base and head
  with docstrings removed: identical. The added test fails under the
  every-miss rule and under an ignored skip. Verify-gate ruled APPROVED at
  round 1.

## Outcome

PR 2418 merged at 9352232f7; ticket 1514 closed. No behaviour changed.

## References

`memory/evidence/attribution/2026-11-10-review-attribution-pr2418.md`;
`tickets/closed/1514-*.erg`.
