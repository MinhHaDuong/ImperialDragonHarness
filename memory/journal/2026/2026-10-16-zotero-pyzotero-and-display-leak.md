# Zotero helper moves to pyzotero; test fixture leaked onto the author's screen

Audience: public. 2026-10-16, padme, Claude Code session finishing PR #1441
(tickets 1113 and 1111).

## Decisions made by the author

- "In tests up Zotero as a fixture or skip -- no mock": the in-process stub
  of the local API and connector was deleted.
- "Plan A. On arrête le YAGNI massacre": the hand-rolled local-API client was
  replaced by pyzotero 1.16 in local mode, for reads and writes; the desktop
  connector path was deleted.
- Libraries compared on request: pyzotero (local reads and writes),
  papers-zotero 0.3.1 and zotero_api_rs 1.0.0 (Web API only),
  bahayonghang/zotero-cli (reads `zotero.sqlite`, writes through the Web API).
  Only pyzotero fits local-only, never-sqlite, never-web.
- Size review after the swap: accepted all five cuts and three /gaze calls for
  ticket 1116 (merge `audit`/`reconcile`, Zotero search plus rapidfuzz, drop
  RIS, JSON-only dedup report, pdf2doi offline evaluation; "Always Allow" keys
  only, Zotero 10 floor, slow read fails visibly).

## Observed events

- The orchestrator relayed a third-party README saying the local API is
  read-only. The author said Zotero 10 accepts local writes and asked for
  verification instead of doubt. `server_localAPI.js` in zotero/zotero: no
  write methods at tag 9.0.6; POST/PUT/PATCH/DELETE, `/api/local/authorize`
  and the `Zotero-Server-ID` requirement present from 10.0.0 to 10.0.6.
- The live test fixture passed the caller's `DISPLAY` (`:1`),
  `WAYLAND_DISPLAY`, `XAUTHORITY` and session bus to the throwaway Zotero. Test
  runs opened Zotero windows and "Always Allow" dialogs on the author's
  screen; the author ordered it stopped. The worker was stopped; the fixture
  now runs Zotero on a private Xvfb. A `/proc` probe during the next run saw 19
  Zotero processes, all on the private display; 249 tests passed, none skipped.
- `scripts/zotero.py` line counts: 3,177 on main before the PR, 3,051 at the
  size review after the pyzotero swap.
- `erg-pr-merge` closed and archived 1111/1113 in a commit made before
  rebasing; the commit also edited ticket 1116, which conflicted with #1444
  (ticket-only, merged meanwhile). The orchestrator resolved the log-line
  conflict by keeping both lines, then the forge merged #1441.

## References

PRs #1441, #1443, #1444, #1445; tickets 1113, 1111 (closed), 1116;
`memory/evidence/2026-10-16-review-identities-pr1441.md`.
