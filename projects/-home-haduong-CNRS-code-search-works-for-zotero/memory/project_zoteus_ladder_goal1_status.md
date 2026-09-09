---
name: project-zoteus-ladder-goal1-status
description: "Where zoteus stands on the acceptance ladder's goal 1 (R10/R15/R22) as of 2026-09-04 — gaps A and B closed and sent upstream, gap C now a real decided FAIL, waiting on the maintainer"
metadata: 
  node_type: memory
  type: project
  originSessionId: dc5e15a4-edc1-4528-b6bf-d9afd95441c1
  modified: 2026-09-04T09:07:21.927Z
---

Tracker: ticket 0613. Goal 1's three terms are R10 (no-egress), R15
(uninstall), R22 (durable pause).

**Gap A (R10, phone-home) — closed, sent.** `ZOTEUS_UPDATE_CHECK` defaults
true, phones home at startup. Attribution confirmed by a live measured run
(ticket 0629), not just source reading. Sent as
[oscardvs/zoteus#54](https://github.com/oscardvs/zoteus/issues/54), a soft
proposal (default off, or first-run consent), not a demand.

**Gap B (R15, uninstall) — closed, sent.** No host uninstall lifecycle to
hook, so the surface is a published removal procedure. Proven end-to-end for
real (build, download a model, delete exactly the declared root, zero
residue). Sent as [oscardvs/zoteus#55](https://github.com/oscardvs/zoteus/pull/55)
(a docs PR, README `## Uninstall` + `docs/uninstall.md`).

**Gap C (R22, durable pause) — now DECIDED, and it's a FAIL, for a real
reason.** Was `not-run` for lack of two things: durable work counters
(ticket 0642 built them — real, sqlite-transactional, not the in-memory
`metrics.ts` shortcut a first pass tried and the author rejected — see
[[feedback-validate-utility-before-sending-upstream]]) and a perturbation
zoteus would accept (ticket 0643 wired `action:"build"` against a seeded
incomplete index, since the harness's only prior perturbation,
`EDIT_ONE_ITEM`, zoteus correctly refuses). With both landed, R22 reaches a
real verdict: **FAIL** — `stop` durably cancels the current job but doesn't
gate a subsequent explicit `build`, confirming a tension the adapter's own
docstring had already flagged as open. Sent as
[oscardvs/zoteus#56](https://github.com/oscardvs/zoteus/issues/56).

**A dropped path, worth remembering why.** Ticket 0636 proposed sidestepping
the missing perturbation with a zoteus-private sqlite read instead of a real
counter. Author's "high road" call: reject it even though it was internally
disciplined (read-only, no fabrication) — it would have been zoteus-only and
coupled the harness to undeclared internal storage rather than a contract.
0033 (real target-side counters) stayed the standing target instead.

**Next real step:** wait on the maintainer's response to #56, then rebuild
with whatever he ships plus 0642's counters, and re-measure R22 for real —
not "he merged something," but the actual check passing. The staged
counters PR (`verification/UPSTREAM-PR-WORK-COUNTERS-0642.md`) stays unsent
until then; sending it alone wouldn't make R22 pass.
