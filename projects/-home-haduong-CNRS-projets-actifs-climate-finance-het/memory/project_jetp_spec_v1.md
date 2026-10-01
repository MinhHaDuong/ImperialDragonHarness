---
name: project_jetp_spec_v1
description: "JETP Observer system specification v1 accepted 2026-09-30 (tag jetp-spec-v1); what it fixed, what remains before M2 code"
metadata:
  node_type: memory
  type: project
  originSessionId: 99c20e86-e272-4f1d-999a-588c6d03f2c1
  modified: 2026-09-30T20:42:46.463Z
---

The JETP Observer (system; website = Observatory; ledger = Data tables) has a ten-document specification indexed at `docs/jetp-spec.md` plus `docs/jetp-legal-note.md`, accepted by the author 2026-09-30, tag `jetp-spec-v1` (commit 0217a024). Reviews archived in `docs/jetp-spec-review/`. The author wanted it "explicit and reviewed the heck out of before we launch extraction"; M2 code was gated on it (1506 Blocked-by 1711, now closed).

**Why:** a throwaway prototype (branch `spike-spec-prototype`, never merged) showed USD 14–26 model spend but 58–210 author-hours under a human-review rule; the author's attention is the binding constraint, hence full autonomy.

**How to apply:** open follow-ups: tracker 1703 (1705, 1707 repoint scattered sources; 1706 check 1500/1506 consistency; integration review), 1702 (storage and code catch up: readings/runs/dispositions journals, schema targets), 1712 (Zotero off-site copy, M2 restore test), 1791 (TypeSafe Jev). Legal review is a go-live gate only: never query CNRS legal services about an undeployed service. Horizon to 2030, extension decision 2028. See [[feedback_author_is_not_the_checker]], [[feedback_merge_reviews_critically]], [[project_jetp_milestone_ladder]].
