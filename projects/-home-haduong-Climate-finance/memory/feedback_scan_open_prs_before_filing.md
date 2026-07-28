---
name: feedback_scan_open_prs_before_filing
description: "Before filing a follow-up ticket from a sweep, scan open PRs — a parallel session may be delivering the same defect class right now"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 69fadc0c-d582-4ce1-adea-c507e9c40443
  modified: 2026-07-27T19:30:09.559Z
---

A sweep that finds a real defect class is not evidence the class is unclaimed.
Main moves fast enough here that a sibling session can be mid-delivery on the
same finding, from the opposite end.

Worked example (2026-07-27): settling ticket 0290 (orphaned includes) exposed
the same drift in the `*_FIGS` sets, so 0373 was filed for it. Ticket **0359**
had been working the figure side independently and landed **the same day**,
delivering all four of 0373's exit criteria — plus its own closure oracle that
duplicated the guard 0290 had just written. 0373 closed as superseded within
hours of being filed, and the duplicate guard had to be folded back into
0359's file at verify time.

**Before filing:** enumerate open PRs and grep their touched paths for the
class, not just for the ticket ID. Use the enumerate-then-query form —
`gh pr list --json files` does not populate `files`:

```bash
for n in $(gh pr list --state open --limit 60 --json number --jq '.[].number'); do
  gh pr view "$n" --json files --jq '.files[].path' | grep -qE '<paths of the class>' \
    && echo "PR $n touches this class"
done
```

**At verify, re-check for a duplicate guard**, not only a duplicate ticket. Two
tests answering one question is the defect a hygiene ticket exists to remove;
merge them and keep the direction each covers uniquely. See
[[feedback_lean_methods]] and [[feedback_union_only_defects]].
