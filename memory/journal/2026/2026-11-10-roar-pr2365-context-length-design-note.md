# Roar: PR 2365, context length design note and ticket 1499

Date: 2026-11-09 to 2026-11-10 UTC, host padme. Merged and read back MERGED
on the forge: PR 2365, merge 3bac6a5d, head 752af51b. It adds
`design/2026-11-09-context-length-strategy.md` (status: proposed) and files
ticket 1499, open, labelled `needs-human`. Same session as PR 2358.

Context: after PR 2358 the author wrote "Consider not just the three-line
follow-up, but the whole context lenght management strategy in IDH", then
"strategy and implmentation", then "Design note and ticket. No
implementation. Identify up to three small specific pain points to solve
urgently."

Events:
- The interface session first answered in conversation with a 28-day run of
  `scripts/trace-compact-audit.py`. It presented the script's
  `recoverable_usd_upper_bound` as the cost of the runs, and wrote that 25
  raid runs were "told to hand off at about 172K".
- The design note's first draft kept both statements. Two advisor reviews of
  the draft, an `opus` agent and `codex exec -m gpt-6.1-sol`, each returned
  "sound with changes" and both named the skipped diagnosis and the
  mislabelled column.
- Checks made after the reviews: in the two heaviest raid sessions of the
  audit (October, peaks 965,884 and 757,082 cache-read tokens) the raid
  autonomous brief never appears in the transcript; a scan of main-session
  transcripts for turns since 2026-11-01 found 281 sessions, 24 with 30 or
  more turns at or above 230K (19 on claude-opus-5-5, 5 on claude-fable-5-1),
  4 at or above 450K, 1 at or above 550K. The note was rewritten on these
  figures and the statements above were corrected to the author in the
  session's report.
- A probe from inside the session read its own context from its transcript,
  located by the session id in the environment: 211,485 tokens of prompt at
  2026-11-09T22:39Z.
- First gaze on PR 2365: FINDINGS. Its other-family seat (codex,
  gpt-6-luna) ran and its report was refused with "seat reach: invalid reach
  declaration"; the answer was recorded `seats: self-only`. Its verifiable
  finding: ticket 1499 said "do not start before the author has accepted it"
  in its body only, and `erg ready` listed it.
- Fix in one commit: `erg label 1499 needs-human`, and one sentence in the
  note on how the Sol model id was read. Second gaze, narrower: REVIEWED.
  Verify-gate: APPROVED at round 1. `scripts/raid_land.py 2365` ran without
  a refusal after the author's `/merge 2365`.
- The branch received main twice by merge commit and never by force-push.

Observed by roar:
- `memory/evidence/attribution/2026-11-10-review-attribution-pr2365.md`
  marks both gaze findings `adopted: no`; commit 752af51b fixes both. The
  record of PR 2358 marks as `adopted: yes` findings that were left unfixed.
- The two advisor reviews of the note are recorded in the note's Review
  section and are not in the attribution record: they were not gaze seats.
- The roar verdict of PR 2358, "safe to /clear", preceded this whole task in
  the same session.

Left open by the note, for the author: whether an attended raid is an
interface session; what an interface session may do at its ceiling;
acceptance of the note, on which ticket 1499 waits.
