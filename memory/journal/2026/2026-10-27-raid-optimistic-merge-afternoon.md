# Raid 1237, 1227, 1239, 1246, 1244, 1240 and follow-on waves — optimistic merge afternoon (2026-10-27)

Context: `/raid 1237,1227,1239,1246,1244,1240` on the harness, orchestrator Opus 5.5 in Claude Code on padme,
session worktree `explore-raid-prep-116623`, started 11:25 CET. The author extended it to five waves plus
follow-ons (1245, 1241, 1222, 1236, 1255, 1256, 1254, 1260, 1251, 1264, 1261, 1263, 1265, 1269). About 45 PRs
merged, including about 12 ticket-only PRs. Mid-run the author stated "Stay optimistic. Trust, Verify, Monitor."

Events:

- Tracker 1226 (optimistic merge) landed its parts: the before-merge gate shrank to a cheap set of about 13 s
  (1245), the full suite moved after the merge (`merge-gate.py run-after`, 1244), a red after-merge run opens a
  ticket (1251), and landing went through `scripts/raid_land.py` (1255).
- The orchestrator skipped `/merge` step 8 (sync local main) for the first 13 merges, so helpers ran from a
  stale primary checkout. Saved as feedback memory `feedback_sync_local_main_after_merge`.
- No after-merge runner was started for 15 merges, until the orchestrator ran one by hand. Ticket 1265 (PR #1774)
  moved the start into `hooks/reference-transaction`. On the next two landings (#1774, #1775) the hook-started
  runner was observed in the process list (`merge-gate.py run-after --open-ticket --ref main`).
- A gate launched with the literal session id `SESSIONID` consumed #1738's second round; the author approved the
  merge on the round-1 APPROVED.
- `git reset --keep` in the orchestrator's worktree dropped unpushed ticket commits; they were restored by
  cherry-pick and the DOIfetch ticket renumbered to 1266.
- Tests leaked into the real `~/.local/bin` (fixed in #1759); install tests inherited PATH and turned main red
  after the author's `idh install` (fixed in #1767 with `isolated_path()`).
- Zotero 401 flake (tracker 1254): isolated by positive control to a live-versus-live xdist port collision;
  fixed in 1258 and 1259.
- #1763 (1261): after several parser bypasses the author chose to hash the raw ticket body.
- Review attribution: `attribution_record.py --capture-pr` refused all 29 PRs of the session checked at roar.
  Causes printed: seat model "not observed" or a placeholder, a missing identity field, and "fact order requires
  kind, pr, writer before reviewers" (the last also printed by every `raid_land.py` landing). Logged on ticket 1243.
- #1777 red control: the first run of a new fixture passed on the old code because `sh`'s `printf` has no `\x`
  escapes, so the marker never appeared; rewritten with `sed`, it then failed on the old code and passed on the fix.
- The gate on #1769 named an IPv4-mapped `is_private` consent hole on Python before 3.13. On padme,
  `ipaddress.ip_address('::ffff:93.184.216.34').is_private` is False on 3.11 (venv) and 3.12 (system); the fix was
  dropped from #1777.
- Ticket 1184 closed with the phase timing table: #1774 10m26s first review to merge (gaze 4m46s slowest),
  #1775 16m11s (orchestrator queue wait 10m25s slowest). Gaze results printed no `seat times:` line.

Outcome: main green at dd222149 after #1777; issue #1654 closed by #1775; no open PRs from this session.

Decisions recorded by the author during the run: forge independence for raid/hunt/gaze/merge deferred (1252, "not
today"); `idh-` prefix for generic command names; aider route to padme's local LLM (1263); one review then the
gate, non-blocking findings to tickets or a cleanup PR; `idh.mainGuard enforce` left to the author.
