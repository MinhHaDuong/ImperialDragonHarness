# One-call attribution capture; merge-commit storage filed

Context: the author found merge-time attribution extraction and capture
burdensome and asked whether a strict one-ticket-per-PR rule would let the
record live in `erg log` instead of journal annex files.

Events:
- Option compared and rejected: `erg log` is one line per entry, while a
  record is about 30 lines whose `path:line` anchors `attribution_query.py`
  scores on; `.erg` files have no encrypted audience; the one-ticket rule was
  not needed by any alternative.
- PR #1719 (ticket 1242) added `attribution_record.py --capture-pr N`, which
  runs the seats join, the extract with the forge's `mergedAt` date, and the
  capture in one call. Gaze REVIEWED, verify-gate APPROVED round 1.
- Its first live use captured PR #1719's own record in this roar, exit 0.
- PR #1720 filed ticket 1243: write the PR body's attribution block into the
  merge commit body and drop the post-merge journal write. Labelled
  needs-human for private-audience storage and for refusing incomplete blocks
  at merge.
- The ticket-only merge of #1720 needed two gate-record runs: main moved
  during the first 79 s test run.
