---
name: feedback_union_append_only_by_timestamp
description: "Resolve erg log-tail conflicts by unioning and sorting on each line's own timestamp, never by side; and verify the union with a probe that can actually match every author"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cd1175b7-c704-41ea-ba61-27f00fc2ff49
  modified: 2026-09-03T10:23:37.704Z
---

Every `--- log ---` conflict in a ticket is two **appends**. Neither side deletes,
so taking either side whole silently drops an entry. Resolve by union, ordered by
the `YYYY-MM-DDThh:mmZ` stamp each line carries — not by the side it came from,
and not by append order.

**Why:** three collisions in one session (PRs #261 and #262 against #264's own
entries on `tickets/0120` and `tickets/0606`) all had the same shape, and one of
them carried the author's own `Minh Ha-Duong` log line. Resolving by side would
have deleted it with a clean `make check` and a green `erg check` — nothing
downstream compares a log against what it should have contained.

**How to apply:** script it rather than hand-edit. Match the conflict block,
concatenate both sides, assert every surviving line starts with a timestamp
(refuse to reorder anything that is not a log line), dedupe, sort by stamp.
Working copy: `/home/haduong/.claude/jobs/*/tmp/union_log.py` pattern — regex on
`<<<<<<< / ======= / >>>>>>>`, `re.S | re.M`.

**The verification is where this nearly went wrong.** Checking the union with
`grep -o '^2026-..-..T..:..Z [A-Za-z ]*note'` reported the author's entry
*missing* — because the character class has no hyphen and cannot match
"Minh Ha-Duong". The union was correct; the probe was blind. A probe that returns
"absent" when it cannot match is the same defect as a check whose all-clear is
indistinguishable from "I could not look" ([[feedback_probe_needs_discriminating_control]]).
Verify with `grep -c` on a literal you know is present, or count the stamps.

Related: [[feedback_append_only_merge_union]] (same defect class on DECISIONS.md),
[[feedback_stage_by_path_in_shared_checkouts]].
